# ROIC Analysis Reference (资本效率分析)

## Overview

**ROIC (Return on Invested Capital)** is the most important metric for evaluating business quality.

**Warren Buffett:** "The primary test of a business's quality is its return on invested capital."

**Charlie Munger:** "Over the long term, it's hard for a stock to earn a much better return than the business which underlies it earns."

---

## 📊 ROIC Formula

### Basic Formula

```
ROIC = NOPAT / Invested Capital

Where:
NOPAT = Operating Income × (1 - Tax Rate)
Invested Capital = Equity + Debt - Cash
```

### Detailed Calculation

```python
def calculate_roic(financials):
    """
    Calculate ROIC with detailed breakdown
    
    Returns:
        - roic: Return on invested capital
        - components: Breakdown of calculation
        - quality_score: Interpretation
    """
    # NOPAT (Net Operating Profit After Tax)
    operating_income = financials['operating_income']  # EBIT
    tax_rate = financials.get('effective_tax_rate', 0.21)
    nopat = operating_income * (1 - tax_rate)
    
    # Invested Capital
    equity = financials['shareholders_equity']
    debt = financials.get('total_debt', financials.get('long_term_debt', 0))
    cash = financials.get('cash_and_equivalents', 0)
    
    invested_capital = equity + debt - cash
    
    # Handle edge cases
    if invested_capital <= 0:
        return None, "Negative invested capital"
    
    roic = nopat / invested_capital
    
    # Components breakdown
    components = {
        'operating_income': operating_income,
        'tax_rate': tax_rate,
        'nopat': nopat,
        'equity': equity,
        'debt': debt,
        'cash': cash,
        'invested_capital': invested_capital,
        'roic': roic
    }
    
    return roic, components


def interpret_roic(roic, industry_avg=None):
    """
    Interpret ROIC quality
    
    ROIC Quality Scale:
    - >25%: Exceptional (Buffett-level)
    - 20-25%: Excellent
    - 15-20%: Good
    - 10-15%: Average
    - 5-10%: Below Average
    - <5%: Poor
    - <WACC: Value Destruction
    """
    if roic is None:
        return 'UNDEFINED'
    
    if roic >= 0.25:
        return 'EXCEPTIONAL'
    elif roic >= 0.20:
        return 'EXCELLENT'
    elif roic >= 0.15:
        return 'GOOD'
    elif roic >= 0.10:
        return 'AVERAGE'
    elif roic >= 0.05:
        return 'BELOW_AVERAGE'
    else:
        return 'POOR'
```

---

## 🎯 ROIC vs WACC: The Value Creation Test

### The Most Important Test

```
If ROIC > WACC:
├─ Company creates value with every dollar invested
├─ Growth = Good (more value created)
└─ Can justify premium valuation

If ROIC < WACC:
├─ Company DESTROYS value with every dollar invested
├─ Growth = BAD (more value destroyed)
└─ Should trade at discount or be avoided
```

### WACC Calculation

