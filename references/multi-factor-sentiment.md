# Multi-Factor Market Sentiment Analysis Reference

## Overview

Market sentiment should NEVER be evaluated based on a single indicator. This reference provides a comprehensive multi-factor framework for assessing true market conditions.

---

## 🎯 Core Philosophy

**Single Indicator Fallacy:**
- ❌ Sentiment=48 alone is misleading
- ❌ Valuation=90 alone is insufficient
- ❌ VIX alone doesn't tell the full story

**Multi-Factor Approach:**
- ✅ Combine 15+ indicators across 5 dimensions
- ✅ Weight indicators by predictive power
- ✅ Identify conflicting signals
- ✅ Generate comprehensive market state

---

## 📊 Five Dimensions of Market Analysis

### Dimension 1: Sentiment Indicators (权重: 30%)

#### 1.1 Longbridge Market Temperature
**Command:** `longbridge market-temp`

**Components:**
```
| Field       | Weight | Interpretation |
|-------------|--------|----------------|
| Sentiment   | 40%    | 0-30: Fear, 30-50: Neutral, 50-70: Greed, 70-100: Extreme Greed |
| Temperature | 40%    | Market heat/energy |
| Valuation   | 20%    | Overvaluation risk |
```

**Implementation:**
```python
def analyze_longbridge_sentiment():
    data = longbridge_market_temp()
    
    sentiment_score = data['Sentiment']
    temperature_score = data['Temperature']
    valuation_score = data['Valuation']
    
    # Valuation is inverse (high valuation = high risk)
    valuation_risk = valuation_score  # 90 = very risky
    
    # Combined score
    lb_score = (
        sentiment_score * 0.4 +
        temperature_score * 0.4 +
        valuation_risk * 0.2
    )
    
    return {
        'score': lb_score,
        'sentiment': sentiment_score,
        'temperature': temperature_score,
        'valuation_risk': valuation_risk,
        'weight': 0.30  # 30% of total
    }
```

#### 1.2 VIXM (VIX Mid-Term Futures ETF)
**Command:** `longbridge quote VIXM.US`

**Note:** VIXM 追踪 VIX 指数的中期期货表现，是 VIX 的可交易代理。

**Interpretation:**
```
| VIXM Level | Market State | Action |
|-------------|--------------|--------|
| 0-15        | Complacency/Extreme Greed | 🔴 Reduce position |
| 15-20       | Low volatility/Normal | 🟡 Neutral |
| 20-30       | Elevated concern | 🟢 Selective buying |
| 30-40       | Fear | 🟢 Aggressive buying |
| 40+         | Extreme fear/Panic | 🟢 Maximum buying |
```

**Inverse Relationship:**
- VIXM ↓ = Market risk appetite ↑ (danger)
- VIXM ↑ = Market fear ↑ (opportunity)

**Implementation:**
```python
def analyze_vixm():
    vixm_price = longbridge_quote('VIXM.US')['Last']
    
    # Convert VIXM to sentiment score (inverse)
    # VIXM 12 = score 85 (greedy)
    # VIXM 20 = score 50 (neutral)
    # VIXM 30 = score 25 (fearful)
    
    if vixm_price <= 12:
        vixm_sentiment = 90  # Extreme complacency
    elif vixm_price <= 15:
        vixm_sentiment = 75  # Greed
    elif vixm_price <= 20:
        vixm_sentiment = 55  # Neutral
    elif vixm_price <= 25:
        vixm_sentiment = 40  # Concern
    elif vixm_price <= 30:
        vixm_sentiment = 25  # Fear
    else:
        vixm_sentiment = 15  # Extreme fear
    
    return {
        'vixm_price': vixm_price,
        'vixm_sentiment': vixm_sentiment,
        'weight': 0.20  # 20% of total sentiment
    }
```

#### 1.3 Put/Call Ratio (CBOE)
**Source:** https://www.cboe.com/us/market/batch/ (需要外部数据)

