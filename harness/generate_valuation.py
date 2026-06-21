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
from analysis.engine import ValuationMetricsCalculator
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


def _get_moat_override(symbol: str) -> dict:
    """Get moat override from watchlist.json if available."""
    try:
        wl_path = Path(__file__).parent.parent / 'references' / 'watchlist.json'
        with open(wl_path) as f:
            wl = json.load(f)
        for item in wl.get('watchlist', []):
            if item.get('symbol', '').upper() == symbol.upper():
                moat = item.get('moat_override')
                if moat:
                    return moat
    except Exception:
        pass
    return None


def _calculate_fallback_value(analysis: dict, current_price: float, calc_metrics: dict, industry_config: dict) -> float:
    """
    Calculate fallback value when PE anchor is unavailable.
    Try P/S ratio first, then industry PE median as last resort.
    """
    fallback_value = None
    method = None

    # Method 1: P/S ratio (price-to-sales)
    ps_ratio = None
    revenue = None
    market_cap = None

    financial = analysis.get('financial_data', {})
    ttm = financial.get('ttm', {})
    quote_details = analysis.get('quote_details', {})

    if ttm.get('revenue') and ttm.get('revenue') > 0:
        revenue = ttm['revenue']

    market_cap = quote_details.get('market_cap') or analysis.get('market_cap')
    if market_cap and revenue and revenue > 0:
        ps_ratio = market_cap / revenue
        # Industry-average P/S (conservative estimates)
        industry_ps = _get_industry_ps_ratio(analysis.get('symbol', ''), industry_config)
        if industry_ps and industry_ps > 0 and ps_ratio and ps_ratio > 0:
            sales_per_share = revenue / (market_cap / current_price) if market_cap > 0 else 0
            if sales_per_share > 0:
                fallback_value = sales_per_share * industry_ps
                method = 'ps_ratio'

    # Method 2: Industry PE median from industry_config
    if fallback_value is None or fallback_value <= 0:
        industry_pe = _get_industry_pe_median(analysis.get('symbol', ''), industry_config)
        eps = analysis.get('financial_data', {}).get('ttm', {}).get('eps')
        if industry_pe and industry_pe > 0 and eps and eps > 0:
            fallback_value = eps * industry_pe
            method = 'industry_pe'

    return fallback_value


def _get_industry_ps_ratio(symbol: str, industry_config: dict) -> float:
    """Get industry-average P/S ratio for a symbol."""
    clean = symbol.split('.')[0].upper()
    ps_map = {
        'NVDA': 10.0, 'AMD': 5.0, 'AVGO': 8.0,
        'TSLA': 5.0, 'RIVN': 2.5,
        'BABA': 1.0, 'AMZN': 2.5, 'JD': 0.4,
        'MSFT': 8.0, 'AAPL': 5.0, 'GOOGL': 4.0, 'GOOG': 4.0,
        'PLTR': 10.0, 'COIN': 4.0, 'HOOD': 4.0,
        'DUK': 2.0, 'CEG': 2.5,
    }
    return ps_map.get(clean, 5.0)


