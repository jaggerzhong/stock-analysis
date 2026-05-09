# Position Management Reference

## Overview

Position management determines how much capital to allocate to each stock, when to increase/decrease positions, and how to manage overall portfolio risk. This reference provides rules and strategies for systematic position sizing.

---

## Core Principles

1. **Risk First** — Protect capital before seeking returns
2. **Diversification** — Don't concentrate risk in one stock or sector
3. **Consistency** — Apply rules systematically, not emotionally
4. **Flexibility** — Adjust for market conditions and signal strength
5. **Contrarian Mindset** — Be fearful when others are greedy, greedy when others are fearful

---

## 🎯 Dynamic Position Sizing Based on Market Sentiment

### Core Concept

Total portfolio position should adapt to market conditions, NOT remain fixed. This follows the contrarian investment principle.

### Market Sentiment to Position Mapping

**Data Source:** `longbridge market-temp` command returns:
- `Temperature` (0-100): Market heat index
- `Sentiment` (0-100): Market sentiment index
- `Valuation` (0-100): Valuation level

**Position Adjustment Model:**

| Sentiment Range | Market State | Total Position | Cash Reserve | Strategy |
|-----------------|--------------|----------------|--------------|----------|
| **0-30** | Extreme Fear | **85-100%** | 0-15% | 🟢 Aggressive buying, seize opportunities |
| **30-40** | Fear | **70-85%** | 15-30% | 🟢 Selective buying, value hunting |
| **40-60** | Neutral | **50-70%** | 30-50% | 🟡 Hold positions, selective action |
| **60-70** | Greed | **30-50%** | 50-70% | 🟡 Selective selling, take profits |
| **70-100** | Extreme Greed | **10-30%** | 70-90% | 🔴 Aggressive selling, risk off |

**Implementation Formula:**

```python
def calculate_target_position(sentiment_index):
    """
    Calculate target position percentage based on market sentiment
    
    Args:
        sentiment_index: 0-100 from longbridge market-temp
    
    Returns:
        (target_position_pct, cash_reserve_pct, action)
    """
    if sentiment_index <= 30:
        # Extreme Fear: Maximum allocation
        return (95, 5, 'AGGRESSIVE_BUY')
    
    elif sentiment_index <= 40:
        # Fear: High allocation
        return (80, 20, 'SELECTIVE_BUY')
    
    elif sentiment_index <= 60:
        # Neutral: Moderate allocation
        return (60, 40, 'HOLD')
    
    elif sentiment_index <= 70:
        # Greed: Low allocation
        return (40, 60, 'SELECTIVE_SELL')
    
    else:
        # Extreme Greed: Minimal allocation
        return (20, 80, 'AGGRESSIVE_SELL')


def adjust_position_for_sentiment(current_position, target_position, portfolio_value):
    """
    Calculate position adjustment needed
    
    Returns:
        (action, amount_to_adjust, urgency)
    """
    position_diff = current_position - target_position
    
    if abs(position_diff) < 5:
        return ('NO_ACTION', 0, 'LOW')
    
    elif position_diff > 0:
        # Need to reduce position
        amount_to_sell = (position_diff / 100) * portfolio_value
        urgency = 'HIGH' if position_diff > 20 else 'MEDIUM'
        return ('SELL', amount_to_sell, urgency)
    
    else:
        # Need to increase position
        amount_to_buy = (abs(position_diff) / 100) * portfolio_value
        urgency = 'HIGH' if abs(position_diff) > 20 else 'MEDIUM'
        return ('BUY', amount_to_buy, urgency)
```

### Example Scenarios

**Scenario 1: Extreme Greed (Sentiment = 75)**
```
Market State: Extreme Greed
Target Position: 20%
Current Position: 80% of portfolio
Portfolio Value: $157,220

Analysis:
- Need to reduce from 80% to 20%
- Amount to sell: (80% - 20%) × $157,220 = $94,332
- Action: AGGRESSIVE_SELL
- Urgency: HIGH

Recommendation:
1. Sell most profitable positions first
2. Keep only highest conviction stocks
3. Build large cash buffer for future opportunities
```

