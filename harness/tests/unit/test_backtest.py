#!/usr/bin/env python3
"""
Unit tests for backtest functionality.
Run with: pytest tests/unit/test_backtest.py -v
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Standardized import path
SKILL_DIR = Path(__file__).parent.parent.parent.parent.resolve()
sys.path.insert(0, str(SKILL_DIR))

from backtest import Backtest


class TestBacktest:
    """Test suite for Backtest class"""
    
    @pytest.fixture
    def backtest(self):
        """Create Backtest instance for testing"""
        return Backtest()
    
    @pytest.fixture
    def sample_prediction(self):
        """Sample prediction data"""
        return {
            "date": "2026-04-20",
            "prediction_date": "2026-04-21",
            "watchlist_predictions": [
                {
                    "symbol": "BABA.US",
                    "predicted_direction": "up",
                    "confidence": 0.7,
                    "target_price": "125.00",
                    "stop_loss": "115.00"
                },
                {
                    "symbol": "NVDA.US",
                    "predicted_direction": "up",
                    "confidence": 0.6,
                    "target_price": "185.00",
                    "stop_loss": "175.00"
                },
                {
                    "symbol": "TSLA.US",
                    "predicted_direction": "down",
                    "confidence": 0.5,
                    "target_price": "340.00",
                    "stop_loss": "350.00"
                }
            ]
        }
    
    @pytest.fixture
    def sample_actual_quotes(self):
        """Sample actual quotes"""
        return [
            {
                "symbol": "BABA.US",
                "last_done": "130.00",
                "previous_close": "120.00",
                "change": 10.00,
                "change_rate": 8.33
            },
            {
                "symbol": "NVDA.US",
                "last_done": "182.00",
                "previous_close": "180.00",
                "change": 2.00,
                "change_rate": 1.11
            },
            {
                "symbol": "TSLA.US",
                "last_done": "355.00",
                "previous_close": "350.00",
                "change": 5.00,
                "change_rate": 1.43
            }
        ]
    
    # ==========================================
    # Test: Price Direction Accuracy
    # ==========================================
    
    def test_price_direction_accuracy_correct_prediction(self, backtest, sample_prediction, sample_actual_quotes):
        """
        Test price direction accuracy with correct predictions
        
        Expected:
        - BABA.US: predicted up, actual up (+8.33%) -> Correct
        - NVDA.US: predicted up, actual up (+1.11%) -> Correct
        - TSLA.US: predicted down, actual up (+1.43%) -> Incorrect
        
        Accuracy: 2/3 = 66.67%
        """
        accuracy = backtest.calculate_price_direction_accuracy(
            sample_prediction,
            sample_actual_quotes
        )
        
        assert isinstance(accuracy, float), "Accuracy should be a float"
        assert 0.0 <= accuracy <= 1.0, "Accuracy should be between 0 and 1"
        assert accuracy == pytest.approx(0.6667, rel=0.01), f"Expected 66.67% accuracy, got {accuracy:.2%}"
    
    def test_price_direction_accuracy_all_correct(self, backtest, sample_actual_quotes):
        """Test with all correct predictions"""
        prediction = {
            "watchlist_predictions": [
                {"symbol": "BABA.US", "predicted_direction": "up"},
                {"symbol": "NVDA.US", "predicted_direction": "up"},
                {"symbol": "TSLA.US", "predicted_direction": "up"}
            ]
        }
        
        accuracy = backtest.calculate_price_direction_accuracy(prediction, sample_actual_quotes)
        
        assert accuracy == 1.0, "All predictions correct should give 100% accuracy"
    
    def test_price_direction_accuracy_all_incorrect(self, backtest, sample_actual_quotes):
        """Test with all incorrect predictions"""
        prediction = {
            "watchlist_predictions": [
                {"symbol": "BABA.US", "predicted_direction": "down"},
                {"symbol": "NVDA.US", "predicted_direction": "down"},
                {"symbol": "TSLA.US", "predicted_direction": "down"}
            ]
        }
        
        accuracy = backtest.calculate_price_direction_accuracy(prediction, sample_actual_quotes)
        
        assert accuracy == 0.0, "All predictions incorrect should give 0% accuracy"
    
    def test_price_direction_accuracy_empty_prediction(self, backtest):
        """Test with empty prediction"""
        accuracy = backtest.calculate_price_direction_accuracy(None, [])
        
        assert accuracy == 0.0, "Empty prediction should return 0.0"
    
    def test_price_direction_accuracy_missing_symbols(self, backtest):
        """Test with symbols in prediction but not in actual quotes"""
        prediction = {
            "watchlist_predictions": [
                {"symbol": "AAPL.US", "predicted_direction": "up"},
                {"symbol": "MSFT.US", "predicted_direction": "up"}
            ]
        }
        actual_quotes = [
            {"symbol": "BABA.US", "last_done": "130", "change": 1.0}
        ]
        
        accuracy = backtest.calculate_price_direction_accuracy(prediction, actual_quotes)
        
        # Should handle gracefully (no matches)
        assert isinstance(accuracy, float)
    
    # ==========================================
    # Test: Target Price Accuracy
    # ==========================================
    
    def test_target_price_accuracy_within_threshold(self, backtest, sample_prediction, sample_actual_quotes):
        """
        Test target price accuracy with prices within 5% threshold
        
        Expected:
        - BABA.US: target $125, actual $130 -> 4% off -> Within threshold
        - NVDA.US: target $185, actual $182 -> 1.6% off -> Within threshold
        - TSLA.US: target $340, actual $355 -> 4.4% off -> Within threshold
        
        Accuracy: 3/3 = 100%
        """
        accuracy = backtest.calculate_target_price_accuracy(
            sample_prediction,
            sample_actual_quotes
        )
        
        assert isinstance(accuracy, float), "Accuracy should be a float"
        assert 0.0 <= accuracy <= 1.0, "Accuracy should be between 0 and 1"
        assert accuracy >= 0.9, f"Expected high accuracy (>90%), got {accuracy:.2%}"
    
    def test_target_price_accuracy_outside_threshold(self, backtest):
        """Test with target prices far from actual"""
        prediction = {
            "watchlist_predictions": [
                {"symbol": "BABA.US", "target_price": "100.00"},  # Actual: $130
                {"symbol": "NVDA.US", "target_price": "150.00"}   # Actual: $182
            ]
        }
        actual_quotes = [
            {"symbol": "BABA.US", "last_done": "130.00"},
            {"symbol": "NVDA.US", "last_done": "182.00"}
        ]
        
        accuracy = backtest.calculate_target_price_accuracy(prediction, actual_quotes)
        
        assert accuracy < 0.5, f"Expected low accuracy (<50%), got {accuracy:.2%}"
    
    def test_target_price_accuracy_invalid_target(self, backtest):
        """Test with invalid target price values"""
        prediction = {
            "watchlist_predictions": [
                {"symbol": "BABA.US", "target_price": "invalid"},
                {"symbol": "NVDA.US", "target_price": None},
                {"symbol": "TSLA.US", "target_price": ""}
            ]
        }
        actual_quotes = [
            {"symbol": "BABA.US", "last_done": "130.00"},
            {"symbol": "NVDA.US", "last_done": "182.00"},
            {"symbol": "TSLA.US", "last_done": "355.00"}
        ]
        
        # Should handle invalid values gracefully
        accuracy = backtest.calculate_target_price_accuracy(prediction, actual_quotes)
        
        assert isinstance(accuracy, float)
    
    # ==========================================
    # Test: Backtest Report Generation
    # ==========================================
    
    def test_generate_backtest_report(self, backtest, sample_prediction, sample_actual_quotes):
        """Test backtest report generation"""
        report = backtest.generate_backtest_report(
            "2026-04-20",
            "2026-04-21"
        )
        
        assert report is not None
        assert 'backtest_date' in report
        assert 'prediction_date' in report
        assert 'actual_date' in report
        assert 'metrics' in report
        assert 'passed_thresholds' in report
    
    # ==========================================
    # Test: Cumulative Metrics
    # ==========================================
    
    def test_update_cumulative_metrics(self, backtest, tmp_path):
        """Test updating cumulative metrics"""
        # Create temporary metrics file
        metrics_file = tmp_path / "cumulative_metrics.json"
        backtest.metrics_dir = tmp_path
        backtest.cumulative_metrics_file = metrics_file
        
        report = {
            'backtest_date': '2026-04-21',
            'prediction_date': '2026-04-20',
            'actual_date': '2026-04-20',
            'metrics': {
                'price_direction_accuracy': 0.7,
                'target_price_accuracy': 0.4
            }
        }
        
        backtest.update_cumulative_metrics(report)
        
        # Verify metrics file updated
        assert metrics_file.exists()
        
        import json
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        assert metrics['total_backtests'] == 1
        assert len(metrics['backtest_history']) == 1
        assert metrics['backtest_history'][0]['date'] == '2026-04-21'
    
    def test_cumulative_metrics_averages(self, backtest, tmp_path):
        """Test that cumulative averages are calculated correctly"""
        metrics_file = tmp_path / "cumulative_metrics.json"
        backtest.metrics_dir = tmp_path
        backtest.cumulative_metrics_file = metrics_file
        
        # Add first backtest
        report1 = {
            'backtest_date': '2026-04-20',
            'prediction_date': '2026-04-19',
            'actual_date': '2026-04-19',
            'metrics': {
                'price_direction_accuracy': 0.6,
                'target_price_accuracy': 0.3
            }
        }
        backtest.update_cumulative_metrics(report1)
        
        # Add second backtest
        report2 = {
            'backtest_date': '2026-04-21',
            'prediction_date': '2026-04-20',
            'actual_date': '2026-04-20',
            'metrics': {
                'price_direction_accuracy': 0.8,
                'target_price_accuracy': 0.5
            }
        }
        backtest.update_cumulative_metrics(report2)
        
        # Check averages
        import json
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        expected_price_direction_avg = (0.6 + 0.8) / 2
        assert metrics['average_accuracy']['price_direction'] == pytest.approx(
            expected_price_direction_avg, rel=0.01
        )


class TestBacktestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def backtest(self):
        return Backtest()
    
    def test_missing_actual_quote_field(self, backtest):
        """Test when actual quote is missing required field"""
        prediction = {
            "watchlist_predictions": [
                {"symbol": "BABA.US", "predicted_direction": "up", "target_price": "125"}
            ]
        }
        actual_quotes = [
            {"symbol": "BABA.US"}  # Missing last_done
        ]
        
        # Should handle gracefully
        accuracy = backtest.calculate_target_price_accuracy(prediction, actual_quotes)
        
        # Should not crash
        assert isinstance(accuracy, float)
    
    def test_extreme_price_movements(self, backtest):
        """Test with extreme price movements (e.g., +100%, -50%)"""
        prediction = {
            "watchlist_predictions": [
                {"symbol": "BABA.US", "predicted_direction": "up", "target_price": "240"}
            ]
        }
        actual_quotes = [
            {
                "symbol": "BABA.US",
                "last_done": "240",
                "previous_close": "120",
                "change": 120,
                "change_rate": 100.0  # +100%
            }
        ]
        
        accuracy = backtest.calculate_price_direction_accuracy(prediction, actual_quotes)
        
        assert accuracy == 1.0  # Correctly predicted up
    
    def test_zero_prices(self, backtest):
        """Test with zero prices (edge case)"""
        prediction = {
            "watchlist_predictions": [
                {"symbol": "BABA.US", "target_price": "0"}
            ]
        }
        actual_quotes = [
            {"symbol": "BABA.US", "last_done": "0"}
        ]
        
        # Should handle division by zero
        accuracy = backtest.calculate_target_price_accuracy(prediction, actual_quotes)
        
        # Should not crash
        assert isinstance(accuracy, float)


class TestBacktestIntegration:
    """Integration tests for backtest workflow"""
    
    def test_full_backtest_workflow(self, tmp_path):
        """Test complete backtest workflow from prediction to metrics"""
        # This test would require mocking longbridge CLI
        # For now, it's a placeholder for future implementation
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
