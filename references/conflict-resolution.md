# Strategy Conflict Resolution Reference (策略冲突解决)

## Overview

When analyzing stocks, different frameworks often give conflicting signals. This reference provides systematic methods to resolve these conflicts and make confident decisions.

---

## ⚔️ Common Conflict Scenarios

### Conflict 1: Value Zone vs Gap Analysis

**Scenario:**
```
Value Zone Analysis:
├─ Fair Value: $150-$170
├─ Current Price: $145
├─ Position: UNDERVALUED
└─ Signal: BUY

Gap Analysis:
├─ Recent upward gap: $142-$148 (2 days ago)
├─ Gap type: Common
├─ Fill probability: 70%
└─ Signal: WAIT for pullback to $142

Conflict: Value says buy, Gap says wait
```

**Resolution Framework:**

```python
def resolve_value_gap_conflict(value_analysis, gap_analysis, investment_horizon):
    """
    Resolve conflict between value zone and gap analysis
    
    Priority depends on:
    1. Investment horizon (long-term vs swing)
    2. Gap type and fill probability
    3. Conviction level
    """
    
    if investment_horizon == 'LONG_TERM':
        # Long-term: Value investing rules
        # Buffett: "Time in market > Timing the market"
        
        if value_analysis['position'] in ['DEEP_VALUE', 'VALUE']:
            if gap_analysis['nearest_gap']['type'] == 'BREAKAWAY':
                # Breakaway gap confirms trend, can buy now
                return {
                    'action': 'BUY_NOW',
                    'reason': 'Value + Breakaway gap = Strong buy signal',
                    'strategy': 'Full position, gap confirms trend'
                }
            elif gap_analysis['nearest_gap']['type'] == 'EXHAUSTION':
                # Exhaustion gap at bottom = reversal signal
                return {
                    'action': 'BUY_NOW',
                    'reason': 'Exhaustion gap + undervalued = Reversal opportunity',
                    'strategy': 'Full position, catching reversal'
                }
            else:
                # Common/Runaway gap - start small, add on pullback
                return {
                    'action': 'BUY_PARTIAL',
                    'reason': 'Good value, but gap may pull back',
                    'strategy': '50% now, 50% on gap fill'
                }
        else:
            # Fair value or overvalued - respect gap signal
            return {
                'action': 'WAIT',
                'reason': 'Not enough value discount to ignore gap risk',
                'strategy': 'Wait for gap fill or better value'
            }
    
    elif investment_horizon == 'SWING_TRADE':
        # Swing: Technical rules
        # Gap analysis takes priority
        
        if gap_analysis['distance_to_gap_pct'] < 3:
            return {
                'action': 'WAIT',
                'reason': 'Price too close to gap, wait for test',
                'strategy': 'Wait for pullback to gap zone'
            }
        elif gap_analysis['fill_probability'] > 0.6:
            return {
                'action': 'WAIT',
                'reason': 'High probability of gap fill',
                'strategy': 'Wait for fill, then buy'
            }
        else:
            return {
                'action': 'BUY_NOW',
                'reason': 'Low fill probability, trend likely to continue',
                'strategy': 'Enter with tight stop below gap'
            }
    
    else:  # DAY_TRADE
        # Day trading: Pure technical
        return {
            'action': 'FOLLOW_GAP',
            'reason': 'Short-term: Gap rules supreme',
            'strategy': gap_analysis['recommendation']
        }
```

---

### Conflict 2: Moat Score vs Valuation

**Scenario:**
```
Moat Analysis:
├─ Moat Score: 9/10 (Wide moat)
├─ Company: Wide moat, durable
└─ Signal: Pay premium

Valuation Analysis:
├─ P/E: 35x (vs industry 20x)
├─ P/B: 8x (vs industry 3x)
├─ DCF Fair Value: $150
├─ Current Price: $200
└─ Signal: OVERVALUED

Conflict: Great company, expensive price
```

