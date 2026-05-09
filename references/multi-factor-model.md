# Multi-Factor Model Reference (多因子模型)

## Overview

Systematic investment framework combining multiple factors to identify high-quality stocks with attractive valuations and strong momentum.

**Based on academic research:**
- Fama-French Three-Factor Model
- Carhart Four-Factor Model
- Quality, Value, Momentum factors
- Modern factor investing principles

---

## 📊 Factor Categories

### 1. Quality Factors (质量因子)

#### Return on Equity (ROE)
**Formula:**
```
ROE = Net Income / Shareholders' Equity
```

**Interpretation:**
| ROE Level | Quality | Action |
|-----------|---------|--------|
| > 20% | Excellent | Strong buy signal |
| 15% - 20% | Good | Positive factor |
| 10% - 15% | Average | Neutral |
| 5% - 10% | Below Average | Caution |
| < 5% | Poor | Avoid |

**Calculation:**
```python
def calculate_roe(net_income, shareholders_equity):
    """
    Calculate Return on Equity
    
    Args:
        net_income: Annual net income
        shareholders_equity: Average shareholders' equity
    
    Returns:
        roe: ROE percentage
    """
    if shareholders_equity <= 0:
        return None
    
    roe = (net_income / shareholders_equity) * 100
    return roe
```

---

#### Gross Margin (毛利率)
**Formula:**
```
Gross Margin = (Revenue - COGS) / Revenue
```

**Interpretation:**
- **High (>40%):** Strong pricing power, competitive advantage
- **Medium (20-40%):** Average competitive position
- **Low (<20%):** Commodity business, price competition

**Trend Analysis:**
- Improving margins = Increasing competitive advantage
- Declining margins = Competitive pressures

---

#### Earnings Stability (盈利稳定性)
**Measure:** Standard deviation of EPS growth over 5-10 years

**Calculation:**
```python
def calculate_earnings_stability(eps_history):
    """
    Calculate earnings stability score
    
    Args:
        eps_history: List of annual EPS values (5-10 years)
    
    Returns:
        stability_score: 0-100 (higher = more stable)
    """
    import numpy as np
    
    if len(eps_history) < 3:
        return 50
    
    # Calculate EPS growth rates
    growth_rates = []
    for i in range(1, len(eps_history)):
        if eps_history[i-1] != 0:
            growth = (eps_history[i] - eps_history[i-1]) / abs(eps_history[i-1])
            growth_rates.append(growth)
    
    if not growth_rates:
        return 50
    
    # Calculate volatility
    volatility = np.std(growth_rates)
    
    # Convert to score (0-100)
    # Lower volatility = higher score
    if volatility < 0.10:
        score = 90
    elif volatility < 0.20:
        score = 70
    elif volatility < 0.30:
        score = 50
    elif volatility < 0.40:
        score = 30
    else:
        score = 10
    
    return score
```

---

#### Debt-to-Equity Ratio (负债权益比)
**Formula:**
```
D/E Ratio = Total Debt / Shareholders' Equity
```

**Interpretation by Sector:**
| Sector | Healthy D/E | High Risk D/E |
|--------|-------------|---------------|
| Technology | < 0.5 | > 1.0 |
| Utilities | < 1.5 | > 2.5 |
| Industrials | < 1.0 | > 2.0 |
| Financials | < 4.0 | > 8.0 |

---

### 2. Value Factors (价值因子)

#### Price-to-Earnings Ratio (P/E)
**Already covered in valuation metrics**

#### Price-to-Book Ratio (P/B)
**Already covered in valuation metrics**

#### Enterprise Value to EBITDA (EV/EBITDA)
**Already covered in valuation metrics**

#### Free Cash Flow Yield (FCF Yield)
**Formula:**
```
FCF Yield = Free Cash Flow / Market Capitalization
```