**Interpretation:**
```
| Put/Call Ratio | Market State | Contrarian Signal |
|----------------|--------------|-------------------|
| < 0.7          | Extreme Greed | 🔴 Bearish |
| 0.7 - 0.9      | Greed        | 🟡 Cautious |
| 0.9 - 1.1      | Neutral      | ⚪ Neutral |
| 1.1 - 1.3      | Fear         | 🟢 Bullish |
| > 1.3          | Extreme Fear | 🟢 Very Bullish |
```

**Implementation:**
```python
def analyze_put_call_ratio(ratio):
    if ratio < 0.7:
        return {'state': 'EXTREME_GREED', 'score': 85, 'signal': 'BEARISH'}
    elif ratio < 0.9:
        return {'state': 'GREED', 'score': 70, 'signal': 'CAUTIOUS'}
    elif ratio < 1.1:
        return {'state': 'NEUTRAL', 'score': 50, 'signal': 'NEUTRAL'}
    elif ratio < 1.3:
        return {'state': 'FEAR', 'score': 30, 'signal': 'BULLISH'}
    else:
        return {'state': 'EXTREME_FEAR', 'score': 15, 'signal': 'VERY_BULLISH'}
```

---

### Dimension 2: Technical Indicators (权重: 25%)

#### 2.1 SPY (S&P 500 ETF)
**Command:** `longbridge quote SPY.US`

**Key Levels:**
```python
def analyze_spy_technical():
    quote = longbridge_quote('SPY.US')
    
    current_price = quote['Last']
    prev_close = quote['Prev Close']
    day_change_pct = (current_price - prev_close) / prev_close * 100
    
    # Check if at/near all-time high
    is_ath = check_all_time_high('SPY.US', current_price)
    
    # Distance from 52-week low
    week_52_low = quote.get('Week52Low', current_price * 0.8)
    distance_from_low = (current_price - week_52_low) / week_52_low * 100
    
    # Overbought if > 20% from 52-week low
    if distance_from_low > 30:
        technical_state = 'EXTREMELY_OVERBOUGHT'
        score = 85
    elif distance_from_low > 20:
        technical_state = 'OVERBOUGHT'
        score = 70
    elif distance_from_low > 10:
        technical_state = 'BULLISH'
        score = 60
    else:
        technical_state = 'NEUTRAL'
        score = 50
    
    return {
        'price': current_price,
        'change_pct': day_change_pct,
        'is_all_time_high': is_ath,
        'distance_from_52w_low': distance_from_low,
        'technical_state': technical_state,
        'score': score,
        'weight': 0.35  # 35% of technical dimension
    }
```

#### 2.2 QQQ (NASDAQ-100 ETF)
**Command:** `longbridge quote QQQ.US`

**Same analysis as SPY, but focused on tech sector:**
```python
def analyze_qqq_technical():
    # Similar to SPY analysis
    # Tech stocks are more volatile
    # Higher weight on growth/momentum
    pass
```

#### 2.3 Market Breadth (Advance/Decline)
**Source:** External data or calculated from major holdings

**Formula:**
```
Breadth = (Advancing Stocks - Declining Stocks) / Total Stocks

| Breadth | Interpretation |
|---------|----------------|
| > 0.6   | Very strong (overbought?) |
| 0.3-0.6 | Strong |
| 0-0.3   | Moderately bullish |
| -0.3-0  | Moderately bearish |
| < -0.3  | Weak (oversold?) |
```

**Divergence Warning:**
- If SPY makes new high but breadth declines → **Distribution phase**
- Bearish divergence, expect reversal

#### 2.4 New Highs vs New Lows
**Interpretation:**
```
| New Highs | New Lows | Market State |
|-----------|----------|--------------|
| High (>100) | Low (<10) | Strong uptrend, but potentially overbought |
| Moderate (20-100) | Low | Healthy uptrend |
| Low (<20) | Low | Consolidation |
| Low | High (>100) | Strong downtrend, oversold |
| Low | Moderate (20-100) | Healthy downtrend |
```

