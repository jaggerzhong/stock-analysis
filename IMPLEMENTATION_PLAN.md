# Stock-Analysis Bug Fix Implementation Plan

**Date:** 2026-04-29
**Scope:** 19 confirmed issues (4 HIGH, 7 MEDIUM, 5 LOW, 2 partial, 9 not found)
**Files affected:** engine.py, analyze.py, SKILL.md, daily-summary.sh, adjust-metrics.py, generate_valuation.py, config.yaml, test_engine.py

---

## Phase 1: HIGH Severity (必须立即修复)

### 1.1 #1 — NOPAT计算逻辑错误

**文件:** `analysis/engine.py:2943-2944`
**当前代码:**
```python
elif stock_data.net_income:
    nopat = stock_data.net_income * (1 + tax_rate)
```
**问题:** Net Income已扣除税和利息，乘以`(1+tax_rate)`既没有还原利息也没有正确还原税。NOPAT = Operating Income × (1 - tax_rate)，不是 Net Income × (1 + tax_rate)。
**修复方案:**
```python
elif stock_data.net_income and stock_data.total_debt is not None:
    # 估算: Net Income + Interest Expense × (1 - tax_rate)
    # Interest Expense ≈ total_debt × cost_of_debt
    cost_of_debt = get_config('value_trap', 'wacc_params', default={}).get('default_cost_of_debt', 0.05)
    interest_expense = stock_data.total_debt * cost_of_debt
    nopat = stock_data.net_income + interest_expense * (1 - tax_rate)
```
**验证:** 用NVDA数据(EBITDA存在)和一只无EBITDA的股票分别计算ROIC，确认逻辑一致。

---

### 1.2 #5 — SKILL.md两套情绪-仓位映射表矛盾

**文件:** `SKILL.md:206-213` vs `SKILL.md:767-773`
**问题:** 两张表的阈值和标签不一致:
| Score | Step 1.4 (line 206) | Step 5.1 (line 767) |
|-------|---------------------|---------------------|
| 60-70 | Neutral-Bullish → 40-55% | Greed → 30-50% |
| 70-80 | Greed → 25-40% | (合并入70-100) Extreme Greed → 10-30% |

**修复方案:**
1. 以 Step 1.4 的6档映射为权威源(与engine.py `comprehensive_score_to_position()`一致)
2. 重写 Step 5.1 的表格，使其与 Step 1.4 完全对齐
3. 删除 `SKILL.md:1121-1159` 的 `dynamic_position_sizing` JSON配置(纯装饰品，未被引擎读取)
4. 在 Step 5.1 表格下方添加标注: "此表与 Step 1.4 保持一致，以 `comprehensive_score_to_position()` 为唯一源"

**具体改动:**
- Step 5.1 表格替换为:
```
| Score Range | Market State     | Target Position | Target Cash | Action              |
|-------------|------------------|-----------------|-------------|---------------------|
| 80-100      | Extreme Greed    | 10-25%          | 75-90%      | Aggressive Sell     |
| 70-80       | Greed            | 25-40%          | 60-75%      | Selective Sell      |
| 60-70       | Neutral-Bullish  | 40-55%          | 45-60%      | Hold                |
| 40-60       | Neutral          | 50-65%          | 35-50%      | Hold/Selective Buy  |
| 30-40       | Fear             | 65-80%          | 20-35%      | Selective Buy       |
| 0-30        | Extreme Fear     | 80-95%          | 5-20%       | Aggressive Buy      |
```

---

### 1.3 #9 — JSON解析截断合法数组

**文件:** `analysis/analyze.py:134-136`
**当前代码:**
```python
if isinstance(parsed, list) and len(parsed) > 0:
    data = parsed[0]
```
**问题:** 批量查询返回数组，只取第一个丢弃其余。
**修复方案:** 将 `parse_quote` 改为返回列表，新增 `parse_batch_quotes` 方法:

```python
@staticmethod
def parse_quote(quote_output: str) -> Union[Dict, List[Dict]]:
    """Parse quote output - returns list for batch, dict for single."""
    if not quote_output or not quote_output.strip():
        return {}
    try:
        parsed = json.loads(quote_output.strip())
        if isinstance(parsed, list):
            return parsed  # 返回完整列表
        elif isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {}

@staticmethod
def parse_batch_quotes(quote_output: str) -> List[Dict]:
    """Always return a list of quote dicts."""
    result = LongbridgeDataFetcher.parse_quote(quote_output)
    if isinstance(result, list):
        return result
    elif isinstance(result, dict):
        return [result] if result else []
    return []
```