**Interpretation:**
| FCF Yield | Valuation | Action |
|-----------|-----------|--------|
| > 10% | Very Cheap | Strong Buy |
| 5% - 10% | Cheap | Buy |
| 3% - 5% | Fair | Hold |
| 1% - 3% | Expensive | Avoid |
| < 1% | Very Expensive | Sell |

---

#### Dividend Yield (股息率)
**Formula:**
```
Dividend Yield = Annual Dividend per Share / Price per Share
```

**Quality Check:**
- **Payout Ratio:** Dividend / EPS < 80% (sustainable)
- **Growth:** Dividend growth rate > inflation
- **Consistency:** No dividend cuts in past 10 years

---

### 3. Growth Factors (成长因子)

#### Revenue Growth (营收增长)
**Formula:**
```
Revenue Growth = (Current Revenue - Previous Revenue) / Previous Revenue
```

**Interpretation:**
| Growth Rate | Category | Typical Companies |
|-------------|----------|-------------------|
| > 20% | High Growth | Tech, Biotech, Emerging markets |
| 10% - 20% | Strong Growth | Most growth companies |
| 5% - 10% | Moderate Growth | Mature companies |
| 0% - 5% | Slow Growth | Defensive, utilities |
| < 0% | Declining | Struggling companies |

**Quality Check:**
- Organic vs acquisition-driven growth
- Sustainable vs one-time growth

---

#### Earnings per Share Growth (EPS增长)
**Formula:**
```
EPS Growth = (Current EPS - Previous EPS) / Previous EPS
```

**Analysis Framework:**
```python
def analyze_eps_growth(eps_history, years=5):
    """
    Analyze EPS growth quality
    
    Args:
        eps_history: List of EPS values (most recent last)
        years: Number of years to analyze
    
    Returns:
        analysis: Dictionary with growth insights
    """
    import numpy as np
    
    if len(eps_history) < years:
        return None
    
    recent_eps = eps_history[-years:]
    
    # Calculate growth rates
    growth_rates = []
    for i in range(1, len(recent_eps)):
        if recent_eps[i-1] != 0:
            growth = (recent_eps[i] - recent_eps[i-1]) / abs(recent_eps[i-1])
            growth_rates.append(growth)
    
    if not growth_rates:
        return None
    
    # Calculate metrics
    avg_growth = np.mean(growth_rates) * 100
    growth_std = np.std(growth_rates) * 100
    consistency = len([g for g in growth_rates if g > 0]) / len(growth_rates)
    
    # Quality assessment
    if avg_growth > 15 and growth_std < 20 and consistency > 0.8:
        quality = 'EXCELLENT'
    elif avg_growth > 10 and growth_std < 25 and consistency > 0.7:
        quality = 'GOOD'
    elif avg_growth > 5:
        quality = 'AVERAGE'
    else:
        quality = 'POOR'
    
    return {
        'average_growth_pct': avg_growth,
        'growth_volatility_pct': growth_std,
        'positive_years_pct': consistency * 100,
        'quality': quality,
        'growth_trend': 'ACCELERATING' if growth_rates[-1] > np.mean(growth_rates[:-1]) else 'DECELERATING'
    }
```

---

#### Future Growth Estimates (未来增长预期)
**Sources:**
- Analyst consensus estimates
- Management guidance
- Industry growth projections

**Reality Check:**
- Compare historical growth vs estimates
- Assess estimate revisions trend
- Consider macro environment

---

### 4. Momentum Factors (动量因子)

#### Price Momentum (价格动量)
**Formulas:**
```
1-Month Momentum = (Current Price / Price 1 month ago) - 1
3-Month Momentum = (Current Price / Price 3 months ago) - 1
6-Month Momentum = (Current Price / Price 6 months ago) - 1
12-Month Momentum = (Current Price / Price 12 months ago) - 1
```

**Academic Research:**
- 12-month momentum strongest (Jegadeesh & Titman, 1993)
- Skip most recent month to avoid reversal
- Momentum persists 3-12 months

