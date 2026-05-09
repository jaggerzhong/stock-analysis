# Gap Theory Reference

## Overview

Price gaps occur when there's a significant difference between the previous day's close and the current day's open. In technical analysis, gaps provide critical signals for support, resistance, and trend continuation/reversal.

---

## Gap Definition

**⚠️ 正确定义：缺口是两个交易日价格区间没有重叠**

### 向上缺口 (Upward Gap)
```
今日最低价 > 昨日最高价

Example:
Yesterday: Low $98, High $100
Today: Low $102, High $105
→ Today_Low ($102) > Yesterday_High ($100) = Upward Gap
→ Gap Zone: $100 - $102
```

### 向下缺口 (Downward Gap)
```
今日最高价 < 昨日最低价

Example:
Yesterday: Low $100, High $105
Today: Low $95, High $98
→ Today_High ($98) < Yesterday_Low ($100) = Downward Gap
→ Gap Zone: $98 - $100
```

### ❌ 常见错误定义
```
错误：Gap % = (Today_Open - Yesterday_Close) / Yesterday_Close × 100
问题：开盘价-收盘价差距 ≥ 1% 不等于真正的缺口！
原因：即使开盘价跳空，如果盘中价格重叠，就不是真正的缺口。

正确：使用 High/Low 判断价格区间是否重叠
```

---

## Gap Types

### 1. Breakaway Gap (突破缺口)

**Characteristics:**
- Occurs at the beginning of a new trend
- Accompanied by significant volume surge (> 1.5x average)
- Often breaks through key support/resistance levels
- **Rarely fills** (fill rate: ~20%)

**Trading Strategy:**
- Enter in direction of gap
- Place stop loss below/above the gap zone
- Target: Next resistance/support level

**Example:**
```
Stock consolidating at $50 for weeks
Gap up to $52.50 on heavy volume (5% gap)
Indicates strong bullish breakout
```

### 2. Runaway Gap (中继缺口/测量缺口)

**Characteristics:**
- Occurs in the middle of an established trend
- Moderate volume increase
- Also called "measuring gap" — helps estimate trend continuation
- **Partially fills** before continuing (fill rate: ~50%)

**Trading Strategy:**
- Add to position in trend direction
- Target = Entry + (Entry - Start_of_trend)

**Example:**
```
Uptrend starts at $50
Runaway gap at $60
Target: $70 (equal distance)
```

### 3. Exhaustion Gap (衰竭缺口)

**Characteristics:**
- Occurs near the end of a trend
- Volume may spike initially then decline
- **Fills quickly** (within 3-10 days, fill rate: ~80%)
- Signals trend reversal

**Trading Strategy:**
- Take profits if holding
- Look for reversal confirmation
- Consider counter-trend position

**Example:**
```
Stock rallied from $50 to $70
Exhaustion gap up to $72
Next few days: gap fills, price drops below $70
Signals uptrend exhaustion
```

### 4. Common Gap (普通缺口)

**Characteristics:**
- Occurs in trading ranges, not trends
- Low or average volume
- **Fills quickly** (within 1-5 days, fill rate: ~90%)
- No significant trend implication

**Trading Strategy:**
- Fade the gap (bet on fill)
- Short-term trade only
- Low probability, avoid if uncertain

**Example:**
```
Stock trading sideways $50-$55
Gap up to $53 within range
Likely to fill back to $52 within 2 days
```

---

## Gap Detection Algorithm

### Step 1: Data Collection

```bash
# Get at least 60 days of daily K-line data
longbridge kline history SYMBOL.US --start $(date -v-60d +%Y-%m-%d) --end $(date +%Y-%m-%d) --period day --format json
```

### Step 2: Gap Identification