**下游影响:**
- `fetch_quote()` 返回单个Dict(从列表取第一个或直接返回dict) — 保持单符号调用兼容
- 新增 `fetch_batch_quotes()` 返回 `Dict[str, Dict]` (symbol → quote)
- `analyze.py` 的 `generate_watchlist_report()` 改为使用批量获取

**验证:** 测试 `longbridge quote BABA.US NVDA.US` 返回2个结果均被保留。

---

### 1.4 #18 — Portfolio + Markdown格式崩溃

**文件:** `analysis/analyze.py:848-854`, `analysis/engine.py:3590`
**当前代码:**
```python
# analyze.py:853
report = analyzer.engine.generate_report(analysis, format='markdown')
# engine.py:3590
md = f"# Stock Analysis Report: {analysis['symbol']}"
```
**问题:** `analyze_portfolio()` 返回的结构没有顶级 `symbol` 键，`generate_report` 直接KeyError。
**修复方案:**
1. 在 `engine.py` 的 `generate_report()` 中增加 portfolio 格式判断
2. 新增 `generate_portfolio_report()` 方法
3. 在 `analyze.py` 中调用正确的方法

**engine.py 改动:**
```python
def generate_report(self, analysis: Dict, format: str = 'markdown') -> str:
    if format == 'json':
        return json.dumps(analysis, indent=2, default=str)
    
    # Detect portfolio report
    if 'positions' in analysis and 'summary' in analysis and 'symbol' not in analysis:
        return self.generate_portfolio_report(analysis, format='markdown')
    
    # Single stock report (existing logic)
    ...

def generate_portfolio_report(self, analysis: Dict, format: str = 'markdown') -> str:
    """Generate markdown report for portfolio analysis."""
    summary = analysis.get('summary', {})
    md = f"""# Portfolio Analysis Report
**Analysis Date:** {analysis.get('analysis_date', 'N/A')}
**Total Positions:** {summary.get('total_positions', 0)}
**Total Value:** ${summary.get('total_market_value', 0):,.2f}
**Total P/L:** ${summary.get('total_profit_loss', 0):,.2f}

## Stock Positions
"""
    for pos in analysis.get('positions', []):
        symbol = pos.get('symbol', 'N/A')
        score = pos.get('overall_assessment', {}).get('overall_score', 'N/A')
        rec = pos.get('overall_assessment', {}).get('recommendation', 'N/A')
        md += f"- **{symbol}**: Score {score}/100, {rec}\n"
    
    md += "\n## Option Positions\n"
    for opt in analysis.get('option_positions', []):
        md += f"- {opt.get('strategy', {}).get('name', 'N/A')}\n"
    
    risk = analysis.get('portfolio_risk', {})
    if risk:
        md += f"\n## Portfolio Risk\n- Concentration: {risk.get('concentration_risk', 'N/A')}\n"
    
    return md
```

**验证:** `python analyze.py --portfolio --format markdown` 不崩溃并生成合理报告。

---

## Phase 2: MEDIUM Severity (本周修复)

### 2.1 #3 — 三套PE行业基准冲突

**文件:** `engine.py:115-125`, `engine.py:2533-2535`, `engine.py:2607-2612`
**问题:** 
- `_SECTOR_PE_BENCHMARKS` (line 115): Technology cheap=15, expensive=35
- `_calculate_pe_score` fallback (line 2534): cheap=12, expensive=25
- `_calculate_ev_ebitda_score` (line 2607-2612): 硬编码 cheap=8, expensive=20

**修复方案:**
1. 统一以 `_get_sector_pe_benchmarks()` 为唯一数据源
2. 在config.yaml中添加 `sector_ev_ebitda_benchmarks`
3. 新增 `_get_sector_ev_ebitda_benchmarks()` 函数
4. `_calculate_pe_score` 和 `_calculate_ev_ebitda_score` 从统一数据源获取基准

