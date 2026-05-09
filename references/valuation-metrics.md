# Extended Valuation Metrics Reference (估值指标体系)

## Overview

Comprehensive valuation framework combining traditional multiples, growth-adjusted metrics, and intrinsic value models.

---

## 📊 Traditional Valuation Multiples

### 1. Price-to-Earnings (P/E) Ratio

**Formula:**
```
P/E Ratio = Market Price per Share / Earnings per Share (EPS)

Variations:
- Trailing P/E: Based on last 12 months earnings
- Forward P/E: Based on next 12 months earnings estimates
```

**Interpretation:**
| P/E Ratio | Valuation Level | Typical Sectors |
|-----------|----------------|-----------------|
| < 10 | Undervalued/Value Trap | Banks, Energy, Utilities |
| 10 - 15 | Fair Value | Industrials, Consumer Staples |
| 15 - 25 | Growth Premium | Technology, Healthcare |
| 25 - 40 | High Growth Expectation | Software, Biotech |
| > 40 | Speculative | Early-stage, High-growth |

**Calculation with Sector Adjustment:**
```python
def calculate_pe_ratio(price, eps, sector=None):
    """
    Calculate P/E ratio with sector context
    
    Args:
        price: Current stock price
        eps: Earnings per share (trailing or forward)
        sector: Industry sector for comparison
    
    Returns:
        pe_ratio: P/E ratio
        percentile: Percentile vs sector
    """
    pe_ratio = price / eps if eps > 0 else None
    
    # Sector benchmarks (example values)
    sector_benchmarks = {
        'Technology': {'median': 22, 'range': (15, 35)},
        'Healthcare': {'median': 18, 'range': (12, 30)},
        'Financials': {'median': 12, 'range': (8, 18)},
        'Consumer Staples': {'median': 16, 'range': (12, 22)},
        'Utilities': {'median': 14, 'range': (10, 18)},
        'Industrials': {'median': 15, 'range': (10, 22)},
        'Energy': {'median': 10, 'range': (6, 15)},
        'Consumer Discretionary': {'median': 18, 'range': (12, 28)}
    }
    
    percentile = None
    if pe_ratio and sector and sector in sector_benchmarks:
        bench = sector_benchmarks[sector]
        if pe_ratio < bench['range'][0]:
            percentile = 'Low'
        elif pe_ratio > bench['range'][1]:
            percentile = 'High'
        else:
            percentile = 'Average'
    
    return pe_ratio, percentile
```

---

### 2. Price-to-Book (P/B) Ratio

**Formula:**
```
P/B Ratio = Market Price per Share / Book Value per Share

Where:
Book Value per Share = (Total Assets - Total Liabilities) / Shares Outstanding
```

**Interpretation:**
| P/B Ratio | Valuation Level | Interpretation |
|-----------|----------------|----------------|
| < 1.0 | Undervalued | Trading below asset value |
| 1.0 - 1.5 | Fair Value | Reasonable asset valuation |
| 1.5 - 3.0 | Growth Premium | Intangible assets/growth |
| > 3.0 | High Growth | Strong intangible assets |

**Sector Considerations:**
- **Low P/B (< 1.5):** Banks, Insurance, Asset-heavy businesses
- **High P/B (> 3.0):** Technology, Pharma, High-ROE businesses

---

### 3. Enterprise Value to EBITDA (EV/EBITDA)

**Formula:**
```
EV/EBITDA = Enterprise Value / EBITDA

Where:
Enterprise Value = Market Cap + Debt - Cash
EBITDA = Earnings Before Interest, Taxes, Depreciation, Amortization
```

**Advantages over P/E:**
- Accounts for capital structure (debt/equity)
- Excludes non-cash expenses
- Better for comparing companies with different depreciation policies

**Interpretation:**
| EV/EBITDA | Valuation Level | Typical Sectors |
|-----------|----------------|-----------------|
| < 6 | Undervalued | Basic Materials, Industrials |
| 6 - 10 | Fair Value | Most sectors |
| 10 - 15 | Growth Premium | Technology, Healthcare |
| > 15 | High Growth | Software, Biotech |

**Calculation:**
```python
def calculate_ev_ebitda(market_cap, debt, cash, ebitda):
    """
    Calculate EV/EBITDA ratio
    
    Args:
        market_cap: Market capitalization
        debt: Total debt
        cash: Cash and equivalents
        ebitda: EBITDA
    
    Returns:
        ev_ebitda: EV/EBITDA ratio
    """
    enterprise_value = market_cap + debt - cash
    
    if ebitda <= 0:
        return None
    
    ev_ebitda = enterprise_value / ebitda
    return ev_ebitda
```

