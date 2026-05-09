#!/usr/bin/env python3
"""
Backtest analysis - analyze stocks as of a specific historical date.
This allows testing how our analysis would have performed on past dates.
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.analyze import LongbridgeDataFetcher, StockAnalyzer


def fetch_historical_kline(symbol: str, end_date: str, days: int = 200) -> List[Dict]:
    """
    Fetch historical K-line data up to a specific date.
    
    Args:
        symbol: Stock symbol
        end_date: End date (YYYY-MM-DD)
        days: Number of days to look back
    """
    fetcher = LongbridgeDataFetcher()
    
    # Calculate start date
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    start_dt = end_dt - timedelta(days=days)
    start_date = start_dt.strftime('%Y-%m-%d')
    
    print(f"  Fetching kline: {start_date} to {end_date}")
    
    output = fetcher.run_command([
        'longbridge', 'kline', 'history', symbol,
        '--start', start_date,
        '--end', end_date,
        '--period', 'day',
        '--format', 'json'
    ])
    
    if not output or not output.strip():
        print(f"  Warning: No kline data for {symbol}")
        return []
    
    try:
        data = json.loads(output)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError as e:
        print(f"  Error parsing kline JSON: {e}")
        return []


def analyze_as_of_date(date: str, watchlist: List[str]) -> Dict:
    """
    Analyze stocks as of a specific historical date.
    
    Args:
        date: Target date (YYYY-MM-DD)
        watchlist: List of symbols to analyze
    """
    print(f"\n{'='*60}")
    print(f"BACKTEST ANALYSIS - As of {date}")
    print(f"{'='*60}\n")
    
    analyzer = StockAnalyzer()
    fetcher = LongbridgeDataFetcher()
    
    analyses = []
    
    for symbol in watchlist:
        print(f"\n{'='*60}")
        print(f"Analyzing: {symbol}")
        print(f"{'='*60}\n")
        
        # Fetch historical kline data up to target date
        print("Fetching historical data...")
        kline_data = fetch_historical_kline(symbol, date, days=365)
        
        if not kline_data:
            print(f"Skipping {symbol} - no data available")
            continue
        
        # Use the last candle as the "current" state
        last_candle = kline_data[-1]
        current_price = float(last_candle.get('close', 0))
        
        print(f"  Current price (as of {date}): ${current_price:.2f}")
        print(f"  Data points: {len(kline_data)} candles")
        
        # Prepare stock data
        print("Preparing stock data...")
        stock_data = analyzer.prepare_stock_data(symbol, {}, kline_data)
        
        # Run analysis
        print("Running comprehensive analysis...")
        analysis = analyzer.engine.analyze_stock(stock_data)
        
        # Add metadata
        analysis['analysis_date'] = date
        analysis['backtest'] = True
        analysis['quote_details'] = {
            'symbol': symbol,
            'current_price': current_price,
            'date': date,
            'high': last_candle.get('high'),
            'low': last_candle.get('low'),
            'open': last_candle.get('open'),
            'volume': last_candle.get('volume')
        }
        
        analyses.append(analysis)
    
    return {
        'date': date,
        'analyses': analyses,
        'watchlist': watchlist
    }


def generate_backtest_report(result: Dict) -> str:
    """Generate markdown report for backtest analysis."""
    date = result['date']
    analyses = result['analyses']
    
    md = f"""# 📊 Backtest Analysis Report
**Analysis Date:** {date}
**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## ⚠️ Important Note
This is a **backtest analysis** showing how our strategy would have evaluated these stocks on {date}.
This allows you to compare our recommendations with actual subsequent performance.

---

## Watchlist Summary