**Resolution Framework:**

```python
def resolve_moat_valuation_conflict(moat_analysis, valuation, current_price):
    """
    Resolve conflict between moat quality and valuation
    
    Buffett's rule: "It's far better to buy a wonderful company at a fair price 
    than a fair company at a wonderful price."
    
    But: Even wonderful companies can be overpriced
    """
    
    moat_score = moat_analysis['total_score']
    fair_value = valuation['fair_value']
    premium = (current_price - fair_value) / fair_value
    
    # Wide moat companies deserve some premium
    if moat_score >= 7:
        # Wide moat
        max_acceptable_premium = {
            9: 0.30,   # Exceptional moat: up to 30% premium
            8: 0.20,   # Strong moat: up to 20% premium
            7: 0.10    # Narrow moat: up to 10% premium
        }.get(moat_score, 0.10)
        
        if premium <= max_acceptable_premium:
            return {
                'action': 'BUY',
                'reason': f"Wide moat justifies {premium:.0%} premium",
                'fair_value_adjusted': fair_value * (1 + max_acceptable_premium),
                'strategy': 'Premium justified by moat quality'
            }
        else:
            return {
                'action': 'WAIT',
                'reason': f"Even for wide moat, {premium:.0%} premium is too high",
                'target_price': fair_value * (1 + max_acceptable_premium),
                'strategy': f"Wait for pullback to ${fair_value * (1 + max_acceptable_premium):.0f}"
            }
    
    elif moat_score >= 5:
        # Narrow moat - limited premium tolerance
        if premium <= 0.05:
            return {
                'action': 'BUY_SMALL',
                'reason': 'Narrow moat, small premium acceptable',
                'strategy': 'Small position, monitor moat trend'
            }
        else:
            return {
                'action': 'AVOID',
                'reason': 'Narrow moat does not justify premium',
                'strategy': 'Look for better value elsewhere'
            }
    
    else:
        # No moat - no premium acceptable
        if premium < 0:  # Trading below fair value
            # But check for value trap!
            return {
                'action': 'CHECK_VALUE_TRAP',
                'reason': 'No moat, even at discount need to check for trap',
                'strategy': 'Run value trap detection first'
            }
        else:
            return {
                'action': 'AVOID',
                'reason': 'No moat, trading at premium - pass',
                'strategy': 'Avoid'
            }
```

---

### Conflict 3: Market Sentiment vs Individual Stock Signal

**Scenario:**
```
Market Analysis:
├─ Sentiment: 75 (Greed)
├─ Valuation: 90 (Extreme)
├─ Target Position: 25% total
└─ Signal: REDUCE RISK

Individual Stock Analysis:
├─ Stock: NVDA
├─ Score: 9/10
├─ Price: Near support
├─ Gap: Upward gap support
└─ Signal: BUY

Conflict: Market says reduce, stock says buy
```

**Resolution Framework:**

