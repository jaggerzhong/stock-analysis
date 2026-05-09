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

---

## Market Regime Classification

### Regime 1: Extreme Greed (Sentiment 70-100)

**Characteristics:**
- ✅ Markets rallying strongly
- ✅ Valuations stretched
- ✅ FOMO (Fear of Missing Out) prevalent
- ✅ Media extremely bullish
- ⚠️ High risk of correction

**Position Strategy:**
```
Total Position: 10-30%
Cash Reserve: 70-90%

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

**Example Portfolio (Sentiment = 75):**
```
Portfolio Value: $157,220
Target Position: 20% ($31,444)
Target Cash: 80% ($125,776)

Holdings:
├─ Cash: $125,776 (80%)
├─ CEG.US: $15,000 (10%) - AI infrastructure
├─ TSLA.US: $10,000 (6%) - Strong fundamentals
└─ BABA.US: $6,444 (4%) - Value play
```

---

### Regime 2: Greed (Sentiment 60-70)

**Characteristics:**
- ✅ Markets trending upward
- ✅ Good economic data
- ✅ Moderate optimism
- ⚠️ Some froth but not extreme

**Position Strategy:**
```
Total Position: 30-50%
Cash Reserve: 50-70%

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

**Example Portfolio (Sentiment = 65):**
```
Portfolio Value: $157,220
Target Position: 40% ($62,888)
Target Cash: 60% ($94,332)

Holdings:
├─ Cash: $94,332 (60%)
├─ CEG.US: $20,000 (13%)
├─ TSLA.US: $18,000 (11%)
├─ BABA.US: $15,000 (10%)
└─ NVDA.US: $9,888 (6%)
```

---

### Regime 3: Neutral (Sentiment 40-60)

**Characteristics:**
- ✅ Markets sideways or mild trends
- ✅ Balanced bullish/bearish sentiment
- ✅ Mixed economic signals
- ✅ Stock picking matters

**Position Strategy:**
```
Total Position: 50-70%
Cash Reserve: 30-50%

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

**Example Portfolio (Sentiment = 50):**
```
Portfolio Value: $157,220
Target Position: 60% ($94,332)
Target Cash: 40% ($62,888)

Holdings:
├─ Cash: $62,888 (40%)
├─ CEG.US: $25,000 (16%)
├─ TSLA.US: $22,000 (14%)
├─ BABA.US: $20,000 (13%)
├─ NVDA.US: $15,000 (10%)
└─ PLTR.US: $12,332 (8%)
```

---

### Regime 4: Fear (Sentiment 30-40)

**Characteristics:**
- ⚠️ Markets declining
- ⚠️ Negative news flow
- ⚠️ Investor pessimism
- ✅ Value opportunities emerging

**Position Strategy:**
```
Total Position: 70-85%
Cash Reserve: 15-30%

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

**Example Portfolio (Sentiment = 35):**
```
Portfolio Value: $157,220
Target Position: 80% ($125,776)
Target Cash: 20% ($31,444)

Holdings:
├─ Cash: $31,444 (20%)
├─ CEG.US: $30,000 (19%)
├─ TSLA.US: $28,000 (18%)
├─ BABA.US: $25,000 (16%)
├─ NVDA.US: $22,000 (14%)
├─ PLTR.US: $15,000 (10%)
└─ COIN.US: $5,776 (4%)
```

---

### Regime 5: Extreme Fear (Sentiment 0-30)

**Characteristics:**
- 🔴 Markets crashing or deeply oversold
- 🔴 Panic selling
- 🔴 Extremely negative sentiment
- ✅ Opportunity of a lifetime

**Position Strategy:**
```
Total Position: 85-100%
Cash Reserve: 0-15%

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

**Example Portfolio (Sentiment = 25):**
```
Portfolio Value: $157,220
Target Position: 95% ($149,359)
Target Cash: 5% ($7,861)

