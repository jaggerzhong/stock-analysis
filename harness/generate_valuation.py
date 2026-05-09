#!/usr/bin/env python3
"""
Generate VALUE ASSESSMENT for stocks using the analysis engine.

Core Philosophy:
- We do NOT predict stock prices (speculation)
- We assess CORE VALUE and measure how much price deviates from it
- Decision: WAIT (overvalued) vs GET ON BOARD (undervalued vs fair)

Three-Layer Valuation Model:
1. Current Value (PE Percentile): Historical估值锚点
2. Growth Premium (Industry Trend): 行业趋势溢价
3. Moat Premium (Competitive Barrier): 护城河溢价
"""

import sys
import os
import json
import re
import yaml
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.analyze import StockAnalyzer
from watchlist_utils import load_watchlist


# Load industry configuration
def load_industry_config():
    config_path = Path(__file__).parent.parent / 'analysis' / 'industry_config.yaml'
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}


def get_symbol_premiums(symbol: str, industry_config: dict) -> dict:
    """
    Get growth and moat premiums for a symbol.
    Returns dict with growth_premium, moat_premium, and thesis.
    """
    result = {
        'growth_premium': 0.0,
        'moat_premium': 0.0,
        'thesis': [],
        'matched_industries': []
    }
    
    # Strip market suffix (e.g., '.US', '.HK')
    clean_symbol = symbol.split('.')[0].upper()
    
    industries = industry_config.get('industries', {})
    
    for industry_key, industry_data in industries.items():
        if industry_key.startswith('_'):
            continue  # Skip comments/anchors
        
        symbols = industry_data.get('symbols', [])
        if clean_symbol in [s.upper().split('.')[0] for s in symbols]:
            growth = industry_data.get('growth_premium', 0.0)
            moat = industry_data.get('moat_premium', 0.0)
            
            if growth > 0:
                result['growth_premium'] += growth
                result['matched_industries'].append(industry_data.get('name', industry_key))
                result['thesis'].append(industry_data.get('thesis', ''))
            
            if moat > 0:
                result['moat_premium'] = max(result['moat_premium'], moat)
    
    return result


