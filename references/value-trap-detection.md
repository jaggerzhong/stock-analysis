# Value Trap Detection Reference (价值陷阱检测)

## Overview

**Value Trap Definition:** A stock that appears cheap based on traditional metrics (low P/E, P/B) but is actually a poor investment because the business is deteriorating.

**Key Insight:** Cheap ≠ Good Value

---

## 🚨 Value Trap Warning Signs

### Category 1: Fundamental Deterioration (基本面恶化)

#### 1.1 ROIC < WACC (Capital Destruction)

**The Most Important Test:**

```
ROIC (Return on Invested Capital) = NOPAT / Invested Capital
WACC (Weighted Average Cost of Capital) = Cost of equity × (E/V) + Cost of debt × (D/V) × (1 - Tax rate)

If ROIC < WACC:
├─ The company DESTROYS value with every dollar invested
├─ Growing = Getting worse (value destruction accelerates)
└─ RUN, don't walk, away
```

**Implementation:**
```python
def check_roic_vs_wacc(financials):
    """
    Check if company is destroying value
    
    Returns: (is_value_trap, warning_severity, explanation)
    """
    nopat = financials['operating_income'] * (1 - financials['tax_rate'])
    invested_capital = financials['equity'] + financials['debt'] - financials['cash']
    
    roic = nopat / invested_capital if invested_capital > 0 else 0
    
    # Estimate WACC
    risk_free_rate = 0.045  # 10-Year Treasury
    market_risk_premium = 0.06
    beta = financials.get('beta', 1.0)
    cost_of_equity = risk_free_rate + beta * market_risk_premium
    
    cost_of_debt = financials.get('interest_expense', 0) / max(financials['debt'], 1)
    tax_rate = financials.get('tax_rate', 0.25)
    
    equity_weight = financials['equity'] / (financials['equity'] + financials['debt'])
    debt_weight = 1 - equity_weight
    
    wacc = (
        cost_of_equity * equity_weight +
        cost_of_debt * (1 - tax_rate) * debt_weight
    )
    
    spread = roic - wacc
    
    if spread < -0.05:  # ROIC more than 5% below WACC
        return True, 'CRITICAL', f"ROIC ({roic:.1%}) << WACC ({wacc:.1%}), massive value destruction"
    elif spread < 0:
        return True, 'HIGH', f"ROIC ({roic:.1%}) < WACC ({wacc:.1%}), destroying value"
    else:
        return False, 'LOW', f"ROIC ({roic:.1%}) > WACC ({wacc:.1%}), creating value"
```

#### 1.2 Negative Free Cash Flow Trend

**FCF = Operating Cash Flow - Capital Expenditures**

```python
def check_fcf_trend(financials):
    """
    Check free cash flow trend
    
    Warning signs:
    - FCF negative for 2+ years
    - FCF declining while revenue growing (burning more to grow)
    - FCF margin < -5%
    """
    fcf_history = financials.get('fcf_history', [])
    
    if len(fcf_history) < 3:
        return None, 'INSUFFICIENT_DATA'
    
    # Check recent FCF
    fcf_recent_3yr = fcf_history[-3:]
    negative_count = sum(1 for f in fcf_recent_3yr if f < 0)
    
    if negative_count >= 2:
        return True, f"Negative FCF in {negative_count}/3 years"
    
    # Check FCF trend
    fcf_trend = (fcf_history[-1] - fcf_history[-3]) / abs(fcf_history[-3]) if fcf_history[-3] != 0 else 0
    
    if fcf_trend < -0.3:  # 30% decline
        return True, f"FCF declining: {fcf_trend:.0%} over 3 years"
    
    # Check FCF margin
    fcf_margin = fcf_history[-1] / financials['revenue']
    if fcf_margin < -0.05:
        return True, f"High cash burn: FCF margin = {fcf_margin:.1%}"
    
    return False, "Healthy FCF trend"
```

#### 1.3 Debt Growing Faster Than Revenue

**Leverage Trap:**