**Calculation:**
```python
def calculate_price_momentum(prices, periods=[1, 3, 6, 12]):
    """
    Calculate price momentum for different periods
    
    Args:
        prices: List of historical prices (most recent last)
        periods: List of periods in months
    
    Returns:
        momentum_dict: Dictionary of momentum by period
    """
    momentum_dict = {}
    current_price = prices[-1]
    
    for period in periods:
        if len(prices) >= period * 21:  # ~21 trading days per month
            past_price = prices[-period * 21]
            momentum = (current_price / past_price) - 1
            momentum_dict[f'{period}_month'] = momentum * 100  # Percentage
        else:
            momentum_dict[f'{period}_month'] = None
    
    return momentum_dict
```

---

#### Earnings Momentum (盈利动量)
**Measure:** Earnings estimate revisions

**Calculation:**
```python
def calculate_earnings_momentum(eps_estimates):
    """
    Calculate earnings momentum based on estimate revisions
    
    Args:
        eps_estimates: List of EPS estimate changes
        
    Returns:
        momentum_score: 0-100 (higher = positive momentum)
    """
    if len(eps_estimates) < 4:
        return 50
    
    # Calculate percentage of upward revisions
    upward_revisions = sum(1 for change in eps_estimates if change > 0)
    total_revisions = len(eps_estimates)
    
    upward_ratio = upward_revisions / total_revisions
    
    # Convert to score
    if upward_ratio > 0.7:
        score = 90
    elif upward_ratio > 0.6:
        score = 80
    elif upward_ratio > 0.5:
        score = 70
    elif upward_ratio > 0.4:
        score = 60
    elif upward_ratio > 0.3:
        score = 50
    elif upward_ratio > 0.2:
        score = 40
    else:
        score = 30
    
    return score
```

---

#### Relative Strength (相对强度)
**Formula:**
```
Relative Strength = Stock Return / Benchmark Return

Where Benchmark = S&P 500, sector ETF, or peer group
```

**Interpretation:**
- **RS > 1:** Outperforming benchmark
- **RS < 1:** Underperforming benchmark
- **RS Trend:** Improving vs deteriorating

---

### 5. Low Volatility Factors (低波动因子)

#### Historical Volatility (历史波动率)
**Already covered in risk metrics**

#### Beta Coefficient (贝塔系数)
**Already covered in risk metrics**

#### Downside Capture Ratio (下行捕获率)
**Formula:**
```
Downside Capture = Stock Return in Down Markets / Market Return in Down Markets
```

**Interpretation:**
- **< 80%:** Defensive (loses less in down markets)
- **80% - 120%:** Neutral
- **> 120%:** Aggressive (loses more in down markets)

---

## 🎯 Factor Scoring System

### Individual Factor Scores