---

### 4. Price-to-Sales (P/S) Ratio

**Formula:**
```
P/S Ratio = Market Cap / Total Revenue

Useful for:
- Companies with negative earnings
- High-growth companies
- Comparing within same industry
```

**Interpretation:**
| P/S Ratio | Valuation Level | Typical Companies |
|-----------|----------------|-------------------|
| < 1.0 | Undervalued | Mature, low-margin businesses |
| 1.0 - 2.0 | Fair Value | Most established companies |
| 2.0 - 5.0 | Growth Premium | Growing companies |
| > 5.0 | High Growth | Tech, SaaS, High-margin |

**Sector-Specific Benchmarks:**
- **Retail:** 0.5 - 1.0
- **Software:** 5.0 - 15.0
- **Biotech:** 3.0 - 10.0
- **Consumer Goods:** 1.0 - 3.0

---

## 📈 Growth-Adjusted Valuation Metrics

### 1. PEG Ratio (Price/Earnings to Growth)

**Formula:**
```
PEG Ratio = P/E Ratio / Earnings Growth Rate

Where:
Earnings Growth Rate = Expected annual EPS growth (%)
```

**Interpretation (Peter Lynch):**
| PEG Ratio | Valuation | Action |
|-----------|-----------|--------|
| < 0.5 | Significantly Undervalued | Strong Buy |
| 0.5 - 1.0 | Fair Value or Undervalued | Buy |
| 1.0 - 1.5 | Fairly Valued | Hold |
| 1.5 - 2.0 | Overvalued | Consider Selling |
| > 2.0 | Significantly Overvalued | Sell |

**Calculation:**
```python
def calculate_peg_ratio(pe_ratio, growth_rate, years=5):
    """
    Calculate PEG ratio
    
    Args:
        pe_ratio: Current P/E ratio
        growth_rate: Expected annual earnings growth rate (decimal)
        years: Growth projection period
    
    Returns:
        peg_ratio: PEG ratio
    """
    if growth_rate <= 0:
        return None
    
    peg_ratio = pe_ratio / (growth_rate * 100)  # Convert growth to percentage
    
    return peg_ratio
```

---

### 2. PEGY Ratio (PEG + Yield)

**Formula:**
```
PEGY Ratio = P/E Ratio / (Earnings Growth Rate + Dividend Yield)

Better for dividend-paying companies
```

**Interpretation:**
- Similar to PEG but accounts for dividend income
- < 0.5: Very attractive
- 0.5 - 1.0: Attractive
- > 1.0: Fully valued or overvalued

---

### 3. Price-to-Earnings-Growth-Yield (PEGY)

**Formula:**
```
PEGY = P/E Ratio / (Growth Rate + Dividend Yield)
```

**Example:**
```
Company: JNJ
- P/E: 18x
- Growth: 6%
- Dividend Yield: 2.5%
- PEGY = 18 / (6 + 2.5) = 2.12 → Overvalued
```

---

## 🏦 Cash Flow-Based Valuation

### 1. Price-to-Free-Cash-Flow (P/FCF)

**Formula:**
```
P/FCF = Market Cap / Free Cash Flow

Where:
Free Cash Flow = Operating Cash Flow - Capital Expenditures
```

**Advantages:**
- Harder to manipulate than earnings
- Represents actual cash generation
- Essential for dividend sustainability

**Interpretation:**
| P/FCF | Valuation | Quality |
|-------|-----------|---------|
| < 10 | Very Cheap | High cash generation |
| 10 - 20 | Reasonable | Good cash generation |
| 20 - 30 | Expensive | Moderate cash generation |
| > 30 | Very Expensive | Low cash generation |

---

### 2. Free Cash Flow Yield (FCF Yield)

**Formula:**
```
FCF Yield = Free Cash Flow / Market Cap

Inverse of P/FCF, expressed as percentage
```

**Interpretation:**
| FCF Yield | Attractiveness | Action |
|-----------|----------------|--------|
| > 10% | Very Attractive | Strong Buy |
| 5% - 10% | Attractive | Buy |
| 3% - 5% | Fair | Hold |
| < 3% | Unattractive | Avoid/Sell |

---

## 📐 Intrinsic Value Models

### 1. Discounted Cash Flow (DCF) Model