**Scenario 2: Extreme Fear (Sentiment = 25)**
```
Market State: Extreme Fear
Target Position: 95%
Current Position: 20% of portfolio
Portfolio Value: $157,220

Analysis:
- Need to increase from 20% to 95%
- Amount to buy: (95% - 20%) × $157,220 = $117,915
- Action: AGGRESSIVE_BUY
- Urgency: HIGH

Recommendation:
1. Deploy cash into quality stocks
2. Focus on oversold high-quality stocks
3. Use margin if available (cautiously)
```

### Important Considerations

**1. Gradual Adjustment**
- Don't adjust all at once
- Scale in/out over 3-5 trading days
- Monitor market conditions during adjustment

**2. Signal Confirmation**
- Check multiple indicators (sentiment, valuation, technical)
- Don't rely solely on one metric
- Consider market regime (bull/bear/sideways)

**3. Risk Management**
- Always maintain some cash for emergencies
- Don't go 100% long even in extreme fear
- Don't go 100% cash even in extreme greed

---

## Position Sizing Rules

### Rule 1: Maximum Single Position

**Hard Limit:** No single stock > 15% of total portfolio value

```python
def check_position_limit(symbol, portfolio_value, max_pct=15):
    """
    Check if position exceeds maximum allowed
    
    Returns: (is_within_limit, allowed_value, excess_value)
    """
    max_allowed = portfolio_value * (max_pct / 100)
    current_position = get_position_value(symbol)
    
    is_within = current_position <= max_allowed
    excess = max(0, current_position - max_allowed)
    
    return is_within, max_allowed, excess
```

**Rationale:**
- Prevents over-concentration
- Limits impact of single-stock risk
- Allows for meaningful position without excessive exposure

**Exceptions:**
- Index funds/ETFs can exceed (lower single-stock risk)
- If user explicitly requests higher allocation (document risk)

### Rule 2: Sector Concentration

**Hard Limit:** No sector > 30% of portfolio

```python
def check_sector_concentration(portfolio, sector_map):
    """
    Check sector concentration
    
    Args:
        portfolio: Dict of {symbol: value}
        sector_map: Dict of {symbol: sector}
    
    Returns: Dict of {sector: concentration_pct}
    """
    sector_values = {}
    total_value = sum(portfolio.values())
    
    for symbol, value in portfolio.items():
        sector = sector_map.get(symbol, 'Other')
        sector_values[sector] = sector_values.get(sector, 0) + value
    
    concentration = {
        sector: (value / total_value) * 100 
        for sector, value in sector_values.items()
    }
    
    return concentration
```

**Common Sectors:**
- Technology
- Healthcare
- Financials
- Consumer Discretionary
- Consumer Staples
- Energy
- Industrials
- Utilities
- Real Estate
- Materials
- Communication Services

**If Sector > 30%:**
1. Identify highest-weighted stocks in sector
2. Recommend reducing positions to rebalance
3. Prioritize reducing lowest-conviction holdings first

### Rule 3: Dynamic Cash Reserve

**IMPORTANT:** Cash reserve is NOT fixed at 10%. It dynamically adjusts based on market sentiment (see Dynamic Position Sizing section above).

**Dynamic Cash Reserve Model:**

| Market State | Cash Reserve | Rationale |
|--------------|--------------|-----------|
| Extreme Greed | **70-90%** | Risk off, preserve capital for future opportunities |
| Greed | **50-70%** | Take profits, build cash buffer |
| Neutral | **30-50%** | Balanced approach |
| Fear | **15-30%** | Deploy cash into value opportunities |
| Extreme Fear | **5-15%** | Maximum deployment into oversold quality stocks |

**Implementation:**

```python
def calculate_target_cash(sentiment_index, portfolio_value):
    """
    Calculate target cash reserve based on market sentiment
    
    Returns: (target_cash_pct, target_cash_amount)
    """
    # Use the inverse of target position
    target_position_pct, target_cash_pct, _ = calculate_target_position(sentiment_index)
    
    target_cash_amount = portfolio_value * (target_cash_pct / 100)
    
    return target_cash_pct, target_cash_amount


def calculate_available_cash(portfolio_value, current_cash, sentiment_index):
    """
    Calculate cash available for new positions based on dynamic model
    
    Args:
        portfolio_value: Total portfolio value
        current_cash: Current cash balance
        sentiment_index: Market sentiment (0-100)
    
    Returns:
        (available_cash, target_cash, surplus_deficit)
    """
    # Get target cash based on sentiment
    _, target_cash_amount = calculate_target_cash(sentiment_index, portfolio_value)
    
    # Calculate available cash (surplus) or deficit
    surplus_deficit = current_cash - target_cash_amount
    
    if surplus_deficit > 0:
        # Have more cash than target, can deploy
        available_cash = surplus_deficit
        status = 'SURPLUS'
    else:
        # Need to raise cash
        available_cash = 0
        status = 'DEFICIT'
    
    return available_cash, target_cash_amount, surplus_deficit, status
```