```python
def resolve_market_stock_conflict(market_analysis, stock_analysis, current_portfolio):
    """
    Resolve conflict between market conditions and individual stock signal
    
    Rule: Market regime trumps individual stock signals
    Exception: If stock is high conviction and portfolio has room
    """
    
    market_state = market_analysis['market_state']
    target_position = market_analysis['target_position']
    current_position = current_portfolio['position_pct']
    
    # Position room available?
    room_available = target_position - current_position
    
    if market_state in ['EXTREME_GREED', 'GREED']:
        # Market is risky
        
        if stock_analysis['score'] >= 9:
            # Exceptional stock
            if room_available > 0:
                return {
                    'action': 'BUY_SMALL',
                    'reason': 'Exceptional stock, but market risky - small position only',
                    'max_position': min(room_available, 0.05),  # Max 5% addition
                    'strategy': 'Tight stop loss, monitor market closely'
                }
            else:
                return {
                    'action': 'HOLD',
                    'reason': 'No room in portfolio (market too risky)',
                    'strategy': 'Wait for market pullback or reduce other positions first'
                }
        else:
            return {
                'action': 'NO_BUY',
                'reason': 'Market risk too high for non-exceptional stocks',
                'strategy': 'Preserve capital for better entry'
            }
    
    elif market_state in ['EXTREME_FEAR', 'FEAR']:
        # Market is fearful = opportunity
        
        if stock_analysis['score'] >= 7:
            return {
                'action': 'BUY',
                'reason': 'Good stock + fearful market = Opportunity',
                'position_size': min(room_available, 0.15),  # Up to 15%
                'strategy': 'Deploy capital into quality'
            }
        else:
            return {
                'action': 'SELECTIVE_BUY',
                'reason': 'Fearful market, but only buy quality',
                'strategy': 'Focus on high-conviction stocks only'
            }
    
    else:  # NEUTRAL market
        # Follow individual stock signal
        return {
            'action': 'FOLLOW_STOCK_SIGNAL',
            'reason': 'Neutral market - stock quality matters',
            'strategy': stock_analysis['recommendation']
        }
```

---

### Conflict 4: ROIC vs Current Earnings

**Scenario:**
```
ROIC Analysis:
├─ ROIC: 25% (Excellent)
├─ Trend: Improving
├─ Spread vs WACC: +15%
└─ Signal: Quality business

Earnings Analysis:
├─ Recent Quarter: Missed by 10%
├─ Guidance: Lowered
├─ P/E: Still high at 25x
└─ Signal: CAUTION

Conflict: Great business quality, poor recent performance
```

**Resolution Framework:**

```python
def resolve_roic_earnings_conflict(roic_analysis, earnings_analysis, financials):
    """
    Resolve conflict between ROIC (business quality) and recent earnings
    
    Key insight: ROIC is structural, earnings are cyclical
    - Short-term: Earnings matter for valuation
    - Long-term: ROIC determines compounding
    """
    
    if roic_analysis['trend'] == 'IMPROVING' or roic_analysis['trend'] == 'STABLE':
        # Structural quality intact
        
        # Check if earnings miss is cyclical or structural
        cyclical_factors = identify_cyclical_factors(earnings_analysis)
        
        if cyclical_factors:
            # Earnings issue is cyclical
            return {
                'action': 'BUY_ON_WEAKNESS',
                'reason': 'High ROIC business, cyclical earnings weakness',
                'strategy': 'Buy on earnings dip - structural quality intact',
                'watch_for': 'Earnings recovery in next 1-2 quarters'
            }
        else:
            # Check if ROIC is about to decline
            leading_indicators = check_roic_leading_indicators(financials)
            
            if leading_indicators['warning']:
                return {
                    'action': 'WAIT',
                    'reason': 'Earnings miss may signal ROIC decline ahead',
                    'strategy': 'Wait for confirmation that ROIC is intact'
                }
            else:
                return {
                    'action': 'MONITOR',
                    'reason': 'Earnings weak but no sign of ROIC deterioration',
                    'strategy': 'Small position, monitor closely'
                }
    
    else:  # ROIC declining
        # Structural issue
        return {
            'action': 'AVOID',
            'reason': 'Declining ROIC + weak earnings = structural problem',
            'strategy': 'Pass, look for better opportunities'
        }
```

---

### Conflict 5: Multiple Timeframe Signals

**Scenario:**
```
Weekly Chart (Long-term):
├─ Uptrend intact
├─ Above 50-week MA
├─ Support at $140
└─ Signal: BULLISH

Daily Chart (Short-term):
├─ Broke below 50-day MA
├─ Distribution pattern
├─ Target: $135
└─ Signal: BEARISH

Conflict: Weekly bullish, daily bearish
```

**Resolution Framework:**