Holdings:
├─ Cash: $7,861 (5%) - Emergency reserve
├─ CEG.US: $35,000 (22%)
├─ TSLA.US: $32,000 (20%)
├─ BABA.US: $28,000 (18%)
├─ NVDA.US: $25,000 (16%)
├─ PLTR.US: $18,000 (11%)
└─ COIN.US: $11,359 (7%)
```

---

## Multi-Factor Confirmation

**IMPORTANT:** Don't rely solely on sentiment. Confirm with multiple indicators.

### Confirmation Checklist

```python
def confirm_market_regime(sentiment_index):
    """
    Confirm market regime with multiple indicators
    
    Returns: (confirmed, confidence_level, regime)
    """
    confidence = 0
    
    # 1. Sentiment index
    if sentiment_index < 30:
        confidence += 1  # Fear confirmed
    elif sentiment_index > 70:
        confidence += 1  # Greed confirmed
    
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
        return (True, 'HIGH', classify_regime(sentiment_index))
    elif confidence >= 2:
        return (True, 'MEDIUM', classify_regime(sentiment_index))
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
# Returns: (60, 40, 'HOLD') for sentiment = 48
```

**Step 3: Compare with Current Position**
```python
current_position_pct = 80  # Your current holdings %
position_diff = current_position_pct - target_position_pct
# position_diff = 80 - 60 = 20
```

**Step 4: Determine Action**
```python
if position_diff > 10:
    action = 'SELL'
    amount = (position_diff / 100) * portfolio_value
elif position_diff < -10:
    action = 'BUY'
    amount = (abs(position_diff) / 100) * portfolio_value
else:
    action = 'HOLD'
```

**Step 5: Execute Gradually**
- Don't adjust all at once
- Spread over 3-5 trading days
- Monitor market conditions
- Adjust as needed

---

## Risk Management During Regime Shifts

### Scenario: Market Shifts from Greed to Fear

**Before (Sentiment = 70):**
```
Position: 30%
Cash: 70%
```

**After (Sentiment = 35):**
```
Target Position: 80%
Target Cash: 20%
```

**Action Plan:**
```
Day 1: Deploy 25% of cash into stocks
Day 2: Deploy another 25%
Day 3: Deploy remaining 20%
Total deployed: 70% of cash → 20% of portfolio
New position: 30% + 70% = 100% (exceeds target)
Adjustment: Keep 80% position, reserve 20% cash
```

### Scenario: Market Shifts from Fear to Greed

**Before (Sentiment = 30):**
```
Position: 85%
Cash: 15%
```

**After (Sentiment = 75):**
```
Target Position: 20%
Target Cash: 80%
```

**Action Plan:**
```
Day 1: Sell 20% of portfolio
Day 2: Sell another 20%
Day 3: Sell remaining 25%
Total sold: 65% of portfolio → cash
New position: 85% - 65% = 20% (matches target)
New cash: 15% + 65% = 80% (matches target)
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Ignoring Sentiment Shifts
```
Wrong: Keeping 80% position when sentiment shifts from 50 to 75
Result: Large drawdown during market correction
```

### ❌ Mistake 2: Over-reacting to Small Shifts
```
Wrong: Adjusting position when sentiment moves from 48 to 52
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

| Sentiment | Regime | Position | Cash | Action | Risk |
|-----------|--------|----------|------|--------|------|
| 0-30 | Extreme Fear | 85-100% | 0-15% | 🟢 Aggressive Buy | High (but opportunity) |
| 30-40 | Fear | 70-85% | 15-30% | 🟢 Selective Buy | Medium-High |
| 40-60 | Neutral | 50-70% | 30-50% | 🟡 Hold/Selective | Medium |
| 60-70 | Greed | 30-50% | 50-70% | 🟡 Selective Sell | Medium-High |
| 70-100 | Extreme Greed | 10-30% | 70-90% | 🔴 Aggressive Sell | High (correction risk) |

**Key Principle:** Be fearful when others are greedy, and greedy when others are fearful.