**Implementation:**
```python
def analyze_new_highs_lows(new_highs, new_lows):
    if new_highs > 100 and new_lows < 10:
        return {'state': 'OVERBOUGHT', 'score': 80}
    elif new_highs > 20 and new_lows < 10:
        return {'state': 'BULLISH', 'score': 65}
    elif new_highs < 20 and new_lows < 20:
        return {'state': 'NEUTRAL', 'score': 50}
    elif new_lows > 100 and new_highs < 10:
        return {'state': 'OVERSOLD', 'score': 20}
    else:
        return {'state': 'BEARISH', 'score': 35}
```

---

### Dimension 3: Valuation Metrics (权重: 25%)

#### 3.1 Market P/E Ratio
**Command:** `longbridge valuation SPY.US`

**Historical Context:**
```
| S&P 500 P/E | Percentile | Interpretation |
|-------------|------------|----------------|
| < 15        | < 20%      | Very cheap (historical opportunities) |
| 15-18       | 20-40%     | Cheap |
| 18-22       | 40-60%     | Fair value |
| 22-26       | 60-80%     | Expensive |
| > 26        | > 80%      | Very expensive (historical tops) |
| > 30        | > 95%      | Bubble territory |
```

**Implementation:**
```python
def analyze_market_pe(pe_ratio):
    if pe_ratio < 15:
        return {'state': 'VERY_CHEAP', 'score': 20, 'action': 'AGGRESSIVE_BUY'}
    elif pe_ratio < 18:
        return {'state': 'CHEAP', 'score': 35, 'action': 'SELECTIVE_BUY'}
    elif pe_ratio < 22:
        return {'state': 'FAIR', 'score': 50, 'action': 'NEUTRAL'}
    elif pe_ratio < 26:
        return {'state': 'EXPENSIVE', 'score': 70, 'action': 'SELECTIVE_SELL'}
    elif pe_ratio < 30:
        return {'state': 'VERY_EXPENSIVE', 'score': 85, 'action': 'AGGRESSIVE_SELL'}
    else:
        return {'state': 'BUBBLE', 'score': 95, 'action': 'EXIT_ALL'}
```

#### 3.2 Shiller PE (CAPE Ratio)
**Source:** https://www.multpl.com/shiller-pe (外部数据)

**Historical Context:**
```
| CAPE Ratio | Historical Context |
|------------|-------------------|
| < 12       | 1929, 1982 bottoms |
| 12-18      | Historical average range |
| 18-25      | Above average |
| 25-30      | 2007 peak |
| > 30       | 1929, 2000, 2021 peaks |
```

#### 3.3 Market Cap to GDP (Buffett Indicator)
**Source:** Federal Reserve data

**Interpretation:**
```
| Market Cap / GDP | Historical Context |
|------------------|-------------------|
| < 70%            | Significantly undervalued |
| 70-100%          | Normal range |
| 100-130%         | Overvalued |
| > 130%           | Significantly overvalued (2021 peak was 200%) |
```

#### 3.4 Longbridge Valuation Score
**From:** `longbridge market-temp` → Valuation field

```
| Valuation | Interpretation |
|-----------|----------------|
| 0-30      | Very cheap |
| 30-50     | Fair value |
| 50-70     | Expensive |
| 70-85     | Very expensive |
| 85-100    | Bubble territory ⚠️ |
```

---

### Dimension 4: Macro Environment (权重: 10%)

#### 4.1 Federal Reserve Policy
**Key Indicators:**
- Fed Funds Rate
- Quantitative Tightening/Easing
- Fed Forward Guidance

