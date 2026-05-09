#!/usr/bin/env python3
"""
Backtest script to compare predictions vs actual performance.
Run this script at 9:30 AM Beijing Time to evaluate yesterday's predictions vs yesterday's actual US market performance.
"""

import os
import sys
import json
import yaml
import glob
from datetime import datetime, timedelta
from pathlib import Path

# Standardized import path
SKILL_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(SKILL_DIR))

from watchlist_utils import load_watchlist


class Backtest:
    def __init__(self, config_path=None):
        """Initialize backtest with configuration."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config = self.load_config(config_path)
        self.data_dir = Path(__file__).parent / self.config['data_dir']
        self.predictions_dir = self.data_dir / self.config['predictions_dir']
        self.daily_reports_dir = self.data_dir / self.config['daily_reports_dir']
        self.backtests_dir = self.data_dir / self.config['backtests_dir']
        self.metrics_dir = self.data_dir / self.config['metrics_dir']
        
        # Create directories if they don't exist
        self.backtests_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        config_watchlist = self.config.get('watchlist', [])
        self.watchlist = config_watchlist if config_watchlist else load_watchlist()
    
    def load_config(self, config_path):
        """Load YAML configuration file."""
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except ImportError:
            print("Warning: PyYAML not installed, using default config")
            return {}
        except FileNotFoundError:
            print(f"Config file not found: {config_path}, using defaults")
            return {}
    
    def get_yesterday_date(self):
        """Get yesterday's date in YYYY-MM-DD format."""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    def get_today_date(self):
        """Get today's date in YYYY-MM-DD format."""
        return datetime.now().strftime('%Y-%m-%d')
    
    def load_prediction(self, date):
        """Load prediction file for given date."""
        prediction_file = self.predictions_dir / f"prediction-{date}.json"
        if not prediction_file.exists():
            return None
        
        try:
            with open(prediction_file, 'r') as f:
                data = json.load(f)
                data['_source_file'] = str(prediction_file)
                return data
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {prediction_file}")
            return None
    
    def load_actual_quotes(self, date):
        """Load actual quotes for given date. Supports both list and dict formats."""
        for dirname in [self.daily_reports_dir, self.data_dir / 'daily']:
            quotes_file = dirname / f"quotes-{date}.json"
            if quotes_file.exists():
                try:
                    with open(quotes_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'quotes' in data:
                            return data['quotes']
                        if isinstance(data, list):
                            return data
                        return [data] if isinstance(data, dict) else data
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from {quotes_file}")
                    continue
        return None
    
    def _extract_actual_direction(self, actual_quote):
        """Extract actual price direction from quote data. Returns 'up', 'down', 'neutral', or None."""
        change_rate = actual_quote.get('change_rate')
        if change_rate is not None:
            try:
                change_rate = float(change_rate)
                return 'up' if change_rate > 0 else 'down' if change_rate < 0 else 'neutral'
            except (ValueError, TypeError):
                pass
        
        last_price = None
        prev_close_price = None
        
        for key in ('last', 'last_done', 'current_price'):
            if key in actual_quote and actual_quote[key] is not None:
                try:
                    last_price = float(actual_quote[key])
                    break
                except (ValueError, TypeError):
                    continue
        
        for key in ('prev_close', 'previous_close'):
            if key in actual_quote and actual_quote[key] is not None:
                try:
                    prev_close_price = float(actual_quote[key])
                    break
                except (ValueError, TypeError):
                    continue
        
        if last_price is not None and prev_close_price is not None and prev_close_price > 0:
            diff_pct = (last_price - prev_close_price) / prev_close_price
            if diff_pct > 0.005:
                return 'up'
            elif diff_pct < -0.005:
                return 'down'
            else:
                return 'neutral'
        
        return None
    
    def _normalize_direction(self, direction):
        """Normalize direction strings: 'uncertain'/'sideways' → 'neutral'."""
        if not direction:
            return None
        d = direction.lower().strip()
        if d in ('uncertain', 'sideways', 'flat', 'range'):
            return 'neutral'
        if d in ('up', 'bullish', 'positive'):
            return 'up'
        if d in ('down', 'bearish', 'negative'):
            return 'down'
        return d if d in ('up', 'down', 'neutral') else None
    
    def calculate_price_direction_accuracy(self, prediction, actual_quotes):
        """
        Calculate accuracy of price direction predictions.
        
        Args:
            prediction: Dict with 'watchlist_predictions' containing predicted_direction
            actual_quotes: List of quote dicts with 'last', 'prev_close', or 'change_rate'
        
        Returns:
            Accuracy score between 0.0 and 1.0
        """
        if not prediction or not actual_quotes:
            return 0.0
        
        correct = 0
        total = 0
        
        pred_items = prediction.get('watchlist_predictions', [])
        actual_dict = {}
        if isinstance(actual_quotes, list):
            for item in actual_quotes:
                sym = item.get('symbol')
                if sym:
                    actual_dict[sym] = item
        
        for pred in pred_items:
            symbol = pred.get('symbol')
            predicted_direction = self._normalize_direction(pred.get('predicted_direction', ''))
            
            if symbol in actual_dict and predicted_direction:
                actual_direction = self._extract_actual_direction(actual_dict[symbol])
                
                if actual_direction is None:
                    continue
                
                if predicted_direction == actual_direction:
                    correct += 1
                elif predicted_direction == 'neutral' and actual_direction != 'neutral':
                    pass
                elif actual_direction == 'neutral':
                    correct += 0.5
                
                total += 1
        
        return correct / total if total > 0 else 0.0
    
    def calculate_target_price_accuracy(self, prediction, actual_quotes):
        """
        Calculate accuracy of target price predictions.
        
        Uses wider 10% threshold (was 5%) to account for AI stock volatility.
        Also checks entry_price and stop_loss fields.

        Args:
            prediction: Dict with 'watchlist_predictions' containing target_price
            actual_quotes: List of quote dicts with 'last' or 'last_done'
        
        Returns:
            Accuracy score between 0.0 and 1.0
        """
        if not prediction or not actual_quotes:
            return 0.0
        
        within_threshold = 0
        total = 0
        
        pred_items = prediction.get('watchlist_predictions', [])
        actual_dict = {}
        if isinstance(actual_quotes, list):
            for item in actual_quotes:
                sym = item.get('symbol')
                if sym:
                    actual_dict[sym] = item
        
        for pred in pred_items:
            symbol = pred.get('symbol')
            
            target_price_str = pred.get('target_price')
            if target_price_str is None or target_price_str == '' or target_price_str == 'None':
                continue
            
            try:
                target_price = float(str(target_price_str).replace('$', '').replace(',', '').split('-')[0].strip())
            except (ValueError, TypeError):
                continue
            
            if target_price <= 0:
                continue
            
            if symbol in actual_dict:
                actual_quote = actual_dict[symbol]
                actual_price = None
                
                for key in ('last', 'last_done', 'current_price'):
                    if key in actual_quote and actual_quote[key] is not None:
                        try:
                            actual_price = float(actual_quote[key])
                            break
                        except (ValueError, TypeError):
                            continue
                
                if actual_price is not None and actual_price > 0:
                    diff_pct = abs(actual_price - target_price) / target_price
                    if diff_pct <= 0.10:
                        within_threshold += 1
                    total += 1
        
        return within_threshold / total if total > 0 else 0.0
    
    def calculate_recommendation_accuracy(self, prediction, actual_quotes):
        """
        Calculate accuracy of BUY/HOLD/SELL recommendations.
        
        A BUY/GET_ON_BOARD recommendation is correct if the stock went up.
        A SELL/AVOID recommendation is correct if the stock went down.
        A HOLD/WAIT/NEUTRAL recommendation is correct if the stock moved < 3% (widened from 2%).

        Args:
            prediction: Dict with 'watchlist_predictions' containing recommendation
            actual_quotes: List of quote dicts with price change data
            
        Returns:
            Accuracy score between 0.0 and 1.0
        """
        if not prediction or not actual_quotes:
            return 0.0
        
        correct = 0
        total = 0
        
        pred_items = prediction.get('watchlist_predictions', [])
        actual_dict = {}
        if isinstance(actual_quotes, list):
            for item in actual_quotes:
                sym = item.get('symbol')
                if sym:
                    actual_dict[sym] = item
        
        for pred in pred_items:
            symbol = pred.get('symbol')
            recommendation = pred.get('recommendation', 'HOLD').upper().strip()
            
            if symbol not in actual_dict:
                continue
            
            actual_quote = actual_dict[symbol]
            actual_direction = self._extract_actual_direction(actual_quote)
            
            if actual_direction is None:
                continue
            
            last_price = None
            prev_close_price = None
            
            for key in ('last', 'last_done', 'current_price'):
                if key in actual_quote and actual_quote[key] is not None:
                    try:
                        last_price = float(actual_quote[key])
                        break
                    except (ValueError, TypeError):
                        continue
            
            for key in ('prev_close', 'previous_close'):
                if key in actual_quote and actual_quote[key] is not None:
                    try:
                        prev_close_price = float(actual_quote[key])
                        break
                    except (ValueError, TypeError):
                        continue
            
            if last_price and prev_close_price and prev_close_price > 0:
                change_rate = (last_price - prev_close_price) / prev_close_price
            else:
                change_rate = 0.0
                if actual_direction == 'up':
                    change_rate = 0.01
                elif actual_direction == 'down':
                    change_rate = -0.01
            
            total += 1
            
            buy_signals = ('BUY', 'STRONG BUY', 'GET_ON_BOARD', 'BUY_SMALL')
            sell_signals = ('SELL', 'STRONG SELL', 'AVOID', 'REDUCE')
            hold_signals = ('HOLD', 'WEAK HOLD', 'NEUTRAL', 'WAIT')
            
            is_buy = any(s in recommendation for s in buy_signals)
            is_sell = any(s in recommendation for s in sell_signals)
            is_hold = any(s in recommendation for s in hold_signals)
            
            if is_buy and change_rate > 0:
                correct += 1
            elif is_sell and change_rate < 0:
                correct += 1
            elif is_hold and abs(change_rate) < 0.03:
                correct += 1
            elif is_hold and change_rate > 0:
                correct += 0.5
        
        return correct / total if total > 0 else 0.0
    
    def generate_backtest_report(self, prediction_date, actual_date):
        """Generate backtest report comparing predictions vs actual."""
        print(f"Running backtest for {prediction_date} predictions vs {actual_date} actual")
        
        prediction = self.load_prediction(prediction_date)
        actual_quotes = self.load_actual_quotes(actual_date)
        
        if not prediction:
            print(f"No prediction found for {prediction_date}")
            return None
        
        if not actual_quotes:
            print(f"No actual quotes found for {actual_date}")
            return None
        
        matched_symbols = set()
        if isinstance(actual_quotes, list):
            for q in actual_quotes:
                sym = q.get('symbol')
                if sym:
                    matched_symbols.add(sym)
        pred_symbols = set()
        for p in prediction.get('watchlist_predictions', []):
            sym = p.get('symbol')
            if sym:
                pred_symbols.add(sym)
        
        overlap = pred_symbols & matched_symbols
        if not overlap:
            print(f"WARNING: No symbol overlap! Pred: {pred_symbols}, Actual: {matched_symbols}")
        
        price_direction_acc = self.calculate_price_direction_accuracy(prediction, actual_quotes)
        target_price_acc = self.calculate_target_price_accuracy(prediction, actual_quotes)
        recommendation_acc = self.calculate_recommendation_accuracy(prediction, actual_quotes)
        
        report = {
            'backtest_date': self.get_today_date(),
            'prediction_date': prediction_date,
            'actual_date': actual_date,
            'symbols_matched': list(overlap),
            'symbols_in_prediction': list(pred_symbols),
            'symbols_in_actual': list(matched_symbols),
            'metrics': {
                'price_direction_accuracy': round(price_direction_acc, 4),
                'target_price_accuracy': round(target_price_acc, 4),
                'recommendation_accuracy': round(recommendation_acc, 4),
            },
            'thresholds': self.config.get('backtest', {}).get('thresholds', {}),
            'passed_thresholds': {
                'price_direction_accuracy': price_direction_acc >= self.config.get('backtest', {}).get('thresholds', {}).get('price_direction_accuracy', 0.6),
                'target_price_accuracy': target_price_acc >= self.config.get('backtest', {}).get('thresholds', {}).get('target_price_accuracy', 0.3),
                'recommendation_accuracy': recommendation_acc >= self.config.get('backtest', {}).get('thresholds', {}).get('recommendation_accuracy', 0.7),
            },
            'summary': 'Good' if price_direction_acc >= 0.6 else 'Needs Improvement'
        }
        
        report_file = self.backtests_dir / f"backtest-{prediction_date}-{actual_date}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Backtest report saved to: {report_file}")
        
        self.update_cumulative_metrics(report)
        
        return report
    
    def update_cumulative_metrics(self, report):
        """Update cumulative metrics file with latest backtest results. Skips duplicates."""
        metrics_file = self.metrics_dir / "cumulative_metrics.json"
        
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
        else:
            metrics = {
                'total_backtests': 0,
                'average_accuracy': {
                    'price_direction': 0.0,
                    'target_price': 0.0,
                    'recommendation': 0.0
                },
                'backtest_history': []
            }
        
        combo_key = f"{report['prediction_date']}->{report['actual_date']}"
        existing_keys = set()
        for h in metrics['backtest_history']:
            existing_keys.add(f"{h['prediction_date']}->{h['actual_date']}")
        
        if combo_key in existing_keys:
            print(f"Skipping duplicate: {combo_key}")
            return
        
        metrics['total_backtests'] += 1
        metrics['backtest_history'].append({
            'date': report['backtest_date'],
            'prediction_date': report['prediction_date'],
            'actual_date': report['actual_date'],
            'metrics': report['metrics']
        })
        
        history = metrics['backtest_history']
        if history:
            metrics['average_accuracy']['price_direction'] = round(sum(
                h['metrics']['price_direction_accuracy'] for h in history
            ) / len(history), 4)
            metrics['average_accuracy']['target_price'] = round(sum(
                h['metrics']['target_price_accuracy'] for h in history
            ) / len(history), 4)
            metrics['average_accuracy']['recommendation'] = round(sum(
                h['metrics'].get('recommendation_accuracy', 0) for h in history
            ) / len(history), 4)
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Cumulative metrics updated: {metrics_file}")
    
    def run(self):
        """Run backtest: compare prediction from date D vs actual from date D+1."""
        yesterday = self.get_yesterday_date()
        today = self.get_today_date()
        
        print(f"Running backtest: {yesterday} predictions vs {today} actual")
        
        report = self.generate_backtest_report(yesterday, today)
        
        if report:
            print("\n" + "="*50)
            print("BACKTEST RESULTS")
            print("="*50)
            print(f"Prediction Date: {report['prediction_date']}")
            print(f"Actual Date:     {report['actual_date']}")
            print(f"Symbols Matched: {report.get('symbols_matched', [])}")
            print(f"\nMetrics:")
            print(f"  Price Direction Accuracy: {report['metrics']['price_direction_accuracy']:.2%}")
            print(f"  Target Price Accuracy:    {report['metrics']['target_price_accuracy']:.2%}")
            print(f"  Recommendation Accuracy:  {report['metrics']['recommendation_accuracy']:.2%}")
            print(f"\nThreshold Checks:")
            print(f"  Price Direction: {'PASS' if report['passed_thresholds']['price_direction_accuracy'] else 'FAIL'}")
            print(f"  Target Price:    {'PASS' if report['passed_thresholds']['target_price_accuracy'] else 'FAIL'}")
            print(f"\nSummary: {report['summary']}")
            print("="*50)
            
            self.check_adjustment_needed(report)
            
            return report
        else:
            print("Backtest failed - insufficient data")
            return None
    
    def check_adjustment_needed(self, report):
        """Check if adjustment of tracking metrics is needed based on results."""
        thresholds = self.config.get('backtest', {}).get('thresholds', {})
        adjustment_config = self.config.get('adjustment', {})
        
        if not adjustment_config.get('enabled', False):
            return
        
        # Check if any metric is below threshold
        needs_adjustment = False
        for metric, threshold in thresholds.items():
            if metric in report['metrics']:
                if report['metrics'][metric] < threshold:
                    print(f"\n⚠️  {metric.replace('_', ' ').title()} below threshold ({report['metrics'][metric]:.2%} < {threshold:.2%})")
                    needs_adjustment = True
        
        if needs_adjustment:
            print("\nAdjustment may be needed for tracking metrics.")
            print("Consider running adjustment script or reviewing analysis methods.")
            
            # Log adjustment suggestion
            adjustment_log = self.metrics_dir / "adjustment_suggestions.json"
            suggestion = {
                'date': self.get_today_date(),
                'reason': 'Metrics below threshold',
                'suggested_actions': [
                    'Review prediction models',
                    'Adjust indicator weights',
                    'Add new technical indicators',
                    'Increase sample size before making changes'
                ]
            }
            
            if adjustment_log.exists():
                with open(adjustment_log, 'r') as f:
                    log = json.load(f)
            else:
                log = {'suggestions': []}
            
            log['suggestions'].append(suggestion)
            
            with open(adjustment_log, 'w') as f:
                json.dump(log, f, indent=2)

def main():
    """Main entry point."""
    backtest = Backtest()
    backtest.run()

if __name__ == "__main__":
    main()