def calculate_core_value(analysis: dict, valuation_data: dict = None, industry_config: dict = None) -> dict:
    """
    Calculate core value using Three-Layer Model.
    
    Layer 1: Current Value (PE Percentile) - 40% weight
    Layer 2: Growth Premium (Industry Trend) - 35% weight
    Layer 3: Moat Premium (Competitive Barrier) - 25% weight
    
    Returns:
        {
            'pe_percentile': float or None,
            'pe_median': float or None,
            'pe_current': float or None,
            'layer1_value': float,      # PE percentile based value
            'layer2_growth_premium': float,
            'layer2_growth_value': float,
            'layer3_moat_premium': float,
            'layer3_moat_value': float,
            'core_value': float,
            'core_value_method': str,
            'thesis': list,
        }
    """
    symbol = analysis.get('symbol', '')
    current_price = analysis.get('current_price', 0)
    calc_metrics = analysis.get('quote_details', {}).get('calc_index', {})
    tech = analysis.get('technical_analysis', {})
    moat_data = analysis.get('moat_analysis', {})
    
    # Get premiums from industry config
    premiums = get_symbol_premiums(symbol, industry_config or {})
    growth_premium = premiums['growth_premium']
    moat_premium = premiums['moat_premium']
    
    # ============================================================
    # LAYER 1: Current Value (PE Percentile) - 40% weight
    # ============================================================
    pe_percentile = None
    pe_median = None
    pe_current = None
    layer1_value = current_price  # Default to current price
    
    if valuation_data:
        pe_data = valuation_data.get('history', {}).get('metrics', {}).get('pe', {})
        overview_pe = valuation_data.get('overview', {}).get('metrics', {}).get('pe', {})
        
        # Extract current PE
        pe_str = overview_pe.get('metric', '')
        if pe_str:
            pe_current = float(pe_str.replace('x', ''))
        
        # Extract historical median
        pe_median = float(pe_data.get('median', 0)) if pe_data.get('median') else None
        
        # Extract percentile from description
        desc = pe_data.get('desc', '')
        match = re.search(r'比近.*?年.*?(\d+\.\d+)%', desc)
        if match:
            pe_percentile = float(match.group(1))
        
        # Calculate PE-based fair value
        if pe_current and pe_median and current_price > 0:
            eps = current_price / pe_current
            
            if pe_percentile and pe_percentile >= 70:
                # Undervalued: PE is historically low
                # If PE reverts to median, value = eps * pe_median
                layer1_value = eps * pe_median
            elif pe_percentile and pe_percentile <= 30:
                # Overvalued: PE is historically high
                layer1_value = eps * pe_median
            else:
                # Fair range
                layer1_value = current_price
    
    # ============================================================
    # LAYER 2: Growth Premium (Industry Trend) - 35% weight
    # ============================================================
    layer2_growth_value = layer1_value * (1 + growth_premium)
    
    # ============================================================
    # LAYER 3: Moat Premium (Competitive Barrier) - 25% weight
    # ============================================================
    # Use moat data from engine if available
    moat_width = moat_data.get('moat_width')  # None if no moat, not string 'None'
    moat_score = moat_data.get('moat_score', 5)
    
    # Moat premium from config overrides if higher
    if moat_width == 'Wide':
        moat_premium = max(moat_premium, 0.20)
    elif moat_width == 'Narrow':
        moat_premium = max(moat_premium, 0.10)
    elif moat_width == 'Minimal':
        moat_premium = max(moat_premium, 0.05)
    
    layer3_moat_value = layer2_growth_value * (1 + moat_premium)
    
    # ============================================================
    # FINAL: Weighted Average
    # ============================================================
    # CRITICAL: When PE percentile is N/A, we have no historical valuation anchor.
    # Growth/moat premiums without a PE anchor create circular reasoning:
    #   Layer1 = current_price → Layer2 = current_price * (1+premium)
    #   → core_value > current_price → stock appears "undervalued" → BUY
    # This produces false buy signals. Fall back to current_price as core value.
    no_pe_anchor = (pe_percentile is None and layer1_value == current_price)

    if no_pe_anchor:
        core_value = current_price
        core_value_method = 'current_price'  # No PE anchor available
    else:
        # Adjust weights based on available data
        weight1 = 0.40 if layer1_value != current_price else 0.50
        weight2 = 0.35 if growth_premium > 0 else 0.30
        weight3 = 0.25 if moat_premium > 0 else 0.20

        # Normalize weights
        total_weight = weight1 + weight2 + weight3
        weight1 /= total_weight
        weight2 /= total_weight
        weight3 /= total_weight

        core_value = (
            layer1_value * weight1 +
            layer2_growth_value * weight2 +
            layer3_moat_value * weight3
        )

        # Determine method string
        method_parts = ['pe_percentile']
        if growth_premium > 0:
            method_parts.append(f'growth+{int(growth_premium*100)}%')
        if moat_premium > 0:
            method_parts.append(f'moat+{int(moat_premium*100)}%')
        core_value_method = '+'.join(method_parts)
    
    return {
        'pe_percentile': pe_percentile,
        'pe_median': pe_median,
        'pe_current': pe_current,
        'layer1_value': round(layer1_value, 2),
        'layer2_growth_premium': growth_premium,
        'layer2_growth_value': round(layer2_growth_value, 2),
        'layer3_moat_premium': moat_premium,
        'layer3_moat_value': round(layer3_moat_value, 2),
        'core_value': round(core_value, 2),
        'core_value_method': core_value_method,
        'no_pe_anchor': no_pe_anchor,
        'moat_width': moat_width,
        'moat_score': moat_score,
        'thesis': premiums.get('thesis', []),
        'matched_industries': premiums.get('matched_industries', []),
    }