**Implementation:**
```python
def analyze_fed_environment():
    # Get current Fed rate
    fed_rate = get_fed_funds_rate()
    
    # Rate environment
    if fed_rate < 2:
        environment = 'ACCOMMODATIVE'
        score = 30  # Bullish for stocks
    elif fed_rate < 4:
        environment = 'NEUTRAL'
        score = 50
    elif fed_rate < 6:
        environment = 'RESTRICTIVE'
        score = 70  # Bearish for stocks
    else:
        environment = 'VERY_RESTRICTIVE'
        score = 85  # Very bearish
    
    # Check if rates are rising or falling
    rate_trend = get_rate_trend()  # 'RISING', 'FALLING', 'STABLE'
    
    return {
        'fed_rate': fed_rate,
        'environment': environment,
        'rate_trend': rate_trend,
        'score': score,
        'weight': 0.05
    }
```

#### 4.2 Yield Curve
**Indicator:** 10-Year Treasury - 2-Year Treasury

**Interpretation:**
```
| Spread | Signal |
|--------|--------|
| > 100 bps | Normal, healthy economy |
| 0-100 bps | Warning sign |
| < 0 (Inverted) | Recession signal (typically 12-18 months ahead) |
```

#### 4.3 Credit Spreads
**Indicator:** BBB Corporate Bond Yield - 10-Year Treasury

```
| Spread | Risk Appetite |
|--------|---------------|
| < 150 bps | High risk appetite (complacent) |
| 150-250 bps | Normal |
| > 250 bps | Risk off (fear) |
```

---

### Dimension 5: Flow & Positioning (权重: 10%)

#### 5.1 Institutional Positioning
**Source:** 13F filings, commitment of traders report

**Indicators:**
- Hedge fund leverage
- Institutional cash levels
- Short interest

#### 5.2 Retail Sentiment
**Sources:**
- AAII Sentiment Survey
- Reddit/StockTwits sentiment
- Google Trends for "buy stocks"

#### 5.3 Capital Flow
**Command:** `longbridge capital --flow`

**Implementation:**
```python
def analyze_capital_flow():
    flows = longbridge_capital_flow()
    
    # Net inflow/outflow
    net_flow = flows.get('net_flow', 0)
    
    if net_flow > 0:
        state = 'INFLOW'  # Bullish
        score = 40
    else:
        state = 'OUTFLOW'  # Bearish
        score = 60
    
    return {
        'net_flow': net_flow,
        'state': state,
        'score': score,
        'weight': 0.10
    }
```

---

## 🎯 Comprehensive Market State Calculation

### Master Formula