```python
def detect_gaps(kline_data):
    """
    Detect TRUE price gaps from K-line data
    
    ⚠️ 正确逻辑：缺口 = 价格区间无重叠
    - 向上缺口：今日最低价 > 昨日最高价
    - 向下缺口：今日最高价 < 昨日最低价
    
    Args:
        kline_data: List of OHLCV candles (must have high/low)
    
    Returns:
        List of gap objects
    """
    gaps = []
    
    for i in range(1, len(kline_data)):
        yesterday = kline_data[i-1]
        today = kline_data[i]
        
        prev_high = float(yesterday['high'])
        prev_low = float(yesterday['low'])
        today_high = float(today['high'])
        today_low = float(today['low'])
        
        # Check for TRUE gap (no price overlap)
        gap_up = today_low > prev_high    # Upward gap
        gap_down = today_high < prev_low  # Downward gap
        
        if gap_up or gap_down:
            # Calculate gap magnitude
            if gap_up:
                gap_pct = (today_low - prev_high) / prev_high * 100
                gap_zone = (prev_high, today_low)
                direction = 'UP'
            else:
                gap_pct = (prev_low - today_high) / prev_low * 100
                gap_zone = (today_high, prev_low)
                direction = 'DOWN'
            
            # Get average volume for context
            avg_volume_20d = sum([float(c['volume']) for c in kline_data[max(0,i-20):i]]) / min(20, i)
            volume_ratio = float(today['volume']) / avg_volume_20d if avg_volume_20d > 0 else 1
            
            # Check if filled
            current_price = float(kline_data[-1]['close'])
            is_filled = check_gap_filled(current_price, gap_zone, direction)
            
            gaps.append({
                'date': today['date'],
                'direction': direction,
                'magnitude': round(abs(gap_pct), 2),
                'gap_zone': (round(gap_zone[0], 2), round(gap_zone[1], 2)),
                'volume_ratio': round(volume_ratio, 2),
                'is_filled': is_filled,
                'days_ago': len(kline_data) - i - 1,
                'type': classify_gap(gap_pct, volume_ratio, i, len(kline_data))
            })
    
    return gaps

def check_gap_filled(current_price, gap_zone, direction):
    """Check if gap has been filled by current price"""
    if direction == 'up':
        return current_price <= gap_zone[1]
    else:
        return current_price >= gap_zone[0]

def classify_gap(gap_pct, volume_ratio, position_index, total_candles):
    """Classify gap type based on characteristics"""
    
    # Heuristics for classification
    is_upward = gap_pct > 0
    high_volume = volume_ratio > 1.5
    is_recent = position_index > total_candles - 10
    
    if high_volume and not is_recent:
        return 'breakaway'
    elif 1.0 <= volume_ratio <= 1.5:
        return 'runaway'
    elif is_recent and volume_ratio > 1.2:
        return 'exhaustion'
    else:
        return 'common'
```

### Step 3: Gap Analysis Output

For each detected gap, provide:

```
Gap Analysis for AAPL.US

---

## ⚠️ IMPORTANT: Systematic Gap Detection Protocol (避免遗漏缺口)

### 问题根因分析

**为什么会漏掉缺口？**
```
1. 手动肉眼观察 → 容易遗漏
2. 只关注"大"缺口 → 忽略标准阈值(≥1%)的所有缺口
3. 没有逐日计算 → 可能跳过某些日期
4. 没有验证检查 → 分析完成后没有回查
```

### 🔴 强制执行：缺口检测检查清单

**在分析任何股票的缺口时，必须完成以下步骤：**

```markdown
## Gap Detection Checklist

### Step 1: 数据准备
- [ ] 获取至少60天K线数据
- [ ] 确认数据完整（无缺失日期）
- [ ] 记录数据起始和结束日期

### Step 2: 逐日缺口计算（核心）
对每一天执行以下计算：

for i in range(1, len(kline_data)):
    date = kline_data[i]['date']
    prev_high = kline_data[i-1]['high']
    prev_low = kline_data[i-1]['low']
    today_high = kline_data[i]['high']
    today_low = kline_data[i]['low']
    
    # ⚠️ 正确逻辑：价格区间无重叠
    if today_low > prev_high:
        ✅ 记录向上缺口 (gap_up)
        gap_zone = (prev_high, today_low)
    elif today_high < prev_low:
        ✅ 记录向下缺口 (gap_down)
        gap_zone = (today_high, prev_low)

### Step 3: 缺口汇总表（强制输出）
必须生成如下表格：

| 序号 | 日期 | 前日收盘 | 今日开盘 | 缺口% | 缺口区间 | 方向 | 状态 |
|------|------|----------|----------|-------|----------|------|------|
| 1 | YYYY-MM-DD | $XXX.XX | $XXX.XX | ±X.X% | $XX-$XX | ↑/↓ | 填/未填 |

### Step 4: 验证检查
- [ ] 表格是否完整列出所有 ≥1% 的缺口？
- [ ] 缺口数量是否合理？（通常2-5个/60天）
- [ ] 是否有大缺口(>3%)被遗漏？
- [ ] 缺口区间计算是否正确？