def _get_industry_pe_median(symbol: str, industry_config: dict) -> float:
    """Get industry median PE from config or defaults."""
    config_path = Path(__file__).parent.parent / 'analysis' / 'config.yaml'
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        benchmarks = config.get('valuation', {}).get('sector_pe_benchmarks', {})
        clean = symbol.split('.')[0].upper()
        industry_map = {
            'NVDA': 'Technology', 'AMD': 'Technology', 'AVGO': 'Technology',
            'MSFT': 'Technology', 'AAPL': 'Technology', 'GOOGL': 'Technology',
            'PLTR': 'Technology', 'TSLA': 'Consumer_Discretionary',
            'BABA': 'Technology', 'COIN': 'Financials', 'HOOD': 'Financials',
            'DUK': 'Utilities', 'CEG': 'Utilities',
        }
        sector = industry_map.get(clean, 'Technology')
        if sector in benchmarks:
            return benchmarks[sector].get('median', 16.0)
    except Exception:
        pass
    return 16.0


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

        # Calculate PE-based fair value using mean reversion
        # PE percentile interpretation:
        #   - HIGH percentile (>=70): current PE is ABOVE historical median
        #     → stock is expensive relative to its own PE history
        #     → if EPS is strong and PE reverts to median, fair value = EPS * pe_median
        #     → this can make the stock appear "cheap" vs median, but PE is still HIGH
        #     → RISK: mean reversion may not happen (structural PE change)
        #   - LOW percentile (<=30): current PE is BELOW historical median
        #     → stock may be undervalued or earnings declining
        #     → fair value = EPS * pe_median (mean reversion upside)
        #   - MID range (30-70): PE is in normal historical range
        #     → use current price as fair value (no strong signal)
        if pe_current and pe_median and current_price > 0:
            eps = current_price / pe_current

            if pe_percentile is not None:
                if pe_percentile >= 80:
                    skepticism = 0.80
                    layer1_value = eps * pe_median * skepticism
                elif pe_percentile >= 60:
                    skepticism = 0.88
                    layer1_value = eps * pe_median * skepticism
                elif pe_percentile >= 40:
                    layer1_value = current_price
                elif pe_percentile >= 20:
                    layer1_value = eps * pe_median
                else:
                    skepticism = 0.85
                    layer1_value = eps * pe_median * skepticism
            else:
                # No percentile data — use median PE as baseline
                if pe_median and pe_median > 0:
                    layer1_value = eps * pe_median
                else:
                    layer1_value = current_price

    # ============================================================
    # LAYER 2: Growth Premium (Industry Trend) - ADDITIVE, not multiplicative
    # ============================================================
    # FIX: Previous version used multiplication (layer1 * 1.25 * 1.20 = +50%)
    # This caused systematic overvaluation. Now use ADDITIVE premiums capped at 25%.
    MAX_TOTAL_PREMIUM = 0.15
    growth_additive = growth_premium
    layer2_growth_value = layer1_value * (1 + growth_additive)

    # ============================================================
    # LAYER 3: Moat Premium (Competitive Barrier) - ADDITIVE, not multiplicative
    # ============================================================
    moat_width = moat_data.get('moat_width')
    moat_score = moat_data.get('moat_score', 5)

    # Apply watchlist moat overrides if available
    moat_override = _get_moat_override(symbol)
    if moat_override:
        moat_width = moat_override.get('moat_width', moat_width)
        moat_score = moat_override.get('moat_score', moat_score)
        moat_premium = moat_override.get('moat_premium', moat_premium)

    if moat_width == 'Wide':
        moat_premium = max(moat_premium, 0.15)
    elif moat_width == 'Narrow':
        moat_premium = max(moat_premium, 0.08)
    elif moat_width == 'Minimal':
        moat_premium = max(moat_premium, 0.03)

    moat_additive = moat_premium
    layer3_moat_value = layer1_value * (1 + growth_additive + moat_additive)

    # Cap total premium to prevent overvaluation
    total_premium = growth_additive + moat_additive
    if total_premium > MAX_TOTAL_PREMIUM:
        scale = MAX_TOTAL_PREMIUM / total_premium
        growth_additive *= scale
        moat_additive *= scale
        total_premium = MAX_TOTAL_PREMIUM
        layer3_moat_value = layer1_value * (1 + total_premium)

    # ============================================================
    # FALLBACK: P/S ratio or Industry PE median when PE anchor unavailable
    # ============================================================
    no_pe_anchor = (pe_percentile is None and layer1_value == current_price)

    if no_pe_anchor:
        fallback_value = _calculate_fallback_value(analysis, current_price, calc_metrics, industry_config)
        if fallback_value and fallback_value > 0:
            layer1_value = fallback_value
            layer2_growth_value = layer1_value * (1 + min(growth_additive, MAX_TOTAL_PREMIUM * 0.6))
            layer3_moat_value = layer1_value * (1 + min(growth_additive + moat_additive, MAX_TOTAL_PREMIUM))
            no_pe_anchor = False
            core_value_method = 'fallback_ps'
        else:
            core_value = current_price
            core_value_method = 'current_price'

    if not no_pe_anchor:
        # Weighted average of three layers
        weight1 = 0.50 if layer1_value != current_price else 0.60
        weight2 = 0.30 if total_premium > 0 else 0.20
        weight3 = 0.20 if moat_additive > 0 else 0.20
        total_w = weight1 + weight2 + weight3
        weight1 /= total_w
        weight2 /= total_w
        weight3 /= total_w

        core_value = (
            layer1_value * weight1 +
            layer2_growth_value * weight2 +
            layer3_moat_value * weight3
        )
        core_value_method = 'pe_percentile'
        if growth_additive > 0:
            core_value_method += f'+growth{int(growth_additive*100)}%'
        if moat_additive > 0:
            core_value_method += f'+moat{int(moat_additive*100)}%'

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