**Three-Stage DCF Formula:**
```
Intrinsic Value = ∑(FCF_t / (1 + WACC)^t) + Terminal Value / (1 + WACC)^n

Where:
- Stage 1: High growth (3-5 years)
- Stage 2: Transition growth (31-5 years)
- Stage 3: Terminal growth (perpetual)
```

**Simplified DCF Calculation:**
```python
def calculate_dcf_intrinsic_value(
    current_fcf,
    growth_rate_1,
    years_1,
    growth_rate_2,
    years_2,
    terminal_growth_rate,
    wacc,
    shares_outstanding
):
    """
    Calculate DCF intrinsic value per share
    
    Args:
        current_fcf: Current free cash flow
        growth_rate_1: High growth rate (decimal)
        years_1: High growth period years
        growth_rate_2: Transition growth rate (decimal)
        years_2: Transition period years
        terminal_growth_rate: Perpetual growth rate (decimal)
        wacc: Weighted average cost of capital (decimal)
        shares_outstanding: Number of shares
    
    Returns:
        intrinsic_value: Per share intrinsic value
    """
    # Stage 1: High growth
    pv_stage1 = 0
    fcf = current_fcf
    
    for year in range(1, years_1 + 1):
        fcf *= (1 + growth_rate_1)
        pv_stage1 += fcf / ((1 + wacc) ** year)
    
    # Stage 2: Transition growth
    pv_stage2 = 0
    for year in range(years_1 + 1, years_1 + years_2 + 1):
        fcf *= (1 + growth_rate_2)
        pv_stage2 += fcf / ((1 + wacc) ** year)
    
    # Stage 3: Terminal value
    terminal_fcf = fcf * (1 + terminal_growth_rate)
    terminal_value = terminal_fcf / (wacc - terminal_growth_rate)
    pv_terminal = terminal_value / ((1 + wacc) ** (years_1 + years_2))
    
    # Total enterprise value
    enterprise_value = pv_stage1 + pv_stage2 + pv_terminal
    
    # Per share value
    intrinsic_value = enterprise_value / shares_outstanding
    
    return intrinsic_value
```

**Key Assumptions:**
- **WACC (Weighted Average Cost of Capital):** 8-12% for most companies
- **Terminal Growth Rate:** 2-3% (in line with long-term GDP/inflation)
- **Growth Rates:** Based on industry, competitive position, market size

---

### 2. Dividend Discount Model (DDM)

**Formula:**
```
Intrinsic Value = D1 / (r - g)

Where:
D1 = Next year's expected dividend
r = Required rate of return
g = Dividend growth rate
```

**Multi-Stage DDM:**
```python
def calculate_ddm_intrinsic_value(
    current_dividend,
    growth_rate_1,
    years_1,
    growth_rate_2,
    years_2,
    terminal_growth_rate,
    required_return
):
    """
    Calculate DDM intrinsic value
    
    Args:
        current_dividend: Current annual dividend
        growth_rate_1: High growth rate
        years_1: High growth years
        growth_rate_2: Transition growth rate
        years_2: Transition years
        terminal_growth_rate: Perpetual growth rate
        required_return: Investor's required return
    
    Returns:
        intrinsic_value: Per share intrinsic value
    """
    # Similar to DCF but with dividends instead of FCF
    # Implementation similar to DCF above
    pass
```

---

### 3. Graham Formula (Benjamin Graham)

**Original Formula:**
```
Intrinsic Value = EPS × (8.5 + 2g)

Where:
EPS = Earnings per share
g = Expected growth rate for next 7-10 years
```

**Revised Formula (with bond yield adjustment):**
```
Intrinsic Value = [EPS × (8.5 + 2g) × 4.4] / Current AAA Corporate Bond Yield
```

**Calculation:**
```python
def calculate_graham_intrinsic_value(eps, growth_rate, bond_yield):
    """
    Calculate Graham intrinsic value
    
    Args:
        eps: Earnings per share
        growth_rate: Expected growth rate (decimal)
        bond_yield: Current AAA corporate bond yield (decimal)
    
    Returns:
        intrinsic_value: Graham intrinsic value
    """
    if bond_yield <= 0:
        return None
    
    # Original formula
    base_value = eps * (8.5 + 2 * growth_rate * 100)  # Convert growth to percentage
    
    # Adjust for bond yield
    intrinsic_value = (base_value * 4.4) / (bond_yield * 100)
    
    return intrinsic_value
```