```python
def calculate_wacc(financials, market_data):
    """
    Calculate Weighted Average Cost of Capital
    
    WACC = E/V × Re + D/V × Rd × (1 - T)
    
    Where:
    Re = Cost of Equity (CAPM)
    Rd = Cost of Debt
    E = Market value of equity
    D = Market value of debt
    V = E + D
    T = Corporate tax rate
    """
    # Risk-free rate (10-year Treasury)
    risk_free_rate = 0.045  # Update based on current rates
    
    # Market risk premium
    market_risk_premium = 0.06  # Historical average ~6%
    
    # Beta
    beta = financials.get('beta', 1.0)
    
    # Cost of Equity (CAPM)
    cost_of_equity = risk_free_rate + beta * market_risk_premium
    
    # Cost of Debt
    interest_expense = financials.get('interest_expense', 0)
    total_debt = financials.get('total_debt', 0)
    cost_of_debt = interest_expense / total_debt if total_debt > 0 else 0.05
    
    # Capital Structure
    market_cap = market_data.get('market_cap', financials['shareholders_equity'])
    debt_value = total_debt  # Simplified: use book value of debt
    total_value = market_cap + debt_value
    
    equity_weight = market_cap / total_value
    debt_weight = debt_value / total_value
    
    # Tax rate
    tax_rate = financials.get('effective_tax_rate', 0.21)
    
    # WACC
    wacc = (
        equity_weight * cost_of_equity +
        debt_weight * cost_of_debt * (1 - tax_rate)
    )
    
    return {
        'wacc': wacc,
        'cost_of_equity': cost_of_equity,
        'cost_of_debt': cost_of_debt,
        'equity_weight': equity_weight,
        'debt_weight': debt_weight
    }


def calculate_roic_wacc_spread(financials, market_data):
    """
    Calculate ROIC - WACC spread
    
    This is the most important metric for value creation
    """
    roic, _ = calculate_roic(financials)
    wacc_data = calculate_wacc(financials, market_data)
    wacc = wacc_data['wacc']
    
    spread = roic - wacc
    
    interpretation = {
        spread > 0.15: "Exceptional value creation",
        spread > 0.10: "Strong value creation",
        spread > 0.05: "Good value creation",
        spread > 0: "Modest value creation",
        spread > -0.05: "Slight value destruction",
        spread <= -0.05: "Significant value destruction"
    }
    
    message = interpretation.get(True, "Unknown")
    
    return {
        'roic': roic,
        'wacc': wacc,
        'spread': spread,
        'interpretation': message,
        'quality': 'GOOD' if spread > 0 else 'BAD'
    }
```

---

## 📈 ROIC by Business Model

### Asset-Light vs Asset-Heavy

```
Asset-Light Businesses (Higher ROIC):
├─ Software: 40-60% ROIC
│   Examples: Microsoft, Adobe, Salesforce
├─ Platforms: 30-50% ROIC
│   Examples: Google, Meta, Visa
├─ Luxury Brands: 25-35% ROIC
│   Examples: LVMH, Hermès
└─ Consulting: 20-30% ROIC

Asset-Heavy Businesses (Lower ROIC):
├─ Manufacturing: 8-15% ROIC
├─ Utilities: 6-10% ROIC
├─ Airlines: 5-10% ROIC (bad business)
├─ Retail: 10-15% ROIC
└─ Banks: 10-15% ROIC (different model)
```

### ROIC Benchmarks by Industry

```python
INDUSTRY_ROIC_BENCHMARKS = {
    # Technology
    'Software': 0.30,
    'Semiconductors': 0.18,
    'Hardware': 0.15,
    'IT Services': 0.15,
    
    # Platforms
    'Internet Platforms': 0.35,
    'Social Media': 0.30,
    'E-commerce': 0.12,
    
    # Consumer
    'Luxury Goods': 0.28,
    'Consumer Staples': 0.18,
    'Apparel': 0.15,
    'Restaurants': 0.15,
    
    # Healthcare
    'Pharmaceuticals': 0.22,
    'Biotech': 0.12,  # High variance
    'Medical Devices': 0.18,
    'Healthcare Services': 0.12,
    
    # Financials
    'Banking': 0.12,
    'Insurance': 0.10,
    'Asset Management': 0.25,
    'Payments': 0.30,
    
    # Industrial
    'Aerospace & Defense': 0.12,
    'Machinery': 0.12,
    'Construction': 0.08,
    
    # Energy
    'Oil & Gas': 0.10,
    'Utilities': 0.08,
    'Renewable Energy': 0.08,
    
    # Other
    'Airlines': 0.06,
    'Auto Manufacturers': 0.08,
    'Real Estate': 0.08,
}

def get_roic_percentile(roic, industry):
    """
    Get ROIC percentile within industry
    """
    benchmark = INDUSTRY_ROIC_BENCHMARKS.get(industry, 0.12)
    
    if roic >= benchmark * 1.5:
        return 'TOP_DECILE'
    elif roic >= benchmark * 1.2:
        return 'TOP_QUARTILE'
    elif roic >= benchmark:
        return 'ABOVE_AVERAGE'
    elif roic >= benchmark * 0.8:
        return 'AVERAGE'
    else:
        return 'BOTTOM_QUARTILE'
```

---

