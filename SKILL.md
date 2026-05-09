---
name: stock-analysis
description: 'Comprehensive stock portfolio analyzer with watchlist. TRIGGER on ANY of: (1) watchlist analysis — "分析自选股" / "analyze watchlist" / "my watchlist"; (2) portfolio analysis requests in any language — "分析我的持仓" / "portfolio analysis" / "stock review"; (3) market sentiment queries — "大盘情绪" / "market outlook"; (4) gap analysis — "缺口分析" / "support/resistance levels"; (5) position sizing — "仓位建议" / "should I buy/sell". Watchlist is defined in references/watchlist.json. Integrates market sentiment, technical analysis (gap theory), valuation, and position management strategies.'
---

# Stock Portfolio Analyzer

**Investment Philosophy: Value Investing (价值投资)**

We do NOT predict stock prices (speculation). Instead, we:
1. **Assess Core Value** — What is the stock actually worth?
2. **Measure Price Deviation** — How far is price from core value?
3. **Decide: Wait or Get On Board** — Is there a margin of safety?

**Data Source:** Longbridge CLI (real-time quotes, positions, news)

---

## Quick Commands

### 🎯 Analyze My Watchlist (固定自选股分析)

**Trigger:** "分析自选股" / "analyze watchlist" / "我的自选股"

**Fixed Watchlist:**
> See [references/watchlist.json](references/watchlist.json) for the authoritative watchlist definition.
> Use `from watchlist_utils import load_watchlist` in Python, or the shell command below to get current symbols.
>
> ```bash
> python3 -c "from watchlist_utils import load_watchlist; print(' '.join(load_watchlist()))"
> ```

**Quick Analysis Workflow:**

1. **Get Market Sentiment** (30 seconds)
```bash
longbridge market-temp
longbridge quote .^GSPC.US .^DJI.US .^IXIC.US
```

2. **Batch Fetch Quotes** (parallel execution, ~1 minute)
```bash
# Load symbols from watchlist.json at runtime
WATCHLIST=$(python3 -c "from watchlist_utils import load_watchlist; print(' '.join(load_watchlist()))")
longbridge quote $WATCHLIST
```

3. **Get News for Each Symbol** (parallel, ~2 minutes)
```bash
# Load symbols and fetch news for each
for SYMBOL in $(python3 -c "from watchlist_utils import load_watchlist; print(' '.join(load_watchlist()))"); do
  longbridge news $SYMBOL &
done
wait
```

4. **Generate Summary Report:**
   - Price action for each stock
   - Key support/resistance levels
   - Recent catalysts
   - Buy/Hold/Sell recommendation

**Output Format:**
```markdown
# 📊 自选股快速分析报告
日期: YYYY-MM-DD

## 市场概况
- 情绪指数: XX
- 主要指数: S&P 500 +X%, NASDAQ +X%

## 自选股概览
| 股票 | 价格 | 涨跌 | 成交量 | 区间 | 建议 | 评分 |
|------|------|------|--------|------|------|------|
| BABA.US | $141.01 | +1.7% | 12.8M | 支撑区 | 买入 | 8/10 |
| NVDA.US | $XXX | +X% | XXM | XXX | XXX | X/10 |
| ... | ... | ... | ... | ... | ... | ... |

## 详细分析

### BABA.US - 阿里巴巴
**价格状态:** $141.01 (+1.7%)
- 52周区间: $XXX - $XXX
- 成交量: 12.8M (高于/低于均值)

**技术面:**
- 支撑: $XXX
- 阻力: $XXX
- 缺口: [缺口分析]

**催化剂:**
- [最新新闻1]
- [最新新闻2]

**建议:** BUY/HOLD/SELL
- 理由: [2-3句话]
- 入场价: $XXX
- 止损: $XXX
- 目标价: $XXX

---

[重复其他股票]
```

---

## Core Workflow

When the user requests portfolio analysis, follow this 5-step process:

### Step 1: Multi-Factor Market Sentiment Analysis 🎯

**CRITICAL:** Never rely on a single indicator. Market sentiment must be assessed using multiple factors across 5 dimensions.

**Reference:** See [references/multi-factor-sentiment.md](references/multi-factor-sentiment.md) for detailed methodology.

#### Step 1.1: Gather Data from All Dimensions

**Dimension 1: Sentiment Indicators**
```bash
# Primary sentiment data
longbridge market-temp

# Volatility index (VIXM = VIX Mid-Term Futures ETF)
longbridge quote VIXM.US
```

**Dimension 2: Technical Indicators**
```bash
# Major indices
longbridge quote SPY.US QQQ.US

# Check if at all-time highs
longbridge kline history SPY.US --start 2025-01-01 --period week
```

**Dimension 3: Valuation Metrics**
```bash
# Market valuation
longbridge valuation SPY.US

# P/E ratios
longbridge calc-index SPY.US
```

**Dimension 4: Market Breadth & Flows**
```bash
# Capital flows
longbridge capital --flow

# Market status
longbridge market-status
```

#### Step 1.2: Calculate Comprehensive Market Score

**Formula:**
```python
comprehensive_score = (
    sentiment_dimension_score * 0.30 +   # Sentiment indicators
    technical_dimension_score * 0.25 +   # Technical analysis
    valuation_dimension_score * 0.25 +   # Valuation metrics
    macro_dimension_score * 0.10 +       # Macro environment
    flow_dimension_score * 0.10          # Capital flows
)
```

**Key Indicators to Check:**

| Indicator | Command | Critical Values |
|-----------|---------|-----------------|
| **Longbridge Sentiment** | `market-temp → Sentiment` | <30: Fear, >70: Greed |
| **Longbridge Temperature** | `market-temp → Temperature` | >70: Overheated |
| **Longbridge Valuation** | `market-temp → Valuation` | **>85: DANGER** ⚠️ |
| **VIXM** | `quote VIXM.US` | <15: Complacent, >30: Fearful |
| **SPY** | `quote SPY.US` | ATH? Overbought if >20% from 52w low |
| **QQQ** | `quote QQQ.US` | ATH? Tech overvaluation risk |

#### Step 1.3: Detect Divergences ⚠️

**Critical Warning Signs:**

1. **Valuation-Sentiment Divergence:**
   - Valuation > 85 BUT Sentiment < 60
   - **Interpretation:** Distribution phase, institutions exiting
   - **Action:** Cap position at 30-35% regardless of sentiment

2. **Technical-Sentiment Divergence:**
   - SPY/QQQ at all-time high BUT Sentiment < 60
   - **Interpretation:** Late-stage rally, smart money selling
   - **Action:** Reduce position, wait for pullback
3. **VIXM-Sentiment Divergence:**

   - VIXM < 15 (complacent) BUT Sentiment neutral
   - **Interpretation:** Hidden risk, potential spike
   - **Action:** Increase cash reserve

#### Step 1.4: Classify Market State

**Based on Comprehensive Score:**

| Score Range | Market State | Target Position | Action |
|-------------|--------------|-----------------|--------|
| **80-100** | Extreme Greed | 10-25% | 🔴 Aggressive Sell |
| **70-80** | Greed | 25-40% | 🟡 Selective Sell |
| **60-70** | Neutral-Bullish | 40-55% | 🟡 Hold |
| **40-60** | Neutral | 50-65% | ⚪ Hold/Selective Buy |
| **30-40** | Fear | 65-80% | 🟢 Selective Buy |
| **0-30** | Extreme Fear | 80-95% | 🟢 Aggressive Buy |

#### Step 1.5: Apply Position Caps

**CRITICAL RULES:**

