#!/usr/bin/env python3
"""
Value Assessment Backtest

Validates value assessment framework over time.

Instead of checking "did we predict the direction correctly?" (speculation),
we validate:
1. Did our core value estimate make sense? (valuation accuracy)
2. Did stocks we rated as 'undervalued' outperform those rated 'overvalued'?
3. Did our safety margins protect us from downside?
4. Did we avoid value traps?

This is INVESTMENT validation, not TRADING validation.
"""

import os
import sys
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class ValueBacktest:
    """Backtest value assessment framework."""
    
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config = self.load_config(config_path)
        self.data_dir = Path(__file__).parent / self.config.get('data_dir', 'data')
        self.predictions_dir = self.data_dir / self.config.get('predictions_dir', 'predictions')
        self.daily_reports_dir = self.data_dir / self.config.get('daily_reports_dir', 'daily')
        self.backtests_dir = self.data_dir / self.config.get('backtests_dir', 'backtests')
        self.metrics_dir = self.data_dir / self.config.get('metrics_dir', 'metrics')
        
        self.backtests_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self, config_path):
        try:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except (ImportError, FileNotFoundError):
            return {}
    
    def get_yesterday_date(self):
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    def get_today_date(self):
        return datetime.now().strftime('%Y-%m-%d')
    
    def load_assessment(self, date):
        """Load value assessment file for given date."""
        # Try new format first
        assessment_file = self.predictions_dir / f"assessment-{date}.json"
        if not assessment_file.exists():
            # Fallback to prediction format
            assessment_file = self.predictions_dir / f"prediction-{date}.json"
        
        if not assessment_file.exists():
            return None
        
        try:
            with open(assessment_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {assessment_file}")
            return None
    
    def load_actual_quotes(self, date):
        """Load actual quotes for given date."""
        quotes_file = self.daily_reports_dir / f"quotes-{date}.json"
        if not quotes_file.exists():
            return None
        
        try:
            with open(quotes_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    
    def calculate_value_assessment_accuracy(self, assessment, actual_quotes):
        """
        Validate value assessment accuracy.
        
        Returns dict with:
        - valuation_bias: Did we systematically over/under-value?
        - action_effectiveness: Did our actions (BUY/WAIT) match outcomes?
        - safety_margin_effectiveness: Did safety margins protect from losses?
        - value_trap_detection: Did we correctly flag traps?
        """
        if not assessment or not actual_quotes:
            return None
        
        # Build actual prices dict
        actual_dict = {}
        if isinstance(actual_quotes, list):
            for q in actual_quotes:
                symbol = q.get('symbol')
                if symbol:
                    actual_dict[symbol] = {
                        'price': float(q.get('last') or q.get('last_done', 0)),
                        'prev_close': float(q.get('prev_close') or q.get('previous_close', 0)),
                    }
        
        assessments = assessment.get('watchlist_assessments', 
                                    assessment.get('watchlist_predictions', []))
        
        results = {
            'total': 0,
            'valuation_bias': [],  # (core_value - actual_price) / actual_price
            'action_outcomes': {'GET_ON_BOARD': [], 'BUY': [], 'BUY_SMALL': [], 
                              'HOLD': [], 'WAIT': [], 'AVOID': []},
            'safety_margin_protection': [],
            'value_trap_flagged_correctly': [],
            'undervalued_outperformance': [],
            'overvalued_underperformance': [],
        }
        
        for item in assessments:
            symbol = item.get('symbol')
            if symbol not in actual_dict:
                continue
            
            actual_price = actual_dict[symbol]['price']
            prev_close = actual_dict[symbol]['prev_close']
            actual_return = (actual_price - prev_close) / prev_close if prev_close > 0 else 0
            
            # Get core value and deviation
            core_value = item.get('core_value')
            deviation_pct = item.get('deviation_pct', 0)
            action = item.get('action', 'HOLD')
            
            if core_value and actual_price > 0:
                # Valuation bias: (core_value - actual_price) / actual_price
                # Positive = we think it's worth more than price (undervalued)
                bias = (core_value - actual_price) / actual_price
                results['valuation_bias'].append({
                    'symbol': symbol,
                    'bias': bias,
                    'deviation': deviation_pct,
                    'actual_return': actual_return,
                })
            
            # Action outcome tracking
            if action in results['action_outcomes']:
                results['action_outcomes'][action].append({
                    'symbol': symbol,
                    'actual_return': actual_return,
                    'deviation': deviation_pct,
                })
            
            results['total'] += 1
        
        # Calculate metrics
        metrics = self._calculate_metrics(results)
        return metrics
    
    def _calculate_metrics(self, results):
        """Calculate composite metrics from results."""
        metrics = {}
        
        # 1. Valuation Bias (are we too optimistic/pessimistic?)
        if results['valuation_bias']:
            biases = [r['bias'] for r in results['valuation_bias']]
            avg_bias = sum(biases) / len(biases)
            
            # Check if undervalued stocks actually outperformed
            undervalued = [r for r in results['valuation_bias'] if r['deviation'] < -10]
            overvalued = [r for r in results['valuation_bias'] if r['deviation'] > 10]
            
            if undervalued:
                avg_undervalued_return = sum(r['actual_return'] for r in undervalued) / len(undervalued)
            else:
                avg_undervalued_return = 0
            
            if overvalued:
                avg_overvalued_return = sum(r['actual_return'] for r in overvalued) / len(overvalued)
            else:
                avg_overvalued_return = 0
            
            # Value spread: did undervalued outperform overvalued?
            value_spread = avg_undervalued_return - avg_overvalued_return
            
            metrics['valuation'] = {
                'avg_bias': round(avg_bias, 3),
                'undervalued_count': len(undervalued),
                'overvalued_count': len(overvalued),
                'avg_undervalued_return': round(avg_undervalued_return, 4),
                'avg_overvalued_return': round(avg_overvalued_return, 4),
                'value_spread': round(value_spread, 4),
                'value_spread_positive': value_spread > 0,
            }
        
        # 2. Action Effectiveness
        action_metrics = {}
        for action, items in results['action_outcomes'].items():
            if items:
                avg_return = sum(i['actual_return'] for i in items) / len(items)
                action_metrics[action] = {
                    'count': len(items),
                    'avg_return': round(avg_return, 4),
                }
        metrics['action_effectiveness'] = action_metrics
        
        # 3. Overall Score
        # Good if:
        # - Value spread is positive (undervalued outperformed overvalued)
        # - BUY actions had positive returns
        # - AVOID actions had lower/negative returns
        
        score = 0
        score_breakdown = []
        
        if 'value_spread' in metrics.get('valuation', {}):
            vs = metrics['valuation']['value_spread']
            if vs > 0:
                score += 40
                score_breakdown.append(f"Value spread positive: +40")
            elif vs > -0.005:
                score += 20
                score_breakdown.append(f"Value spread neutral: +20")
            else:
                score_breakdown.append(f"Value spread negative: +0")
        
        buy_actions = (results['action_outcomes'].get('GET_ON_BOARD', []) + 
                      results['action_outcomes'].get('BUY', []) +
                      results['action_outcomes'].get('BUY_SMALL', []))
        if buy_actions:
            avg_buy_return = sum(i['actual_return'] for i in buy_actions) / len(buy_actions)
            if avg_buy_return > 0:
                score += 30
                score_breakdown.append(f"Buy actions positive: +30")
            elif avg_buy_return > -0.01:
                score += 15
                score_breakdown.append(f"Buy actions slightly negative: +15")
            else:
                score_breakdown.append(f"Buy actions negative: +0")
        
        avoid_actions = results['action_outcomes'].get('AVOID', [])
        if avoid_actions:
            avg_avoid_return = sum(i['actual_return'] for i in avoid_actions) / len(avoid_actions)
            if avg_avoid_return < 0:
                score += 30
                score_breakdown.append(f"Avoid actions correctly negative: +30")
            elif avg_avoid_return < 0.01:
                score += 15
                score_breakdown.append(f"Avoid actions near zero: +15")
            else:
                score_breakdown.append(f"Avoid actions positive (missed opportunity): +0")
        
        metrics['overall_score'] = score
        metrics['overall_score_breakdown'] = score_breakdown
        metrics['overall_grade'] = 'A' if score >= 80 else 'B' if score >= 60 else 'C' if score >= 40 else 'D'
        
        return metrics
    
    def generate_backtest_report(self, assessment_date, actual_date):
        """Generate value backtest report."""
        print(f"Running value backtest: {assessment_date} assessment vs {actual_date} actual")
        
        assessment = self.load_assessment(assessment_date)
        actual_quotes = self.load_actual_quotes(actual_date)
        
        if not assessment:
            print(f"No assessment found for {assessment_date}")
            return None
        
        if not actual_quotes:
            print(f"No actual quotes found for {actual_date}")
            return None
        
        metrics = self.calculate_value_assessment_accuracy(assessment, actual_quotes)
        
        if not metrics:
            print("Could not calculate metrics")
            return None
        
        report = {
            'backtest_date': self.get_today_date(),
            'assessment_date': assessment_date,
            'actual_date': actual_date,
            'metrics': metrics,
            'summary': f"Grade {metrics['overall_grade']} (Score: {metrics['overall_score']}/100)",
        }
        
        # Save report
        report_file = self.backtests_dir / f"value-backtest-{assessment_date}-{actual_date}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Value backtest report saved to: {report_file}")
        
        # Update cumulative metrics
        self.update_cumulative_metrics(report)
        
        return report
    
    def update_cumulative_metrics(self, report):
        """Update cumulative metrics."""
        metrics_file = self.metrics_dir / "cumulative_value_metrics.json"
        
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
        else:
            metrics = {
                'total_backtests': 0,
                'grade_distribution': {'A': 0, 'B': 0, 'C': 0, 'D': 0},
                'avg_value_spread': 0.0,
                'backtest_history': []
            }
        
        metrics['total_backtests'] += 1
        grade = report['metrics']['overall_grade']
        metrics['grade_distribution'][grade] = metrics['grade_distribution'].get(grade, 0) + 1
        
        # Track value spread
        val_metrics = report['metrics'].get('valuation', {})
        if 'value_spread' in val_metrics:
            history = metrics.get('backtest_history', [])
            if history:
                metrics['avg_value_spread'] = sum(
                    h['metrics'].get('valuation', {}).get('value_spread', 0) 
                    for h in history
                ) / len(history)
        
        metrics['backtest_history'].append({
            'date': report['backtest_date'],
            'assessment_date': report['assessment_date'],
            'grade': grade,
            'score': report['metrics']['overall_score'],
        })
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    def run(self):
        """Run backtest for yesterday's assessment vs today's actual."""
        yesterday = self.get_yesterday_date()
        today = self.get_today_date()
        
        print(f"Running value backtest: {yesterday} assessment vs {today} actual")
        
        report = self.generate_backtest_report(yesterday, today)
        
        if report:
            print("\n" + "="*60)
            print("VALUE BACKTEST RESULTS")
            print("="*60)
            print(f"Assessment Date: {report['assessment_date']}")
            print(f"Actual Date:     {report['actual_date']}")
            print(f"\nGrade: {report['metrics']['overall_grade']}")
            print(f"Score: {report['metrics']['overall_score']}/100")
            
            if 'valuation' in report['metrics']:
                val = report['metrics']['valuation']
                print(f"\nValuation Accuracy:")
                print(f"  Avg Bias: {val.get('avg_bias', 0):+.1%}")
                print(f"  Value Spread: {val.get('value_spread', 0):+.2%}")
                print(f"  Undervalued stocks avg return: {val.get('avg_undervalued_return', 0):+.2%}")
                print(f"  Overvalued stocks avg return: {val.get('avg_overvalued_return', 0):+.2%}")
                print(f"  Undervalued outperformed: {'✅ YES' if val.get('value_spread_positive') else '❌ NO'}")
            
            if 'action_effectiveness' in report['metrics']:
                print(f"\nAction Effectiveness:")
                for action, data in report['metrics']['action_effectiveness'].items():
                    print(f"  {action}: {data['count']} stocks, avg return {data['avg_return']:+.2%}")
            
            print(f"\nSummary: {report['summary']}")
            print("="*60)
            
            return report
        else:
            print("Backtest failed - insufficient data")
            return None


def main():
    backtest = ValueBacktest()
    backtest.run()


if __name__ == "__main__":
    main()