```python
def resolve_timeframe_conflict(weekly_analysis, daily_analysis, investment_horizon):
    """
    Resolve conflict between different timeframe signals
    
    General rule:
    - Long-term investors: Weekly chart rules
    - Swing traders: Daily chart rules
    - Position sizing: Use weekly for direction, daily for entry
    """
    
    if investment_horizon == 'LONG_TERM':
        # Weekly chart dominates
        if weekly_analysis['signal'] == 'BULLISH':
            return {
                'action': 'BUY_ON_DAILY_WEAKNESS',
                'reason': 'Weekly trend bullish, use daily weakness as entry',
                'strategy': 'Accumulate as daily chart shows weakness',
                'entry_timing': 'Wait for daily stabilization'
            }
        else:
            return {
                'action': 'AVOID',
                'reason': 'Weekly trend bearish - stay away',
                'strategy': 'Wait for weekly trend to turn'
            }
    
    elif investment_horizon == 'SWING_TRADE':
        # Daily chart dominates
        return {
            'action': 'FOLLOW_DAILY',
            'reason': 'Swing trades follow short-term signals',
            'strategy': daily_analysis['recommendation']
        }
    
    else:  # POSITION_TRADE (weeks to months)
        # Use weekly for direction, daily for timing
        if weekly_analysis['signal'] == 'BULLISH':
            if daily_analysis['signal'] == 'BEARISH':
                return {
                    'action': 'WAIT_FOR_DAILY_REVERSAL',
                    'reason': 'Weekly bullish but daily bearish - wait for alignment',
                    'strategy': 'Wait for daily to turn bullish, then enter'
                }
            else:
                return {
                    'action': 'BUY',
                    'reason': 'Weekly and daily aligned bullish',
                    'strategy': 'Enter with weekly support as stop'
                }
        else:
            return {
                'action': 'AVOID',
                'reason': 'Weekly bearish',
                'strategy': 'No long positions'
            }
```

---

## 🎯 Universal Conflict Resolution Framework

### Priority Hierarchy

When in doubt, follow this hierarchy:

```
1. MARKET REGIME (Most Important)
   └─ Market conditions trump everything
   
2. BUSINESS QUALITY (ROIC + Moat)
   └─ Structural quality beats short-term noise
   
3. VALUATION
   └─ Price matters, but quality can justify premium
   
4. TECHNICAL (Gaps, Support/Resistance)
   └─ Timing tool, not primary decision maker
   
5. SHORT-TERM NOISE (Least Important)
   └─ Earnings misses, headlines, daily fluctuations
```

### Decision Matrix

```python
def resolve_all_conflicts(analysis_results):
    """
    Master conflict resolution function
    
    Takes all analysis results and produces final recommendation
    """
    market = analysis_results['market']
    stock = analysis_results['stock']
    moat = analysis_results['moat']
    roic = analysis_results['roic']
    valuation = analysis_results['valuation']
    gaps = analysis_results['gaps']
    
    # Step 1: Check market regime (highest priority)
    if market['state'] in ['EXTREME_GREED']:
        if market['valuation'] > 85:
            # High risk market
            if stock['score'] < 9:
                return {
                    'final_action': 'NO_NEW_POSITIONS',
                    'reason': 'Extreme market risk, only exceptional stocks allowed'
                }
    
    # Step 2: Check business quality
    quality_score = (moat['total_score'] + roic['quality_score']) / 2
    
    if quality_score < 5:
        # Poor quality
        return {
            'final_action': 'AVOID',
            'reason': f'Low quality business (score: {quality_score:.1f})'
        }
    
    # Step 3: Check for value trap
    if valuation['position'] in ['VALUE', 'DEEP_VALUE']:
        if quality_score < 6:
            # Cheap but low quality = potential trap
            return {
                'final_action': 'AVOID',
                'reason': 'Value trap risk: cheap but low quality'
            }
    
    # Step 4: Check valuation relative to quality
    fair_premium = calculate_fair_premium_for_quality(quality_score)
    actual_premium = valuation['premium_to_fair_value']
    
    if actual_premium > fair_premium * 1.5:
        # Too expensive even for quality
        return {
            'final_action': 'WAIT',
            'reason': f'Overpriced: {actual_premium:.0%} premium exceeds fair {fair_premium:.0%}'
        }
    
    # Step 5: Check gap timing
    if gaps['nearest_gap']:
        gap_distance = gaps['distance_to_gap_pct']
        if gap_distance < 2:
            # Near gap
            if gaps['fill_probability'] > 0.5:
                # Likely to pull back
                return {
                    'final_action': 'BUY_PARTIAL',
                    'reason': 'Good fundamentals, but gap suggests waiting',
                    'strategy': '50% now, 50% on pullback'
                }
    
    # Step 6: Final recommendation
    position_size = calculate_position_size(quality_score, valuation, market)
    
    return {
        'final_action': 'BUY',
        'quality_score': quality_score,
        'position_size': position_size,
        'entry_strategy': determine_entry_strategy(gaps, valuation),
        'stop_loss': calculate_stop_loss(gaps, valuation),
        'reason': generate_final_reason(analysis_results, quality_score, valuation)
    }
```