```python
def comprehensive_score_to_position(comprehensive_score):
    """
    Map 5-dimension comprehensive score to base target position %.
    This is the single source of truth for score→position mapping.
    """
    if comprehensive_score >= 80:
        return 17.5    # Extreme Greed: midpoint of 10-25%
    elif comprehensive_score >= 70:
        return 32.5    # Greed: midpoint of 25-40%
    elif comprehensive_score >= 60:
        return 47.5    # Neutral-Bullish: midpoint of 40-55%
    elif comprehensive_score >= 40:
        return 57.5    # Neutral: midpoint of 50-65%
    elif comprehensive_score >= 30:
        return 72.5    # Fear: midpoint of 65-80%
    else:
        return 87.5    # Extreme Fear: midpoint of 80-95% (hard cap 95%)

def apply_position_caps(comprehensive_score, valuation, is_ath):
    """
    Apply hard position caps based on risk factors
    """
    base_position = comprehensive_score_to_position(comprehensive_score)
    
    # Cap 1: Valuation cap (MOST IMPORTANT)
    if valuation > 90:
        capped_position = min(base_position, 25)  # Max 25%
        warning = "EXTREME_VALUATION_RISK"
    elif valuation > 85:
        capped_position = min(base_position, 35)  # Max 35%
        warning = "HIGH_VALUATION_RISK"
    elif valuation > 75:
        capped_position = min(base_position, 50)  # Max 50%
        warning = "ELEVATED_VALUATION"
    else:
        capped_position = base_position
        warning = None
    
    # Cap 2: All-time high cap
    if is_ath:
        capped_position = min(capped_position, capped_position * 0.85)
        # Reduce by 15% when at ATH
    
    return capped_position, warning
```

**Example Calculation (Current Market):**

```
Data Collected:
├─ Longbridge Sentiment: 48
├─ Longbridge Temperature: 69
├─ Longbridge Valuation: 90 ⚠️
├─ VIXM: ~15 (low)
├─ SPY: $710.14 (All-time high) ⚠️
└─ QQQ: $648.85 (All-time high) ⚠️

Dimension Scores:
├─ Sentiment: 59.6 (weighted)
├─ Technical: 72.5 (overbought)
├─ Valuation: 85.0 (extreme) ⚠️
├─ Macro: 65.0 (neutral)
└─ Flow: 55.0 (neutral)

Comprehensive Score: 68.03 → GREED

Base Position (Score=68): 40%

Apply Caps:
├─ Valuation=90 → Cap at 25% ⚠️
├─ ATH detected → Reduce to 21%
└─ Final Position: 21%

RECOMMENDATION: Position = 20-25%, Cash = 75-80%
```

#### Step 1.6: Generate Market Report

**Template Output:**

```markdown
## 🎯 Multi-Factor Market Analysis

### Market State: GREED (Score: 68/100)

### Dimension Breakdown:
| Dimension | Score | Status | Weight |
|-----------|-------|--------|--------|
| Sentiment | 59.6 | Neutral | 30% |
| Technical | 72.5 | Overbought ⚠️ | 25% |
| Valuation | 85.0 | **Extreme** 🔴 | 25% |
| Macro | 65.0 | Neutral | 10% |
| Flow | 55.0 | Neutral | 10% |

### ⚠️ Critical Warnings:

1. **VALUATION EXTREME:** Valuation=90, historical top territory
2. **ALL-TIME HIGHS:** SPY/QQQ at ATH, momentum exhaustion risk
3. **DIVERGENCE:** Valuation extreme but sentiment neutral
   → Classic distribution phase, institutional selling

### Recommended Position:
- **Target Position:** 20-25% (NOT 40%)
- **Cash Reserve:** 75-80%
- **Action:** SELECTIVE_SELL / WAIT
- **Urgency:** MEDIUM

### Position Caps Applied:
- ✅ Valuation cap: 90 > 85 → Max 35%
- ✅ ATH cap: All-time high → Reduce 15%
- ✅ Final cap: 25% → **Recommended: 20-25%**
```

---

### Step 2: Business Quality Analysis 🏰

**NEW:** Before analyzing individual stocks, assess business quality. This determines:
- Whether to invest at all
- How much to pay (safety margin)
- Position sizing

**Reference:** 
- [references/moat-analysis.md](references/moat-analysis.md) - Economic moat analysis
- [references/roic-analysis.md](references/roic-analysis.md) - Capital efficiency analysis

#### Step 2.1: Moat Analysis (护城河分析)

**Five Types of Economic Moats:**

1. **Brand Moat** (品牌护城河) - Premium pricing power
2. **Network Effect Moat** (网络效应) - Value increases with users
3. **Switching Cost Moat** (转换成本) - High cost to switch
4. **Cost Advantage Moat** (成本优势) - Low-cost producer
5. **Regulatory Moat** (监管壁垒) - Licenses, patents, regulations

**Moat Scoring (0-10):**
| Score | Moat Width | Required Margin |
|-------|------------|-----------------|
| 7-10 | Wide Moat | 0-10% discount |
| 5-7 | Narrow Moat | 20% discount |
| 3-5 | Minimal Moat | 35% discount |
| 0-3 | No Moat | AVOID |

**Data Sources:**
```bash
# Financial data for moat analysis
longbridge quote SYMBOL.US
longbridge kline history SYMBOL.US --start $(date -v-365d +%Y-%m-%d) --period day
```

#### Step 2.2: ROIC Analysis (资本效率分析)

**ROIC Formula:**
```
ROIC = NOPAT / Invested Capital
NOPAT = Operating Income × (1 - Tax Rate)
Invested Capital = Equity + Debt - Cash
```

**ROIC Quality Scale:**
| ROIC | Quality | Interpretation |
|------|---------|----------------|
| >25% | Exceptional | Buffett-level business |
| 20-25% | Excellent | Great business |
| 15-20% | Good | Solid business |
| 10-15% | Average | Mediocre business |
| <10% | Poor | Avoid or deep discount |
| <WACC | Value Destruction | AVOID |

**Value Creation Test:**
```
If ROIC > WACC → Creating value (good)
If ROIC < WACC → Destroying value (bad - likely value trap)
```

#### Step 2.3: Quality Score Calculation

```python
def calculate_quality_score(moat_score, roic, roic_trend):
    """
    Combined quality score determines investment worthiness
    """
    # Weight: Moat 60%, ROIC 40%
    quality_score = moat_score * 0.6 + roic_score * 0.4
    
    # Adjust for trend
    if roic_trend == 'DECLINING':
        quality_score -= 1
    elif roic_trend == 'IMPROVING':
        quality_score += 0.5
    
    return quality_score
```

**Quality Score Impact:**
| Quality Score | Investment Action | Position Size |
|---------------|-------------------|---------------|
| 8-10 | Buy at fair price | Can be larger |
| 6-8 | Buy with discount | Standard |
| 4-6 | Deep discount required | Small only |
| <4 | Avoid | N/A |

---

### Step 3: Value Trap Detection 🚨

**CRITICAL:** Cheap stocks are often cheap for a reason. Before recommending any "undervalued" stock, run value trap detection.

**Reference:** [references/value-trap-detection.md](references/value-trap-detection.md)

#### Step 3.1: Value Trap Warning Signs

**Category 1: Fundamental Deterioration**
- ROIC < WACC (value destruction)
- Negative free cash flow trend
- Debt growing faster than revenue

**Category 2: Earnings Quality Issues**
- AR growing faster than revenue (channel stuffing)
- High accruals (>20% of assets)
- One-time gains masking weakness

**Category 3: Structural Issues**
- Industry in structural decline
- Commodity business without cost advantage
- Regulatory headwinds

**Category 4: Market Signals**
- Heavy insider selling
- High short interest (>15%)
- Unsustainable dividend (>8% yield)

#### Step 3.2: Value Trap Score