**engine.py 改动:**
```python
_SECTOR_EV_EBITDA_BENCHMARKS = None

def _get_sector_ev_ebitda_benchmarks():
    global _SECTOR_EV_EBITDA_BENCHMARKS
    if _SECTOR_EV_EBITDA_BENCHMARKS is not None:
        return _SECTOR_EV_EBITDA_BENCHMARKS
    raw = get_config('valuation', 'sector_ev_ebitda_benchmarks')
    if raw:
        _SECTOR_EV_EBITDA_BENCHMARKS = {}
        for sector, data in raw.items():
            norm = sector.replace('_', ' ')
            _SECTOR_EV_EBITDA_BENCHMARKS[norm] = {
                'cheap': data.get('range', [6, 15])[0],
                'expensive': data.get('range', [6, 15])[1],
            }
    else:
        _SECTOR_EV_EBITDA_BENCHMARKS = {
            'Technology': {'cheap': 8, 'expensive': 20},
            'Healthcare': {'cheap': 8, 'expensive': 20},
            'Financials': {'cheap': 5, 'expensive': 12},
            'Utilities': {'cheap': 5, 'expensive': 12},
            'Industrials': {'cheap': 6, 'expensive': 15},
            'Energy': {'cheap': 4, 'expensive': 10},
            'Consumer Staples': {'cheap': 6, 'expensive': 15},
            'Consumer Discretionary': {'cheap': 6, 'expensive': 15},
        }
    return _SECTOR_EV_EBITDA_BENCHMARKS
```

**_calculate_pe_score 改动 (line 2530-2535):**
```python
if sector and sector in sector_benchmarks:
    cheap = sector_benchmarks[sector]['cheap']
    expensive = sector_benchmarks[sector]['expensive']
else:
    # 使用所有行业基准的中位数作为fallback
    all_cheaps = [v['cheap'] for v in sector_benchmarks.values()]
    all_expensive = [v['expensive'] for v in sector_benchmarks.values()]
    cheap = sorted(all_cheaps)[len(all_cheaps) // 2]
    expensive = sorted(all_expensive)[len(all_expensive) // 2]
```

**_calculate_ev_ebitda_score 改动 (line 2606-2612):**
```python
sector_ev_ebitda = _get_sector_ev_ebitda_benchmarks()
if sector and sector in sector_ev_ebitda:
    cheap = sector_ev_ebitda[sector]['cheap']
    expensive = sector_ev_ebitda[sector]['expensive']
else:
    cheap, expensive = 6, 15
```

**config.yaml 新增:**
```yaml
valuation:
  sector_ev_ebitda_benchmarks:
    Technology:    { range: [8, 20] }
    Healthcare:    { range: [8, 20] }
    Financials:    { range: [5, 12] }
    Utilities:     { range: [5, 12] }
    Industrials:   { range: [6, 15] }
    Energy:        { range: [4, 10] }
    Consumer_Staples:     { range: [6, 15] }
    Consumer_Discretionary: { range: [6, 15] }
```

---

### 2.2 #8 — 估值评分语义反转未文档化

**文件:** `engine.py:3436`, `SKILL.md`
**修复方案:**
1. 在 `engine.py:3436` 添加详细注释
2. 在 `calculate_valuation_score` 方法处添加文档说明语义
3. 在 SKILL.md 估值评分章节添加说明

**engine.py 注释改动 (line 3434-3438):**
```python
# NOTE: valuation_score uses "lower = more undervalued" semantics (0=cheap, 100=expensive).
# We invert it here: (100 - valuation_score) so that undervalued stocks contribute
# a HIGHER score to the overall assessment, making "higher = better" consistent across all dimensions.
overall_score = (
    (100 - risk_score) * weights['risk'] +
    (100 - valuation_score) * weights['valuation'] +
    technical_score * weights['technical'] +
    factor_score * weights['factor']
)
```

**SKILL.md 在估值评分描述处添加:**
```markdown
> **Important:** Valuation Score uses "lower is better" semantics (0 = significantly undervalued, 100 = significantly overvalued). 
> When calculating the overall score, this is inverted to (100 - valuation_score) so that undervalued stocks score higher overall.
```

---

### 2.3 #11 — is_itm属性永远返回None

**文件:** `engine.py:246-250`, `engine.py:278-287`, `engine.py:313-316`
**问题:** `parse_symbol()` 和 `parse_positions()` 都不设置 `underlying_price`。
**修复方案:**
1. `OptionAnalyzer.analyze_option()` 接收 `underlying_price` 后赋值给 `option.underlying_price`
2. `parse_positions()` 添加可选的 `underlying_prices` 参数

