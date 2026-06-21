# Market Regime Analysis Reference

## Overview

Market regime analysis determines the current state of the market (greed/fear, bull/bear, trending/ranging) and adjusts investment strategy accordingly. This is the foundation of dynamic position sizing.

---

## Market Sentiment Indicators

### Primary Indicator: Longbridge Market Temperature

**Command:** `longbridge market-temp`

**Output:**
```
| Field       | Value                               |
|-------------|-------------------------------------|
| Market      | HK                                  |
| Temperature | 69                                  |
| Description | Temp Comfortable & Gradually Rising |
| Valuation   | 90                                  |
| Sentiment   | 48                                  |
```

**Fields Explained:**

1. **Temperature (0-100)**
   - Market heat index
   - Higher = more bullish
   - Lower = more bearish

2. **Sentiment (0-100)**
   - **0-30:** Extreme Fear (contrarian buy signal)
   - **30-50:** Fear (selective buying)
   - **50-70:** Neutral/Greed (hold/sell)
   - **70-100:** Extreme Greed (contrarian sell signal)

3. **Valuation (0-100)**
   - Market valuation level
   - Higher = more expensive
   - Lower = cheaper

**Current authoritative position model:** use the Step 1 multi-factor market score as the final input. `Sentiment` alone is only one dimension. The raw target comes from `analysis/config.yaml` under `overall.score_to_position`, then weekly rebalancing discipline is applied.

| Comprehensive Score | Regime | Raw Position | Cash | Default Action |
|---------------------|--------|--------------|------|----------------|
| 80-100 | Extreme Greed | 10-25% | 75-90% | Aggressive Sell |
| 70-80 | Greed | 25-40% | 60-75% | Selective Sell |
| 60-70 | Neutral-Bullish | 40-55% | 45-60% | Hold/Trim |
| 40-60 | Neutral | 50-65% | 35-50% | Hold/Selective |
| 30-40 | Fear | 65-80% | 20-35% | Selective Buy |
| 0-30 | Extreme Fear | 80-95% | 5-20% | Aggressive Buy |

**Execution discipline:** rebalance weekly by default, ignore target changes below 5 percentage points, and move partially toward the target instead of jumping all the way in one trade. Daily rebalancing caused excessive turnover in local backtests.

---

## Market Regime Classification

### Regime 1: Extreme Greed (Comprehensive Score 80-100)

**Characteristics:**
- ✅ Markets rallying strongly
- ✅ Valuations stretched
- ✅ FOMO (Fear of Missing Out) prevalent
- ✅ Media extremely bullish
- ⚠️ High risk of correction

**Position Strategy:**
```
Total Position: 10-25%
Cash Reserve: 75-90%

Actions:
🔴 Aggressively sell profitable positions
🔴 Reduce position sizes across the board
🔴 Keep only highest conviction stocks
🔴 Build large cash buffer

Stock Selection:
- Focus on quality, avoid speculative plays
- Prioritize defensive sectors
- Avoid high-momentum stocks
- Consider inverse ETFs for hedging
```

**Example Portfolio (Comprehensive Score = 82):**
```
Portfolio Value: $157,220
Target Position: 17.5% ($27,514)
Target Cash: 82.5% ($129,706)

Holdings:
├─ Cash: $129,706 (82.5%)
├─ CEG.US: $12,000 (7.6%) - AI infrastructure
├─ TSLA.US: $8,000 (5.1%) - Strong fundamentals
└─ BABA.US: $7,514 (4.8%) - Value play
```

---

### Regime 2: Greed (Comprehensive Score 70-80)

**Characteristics:**
- ✅ Markets trending upward
- ✅ Good economic data
- ✅ Moderate optimism
- ⚠️ Some froth but not extreme

**Position Strategy:**
```
Total Position: 25-40%
Cash Reserve: 60-75%

Actions:
🟡 Selectively sell profitable positions
🟡 Reduce high-risk positions
🟡 Maintain core positions
🟡 Build cash buffer gradually

Stock Selection:
- Trim winners
- Avoid new high-risk entries
- Focus on quality over momentum
- Consider taking partial profits
```

**Example Portfolio (Comprehensive Score = 75):**
```
Portfolio Value: $157,220
Target Position: 32.5% ($51,096)
Target Cash: 67.5% ($106,124)

Holdings:
├─ Cash: $106,124 (67.5%)
├─ CEG.US: $16,000 (10.2%)
├─ TSLA.US: $13,000 (8.3%)
├─ BABA.US: $12,000 (7.6%)
└─ NVDA.US: $10,096 (6.4%)
```

---

### Regime 3: Neutral (Comprehensive Score 40-60)

**Characteristics:**
- ✅ Markets sideways or mild trends
- ✅ Balanced bullish/bearish sentiment
- ✅ Mixed economic signals
- ✅ Stock picking matters