```python
def check_debt_growth(financials):
    """
    Check if debt is growing unsustainably
    
    Warning signs:
    - Debt growing > Revenue growth for 3+ years
    - Debt/EBITDA > 5x
    - Interest coverage < 3x
    """
    debt_growth = financials.get('debt_growth_3yr_cagr', 0)
    revenue_growth = financials.get('revenue_growth_3yr_cagr', 0)
    
    warnings = []
    is_trap = False
    
    # 1. Debt growing faster than revenue
    if debt_growth > revenue_growth * 1.5 and debt_growth > 0.05:
        is_trap = True
        warnings.append(f"Debt growing {debt_growth:.1%} vs revenue {revenue_growth:.1%}")
    
    # 2. Debt/EBITDA ratio
    debt_to_ebitda = financials['debt'] / max(financials['ebitda'], 1)
    if debt_to_ebitda > 5:
        is_trap = True
        warnings.append(f"High leverage: Debt/EBITDA = {debt_to_ebitda:.1f}x")
    elif debt_to_ebitda > 3:
        warnings.append(f"Elevated leverage: Debt/EBITDA = {debt_to_ebitda:.1f}x")
    
    # 3. Interest coverage
    interest_coverage = financials['ebit'] / max(financials['interest_expense'], 1)
    if interest_coverage < 3:
        is_trap = True
        warnings.append(f"Low interest coverage: {interest_coverage:.1f}x")
    elif interest_coverage < 5:
        warnings.append(f"Tight interest coverage: {interest_coverage:.1f}x")
    
    return is_trap, warnings
```

---

### Category 2: Earnings Quality Issues (盈利质量问题)

#### 2.1 Revenue Quality: AR Growing Faster Than Revenue

**Channel Stuffing / Aggressive Recognition:**

```python
def check_revenue_quality(financials):
    """
    Check if revenue growth is backed by cash collection
    
    Warning signs:
    - AR growing faster than revenue
    - DSO (Days Sales Outstanding) increasing
    - Revenue up but cash not collected
    """
    ar_growth = financials.get('ar_growth', 0)
    revenue_growth = financials.get('revenue_growth', 0)
    
    warnings = []
    is_trap = False
    
    # 1. AR vs Revenue growth
    if ar_growth > revenue_growth * 1.5 and ar_growth > 0.1:
        is_trap = True
        warnings.append(f"AR growing {ar_growth:.1%} vs revenue {revenue_growth:.1%} - potential channel stuffing")
    
    # 2. Days Sales Outstanding trend
    dso_current = financials['ar'] / (financials['revenue'] / 365)
    dso_prior = financials.get('ar_prior') / (financials.get('revenue_prior') / 365)
    
    if dso_current > dso_prior * 1.2:
        warnings.append(f"DSO increased: {dso_prior:.0f} → {dso_current:.0f} days")
        is_trap = True
    
    # 3. Cash conversion
    operating_cf = financials.get('operating_cash_flow', 0)
    net_income = financials.get('net_income', 0)
    
    if operating_cf < net_income * 0.5:
        warnings.append(f"Poor cash conversion: OCF/NI = {operating_cf/net_income:.1%}")
        is_trap = True
    
    return is_trap, warnings
```

#### 2.2 Earnings Quality: Accruals Anomaly

**High Accruals = Low Quality Earnings:**

```python
def check_accruals_quality(financials):
    """
    Sloan's Accrual Anomaly:
    - High accruals = Low future returns
    - Low accruals = High future returns
    
    Accruals = NI - Operating Cash Flow
    Accruals/Assets > 20% = Warning
    """
    net_income = financials['net_income']
    operating_cf = financials['operating_cash_flow']
    total_assets = financials['total_assets']
    
    accruals = net_income - operating_cf
    accruals_to_assets = accruals / total_assets
    
    if accruals_to_assets > 0.20:
        return True, f"High accruals: {accruals_to_assets:.1%} of assets - earnings quality concern"
    elif accruals_to_assets > 0.10:
        return False, f"Elevated accruals: {accruals_to_assets:.1%} - monitor closely"
    else:
        return False, f"Healthy accruals: {accruals_to_assets:.1%}"
```

#### 2.3 One-Time Gains Masking Weakness

