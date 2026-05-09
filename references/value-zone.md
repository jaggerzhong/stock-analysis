# Value Zone Analysis Reference

## Overview

Value zones represent price levels where a stock is likely to find support (buyers) or resistance (sellers). Combining technical price zones with fundamental valuation metrics provides a comprehensive view of "fair value."

---

## Three-Layer Value Zone Model

### Layer 1: Technical Price Zones

Based on historical price action and volume.

#### A. Support Zone

**Definition:** Price level where buying pressure exceeds selling pressure

**Identification Methods:**

1. **Volume Profile (Most Reliable)**
   - Price levels with highest trading volume
   - Indicates where most shares changed hands
   - Acts as strong support/resistance

2. **Previous Swing Lows**
   - Multiple touches = stronger support
   - Recent lows more relevant than old ones

3. **Moving Averages**
   - 20-day MA: Short-term support
   - 50-day MA: Medium-term support
   - 200-day MA: Long-term support

4. **Unfilled Gaps**
   - Upward gaps act as support
   - See gap-theory.md for details

**Support Zone Calculation:**

```python
def calculate_support_zone(kline_data, lookback_days=60):
    """
    Calculate support zone from K-line data
    
    Returns:
        (support_low, support_high, strength_score)
    """
    recent_data = kline_data[-lookback_days:]
    
    # Method 1: Volume profile (price level with most volume)
    price_volume = {}
    for candle in recent_data:
        # Use candle range as price zone
        low = candle['low']
        high = candle['high']
        mid = (low + high) / 2
        zone = round(mid / 0.5) * 0.5  # Round to nearest $0.50
        
        price_volume[zone] = price_volume.get(zone, 0) + candle['volume']
    
    # Find zone with highest volume
    volume_cluster_zone = max(price_volume, key=price_volume.get)
    
    # Method 2: Swing lows (local minima)
    swing_lows = []
    for i in range(2, len(recent_data)-2):
        if (recent_data[i]['low'] < recent_data[i-1]['low'] and 
            recent_data[i]['low'] < recent_data[i-2]['low'] and
            recent_data[i]['low'] < recent_data[i+1]['low'] and 
            recent_data[i]['low'] < recent_data[i+2]['low']):
            swing_lows.append(recent_data[i]['low'])
    
    # Combine methods
    support_levels = [volume_cluster_zone] + swing_lows
    support_levels = sorted(set(support_levels))
    
    # Find clustering (strongest support)
    if len(support_levels) >= 2:
        support_zone = (min(support_levels[:3]), max(support_levels[:3]))
    else:
        support_zone = (min(support_levels), max(support_levels))
    
    # Strength score (0-10)
    touches = sum(1 for candle in recent_data 
                  if candle['low'] <= support_zone[1] and candle['close'] > candle['low'])
    strength = min(10, touches * 0.5 + len(swing_lows) * 0.5)
    
    return support_zone[0], support_zone[1], strength
```

#### B. Resistance Zone

**Definition:** Price level where selling pressure exceeds buying pressure

**Identification Methods:**

1. **Volume Profile** (same as support)
2. **Previous Swing Highs**
3. **All-Time Highs / 52-Week Highs**
4. **Round Numbers** ($100, $150, $200)
5. **Unfilled Downward Gaps**

**Resistance Zone Calculation:**

```python
def calculate_resistance_zone(kline_data, lookback_days=60):
    """Similar to support calculation, but for swing highs"""
    recent_data = kline_data[-lookback_days:]
    
    # Volume cluster
    price_volume = {}
    for candle in recent_data:
        mid = (candle['low'] + candle['high']) / 2
        zone = round(mid / 0.5) * 0.5
        price_volume[zone] = price_volume.get(zone, 0) + candle['volume']
    
    volume_cluster_zone = max(price_volume, key=price_volume.get)
    
    # Swing highs
    swing_highs = []
    for i in range(2, len(recent_data)-2):
        if (recent_data[i]['high'] > recent_data[i-1]['high'] and 
            recent_data[i]['high'] > recent_data[i-2]['high'] and
            recent_data[i]['high'] > recent_data[i+1]['high'] and 
            recent_data[i]['high'] > recent_data[i+2]['high']):
            swing_highs.append(recent_data[i]['high'])
    
    # 52-week high
    high_52w = max([c['high'] for c in kline_data[-252:]]) if len(kline_data) >= 252 else max([c['high'] for c in kline_data])
    
    resistance_levels = sorted(set([volume_cluster_zone] + swing_highs + [high_52w]), reverse=True)
    
    return resistance_levels[1] if len(resistance_levels) > 1 else resistance_levels[0]
```

#### C. Fair Value Zone

**Definition:** Price range where the stock is "fairly valued" based on technical indicators