**engine.py 改动 (line 410-425):**
```python
@staticmethod
def analyze_option(option: OptionPosition, underlying_price: float) -> Dict:
    # 设置 underlying_price 使 is_itm 属性可用
    option.underlying_price = underlying_price
    
    try:
        option = OptionAnalyzer.estimate_greeks(option, underlying_price)
    except ImportError:
        pass
    
    itm = option.is_itm_with_price(underlying_price)
    ...
```

**验证:** 调用 `analyze_option()` 后，`option.is_itm` 不再返回None。

---

### 2.4 #14 — 经常性收入硬编码猜测

**文件:** `engine.py:148-183` (StockData), `engine.py:2861-2873`
**修复方案:**
1. StockData 新增 `recurring_revenue_pct` 字段
2. `analyze_moat()` 优先使用 `stock_data.recurring_revenue_pct`，缺失时回退到行业均值

**engine.py StockData 新增 (line 168后):**
```python
recurring_revenue_pct: Optional[float] = None
```

**engine.py analyze_moat 改动 (line 2861-2873):**
```python
recurring_revenue_pct = None
if stock_data.recurring_revenue_pct is not None:
    recurring_revenue_pct = stock_data.recurring_revenue_pct
else:
    sector_recurring = get_config('moat', 'sector_recurring_revenue', default={
        'Technology': 0.60, 'Financials': 0.70, 'Healthcare': 0.50,
        'Consumer Staples': 0.40, 'Utilities': 0.50, 'Industrials': 0.30,
        'Energy': 0.20, 'Consumer Discretionary': 0.30
    })
    if stock_data.sector and stock_data.sector in sector_recurring:
        recurring_revenue_pct = sector_recurring[stock_data.sector]
```

**config.yaml moat 部分新增:**
```yaml
moat:
  sector_recurring_revenue:
    Technology: 0.60
    Financials: 0.70
    Healthcare: 0.50
    Consumer_Staples: 0.40
    Utilities: 0.50
    Industrials: 0.30
    Energy: 0.20
    Consumer_Discretionary: 0.30
```

---

### 2.5 #26 — 仓位配置未被引擎读取

**文件:** `engine.py:128-144`, `config.yaml`, `SKILL.md:1117-1159`
**修复方案:**
1. 在 `config.yaml` 添加 `position_sizing.score_to_position` 映射
2. `comprehensive_score_to_position()` 从 config 读取
3. 删除 SKILL.md 中装饰性的 JSON 配置段

**config.yaml 新增 (under overall):**
```yaml
overall:
  score_to_position:
    extreme_greed:     { min: 80, position: 17.5 }
    greed:             { min: 70, position: 32.5 }
    neutral_bullish:   { min: 60, position: 47.5 }
    neutral:           { min: 40, position: 57.5 }
    fear:              { min: 30, position: 72.5 }
    extreme_fear:      { min: 0,  position: 87.5 }
```

**engine.py 改动 (line 128-144):**
```python
def comprehensive_score_to_position(comprehensive_score: float) -> float:
    score_map = get_config('overall', 'score_to_position', default=None)
    if score_map:
        for regime_name, params in sorted(
            score_map.items(),
            key=lambda x: x[1].get('min', 0),
            reverse=True
        ):
            if comprehensive_score >= params.get('min', 0):
                return params.get('position', 57.5)
    
    # Fallback hardcoded (matches config)
    if comprehensive_score >= 80: return 17.5
    elif comprehensive_score >= 70: return 32.5
    elif comprehensive_score >= 60: return 47.5
    elif comprehensive_score >= 40: return 57.5
    elif comprehensive_score >= 30: return 72.5
    else: return 87.5
```

**SKILL.md 改动:** 删除 line 1104-1159 的 "Legacy Parameters" 和 "Dynamic Position Sizing Configuration" 两段，替换为:
```markdown
### Position Sizing Configuration

Position sizing is configured in `analysis/config.yaml` under `overall.score_to_position`.
The mapping matches Step 1.4 (the authoritative source). See the config file for exact values.
```

---

### 2.6 #34 — current_price可能取stale kline收盘价

**文件:** `analyze.py:353`, `engine.py:181-182`
**修复方案:**
1. `prepare_stock_data()` 中kline收盘价fallback时添加警告日志
2. `analyze_symbol()` 中分析前用实时报价覆盖(已有line 472-475，但不改analysis内部数据)
3. 在分析结果中添加 `price_source` 标记

