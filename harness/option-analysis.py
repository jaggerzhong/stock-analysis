#!/usr/bin/env python3
"""
Option Analysis Script for Harness
Analyzes option positions from longbridge positions JSON.
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Standardized import path
SKILL_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(SKILL_DIR))

from analysis.engine import OptionPosition, OptionAnalyzer


def main():
    parser = argparse.ArgumentParser(description='Analyze option positions')
    parser.add_argument('--positions', '-p', required=True, help='Path to positions JSON file')
    parser.add_argument('--output', '-o', help='Output markdown file path')
    parser.add_argument('--json', action='store_true', help='Output JSON instead of markdown')
    args = parser.parse_args()

    # Load positions
    positions_file = Path(args.positions)
    if not positions_file.exists():
        print(f"Error: Positions file not found: {positions_file}")
        return 1

    with open(positions_file) as f:
        positions = json.load(f)

    if not positions:
        print("No positions found")
        return 0

    # Parse option positions
    options = OptionAnalyzer.parse_positions(positions)

    if not options:
        if args.output:
            with open(args.output, 'w') as f:
                f.write("No option positions found.\n")
        if not args.json:
            print("No option positions found")
        return 0

    # Fetch underlying prices and analyze each option
    analyses = []

    for opt in options:
        # Find original position data to get current price
        orig_pos = next((p for p in positions if p.get('symbol') == opt.symbol), {})
        opt_cost_price = float(orig_pos.get('cost_price', 0))
        opt.current_price = opt_cost_price  # Use entry price as current (simplified)
        
        # Get underlying stock price (separate from option premium)
        underlying_price = 0
        try:
            result = subprocess.run(
                ['longbridge', 'quote', f'{opt.underlying}.US', '--format', 'json'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                quote_data = json.loads(result.stdout.strip())
                if quote_data and isinstance(quote_data, list):
                    underlying_price = float(quote_data[0].get('last', 0))
        except Exception as e:
            print(f"Warning: Could not fetch underlying price for {opt.underlying}: {e}")
        
        # Fallback: use strike if we couldn't get underlying
        if underlying_price == 0:
            underlying_price = opt.strike

        # Also try to get current option price from longbridge
        try:
            result = subprocess.run(
                ['longbridge', 'quote', opt.symbol, '--format', 'json'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                quote_data = json.loads(result.stdout.strip())
                if quote_data and isinstance(quote_data, list) and quote_data[0].get('last'):
                    opt.current_price = float(quote_data[0].get('last', 0))
        except Exception:
            pass  # Use entry price as fallback

        # Analyze
        analysis = OptionAnalyzer.analyze_option(opt, underlying_price)
        analyses.append(analysis)

    # Output
    if args.json:
        output_data = {
            'analysis_date': datetime.now().isoformat(),
            'option_positions': analyses,
            'summary': {
                'total_options': len(analyses),
                'total_market_value': sum(a.get('market_value', 0) for a in analyses),
                'total_pnl': sum(a.get('pnl', 0) for a in analyses if a.get('pnl') is not None),
            }
        }
        print(json.dumps(output_data, indent=2))
        return 0

    # Generate markdown report
    lines = []
    lines.append("### 期权持仓分析\n")

    if not analyses:
        lines.append("无期权持仓\n")
    else:
        # Summary table
        lines.append("| 期权 | 类型 | 方向 | 行权价 | 到期日 | 盈亏 | 盈利概率 | 建议 |")
        lines.append("|------|------|------|--------|--------|------|----------|------|")

        for a in analyses:
            symbol = a['symbol'].replace('.US', '')
            opt_type = 'Put' if a['option_type'] == 'put' else 'Call'
            direction = '卖出' if a['direction'] == 'short' else '买入'
            pnl_str = f"${a['pnl']:.0f}" if a.get('pnl') is not None else 'N/A'
            prob = f"{a['risk_metrics']['prob_of_profit']:.0%}"
            action = a['recommendation']['action']
            lines.append(f"| {symbol} | {opt_type} | {direction} | ${a['strike']:.0f} | {a['expiry']} | {pnl_str} | {prob} | {action} |")

        lines.append("")

        # Detailed analysis for each option
        for a in analyses:
            lines.append(OptionAnalyzer.generate_option_report(a))
            lines.append("")

    report = "\n".join(lines)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Option analysis saved to: {args.output}")
    else:
        print(report)

    return 0


if __name__ == '__main__':
    sys.exit(main())