```python
def calculate_comprehensive_market_state():
    """
    Calculate comprehensive market state from all dimensions
    
    Returns:
        - Overall score (0-100)
        - Market state classification
        - Recommended position
        - Risk level
        - Key signals and divergences
    """
    
    # Dimension 1: Sentiment Indicators (30%)
    lb_sentiment = analyze_longbridge_sentiment()
    vix = analyze_vix()
    put_call = analyze_put_call_ratio(get_put_call_data())
    
    sentiment_score = (
        lb_sentiment['score'] * lb_sentiment['weight'] +
        vix['vix_sentiment'] * vix['weight'] +
        put_call['score'] * (1 - lb_sentiment['weight'] - vix['weight'])
    )
    
    # Dimension 2: Technical Indicators (25%)
    spy_tech = analyze_spy_technical()
    qqq_tech = analyze_qqq_technical()
    breadth = analyze_market_breadth()
    new_highs_lows = analyze_new_highs_lows(get_new_highs_lows_data())
    
    technical_score = (
        spy_tech['score'] * spy_tech['weight'] +
        qqq_tech['score'] * qqq_tech['weight'] +
        breadth['score'] * 0.20 +
        new_highs_lows['score'] * 0.10
    )
    
    # Dimension 3: Valuation Metrics (25%)
    market_pe = analyze_market_pe(get_spy_pe())
    shiller_pe = analyze_shiller_pe(get_shiller_pe())
    lb_valuation = analyze_longbridge_valuation()
    
    valuation_score = (
        market_pe['score'] * 0.40 +
        shiller_pe['score'] * 0.30 +
        lb_valuation['score'] * 0.30
    )
    
    # Dimension 4: Macro Environment (10%)
    fed_env = analyze_fed_environment()
    yield_curve = analyze_yield_curve()
    credit_spreads = analyze_credit_spreads()
    
    macro_score = (
        fed_env['score'] * 0.50 +
        yield_curve['score'] * 0.30 +
        credit_spreads['score'] * 0.20
    )
    
    # Dimension 5: Flow & Positioning (10%)
    capital_flow = analyze_capital_flow()
    institutional = analyze_institutional_positioning()
    retail = analyze_retail_sentiment()
    
    flow_score = (
        capital_flow['score'] * 0.40 +
        institutional['score'] * 0.30 +
        retail['score'] * 0.30
    )
    
    # Comprehensive Score
    overall_score = (
        sentiment_score * 0.30 +
        technical_score * 0.25 +
        valuation_score * 0.25 +
        macro_score * 0.10 +
        flow_score * 0.10
    )
    
    # Classify market state
    market_state = classify_market_state(overall_score)
    
    # Determine target position
    target_position = calculate_target_position(overall_score, valuation_score)
    
    # Identify divergences
    divergences = identify_divergences(
        sentiment_score, technical_score, valuation_score
    )
    
    return {
        'overall_score': overall_score,
        'market_state': market_state,
        'target_position': target_position,
        'risk_level': calculate_risk_level(overall_score, valuation_score),
        'dimensions': {
            'sentiment': sentiment_score,
            'technical': technical_score,
            'valuation': valuation_score,
            'macro': macro_score,
            'flow': flow_score
        },
        'divergences': divergences,
        'recommendations': generate_recommendations(
            overall_score, market_state, divergences
        )
    }
```

### Market State Classification

```python
def classify_market_state(score):
    """
    Classify market state based on comprehensive score
    
    Higher score = More greedy/risky
    Lower score = More fearful/opportunistic
    """
    if score >= 80:
        return {
            'state': 'EXTREME_GREED',
            'description': 'Market euphoria, bubble territory',
            'historical_similarity': ['2000 Dot-com', '2007 Pre-crisis', '2021 Peak'],
            'action': 'AGGRESSIVE_SELL',
            'urgency': 'HIGH'
        }
    elif score >= 70:
        return {
            'state': 'GREED',
            'description': 'Market optimism, but elevated risk',
            'historical_similarity': ['2018 Peak', '2020 Pre-COVID'],
            'action': 'SELECTIVE_SELL',
            'urgency': 'MEDIUM'
        }
    elif score >= 60:
        return {
            'state': 'NEUTRAL_BULLISH',
            'description': 'Moderate optimism, sustainable rally',
            'action': 'HOLD',
            'urgency': 'LOW'
        }
    elif score >= 40:
        return {
            'state': 'NEUTRAL',
            'description': 'Balanced market, stock picking matters',
            'action': 'SELECTIVE_BUY',
            'urgency': 'LOW'
        }
    elif score >= 30:
        return {
            'state': 'FEAR',
            'description': 'Market pessimism, opportunities emerging',
            'historical_similarity': ['2018 Dec selloff', '2022 Bottom'],
            'action': 'SELECTIVE_BUY',
            'urgency': 'MEDIUM'
        }
    else:
        return {
            'state': 'EXTREME_FEAR',
            'description': 'Market panic, generational opportunity',
            'historical_similarity': ['2009 Bottom', '2020 COVID bottom', '2022 Low'],
            'action': 'AGGRESSIVE_BUY',
            'urgency': 'HIGH'
        }
```

### Divergence Detection

**Critical Warning System:**