```python
def check_one_time_gains(financials):
    """
    Check if earnings are propped up by non-recurring items
    
    Warning signs:
    - Large one-time gains (asset sales, tax benefits)
    - Restructuring charges every year
    - "Non-recurring" items that recur
    """
    warnings = []
    is_trap = False
    
    net_income = financials['net_income']
    net_income_continuing = financials.get('net_income_continuing', net_income)
    
    one_time_items = net_income - net_income_continuing
    
    if abs(one_time_items) > net_income * 0.3:
        is_trap = True
        warnings.append(f"Significant one-time items: {one_time_items/net_income:.0%} of NI")
    
    # Check for recurring "non-recurring" charges
    restructuring_history = financials.get('restructuring_charges_history', [])
    if len(restructuring_history) >= 3:
        years_with_charges = sum(1 for r in restructuring_history if r > 0)
        if years_with_charges >= 3:
            warnings.append("Restructuring charges are recurring - operational issue")
            is_trap = True
    
    return is_trap, warnings
```

---

### Category 3: Industry/Structural Issues (行业/结构性问题)

#### 3.1 Structural Decline

```python
def check_structural_decline(financials, industry_data):
    """
    Check if industry is in structural decline
    
    Warning signs:
    - Industry revenue declining 3+ years
    - Technology disruption
    - Regulatory headwinds
    - Secular demand decline
    """
    industry_growth_5yr = industry_data.get('revenue_cagr_5yr', 0)
    
    warnings = []
    is_trap = False
    
    if industry_growth_5yr < -0.03:  # -3% CAGR
        is_trap = True
        warnings.append(f"Industry in decline: {industry_growth_5yr:.1%} 5yr CAGR")
    
    # Check disruption risk
    disruption_risk = assess_disruption_risk(financials['industry'])
    if disruption_risk == 'HIGH':
        is_trap = True
        warnings.append("High disruption risk (AI, cloud, streaming, etc.)")
    
    return is_trap, warnings

def assess_disruption_risk(industry):
    """
    Assess technology disruption risk
    """
    high_risk_industries = [
        'Traditional Retail',
        'Print Media',
        'Cable TV',
        'Traditional Banking (consumer)',
        'Oil & Gas (long-term)',
        'Coal',
        'Traditional Auto'
    ]
    
    if industry in high_risk_industries:
        return 'HIGH'
    return 'LOW'
```

#### 3.2 Commodity Trap

```python
def check_commodity_trap(financials):
    """
    Commodity businesses are value traps
    
    Characteristics:
    - No pricing power
    - Price taker, not price maker
    - Cyclical earnings
    - Low ROIC across cycle
    """
    
    # Check if commodity business
    commodity_industries = [
        'Steel', 'Aluminum', 'Copper Mining',
        'Coal', 'Oil & Gas E&P',
        'Airlines', 'Trucking',
        'Paper & Pulp', 'Chemicals (commodity)'
    ]
    
    if financials['industry'] in commodity_industries:
        # These are cyclical - buying at "low P/E" is usually at peak earnings
        return True, "Commodity business - P/E appears low at earnings peak"
    
    return False, "Non-commodity business"
```

#### 3.3 Regulatory Headwinds

```python
def check_regulatory_headwinds(financials, news_data):
    """
    Check for regulatory threats
    
    Warning signs:
    - Antitrust investigations
    - Environmental regulations
    - Price controls
    - Licensing at risk
    """
    # Would need news analysis
    # This is a placeholder for the framework
    pass
```

---

### Category 4: Market Signals (市场信号)

#### 4.1 Insiders Selling

```python
def check_insider_activity(insider_data):
    """
    Check insider buying/selling patterns
    
    Warning signs:
    - Heavy insider selling
    - Executives exercising options and selling immediately
    - No insider buying even at "low" prices
    """
    sells = insider_data.get('sells_6mo', 0)
    buys = insider_data.get('buys_6mo', 0)
    
    if sells > buys * 5 and sells > 0:
        return True, f"Heavy insider selling: {sells} sells vs {buys} buys in 6 months"
    elif sells > buys * 2 and sells > 0:
        return False, f"Insider selling: {sells} sells vs {buys} buys"
    elif buys > sells:
        return False, f"Insider buying: {buys} buys vs {sells} sells - bullish"
    
    return False, "No significant insider activity"
```