def _is_stable_sector(symbol: str) -> bool:
    """Check if a symbol is in a stable/regulated sector where high PE percentile is normal."""
    stable_symbols = {
        'DUK': 'Utilities', 'NEE': 'Utilities', 'SO': 'Utilities',
        'EXC': 'Utilities', 'AEP': 'Utilities', 'XEL': 'Utilities',
        'CEG': 'Utilities', 'VST': 'Utilities', 'NRG': 'Utilities',
        'JPM': 'Financials', 'BAC': 'Financials', 'WFC': 'Financials',
        'GS': 'Financials', 'MS': 'Financials',
    }
    clean = symbol.split('.')[0].upper()
    return clean in stable_symbols


def _get_sector_for_symbol(symbol: str) -> str:
    """Get sector classification for a symbol."""
    clean = symbol.split('.')[0].upper()
    sector_map = {
        'NVDA': 'Technology', 'AMD': 'Technology', 'AVGO': 'Technology',
        'MSFT': 'Technology', 'AAPL': 'Technology', 'GOOGL': 'Technology', 'GOOG': 'Technology',
        'PLTR': 'Technology', 'HOOD': 'Financials', 'COIN': 'Financials',
        'TSLA': 'Consumer_Discretionary', 'BABA': 'Technology',
        'DUK': 'Utilities', 'CEG': 'Utilities', 'VST': 'Utilities', 'NEE': 'Utilities',
    }
    return sector_map.get(clean, 'Technology')


def _classify_price_vs_range(price: float, lower: float, upper: float, mid: float) -> str:
    """Classify where current price falls relative to valuation range."""
    if price < lower:
        return 'Below Range (Undervalued)'
    elif price < mid:
        return 'Within Range (Undervalued)'
    elif price <= upper:
        return 'Within Range (Fair/Overvalued)'
    else:
        return 'Above Range (Overvalued)'