### Step 5: 当前价格定位
- [ ] 当前价格相对于每个缺口的位置
- [ ] 哪些缺口是支撑？哪些是阻力？
- [ ] 最近的未填充缺口是什么？
```

### 缺口检测模板代码（直接使用）

```python
def detect_all_gaps_systematic(kline_data):
    """
    系统化缺口检测 - 使用正确的 High/Low 逻辑
    
    ⚠️ 正确逻辑：
    - 向上缺口：今日最低价 > 昨日最高价（无价格重叠）
    - 向下缺口：今日最高价 < 昨日最低价（无价格重叠）
    
    使用方法：
    1. 获取K线数据（必须有 high/low 字段）
    2. 调用此函数
    3. 输出完整缺口表格
    4. 验证是否有遗漏
    """
    if len(kline_data) < 2:
        return []
    
    gaps = []
    current_price = float(kline_data[-1]['close'])
    
    # 逐日检查（从第2天开始）
    for i in range(1, len(kline_data)):
        yesterday = kline_data[i - 1]
        today = kline_data[i]
        
        # 获取 High/Low 数据
        prev_high = float(yesterday['high'])
        prev_low = float(yesterday['low'])
        today_high = float(today['high'])
        today_low = float(today['low'])
        
        # 检测缺口（价格区间无重叠）
        gap_up = today_low > prev_high
        gap_down = today_high < prev_low
        
        if gap_up or gap_down:
            # 计算缺口大小和区间
            if gap_up:
                gap_pct = (today_low - prev_high) / prev_high * 100
                gap_zone = (prev_high, today_low)
                direction = 'UP'
            else:
                gap_pct = (prev_low - today_high) / prev_low * 100
                gap_zone = (today_high, prev_low)
                direction = 'DOWN'
            
            # 检查是否填充
            if direction == 'UP':
                is_filled = current_price <= gap_zone[0]
            else:
                is_filled = current_price >= gap_zone[1]
            
            # 计算成交量比
            if i >= 20:
                avg_vol = sum(float(c['volume']) for c in kline_data[i-20:i]) / 20
                vol_ratio = float(today['volume']) / avg_vol if avg_vol > 0 else 1.0
            else:
                vol_ratio = 1.0
            
            gaps.append({
                'index': len(gaps) + 1,
                'date': today['time'][0:10] if 'time' in today else today.get('date', ''),
                'prev_high': round(prev_high, 2),
                'prev_low': round(prev_low, 2),
                'today_high': round(today_high, 2),
                'today_low': round(today_low, 2),
                'gap_pct': round(gap_pct, 2),
                'gap_zone': (round(gap_zone[0], 2), round(gap_zone[1], 2)),
                'direction': direction,
                'is_filled': is_filled,
                'fill_status': 'FILLED' if is_filled else 'UNFILLED',
                'vol_ratio': round(vol_ratio, 2),
                'days_ago': len(kline_data) - i - 1
            })
    
    return gaps


def print_gap_table(gaps, symbol, current_price):
    """
    打印缺口表格（用于验证）
    """
    print(f"\n{'='*100}")
    print(f"GAP ANALYSIS: {symbol} | Current Price: ${current_price}")
    print(f"{'='*100}")
    print(f"{'#':<3} {'Date':<12} {'Prev High':>10} {'Prev Low':>10} {'Today High':>11} {'Today Low':>10} {'Gap%':>8} {'Gap Zone':>20} {'Dir':<4} {'Status':<10}")
    print(f"{'-'*100}")
    
    for g in gaps:
        zone_str = f"${g['gap_zone'][0]:.2f}-${g['gap_zone'][1]:.2f}"
        print(f"{g['index']:<3} {g['date']:<12} ${g['prev_high']:>8.2f} ${g['prev_low']:>8.2f} ${g['today_high']:>9.2f} ${g['today_low']:>8.2f} {g['gap_pct']:>+7.2f}% {zone_str:>20} {g['direction']:<4} {g['fill_status']:<10}")
    
    print(f"{'='*100}")
    print(f"Total gaps detected: {len(gaps)}")
    print(f"Unfilled gaps: {sum(1 for g in gaps if not g['is_filled'])}")
    print(f"{'='*100}\n")


# 使用示例
"""
kline_data = get_kline_data('CEG.US', days=60)
gaps = detect_all_gaps_systematic(kline_data)
print_gap_table(gaps, 'CEG.US', float(kline_data[-1]['close']))
"""
```

### 实战案例：CEG.US 缺口检测验证

```python
# CEG.US K-line data (2026-02-01 to 2026-04-20)
# 使用上述函数后输出：

================================================================================
GAP ANALYSIS: CEG.US | Current Price: $287.56
================================================================================
#  Date         Prev Close  Today Open    Gap%           Gap Zone Dir Status    
--------------------------------------------------------------------------------
1  2026-03-31     $298.61    $275.05    -7.90%  $275.05-$298.61    DOWN   UNFILLED  
2  2026-04-08     $272.58    $283.00    +3.82%  $272.58-$283.00    UP     UNFILLED  
3  2026-04-14     $291.72    $295.75    +1.38%  $291.72-$295.75    UP     FILLED    
4  2026-04-17     $299.14    $304.02    +1.63%  $299.14-$304.02    UP     UNFILLED  
================================================================================
Total gaps detected: 4
Unfilled gaps: 3
================================================================================