```python
def calculate_factor_scores(financials, prices, sector=None):
    """
    Calculate scores for all factor categories
    
    Args:
        financials: Dictionary of financial metrics
        prices: Historical price data
        sector: Industry sector for context
    
    Returns:
        factor_scores: Dictionary of factor scores (0-100)
    """
    scores = {}
    
    # 1. Quality Factors (30% weight)
    quality_score = calculate_quality_score(financials)
    scores['quality'] = {
        'score': quality_score,
        'components': {
            'roe': calculate_roe_score(financials.get('roe')),
            'gross_margin': calculate_margin_score(financials.get('gross_margin')),
            'earnings_stability': financials.get('earnings_stability_score', 50),
            'debt_equity': calculate_debt_score(financials.get('debt_to_equity'), sector)
        }
    }
    
    # 2. Value Factors (25% weight)
    value_score = calculate_value_score(financials, prices[-1] if prices else 0, sector)
    scores['value'] = {
        'score': value_score,
        'components': {
            'pe_ratio': calculate_pe_score(financials.get('pe_ratio'), sector),
            'ev_ebitda': calculate_ev_ebitda_score(financials.get('ev_ebitda'), sector),
            'fcf_yield': calculate_fcf_yield_score(financials.get('fcf_yield')),
            'dividend_yield': calculate_dividend_score(financials.get('dividend_yield'))
        }
    }
    
    # 3. Growth Factors (20% weight)
    growth_score = calculate_growth_score(financials)
    scores['growth'] = {
        'score': growth_score,
        'components': {
            'revenue_growth': calculate_growth_component_score(financials.get('revenue_growth_5yr')),
            'eps_growth': calculate_growth_component_score(financials.get('eps_growth_5yr')),
            'future_growth': calculate_future_growth_score(financials.get('estimated_growth'))
        }
    }
    
    # 4. Momentum Factors (15% weight)
    momentum_score = calculate_momentum_score(prices, financials.get('eps_estimates', []))
    scores['momentum'] = {
        'score': momentum_score,
        'components': {
            'price_momentum': calculate_price_momentum_score(prices),
            'earnings_momentum': calculate_earnings_momentum_score(financials.get('eps_estimate_changes', [])),
            'relative_strength': calculate_relative_strength_score(prices, sector)
        }
    }
    
    # 5. Low Volatility Factors (10% weight)
    volatility_score = calculate_volatility_score(prices)
    scores['low_volatility'] = {
        'score': volatility_score,
        'components': {
            'historical_vol': calculate_volatility_component_score(prices),
            'beta': calculate_beta_score(financials.get('beta', 1.0)),
            'downside_capture': calculate_downside_capture_score(financials.get('downside_capture', 100))
        }
    }
    
    return scores

def calculate_quality_score(financials):
    """Calculate overall quality score"""
    components = []
    weights = []
    
    # ROE component (30%)
    roe = financials.get('roe')
    if roe:
        components.append(calculate_roe_score(roe))
        weights.append(0.30)
    
    # Gross Margin component (25%)
    gross_margin = financials.get('gross_margin')
    if gross_margin:
        components.append(calculate_margin_score(gross_margin))
        weights.append(0.25)
    
    # Earnings Stability (25%)
    stability = financials.get('earnings_stability_score', 50)
    components.append(stability)
    weights.append(0.25)
    
    # Debt/Equity (20%)
    debt_eq = financials.get('debt_to_equity')
    if debt_eq:
        components.append(calculate_debt_score(debt_eq))
        weights.append(0.20)
    
    # Calculate weighted average
    if not components:
        return 50
    
    total_score = 0
    total_weight = 0
    
    for score, weight in zip(components, weights):
        total_score += score * weight
        total_weight += weight
    
    return total_score / total_weight

def calculate_value_score(financials, current_price, sector):
    """Calculate overall value score"""
    components = []
    weights = []
    
    # P/E component (30%)
    pe_ratio = financials.get('pe_ratio')
    if pe_ratio:
        components.append(calculate_pe_score(pe_ratio, sector))
        weights.append(0.30)
    
    # EV/EBITDA component (30%)
    ev_ebitda = financials.get('ev_ebitda')
    if ev_ebitda:
        components.append(calculate_ev_ebitda_score(ev_ebitda, sector))
        weights.append(0.30)
    
    # FCF Yield component (25%)
    fcf_yield = financials.get('fcf_yield')
    if fcf_yield:
        components.append(calculate_fcf_yield_score(fcf_yield))
        weights.append(0.25)
    
    # Dividend Yield component (15%)
    div_yield = financials.get('dividend_yield')
    if div_yield:
        components.append(calculate_dividend_score(div_yield))
        weights.append(0.15)
    
    # Calculate weighted average
    if not components:
        return 50
    
    total_score = 0
    total_weight = 0
    
    for score, weight in zip(components, weights):
        total_score += score * weight
        total_weight += weight
    
    return total_score / total_weight

def calculate_roe_score(roe):
    """Convert ROE to 0-100 score"""
    if roe is None:
        return 50
    
    if roe > 25:
        return 90
    elif roe > 20:
        return 80
    elif roe > 15:
        return 70
    elif roe > 10:
        return 60
    elif roe > 5:
        return 50
    elif roe > 0:
        return 40
    else:
        return 20

def calculate_pe_score(pe_ratio, sector):
    """Convert P/E ratio to 0-100 score (lower P/E = higher score)"""
    if pe_ratio is None or pe_ratio <= 0:
        return 50
    
    # Sector-adjusted scoring
    sector_benchmarks = {
        'Technology': {'cheap': 15, 'expensive': 30},
        'Healthcare': {'cheap': 12, 'expensive': 25},
        'Financials': {'cheap': 8, 'expensive': 15},
        'Consumer Staples': {'cheap': 12, 'expensive': 20},
        'Utilities': {'cheap': 10, 'expensive': 18},
        'Industrials': {'cheap': 10, 'expensive': 18},
        'Energy': {'cheap': 8, 'expensive': 15},
        'Consumer Discretionary': {'cheap': 12, 'expensive': 22}
    }
    
    if sector and sector in sector_benchmarks:
        cheap = sector_benchmarks[sector]['cheap']
        expensive = sector_benchmarks[sector]['expensive']
    else:
        cheap = 12
        expensive = 25
    
    if pe_ratio < cheap:
        return 90  # Very cheap
    elif pe_ratio < (cheap + expensive) / 2:
        return 70  # Cheap
    elif pe_ratio < expensive:
        return 50  # Fair
    elif pe_ratio < expensive * 1.5:
        return 30  # Expensive
    else:
        return 10  # Very expensive

def calculate_fcf_yield_score(fcf_yield):
    """Convert FCF Yield to 0-100 score (higher yield = higher score)"""
    if fcf_yield is None:
        return 50
    
    if fcf_yield > 0.10:
        return 90
    elif fcf_yield > 0.07:
        return 80
    elif fcf_yield > 0.05:
        return 70
    elif fcf_yield > 0.03:
        return 60
    elif fcf_yield > 0.01:
        return 50
    elif fcf_yield > 0:
        return 40
    else:
        return 20
```