def calculate_value_deviation(current_price: float, core_value: float, pe_percentile: float = None,
                               growth_premium: float = 0.0, moat_premium: float = 0.0) -> dict:
    """
    Calculate how much price deviates from core value.
    
    Balance between:
    - PE percentile (historical valuation anchor)
    - Deviation (current price vs adjusted core value)
    - Growth/Moat premiums (future potential)
    
    For stocks with strong growth/moat premiums:
    - Give more weight to the adjusted core value
    - PE percentile serves as a warning signal, not a hard rule
    
    Returns:
        {
            'deviation_pct': float,
            'status': str,
            'action': str,
        }
    """
    if core_value <= 0 or current_price <= 0:
        return {
            'deviation_pct': 0,
            'status': 'unknown',
            'action': 'HOLD',
        }
    
    deviation_pct = (current_price - core_value) / core_value
    
    # Determine if we have strong forward-looking premiums
    has_strong_premium = growth_premium >= 0.20 or moat_premium >= 0.15

    # When PE percentile is N/A, we lack a valuation anchor.
    # Growth premiums without a PE anchor are speculative — cap buy signals at HOLD.
    no_pe_anchor = pe_percentile is None

    # Calculate base action from deviation
    if deviation_pct < -0.30:
        dev_status = 'deep_discount'
        dev_action = 'GET_ON_BOARD'
    elif deviation_pct < -0.15:
        dev_status = 'discount'
        dev_action = 'BUY'
    elif deviation_pct < -0.05:
        dev_status = 'slight_discount'
        dev_action = 'BUY_SMALL'
    elif deviation_pct <= 0.05:
        dev_status = 'fair'
        dev_action = 'HOLD'
    elif deviation_pct <= 0.15:
        dev_status = 'premium'
        dev_action = 'WAIT'
    else:
        dev_status = 'significant_premium'
        dev_action = 'AVOID'
    
    # Adjust based on PE percentile and premiums
    if pe_percentile is not None:
        if pe_percentile >= 80:
            status = 'deep_discount'
            action = 'GET_ON_BOARD'
        elif pe_percentile >= 70:
            status = 'discount'
            action = 'BUY'
        elif pe_percentile >= 50:
            status = 'slight_discount'
            action = 'BUY_SMALL'
        elif pe_percentile >= 30:
            status = 'fair'
            action = 'HOLD'
        elif pe_percentile >= 20:
            status = 'premium'
            action = 'WAIT'
        else:
            # PE percentile < 20% means historically expensive
            # But if we have strong premiums and actual deviation is favorable, upgrade
            if has_strong_premium and deviation_pct < -0.05:
                # Strong growth/moat story + undervalued = BUY
                status = 'discount'
                action = 'BUY'
            elif has_strong_premium and deviation_pct < 0.05:
                # Strong story + fair value = HOLD
                status = 'fair'
                action = 'HOLD'
            elif deviation_pct < -0.15:
                # Not expensive relative to adjusted value
                status = 'discount'
                action = 'BUY'
            else:
                # Expensive by all measures
                status = 'significant_premium'
                action = 'AVOID'
    else:
        # No PE data — no valuation anchor. Cap buy signals at HOLD.
        # Growth premiums without a PE anchor are speculative;
        # we can identify overvaluation but cannot confirm undervaluation.
        if dev_action in ('GET_ON_BOARD', 'BUY', 'BUY_SMALL'):
            status = 'fair'
            action = 'HOLD'
        else:
            status = dev_status
            action = dev_action
    
    return {
        'deviation_pct': round(deviation_pct * 100, 1),
        'status': status,
        'action': action,
    }