**Position Strategy:**
```
Total Position: 50-65%
Cash Reserve: 35-50%

Actions:
🟡 Hold existing positions
🟡 Selective buying on dips
🟡 Selective selling on rallies
🟡 Active portfolio management

Stock Selection:
- Focus on individual stock fundamentals
- Buy on support, sell at resistance
- Maintain diversification
- Consider sector rotation
```

**Example Portfolio (Comprehensive Score = 50):**
```
Portfolio Value: $157,220
Target Position: 57.5% ($90,402)
Target Cash: 42.5% ($66,818)

Holdings:
├─ Cash: $66,818 (42.5%)
├─ CEG.US: $22,000 (14.0%)
├─ TSLA.US: $20,000 (12.7%)
├─ BABA.US: $18,000 (11.4%)
├─ NVDA.US: $16,000 (10.2%)
└─ PLTR.US: $14,402 (9.2%)
```

---

### Regime 4: Fear (Comprehensive Score 30-40)

**Characteristics:**
- ⚠️ Markets declining
- ⚠️ Negative news flow
- ⚠️ Investor pessimism
- ✅ Value opportunities emerging

**Position Strategy:**
```
Total Position: 65-80%
Cash Reserve: 20-35%

Actions:
🟢 Selective buying of quality stocks
🟢 Focus on oversold quality names
🟢 Scale into positions gradually
🟢 Prepare for opportunity

Stock Selection:
- Buy quality stocks at discounts
- Focus on strong balance sheets
- Avoid catching falling knives
- Prioritize defensive sectors
```

**Example Portfolio (Comprehensive Score = 35):**
```
Portfolio Value: $157,220
Target Position: 72.5% ($113,985)
Target Cash: 27.5% ($43,235)

Holdings:
├─ Cash: $43,235 (27.5%)
├─ CEG.US: $23,000 (14.6%)
├─ TSLA.US: $22,000 (14.0%)
├─ BABA.US: $21,000 (13.4%)
├─ NVDA.US: $20,000 (12.7%)
├─ PLTR.US: $18,000 (11.4%)
└─ COIN.US: $9,985 (6.4%)
```

---

### Regime 5: Extreme Fear (Comprehensive Score 0-30)

**Characteristics:**
- 🔴 Markets crashing or deeply oversold
- 🔴 Panic selling
- 🔴 Extremely negative sentiment
- ✅ Opportunity of a lifetime

**Position Strategy:**
```
Total Position: 80-95%
Cash Reserve: 5-20%

Actions:
🟢 Aggressive buying of quality stocks
🟢 Deploy cash into oversold names
🟢 Focus on high-quality survivors
🟢 Consider using margin (cautiously)

Stock Selection:
- Buy best-in-class companies
- Focus on companies with strong cash positions
- Avoid highly leveraged companies
- Prioritize secular growth stories
- Be patient, recovery takes time
```

**Example Portfolio (Comprehensive Score = 25):**
```
Portfolio Value: $157,220
Target Position: 87.5% ($137,568)
Target Cash: 12.5% ($19,653)

Holdings:
├─ Cash: $19,653 (12.5%) - Emergency reserve
├─ CEG.US: $23,000 (14.6%)
├─ TSLA.US: $22,500 (14.3%)
├─ BABA.US: $22,000 (14.0%)
├─ NVDA.US: $21,500 (13.7%)
├─ PLTR.US: $20,000 (12.7%)
├─ COIN.US: $14,568 (9.3%)
└─ Other quality candidates: $14,000 (8.9%)
```

---

## Multi-Factor Confirmation

**IMPORTANT:** Don't rely solely on sentiment. Confirm with multiple indicators.

### Confirmation Checklist

```python
def confirm_market_regime(comprehensive_score, sentiment=None, valuation=None, temperature=None):
    """
    Confirm market regime with multiple indicators

    Returns: (confirmed, confidence_level, regime)
    """
    confidence = 0

    def classify_score(score):
        if score >= 80:
            return 'EXTREME_GREED'
        if score >= 70:
            return 'GREED'
        if score >= 60:
            return 'NEUTRAL_BULLISH'
        if score >= 40:
            return 'NEUTRAL'
        if score >= 30:
            return 'FEAR'
        return 'EXTREME_FEAR'
    
    # 1. Comprehensive score is the primary regime input
    if comprehensive_score < 30:
        confidence += 1  # Extreme fear confirmed
    elif comprehensive_score > 80:
        confidence += 1  # Extreme greed confirmed
    
    # 2. Check major indices (SPY, QQQ)
    # - Are they above/below 200-day MA?
    # - Are they making new highs/lows?
    
    # 3. Check breadth indicators
    # - Advance/decline ratio
    # - New highs/new lows
    
    # 4. Check volatility (VIXM)
    # - VIXM > 25 = Fear
    # - VIXM < 15 = Greed
    
    # 5. Check valuation metrics
    # - P/E ratio vs historical
    # - P/B ratio
    
    # 6. Check news sentiment
    # - Positive/negative news flow
    # - Analyst upgrades/downgrades
    
    if confidence >= 3:
        return (True, 'HIGH', classify_score(comprehensive_score))
    elif confidence >= 2:
        return (True, 'MEDIUM', classify_score(comprehensive_score))
    else:
        return (False, 'LOW', 'UNCERTAIN')
```