**Components:**

1. **Moving Average Convergence**
   - Zone where 20 MA and 50 MA converge
   - Indicates equilibrium price

2. **Price Range Mean**
   - Average of recent high and low
   - (52-week high + 52-week low) / 2

3. **Volume-Weighted Average Price (VWAP)**
   - For intraday analysis
   - Acts as fair value reference

**Fair Value Calculation:**

```python
def calculate_fair_value_zone(kline_data):
    """
    Calculate fair value zone based on moving averages and range
    """
    closes = [c['close'] for c in kline_data]
    
    # 20-day and 50-day moving averages
    ma_20 = sum(closes[-20:]) / 20
    ma_50 = sum(closes[-50:]) / 50
    
    # 52-week range
    high_52w = max([c['high'] for c in kline_data[-252:]])
    low_52w = min([c['low'] for c in kline_data[-252:]])
    range_mid = (high_52w + low_52w) / 2
    
    # Combine
    fair_value_low = min(ma_20, ma_50, range_mid)
    fair_value_high = max(ma_20, ma_50, range_mid)
    
    return round(fair_value_low, 2), round(fair_value_high, 2)
```

---

### Layer 2: Fundamental Valuation Zones

Based on company financials and valuation multiples.

#### A. P/E Ratio Zone

```
Fair P/E Zone = Industry Average P/E × (0.8 to 1.2)

Example:
- Industry Average P/E: 25
- Fair P/E Zone: 20 - 30
- Stock EPS: $5

Implied Fair Value Zone:
- Lower bound: $5 × 20 = $100
- Upper bound: $5 × 30 = $150
```

**Stock Valuation:**

```python
def calculate_pe_value_zone(current_eps, industry_avg_pe):
    """Calculate value zone based on P/E ratio"""
    pe_low = industry_avg_pe * 0.8   # 20% discount
    pe_high = industry_avg_pe * 1.2  # 20% premium
    
    value_low = current_eps * pe_low
    value_high = current_eps * pe_high
    
    return value_low, value_high
```

#### B. P/B Ratio Zone

```
Fair P/B Zone = Industry Average P/B × (0.7 to 1.3)

Example:
- Industry Average P/B: 3.0
- Fair P/B Zone: 2.1 - 3.9
- Stock Book Value: $30

Implied Fair Value Zone:
- Lower bound: $30 × 2.1 = $63
- Upper bound: $30 × 3.9 = $117
```

#### C. DCF Value Zone (If Available)

```
Intrinsic Value Range = DCF Value × (0.85 to 1.15)

Accounts for model uncertainty with ±15% buffer
```

---

### Layer 3: Combined Value Zone

**Integration Formula:**

```python
def calculate_combined_value_zone(symbol, kline_data, fundamentals):
    """
    Combine technical and fundamental zones
    Returns: (strong_support, fair_value_low, fair_value_high, strong_resistance)
    """
    # Technical zones
    tech_support = calculate_support_zone(kline_data)
    tech_resistance = calculate_resistance_zone(kline_data)
    tech_fair = calculate_fair_value_zone(kline_data)
    
    # Fundamental zones
    fund_fair = calculate_pe_value_zone(
        fundamentals['eps'],
        fundamentals['industry_pe']
    )
    
    # Combine fair value zones (intersection is strongest)
    combined_fair_low = max(tech_fair[0], fund_fair[0])
    combined_fair_high = min(tech_fair[1], fund_fair[1])
    
    # If no overlap, use average
    if combined_fair_low > combined_fair_high:
        combined_fair_low = (tech_fair[0] + fund_fair[0]) / 2
        combined_fair_high = (tech_fair[1] + fund_fair[1]) / 2
    
    # Strong support: Highest technical support within fundamental range
    strong_support = tech_support[0] if tech_support[0] >= combined_fair_low else tech_support[0]
    
    # Strong resistance: Lowest technical resistance
    strong_resistance = tech_resistance
    
    return {
        'strong_support': strong_support,
        'fair_value_low': combined_fair_low,
        'fair_value_high': combined_fair_high,
        'strong_resistance': strong_resistance,
        'current_position': get_price_position(
            kline_data[-1]['close'],
            strong_support,
            combined_fair_low,
            combined_fair_high,
            strong_resistance
        )
    }

def get_price_position(current_price, support, fair_low, fair_high, resistance):
    """Determine where current price sits in the value zone framework"""
    
    if current_price <= support:
        return 'DEEP_VALUE'  # Significantly undervalued
    elif current_price <= fair_low:
        return 'VALUE'       # Undervalued
    elif current_price <= fair_high:
        return 'FAIR_VALUE'  # Fairly valued
    elif current_price <= resistance:
        return 'OVERVALUED'  # Overvalued
    else:
        return 'EXTENDED'    # Significantly overvalued
```