| Symbol | Price | Score | Recommendation | Risk Level | RSI |
|--------|-------|-------|----------------|------------|-----|
"""
    
    for analysis in analyses:
        symbol = analysis.get('symbol', 'N/A')
        quote = analysis.get('quote_details', {})
        overall = analysis.get('overall_assessment', {})
        risk = analysis.get('risk_analysis', {})
        tech = analysis.get('technical_analysis', {})
        
        price = quote.get('current_price', 'N/A')
        score = overall.get('overall_score', 50)
        recommendation = overall.get('recommendation', 'HOLD')
        risk_level = risk.get('risk_score', 50)
        
        # Format price
        if isinstance(price, (int, float)):
            price_str = f"${price:.2f}"
        else:
            price_str = str(price)
        
        # Risk label
        risk_label = 'Low' if risk_level < 40 else 'Medium' if risk_level < 60 else 'High'
        
        # RSI
        rsi = None
        if tech.get('rsi'):
            rsi = tech['rsi'][-1] if tech['rsi'] else None
        
        rsi_str = f"{rsi:.1f}" if rsi else "N/A"
        
        md += f"| {symbol} | {price_str} | {score:.1f}/100 | {recommendation} | {risk_label} | {rsi_str} |\n"
    
    md += "\n---\n\n## Detailed Analysis\n\n"
    
    for analysis in analyses:
        symbol = analysis.get('symbol', 'N/A')
        quote = analysis.get('quote_details', {})
        overall = analysis.get('overall_assessment', {})
        risk = analysis.get('risk_analysis', {})
        tech = analysis.get('technical_analysis', {})
        factor = analysis.get('factor_analysis', {})
        
        price = quote.get('current_price', 'N/A')
        
        md += f"### {symbol}\n\n"
        md += f"**Price (as of {date}):** "
        if isinstance(price, (int, float)):
            md += f"${price:.2f}\n\n"
        else:
            md += f"{price}\n\n"
        
        md += f"**Recommendation:** {overall.get('recommendation', 'N/A')} "
        md += f"({overall.get('confidence', 'N/A')} confidence)\n\n"
        
        md += f"**Overall Score:** {overall.get('overall_score', 50):.1f}/100\n\n"
        
        # Score breakdown
        breakdown = overall.get('score_breakdown', {})
        md += "**Score Breakdown:**\n"
        md += f"- Risk: {breakdown.get('risk_score', 50):.1f}/100\n"
        md += f"- Valuation: {breakdown.get('valuation_score', 50):.1f}/100\n"
        md += f"- Technical: {breakdown.get('technical_score', 50):.1f}/100\n"
        md += f"- Factor: {breakdown.get('factor_score', 50):.1f}/100\n\n"
        
        # Key metrics
        md += "**Key Metrics:**\n"
        if risk.get('sharpe_ratio'):
            md += f"- Sharpe Ratio: {risk['sharpe_ratio']:.2f}\n"
        if risk.get('max_drawdown'):
            md += f"- Max Drawdown: {risk['max_drawdown']:.1%}\n"
        if risk.get('historical_volatility'):
            md += f"- Volatility: {risk['historical_volatility']:.1%}\n"
        
        if tech.get('rsi'):
            rsi = tech['rsi'][-1] if tech['rsi'] else None
            if rsi:
                md += f"- RSI: {rsi:.1f}\n"
        
        if factor.get('composite_score'):
            md += f"- Factor Score: {factor['composite_score']:.1f}/100\n"
        
        md += "\n---\n\n"
    
    # Add strategy summary
    md += """## Strategy Summary

Based on the analysis above, here's the recommended action:

"""
    
    # Sort by score
    sorted_analyses = sorted(analyses, key=lambda x: x.get('overall_assessment', {}).get('overall_score', 0), reverse=True)
    
    buy_candidates = [a for a in sorted_analyses if a.get('overall_assessment', {}).get('overall_score', 0) >= 50]
    sell_candidates = [a for a in sorted_analyses if a.get('overall_assessment', {}).get('recommendation') == 'SELL']
    
    if buy_candidates:
        md += "### ✅ Buy Candidates (Score ≥ 50)\n\n"
        for a in buy_candidates:
            symbol = a.get('symbol')
            score = a.get('overall_assessment', {}).get('overall_score', 0)
            price = a.get('quote_details', {}).get('current_price', 0)
            md += f"- **{symbol}** (Score: {score:.1f}/100, Price: ${price:.2f})\n"
        md += "\n"
    
    if sell_candidates:
        md += "### ⚠️ Sell/High Risk Positions\n\n"
        for a in sell_candidates:
            symbol = a.get('symbol')
            risk_score = a.get('risk_analysis', {}).get('risk_score', 0)
            md += f"- **{symbol}** (Risk: {risk_score:.1f}/100)\n"
        md += "\n"
    
    md += f"""---

**Note:** This analysis was performed using data available as of {date}.
Compare these recommendations with the actual performance after {date} to evaluate strategy effectiveness.
"""
    
    return md


def main():
    parser = argparse.ArgumentParser(description='Backtest stock analysis for a specific date')
    parser.add_argument('date', help='Target date for analysis (YYYY-MM-DD)')
    parser.add_argument('--symbols', nargs='+', 
                       default=['BABA.US', 'NVDA.US', 'TSLA.US', 'CEG.US', 'COIN.US', 'PLTR.US'],
                       help='Symbols to analyze')
    parser.add_argument('--output', '-o', help='Output file path')
    
    args = parser.parse_args()
    
    # Validate date
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD.")
        sys.exit(1)
    
    # Run backtest analysis
    result = analyze_as_of_date(args.date, args.symbols)
    
    # Generate report
    report = generate_backtest_report(result)
    
    # Output
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n✅ Report saved to: {output_file}")
    else:
        print("\n" + "="*60)
        print("BACKTEST REPORT")
        print("="*60 + "\n")
        print(report)
    
    # Also save JSON result
    json_file = Path(args.output).with_suffix('.json') if args.output else Path(f'/tmp/backtest-{args.date}.json')
    with open(json_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"JSON data saved to: {json_file}")


if __name__ == "__main__":
    main()