**Example:**

```python
# Scenario: Extreme Greed (Sentiment = 75)
portfolio_value = $157,220
current_cash = $20,720

target_cash_pct = 80%  # From dynamic model
target_cash_amount = $157,220 × 0.80 = $125,776

# Analysis:
# - Current cash: $20,720
# - Target cash: $125,776
# - Deficit: -$105,056
# - Action: Need to SELL $105,056 worth of stocks to raise cash

# Scenario: Extreme Fear (Sentiment = 25)
portfolio_value = $157,220
current_cash = $20,720

target_cash_pct = 5%  # From dynamic model
target_cash_amount = $157,220 × 0.05 = $7,861

# Analysis:
# - Current cash: $20,720
# - Target cash: $7,861
# - Surplus: +$12,859
# - Action: Can deploy $12,859 into stocks
```

**Rationale:**
- **Contrarian approach:** Build cash when market is greedy, deploy when fearful
- **Risk management:** Protect capital in risky environments
- **Opportunity capture:** Have cash ready when opportunities arise
- **Psychological discipline:** Remove emotion from decision-making

**Hard Limits (Always Apply):**
- Minimum absolute cash: 5% (even in extreme fear)
- Maximum absolute cash: 95% (even in extreme greed)
- Emergency fund: Always keep 5% for emergencies (separate from trading cash)

**Dynamic Adjustment:**
- Market Fear (sentiment < 40): Increase to 15-20%
- Market Greed (sentiment > 70): Increase to 15-20%
- Market Neutral (sentiment 40-70): Maintain 10%

---

## Default Position Allocation

### Base Allocation: 10%

Starting point for most stocks.

```python
def calculate_base_position(portfolio_value, base_pct=10):
    """Calculate base position value"""
    return portfolio_value * (base_pct / 100)
```

### Signal Strength Multiplier

Adjust position size based on conviction.

```python
def calculate_signal_strength(score_components):
    """
    Calculate signal strength from multiple factors
    
    Score Components (each 0-10):
    - Technical: Chart patterns, support/resistance, gaps
    - Fundamental: Valuation, growth, profitability
    - Sentiment: Market conditions, news catalyst
    - Momentum: Price trend, volume
    
    Returns: Multiplier (0.5 to 1.5)
    """
    technical = score_components.get('technical', 5)
    fundamental = score_components.get('fundamental', 5)
    sentiment = score_components.get('sentiment', 5)
    momentum = score_components.get('momentum', 5)
    
    # Weighted average
    avg_score = (
        technical * 0.25 +
        fundamental * 0.25 +
        sentiment * 0.25 +
        momentum * 0.25
    )
    
    # Convert to multiplier
    # Score 0 = 0.5x, Score 5 = 1.0x, Score 10 = 1.5x
    multiplier = 0.5 + (avg_score / 20)
    
    return round(multiplier, 2)
```

**Signal Strength Examples:**

| Score | Multiplier | Position Adjustment |
|-------|------------|---------------------|
| 0-3 | 0.5x | Reduce or avoid |
| 4-5 | 0.75x | Small position |
| 6-7 | 1.0x | Standard position |
| 8-9 | 1.25x | Larger position |
| 10 | 1.5x | Maximum conviction |

### Market Condition Adjustment

Adjust for overall market environment.

```python
def calculate_market_condition(sentiment_index):
    """
    Adjust position based on market sentiment
    
    Args:
        sentiment_index: 0-100 (from longbridge market-temp)
    
    Returns: Multiplier (0.7 to 1.3)
    """
    if sentiment_index < 30:
        # Extreme fear: Good buying opportunity
        return 1.3
    elif sentiment_index < 50:
        # Fear: Slightly bullish
        return 1.1
    elif sentiment_index < 70:
        # Neutral/Greed: Standard
        return 1.0
    else:
        # Extreme greed: Cautious
        return 0.7
```