---

## 🎯 Relative Valuation Framework

### 1. Comparable Company Analysis (Comps)

**Steps:**
1. Select peer group (similar size, growth, profitability)
2. Calculate valuation multiples for each peer
3. Apply median/mean multiples to target company
4. Derive implied value range

**Peer Selection Criteria:**
- Same industry/sector
- Similar revenue size
- Comparable growth rates
- Similar profitability margins
- Geographic overlap

---

### 2. Sum-of-the-Parts (SOTP) Valuation

**For Conglomerates or Multi-Business Companies:**
```
Total Value = ∑(Business Unit Value)

Where each business unit is valued separately using appropriate multiples
```

**Example:**
```
Company with 3 divisions:
1. Software: 15x EBITDA
2. Hardware: 8x EBITDA  
3. Services: 10x EBITDA
Total = Sum of (EBITDA × Multiple) for each division
```

---

## 📊 Valuation Scorecard System

### Comprehensive Valuation Score

```python
def calculate_valuation_score(valuation_metrics, sector=None):
    """
    Calculate comprehensive valuation score (0-100, lower = more undervalued)
    
    Args:
        valuation_metrics: Dictionary of valuation metrics
        sector: Industry sector for context
    
    Returns:
        score: Valuation score (0-100)
        breakdown: Score breakdown by metric
    """
    scores = {}
    
    # 1. P/E Score (0-100)
    pe_ratio = valuation_metrics.get('pe_ratio')
    if pe_ratio:
        if pe_ratio < 10:
            scores['pe'] = 20  # Very cheap
        elif pe_ratio < 15:
            scores['pe'] = 40  # Cheap
        elif pe_ratio < 20:
            scores['pe'] = 60  # Fair
        elif pe_ratio < 30:
            scores['pe'] = 80  # Expensive
        else:
            scores['pe'] = 100  # Very expensive
    
    # 2. PEG Score (0-100)
    peg_ratio = valuation_metrics.get('peg_ratio')
    if peg_ratio:
        if peg_ratio < 0.5:
            scores['peg'] = 20  # Very cheap
        elif peg_ratio < 1.0:
            scores['peg'] = 40  # Cheap
        elif peg_ratio < 1.5:
            scores['peg'] = 60  # Fair
        elif peg_ratio < 2.0:
            scores['peg'] = 80  # Expensive
        else:
            scores['peg'] = 100  # Very expensive
    
    # 3. P/FCF Score (0-100)
    p_fcf = valuation_metrics.get('p_fcf_ratio')
    if p_fcf:
        if p_fcf < 10:
            scores['p_fcf'] = 20
        elif p_fcf < 15:
            scores['p_fcf'] = 40
        elif p_fcf < 20:
            scores['p_fcf'] = 60
        elif p_fcf < 25:
            scores['p_fcf'] = 80
        else:
            scores['p_fcf'] = 100
    
    # 4. EV/EBITDA Score (0-100)
    ev_ebitda = valuation_metrics.get('ev_ebitda_ratio')
    if ev_ebitda:
        if ev_ebitda < 6:
            scores['ev_ebitda'] = 20
        elif ev_ebitda < 10:
            scores['ev_ebitda'] = 40
        elif ev_ebitda < 15:
            scores['ev_ebitda'] = 60
        elif ev_ebitda < 20:
            scores['ev_ebitda'] = 80
        else:
            scores['ev_ebitda'] = 100
    
    # 5. DCF Margin of Safety (0-100)
    dcf_mos = valuation_metrics.get('dcf_margin_of_safety')
    if dcf_mos:
        if dcf_mos > 0.30:  # >30% discount to DCF
            scores['dcf'] = 20
        elif dcf_mos > 0.15:  # 15-30% discount
            scores['dcf'] = 40
        elif dcf_mos > -0.10:  # -10% to +15%
            scores['dcf'] = 60
        elif dcf_mos > -0.25:  # -25% to -10%
            scores['dcf'] = 80
        else:  # >25% premium
            scores['dcf'] = 100
    
    # Calculate weighted average score
    weights = {
        'pe': 0.20,
        'peg': 0.25,
        'p_fcf': 0.20,
        'ev_ebitda': 0.20,
        'dcf': 0.15
    }
    
    total_score = 0
    total_weight = 0
    breakdown = {}
    
    for metric, weight in weights.items():
        if metric in scores:
            total_score += scores[metric] * weight
            total_weight += weight
            breakdown[metric] = {
                'score': scores[metric],
                'weight': weight,
                'contribution': scores[metric] * weight
            }
    
    if total_weight > 0:
        final_score = total_score / total_weight
    else:
        final_score = 50  # Neutral if no metrics available
    
    return final_score, breakdown
```

