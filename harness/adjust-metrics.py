#!/usr/bin/env python3
"""
Adjust tracking metrics based on historical performance.
This script analyzes backtest results and suggests adjustments to improve accuracy.
"""

import os
import sys
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class MetricsAdjuster:
    def __init__(self, config_path=None):
        """Initialize metrics adjuster."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config = self.load_config(config_path)
        self.data_dir = Path(__file__).parent / self.config['data_dir']
        self.metrics_dir = self.data_dir / self.config['metrics_dir']
        self.backtests_dir = self.data_dir / self.config['backtests_dir']
        
        # Load cumulative metrics
        self.cumulative_metrics = self.load_cumulative_metrics()
        
        # Load weights from config thresholds (aligns with backtest)
        backtest_thresholds = self.config.get('backtest', {}).get('thresholds', {})
        self.metrics_weights = {
            'price_direction': backtest_thresholds.get('price_direction_accuracy', 0.6) * 0.5 + 0.1,
            'target_price': backtest_thresholds.get('target_price_accuracy', 0.3) * 0.5 + 0.15,
            'recommendation': backtest_thresholds.get('recommendation_accuracy', 0.7) * 0.5 + 0.05
        }
        # Normalize weights to sum to 1.0
        total = sum(self.metrics_weights.values())
        if total > 0:
            self.metrics_weights = {k: v / total for k, v in self.metrics_weights.items()}
    
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
    
    def load_cumulative_metrics(self):
        """Load cumulative metrics from file."""
        metrics_file = self.metrics_dir / "cumulative_metrics.json"
        if not metrics_file.exists():
            return None
        
        try:
            with open(metrics_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {metrics_file}")
            return None
    
    def analyze_performance_trends(self):
        """Analyze performance trends over time."""
        if not self.cumulative_metrics:
            print("No cumulative metrics found. Run backtests first.")
            return None
        
        history = self.cumulative_metrics.get('backtest_history', [])
        if len(history) < 5:
            print(f"Insufficient history ({len(history)} backtests). Need at least 5.")
            return None
        
        # Calculate trends for each metric
        trends = {}
        metrics_to_check = ['price_direction_accuracy', 'target_price_accuracy']
        
        for metric in metrics_to_check:
            values = [h['metrics'].get(metric, 0) for h in history]
            if len(values) >= 2:
                # Simple linear trend: (last - first) / first
                first_avg = sum(values[:3]) / 3 if len(values) >= 3 else values[0]
                last_avg = sum(values[-3:]) / 3 if len(values) >= 3 else values[-1]
                
                if first_avg > 0:
                    trend_pct = (last_avg - first_avg) / first_avg
                else:
                    trend_pct = 0
                
                trends[metric] = {
                    'first_avg': first_avg,
                    'last_avg': last_avg,
                    'trend_pct': trend_pct,
                    'trend': 'improving' if trend_pct > 0.05 else 'declining' if trend_pct < -0.05 else 'stable'
                }
        
        return trends
    
    def identify_poor_performers(self):
        """Identify metrics that are performing poorly."""
        if not self.cumulative_metrics:
            return []
        
        avg_accuracy = self.cumulative_metrics.get('average_accuracy', {})
        thresholds = self.config.get('backtest', {}).get('thresholds', {})
        
        poor_performers = []
        
        # Map metric names
        metric_map = {
            'price_direction': 'price_direction_accuracy',
            'target_price': 'target_price_accuracy'
        }
        
        for metric_name, config_name in metric_map.items():
            accuracy = avg_accuracy.get(metric_name, 0)
            threshold = thresholds.get(config_name, 0.5)
            
            if accuracy < threshold:
                poor_performers.append({
                    'metric': metric_name,
                    'accuracy': accuracy,
                    'threshold': threshold,
                    'deficit': threshold - accuracy
                })
        
        return poor_performers
    
    def generate_adjustment_suggestions(self):
        """Generate suggestions for adjusting tracking metrics."""
        print("Analyzing performance data...")
        
        trends = self.analyze_performance_trends()
        poor_performers = self.identify_poor_performers()
        
        suggestions = []
        
        # Suggestion 1: Adjust weights based on performance
        if poor_performers:
            for performer in poor_performers:
                metric = performer['metric']
                accuracy = performer['accuracy']
                threshold = performer['threshold']
                
                suggestion = {
                    'type': 'weight_adjustment',
                    'metric': metric,
                    'current_weight': self.metrics_weights.get(metric, 0.1),
                    'suggested_weight': self.metrics_weights.get(metric, 0.1) * 0.8,  # Reduce weight
                    'reason': f"Accuracy ({accuracy:.2%}) below threshold ({threshold:.2%})",
                    'priority': 'high' if performer['deficit'] > 0.2 else 'medium'
                }
                suggestions.append(suggestion)
        
        # Suggestion 2: Add new metrics if trends are declining
        if trends:
            for metric_name, trend_info in trends.items():
                if trend_info['trend'] == 'declining':
                    suggestion = {
                        'type': 'add_metric',
                        'suggested_metric': self.get_complementary_metric(metric_name),
                        'reason': f"{metric_name} showing declining trend ({trend_info['trend_pct']:.2%})",
                        'priority': 'medium'
                    }
                    suggestions.append(suggestion)
        
        # Suggestion 3: Remove consistently poor performers
        if self.cumulative_metrics and len(self.cumulative_metrics.get('backtest_history', [])) >= 10:
            consistently_poor = []
            for metric in ['price_direction', 'target_price']:
                accuracies = [h['metrics'].get(f"{metric}_accuracy", 0) 
                             for h in self.cumulative_metrics['backtest_history'][-10:]]
                avg_last_10 = sum(accuracies) / len(accuracies) if accuracies else 0
                
                if avg_last_10 < 0.4:  # Very poor performance
                    consistently_poor.append(metric)
            
            for metric in consistently_poor:
                suggestion = {
                    'type': 'remove_metric',
                    'metric': metric,
                    'reason': f"Consistently poor performance (last 10 avg: {avg_last_10:.2%})",
                    'priority': 'high'
                }
                suggestions.append(suggestion)
        
        # Suggestion 4: Adjust thresholds
        if poor_performers and len(poor_performers) >= 3:
            suggestion = {
                'type': 'adjust_threshold',
                'current_thresholds': self.config.get('backtest', {}).get('thresholds', {}),
                'suggested_adjustment': 'Increase thresholds for better filtering',
                'reason': f"{len(poor_performers)} metrics consistently below threshold",
                'priority': 'medium'
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def get_complementary_metric(self, metric_name):
        """Get complementary metric for a given metric."""
        complementary_map = {
            'price_direction_accuracy': ['volume_analysis', 'rsi', 'macd'],
            'target_price_accuracy': ['value_zones', 'gap_analysis'],
            'recommendation_accuracy': ['market_sentiment', 'volume_analysis']
        }
        
        return complementary_map.get(metric_name, ['market_sentiment'])[0]
    
    def apply_adjustments(self, suggestions):
        """Apply selected adjustments to configuration."""
        if not suggestions:
            print("No adjustments to apply.")
            return
        
        print("\nApplying adjustments...")
        
        config_file = Path(__file__).parent / "config.yaml"
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
        except Exception:
            config = {}
        
        weight_adjustments = [s for s in suggestions if s['type'] == 'weight_adjustment']
        for adj in weight_adjustments:
            metric = adj['metric']
            new_weight = adj['suggested_weight']
            
            self.metrics_weights[metric] = new_weight
            print(f"  - Adjusted weight for {metric}: {adj['current_weight']:.2f} -> {new_weight:.2f}")
        
        weights_file = self.metrics_dir / "metric_weights.json"
        with open(weights_file, 'w') as f:
            json.dump(self.metrics_weights, f, indent=2)
        
        print(f"\nUpdated metric weights saved to: {weights_file}")
        
        if weight_adjustments and config:
            if 'adjustment' not in config:
                config['adjustment'] = {}
            config['adjustment']['metric_weights'] = self.metrics_weights
            try:
                with open(config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                print(f"Config updated: {config_file}")
            except Exception as e:
                print(f"Warning: Could not update config.yaml: {e}")
        
        adjustment_log = self.metrics_dir / "adjustments_applied.json"
        log_entry = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'suggestions_applied': suggestions,
            'new_weights': self.metrics_weights
        }
        
        if adjustment_log.exists():
            with open(adjustment_log, 'r') as f:
                log = json.load(f)
        else:
            log = {'adjustment_history': []}
        
        log['adjustment_history'].append(log_entry)
        
        with open(adjustment_log, 'w') as f:
            json.dump(log, f, indent=2)
        
        print(f"Adjustment logged to: {adjustment_log}")
    
    def run(self, apply=False):
        """Run metrics adjustment analysis."""
        print("="*60)
        print("METRICS ADJUSTMENT ANALYSIS")
        print("="*60)
        
        # Check if we have enough data
        if not self.cumulative_metrics:
            print("❌ No cumulative metrics found.")
            print("Run backtests for at least 5 days before adjusting metrics.")
            return
        
        history_len = len(self.cumulative_metrics.get('backtest_history', []))
        print(f"Backtest history: {history_len} days")
        
        if history_len < 5:
            print(f"⚠️  Insufficient data. Need at least 5 backtests, have {history_len}.")
            print("Continue running daily backtests to gather more data.")
            return
        
        # Generate suggestions
        suggestions = self.generate_adjustment_suggestions()
        
        if not suggestions:
            print("\n✅ All metrics performing well. No adjustments needed.")
            return
        
        print(f"\n📋 Generated {len(suggestions)} adjustment suggestions:")
        print("-"*60)
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion['type'].replace('_', ' ').title()}")
            print(f"   Metric: {suggestion.get('metric', suggestion.get('suggested_metric', 'N/A'))}")
            print(f"   Reason: {suggestion['reason']}")
            print(f"   Priority: {suggestion['priority'].upper()}")
            
            if 'current_weight' in suggestion:
                print(f"   Current weight: {suggestion['current_weight']:.2f}")
                print(f"   Suggested weight: {suggestion['suggested_weight']:.2f}")
        
        print("\n" + "="*60)
        
        if apply:
            print("\nApplying adjustments automatically...")
            self.apply_adjustments(suggestions)
        else:
            print("\nTo apply these adjustments automatically, run:")
            print("  python adjust-metrics.py --apply")
            print("\nOr manually update your analysis methods based on these suggestions.")
        
        return suggestions

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Adjust tracking metrics based on performance')
    parser.add_argument('--apply', action='store_true', help='Apply adjustments automatically')
    parser.add_argument('--config', help='Path to config file')
    
    args = parser.parse_args()
    
    adjuster = MetricsAdjuster(args.config)
    adjuster.run(apply=args.apply)

if __name__ == "__main__":
    main()