**Indicators to Check:**

1. **Technical Indicators:**
   ```bash
   longbridge quote SPY.US QQQ.US
   # Check if above/below key moving averages
   # Check RSI, MACD
   ```

2. **Market Breadth:**
   - Advance/Decline ratio
   - New highs vs new lows
   - Volume trends

3. **Volatility:**
   - VIXM index
   - Implied volatility

4. **Valuation:**
   ```bash
   longbridge valuation SPY.US QQQ.US
   # Check P/E, P/B ratios
   ```

5. **News Flow:**
   ```bash
   longbridge news SPY.US
   # Check sentiment of recent news
   ```

---

## Position Adjustment Workflow

### Step-by-Step Process

**Step 1: Get Market Sentiment**
```bash
longbridge market-temp
# Note the Sentiment value
```

**Step 2: Calculate Target Position**
```python
sentiment = 48  # From market-temp
target_position_pct = calculate_target_position(sentiment)
# Returns: raw target midpoint from analysis/config.yaml
```

**Step 3: Compare with Current Position**
```python
current_position_pct = 80  # Your current holdings %
position_diff = current_position_pct - raw_target_position_pct
```

**Step 4: Determine Action**
```python
if abs(position_diff) < 5:
    action = 'NO_TRADE'
    amount = 0
elif position_diff > 0:
    action = 'SELL'
    weekly_step = position_diff * 0.35
    amount = (weekly_step / 100) * portfolio_value
else:
    action = 'BUY'
    weekly_step = abs(position_diff) * 0.35
    amount = (weekly_step / 100) * portfolio_value
```

**Step 5: Execute Weekly**
- Don't adjust all at once
- Rebalance weekly by default
- Ignore gaps under 5 percentage points
- Move about 35% of the gap per rebalance
- Monitor market conditions and hard risk caps

---

## Risk Management During Regime Shifts

### Scenario: Market Shifts from Greed to Fear

**Before (Comprehensive Score = 70):**
```
Position: 32.5%
Cash: 67.5%
```

**After (Comprehensive Score = 35):**
```
Raw Target Position: 72.5%
Target Cash: 27.5%
```

**Action Plan:**
```
Gap: 72.5% - 32.5% = 40.0 percentage points
Weekly step: 40.0% × 35% = 14.0 percentage points
This week: buy 14.0% of portfolio value
Next week: reassess score and caps before adding more
```

### Scenario: Market Shifts from Fear to Greed

**Before (Comprehensive Score = 30):**
```
Position: 72.5%
Cash: 27.5%
```

**After (Comprehensive Score = 82):**
```
Raw Target Position: 17.5%
Target Cash: 82.5%
```

**Action Plan:**
```
Gap: 72.5% - 17.5% = 55.0 percentage points
Weekly step: 55.0% × 35% = 19.25 percentage points
This week: sell 19.25% of portfolio value
Next week: reassess score, valuation cap, and ATH risk before selling more
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Ignoring Sentiment Shifts
```
Wrong: Keeping 80% position when comprehensive score shifts from 50 to 82
Result: Large drawdown during market correction
```

### ❌ Mistake 2: Over-reacting to Small Shifts
```
Wrong: Adjusting position when comprehensive score moves from 48 to 52
Result: Excessive trading, transaction costs
```

### ❌ Mistake 3: Not Confirming with Multiple Indicators
```
Wrong: Acting solely on sentiment index
Result: False signals, whipsaws
```

### ❌ Mistake 4: Adjusting Too Quickly
```
Wrong: Selling entire portfolio in one day
Result: Panic selling, miss recovery
```

### ❌ Mistake 5: Emotional Override
```
Wrong: "This time is different, I won't sell"
Result: Ignore proven strategy, large losses
```

---

## Summary: Market Regime Quick Reference

| Comprehensive Score | Regime | Position | Cash | Action | Risk |
|---------------------|--------|----------|------|--------|------|
| 0-30 | Extreme Fear | 80-95% | 5-20% | 🟢 Aggressive Buy | High (but opportunity) |
| 30-40 | Fear | 65-80% | 20-35% | 🟢 Selective Buy | Medium-High |
| 40-60 | Neutral | 50-65% | 35-50% | 🟡 Hold/Selective | Medium |
| 60-70 | Neutral-Bullish | 40-55% | 45-60% | 🟡 Hold/Trim | Medium |
| 70-80 | Greed | 25-40% | 60-75% | 🟡 Selective Sell | Medium-High |
| 80-100 | Extreme Greed | 10-25% | 75-90% | 🔴 Aggressive Sell | High (correction risk) |

**Rebalancing:** weekly by default. Do not trade if the target gap is under 5 percentage points. Move gradually toward the target unless a hard risk cap is breached.

**Key Principle:** Be fearful when others are greedy, and greedy when others are fearful.
