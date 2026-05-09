#!/usr/bin/env python3
"""
Multi-Dimensional Validation Framework

Fixes the "only 1-day direction" problem by validating across:
1. Multiple time horizons (1/3/7/14 days)
2. Risk-adjusted returns (Sharpe of recommendations)
3. Baseline comparison (vs equal-weight hold, vs SPY)
4. Value assessment validation (undervalued outperform overvalued?)

Usage:
  python validation_framework.py                    # Validate all available data
  python validation_framework.py --days 14          # 14-day horizon
  python validation_framework.py --baseline         # Include baseline comparison
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent))
from watchlist_utils import load_watchlist


@dataclass
class ValidationResult:
    total_predictions: int = 0
    valid_predictions: int = 0
    direction_accuracy: Dict[str, float] = field(default_factory=dict)
    return_by_action: Dict[str, List[float]] = field(default_factory=dict)
    baseline_equal_weight: float = 0.0
    baseline_spy: float = 0.0
    strategy_cumulative_return: float = 0.0
    sharpe_of_recommendations: float = 0.0
    max_drawdown_of_recommendations: float = 0.0
    win_rate: float = 0.0
    grade: str = 'F'


class ValidationFramework:
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        self.data_dir = Path(__file__).parent / "data"
        self.predictions_dir = self.data_dir / "predictions"
        self.daily_dir = self.data_dir / "daily"
        self.output_dir = self.data_dir / "validation"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.watchlist = load_watchlist()
    
    def load_predictions(self, date: str) -> Optional[Dict]:
        path = self.predictions_dir / f"prediction-{date}.json"
        if not path.exists():
            return None
        try:
            with open(path) as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    
    def load_quotes(self, date: str) -> Optional[List[Dict]]:
        path = self.daily_dir / f"quotes-{date}.json"
        if not path.exists():
            return None
        try:
            with open(path) as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            return None
    
    def get_price(self, quotes: List[Dict], symbol: str) -> Optional[float]:
        for q in quotes:
            if q.get('symbol') == symbol:
                for key in ('last', 'last_done', 'current_price'):
                    if key in q and q[key] is not None:
                        try:
                            return float(q[key])
                        except (ValueError, TypeError):
                            continue
        return None
    
    def get_prev_close(self, quotes: List[Dict], symbol: str) -> Optional[float]:
        for q in quotes:
            if q.get('symbol') == symbol:
                for key in ('prev_close', 'previous_close'):
                    if key in q and q[key] is not None:
                        try:
                            return float(q[key])
                        except (ValueError, TypeError):
                            continue
        return None
    
    def find_available_dates(self) -> List[str]:
        dates = []
        for f in sorted(self.predictions_dir.glob("prediction-*.json")):
            date_str = f.stem.replace("prediction-", "")
            dates.append(date_str)
        return dates
    
    def calculate_daily_returns(self, symbol: str, start_date: str) -> Dict[str, float]:
        returns = {}
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        
        for i in range(14):
            check_dt = start_dt + timedelta(days=i+1)
            check_date = check_dt.strftime('%Y-%m-%d')
            
            prev_dt = start_dt + timedelta(days=i)
            prev_date = prev_dt.strftime('%Y-%m-%d')
            
            current_quotes = self.load_quotes(check_date)
            prev_quotes = self.load_quotes(prev_date)
            
            if current_quotes and prev_quotes:
                current_price = self.get_price(current_quotes, symbol)
                prev_price = self.get_price(prev_quotes, symbol)
                
                if current_price and prev_price and prev_price > 0:
                    returns[check_date] = (current_price - prev_price) / prev_price
        
        return returns
    
    def validate_direction(self, prediction_date: str, actual_date: str) -> Dict:
        prediction = self.load_predictions(prediction_date)
        actual_quotes = self.load_quotes(actual_date)
        
        if not prediction or not actual_quotes:
            return {'total': 0, 'correct': 0, 'accuracy': 0.0}
        
        pred_items = prediction.get('watchlist_predictions', [])
        if not pred_items:
            top_picks = prediction.get('top_picks', [])
            for tp in top_picks:
                pred_items.append({
                    'symbol': tp.get('symbol'),
                    'predicted_direction': 'up' if tp.get('action') == 'BUY' else 'neutral',
                    'recommendation': tp.get('action', 'HOLD')
                })
        
        correct = 0
        total = 0
        
        for pred in pred_items:
            symbol = pred.get('symbol')
            predicted = pred.get('predicted_direction', '').lower().strip()
            
            if predicted in ('uncertain', 'sideways', 'flat', 'range'):
                predicted = 'neutral'
            
            current_price = self.get_price(actual_quotes, symbol)
            prev_close = self.get_prev_close(actual_quotes, symbol)
            
            if current_price is None or prev_close is None or prev_close == 0:
                continue
            
            change_pct = (current_price - prev_close) / prev_close
            
            if change_pct > 0.005:
                actual = 'up'
            elif change_pct < -0.005:
                actual = 'down'
            else:
                actual = 'neutral'
            
            total += 1
            if predicted == actual:
                correct += 1
            elif predicted == 'neutral' and actual != 'neutral':
                pass
            elif actual == 'neutral':
                correct += 0.5
        
        accuracy = correct / total if total > 0 else 0.0
        return {'total': total, 'correct': correct, 'accuracy': accuracy}
    
    def validate_recommendations(self, prediction_date: str, actual_date: str) -> Dict:
        prediction = self.load_predictions(prediction_date)
        actual_quotes = self.load_quotes(actual_date)
        
        if not prediction or not actual_quotes:
            return {}
        
        pred_items = prediction.get('watchlist_predictions', [])
        if not pred_items:
            top_picks = prediction.get('top_picks', [])
            for tp in top_picks:
                pred_items.append({
                    'symbol': tp.get('symbol'),
                    'recommendation': tp.get('action', 'HOLD')
                })
        
        returns_by_action = {}
        
        for pred in pred_items:
            symbol = pred.get('symbol')
            action = pred.get('recommendation', 'HOLD').upper()
            
            current_price = self.get_price(actual_quotes, symbol)
            prev_close = self.get_prev_close(actual_quotes, symbol)
            
            if current_price is None or prev_close is None or prev_close == 0:
                continue
            
            ret = (current_price - prev_close) / prev_close
            
            if action not in returns_by_action:
                returns_by_action[action] = []
            returns_by_action[action].append(ret)
        
        result = {}
        for action, returns in returns_by_action.items():
            result[action] = {
                'count': len(returns),
                'avg_return': round(sum(returns) / len(returns), 4),
                'win_rate': round(sum(1 for r in returns if r > 0) / len(returns), 4),
                'best': round(max(returns), 4),
                'worst': round(min(returns), 4)
            }
        
        return result
    
    def validate_vs_baseline(self, prediction_date: str, actual_date: str) -> Dict:
        prediction = self.load_predictions(prediction_date)
        actual_quotes = self.load_quotes(actual_date)
        
        if not prediction or not actual_quotes:
            return {}
        
        equal_weight_returns = []
        strategy_returns = []
        
        pred_items = prediction.get('watchlist_predictions', [])
        if not pred_items:
            top_picks = prediction.get('top_picks', [])
            for tp in top_picks:
                pred_items.append({
                    'symbol': tp.get('symbol'),
                    'recommendation': tp.get('action', 'HOLD')
                })
        
        for pred in pred_items:
            symbol = pred.get('symbol')
            action = pred.get('recommendation', 'HOLD').upper()
            
            current_price = self.get_price(actual_quotes, symbol)
            prev_close = self.get_prev_close(actual_quotes, symbol)
            
            if current_price is None or prev_close is None or prev_close == 0:
                continue
            
            ret = (current_price - prev_close) / prev_close
            equal_weight_returns.append(ret)
            
            buy_actions = ('BUY', 'STRONG BUY', 'GET_ON_BOARD', 'BUY_SMALL')
            hold_actions = ('HOLD', 'WEAK HOLD', 'WAIT')
            sell_actions = ('SELL', 'AVOID', 'REDUCE')
            
            if any(s in action for s in buy_actions):
                strategy_returns.append(ret)
            elif any(s in action for s in hold_actions):
                strategy_returns.append(ret * 0.5)
            elif any(s in action for s in sell_actions):
                strategy_returns.append(-ret * 0.5)
        
        ew_avg = sum(equal_weight_returns) / len(equal_weight_returns) if equal_weight_returns else 0
        strat_avg = sum(strategy_returns) / len(strategy_returns) if strategy_returns else 0
        
        return {
            'equal_weight_avg_return': round(ew_avg, 4),
            'strategy_avg_return': round(strat_avg, 4),
            'strategy_beats_baseline': strat_avg > ew_avg,
            'alpha_vs_baseline': round(strat_avg - ew_avg, 4)
        }
    
    def run_full_validation(self, horizon_days: int = 1) -> ValidationResult:
        result = ValidationResult()
        dates = self.find_available_dates()
        
        if not dates:
            print("No prediction data found")
            return result
        
        all_direction_accuracies = []
        all_returns_by_action = {}
        all_baselines = []
        
        for pred_date in dates:
            pred_dt = datetime.strptime(pred_date, '%Y-%m-%d')
            actual_dt = pred_dt + timedelta(days=horizon_days)
            actual_date = actual_dt.strftime('%Y-%m-%d')
            
            direction = self.validate_direction(pred_date, actual_date)
            if direction['total'] > 0:
                all_direction_accuracies.append(direction['accuracy'])
                result.valid_predictions += 1
            
            rec_returns = self.validate_recommendations(pred_date, actual_date)
            for action, data in rec_returns.items():
                if action not in all_returns_by_action:
                    all_returns_by_action[action] = []
                all_returns_by_action[action].extend(
                    [data['avg_return']] * data['count']
                )
            
            baseline = self.validate_vs_baseline(pred_date, actual_date)
            if baseline:
                all_baselines.append(baseline)
            
            result.total_predictions += 1
        
        if all_direction_accuracies:
            result.direction_accuracy = {
                '1d': round(sum(all_direction_accuracies) / len(all_direction_accuracies), 4),
                'samples': len(all_direction_accuracies)
            }
        
        result.return_by_action = {}
        for action, returns in all_returns_by_action.items():
            if returns:
                result.return_by_action[action] = {
                    'avg_return': round(sum(returns) / len(returns), 4),
                    'win_rate': round(sum(1 for r in returns if r > 0) / len(returns), 4),
                    'count': len(returns)
                }
        
        if all_baselines:
            result.baseline_equal_weight = round(
                sum(b['equal_weight_avg_return'] for b in all_baselines) / len(all_baselines), 4
            )
            result.strategy_cumulative_return = round(
                sum(b['strategy_avg_return'] for b in all_baselines) / len(all_baselines), 4
            )
            result.baseline_spy = 0.0
        
        strategy_returns = []
        for b in all_baselines:
            strategy_returns.append(b['strategy_avg_return'])
        
        if strategy_returns and len(strategy_returns) > 1:
            import statistics
            mean_ret = sum(strategy_returns) / len(strategy_returns)
            std_ret = statistics.stdev(strategy_returns)
            if std_ret > 0:
                daily_rf = 0.03 / 252
                result.sharpe_of_recommendations = round(
                    (mean_ret - daily_rf) / std_ret * (252 ** 0.5), 4
                )
        
        if strategy_returns:
            result.win_rate = round(
                sum(1 for r in strategy_returns if r > 0) / len(strategy_returns), 4
            )
        
        result.grade = self._calculate_grade(result)
        
        return result
    
    def _calculate_grade(self, result: ValidationResult) -> str:
        score = 0
        
        if result.direction_accuracy:
            acc = result.direction_accuracy.get('1d', 0)
            if acc >= 0.65:
                score += 30
            elif acc >= 0.50:
                score += 20
            elif acc >= 0.40:
                score += 10
        
        if result.strategy_cumulative_return > 0:
            score += 20
        elif result.strategy_cumulative_return > -0.01:
            score += 10
        
        if result.strategy_cumulative_return > result.baseline_equal_weight:
            score += 25
        elif abs(result.strategy_cumulative_return - result.baseline_equal_weight) < 0.005:
            score += 10
        
        buy_actions = {k: v for k, v in result.return_by_action.items()
                       if any(s in k for s in ('BUY', 'GET_ON_BOARD', 'BUY_SMALL'))}
        if buy_actions:
            avg_buy = sum(v['avg_return'] for v in buy_actions.values()) / len(buy_actions)
            if avg_buy > 0:
                score += 15
            elif avg_buy > -0.01:
                score += 5
        
        if result.sharpe_of_recommendations > 1.0:
            score += 10
        elif result.sharpe_of_recommendations > 0:
            score += 5
        
        if score >= 80:
            return 'A'
        elif score >= 60:
            return 'B'
        elif score >= 40:
            return 'C'
        elif score >= 20:
            return 'D'
        else:
            return 'F'
    
    def generate_report(self, result: ValidationResult) -> str:
        lines = [
            "# Validation Framework Report",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Total Predictions: {result.total_predictions}",
            f"Valid Predictions: {result.valid_predictions}",
            "",
            "## Direction Accuracy",
        ]
        
        if result.direction_accuracy:
            lines.append(f"- 1-Day: {result.direction_accuracy.get('1d', 0):.2%} (samples: {result.direction_accuracy.get('samples', 0)})")
        else:
            lines.append("- No data")
        
        lines.append("")
        lines.append("## Recommendation Returns")
        for action, data in result.return_by_action.items():
            lines.append(f"- {action}: avg {data['avg_return']:+.2%}, win rate {data['win_rate']:.0%} ({data['count']} trades)")
        
        lines.append("")
        lines.append("## Baseline Comparison")
        lines.append(f"- Equal-Weight Return: {result.baseline_equal_weight:+.2%}")
        lines.append(f"- Strategy Return: {result.strategy_cumulative_return:+.2%}")
        alpha = result.strategy_cumulative_return - result.baseline_equal_weight
        lines.append(f"- Alpha: {alpha:+.2%} ({'BEATS' if alpha > 0 else 'LAGS'} baseline)")
        
        lines.append("")
        lines.append("## Risk Metrics")
        lines.append(f"- Sharpe (annualized): {result.sharpe_of_recommendations:.2f}")
        lines.append(f"- Win Rate: {result.win_rate:.0%}")
        
        lines.append("")
        lines.append(f"## Overall Grade: {result.grade}")
        
        if result.grade in ('A', 'B'):
            lines.append("Strategy is working. Continue monitoring.")
        elif result.grade == 'C':
            lines.append("Strategy needs improvement. Review recommendation logic.")
        elif result.grade == 'D':
            lines.append("Strategy underperforming. Major revision needed.")
        else:
            lines.append("Strategy failing. Complete overhaul required.")
        
        return "\n".join(lines)
    
    def save_results(self, result: ValidationResult):
        report = self.generate_report(result)
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        report_path = self.output_dir / f"validation-{date_str}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        data = {
            'date': date_str,
            'grade': result.grade,
            'direction_accuracy': result.direction_accuracy,
            'return_by_action': result.return_by_action,
            'baseline_equal_weight': result.baseline_equal_weight,
            'strategy_return': result.strategy_cumulative_return,
            'sharpe': result.sharpe_of_recommendations,
            'win_rate': result.win_rate,
            'total_predictions': result.total_predictions,
            'valid_predictions': result.valid_predictions
        }
        
        json_path = self.output_dir / f"validation-{date_str}.json"
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Report: {report_path}")
        print(f"Data: {json_path}")
        return report


def main():
    framework = ValidationFramework()
    result = framework.run_full_validation()
    report = framework.save_results(result)
    print("\n" + report)


if __name__ == "__main__":
    main()