### Final Position Size Formula

```python
def calculate_target_position(portfolio_value, signal_strength, market_condition, base_pct=10, max_pct=15):
    """
    Calculate target position size
    
    Formula:
    Target = Base × Signal_Strength × Market_Condition
    
    Capped at max_pct
    """
    base_position = portfolio_value * (base_pct / 100)
    
    target = base_position * signal_strength * market_condition
    
    # Apply hard limit
    max_position = portfolio_value * (max_pct / 100)
    target = min(target, max_position)
    
    return round(target, 2)
```

**Example:**

```
Portfolio Value: $100,000
Base Allocation: 10% = $10,000

Signal Analysis:
- Technical: 8 (strong support, upward trend)
- Fundamental: 7 (fair valuation, good growth)
- Sentiment: 6 (market neutral)
- Momentum: 8 (volume confirming)

Signal Strength = 0.5 + ((8+7+6+8)/4 / 20) = 0.5 + 0.29 = 1.19

Market Condition:
- Sentiment Index: 45 (fear)
- Multiplier: 1.1

Target Position = $10,000 × 1.19 × 1.1 = $13,090

Apply max limit: $100,000 × 15% = $15,000

Final Target: $13,090 (13.1% of portfolio)
```

---

## Position Adjustment Rules

### When to Increase Position

**Buy More Signal:**

1. Price near strong support zone (within 5%)
2. Unfilled upward gap nearby acting as support
3. Market sentiment: Fear (index < 50)
4. Positive catalyst from news
5. Volume above average (confirmation)
6. Strong fundamentals (P/E below industry average)
7. Current position below target allocation

**Increase Formula:**

```python
def calculate_position_increase(current_value, target_value, price, support_zone):
    """
    Calculate additional shares to buy
    
    Returns: (additional_value, additional_shares, entry_price)
    """
    if current_value >= target_value:
        return 0, 0, None
    
    additional_value = target_value - current_value
    
    # Optimal entry: near support zone
    if price <= support_zone[1]:
        entry_price = price
    else:
        # Wait for pullback
        entry_price = support_zone[1]
    
    additional_shares = int(additional_value / entry_price)
    
    return additional_value, additional_shares, entry_price
```

### When to Reduce Position

**Sell Signal:**

1. Price near strong resistance zone (within 5%)
2. Unfilled downward gap nearby acting as resistance
3. Market sentiment: Extreme greed (index > 70)
4. Negative catalyst from news
5. Current position exceeds target allocation
6. Valuation extended (P/E above industry average)
7. Sector over-concentration

**Reduce Formula:**

```python
def calculate_position_reduction(current_value, target_value, current_shares, price):
    """
    Calculate shares to sell
    
    Returns: (reduce_value, reduce_shares, exit_price)
    """
    if current_value <= target_value:
        return 0, 0, None
    
    reduce_value = current_value - target_value
    reduce_shares = int(reduce_value / price)
    
    # Current price as exit (or wait for resistance test)
    exit_price = price
    
    return reduce_value, reduce_shares, exit_price
```

**Partial Reduction Strategy:**

```
If position significantly overweight (> 20% of portfolio):
- Reduce 50% immediately
- Reduce remaining 50% if price continues higher

If position moderately overweight (15-20%):
- Reduce 25-30% at current price
- Reduce more if resistance reached
```

### When to Exit Completely

**Exit All Signal:**

1. Fundamental deterioration (earnings miss, guidance cut)
2. Technical breakdown (below key support with volume)
3. Negative catalyst (regulatory, competitive, legal)
4. Position purpose no longer valid (thesis broken)
5. Better opportunity elsewhere (opportunity cost)

---

## Stop Loss Management

### Hard Stop Loss

**Fixed Percentage:** 8-10% below entry price

```python
def set_hard_stop(entry_price, stop_pct=8):
    """Set fixed percentage stop loss"""
    return entry_price * (1 - stop_pct / 100)
```

### Trailing Stop Loss

**Follow Price Up:**