```python
def calculate_trap_score(symbol, financials, market_data):
    """
    Trap Score 0-100 (higher = more likely a trap)
    """
    trap_score = 0
    
    # ROIC < WACC
    if roic < wacc:
        trap_score += 25
    
    # Negative FCF
    if fcf_negative_2_of_3_years:
        trap_score += 15
    
    # Debt issues
    if debt_to_ebitda > 5:
        trap_score += 15
    
    # AR vs Revenue
    if ar_growth > revenue_growth * 1.5:
        trap_score += 15
    
    # Industry decline
    if industry_cagr < -3%:
        trap_score += 15
    
    # Insider selling
    if insider_selling_heavy:
        trap_score += 10
    
    return trap_score
```

**Trap Score Interpretation:**
| Trap Score | Risk Level | Action |
|------------|------------|--------|
| 0-15 | LOW | OK - Standard analysis |
| 15-30 | MEDIUM | Caution - Require extra margin |
| 30-50 | HIGH | Avoid or minimal position |
| 50+ | CRITICAL | AVOID |

---

### Step 4: Watchlist Analysis

**Fixed Watchlist (自选股列表):**

This skill maintains a watchlist defined in [references/watchlist.json](references/watchlist.json).
Load symbols at runtime:

```bash
python3 -c "from watchlist_utils import load_watchlist; print(' '.join(load_watchlist()))"
```

**Data Collection:**

For each symbol in watchlist, fetch:

```bash
# Parallel execution for efficiency
WATCHLIST=$(python3 -c "from watchlist_utils import load_watchlist; print(' '.join(load_watchlist()))")
longbridge quote $WATCHLIST

# Individual analysis (can be parallel, example for one symbol)
longbridge quote BABA.US
longbridge kline history BABA.US --start $(date -v-60d +%Y-%m-%d) --end $(date +%Y-%m-%d) --period day
longbridge intraday BABA.US
longbridge news BABA.US
```

**Also check user's actual positions:**

```bash
longbridge positions --format json
longbridge portfolio
```

If user holds stocks not in watchlist, add them to analysis.

**NEW: Integrated Analysis per symbol:**

1. **Quality Assessment:**
   - Moat score (0-10)
   - ROIC and ROIC trend
   - Quality score

2. **Value Trap Check:**
   - Trap score (0-100)
   - Warning signs identified

3. **Price Analysis:**
   - Current price & change %
   - 52-week high/low position
   - Volume vs 20-day average

4. **Technical Setup:**
   - Gap analysis (see Step 6)
   - Support/resistance levels

5. **Recommendation:**
   - Quality-adjusted score (1-10)
   - Action: BUY/HOLD/SELL/AVOID

---

### Step 5: Position Analysis (Value Zones)

Analyze current holdings in detail:

```bash
longbridge positions --format json
longbridge portfolio                # P/L, asset distribution
```

For each holding, determine:

**A. Price Zone Analysis** (see [references/value-zone.md](references/value-zone.md)):
```bash
# Get 90-day K-line data
longbridge kline history SYMBOL.US --start $(date -v-90d +%Y-%m-%d) --end $(date +%Y-%m-%d) --period day --format json
```

Calculate:
- **Support Zone:** Price levels with highest volume clusters (volume profile)
- **Resistance Zone:** Recent swing highs, gap resistance
- **Fair Value Zone:** 20-day and 50-day moving averages convergence area
- **Current Position:** Where is price relative to these zones?

**B. Quality-Adjusted Safety Margin** 🆕:

**Reference:** [references/value-zone.md](references/value-zone.md) - Quality-Adjusted Safety Margin section

```python
def calculate_buy_price(fair_value, moat_score, roic):
    """
    Calculate buy price based on quality-adjusted margin
    
    Higher quality = Lower required margin
    """
    # Get required margin based on quality
    margin = calculate_required_safety_margin(moat_score, roic)
    
    if margin is None:
        return None  # Avoid - no moat
    
    buy_price = fair_value * (1 - margin)
    return buy_price
```

**Example:**
```
Stock: NVDA
├─ Fair Value (DCF): $600
├─ Moat Score: 8/10 (Wide moat)
├─ ROIC: 42% (Exceptional)
├─ Required Margin: 5% (reduced for high ROIC)
├─ Buy Price: $600 × 95% = $570
└─ Current Price: $550 → UNDERVALUED ✅
```

**C. Valuation Metrics:**
```bash
# Use Python SDK for detailed financials if available
# Or parse from longbridge quote output
```

Key metrics:
- P/E ratio vs sector average
- P/B ratio
- EPS growth trend
- Revenue growth

**D. Position Health:**
- Unrealized P/L %
- Days held
- Risk level (volatility)

---

### Step 6: Gap Theory Analysis

Identify and analyze price gaps for all symbols.

**Gap Definition:** Price jump ≥ 1% between consecutive trading days.

**Gap Types:**
1. **Breakaway Gap** — At start of new trend (volume surge)
2. **Runaway Gap** — Mid-trend continuation
3. **Exhaustion Gap** — Near trend end (reversal signal)
4. **Common Gap** — Fills quickly, no trend significance

**Gap Detection Algorithm:**

```bash
# Get daily K-line data (at least 60 days for pattern recognition)
longbridge kline history SYMBOL.US --start $(date -v-60d +%Y-%m-%d) --end $(date +%Y-%m-%d) --period day --format json
```

**🆕 Advanced Gap Analysis:**

**Reference:** [references/gap-theory.md](references/gap-theory.md) - Advanced Gap Analysis section

1. **Dynamic Fill Probability** - Not fixed, depends on:
   - Gap type, age, size
   - Market trend
   - Test count

2. **Multi-Gap Patterns:**
   - Island Reversal (very strong reversal signal)
   - Gap Clusters (momentum indicator)

3. **Precise Entry Zones:**
   - Conservative: Wait for deep pullback
   - Moderate: Gap midpoint
   - Aggressive: Gap top

**Gap Trading Rules:**
- **Unfilled gaps act as support/resistance**
- **Upward gaps below price → Support**
- **Downward gaps above price → Resistance**
- **Common gaps fill within 3-5 days**
- **Breakaway gaps rarely fill**

For each symbol, output:
- List of significant gaps (last 60 days)
- Nearest unfilled gap (support/resistance)
- Distance to gap in %
- **Dynamic fill probability** 🆕
- **Precise entry zone** 🆕

See detailed gap theory in [references/gap-theory.md](references/gap-theory.md).

---

### Step 7: Strategy Conflict Resolution 🆕

When different analysis frameworks give conflicting signals, use systematic resolution.

**Reference:** [references/conflict-resolution.md](references/conflict-resolution.md)

#### Common Conflicts:

1. **Value Zone vs Gap Analysis**
   - Value says buy, Gap says wait
   - Resolution depends on investment horizon

2. **Moat Quality vs Valuation**
   - Great company, expensive price
   - Wide moat can justify some premium

3. **Market Sentiment vs Stock Signal**
   - Market risky, stock looks good
   - Market regime trumps individual stock

4. **ROIC vs Current Earnings**
   - High ROIC, weak recent earnings
   - ROIC is structural, earnings cyclical

#### Priority Hierarchy:

```
1. MARKET REGIME (Most Important)
   └─ Market conditions trump everything

2. BUSINESS QUALITY (ROIC + Moat)
   └─ Structural quality beats short-term noise

3. VALUATION
   └─ Price matters, but quality justifies premium

4. TECHNICAL (Gaps, Support/Resistance)
   └─ Timing tool, not primary decision maker

5. SHORT-TERM NOISE (Least Important)
   └─ Earnings misses, headlines
```

#### Resolution Example:

```
Conflict:
├─ Market: GREED (reduce risk)
├─ Stock Score: 9/10 (strong buy)
├─ Valuation: Fair price
└─ Gap: Near support

Resolution:
├─ Priority: Market regime first
├─ Limit new positions due to market risk
├─ But exceptional stock quality allows small position
└─ Action: BUY_SMALL (3% position max)
```

---

### Step 8: Dynamic Position Management Recommendations

**CRITICAL:** Total portfolio position is DYNAMIC, not fixed. Adjust based on market sentiment.

**Reference:** See [references/market-regime.md](references/market-regime.md) for detailed regime analysis.

#### Step 5.1: Determine Market Regime

```bash
longbridge market-temp
```

**Extract sentiment index and determine regime:**

| Score Range | Market State | Target Total Position | Target Cash | Action |
|-------------|--------------|-----------------------|-------------|--------|
| **80-100** | Extreme Greed | 10-25% | 75-90% | 🔴 Aggressive Sell |
| **70-80** | Greed | 25-40% | 60-75% | 🟡 Selective Sell |
| **60-70** | Neutral-Bullish | 40-55% | 45-60% | 🟡 Hold |
| **40-60** | Neutral | 50-65% | 35-50% | ⚪ Hold/Selective Buy |
| **30-40** | Fear | 65-80% | 20-35% | 🟢 Selective Buy |
| **0-30** | Extreme Fear | 80-95% | 5-20% | 🟢 Aggressive Buy |

> **Note:** This table is aligned with Step 1.4 (the authoritative source). Hard cap at 95% maximum position, 5% minimum cash reserve. The `comprehensive_score_to_position()` function in the engine implements these midpoints.

#### Step 5.2: Calculate Target Position

```python
# Example: Sentiment = 48 (Neutral)
sentiment = 48
target_position_pct = 60  # Neutral market
target_cash_pct = 40

# Compare with current position
current_position_pct = (market_value / total_assets) * 100
current_cash_pct = (total_cash / total_assets) * 100

# Calculate adjustment needed
position_diff = current_position_pct - target_position_pct
```

**Example Analysis:**
```
Market Sentiment: 48 (Neutral)
Portfolio Value: $157,220
Current Holdings: $125,776 (80%)
Current Cash: $31,444 (20%)

Target Position: 60% ($94,332)
Target Cash: 40% ($62,888)

Adjustment Needed:
- Reduce position by: 80% - 60% = 20%
- Amount to sell: $157,220 × 20% = $31,444
- Action: SELL
- Urgency: MEDIUM (position_diff = 20%)
```

#### Step 5.3: Select Stocks for Adjustment

**If Need to SELL (Position too high):**

Priority order:
1. **Sell lowest conviction stocks first** (lowest score)
2. **Sell stocks near resistance** (within 5%)
3. **Sell stocks with negative catalysts**
4. **Sell stocks with unfilled downward gaps above price**
5. **Trim oversized positions** (>15% of portfolio)

**If Need to BUY (Position too low):**

Priority order:
1. **Buy highest conviction stocks** (highest score)
2. **Buy stocks near support** (within 5%)
3. **Buy stocks with positive catalysts**
4. **Buy stocks with unfilled upward gaps below price**
5. **Add to underweight positions** (<5% of portfolio)

#### Step 5.4: Individual Stock Sizing

**Maximum Position Size (Hard Limits):**
- Single stock: ≤ 15% of portfolio
- Sector concentration: ≤ 30% of portfolio
- **Note:** These limits apply within the dynamic total position

**Individual Stock Allocation Formula:**

```
Individual Stock Position = (Target Total Position × Individual Weight)

Where:
- Target Total Position = Based on market sentiment (from Step 5.1)
- Individual Weight = Stock score / Sum of all scores

Example:
- Target Total Position: 60% (Neutral market)
- Portfolio Value: $157,220
- Total investable: $94,332

Stock Scores:
- CEG.US: 9/10 (highest priority)
- TSLA.US: 8/10
- BABA.US: 8/10
- NVDA.US: 7/10
- PLTR.US: 6/10
- COIN.US: 3/10

Total Score: 9 + 8 + 8 + 7 + 6 + 3 = 41

Individual Allocations:
- CEG.US: (9/41) × $94,332 = $20,705 (13.2%)
- TSLA.US: (8/41) × $94,332 = $18,407 (11.7%)
- BABA.US: (8/41) × $94,332 = $18,407 (11.7%)
- NVDA.US: (7/41) × $94,332 = $16,106 (10.3%)
- PLTR.US: (6/41) × $94,332 = $13,807 (8.8%)
- COIN.US: (3/41) × $94,332 = $6,904 (4.4%) - or skip
```

#### Step 5.5: Generate Recommendations

**Template Output:**

```markdown
## Dynamic Position Management Report

### Market Regime Analysis
- Sentiment Index: 48 (Neutral)
- Target Total Position: 60%
- Target Cash: 40%

### Current vs Target
- Current Position: 80% ($125,776)
- Target Position: 60% ($94,332)
- **Adjustment Needed: SELL $31,444**

### Stock Selection for Adjustment

**Stocks to SELL (Priority Order):**

1. **COIN.US** (Score: 3/10)
   - Current: $202.56 (1.3% of portfolio)
   - Recommendation: SELL ALL
   - Reason: Lowest conviction, negative sentiment
   - Amount: $202.56

2. **NVDA.US** (Score: 7/10)
   - Current: Near resistance ($202)
   - Recommendation: REDUCE 50%
   - Reason: Near resistance, overvalued
   - Amount: $10,000 → $5,000

**Stocks to HOLD:**

3. **CEG.US** (Score: 9/10) ⭐
   - Current: 0% (not held)
   - Recommendation: BUY
   - Target: $20,705 (13.2%)
   - Reason: Highest conviction, AI infrastructure play

4. **TSLA.US** (Score: 8/10)
   - Current: 0% (not held)
   - Recommendation: BUY
   - Target: $18,407 (11.7%)
   - Reason: Strong momentum, breakout above $400

5. **BABA.US** (Score: 8/10)
   - Current: 0% (not held)
   - Recommendation: BUY
   - Target: $18,407 (11.7%)
   - Reason: AI catalyst, undervalued

### Execution Plan

**Day 1:**
- Sell COIN.US 1 share → +$202.56
- Reduce NVDA.US position → +$5,000

**Day 2:**
- Buy CEG.US ~70 shares → -$20,705
- Buy TSLA.US ~46 shares → -$18,407

**Day 3:**
- Buy BABA.US ~130 shares → -$18,407
- Monitor and adjust as needed

**Final Portfolio:**
- Cash: $62,888 (40%)
- CEG.US: $20,705 (13.2%)
- TSLA.US: $18,407 (11.7%)
- BABA.US: $18,407 (11.7%)
- NVDA.US: $5,000 (3.2%)
- Total Position: $62,519 (39.8%)
- Adjust to target: Increase position slightly to 60%
```

---

## Complete Analysis Example

When user asks: "分析我的持仓" or "Analyze my portfolio"

**Execute in order:**

```bash
# 1. Market Sentiment (CRITICAL - determines position sizing)
longbridge market-temp
longbridge quote SPY.US QQQ.US
longbridge news SPY.US

# 2. Get Holdings
longbridge positions --format json
longbridge portfolio

# 3. For each holding (parallel execution)
for SYMBOL in $(positions); do
  longbridge quote $SYMBOL
  longbridge kline history $SYMBOL --start $(date -v-90d +%Y-%m-%d) --end $(date +%Y-%m-%d) --period day --format json
  longbridge news $SYMBOL
done

# 4. Gap Analysis (process K-line data)
# 5. Generate Recommendations
```

---

## Output Format

### Detailed Report Structure