---

## Visual Representation

```
Price
  ↑
  │                 ════════════ Strong Resistance ($195-$200)
  │                 ║          ║
  │                 ║ OVERVALUED║
  │                 ║          ║
  │─────────────────║──────────║──── Fair Value High ($175)
  │                 ║ FAIR     ║
  │                 ║ VALUE    ║
  │                 ║ ZONE     ║
  │─────────────────║──────────║──── Fair Value Low ($165)
  │                 ║          ║
  │                 ║ VALUE    ║
  │                 ║          ║
  │                 ════════════ Strong Support ($150-$155)
  │
  └──────────────────────────────────→ Time

Current Price: $170 → Position: FAIR_VALUE
```

---

## Trading Decisions Based on Value Zones

### Position Decisions

| Price Position | Action | Rationale |
|----------------|--------|-----------|
| DEEP_VALUE | Strong Buy | Significantly undervalued, high margin of safety |
| VALUE | Buy | Undervalued, good entry opportunity |
| FAIR_VALUE | Hold/Small Position | Fairly priced, no urgency |
| OVERVALUED | Reduce Position | Above fair value, take some profits |
| EXTENDED | Sell | Significantly overvalued, exit or short |

### Entry/Exit Zones

**Buying:**
```
Primary Entry: Near Fair Value Low
Secondary Entry: Near Strong Support
Stop Loss: 5% below Strong Support

Scale-in Strategy:
- 50% position at Fair Value Low
- 30% position at Strong Support
- 20% position on breakout above Fair Value High (trend confirmation)
```

**Selling:**
```
Primary Exit: Near Fair Value High
Secondary Exit: Near Strong Resistance
Stop Loss (for shorts): 3% above Strong Resistance

Scale-out Strategy:
- 50% position at Fair Value High
- 30% position at Strong Resistance
- 20% position on breakdown below Fair Value Low (trend reversal)
```

---

## Practical Example

**Symbol: AAPL.US**

```bash
# Get data
longbridge kline history AAPL.US --start 2025-01-01 --end 2026-04-20 --period day --format json
longbridge quote AAPL.US
```

**Analysis:**

```
Technical Zones:
- 52-Week High: $199.50
- 52-Week Low: $165.00
- 20-Day MA: $182.50
- 50-Day MA: $178.30
- Volume Cluster (Support): $170-$175
- Recent Swing High: $188.50

Fundamental Data:
- EPS: $6.50
- Industry P/E: 28
- Book Value: $4.20
- Industry P/B: 45

Fundamental Value Zones:
- P/E Fair Value: $6.50 × 28 × (0.8 to 1.2) = $145.60 - $218.40
- P/B Fair Value: $4.20 × 45 × (0.7 to 1.3) = $132.30 - $245.70

Combined Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Zone               Price Range      Interpretation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Strong Resistance  $188-$195        Recent highs, selling pressure
Fair Value High    $182             MA convergence, P/E midpoint
Fair Value Low     $175             Volume cluster start
Strong Support     $170-$175        Volume cluster + gap support
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Price: $185.50
Position: Slightly OVERVALUED (above Fair Value High)
Distance to Support: -8.4%
Distance to Resistance: +1.4%
```

**Recommendation:**

```
AAPL.US is trading slightly above fair value zone.

If holding:
- Consider taking partial profits (20-30% of position)
- Set trailing stop at $175 (Fair Value Low)

If looking to buy:
- Wait for pullback to $175-$180 zone
- Strong support confluence at $170-$175

Key Levels:
- Support: $175, $170
- Resistance: $188, $195
- Fair Value: $175-$182
```

---

## Key Takeaways

1. **Combine technical and fundamental analysis** for robust value zones
2. **Volume profile is the most reliable** support/resistance indicator
3. **Fair value zone should align** with both technical and fundamental metrics
4. **Price position determines action** — deep value to extended spectrum
5. **Use zones as guidelines, not absolute rules** — market conditions matter
6. **Re-evaluate zones regularly** — at least monthly, or after significant price moves

---

## 🎯 Quality-Adjusted Safety Margin (质量调整安全边际)

### The Problem with Fixed Margins

**Traditional approach (WRONG):**
```
Fair P/E = Industry Avg × (0.8 to 1.2)  # Same for all companies!
```

**Why this fails:**
- Apple (wide moat) deserves higher P/E than generic retailer
- High ROIC companies can grow into premium valuations
- Low quality companies need larger margin (value trap risk)

### Correct Approach: Margin Based on Quality