---

### Composite Factor Score

```python
def calculate_composite_factor_score(factor_scores, strategy='balanced'):
    """
    Calculate composite factor score based on investment strategy
    
    Args:
        factor_scores: Dictionary of factor category scores
        strategy: Investment strategy type
    
    Returns:
        composite_score: Overall factor score (0-100)
        breakdown: Contribution by factor
    """
    # Strategy weightings
    strategies = {
        'quality_value': {
            'quality': 0.40,
            'value': 0.40,
            'growth': 0.10,
            'momentum': 0.05,
            'low_volatility': 0.05
        },
        'growth_momentum': {
            'quality': 0.20,
            'value': 0.10,
            'growth': 0.40,
            'momentum': 0.25,
            'low_volatility': 0.05
        },
        'balanced': {
            'quality': 0.25,
            'value': 0.25,
            'growth': 0.20,
            'momentum': 0.20,
            'low_volatility': 0.10
        },
        'defensive': {
            'quality': 0.30,
            'value': 0.30,
            'growth': 0.10,
            'momentum': 0.10,
            'low_volatility': 0.20
        },
        'aggressive_growth': {
            'quality': 0.15,
            'value': 0.10,
            'growth': 0.50,
            'momentum': 0.20,
            'low_volatility': 0.05
        }
    }
    
    weights = strategies.get(strategy, strategies['balanced'])
    
    composite_score = 0
    breakdown = {}
    total_weight = 0
    
    for factor, weight in weights.items():
        if factor in factor_scores:
            factor_data = factor_scores[factor]
            factor_value = factor_data.get('score', 50)
            
            contribution = factor_value * weight
            composite_score += contribution
            total_weight += weight
            
            breakdown[factor] = {
                'score': factor_value,
                'weight': weight,
                'contribution': contribution
            }
    
    # Normalize if total_weight < 1
    if total_weight > 0:
        composite_score = composite_score / total_weight
    
    return composite_score, breakdown, strategy
```