---

## Quick Reference: Conflict Resolution Checklist

When signals conflict:

1. **Ask: What's my investment horizon?**
   - Long-term → Prioritize fundamentals (moat, ROIC, valuation)
   - Short-term → Priorify technicals (gaps, support/resistance)

2. **Ask: What's the market regime?**
   - Extreme Greed → Reduce risk, raise bar for new positions
   - Extreme Fear → Opportunity, but check quality first

3. **Ask: Is the business quality high?**
   - Wide moat + High ROIC → Can pay fair price
   - No moat + Low ROIC → Even cheap may be expensive

4. **Ask: Is this a value trap?**
   - Cheap + Poor quality → Likely trap
   - Cheap + High quality → Opportunity

5. **Ask: What's the risk/reward?**
   - Good fundamentals + Bad timing → Scale in
   - Bad fundamentals + Good timing → Pass

---

## Example: Full Conflict Resolution

```
Symbol: NVDA
Analysis Date: 2026-04-20

Market Analysis:
├─ State: GREED (Score: 68)
├─ Valuation: 90 (Extreme)
├─ Target Position: 25%
└─ Current Position: 20%

Stock Analysis:
├─ Score: 9/10
├─ Price: $710
├─ 52-Week Range: $450-$720

Moat Analysis:
├─ Score: 8.5/10 (Wide moat)
├─ Network Effect: 2
├─ Switching Cost: 2
└─ Brand: 1.5

ROIC Analysis:
├─ ROIC: 42% (Exceptional)
├─ WACC: 10%
├─ Spread: +32%
└─ Quality: EXCELLENT

Valuation:
├─ Fair Value (DCF): $650
├─ Current Price: $710
├─ Premium: +9%
└─ Fair Premium for Moat: +20%

Gap Analysis:
├─ Nearest Gap: Upward $695-$702 (5 days ago)
├─ Type: Runaway
├─ Fill Probability: 35%
└─ Signal: Support nearby

CONFLICTS:
1. Market = Greed vs Stock = Strong buy
2. Valuation = Premium vs Moat = Justifies premium
3. Gap = Wait for pullback vs Stock = Strong

RESOLUTION:
├─ Priority 1: Market regime → Limit new positions
├─ Priority 2: Business quality → Exceptional (can buy)
├─ Priority 3: Valuation → Within fair premium (9% < 20%)
└─ Priority 4: Gap → Low fill probability, don't wait

FINAL RECOMMENDATION:
├─ Action: BUY_SMALL
├─ Position: +3% (to reach 23% total, under 25% limit)
├─ Entry: Current price $710
├─ Stop: $650 (fair value / gap support)
├─ Reason: Exceptional quality, reasonable premium, but market risk limits position size
```