## 🔄 ROIC Trend Analysis

### Is ROIC Improving or Declining?

```python
def analyze_roic_trend(financials_history):
    """
    Analyze ROIC trend over time
    
    Important: 
    - Improving ROIC = Moat strengthening
    - Declining ROIC = Competitive pressure
    """
    if len(financials_history) < 5:
        return "INSUFFICIENT_DATA"
    
    roic_values = []
    for year in financials_history:
        roic, _ = calculate_roic(year)
        if roic is not None:
            roic_values.append(roic)
    
    if len(roic_values) < 5:
        return "INSUFFICIENT_DATA"
    
    # Calculate trend
    recent_3yr_avg = sum(roic_values[-3:]) / 3
    prior_3yr_avg = sum(roic_values[:3]) / 3
    
    change = (recent_3yr_avg - prior_3yr_avg) / prior_3yr_avg if prior_3yr_avg > 0 else 0
    
    # Determine trend
    if change > 0.15:
        trend = 'STRONG_IMPROVEMENT'
        message = "ROIC improving significantly"
    elif change > 0.05:
        trend = 'IMPROVING'
        message = "ROIC improving"
    elif change > -0.05:
        trend = 'STABLE'
        message = "ROIC stable"
    elif change > -0.15:
        trend = 'DECLINING'
        message = "ROIC declining - competitive pressure"
    else:
        trend = 'SHARP_DECLINE'
        message = "ROIC declining sharply - major concern"
    
    return {
        'trend': trend,
        'message': message,
        'roic_values': roic_values,
        'recent_avg': recent_3yr_avg,
        'prior_avg': prior_3yr_avg,
        'change_pct': change
    }
```

---

## 💰 ROIC to Valuation Framework

### Intrinsic Value from ROIC

**Key Insight:** Companies that can reinvest at high ROIC deserve higher valuations.

```python
def calculate_value_from_roic(financials, market_data, growth_rate):
    """
    Estimate intrinsic value based on ROIC and growth
    
    Formula:
    Value = Invested Capital × (ROIC - WACC) / WACC × (1 + Growth)
    
    This is a simplified version. Full DCF would be more accurate.
    """
    roic, components = calculate_roic(financials)
    wacc_data = calculate_wacc(financials, market_data)
    wacc = wacc_data['wacc']
    
    invested_capital = components['invested_capital']
    
    # Economic profit
    economic_profit = invested_capital * (roic - wacc)
    
    # Present value of economic profit (simplified perpetuity)
    if wacc > growth_rate:
        value_of_future_ep = economic_profit / (wacc - growth_rate)
    else:
        value_of_future_ep = economic_profit / wacc  # Cap at WACC
    
    # Total intrinsic value
    intrinsic_value = invested_capital + value_of_future_ep
    
    return {
        'invested_capital': invested_capital,
        'economic_profit': economic_profit,
        'value_of_future_ep': value_of_future_ep,
        'intrinsic_value': intrinsic_value,
        'current_market_cap': market_data['market_cap'],
        'premium_discount': (intrinsic_value / market_data['market_cap'] - 1)
    }
```

### ROIC-Based P/E Multiple

```python
def estimate_fair_pe_from_roic(roic, growth_rate, wacc, payout_ratio=0.5):
    """
    Estimate fair P/E based on ROIC
    
    Higher ROIC + Growth = Higher justified P/E
    
    Formula:
    Fair P/E = (ROIC - g) / (WACC - g) × (1 - payout_ratio) + payout_ratio / (WACC - g)
    
    Simplified version for illustrative purposes
    """
    if roic <= 0 or wacc <= 0:
        return None
    
    # Growth rate (max at ROIC × retention)
    sustainable_growth = roic * (1 - payout_ratio)
    effective_growth = min(growth_rate, sustainable_growth)
    
    # Fair P/E approximation
    if wacc > effective_growth:
        pe_ratio = (roic - effective_growth) / (wacc - effective_growth) * 10
        # Normalized around 10x base
    else:
        pe_ratio = roic / wacc * 15
    
    return max(5, min(50, pe_ratio))  # Cap between 5x and 50x
```

---

## 📊 ROIC Analysis Output Template