```python
def identify_divergences(sentiment, technical, valuation):
    """
    Identify dangerous divergences between indicators
    
    Returns: List of divergence warnings
    """
    divergences = []
    
    # Divergence 1: Technical high but sentiment low
    if technical > 70 and sentiment < 50:
        divergences.append({
            'type': 'TECHNICAL_SENTIMENT_DIVERGENCE',
            'warning': 'Price at highs but sentiment cautious',
            'interpretation': 'Could be late stage rally, "smart money" exiting',
            'risk': 'HIGH',
            'action': 'Reduce position despite neutral sentiment'
        })
    
    # Divergence 2: Valuation extreme but sentiment neutral
    if valuation > 85 and sentiment < 60:
        divergences.append({
            'type': 'VALUATION_SENTIMENT_DIVERGENCE',
            'warning': 'Extremely expensive but sentiment not euphoric',
            'interpretation': 'Distribution phase, institutional selling',
            'risk': 'VERY HIGH',
            'action': 'Cap position at 30% regardless of sentiment'
        })
    
    # Divergence 3: VIXM low but breadth declining
    # (Need external data)
    
    # Divergence 4: Index high but new lows increasing
    # (Need external data)
    
    # Divergence 5: Sentiment extreme but no reversal
    if sentiment > 70:
        divergences.append({
            'type': 'SENTIMENT_EXTREME',
            'warning': 'Sentiment at extreme greed',
            'interpretation': 'Contrarian sell signal',
            'risk': 'HIGH',
            'action': 'Prepare for reversal'
        })
    
    return divergences
```

---

## 📊 Practical Example: Current Market Analysis

### Data Collected (2026-04-20)

```
Dimension 1: Sentiment
├─ Longbridge Sentiment: 48 (weight 40%)
├─ Longbridge Temperature: 69 (weight 40%)
├─ Longbridge Valuation: 90 (weight 20%)
├─ VIXM: ~15 (estimated)
└─ Sentiment Score: 59.6

Dimension 2: Technical
├─ SPY: $710.14, All-time high, +1.21%
├─ QQQ: $648.85, All-time high, +1.31%
├─ Distance from 52w low: ~25% (overbought)
└─ Technical Score: 72.5

Dimension 3: Valuation
├─ Longbridge Valuation: 90
├─ S&P 500 P/E: ~26 (estimated)
├─ Shiller PE: ~32 (estimated)
└─ Valuation Score: 85

Dimension 4: Macro
├─ Fed Rate: ~5.25% (restrictive)
├─ Yield Curve: Inverted (warning)
└─ Macro Score: 65

Dimension 5: Flow
├─ Capital inflows positive
├─ Institutional positioning: Neutral
└─ Flow Score: 55
```

### Comprehensive Calculation

```python
overall_score = (
    59.6 * 0.30 +   # Sentiment
    72.5 * 0.25 +   # Technical
    85.0 * 0.25 +   # Valuation ⚠️ Highest weight on risk
    65.0 * 0.10 +   # Macro
    55.0 * 0.10     # Flow
) = 68.03

# Rounded: 68
```

### Market State: GREED

**Classification:**
```
State: GREED
Score: 68
Description: Market optimism, but elevated risk

Recommendations:
├─ Target Position: 35% (NOT 60%)
├─ Cash Reserve: 65%
├─ Action: SELECTIVE_SELL
├─ Urgency: MEDIUM
```

### Divergences Detected

**⚠️ Critical Divergence:**
```
Type: VALUATION_SENTIMENT_DIVERGENCE

Warning: Valuation = 90 (extreme) but Sentiment = 48 (neutral)

Interpretation: 
- Market is extremely expensive
- But investors not euphoric yet
- Classic distribution phase
- "Smart money" quietly exiting

Risk: VERY HIGH
Action: Cap position at 30-35% regardless of sentiment
```