```python
def calculate_required_safety_margin(moat_score, roic, moat_trend):
    """
    Calculate required safety margin based on business quality
    
    Higher quality = Lower required margin (can pay fair price)
    Lower quality = Higher required margin (need discount)
    
    Buffett: "It's far better to buy a wonderful company at a fair price 
    than a fair company at a wonderful price."
    """
    
    # Base margin by moat score
    base_margin = {
        (9, 10): 0.00,    # Exceptional moat: Pay fair price
        (7, 9): 0.10,     # Wide moat: 10% discount
        (5, 7): 0.20,     # Narrow moat: 20% discount
        (3, 5): 0.35,     # Minimal moat: 35% discount
        (0, 3): None,     # No moat: AVOID (value trap risk)
    }
    
    margin = None
    for score_range, m in base_margin.items():
        if score_range[0] <= moat_score < score_range[1]:
            margin = m
            break
    
    if margin is None:
        return None, "Avoid - No economic moat"
    
    # Adjust for ROIC
    if roic >= 0.30:  # 30%+ ROIC
        margin = max(0, margin - 0.05)  # Reduce margin requirement
    elif roic >= 0.20:
        margin = max(0, margin - 0.03)
    elif roic < 0.10:  # Low ROIC
        margin += 0.10  # Need extra margin
    
    # Adjust for moat trend
    if moat_trend == 'ERODING':
        margin += 0.10  # Need extra margin for declining moat
    elif moat_trend == 'STRENGTHENING':
        margin = max(0, margin - 0.05)
    
    return margin, f"Required margin: {margin:.0%}"


def calculate_quality_adjusted_fair_value(
    base_fair_value, 
    moat_score, 
    roic, 
    moat_trend
):
    """
    Calculate fair value adjusted for business quality
    
    Example:
    - Base fair value (DCF): $100
    - Moat score: 8/10 (Wide moat)
    - ROIC: 25% (Excellent)
    - Moat trend: Stable
    
    Required margin: 10% (wide moat) - 3% (high ROIC) = 7%
    
    Buy price: $100 × (1 - 7%) = $93
    """
    margin, reason = calculate_required_safety_margin(moat_score, roic, moat_trend)
    
    if margin is None:
        return None, "Avoid - Insufficient quality"
    
    buy_price = base_fair_value * (1 - margin)
    
    return {
        'base_fair_value': base_fair_value,
        'required_margin': margin,
        'buy_price': buy_price,
        'reason': reason
    }
```

### Example Scenarios

**Scenario 1: Exceptional Company (Apple-like)**
```
Moat Score: 9/10 (Brand: 2, Network: 1, Switching: 2, Cost: 2, Reg: 2)
ROIC: 45%
Moat Trend: STABLE

Required Margin Calculation:
├─ Base (Moat 9): 0%
├─ ROIC Adjustment: -5% (exceptional ROIC)
├─ Trend Adjustment: 0% (stable)
└─ Final Margin: 0%

Interpretation: Can pay FAIR PRICE
DCF Fair Value: $200
Buy Price: $200 (no discount needed)
```

**Scenario 2: Good Company (Narrow Moat)**
```
Moat Score: 6/10 (Brand: 1.5, Switching: 1.5, Cost: 2)
ROIC: 18%
Moat Trend: STABLE

Required Margin Calculation:
├─ Base (Moat 6): 20%
├─ ROIC Adjustment: 0% (good but not exceptional)
├─ Trend Adjustment: 0% (stable)
└─ Final Margin: 20%

Interpretation: Need 20% DISCOUNT
DCF Fair Value: $100
Buy Price: $80
```

**Scenario 3: Declining Business**
```
Moat Score: 5/10 (Cost: 2, Brand: 1)
ROIC: 8%
Moat Trend: ERODING

Required Margin Calculation:
├─ Base (Moat 5): 20%
├─ ROIC Adjustment: +10% (low ROIC)
├─ Trend Adjustment: +10% (eroding)
└─ Final Margin: 40%

Interpretation: Need 40% DISCOUNT (high risk)
DCF Fair Value: $50
Buy Price: $30

WARNING: Consider avoiding altogether
```

---

## Integration Checklist

When analyzing a stock's value zone:

- [ ] Get 60-90 days of K-line data
- [ ] Calculate technical support/resistance from volume profile
- [ ] Identify swing highs/lows
- [ ] Calculate moving averages (20, 50, 200)
- [ ] Get fundamental data (EPS, P/E, P/B, industry averages)
- [ ] Calculate fundamental fair value zone
- [ ] **NEW: Calculate moat score**
- [ ] **NEW: Calculate ROIC**
- [ ] **NEW: Determine quality-adjusted safety margin**
- [ ] Combine technical and fundamental zones
- [ ] Determine current price position
- [ ] **NEW: Adjust for business quality**
- [ ] Provide entry/exit recommendations