⚠️ 关键发现：
- 3/31 大向下缺口 ($275-$299) 部分未填充
- 4/8 大向上缺口 ($272-$283) 未填充 ← 重要支撑
- 这两个缺口形成 $272-275 重叠支撑区
```

### 实战案例：BABA.US 缺口检测验证

```python
================================================================================
GAP ANALYSIS: BABA.US | Current Price: $140.17
================================================================================
#  Date         Prev Close  Today Open    Gap%           Gap Zone Dir Status    
--------------------------------------------------------------------------------
1  2026-03-19     $134.43    $123.02    -8.49%  $123.02-$134.43    DOWN   FILLED    
2  2026-04-08     $119.72    $128.11    +6.99%  $119.72-$128.11    UP     UNFILLED  
3  2026-04-17     $138.59    $141.15    +1.85%  $138.59-$141.15    UP     UNFILLED  
================================================================================
Total gaps detected: 3
Unfilled gaps: 2
================================================================================

⚠️ 关键发现：
- 4/8 大向上缺口 ($119.72-$128.11) 未填充 ← 强支撑
- 4/17 小向上缺口 ($138.59-$141.15) 未填充，当前价格在缺口内
- 支撑区域: $119.72 - $128.11
```

---

## 🔴 强制规则：缺口分析报告必须包含

每份缺口分析报告必须包含：

1. **缺口汇总表** - 列出所有 ≥1% 的缺口
2. **缺口数量统计** - 总数、未填充数、已填充数
3. **最近未填充缺口** - 支撑/阻力位置
4. **当前价格定位** - 相对于缺口的位置
5. **验证签名** - 确认已逐日检查

```markdown
## Gap Analysis Verification

- [ ] Checked all trading days in period
- [ ] All gaps ≥ 1% included in table
- [ ] Gap zones calculated correctly
- [ ] Fill status verified against current price
- [ ] No gaps missed

Analyst: [Agent Name]
Date: [Analysis Date]
Total gaps found: [N]
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Date: 2026-03-15
Direction: UP
Magnitude: 2.3%
Gap Zone: $180.50 - $184.65
Type: Breakaway
Volume Ratio: 1.8x (above average)
Fill Status: UNFILLED
Days Ago: 35
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Price: $186.20
Distance Above Gap: 1.1%
Role: SUPPORT
Interpretation: Strong support zone. Price unlikely to fall below $180.50 unless major reversal.
```

---

## Gap Trading Rules

### Unfilled Gaps as Support/Resistance

**Upward Gaps (Below Current Price)**
- Act as **SUPPORT**
- Buy when price retraces to gap zone
- Stop loss below gap zone

**Downward Gaps (Above Current Price)**
- Act as **RESISTANCE**
- Sell/short when price rallies to gap zone
- Stop loss above gap zone

### Fill Probability by Gap Type

| Gap Type | Fill Rate | Time to Fill | Trading Strategy |
|----------|-----------|--------------|------------------|
| Breakaway | 20% | Rarely | Don't bet on fill |
| Runaway | 50% | 10-30 days | Partial fill possible |
| Exhaustion | 80% | 3-10 days | Bet on fill |
| Common | 90% | 1-5 days | High probability fade |

### Entry Rules

**Near Gap Support (Upward Gap):**
```
Buy Signal:
1. Price within 3% of gap zone
2. Volume declining (selling exhaustion)
3. Market sentiment neutral or fearful
4. No negative catalysts

Entry: At or slightly above gap top
Stop Loss: 2-3% below gap bottom
Target 1: Previous swing high
Target 2: Next resistance level
```

**Near Gap Resistance (Downward Gap):**
```
Sell Signal:
1. Price within 3% of gap zone
2. Volume declining (buying exhaustion)
3. Market sentiment greedy
4. Negative catalyst present

Entry: At or slightly below gap bottom
Stop Loss: 2-3% above gap top
Target 1: Previous swing low
Target 2: Next support level
```

---

## Practical Examples

### Example 1: Support from Unfilled Upward Gap

```
Symbol: TSLA.US
Current Price: $250

Gap History:
- 2026-02-10: Upward gap $235-$242 (2.9%, breakaway, unfilled)

Analysis:
- Strong support at $235-$242
- Price currently 3.3% above gap
- Breakaway gap unlikely to fill