**Strategy Selection Guide:**
| Strategy | Best For | Market Conditions |
|----------|----------|-------------------|
| Quality-Value | Long-term investors | All markets |
| Growth-Momentum | Growth investors | Bull markets |
| Balanced | Most investors | All markets |
| Defensive | Risk-averse investors | Volatile/bear markets |
| Aggressive Growth | High-risk investors | Strong bull markets |

---

## 📈 Factor Timing & Rotation

### Market Regime Detection

```python
def detect_market_regime(market_indicators):
    """
    Detect current market regime for factor rotation
    
    Args:
        market_indicators: Dictionary of market metrics
    
    Returns:
        regime: Market regime classification
        recommended_factors: Best performing factors for regime
    """
    # Extract indicators
    volatility = market_indicators.get('volatility', 0.15)
    trend = market_indicators.get('trend', 'NEUTRAL')
    valuation = market_indicators.get('valuation', 'FAIR')
    sentiment = market_indicators.get('sentiment', 50)
    
    # Determine regime
    if volatility > 0.25 and trend == 'DOWNTREND':
        regime = 'BEAR_MARKET'
        recommended_factors = ['quality', 'low_volatility', 'value']
        
    elif volatility > 0.20 and trend == 'NEUTRAL':
        regime = 'HIGH_VOLATILITY'
        recommended_factors = ['quality', 'low_volatility']
        
    elif trend == 'UPTREND' and sentiment > 60:
        regime = 'BULL_MARKET'
        recommended_factors = ['growth', 'momentum', 'quality']
        
    elif valuation == 'CHEAP' and trend == 'NEUTRAL':
        regime = 'RECOVERY_PHASE'
        recommended_factors = ['value', 'quality', 'growth']
        
    else:
        regime = 'NEUTRAL'
        recommended_factors = ['balanced']
    
    return regime, recommended_factors
```

**Historical Factor Performance by Regime:**
| Market Regime | Best Performing Factors | Worst Performing Factors |
|---------------|-------------------------|--------------------------|
| Bull Market | Growth, Momentum | Low Volatility, Value |
| Bear Market | Quality, Low Volatility | Growth, Momentum |
| High Volatility | Quality, Low Volatility | Momentum, Growth |
| Recovery | Value, Quality | Low Volatility |
| Sideways | Quality, Value | Momentum |

---

## 📊 Portfolio Construction with Factors

### Factor-Based Portfolio Optimization

```python
def construct_factor_portfolio(stocks, factor_scores, target_factors, constraints):
    """
    Construct portfolio optimized for target factor exposures
    
    Args:
        stocks: List of stock symbols
        factor_scores: Dictionary of factor scores for each stock
        target_factors: Desired factor exposures
        constraints: Portfolio constraints (max weight, sector limits, etc.)
    
    Returns:
        portfolio: Optimized portfolio weights
        factor_exposures: Actual factor exposures
    """
    # This is a simplified version
    # Real implementation would use optimization library
    
    portfolio = {}
    total_score = 0
    
    # Calculate composite scores for each stock
    stock_scores = {}
    for symbol in stocks:
        if symbol in factor_scores:
            # Calculate score aligned with target factors
            score = 0
            for factor, target_weight in target_factors.items():
                if factor in factor_scores[symbol]:
                    factor_value = factor_scores[symbol][factor].get('score', 50)
                    score += factor_value * target_weight
            
            stock_scores[symbol] = score
            total_score += score
    
    # Assign weights based on scores (simplified)
    if total_score > 0:
        for symbol, score in stock_scores.items():
            # Base weight proportional to score
            base_weight = score / total_score
            
            # Apply constraints
            max_weight = constraints.get('max_single_weight', 0.10)
            final_weight = min(base_weight, max_weight)
            
            portfolio[symbol] = final_weight
    
    # Normalize weights to sum to 1
    total_weight = sum(portfolio.values())
    if total_weight > 0:
        portfolio = {k: v/total_weight for k, v in portfolio.items()}
    
    return portfolio
```