```markdown
# Portfolio Analysis Report
Date: YYYY-MM-DD HH:MM

## Market Overview
- Sentiment Index: XX (Interpretation)
- Major Indices: S&P 500 +X%, Dow +X%, NASDAQ +X%
- Key Catalysts: [Top 3 market-moving news]

## Holdings Summary
| Symbol | Shares | Value | P/L | Position % | Zone | Action |
|--------|--------|-------|-----|------------|------|--------|
| AAPL.US | 100 | $18,500 | +12% | 12.3% | Resistance | Reduce |
| TSLA.US | 50 | $12,000 | -5% | 8.0% | Support | Hold |
| ... | ... | ... | ... | ... | ... | ... |

## Detailed Analysis

### [SYMBOL.US]
**Current Status:**
- Price: $XXX.XX (+X.XX%)
- 52-Week Range: $XXX - $XXX
- Volume: X.XM (vs 20-day avg X.XM)

**Value Zone:**
- Support: $XXX - $XXX (volume cluster)
- Fair Value: $XXX (20/50 MA)
- Resistance: $XXX - $XXX

**Gap Analysis:**
- Nearest Unfilled Gap: $XXX (upward, support, X days ago)
- Distance: X.X%
- Gap Type: Breakaway
- Fill Probability: Low

**Valuation:**
- P/E: XX.X (sector avg: XX.X)
- P/B: X.X
- EPS Growth: +XX%

**News Catalysts:**
1. [Date] Headline...
2. [Date] Headline...

**Recommendation:**
- Action: BUY / HOLD / SELL / REDUCE
- Target Position: $XX,XXX (XX% of portfolio)
- Entry/Exit Points: $XXX
- Stop Loss: $XXX
- Rationale: [2-3 sentences]

---

## Portfolio-Level Recommendations

1. **Risk Assessment:**
   - Concentration Risk: High/Medium/Low
   - Sector Exposure: Tech XX%, Finance XX%, etc.
   - Cash Position: XX%

2. **Suggested Rebalancing:**
   - Sell: [SYMBOL] $X,XXX (reason)
   - Buy: [SYMBOL] $X,XXX (reason)
   - Keep Cash: $X,XXX (for opportunities)

3. **Watchlist Additions:**
   - [SYMBOL]: Near support, unfilled gap, positive catalyst
```

---

## Reference Files

### 🆕 Value Investing Framework
- **Moat Analysis** 🏰 — Economic moat scoring, 5 types of moats, quality-based margins: [references/moat-analysis.md](references/moat-analysis.md)
- **ROIC Analysis** 📊 — Capital efficiency, value creation test, ROIC vs WACC: [references/roic-analysis.md](references/roic-analysis.md)
- **Value Trap Detection** 🚨 — 4-category warning signs, trap score calculation: [references/value-trap-detection.md](references/value-trap-detection.md)

### Market & Sentiment
- **Multi-Factor Sentiment Analysis** 🎯 — comprehensive 5-dimension market analysis, divergence detection, position caps: [references/multi-factor-sentiment.md](references/multi-factor-sentiment.md)
- **Market Regime Analysis** — sentiment-based regime classification, dynamic position sizing: [references/market-regime.md](references/market-regime.md)

### Technical Analysis
- **Gap Theory** — Gap types, detection algorithm, 🆕 dynamic fill probability, 🆕 multi-gap patterns: [references/gap-theory.md](references/gap-theory.md)
- **Value Zone Analysis** — Support/resistance identification, volume profile, 🆕 quality-adjusted safety margin: [references/value-zone.md](references/value-zone.md)

### Decision Framework
- **Conflict Resolution** 🆕 — Systematic resolution when frameworks conflict, priority hierarchy: [references/conflict-resolution.md](references/conflict-resolution.md)
- **Position Management** — Dynamic sizing rules, risk management, rebalancing: [references/position-management.md](references/position-management.md)

---

## Voice Triggers

**Quick Watchlist Analysis:**
- "分析自选股" / "analyze watchlist" / "我的自选股" / "watchlist analysis"
- "check my watchlist" / "review watchlist"

**Full Portfolio Analysis:**
- "分析我的持仓" / "portfolio analysis" / "analyze my stocks"

**Market Sentiment:**
- "大盘怎么样" / "market sentiment" / "how's the market"

**Individual Stock Analysis:**
- "这个股票能买吗" / "should I buy [SYMBOL]" / "entry point for [SYMBOL]"

**Position Management:**
- "要不要减仓" / "position sizing" / "reduce position?"

**Technical Analysis:**
- "缺口在哪里" / "gap analysis" / "support and resistance"

---

## Configuration

User can customize parameters in the following YAML config files:

- **Analysis Engine:** `analysis/config.yaml` - risk weights, valuation weights, technical weights, factor strategies, moat thresholds, value trap detection
- **Harness:** `harness/config.yaml` - backtest thresholds, adjustment settings

### Position Sizing Configuration

Position sizing is configured in `analysis/config.yaml` under `overall.score_to_position`. The mapping matches Step 1.4 (the authoritative source). See the config file for exact values.

> **Note:** The old JSON config format at `~/.config/stock-analysis/config.json` and the inline `dynamic_position_sizing` JSON are deprecated and no longer used. All configuration is now in YAML format under `analysis/config.yaml` and `harness/config.yaml`.

**Customization:**
- Adjust `target_position_pct` based on risk tolerance
- Conservative: Reduce position percentages by 10-20%
- Aggressive: Increase position percentages by 10-20%

### Risk Management

```json
{
  "risk_management": {
    "min_absolute_cash": 5,
    "max_absolute_cash": 95,
    "emergency_reserve_pct": 5
  }
}
```

**Hard Limits:**
- **Always** keep at least 5% cash (emergency reserve)
- **Never** exceed 95% position (even in extreme fear)
- **Never** go below 5% position (even in extreme greed)

**Fixed Watchlist:**

The watchlist is defined in [references/watchlist.json](references/watchlist.json). To modify:

1. Edit the file directly
2. Add/remove symbols as needed
3. Update sector information

**Watchlist Structure:**
```json
{
  "symbol": "BABA.US",
  "name": "阿里巴巴",
  "sector": "Technology",
  "description": "中国电商和云计算巨头",
  "priority": 1  // 1 = high priority, 2 = medium, 3 = low
}
```

---

## 🎯 Daily Harness: Continuous Improvement System

**NEW:** The stock analysis skill now includes a harness system for daily review and continuous improvement. This system helps you:

1. **Daily Summary** - Generate end-of-day reports on watchlist performance
2. **Backtesting** - Compare predictions vs actual performance
3. **Metrics Adjustment** - Automatically adjust tracking metrics based on accuracy
4. **Continuous Learning** - Improve analysis methods over time

### Harness Components

```
stock-analysis/
├── harness/
│   ├── daily-summary.sh      # Generate daily reports
│   ├── backtest.py           # Compare predictions vs actual
│   ├── adjust-metrics.py     # Adjust tracking metrics
│   ├── harness-run.sh        # Main orchestrator script
│   └── config.yaml           # Configuration
└── data/
    ├── daily/                # Daily reports
    ├── predictions/          # Prediction files
    ├── backtests/           # Backtest results
    └── metrics/             # Performance metrics
```

### Quick Start

**Run full harness workflow:**
```bash
cd /Users/Jagger/.agents/skills/stock-analysis/harness
./harness-run.sh
```

**Run individual components:**
```bash
# Daily summary only (run at 9:00 AM Beijing Time)
./harness-run.sh --daily

# Backtest only (compare yesterday's predictions vs yesterday's actual at 9:30 AM Beijing Time)
./harness-run.sh --backtest

# Adjustment analysis only (suggest metric adjustments)
./harness-run.sh --adjust

# Generate report only
./harness-run.sh --report
```