Recommendation:
- Buy on pullback to $242-$245
- Stop loss: $232
- Target: $275 (previous high)
```

### Example 2: Resistance from Unfilled Downward Gap

```
Symbol: NVDA.US
Current Price: $480

Gap History:
- 2026-03-01: Downward gap $495-$487 (1.6%, exhaustion, unfilled)

Analysis:
- Resistance at $487-$495
- Price currently 1.5% below gap
- Exhaustion gap, high fill probability

Recommendation:
- Reduce position if rallies to $490-$495
- Gap may fill, but expect resistance first
- Buy opportunity if gap fills and bounces
```

### Example 3: Multiple Gaps Confluence

```
Symbol: AAPL.US
Current Price: $185

Gap History:
- 2026-01-15: Upward gap $170-$173 (1.8%, breakaway, unfilled)
- 2026-02-20: Upward gap $175-$178 (1.7%, runaway, unfilled)
- 2026-03-10: Downward gap $188-$185 (1.6%, exhaustion, unfilled)

Analysis:
- Multiple support zones: $170-173, $175-178
- Resistance above at $185-188
- Exhaustion gap at top suggests pullback likely

Recommendation:
- Wait for pullback to $175-178 zone
- Strong confluence of two gaps = very strong support
- Buy signal: pullback to $178 with volume confirmation
```

---

## Key Takeaways

1. **Always check gap context** — not all gaps are created equal
2. **Volume confirms gap significance** — high volume = breakaway/exhaustion
3. **Gap fills are not guaranteed** — breakaway gaps rarely fill
4. **Use gaps with other indicators** — don't rely solely on gap analysis
5. **Time matters** — older gaps are more significant support/resistance
6. **Multiple gaps = stronger levels** — confluence increases reliability

---

## Integration with Stock Analysis Skill

When analyzing a stock:

1. **First:** Get 60+ days of K-line data
2. **Detect:** All gaps ≥ 1%
3. **Classify:** Gap type using volume and trend context
4. **Identify:** Nearest unfilled gap (support or resistance)
5. **Measure:** Distance from current price to gap zone
6. **Recommend:** Trade action based on gap analysis + other factors

Combine with:
- Value zone analysis (for support/resistance confirmation)
- Market sentiment (for timing)
- Position sizing (for risk management)

---

## 🎯 Advanced Gap Analysis (专业级缺口分析)

### Dynamic Fill Probability (动态填充概率)

**Problem:** Fixed fill rates are too simplistic. Fill probability depends on multiple factors.

```python
def calculate_dynamic_fill_probability(gap, market_conditions):
    """
    Calculate dynamic gap fill probability
    
    Factors:
    1. Gap type (base probability)
    2. Gap age (older = less likely to fill)
    3. Gap size (larger = harder to fill)
    4. Market trend (trend affects fill probability)
    5. Test count (more tests = stronger level)
    """
    # Base probabilities by type
    base_prob = {
        'breakaway': 0.20,
        'runaway': 0.50,
        'exhaustion': 0.80,
        'common': 0.90
    }
    
    probability = base_prob.get(gap['type'], 0.50)
    adjustments = []
    
    # 1. Time decay (older gaps less likely to fill)
    days_old = gap['days_ago']
    if days_old > 60:
        probability -= 0.15
        adjustments.append("Old gap (>60 days): -15%")
    elif days_old > 30:
        probability -= 0.10
        adjustments.append("Mature gap (>30 days): -10%")
    elif days_old > 10:
        probability -= 0.05
        adjustments.append("Aged gap (>10 days): -5%")
    
    # 2. Gap magnitude (larger gaps harder to fill)
    magnitude = gap['magnitude']
    if magnitude > 5:
        probability -= 0.20
        adjustments.append(f"Large gap ({magnitude}%): -20%")
    elif magnitude > 3:
        probability -= 0.10
        adjustments.append(f"Medium gap ({magnitude}%): -10%")
    
    # 3. Market trend influence
    trend = market_conditions.get('trend', 'NEUTRAL')
    if trend == 'STRONG_UPTREND' and gap['direction'] == 'up':
        probability -= 0.15
        adjustments.append("Strong uptrend (up gap support): -15%")
    elif trend == 'STRONG_DOWNTREND' and gap['direction'] == 'down':
        probability -= 0.15
        adjustments.append("Strong downtrend (down gap resistance): -15%")
    elif trend == 'HIGH_VOLATILITY':
        probability += 0.10
        adjustments.append("High volatility: +10%")
    
    # 4. Number of tests (more tests = stronger level)
    test_count = gap.get('test_count', 0)
    if test_count >= 3:
        probability -= 0.20
        adjustments.append(f"Tested {test_count} times: -20%")
    elif test_count >= 2:
        probability -= 0.10
        adjustments.append(f"Tested {test_count} times: -10%")
    
    # 5. Volume on gap day
    vol_ratio = gap.get('volume_ratio', 1.0)
    if vol_ratio > 2.0:
        probability -= 0.10
        adjustments.append(f"High volume gap ({vol_ratio:.1f}x): -10%")
    
    # Clamp between 5% and 95%
    final_prob = max(0.05, min(0.95, probability))
    
    return {
        'fill_probability': final_prob,
        'adjustments': adjustments,
        'interpretation': interpret_fill_probability(final_prob)
    }