```python
def update_trailing_stop(current_price, highest_price_since_entry, trail_pct=10):
    """
    Update trailing stop loss
    
    Triggers when price falls X% from highest point since entry
    """
    trailing_stop = highest_price_since_entry * (1 - trail_pct / 100)
    return trailing_stop

# Example
Entry Price: $100
Price rises to: $120
Trailing Stop: $120 × 0.90 = $108

If price falls to $108, sell.
If price rises to $130, trailing stop moves to $117.
```

### Support-Based Stop Loss

**Place stop below key support:**

```python
def set_support_stop(entry_price, support_zone, buffer_pct=3):
    """
    Set stop loss below support zone
    
    Buffer allows for slight penetration before triggering
    """
    stop = support_zone[0] * (1 - buffer_pct / 100)
    
    # Ensure stop isn't too far from entry
    max_stop_distance = entry_price * 0.15  # Max 15% stop
    if entry_price - stop > max_stop_distance:
        stop = entry_price * 0.85
    
    return stop
```

**Stop Loss Selection:**

| Situation | Stop Type | Placement |
|-----------|-----------|-----------|
| Volatile stock | Support-based | Below strong support |
| Trend following | Trailing | 10-15% below high |
| Value investment | Hard stop | 10-12% below entry |
| Swing trade | Hard stop | 5-8% below entry |

---

## Rebalancing Strategy

### Time-Based Rebalancing

**Frequency:** Monthly or Quarterly

```python
def rebalance_portfolio(portfolio, target_allocations, threshold_pct=5):
    """
    Check if rebalancing needed
    
    Args:
        portfolio: Current {symbol: value}
        target_allocations: Target {symbol: pct}
        threshold_pct: Rebalance if deviation > threshold
    
    Returns: List of rebalancing actions
    """
    total_value = sum(portfolio.values())
    actions = []
    
    for symbol, target_pct in target_allocations.items():
        current_value = portfolio.get(symbol, 0)
        current_pct = (current_value / total_value) * 100
        
        deviation = abs(current_pct - target_pct)
        
        if deviation > threshold_pct:
            target_value = total_value * (target_pct / 100)
            action = 'BUY' if current_value < target_value else 'SELL'
            amount = abs(target_value - current_value)
            
            actions.append({
                'symbol': symbol,
                'action': action,
                'current_pct': round(current_pct, 1),
                'target_pct': target_pct,
                'deviation': round(deviation, 1),
                'amount': round(amount, 2)
            })
    
    return sorted(actions, key=lambda x: x['deviation'], reverse=True)
```

### Trigger-Based Rebalancing

**Rebalance when:**

1. Single position exceeds 15%
2. Sector concentration exceeds 30%
3. Cash falls below 10%
4. Significant price move (> 20% in a stock)
5. Signal strength change (upgraded/downgraded)

---

## Risk Management Framework

### Portfolio Heat Map

```python
def generate_risk_assessment(portfolio, kline_data_dict, fundamentals_dict):
    """
    Generate portfolio risk assessment
    
    Returns: Risk score (0-100, lower is better)
    """
    risk_score = 0
    
    # 1. Concentration risk
    max_position_pct = max([v / sum(portfolio.values()) for v in portfolio.values()])
    risk_score += max(0, (max_position_pct - 0.15) * 100) * 2
    
    # 2. Sector concentration
    sector_conc = check_sector_concentration(portfolio, get_sector_map())
    max_sector = max(sector_conc.values())
    risk_score += max(0, (max_sector - 30) * 1.5)
    
    # 3. Volatility risk (from K-line)
    avg_volatility = np.mean([
        calculate_volatility(kline_data_dict[symbol]) 
        for symbol in portfolio.keys()
    ])
    risk_score += avg_volatility * 10
    
    # 4. Valuation risk
    avg_pe_ratio = np.mean([
        fundamentals_dict[symbol]['pe'] / fundamentals_dict[symbol]['industry_pe']
        for symbol in portfolio.keys()
    ])
    risk_score += max(0, (avg_pe_ratio - 1.0) * 20)
    
    # 5. Cash buffer
    cash_pct = get_cash_percentage()
    risk_score += max(0, (10 - cash_pct) * 2)
    
    return min(100, max(0, risk_score))
```

**Risk Score Interpretation:**