### Daily Workflow (Beijing Time)

1. **9:00 AM Beijing Time (After US Market Close):**
   ```bash
   ./harness-run.sh --daily
   ```
   - Analyzes previous US trading day's market sentiment and performance
   - Records watchlist closing prices (US market already closed)
   - Saves predictions for next US trading day

2. **9:30 AM Beijing Time:**
   ```bash
   ./harness-run.sh --backtest
   ```
   - Compares yesterday's predictions vs yesterday's actual US market performance
   - Calculates accuracy metrics (price direction, target price)
   - Updates cumulative performance tracking

3. **Weekly Adjustment (Friday 10:00 AM Beijing Time):**
   ```bash
   ./harness-run.sh --adjust
   ```
   - Analyzes week's prediction accuracy
   - Suggests metric adjustments based on performance
   - Updates tracking weights and thresholds

### Automation with Cron

Add to crontab for fully automated daily analysis (Beijing Time schedule):
```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily summary at 9:00 AM Beijing Time (after US market close, analyze previous day)
0 9 * * * cd /Users/Jagger/.agents/skills/stock-analysis/harness && ./harness-run.sh --daily

# Backtest at 9:30 AM Beijing Time (review yesterday's predictions vs actual)
30 9 * * * cd /Users/Jagger/.agents/skills/stock-analysis/harness && ./harness-run.sh --backtest

# Weekly adjustment every Friday at 10:00 AM Beijing Time
0 10 * * 5 cd /Users/Jagger/.agents/skills/stock-analysis/harness && ./harness-run.sh --adjust
```

**Why Beijing Time 9 AM?**
- **9:00 AM Beijing Time** = ~8-9 PM previous day US Eastern Time
- US stock market closes at 4:00 PM EST = 5:00 AM next day Beijing Time
- By 9:00 AM Beijing Time, all US market data is finalized
- Perfect timing to analyze completed trading day and prepare for next session

**Time conversion reference:**
- **Beijing Time (CST):** Use times as shown above
- **New York (EST/EDT):** Add 12-13 hours (e.g., 9 AM CST = 8-9 PM previous day EST)
- **London (GMT/BST):** Subtract 7-8 hours (e.g., 9 AM CST = 1-2 AM GMT)
- **San Francisco (PST/PDT):** Add 15-16 hours (e.g., 9 AM CST = 5-6 PM previous day PST)

### Key Features

**1. Daily Summary:**
- Market sentiment snapshot
- Watchlist performance tracking
- Prediction recording for tomorrow
- JSON and Markdown output formats

**2. Backtesting:**
- Price direction accuracy tracking
- Target price accuracy calculation
- Recommendation effectiveness scoring
- Cumulative performance metrics

**3. Adaptive Metrics:**
- Automatic weight adjustment for underperforming metrics
- Suggestion of complementary indicators
- Threshold tuning based on historical performance
- Conservative adjustment to avoid overfitting

**4. Reporting:**
- Daily summary reports in Markdown
- Backtest results in JSON
- Cumulative metrics dashboard
- Adjustment suggestions log

### Configuration

Edit `harness/config.yaml` to customize:

```yaml
# Watchlist — loaded from references/watchlist.json at runtime
# Edit references/watchlist.json to change the actual watchlist
watchlist: []  # Empty = auto-load from watchlist.json

# Backtest thresholds
backtest:
  thresholds:
    price_direction_accuracy: 0.6  # 60%
    target_price_accuracy: 0.3     # 30%
    recommendation_accuracy: 0.7   # 70%

# Adjustment settings
adjustment:
  enabled: false  # Set to true for auto-adjustment
  min_observations: 10  # Minimum days before adjustment
```

### Integration with Existing Analysis

The harness system complements the existing stock analysis by:

1. **Adding temporal dimension** - Track performance over time
2. **Providing feedback loop** - Learn from prediction errors
3. **Enabling adaptation** - Adjust methods based on market conditions
4. **Creating accountability** - Document and review decisions

### Example Output

**Daily Summary Report:**
```markdown
# 📊 Daily Stock Analysis Summary
Date: 2026-04-21

## Market Overview
- **Market Sentiment:** 48 (Neutral)
- **Major Indices:** S&P 500 +1.2%, NASDAQ +1.8%

## Watchlist Performance
| Symbol | Price | Change | Volume | Recommendation |
|--------|-------|--------|--------|----------------|
| BABA.US | $141.01 | +1.7% | 12.8M | Hold |
| NVDA.US | $875.32 | +2.3% | 45.2M | Consider taking profits |
```

**Backtest Results:**
```json
{
  "prediction_date": "2026-04-20",
  "actual_date": "2026-04-21",
  "price_direction_accuracy": 0.75,
  "target_price_accuracy": 0.40,
  "passed_thresholds": true
}
```

### Benefits

1. **Systematic Improvement** - Continuously refine analysis methods
2. **Performance Tracking** - Quantify prediction accuracy
3. **Adaptive Learning** - Adjust to changing market conditions
4. **Disciplined Process** - Enforce daily review routine
5. **Data-Driven Decisions** - Base adjustments on empirical evidence

### Next Steps

1. **Initial Setup:** Run harness manually for a week to collect data
2. **Review:** Check backtest results and adjustment suggestions
3. **Automate:** Set up cron jobs for hands-free operation
4. **Customize:** Modify config.yaml to match your trading style
5. **Extend:** Add custom metrics or analysis methods

---

## 🚀 Advanced Analysis Engine (新增功能)

### Overview

新版本集成了完整的量化分析引擎，提供：

1. **风险指标** - Sharpe Ratio、最大回撤、Sortino Ratio、Beta、VaR等
2. **估值指标** - P/E、PEG、EV/EBITDA、P/FCF、Graham Intrinsic Value等
3. **技术指标** - RSI、MACD、布林带、随机指标、ATR等
4. **多因子模型** - Quality、Value、Growth、Momentum、Low Volatility因子

### Quick Start

**安装依赖:**
```bash
cd /Users/Jagger/.agents/skills/stock-analysis/analysis
pip install -r requirements.txt
```

**命令行使用:**

```bash
# 分析单个股票
python analyze.py AAPL.US

# 分析自选股
python analyze.py --watchlist

# 分析持仓
python analyze.py --portfolio

# 分析多只股票并保存报告
python analyze.py BABA.US NVDA.US TSLA.US -o report.md

# JSON格式输出
python analyze.py AAPL.US --format json -o analysis.json
```

### Python API使用

```python
from analysis.engine import StockData, StockAnalysisEngine

# 创建股票数据对象
stock_data = StockData(
    symbol="AAPL.US",
    prices=[150.0, 152.5, 151.0, 153.0, 155.5],  # 历史价格
    current_price=155.5,
    market_cap=2500000000000,
    sector="Technology",
    eps=6.5,
    revenue=385000000000,
    ebitda=120000000000,
    # ... 更多财务数据
)

# 创建分析引擎
engine = StockAnalysisEngine()

# 执行综合分析
analysis = engine.analyze_stock(stock_data)

# 生成报告
report = engine.generate_report(analysis, format='markdown')
print(report)
```

### Risk Metrics (风险指标)

**Sharpe Ratio (夏普比率)**
```python
from analysis.engine import RiskMetricsCalculator

# 计算Sharpe Ratio
returns = [0.01, -0.02, 0.03, 0.005, -0.01]  # 每日收益率
sharpe = RiskMetricsCalculator.calculate_sharpe_ratio(returns, risk_free_rate=0.03)

# Interpretation:
# > 2.0: Excellent (优秀)
# 1.0-2.0: Good (良好)
# 0.5-1.0: Acceptable (可接受)
# < 0.5: Poor (较差)
```