def interpret_fill_probability(prob):
    """Interpret fill probability for trading"""
    if prob < 0.25:
        return "UNLIKELY to fill - Strong support/resistance"
    elif prob < 0.50:
        return "LOW probability - Decent support/resistance"
    elif prob < 0.70:
        return "MODERATE probability - Weak support/resistance"
    else:
        return "HIGH probability - Likely to fill"
```

---

### Multi-Gap Pattern Analysis (多缺口形态分析)

#### Island Reversal (岛型反转)

**Pattern:**
```
Price action:
1. Upward gap (leaves island)
2. Consolidation (forms island)
3. Downward gap (leaves island in opposite direction)

     ┌───┐
     │   │  ← Island (isolated price action)
─────┘   └─────
  ↑       ↓
Gap up   Gap down

Signal: BEARISH REVERSAL (very strong)
```

**Detection:**
```python
def detect_island_reversal(gaps, kline_data):
    """
    Detect island reversal pattern
    
    Criteria:
    1. Upward gap followed by downward gap
    2. Both gaps unfilled
    3. Time between gaps: 2-10 days
    4. Island price action isolated
    """
    for i in range(len(gaps) - 1):
        gap1 = gaps[i]
        gap2 = gaps[i + 1]
        
        # Must be opposite directions
        if gap1['direction'] == gap2['direction']:
            continue
        
        # Time between gaps
        days_between = abs(gap2['days_ago'] - gap1['days_ago'])
        if days_between < 2 or days_between > 10:
            continue
        
        # Check if island is isolated (gaps don't overlap)
        if gap1['direction'] == 'up':
            island_low = gap1['gap_zone'][1]  # Top of up gap
            island_high = gap2['gap_zone'][0]  # Bottom of down gap
        else:
            island_low = gap2['gap_zone'][1]
            island_high = gap1['gap_zone'][0]
        
        if island_low < island_high:
            return {
                'pattern': 'ISLAND_REVERSAL',
                'signal': 'BEARISH' if gap1['direction'] == 'up' else 'BULLISH',
                'strength': 9,  # Very strong signal
                'island_range': (island_low, island_high),
                'days_on_island': days_between
            }
    
    return None
```

#### Gap Cluster (缺口群)

**Pattern:**
```
Multiple gaps in same direction indicate strong momentum

3+ upward gaps in uptrend:
├─ Signal: Strong bullish momentum
├─ Warning: Extended, watch for exhaustion
└─ Trading: Ride trend, tight stops

3+ downward gaps in downtrend:
├─ Signal: Strong bearish momentum
├─ Warning: Oversold, potential bounce
└─ Trading: Short or wait for reversal
```

**Detection:**
```python
def detect_gap_cluster(gaps, lookback_days=30):
    """
    Detect gap cluster pattern
    
    Returns:
    - Gap cluster info if found
    - Momentum assessment
    - Trading recommendation
    """
    recent_gaps = [g for g in gaps if g['days_ago'] <= lookback_days]
    
    upward_gaps = [g for g in recent_gaps if g['direction'] == 'up' and not g['is_filled']]
    downward_gaps = [g for g in recent_gaps if g['direction'] == 'down' and not g['is_filled']]
    
    if len(upward_gaps) >= 3:
        return {
            'pattern': 'GAP_CLUSTER_BULLISH',
            'gap_count': len(upward_gaps),
            'gaps': upward_gaps,
            'signal': 'STRONG_MOMENTUM',
            'warning': 'Extended - watch for exhaustion gap',
            'recommendation': 'Ride trend with trailing stop'
        }
    elif len(downward_gaps) >= 3:
        return {
            'pattern': 'GAP_CLUSTER_BEARISH',
            'gap_count': len(downward_gaps),
            'gaps': downward_gaps,
            'signal': 'STRONG_DOWNTREND',
            'warning': 'Oversold - potential capitulation',
            'recommendation': 'Wait for stabilization before buying'
        }
    
    return None