**Interpretation:**
| Valuation Score | Attractiveness | Action |
|-----------------|----------------|--------|
| 0-30 | Significantly Undervalued | Strong Buy |
| 30-50 | Undervalued | Buy |
| 50-70 | Fairly Valued | Hold |
| 70-90 | Overvalued | Consider Selling |
| 90-100 | Significantly Overvalued | Sell |

---

## 📈 Sector-Specific Valuation Considerations

### Technology Sector
- **Focus:** P/S, EV/Revenue, P/FCF
- **Key Metrics:** Revenue growth, gross margin, customer acquisition cost
- **Special Cases:** SaaS companies (ARR growth, net dollar retention)

### Financial Sector  
- **Focus:** P/B, P/Tangible Book, Dividend Yield
- **Key Metrics:** ROE, Net Interest Margin, Loan Loss Provisions

### Healthcare Sector
- **Focus:** P/E, EV/EBITDA, Pipeline Value
- **Key Metrics:** R&D efficiency, patent expirations, regulatory milestones

### Consumer Staples
- **Focus:** P/E, Dividend Yield, P/FCF
- **Key Metrics:** Brand strength, pricing power, distribution reach

### Energy Sector
- **Focus:** EV/EBITDA, P/CFPS, Reserve Value
- **Key Metrics:** Production costs, reserve life, commodity price sensitivity

---

## 🎯 Valuation Checklist

### Before Making Valuation Judgment:
1. [ ] Understand the business model and competitive advantages
2. [ ] Check earnings quality (accruals, one-time items)
3. [ ] Verify growth assumptions are realistic
4. [ ] Compare with historical valuation ranges
5. [ ] Consider macroeconomic environment
6. [ ] Assess management quality and capital allocation
7. [ ] Review balance sheet strength
8. [ ] Evaluate industry dynamics and competitive threats

### Red Flags in Valuation:
- Earnings growing but cash flow declining
- High accruals as percentage of assets
- Frequent "one-time" charges
- Aggressive revenue recognition
- Unsustainable growth assumptions
- Dependence on single product/customer

---

## 📋 Implementation in Stock Analysis

### Integration with Existing Framework:

1. **Collect Financial Data:**
   ```bash
   # Get financial statements for valuation metrics
   longbridge financials SYMBOL.US --period annual --count 5
   ```

2. **Calculate Valuation Metrics:**
   ```python
   valuation_data = {
       'pe_ratio': calculate_pe_ratio(price, eps, sector),
       'peg_ratio': calculate_peg_ratio(pe_ratio, growth_rate),
       'ev_ebitda': calculate_ev_ebitda(market_cap, debt, cash, ebitda),
       'p_fcf_ratio': market_cap / free_cash_flow,
       'dcf_value': calculate_dcf_intrinsic_value(...),
       'graham_value': calculate_graham_intrinsic_value(eps, growth_rate, bond_yield)
   }
   ```

3. **Generate Valuation Report:**
   ```markdown
   ## Valuation Analysis
   
   ### Multiples Analysis:
   - P/E Ratio: 18.5x (vs sector avg: 22x) → 15% discount
   - PEG Ratio: 1.2 (Fair value)
   - EV/EBITDA: 10.5x (vs sector: 12x) → 12% discount
   - P/FCF: 15.2x (Attractive)
   
   ### Intrinsic Value Models:
   - DCF Value: $125.40 (Current: $110.20 → 12% discount)
   - Graham Formula: $118.75 (Current: $110.20 → 7% discount)
   
   ### Valuation Score: 42/100 (Undervalued)
   
   ### Recommendation:
   - Current price offers 10-15% margin of safety
   - Buy with target price of $125
   - Stop loss at $95 (14% below current)
   ```

---

## 🎖️ Key Principles

1. **Multiple Methods:** Never rely on a single valuation method
2. **Margin of Safety:** Always require discount to intrinsic value
3. **Quality First:** Better to pay fair price for great business than cheap price for poor business
4. **Context Matters:** Valuation multiples must be considered within sector and market context
5. **Dynamic Assessment:** Update valuation as new information emerges
6. **Patience:** Wait for the right price; opportunities come to those who wait