**Maximum Drawdown (最大回撤)**
```python
prices = [100, 105, 110, 95, 100, 90, 85, 95, 100]
max_dd, peak_idx, trough_idx = RiskMetricsCalculator.calculate_max_drawdown(prices)

# Interpretation:
# < -10%: Low risk (低风险)
# -10% to -20%: Moderate risk (中等风险)
# -20% to -30%: High risk (高风险)
# > -30%: Very high risk (极高风险)
```

**Beta Coefficient (贝塔系数)**
```python
stock_returns = [0.02, -0.01, 0.03, 0.01]
market_returns = [0.015, -0.005, 0.02, 0.01]
beta, r_squared = RiskMetricsCalculator.calculate_beta(stock_returns, market_returns)

# Interpretation:
# β < 0.8: Defensive (防御性)
# 0.8 ≤ β ≤ 1.2: Neutral (中性)
# β > 1.2: Aggressive (激进)
```

**Value at Risk (VaR)**
```python
var_95 = RiskMetricsCalculator.calculate_var(returns, confidence_level=0.95)

# Interpretation: 95%置信度下，单日最大损失不超过var_95
```

**Comprehensive Risk Score (综合风险评分)**
```python
risk_metrics = {
    'max_drawdown': -0.18,
    'volatility': 0.25,
    'beta': 1.15,
    'var_95': -0.025,
    'avg_correlation': 0.5
}
risk_score, breakdown = RiskMetricsCalculator.calculate_comprehensive_risk_score(risk_metrics)

# Returns: risk_score (0-100, 越高风险越大)
```

### Valuation Metrics (估值指标)

**P/E Ratio**
```python
from analysis.engine import ValuationMetricsCalculator

pe_ratio, percentile = ValuationMetricsCalculator.calculate_pe_ratio(
    price=150.0, 
    eps=6.5, 
    sector='Technology'
)

# Percentile: 'Low' (低估), 'Average' (合理), 'High' (高估)
```

**PEG Ratio**
```python
peg_ratio = ValuationMetricsCalculator.calculate_peg_ratio(
    pe_ratio=23.0, 
    growth_rate=0.15  # 15%增长
)

# Interpretation:
# < 0.5: Significantly undervalued (显著低估)
# 0.5-1.0: Fair/Undervalued (合理/低估)
# 1.0-1.5: Fairly valued (合理)
# 1.5-2.0: Overvalued (高估)
# > 2.0: Significantly overvalued (显著高估)
```

**Graham Intrinsic Value (格雷厄姆内在价值)**
```python
graham_value = ValuationMetricsCalculator.calculate_graham_intrinsic_value(
    eps=6.5,
    growth_rate=0.12,
    bond_yield=0.04  # 4% 债券收益率
)

# 公式: EPS × (8.5 + 2g) × 4.4 / 债券收益率
```

**Valuation Score (估值评分)**
```python
valuation_metrics = {
    'pe_ratio': 18.5,
    'peg_ratio': 1.2,
    'p_fcf_ratio': 15.0,
    'ev_ebitda_ratio': 10.5
}
score, breakdown = ValuationMetricsCalculator.calculate_valuation_score(
    valuation_metrics, 
    sector='Technology'
)

# Score: 0-100 (越低越被低估)
# 0-30: Significantly Undervalued
# 30-50: Undervalued
# 50-70: Fairly Valued
# 70-90: Overvalued
# 90-100: Significantly Overvalued
```

### Technical Indicators (技术指标)

**Moving Averages (移动平均线)**
```python
from analysis.engine import TechnicalIndicatorsCalculator

prices = [150.0, 152.5, 151.0, 153.0, 155.5, 154.0, 156.0]

# 计算SMA
sma = TechnicalIndicatorsCalculator.calculate_moving_averages(
    prices, 
    periods=[20, 50, 200], 
    ma_type='sma'
)

# 计算EMA
ema = TechnicalIndicatorsCalculator.calculate_moving_averages(
    prices, 
    periods=[12, 26], 
    ma_type='ema'
)
```

**RSI (相对强弱指标)**
```python
rsi = TechnicalIndicatorsCalculator.calculate_rsi(prices, period=14)

# Interpretation:
# > 70: Overbought (超买)
# 30-70: Normal (正常)
# < 30: Oversold (超卖)
```

**MACD**
```python
macd_dict = TechnicalIndicatorsCalculator.calculate_macd(
    prices, 
    fast=12, 
    slow=26, 
    signal=9
)

# Returns: {'macd_line': [...], 'signal_line': [...], 'histogram': [...]}
# Bullish: MACD crosses above signal line
# Bearish: MACD crosses below signal line
```

**Bollinger Bands (布林带)**
```python
bb = TechnicalIndicatorsCalculator.calculate_bollinger_bands(
    prices, 
    period=20, 
    num_std=2
)

# Returns: {
#   'upper_band': [...],
#   'middle_band': [...],
#   'lower_band': [...],
#   'bandwidth': [...],
#   'percent_b': [...]
# }
```

**Technical Score (技术评分)**
```python
indicators = {
    'ma_50': [...],
    'ma_200': [...],
    'rsi': [...],
    'macd_line': [...],
    'signal_line': [...]
}
score, breakdown = TechnicalIndicatorsCalculator.calculate_technical_score(
    indicators, 
    current_price=155.5
)

# Score: 0-100 (越高越看涨)
# 80-100: Strongly Bullish
# 60-80: Bullish
# 40-60: Neutral
# 20-40: Bearish
# 0-20: Strongly Bearish
```

### Multi-Factor Model (多因子模型)

**Factor Scores Calculation**
```python
from analysis.engine import MultiFactorCalculator

financials = {
    'roe': 0.25,  # 25% ROE
    'gross_margin': 0.45,  # 45% gross margin
    'debt_to_equity': 0.3,  # 0.3 D/E ratio
    'pe_ratio': 18.5,
    'ev_ebitda': 10.5,
    'fcf_yield': 0.048,  # 4.8% FCF yield
    'revenue_growth': 0.15,  # 15% revenue growth
    'eps_growth': 0.18,  # 18% EPS growth
    'estimated_growth': 0.12  # 12% estimated future growth
}

# Calculate individual factor scores
quality_score = MultiFactorCalculator.calculate_quality_score(financials)
value_score = MultiFactorCalculator.calculate_value_score(financials, current_price, sector)
growth_score = MultiFactorCalculator.calculate_growth_score(financials)
momentum_score = MultiFactorCalculator.calculate_momentum_score(prices, eps_estimates)
low_vol_score = MultiFactorCalculator.calculate_low_volatility_score(prices, beta)

factor_scores = {
    'quality': {'score': quality_score},
    'value': {'score': value_score},
    'growth': {'score': growth_score},
    'momentum': {'score': momentum_score},
    'low_volatility': {'score': low_vol_score}
}
```

**Composite Factor Score (综合因子评分)**
```python
composite_score, breakdown, strategy = MultiFactorCalculator.calculate_composite_factor_score(
    factor_scores,
    strategy='balanced'  # Options: 'quality_value', 'growth_momentum', 'balanced', 'defensive', 'aggressive_growth'
)

# Returns:
# - composite_score: 0-100
# - breakdown: 各因子贡献
# - strategy: 使用的策略
```

**Investment Strategies (投资策略)**

| Strategy | Best For | Factor Weights |
|----------|----------|----------------|
| **quality_value** | Long-term investors | Quality 40%, Value 40%, Growth 10%, Momentum 5%, Low Vol 5% |
| **growth_momentum** | Growth investors | Quality 20%, Value 10%, Growth 40%, Momentum 25%, Low Vol 5% |
| **balanced** | Most investors | Quality 25%, Value 25%, Growth 20%, Momentum 20%, Low Vol 10% |
| **defensive** | Risk-averse | Quality 30%, Value 30%, Growth 10%, Momentum 10%, Low Vol 20% |
| **aggressive_growth** | High-risk | Quality 15%, Value 10%, Growth 50%, Momentum 20%, Low Vol 5% |