```

---

### Precise Gap Entry Zones (精确缺口入场区)

**Problem:** "Buy near the gap" is too vague. Need precise entry zones.

```python
def calculate_gap_entry_zone(gap, risk_tolerance, market_conditions):
    """
    Calculate precise entry zone for gap pullback trade
    
    Risk Tolerance:
    - CONSERVATIVE: Wait for deeper pullback, higher probability but may miss
    - MODERATE: Balance between fill probability and opportunity
    - AGGRESSIVE: Enter early, higher risk but catch more moves
    """
    gap_bottom = min(gap['gap_zone'])
    gap_top = max(gap['gap_zone'])
    gap_mid = (gap_bottom + gap_top) / 2
    gap_size = gap_top - gap_bottom
    
    if risk_tolerance == 'CONSERVATIVE':
        # Wait for gap to nearly fill (80-100% fill)
        entry_zone = (gap_bottom * 0.98, gap_bottom * 1.02)
        stop_loss = gap_bottom * 0.97
        probability_of_reaching = 0.30
        risk_reward = 4.0
        
    elif risk_tolerance == 'MODERATE':
        # Enter at gap midpoint (50% fill)
        entry_zone = (gap_mid * 0.98, gap_mid * 1.02)
        stop_loss = gap_bottom * 0.97
        probability_of_reaching = 0.50
        risk_reward = 3.0
        
    else:  # AGGRESSIVE
        # Enter at gap top (immediate support)
        entry_zone = (gap_top * 0.98, gap_top * 1.02)
        stop_loss = gap_mid * 0.97
        probability_of_reaching = 0.70
        risk_reward = 2.0
    
    # Adjust for gap type
    if gap['type'] == 'breakaway':
        # Breakaway gaps - stronger support, can be more aggressive
        stop_loss *= 0.98  # Slightly tighter stop
        probability_of_reaching *= 0.8  # Less likely to fill deep
    elif gap['type'] == 'exhaustion':
        # Exhaustion gaps - likely to fill, be conservative
        probability_of_reaching *= 1.3  # More likely to fill
    
    return {
        'entry_zone': entry_zone,
        'entry_price_target': (entry_zone[0] + entry_zone[1]) / 2,
        'stop_loss': stop_loss,
        'probability_of_entry_trigger': probability_of_reaching,
        'risk_reward_ratio': risk_reward,
        'position_size_recommendation': calculate_position_size(
            entry_zone[1], stop_loss, risk_tolerance
        )
    }


def calculate_position_size(entry, stop_loss, risk_tolerance):
    """
    Calculate recommended position size based on risk
    """
    risk_pct = abs(entry - stop_loss) / entry
    
    # Risk per trade based on tolerance
    risk_per_trade = {
        'CONSERVATIVE': 0.01,  # 1% of portfolio
        'MODERATE': 0.02,      # 2% of portfolio
        'AGGRESSIVE': 0.03     # 3% of portfolio
    }
    
    max_loss_pct = risk_per_trade.get(risk_tolerance, 0.02)
    position_size_pct = max_loss_pct / risk_pct
    
    return min(position_size_pct, 0.15)  # Cap at 15%
```

---

### Gap Trend Phase Analysis (缺口趋势阶段分析)

**More Accurate Gap Classification:**

```python
def classify_gap_by_trend_phase(gap, kline_data, gap_index):
    """
    Classify gap based on trend phase (Wyckoff-inspired)
    
    Trend Phases:
    1. ACCUMULATION: Bottoming process
    2. MARKUP: Bull trend
    3. DISTRIBUTION: Topping process
    4. MARKDOWN: Bear trend
    """
    # Analyze price action before gap
    lookback = min(30, gap_index)
    prior_data = kline_data[gap_index - lookback:gap_index]
    
    # Identify trend phase
    phase = identify_trend_phase(prior_data)
    
    # Volume analysis
    avg_vol = sum([c['volume'] for c in prior_data]) / len(prior_data)
    gap_vol = kline_data[gap_index]['volume']
    vol_ratio = gap_vol / avg_vol
    
    # Classify based on phase and volume
    if phase == 'ACCUMULATION':
        if vol_ratio > 1.5:
            return 'BREAKAWAY_START'  # Trend initiation
        else:
            return 'ACCUMULATION_GAP'  # Within base
            
    elif phase == 'MARKUP':
        if vol_ratio > 1.3:
            # Check if late in trend
            rally_extent = calculate_rally_extent(prior_data)
            if rally_extent > 0.50:  # 50%+ rally
                return 'EXHAUSTION'
            else:
                return 'RUNAWAY'
        else:
            return 'MEASURING_GAP'
            
    elif phase == 'DISTRIBUTION':
        return 'BREAKAWAY_REVERSAL'  # Potential trend change
        
    else:  # MARKDOWN
        if vol_ratio > 1.5:
            return 'BREAKAWAY_DOWN'
        else:
            return 'CONTINUATION_DOWN'