def calculate_value_deviation(current_price: float, core_value: float, pe_percentile: float = None,
                               growth_premium: float = 0.0, moat_premium: float = 0.0,
                               symbol: str = '') -> dict:
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

    # Industry-specific PE percentile adjustment:
    # Utilities and stable financials have naturally high PE percentiles because
    # they're dividend stocks with predictable earnings. A PE percentile of 94%
    # for DUK is NORMAL (it's always that high), not a red flag.
    is_stable = _is_stable_sector(symbol)
    if is_stable and pe_percentile is not None:
        # For stable sectors, shift PE percentile bands up by 15 points
        # This means a utility at PE percentile 94% acts like a normal stock at 79%
        effective_pe = max(0, min(100, pe_percentile - 15))
    else:
        effective_pe = pe_percentile

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
    # FIX: High PE percentile means the stock is EXPENSIVE relative to its history,
    # NOT cheap. So high percentile should make us MORE cautious, not less.
    # NOTE: We use effective_pe which adjusts for stable sectors (utilities etc.)
    # where naturally high PE percentiles are normal.
    if pe_percentile is not None:
        if effective_pe >= 80:
            # PE at historical high — VERY expensive. Use deviation as primary signal
            # but require stronger evidence (higher discount) to recommend buying
            if deviation_pct < -0.20:
                # Even at high PE, if stock is >20% below adjusted value, consider buying
                status = 'discount'
                action = 'BUY_SMALL'
            elif deviation_pct < -0.05:
                status = 'slight_discount'
                action = 'HOLD'  # Downgrade from BUY_SMALL — PE too high for aggressive buying
            elif deviation_pct <= 0.10:
                status = 'premium'
                action = 'WAIT'
            else:
                status = 'significant_premium'
                action = 'AVOID'
        elif effective_pe >= 60:
            # Above-average PE — somewhat expensive
            if deviation_pct < -0.15:
                status = 'discount'
                action = 'BUY'
            elif deviation_pct < -0.05:
                status = 'slight_discount'
                action = 'BUY_SMALL'
            elif deviation_pct <= 0.05:
                status = 'fair'
                action = 'HOLD'
            elif deviation_pct <= 0.10:
                status = 'premium'
                action = 'WAIT'
            else:
                status = 'significant_premium'
                action = 'AVOID'
        elif effective_pe >= 40:
            # Normal PE range
            if deviation_pct < -0.15:
                status = 'deep_discount'
                action = 'GET_ON_BOARD'
            elif deviation_pct < -0.05:
                status = 'slight_discount'
                action = 'BUY_SMALL'
            elif deviation_pct <= 0.05:
                status = 'fair'
                action = 'HOLD'
            elif deviation_pct <= 0.15:
                status = 'premium'
                action = 'WAIT'
            else:
                status = 'significant_premium'
                action = 'AVOID'
        elif effective_pe >= 20:
            # Below-average PE — potentially undervalued
            if deviation_pct < -0.10:
                status = 'deep_discount'
                action = 'GET_ON_BOARD'
            elif deviation_pct < -0.05:
                status = 'discount'
                action = 'BUY'
            elif deviation_pct <= 0.05:
                status = 'slight_discount'
                action = 'BUY_SMALL'
            elif deviation_pct <= 0.15:
                status = 'fair'
                action = 'HOLD'
            else:
                status = 'premium'
                action = 'WAIT'
        else:
            # Very low PE percentile (<20) — historically cheap, potential deep value
            # but also could be value trap
            if has_strong_premium and deviation_pct < -0.05:
                status = 'discount'
                action = 'BUY'
            elif deviation_pct < -0.15:
                status = 'deep_discount'
                action = 'GET_ON_BOARD'
            elif deviation_pct < -0.05:
                status = 'discount'
                action = 'BUY'
            elif deviation_pct <= 0.05:
                status = 'fair'
                action = 'HOLD'
            else:
                status = 'premium'
                action = 'WAIT'
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

            # Calculate core value with three-layer model (fallback)
            value_data = calculate_core_value(analysis, valuation_data, industry_config)
            core_value_layer = value_data['core_value']

            # Calculate DCF + Shiller valuation range (primary anchor)
            valuation_analysis = analysis.get('valuation_analysis', {})
            valuation_range = valuation_analysis.get('valuation_range', {})
            dcf_result = valuation_analysis.get('dcf_result')
            shiller_result = valuation_analysis.get('shiller_result')

            # Use DCF+Shiller composite as primary core value when available
            if valuation_range and valuation_range.get('valuation_mid'):
                core_value = valuation_range['valuation_mid']
                valuation_lower = valuation_range.get('valuation_lower', core_value * 0.8)
                valuation_upper = valuation_range.get('valuation_upper', core_value * 1.2)
                models = valuation_range.get('models', {}) or {}
                if models.get('dcf') and models.get('shiller'):
                    core_value_source = 'dcf_shiller'
                elif models.get('dcf'):
                    core_value_source = 'dcf'
                elif models.get('shiller'):
                    core_value_source = 'shiller'
                else:
                    core_value_source = 'valuation_range'
            else:
                core_value = core_value_layer
                core_value_source = value_data.get('core_value_method', 'three_layer')
                # Build valuation range from three-layer model
                # Lower bound: conservative PE-anchored value (layer1)
                # Upper bound: full moat-inclusive value (layer3)
                l1 = value_data.get('layer1_value', core_value)
                l3 = value_data.get('layer3_moat_value', core_value * 1.2)
                if l1 and l3:
                    valuation_lower = round(min(l1, core_value * 0.85), 2)
                    valuation_upper = round(max(l3, core_value * 1.15), 2)
                else:
                    # Fallback: 15% band around core value
                    valuation_lower = round(core_value * 0.85, 2)
                    valuation_upper = round(core_value * 1.15, 2)
                # Construct valuation_range dict for JSON output
                valuation_range = {
                    'valuation_lower': valuation_lower,
                    'valuation_mid': core_value,
                    'valuation_upper': valuation_upper,
                    'margin_of_safety': round((core_value - current_price) / core_value, 4) if core_value > 0 else 0,
                    'price_vs_range': _classify_price_vs_range(current_price, valuation_lower, valuation_upper, core_value),
                    'source': core_value_source,
                }

            # Calculate deviation using PE percentile + premiums
            deviation = calculate_value_deviation(
                current_price,
                core_value,
                value_data.get('pe_percentile'),
                value_data.get('layer2_growth_premium', 0),
                value_data.get('layer3_moat_premium', 0),
                symbol=symbol
            )

            # Override deviation with valuation_range bounds if available
            if valuation_lower and valuation_upper:
                if current_price < valuation_lower:
                    deviation['status'] = 'below_range'
                    deviation['action'] = 'GET_ON_BOARD' if not _is_stable_sector(symbol) else 'BUY'
                elif current_price < valuation_lower * 1.05:
                    deviation['status'] = 'near_lower_bound'
                    deviation['action'] = 'BUY'
                elif current_price < core_value:
                    deviation['status'] = 'undervalued'
                    deviation['action'] = 'BUY_SMALL'
                elif current_price <= core_value * 1.05:
                    deviation['status'] = 'fair'
                    deviation['action'] = 'HOLD'
                elif current_price <= valuation_upper:
                    deviation['status'] = 'slight_premium'
                    deviation['action'] = 'WAIT'
                elif current_price <= valuation_upper * 1.10:
                    deviation['status'] = 'premium'
                    deviation['action'] = 'WAIT'
                else:
                    deviation['status'] = 'above_range'
                    deviation['action'] = 'AVOID'
                deviation['deviation_pct'] = round((current_price - core_value) / core_value * 100, 1)

            # Value trap check
            trap = analysis.get('value_trap_analysis', {})
            trap_score = trap.get('trap_score', 0)

            # Industry-specific value trap exemption:
            # Utilities and stable financials rarely have value traps — their
            # business model is inherently stable (regulated monopolies).
            # High trap_score for these sectors is usually a false positive.
            is_stable = _is_stable_sector(symbol)
            effective_trap_threshold = 50 if is_stable else 30

            # Adjust action based on value trap
            if trap_score >= effective_trap_threshold and deviation['action'] in ('GET_ON_BOARD', 'BUY', 'BUY_SMALL'):
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

            # Build assessment with three-layer + DCF/Shiller details
            assessment = {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'core_value': round(core_value, 2),
                'core_value_source': core_value_source,
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
                'valuation_range': valuation_range,
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
                    'dcf_value': dcf_result.get('dcf_value') if dcf_result else None,
                    'dcf_upper': dcf_result.get('dcf_upper') if dcf_result else None,
                    'dcf_lower': dcf_result.get('dcf_lower') if dcf_result else None,
                    'shiller_pe': shiller_result.get('shiller_pe') if shiller_result else None,
                    'shiller_intrinsic_mid': shiller_result.get('shiller_intrinsic_mid') if shiller_result else None,
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

            # Build three-layer + DCF/Shiller display
            if value_data.get('no_pe_anchor') and core_value_source != 'dcf_shiller':
                layer_info = "⚠️ No PE anchor — core value = current price (growth premiums suspended)"
            elif core_value_source in ('dcf_shiller', 'dcf', 'shiller'):
                vr = valuation_range or {}
                dcv = dcf_result
                label = 'DCF+Shiller' if core_value_source == 'dcf_shiller' else core_value_source.upper()
                layer_info = f"{label}: ${core_value:.0f}"
                if dcv and dcv.get('dcf_value'):
                    layer_info += f" (DCF: ${dcv['dcf_value']:.0f}"
                    layer_info += f" [{dcv['dcf_lower']:.0f}-{dcv['dcf_upper']:.0f}])"
                if vr.get('valuation_lower') and vr.get('valuation_upper'):
                    layer_info += f" Range: ${vr['valuation_lower']:.0f}-${vr['valuation_upper']:.0f}"
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
        'engine_version': '3.2.0-dcf-shiller',
        'philosophy': 'Value investing: DCF+Shiller composite (55/45), Graham reference-only, three-layer fallback',
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
    print("VALUE ASSESSMENT ENGINE v3.2.0 (DCF+Shiller Composite)")
    print("=" * 70)
    print("Philosophy: DCF 55% + Shiller P/E 45%, Graham reference-only, three-layer fallback")
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