| Score | Risk Level | Action |
|-------|------------|--------|
| 0-20 | Low | Can add positions |
| 21-40 | Moderate | Maintain current allocation |
| 41-60 | Elevated | Consider reducing risk |
| 61-80 | High | Rebalancing recommended |
| 81-100 | Very High | Immediate risk reduction needed |

---

## Example Scenarios

### Scenario 1: Initial Buy

```
Symbol: NVDA.US
Portfolio Value: $100,000
Current Cash: $25,000

Analysis:
- Technical Score: 8 (strong uptrend, volume confirmation)
- Fundamental Score: 7 (fair valuation, AI growth)
- Sentiment Score: 6 (neutral market)
- Momentum Score: 9 (very strong)

Signal Strength: 1.35
Market Condition: 1.0 (neutral)

Target Position = $10,000 × 1.35 × 1.0 = $13,500

Current NVDA Position: $0

Recommendation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action: BUY
Amount: $13,500
Shares: ~50 (at $270/share)
Entry Zone: $265-$275 (near support)
Stop Loss: $243 (below support)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Remaining Cash: $11,500 (11.5% of portfolio) ✓
```

### Scenario 2: Position Increase

```
Symbol: AAPL.US
Portfolio Value: $100,000
Current AAPL Position: $8,000 (8%)
Current Price: $175

Analysis:
- Price near strong support at $170
- Unfilled upward gap at $168-$172
- Market sentiment: 35 (fear)
- Signal Strength: 1.2

Target Position = $10,000 × 1.2 × 1.1 = $13,200

Current: $8,000
Target: $13,200
Gap: $5,200

Recommendation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action: BUY MORE
Additional Amount: $5,200
Additional Shares: ~30 (at $175)
New Position: $13,200 (13.2%)
Stop Loss: $162 (below gap support)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Scenario 3: Position Reduction

```
Symbol: TSLA.US
Portfolio Value: $100,000
Current TSLA Position: $18,000 (18% - OVERWEIGHT)
Current Price: $250

Analysis:
- Price near resistance at $255
- Unfilled downward gap at $252-$248
- Market sentiment: 75 (greed)
- Signal Strength: 0.7 (cautious)

Target Position = $10,000 × 0.7 × 0.7 = $4,900

Current: $18,000
Target: $4,900
Reduction: $13,100

Recommendation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action: REDUCE
Sell Amount: $13,100
Sell Shares: ~52 (at $250)
New Position: $4,900 (4.9%)

Reasons:
- Position exceeds 15% limit (currently 18%)
- Near resistance zone
- Market overly greedy
- Gap resistance overhead
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Staged Exit:
- Sell 26 shares now ($6,500)
- Sell 26 shares if price reaches $255
```

### Scenario 4: Complete Exit

```
Symbol: META.US
Portfolio Value: $100,000
Current META Position: $12,000
Current Price: $480

Analysis:
- Earnings miss: Revenue below expectations
- Guidance cut: Weak ad revenue outlook
- Technical: Breakdown below $500 support on high volume
- News: Increased competition from TikTok

Recommendation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action: EXIT ALL
Sell Amount: $12,000
Sell Shares: ~25 (at $480)

Reasons:
- Fundamental thesis broken (earnings deterioration)
- Technical breakdown confirmed
- Negative catalyst present
- Better opportunities elsewhere
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Key Takeaways

1. **Hard limits protect capital** — never exceed position/sector/cash limits
2. **Signal strength adjusts conviction** — higher conviction = larger position
3. **Market conditions adjust risk** — fearful = more aggressive, greedy = cautious
4. **Stop losses are mandatory** — every position needs an exit plan
5. **Rebalance regularly** — don't let positions drift too far from targets
6. **Document all decisions** — rationale matters for learning and accountability

---

## Configuration Reference

Default settings (customize in `~/.config/stock-analysis/config.json`):

```json
{
  "max_position_pct": 15,
  "max_sector_pct": 30,
  "min_cash_reserve": 10,
  "base_allocation_pct": 10,
  "rebalance_threshold": 5,
  "hard_stop_pct": 8,
  "trailing_stop_pct": 10,
  "stop_buffer_pct": 3
}
```

Adjust based on:
- Risk tolerance (conservative vs aggressive)
- Market conditions
- Investment horizon (short-term vs long-term)
- Portfolio size