**analyze.py 改动 (line 353):**
```python
live_price = quote.get('last') or quote.get('last_done')
if live_price:
    current_price = float(live_price)
    price_source = 'live_quote'
elif prices:
    current_price = prices[-1]
    price_source = 'kline_close_stale'
    print(f"  WARNING: Live quote unavailable for {symbol}, using last kline close (may be stale)")
else:
    current_price = 0
    price_source = 'unavailable'
```

**engine.py `__post_init__` 改动 (line 179-182):**
```python
def __post_init__(self):
    if self.current_price is None and self.prices:
        self.current_price = self.prices[-1] if self.prices else None
        self._price_source = 'kline_close_fallback'
    else:
        self._price_source = 'provided'
```

**analyze.py StockData构造后设置source:**
```python
stock_data._price_source = price_source
```

---

### 2.7 #33 — 三种不同import路径策略

**文件:** `analyze.py:18`, `backtest.py:16`, `generate_predictions.py:14`, `option-analysis.py:17`, test files
**修复方案:** 统一使用 `sys.path.insert(0, SKILL_DIR)` 模式，SKILL_DIR = `Path(__file__).parent.parent`

**标准化模板 (用于harness目录下所有文件):**
```python
import sys
from pathlib import Path
SKILL_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(SKILL_DIR))
```

**analyze.py 保持包导入不变** (从skill根目录运行时 `from analysis.engine import` 自然可用)

**需改的文件:**
| 文件 | 当前方式 | 改为 |
|------|---------|------|
| backtest.py:16 | `sys.path.insert(0, parent)` | 标准模板 |
| generate_predictions.py:14 | 检查并统一 | 标准模板 |
| option-analysis.py:15-17 | `SKILL_DIR = parent` | 标准模板 |
| test_engine.py:13 | 检查并统一 | 标准模板 |
| test_backtest.py:13 | 检查并统一 | 标准模板 |

---

## Phase 3: LOW Severity (下周修复)

### 3.1 #37 — daily-summary.sh fallback DATA_DIR错误

**文件:** `harness/daily-summary.sh:10`
**当前:** `DATA_DIR="$SKILL_DIR/data"` (不存在)
**修复:** 改为 `DATA_DIR="$SCRIPT_DIR/data"`
```bash
DATA_DIR="$SCRIPT_DIR/data"  # 正确: stock-analysis/harness/data/
```

---

### 3.2 #22 — WACC参数代码与配置重复

**文件:** `engine.py:2957-2959`
**修复:** 删除代码中的default dict内WACC重复值，强制从config读取
```python
wacc_params = get_config('value_trap', 'wacc_params')
if not wacc_params:
    wacc_params = {'risk_free_rate': 0.045, 'market_risk_premium': 0.06,
                   'default_cost_of_debt': 0.05, 'default_tax_rate': 0.25}
```
同时在config.yaml添加注释标注这是唯一数据源。

---

### 3.3 #36 — moat_width字符串'None' vs Python None

**文件:** `engine.py:2912`, `generate_valuation.py:159`
**engine.py 改动:**
```python
else:
    moat_width = None  # 不再用字符串 'None'
    required_margin = None
```

**generate_valuation.py 改动:**
```python
moat_width = moat_data.get('moat_width')  # 不再 or 'None'
if moat_width is None:
    # No moat - skip moat premium or use minimal
    moat_premium = max(moat_premium, 0.0)
```

---

### 3.4 #25 — adjust-metrics权重与回测不匹配

**文件:** `harness/adjust-metrics.py:30-34`
**修复:** 从config.yaml读取权重，与backtest thresholds对齐
```python
thresholds = self.config.get('backtest', {}).get('thresholds', {})
self.metrics_weights = {
    'price_direction': 0.4,
    'target_price': 0.3,
    'recommendation': 0.3
}
# 验证权重与阈值存在对应关系
self.metric_thresholds = thresholds
```

---

### 3.5 #24 — SKILL.md配置路径不存在

**文件:** `SKILL.md:1104-1115`
**修复:** 删除废弃的 "Legacy Parameters" 段落和 `~/.config/stock-analysis/config.json` 引用

---

### 3.6 #35 — 陷阱评分权重总和=90而非100(非分红股85)