def generate_value_assessment(date_str: str, watchlist: list) -> dict:
    """
    Generate value assessment for watchlist symbols.
    
    Uses Three-Layer Valuation Model:
    1. Current Value (PE Percentile): Historical估值锚点
    2. Growth Premium (Industry Trend): 行业趋势溢价
    3. Moat Premium (Competitive Barrier): 护城河溢价
    
    Args:
        date_str: Date string YYYY-MM-DD
        watchlist: List of symbol strings
        
    Returns:
        Value assessment dict
    """
    analyzer = StockAnalyzer()
    assessments = []
    
    # Load industry configuration
    industry_config = load_industry_config()
    
    for symbol in watchlist:
        try:
            analysis = analyzer.analyze_symbol(symbol, include_market=False)
            
            current_price = analysis.get('current_price', 0)
            if not current_price:
                continue
            
            # Fetch valuation data (PE percentile, historical range)
            print("Fetching valuation data...")
            valuation_data = analyzer.fetcher.fetch_valuation(symbol)
            
            # Calculate core value with three-layer model
            value_data = calculate_core_value(analysis, valuation_data, industry_config)
            core_value = value_data['core_value']
            
            # Calculate deviation using PE percentile + premiums
            deviation = calculate_value_deviation(
                current_price,
                core_value,
                value_data.get('pe_percentile'),
                value_data.get('layer2_growth_premium', 0),
                value_data.get('layer3_moat_premium', 0)
            )
            
            # Value trap check
            trap = analysis.get('value_trap_analysis', {})
            trap_score = trap.get('trap_score', 0)
            
            # Adjust action based on value trap
            if trap_score >= 30 and deviation['action'] in ('GET_ON_BOARD', 'BUY', 'BUY_SMALL'):
                deviation['action'] = 'AVOID'
                deviation['status'] = 'value_trap'
            
            # Data quality check — if financial data has warnings, flag them
            financial_data = analysis.get('financial_data', {})
            data_quality = financial_data.get('data_quality', {})
            dq_warnings = data_quality.get('warnings', [])
            dq_is_clean = data_quality.get('is_clean', True)
            
            if not dq_is_clean and deviation['action'] in ('GET_ON_BOARD', 'BUY', 'BUY_SMALL'):
                deviation['action'] = 'HOLD'
                deviation['status'] = 'data_warning'
            
            # Format PE percentile for display
            pe_pct_display = f"{value_data['pe_percentile']:.0f}%" if value_data['pe_percentile'] else 'N/A'
            
            # Build assessment with three-layer details
            assessment = {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'core_value': round(core_value, 2),
                'value_methods': value_data['core_value_method'],
                'deviation_pct': deviation['deviation_pct'],
                'status': deviation['status'],
                'action': deviation['action'],
                'no_pe_anchor': value_data.get('no_pe_anchor', False),
                'data_quality_clean': dq_is_clean,
                'data_quality_warnings': dq_warnings,
                'moat_width': value_data.get('moat_width', 'None'),
                'moat_score': value_data.get('moat_score', 5),
                'value_trap_score': trap_score,
                'valuation_details': {
                    'pe_percentile': value_data.get('pe_percentile'),
                    'pe_median': value_data.get('pe_median'),
                    'pe_current': value_data.get('pe_current'),
                    'layer1_value': value_data.get('layer1_value'),
                    'layer2_growth_premium': value_data.get('layer2_growth_premium'),
                    'layer2_growth_value': value_data.get('layer2_growth_value'),
                    'layer3_moat_premium': value_data.get('layer3_moat_premium'),
                    'layer3_moat_value': value_data.get('layer3_moat_value'),
                    'no_pe_anchor': value_data.get('no_pe_anchor', False),
                },
                'thesis': value_data.get('thesis', []),
                'matched_industries': value_data.get('matched_industries', []),
            }
            assessments.append(assessment)
            
            # Print summary with three-layer breakdown
            action_emoji = {
                'GET_ON_BOARD': '🚀',
                'BUY': '✅',
                'BUY_SMALL': '➕',
                'HOLD': '➡️',
                'WAIT': '⏳',
                'AVOID': '❌',
            }
            emoji = action_emoji.get(deviation['action'], '➡️')
            
            dq_flag = ' ⚠️' if not dq_is_clean else ''
            
            # Build three-layer display
            if value_data.get('no_pe_anchor'):
                layer_info = "⚠️ No PE anchor — core value = current price (growth premiums suspended)"
            else:
                layer_info = f"L1: ${value_data.get('layer1_value', current_price):.0f}"
                if value_data.get('layer2_growth_premium', 0) > 0:
                    layer_info += f" → L2: ${value_data.get('layer2_growth_value', 0):.0f} (+{int(value_data['layer2_growth_premium']*100)}%)"
                if value_data.get('layer3_moat_premium', 0) > 0:
                    layer_info += f" → L3: ${value_data.get('layer3_moat_value', 0):.0f} (+{int(value_data['layer3_moat_premium']*100)}%)"

            print(f"  {emoji} {symbol}: ${current_price:.2f} | Core: ${core_value:.2f} | "
                  f"PE Hist: {pe_pct_display} | {deviation['action']}{dq_flag}")
            print(f"      {layer_info}")
            if dq_warnings:
                for w in dq_warnings[:2]:
                    print(f"      ⚠️ Data: {w}")
            
        except Exception as e:
            print(f"  ⚠️  Failed to assess {symbol}: {e}", file=sys.stderr)
            continue
    
    # Sort by deviation (most undervalued first)
    assessments.sort(key=lambda x: x['deviation_pct'])
    
    return {
        'date': date_str,
        'assessment_date': datetime.now().isoformat(),
        'engine_version': '3.0-value',
        'philosophy': 'Value investing: assess core value, measure price deviation, decide WAIT or GET_ON_BOARD',
        'watchlist_assessments': assessments,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Stock Value Assessment Tool')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('symbols', nargs='*', default=None)
    args = parser.parse_args()
    
    print("=" * 70)
    print("VALUE ASSESSMENT ENGINE v3.0")
    print("=" * 70)
    print("Philosophy: Find core value, measure price deviation, decide action")
    print("-" * 70)
    
    symbols = args.symbols if args.symbols else load_watchlist()
    
    result = generate_value_assessment(args.date, symbols)
    
    print("-" * 70)
    print(f"\n📊 Summary ({len(result['watchlist_assessments'])} stocks assessed)")
    
    # Categorize
    onboard = [a for a in result['watchlist_assessments'] if a['action'] == 'GET_ON_BOARD']
    buy = [a for a in result['watchlist_assessments'] if a['action'] == 'BUY']
    wait = [a for a in result['watchlist_assessments'] if a['action'] in ('WAIT', 'AVOID')]
    
    if onboard:
        print(f"\n🚀 GET ON BOARD ({len(onboard)}):")
        for a in onboard:
            print(f"   {a['symbol']}: {a['deviation_pct']:.1f}% below core value")
    
    if buy:
        print(f"\n✅ BUY ({len(buy)}):")
        for a in buy:
            print(f"   {a['symbol']}: {a['deviation_pct']:.1f}% below core value")
    
    if wait:
        print(f"\n⏳ WAIT/AVOID ({len(wait)}):")
        for a in wait:
            print(f"   {a['symbol']}: {a['deviation_pct']:+.1f}% vs core value")
    
    output = json.dumps(result, indent=2)
    
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"\n💾 Assessment saved to: {args.output}")


if __name__ == '__main__':
    main()