### Complete Analysis Example

```python
from analysis.engine import StockData, StockAnalysisEngine

# 创建股票数据
stock_data = StockData(
    symbol="NVDA.US",
    prices=[450, 460, 455, 470, 475, 480, 490],  # 至少200天数据最佳
    highs=[455, 465, 460, 475, 480, 485, 495],
    lows=[445, 455, 450, 465, 470, 475, 485],
    volumes=[15000000, 16000000, 14500000, 17000000, 16500000, 17500000, 18000000],
    current_price=490,
    market_cap=1200000000000,
    sector="Technology",
    eps=12.5,
    revenue=60000000000,
    ebitda=25000000000,
    net_income=20000000000,
    shareholders_equity=40000000000,
    total_debt=10000000000,
    cash=30000000000,
    free_cash_flow=18000000000,
    revenue_growth=0.60,  # 60% growth
    eps_growth=0.80,  # 80% EPS growth
    estimated_growth=0.35  # 35% future growth
)

# 执行综合分析
engine = StockAnalysisEngine()
analysis = engine.analyze_stock(stock_data)

# 查看结果
print(f"Overall Recommendation: {analysis['overall_assessment']['recommendation']}")
print(f"Overall Score: {analysis['overall_assessment']['overall_score']:.1f}/100")
print(f"Risk Score: {analysis['risk_analysis']['risk_score']:.1f}/100")
print(f"Valuation Score: {analysis['valuation_analysis']['valuation_score']:.1f}/100")
print(f"Technical Score: {analysis['technical_analysis']['technical_score']:.1f}/100")
print(f"Factor Score: {analysis['factor_analysis']['composite_score']:.1f}/100")

# 生成Markdown报告
report = engine.generate_report(analysis, format='markdown')
```

### Sample Output

```markdown
# Stock Analysis Report: NVDA.US
**Analysis Date:** 2026-04-21T10:30:00
**Current Price:** $490.00

## Overall Assessment
**Recommendation:** **BUY** (MEDIUM-HIGH confidence)
**Overall Score:** 72.5/100

### Score Breakdown:
- Risk Score: 65.0/100
- Valuation Score: 45.0/100
- Technical Score: 78.0/100
- Factor Score: 82.0/100

## Risk Analysis
**Risk Score:** 65/100 (Moderate-High Risk)

**Key Metrics:**
- Sharpe Ratio: 1.85
- Maximum Drawdown: -22.5%
- Sortino Ratio: 2.15
- Beta: 1.45
- Historical Volatility: 35.2%
- 95% VaR: -3.2%

## Valuation Analysis
**Valuation Score:** 45/100 (Undervalued)
**Attractiveness:** Undervalued

**Key Metrics:**
- P/E Ratio: 39.2x (High)
- EV/EBITDA: 48.0x
- PEG Ratio: 0.49 (Undervalued given growth)
- P/FCF: 66.7x
- FCF Yield: 1.5%

## Technical Analysis
**Technical Score:** 78/100 (Bullish)

**Key Signals:**
- RSI: 62.5 (Bullish momentum)
- MACD: Bullish crossover confirmed
- Price above 50-day and 200-day MA
- Bollinger Band: Upper half

## Multi-Factor Analysis
**Composite Factor Score:** 82/100 (Strong)
**Strategy:** Balanced

**Factor Scores:**
- Quality: 85/100 (Excellent ROE and margins)
- Value: 55/100 (Fair given growth)
- Growth: 95/100 (Exceptional growth)
- Momentum: 88/100 (Strong price momentum)
- Low Volatility: 45/100 (Higher volatility)
```

### Integration with Longbridge CLI

分析引擎与Longbridge CLI无缝集成：

```python
from analysis.analyze import StockAnalyzer

analyzer = StockAnalyzer()

# 分析单个股票
analysis = analyzer.analyze_symbol('AAPL.US')

# 分析自选股
report = analyzer.generate_watchlist_report(['BABA.US', 'NVDA.US', 'TSLA.US'])

# 分析持仓
portfolio_analysis = analyzer.analyze_portfolio()

# 保存报告
analyzer.save_report(report, 'output/watchlist_report.md')
```

### Performance Considerations

1. **数据要求:**
   - 风险指标: 至少60天价格数据
   - 技术指标: 200天数据最佳
   - 估值指标: 需要财务数据

2. **计算效率:**
   - 单股分析: ~1-2秒
   - 自选股分析(11只): ~15-20秒
   - 使用NumPy向量化计算

3. **数据源:**
   - 优先使用Longbridge CLI实时数据
   - 可手动输入历史数据
   - 支持CSV/JSON数据导入

### API Reference

**StockData Class**
```python
@dataclass
class StockData:
    symbol: str
    prices: List[float]  # Required: Historical closing prices
    volumes: Optional[List[float]] = None
    highs: Optional[List[float]] = None
    lows: Optional[List[float]] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    # ... financial metrics
```

**StockAnalysisEngine Methods**
- `analyze_stock(stock_data: StockData) -> Dict` - 执行综合分析
- `generate_report(analysis: Dict, format: str) -> str` - 生成报告

**RiskMetricsCalculator Methods**
- `calculate_sharpe_ratio(returns, risk_free_rate) -> float`
- `calculate_max_drawdown(prices) -> Tuple[float, int, int]`
- `calculate_sortino_ratio(returns, risk_free_rate) -> float`
- `calculate_beta(stock_returns, market_returns) -> Tuple[float, float]`
- `calculate_var(returns, confidence_level) -> float`
- `calculate_historical_volatility(returns) -> float`
- `calculate_comprehensive_risk_score(risk_metrics) -> Tuple[float, Dict]`

**ValuationMetricsCalculator Methods**
- `calculate_pe_ratio(price, eps, sector) -> Tuple[float, str]`
- `calculate_ev_ebitda(market_cap, debt, cash, ebitda) -> float`
- `calculate_peg_ratio(pe_ratio, growth_rate) -> float`
- `calculate_fcf_yield(free_cash_flow, market_cap) -> float`
- `calculate_graham_intrinsic_value(eps, growth_rate, bond_yield) -> float`
- `calculate_valuation_score(valuation_metrics, sector) -> Tuple[float, Dict]`

**TechnicalIndicatorsCalculator Methods**
- `calculate_moving_averages(prices, periods, ma_type) -> Dict`
- `calculate_rsi(prices, period) -> List[float]`
- `calculate_macd(prices, fast, slow, signal) -> Dict`
- `calculate_bollinger_bands(prices, period, num_std) -> Dict`
- `calculate_stochastic(highs, lows, closes, k_period, d_period) -> Dict`
- `calculate_atr(highs, lows, closes, period) -> List[float]`
- `calculate_technical_score(indicators, current_price) -> Tuple[float, Dict]`

**MultiFactorCalculator Methods**
- `calculate_quality_score(financials) -> float`
- `calculate_value_score(financials, current_price, sector) -> float`
- `calculate_growth_score(financials) -> float`
- `calculate_momentum_score(prices, eps_estimates) -> float`
- `calculate_low_volatility_score(prices, beta) -> float`
- `calculate_composite_factor_score(factor_scores, strategy) -> Tuple[float, Dict, str]`

---

## Limitations

1. Gap analysis requires at least 60 days of K-line data for reliability
2. Sentiment index only available during market hours
3. Valuation metrics depend on data availability from Longbridge
4. Recommendations are educational, not financial advice
5. Always confirm with additional research before trading