---

## 🎯 Integration with Existing Framework

### Enhanced Analysis Workflow

1. **Data Collection:**
   ```bash
   # Get comprehensive financial data
   longbridge financials SYMBOL.US --period annual --count 10
   longbridge quote SYMBOL.US --detail
   longbridge estimate SYMBOL.US
   ```

2. **Factor Calculation:**
   ```python
   # Calculate all factor scores
   factor_analysis = {
       'quality': calculate_quality_factors(financials),
       'value': calculate_value_factors(financials, current_price),
       'growth': calculate_growth_factors(financials, estimates),
       'momentum': calculate_momentum_factors(prices, estimates),
       'low_volatility': calculate_volatility_factors(prices, market_data)
   }
   
   # Calculate composite scores
   composite_score, breakdown = calculate_composite_factor_score(factor_analysis)
   ```

3. **Generate Factor Report:**
   ```markdown
   ## Multi-Factor Analysis
   
   ### Factor Scores:
   - Quality: 78/100 (Strong)
     - ROE: 24% (Excellent)
     - Gross Margin: 45% (High)
     - Earnings Stability: 85/100
     - Debt/Equity: 0.3 (Low)
   
   - Value: 65/100 (Attractive)
     - P/E: 18.5x (Sector avg: 22x)
     - EV/EBITDA: 10.2x (Sector avg: 12x)
     - FCF Yield: 4.8% (Good)
     - Dividend Yield: 1.5% (Low)
   
   - Growth: 72/100 (Strong)
     - Revenue Growth (5yr): 15% annual
     - EPS Growth (5yr): 18% annual
     - Future Growth: 12% estimated
   
   - Momentum: 58/100 (Neutral)
     - Price Momentum (6M): +8%
     - Earnings Momentum: Neutral revisions
     - Relative Strength: 1.05 (Slightly outperforming)
   
   - Low Volatility: 45/100 (Average)
     - Historical Volatility: 28%
     - Beta: 1.15 (Slightly aggressive)
     - Downside Capture: 110% (Average)
   
   ### Composite Factor Score: 68/100 (Good)
   - Strategy: Balanced
   - Weighted: Quality 25%, Value 25%, Growth 20%, Momentum 20%, Low Vol 10%
   
   ### Factor Recommendations:
   - Strong quality and growth profile
   - Attractive valuation relative to sector
   - Momentum neutral - not overextended
   - Suitable for quality-growth portfolio
   
   ### Portfolio Fit:
   - Would improve portfolio quality score
   - Adds growth exposure
   - Moderate risk profile
   ```

---

## 🎖️ Best Practices

1. **Holistic Approach:** Consider all factors, not just one
2. **Forward-Looking:** Focus on sustainable factors
3. **Risk-Aware:** Consider factor correlations and risks
4. **Dynamic:** Adjust factor weights based on market regime
5. **Disciplined:** Stick to factor criteria, avoid emotional decisions
6. **Diversified:** Combine multiple factors for better risk-adjusted returns
7. **Backtested:** Validate factor performance historically
8. **Cost-Aware:** Consider trading costs in factor rotation

### Common Pitfalls to Avoid:
- **Value Traps:** Cheap for a reason
- **Growth at Any Price:** Overpaying for growth
- **Momentum Crashes:** Late-cycle momentum reversals
- **Factor Crowding:** Popular factors become expensive
- **Data Mining:** Over-optimizing on historical data
- **Ignoring Quality:** Buying cheap poor-quality businesses

### Success Factors:
1. **Patience:** Factor performance cycles can be long
2. **Consistency:** Stick to the process
3. **Humility:** Accept that factors won't always work
4. **Adaptability:** Adjust as markets evolve
5. **Risk Management:** Protect against factor drawdowns