#### 4.2 Short Interest Rising

```python
def check_short_interest(market_data):
    """
    High short interest can indicate smart money betting against
    
    Warning signs:
    - Short interest > 15% of float
    - Increasing short interest
    - Days to cover > 10
    """
    short_pct = market_data.get('short_pct_of_float', 0)
    short_change = market_data.get('short_interest_change_30d', 0)
    
    if short_pct > 0.20:
        return True, f"Very high short interest: {short_pct:.0%} of float"
    elif short_pct > 0.15 and short_change > 0.1:
        return True, f"High and rising short interest: {short_pct:.0%}, +{short_change:.0%}"
    elif short_pct > 0.10:
        return False, f"Elevated short interest: {short_pct:.0%}"
    
    return False, f"Normal short interest: {short_pct:.0%}"
```

#### 4.3 Dividend Trap

```python
def check_dividend_trap(financials):
    """
    High dividend yield can be a trap
    
    Warning signs:
    - Yield > 8% (usually unsustainable)
    - Payout ratio > 80%
    - Dividend cuts in history
    - FCF not covering dividend
    """
    dividend_yield = financials.get('dividend_yield', 0)
    payout_ratio = financials.get('payout_ratio', 0)
    fcf_payout = financials.get('dividends_paid', 0) / max(financials.get('fcf', 1), 1)
    
    warnings = []
    is_trap = False
    
    if dividend_yield > 0.10:
        is_trap = True
        warnings.append(f"Extremely high yield: {dividend_yield:.1%} - likely unsustainable")
    elif dividend_yield > 0.08:
        warnings.append(f"Very high yield: {dividend_yield:.1%} - verify sustainability")
    
    if payout_ratio > 0.90:
        is_trap = True
        warnings.append(f"Unsustainable payout ratio: {payout_ratio:.0%}")
    elif payout_ratio > 0.80:
        warnings.append(f"High payout ratio: {payout_ratio:.0%}")
    
    if fcf_payout > 1.0:
        is_trap = True
        warnings.append(f"Dividend not covered by FCF: {fcf_payout:.1f}x")
    
    return is_trap, warnings
```

---

## 🎯 Comprehensive Value Trap Score

```python
def calculate_value_trap_score(symbol, financials, market_data, insider_data, industry_data):
    """
    Calculate comprehensive value trap risk score
    
    Returns:
        - trap_score: 0-100 (higher = more likely a trap)
        - risk_level: LOW/MEDIUM/HIGH/CRITICAL
        - warnings: List of warning signs
        - recommendation: AVOID/CAUTION/MONITOR/OK
    """
    
    all_warnings = []
    trap_score = 0
    
    # Category 1: Fundamental Deterioration (Max 40 points)
    is_trap_1, warning_1 = check_roic_vs_wacc(financials)
    if is_trap_1:
        trap_score += 25
        all_warnings.append(("ROIC < WACC", warning_1))
    
    is_trap_2, warning_2 = check_fcf_trend(financials)
    if is_trap_2:
        trap_score += 10
        all_warnings.append(("FCF Issues", warning_2))
    
    is_trap_3, warnings_3 = check_debt_growth(financials)
    if is_trap_3:
        trap_score += 15
        all_warnings.append(("Debt Issues", warnings_3))
    
    # Category 2: Earnings Quality (Max 25 points)
    is_trap_4, warnings_4 = check_revenue_quality(financials)
    if is_trap_4:
        trap_score += 15
        all_warnings.append(("Revenue Quality", warnings_4))
    
    is_trap_5, warning_5 = check_accruals_quality(financials)
    if is_trap_5:
        trap_score += 10
        all_warnings.append(("High Accruals", warning_5))
    
    # Category 3: Structural Issues (Max 25 points)
    is_trap_6, warnings_6 = check_structural_decline(financials, industry_data)
    if is_trap_6:
        trap_score += 15
        all_warnings.append(("Structural Decline", warnings_6))
    
    is_trap_7, warning_7 = check_commodity_trap(financials)
    if is_trap_7:
        trap_score += 10
        all_warnings.append(("Commodity Trap", warning_7))
    
    # Category 4: Market Signals (Max 10 points)
    is_trap_8, warning_8 = check_insider_activity(insider_data)
    if is_trap_8:
        trap_score += 5
        all_warnings.append(("Insider Selling", warning_8))
    
    is_trap_9, warning_9 = check_short_interest(market_data)
    if is_trap_9:
        trap_score += 5
        all_warnings.append(("Short Interest", warning_9))
    
    # Determine risk level
    if trap_score >= 50:
        risk_level = 'CRITICAL'
        recommendation = 'AVOID'
    elif trap_score >= 30:
        risk_level = 'HIGH'
        recommendation = 'AVOID or very small position'
    elif trap_score >= 15:
        risk_level = 'MEDIUM'
        recommendation = 'CAUTION - Require extra margin of safety'
    else:
        risk_level = 'LOW'
        recommendation = 'OK - Standard analysis'
    
    return {
        'symbol': symbol,
        'trap_score': trap_score,
        'risk_level': risk_level,
        'warnings': all_warnings,
        'recommendation': recommendation
    }
```