**⚠️ Technical Divergence:**
```
Type: TECHNICAL_EXTREME

Warning: SPY/QQQ at all-time highs

Interpretation:
- Indices at historical highs
- Low probability of continued momentum
- High probability of pullback
- Buying at highs = poor risk/reward

Risk: HIGH
Action: Wait for pullback before buying
```

---

## 🎯 Recommended Position Sizing (Corrected)

### Based on Comprehensive Analysis

**Original (Wrong):**
```
Sentiment = 48 → Neutral → Position = 60%
Problem: Ignored valuation and technical extremes
```

**Corrected (Multi-Factor):**
```
Comprehensive Score = 68 → Greed → Position = 35%

Rationale:
1. Valuation = 90 (extreme) → Cap position at 40%
2. Technical = All-time high → Reduce to 30-35%
3. Divergence detected → Further reduce to 35%

Final: Position = 35%, Cash = 65%
```

### Position Cap Rules

**When Valuation > 85:**
```python
def apply_valuation_cap(valuation, calculated_position):
    if valuation > 90:
        return min(calculated_position, 25)  # Max 25%
    elif valuation > 85:
        return min(calculated_position, 35)  # Max 35%
    elif valuation > 75:
        return min(calculated_position, 50)  # Max 50%
    else:
        return calculated_position  # No cap
```

**When at All-Time High:**
```python
def apply_ath_cap(is_ath, calculated_position):
    if is_ath:
        return min(calculated_position, calculated_position * 0.8)  # Reduce 20%
    return calculated_position
```

---

## 📋 Quick Reference: Data Sources

### Available via Longbridge CLI

```bash
# Sentiment
longbridge market-temp

# Technical
longbridge quote SPY.US QQQ.US VIXM.US
longbridge intraday SPY.US QQQ.US
longbridge kline history SPY.US --start 2025-01-01 --period week

# Valuation
longbridge valuation SPY.US QQQ.US
longbridge calc-index SPY.US

# Flow
longbridge capital --flow
```

### External Data Sources

```python
external_sources = {
    'VIXM': 'https://www.cboe.com/tradable_products/vix/',
    'Put_Call_Ratio': 'https://www.cboe.com/us/market/batch/',
    'AAII_Sentiment': 'https://www.aaii.com/sentimentsurvey',
    'Shiller_PE': 'https://www.multpl.com/shiller-pe',
    'Yield_Curve': 'https://www.treasury.gov/resource-center/data-chart-center/Pages/index.aspx',
    'Fear_Greed_Index': 'https://www.cnn.com/markets/fear-and-greed',
    'NAAIM_Exposure': 'https://naaim.org/programs/naaim-exposure-index/'
}
```

---

## 🚨 Warning Signs Checklist

Before making any investment, check:

- [ ] **Valuation < 70?** If > 70, cap position
- [ ] **VIXM > 20?** If < 15, be cautious
- [ ] **Index at ATH?** If yes, wait for pullback
- [ ] **Breadth diverging?** If yes, distribution phase
- [ ] **Sentiment extreme?** If > 70 or < 20, contrarian signal
- [ ] **Fed hiking?** If yes, reduce risk
- [ ] **Yield curve inverted?** If yes, recession risk
- [ ] **Divergences present?** If yes, extra caution

**If 3+ warnings are true:**
- Maximum position: 30%
- Minimum cash: 70%
- Strict stop losses

---

## Summary

**Key Takeaways:**

1. **Never use single indicator** - Multi-factor analysis is essential
2. **Weight valuation heavily** - Expensive markets are dangerous
3. **Detect divergences** - Conflicting signals = high risk
4. **Apply position caps** - Hard limits based on valuation/technical
5. **Contrarian mindset** - Greed = sell, Fear = buy
6. **Update continuously** - Market conditions change rapidly

**Remember:**
- Sentiment=48 ≠ Neutral market when Valuation=90
- All-time highs require extra caution
- Distribution phases look "neutral" but are dangerous
- "Smart money" exits quietly, not in euphoria
