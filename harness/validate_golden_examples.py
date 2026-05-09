#!/usr/bin/env python3
"""
Validate golden examples against expected outputs.
Run: python validate_golden_examples.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class GoldenExampleValidator:
    """Validate golden examples against expected behavior"""
    
    def __init__(self):
        self.scenarios_dir = Path(__file__).parent / "golden_examples" / "scenarios"
        self.results = []
    
    def load_scenario(self, scenario_file: Path) -> Dict:
        """Load a golden example scenario"""
        with open(scenario_file, 'r') as f:
            return json.load(f)
    
    def validate_scenario(self, scenario: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a golden example scenario.
        
        Returns:
            Tuple of (passed, issues)
        """
        issues = []
        passed = True
        
        # Validate required fields
        required_fields = [
            'scenario_name',
            'date',
            'stocks',
            'expected_outcomes'
        ]
        
        for field in required_fields:
            if field not in scenario:
                issues.append(f"Missing required field: {field}")
                passed = False
        
        # Validate stocks
        if 'stocks' in scenario:
            for i, stock in enumerate(scenario['stocks']):
                stock_issues = self._validate_stock(stock, i)
                issues.extend(stock_issues)
                if stock_issues:
                    passed = False
        
        # Validate expected outcomes
        if 'expected_outcomes' in scenario:
            outcome_issues = self._validate_outcomes(scenario['expected_outcomes'])
            issues.extend(outcome_issues)
            if outcome_issues:
                passed = False
        
        return passed, issues
    
    def _validate_stock(self, stock: Dict, index: int) -> List[str]:
        """Validate a stock entry"""
        issues = []
        
        required_stock_fields = [
            'symbol',
            'price',
            'expected_action',
            'expected_score_range'
        ]
        
        for field in required_stock_fields:
            if field not in stock:
                issues.append(f"Stock {index}: Missing field '{field}'")
        
        # Validate score range
        if 'expected_score_range' in stock:
            score_range = stock['expected_score_range']
            if not isinstance(score_range, list) or len(score_range) != 2:
                issues.append(f"Stock {index}: expected_score_range must be [min, max]")
            elif score_range[0] > score_range[1]:
                issues.append(f"Stock {index}: score_range min > max")
        
        # Validate RSI if present
        if 'rsi' in stock:
            rsi = stock['rsi']
            if not (0 <= rsi <= 100):
                issues.append(f"Stock {index}: RSI must be between 0 and 100, got {rsi}")
        
        # Validate price
        if 'price' in stock and stock['price'] <= 0:
            issues.append(f"Stock {index}: Price must be positive")
        
        return issues
    
    def _validate_outcomes(self, outcomes: Dict) -> List[str]:
        """Validate expected outcomes"""
        issues = []
        
        # Check for 14-day performance
        if '14_day_performance' in outcomes:
            for symbol, perf in outcomes['14_day_performance'].items():
                if 'expected_return' not in perf:
                    issues.append(f"Missing expected_return for {symbol}")
        
        # Check for strategy accuracy
        if 'strategy_accuracy' in outcomes:
            accuracy = outcomes['strategy_accuracy']
            if 'correct_predictions' not in accuracy:
                issues.append("Missing correct_predictions in strategy_accuracy")
            if 'total_predictions' not in accuracy:
                issues.append("Missing total_predictions in strategy_accuracy")
        
        return issues
    
    def run_validation(self) -> bool:
        """Run validation on all golden examples"""
        print("="*70)
        print("GOLDEN EXAMPLES VALIDATION")
        print("="*70)
        print()
        
        # Find all scenario files
        scenario_files = list(self.scenarios_dir.glob("*.json"))
        
        if not scenario_files:
            print("⚠️  No golden examples found!")
            print(f"   Expected location: {self.scenarios_dir}")
            return False
        
        print(f"Found {len(scenario_files)} scenario(s)")
        print()
        
        all_passed = True
        
        for scenario_file in scenario_files:
            print(f"Validating: {scenario_file.name}")
            print("-" * 70)
            
            try:
                scenario = self.load_scenario(scenario_file)
                passed, issues = self.validate_scenario(scenario)
                
                if passed:
                    print("  ✅ PASSED")
                    print(f"     Name: {scenario.get('scenario_name', 'N/A')}")
                    print(f"     Date: {scenario.get('date', 'N/A')}")
                    print(f"     Stocks: {len(scenario.get('stocks', []))}")
                else:
                    print("  ❌ FAILED")
                    all_passed = False
                    for issue in issues:
                        print(f"     - {issue}")
                
                # Store result
                self.results.append({
                    'file': scenario_file.name,
                    'passed': passed,
                    'issues': issues
                })
                
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON ERROR: {e}")
                all_passed = False
                self.results.append({
                    'file': scenario_file.name,
                    'passed': False,
                    'issues': [f"JSON decode error: {e}"]
                })
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                all_passed = False
                self.results.append({
                    'file': scenario_file.name,
                    'passed': False,
                    'issues': [f"Unexpected error: {e}"]
                })
            
            print()
        
        # Summary
        print("="*70)
        print("VALIDATION SUMMARY")
        print("="*70)
        
        passed_count = sum(1 for r in self.results if r['passed'])
        total_count = len(self.results)
        
        print(f"Total scenarios: {total_count}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {total_count - passed_count}")
        
        if all_passed:
            print()
            print("✅ All golden examples are valid!")
        else:
            print()
            print("❌ Some golden examples have issues. Please fix them.")
        
        return all_passed
    
    def generate_report(self) -> str:
        """Generate validation report"""
        report = f"""# Golden Examples Validation Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- Total scenarios: {len(self.results)}
- Passed: {sum(1 for r in self.results if r['passed'])}
- Failed: {sum(1 for r in self.results if not r['passed'])}

## Details

"""
        
        for result in self.results:
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            report += f"### {result['file']}\n\n"
            report += f"Status: {status}\n\n"
            
            if result['issues']:
                report += "Issues:\n"
                for issue in result['issues']:
                    report += f"- {issue}\n"
            
            report += "\n---\n\n"
        
        return report


def main():
    """Main entry point"""
    validator = GoldenExampleValidator()
    
    success = validator.run_validation()
    
    # Generate and save report
    report = validator.generate_report()
    report_file = Path(__file__).parent / "golden_examples" / "validation_report.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nValidation report saved to: {report_file}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