---

## 📊 Value Trap Examples

### Example 1: Classic Value Trap

```
Symbol: XYZ (Generic Manufacturing Company)

Financial Metrics (appears cheap):
├─ P/E: 8x (vs market 22x)
├─ P/B: 0.7x
├─ Dividend Yield: 9%
└─ EV/EBITDA: 5x

Value Trap Analysis:
├─ ROIC: 6% vs WACC: 10% → Value destruction (-15 pts)
├─ FCF: Negative 2 of 3 years → Cash burn (-10 pts)
├─ Debt/EBITDA: 6x → Overleveraged (-10 pts)
├─ AR growth: 25% vs Revenue: 5% → Channel stuffing (-15 pts)
├─ Industry: Declining -5% CAGR → Structural decline (-15 pts)
├─ Insider: Heavy selling → Smart money exiting (-5 pts)
└─ Dividend: Not covered by FCF → Cut likely (-10 pts)

Trap Score: 80/100 → CRITICAL
Recommendation: AVOID
```

### Example 2: Not a Value Trap (Quality Company)

```
Symbol: ABC (Quality Tech Company)

Financial Metrics (appears expensive but justified):
├─ P/E: 25x (vs market 22x)
├─ P/B: 8x
├─ ROIC: 35% vs WACC: 9% → Creating massive value
├─ FCF: Positive 5 years running
├─ Debt: Minimal (net cash)
├─ Industry: Growing 12% CAGR
└─ Insider: Buying

Trap Score: 5/100 → LOW
Recommendation: OK - Premium valuation justified
```

---

## Integration with Stock Analysis Skill

**In Step 3 (Position Analysis), before recommending:**

```python
def analyze_position_with_trap_detection(symbol, financials, ...):
    """
    Analyze position with value trap detection
    """
    # First, check for value trap
    trap_analysis = calculate_value_trap_score(symbol, financials, ...)
    
    if trap_analysis['risk_level'] in ['HIGH', 'CRITICAL']:
        return {
            'action': 'SELL' if has_position else 'AVOID',
            'reason': f"Value trap risk: {trap_analysis['trap_score']}/100",
            'warnings': trap_analysis['warnings']
        }
    
    # Continue with standard analysis if not a trap
    ...
```

---

## Quick Checklist: Value Trap Red Flags

Before buying any "cheap" stock:

- [ ] ROIC > WACC?
- [ ] FCF positive 2/3 recent years?
- [ ] Debt/EBITDA < 4x?
- [ ] Interest coverage > 4x?
- [ ] AR growth ≤ Revenue growth?
- [ ] Industry NOT in structural decline?
- [ ] Dividend covered by FCF?
- [ ] Insiders not selling heavily?

**If 3+ boxes unchecked → HIGH value trap risk**