```markdown
## ROIC Analysis: [SYMBOL]

### Current ROIC
- ROIC: 25.3%
- Industry Average: 15.0%
- Percentile: TOP_DECILE

### Value Creation Test
- ROIC: 25.3%
- WACC: 9.5%
- Spread: +15.8% ✅
- Interpretation: Exceptional value creation

### ROIC Trend (5-Year)
- 2022: 22.1%
- 2023: 23.5%
- 2024: 24.8%
- 2025: 25.3%
- Trend: IMPROVING ✅
- Moat: Strengthening

### ROIC Breakdown
- Operating Margin: 28%
- Asset Turnover: 0.9x
- Capital Structure: 90% equity, 10% debt

### Peer Comparison
| Company | ROIC | WACC | Spread | Rating |
|---------|------|------|--------|--------|
| [SYMBOL] | 25.3% | 9.5% | +15.8% | ⭐⭐⭐⭐⭐ |
| Peer A | 18.2% | 10.1% | +8.1% | ⭐⭐⭐⭐ |
| Peer B | 12.5% | 9.8% | +2.7% | ⭐⭐⭐ |
| Peer C | 6.1% | 10.5% | -4.4% | ⭐ |

### Investment Implication
- ROIC Quality: EXCEPTIONAL
- Growth Quality: Value-creating
- Valuation Support: Can justify premium P/E
- Position Size: Can be larger (high quality)
```

---

## Integration with Stock Analysis

### In Step 2 (Watchlist Analysis):

```python
def analyze_with_roic(symbol, financials, market_data):
    """
    Analyze stock with ROIC as quality filter
    """
    # Calculate ROIC
    roic, components = calculate_roic(financials)
    roic_spread = calculate_roic_wacc_spread(financials, market_data)
    roic_trend = analyze_roic_trend(financials['history'])
    
    # Quality assessment
    if roic_spread['quality'] == 'BAD':
        # Value destruction - reduce or avoid
        quality_score = 3
        recommendation = "Value destruction - AVOID or minimal position"
    elif roic_trend['trend'] == 'SHARP_DECLINE':
        quality_score = 5
        recommendation = "ROIC declining - CAUTION"
    elif roic > 0.20 and roic_spread['spread'] > 0.10:
        quality_score = 9
        recommendation = "Exceptional business quality"
    elif roic > 0.15:
        quality_score = 7
        recommendation = "Good business quality"
    else:
        quality_score = 5
        recommendation = "Average business quality"
    
    return {
        'roic': roic,
        'wacc': roic_spread['wacc'],
        'spread': roic_spread['spread'],
        'trend': roic_trend,
        'quality_score': quality_score,
        'recommendation': recommendation
    }
```

### ROIC's Impact on Position Sizing:

```python
def adjust_position_for_roic(base_position, roic):
    """
    Adjust position size based on ROIC
    
    Higher ROIC = Higher conviction = Larger position
    """
    if roic >= 0.25:
        return base_position * 1.3  # 30% larger
    elif roic >= 0.20:
        return base_position * 1.15  # 15% larger
    elif roic >= 0.15:
        return base_position  # Standard
    elif roic >= 0.10:
        return base_position * 0.75  # 25% smaller
    else:
        return base_position * 0.5  # 50% smaller - quality concern
```

---

## Quick Reference

### ROIC Quality Checklist

- [ ] ROIC > 15%? (Good business)
- [ ] ROIC > WACC? (Creating value)
- [ ] ROIC > Industry average? (Competitive advantage)
- [ ] ROIC trend stable or improving? (Moat intact)
- [ ] ROIC spread > 10%? (Strong value creation)

**If all checked:** Quality business, can justify premium valuation
**If 3-4 checked:** Decent business, standard valuation
**If <3 checked:** Quality concerns, require discount

### Key Takeaways

1. **ROIC is the ultimate measure of business quality**
2. **ROIC > WACC = Value creation; ROIC < WACC = Value destruction**
3. **Improving ROIC = Moat strengthening**
4. **High ROIC businesses deserve premium valuations**
5. **Always check ROIC before investing in "cheap" stocks**