**文件:** `engine.py:3066-3083`
**问题:** `dividend_yield` 检查是条件的，非分红股最大只能到85分。
**修复方案:** 对非分红股，将dividend_yield的权重重新分配给其他检查项
```python
if stock_data.dividend_per_share and stock_data.current_price:
    dividend_yield = stock_data.dividend_per_share / stock_data.current_price
    if dividend_yield > 0.08:
        trap_score += trap_config.get('dividend_yield', 15)
        warnings.append(f"Unsustainable dividend yield: {dividend_yield:.1%}")
else:
    # 非分红股: 将dividend权重按比例分配给其他检查
    # 25:20:20:20 → 按比例分配15点 → 各增加 ~3.75:3:3:3
    redistribution = {'roic_vs_wacc': 4, 'fcf_health': 4, 'debt_health': 4, 'earnings_quality': 3}
    for name, bonus in redistribution.items():
        trap_config[name] = trap_config.get(name, 20) + bonus
```

---

### 3.7 #12 — test_trap_actions弱断言

**文件:** `harness/tests/unit/test_engine.py:444`
**当前:** `assert result_high['action'] in ('AVOID', 'AVOID_OR_MINIMAL', 'CAUTION')`
**修复:** 高陷阱股票应严格返回 AVOID 或 AVOID_OR_MINIMAL
```python
assert result_high['action'] in ('AVOID', 'AVOID_OR_MINIMAL'), \
    f"Expected AVOID or AVOID_OR_MINIMAL for high-trap stock, got {result_high['action']}"
assert result_high['trap_score'] >= 30, \
    f"Expected trap_score >= 30 for high-trap stock, got {result_high['trap_score']}"
```

---

## 执行顺序和依赖关系

```
Phase 1 (HIGH - 阻塞所有其他修复)
├── #1  NOPAT修复         ← 无依赖
├── #5  SKILL.md映射统一   ← 依赖 #26 (删除装饰性JSON配置)
├── #9  JSON批量解析       ← 无依赖
└── #18 Portfolio报告      ← 无依赖

Phase 2 (MEDIUM - 可并行)
├── #3  PE基准统一         ← 无依赖
├── #8  估值反转文档       ← 无依赖
├── #11 is_itm修复         ← 无依赖
├── #14 recurring_revenue  ← 依赖 config.yaml 修改
├── #26 仓位配置读取       ← 依赖 config.yaml 修改
├── #34 current_price标记  ← 无依赖
└── #33 import统一         ← 无依赖

Phase 3 (LOW - 可并行)
├── #37 daily-summary.sh  ← 无依赖
├── #22 WACC去重          ← 无依赖
├── #36 moat_width None   ← 无依赖
├── #25 adjust-metrics    ← 无依赖
├── #24 废弃路径删除      ← 依赖 #5 / #26
├── #35 陷阱权重归一化     ← 无依赖
└── #12 测试断言加强      ← 依赖 #1 NOPAT修复后验证
```

## 验证计划

### 单元测试
```bash
cd /Users/Jagger/.agents/skills/stock-analysis
python -m pytest harness/tests/ -v
```

### 集成测试清单
1. `python analysis/analyze.py BABA.US` — 单股票分析
2. `python analysis/analyze.py BABA.US NVDA.US` — 批量分析(#9验证)
3. `python analysis/analyze.py --portfolio --format markdown` — Portfolio报告(#18验证)
4. `python analysis/analyze.py --portfolio --format json` — Portfolio JSON
5. `python analysis/analyze.py --watchlist` — 自选股分析

### 回归检查
- 检查 engine.py 所有 `analysis['symbol']` 访问有无遗漏
- 检查 config.yaml 新增字段是否被 `_default_config()` 覆盖
- 检查 SKILL.md 中所有交叉引用是否一致

## 风险评估

| 修改 | 风险 | 缓解 |
|------|------|------|
| #9 parse_quote改返回类型 | 中 — 下游可能假设返回Dict | 保留单符号返回Dict，新增批量方法 |
| #18 generate_report分支 | 低 — 新增方法不影响原有逻辑 | portfolio dict 有 `positions`+`summary` 无 `symbol` 作为判断 |
| #26 comprehensive_score_to_position读config | 低 — 有fallback | config读取失败时回退到原硬编码值 |
| #1 NOPAT修复 | 中 — 改变ROIC计算结果 | 用NVDA等有EBITDA的股票对比验证 |