def identify_trend_phase(kline_data):
    """
    Identify current trend phase using Wyckoff method
    """
    if len(kline_data) < 20:
        return 'UNKNOWN'
    
    # Calculate price metrics
    highs = [c['high'] for c in kline_data]
    lows = [c['low'] for c in kline_data]
    closes = [c['close'] for c in kline_data]
    
    # Trend direction
    start_price = closes[0]
    end_price = closes[-1]
    price_change = (end_price - start_price) / start_price
    
    # Volatility (range expansion/contraction)
    ranges = [h - l for h, l in zip(highs, lows)]
    recent_ranges = ranges[-10:]
    prior_ranges = ranges[:10]
    
    range_expansion = sum(recent_ranges) / sum(prior_ranges) if sum(prior_ranges) > 0 else 1
    
    # Volume trend
    # (Would need volume data)
    
    # Phase determination
    if price_change > 0.20 and range_expansion > 1.2:
        return 'MARKUP'
    elif price_change < -0.20 and range_expansion > 1.2:
        return 'MARKDOWN'
    elif abs(price_change) < 0.10 and range_expansion < 1.0:
        # Low volatility, range-bound
        if end_price < sum(closes) / len(closes):
            return 'ACCUMULATION'
        else:
            return 'DISTRIBUTION'
    else:
        return 'TRANSITION'
```

---

### Gap Confluence Score (缺口共振评分)

**Measure strength when multiple gaps align:**

```python
def calculate_gap_confluence_score(gaps, current_price):
    """
    Calculate confluence score when multiple gaps support same level
    
    Higher score = Stronger support/resistance
    """
    unfilled_gaps = [g for g in gaps if not g['is_filled']]
    
    # Separate by position relative to current price
    support_gaps = [g for g in unfilled_gaps if g['direction'] == 'up' and g['gap_zone'][1] < current_price]
    resistance_gaps = [g for g in unfilled_gaps if g['direction'] == 'down' and g['gap_zone'][0] > current_price]
    
    score = 0
    factors = []
    
    # Support confluence
    if len(support_gaps) >= 2:
        # Check if gaps overlap
        support_zones = [g['gap_zone'] for g in support_gaps]
        overlap = calculate_overlap(support_zones)
        
        if overlap > 0.5:  # Significant overlap
            score += 3
            factors.append(f"Strong support confluence: {len(support_gaps)} gaps overlap")
        elif len(support_gaps) >= 3:
            score += 2
            factors.append(f"Multiple support gaps: {len(support_gaps)} gaps")
    
    # Resistance confluence
    if len(resistance_gaps) >= 2:
        resistance_zones = [g['gap_zone'] for g in resistance_gaps]
        overlap = calculate_overlap(resistance_zones)
        
        if overlap > 0.5:
            score += 3
            factors.append(f"Strong resistance confluence: {len(resistance_gaps)} gaps overlap")
        elif len(resistance_gaps) >= 3:
            score += 2
            factors.append(f"Multiple resistance gaps: {len(resistance_gaps)} gaps")
    
    # Nearest gap bonus
    nearest_gap = find_nearest_gap(unfilled_gaps, current_price)
    if nearest_gap:
        distance = calculate_distance_to_gap(current_price, nearest_gap)
        if distance < 0.02:  # Within 2%
            score += 2
            factors.append("Price at gap zone")
        elif distance < 0.05:
            score += 1
            factors.append("Price near gap zone")
    
    return {
        'confluence_score': min(score, 10),
        'factors': factors,
        'support_count': len(support_gaps),
        'resistance_count': len(resistance_gaps),
        'interpretation': interpret_confluence(score)
    }


def interpret_confluence(score):
    if score >= 7:
        return "VERY STRONG level - High probability support/resistance"
    elif score >= 5:
        return "STRONG level - Good support/resistance"
    elif score >= 3:
        return "MODERATE level - Decent support/resistance"
    else:
        return "WEAK level - Minor support/resistance"
```

---

## Key Takeaways (高级要点)

1. **Dynamic Fill Probability** - Not all gaps are equal; context matters
2. **Trend Phase Analysis** - Gaps have different meanings in different phases
3. **Gap Clusters** - Multiple gaps = stronger signal
4. **Island Reversals** - Very powerful reversal patterns
5. **Precise Entry Zones** - Don't just "buy near the gap"
6. **Confluence Scoring** - Multiple gaps at same level = very strong
