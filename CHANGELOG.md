# Stock Analysis Skill 更新日志

## v2.3.0 - 2026-05-09 🎯 财报数据集成 + 自迭代校验层

### 核心更新

**真实财报数据集成 — 不再基于价格循环推导估值指标。**

之前系统的 EPS 是从 PE 反推的（`current_price / pe_ratio` = 循环论证），营收、FCF、现金、负债等核心财务指标全部为 `None`。本次集成 `longbridge financial-report` 拉取完整三张报表（利润表/资产负债表/现金流量表）。

### 新增功能

#### 1. 财报数据拉取 (`analysis/analyze.py`)
- **`fetch_financials()`** — 调用 `longbridge financial-report`，获取季度（qf）和年度（af）双版本
- **`_extract_financial_data()`** — 解析 IS/BS/CF，提取营收、净利润、EPS、FCF、现金、负债、股东权益
- **`_get_ttm_sum()`** — TTM（滚动 4 季度）求和
- **`_get_yoy_growth()`** — 同比增速计算
- **优先级：年度数据（af）优先** — 避免季度数据缺失导致的错误

#### 2. 数据质量自校验层 (`analysis/analyze.py`)
- **`_validate_financial_data()`** — 每次拉取财报后自动运行，两级校验：
  - **`error`** — 阻断买入信号（缺失关键字段、资产负债表不平）
  - **`warn`** — 仅提示信息（FCF 季度 vs 年度差异、异常 QoQ 波动）
- 校验结果输出到 `data_quality` 字段，透传到评估 JSON

#### 3. 校验联动 (`harness/generate_valuation.py`)
- 当 `data_quality.is_clean == False` 时（存在 error），买入信号降级为 HOLD
- `warn` 级别仅显示 ⚠️ 标识，不阻断正常买入信号
- 校验结果写入评估 JSON 的 `data_quality_warnings` 字段

#### 4. 统一看板加载 (`watchlist_utils.py`)
- **新增 `watchlist_utils.py`** — 单一看板加载入口，所有模块从此读取
- 提供 `load_watchlist()`, `load_watchlist_full()`, `load_watchlist_symbols_by_priority()`
- 所有硬编码看板列表已替换为动态加载

### 数据质量校验检查项

| 检查 | 级别 | 说明 |
|------|------|------|
| TTM 字段完整性 | `error` | 4 个关键字段是否≥3 个有值 |
| EPS 可用性 | `error` | 是否有可用 EPS |
| 资产负债表平衡 | `error` | 资产 ≈ 负债 + 权益（误差<5%）|
| FCF 季度 vs 年度 | `warn` | 季度 TTM 求和与年度值的差异 |
| 异常 QoQ 波动 | `warn` | 营收/净利润/EPS 环比>500% |
| 营收符号异常 | `warn` | 负营收 + 正净利润 |

### 修复的 Bug

#### Bug 1: 循环 EPS 推导
- **问题：** EPS = 现价 / PE，然后用这个 EPS 算 P/E → 循环论证
- **修复：** 从 `longbridge financial-report` 获取真实 EPS（TTM 求和）
- **效果：** AAPL P/E 从 146x（单季 EPS 误算）变为 35.5x（TTM 正确值）

#### Bug 2: DUK FCF 误判（季度数据缺失）
- **问题：** DUK Q2 季度数据为空，TTM 求和只加了 3 个季度 → FCF 看起来 -$1.19B
- **修复：** 改用年度报表（af）计算 TTM → FCF 实际 +$269M
- **校验层捕获：** `fcf_qf_vs_af` 检查发现 196% 差异，标记 warn

#### Bug 3: COIN/PLTR 虚假买入信号
- **问题：** PE 分位 N/A 时，增长溢价把核心价值推高 → 现价看起来被低估
- **修复：** PE 分位 N/A 时，核心价值=现价，买入信号封顶为 HOLD
- **效果：** COIN $201（高于 $168 买入目标）不再喊买

### 修改的文件

| 文件 | 修改内容 |
|------|---------|
| `watchlist_utils.py` | **新增** — 统一看板加载模块 |
| `analysis/analyze.py` | 新增 `fetch_financials()`, `_extract_financial_data()`, `_validate_financial_data()`，更新 `prepare_stock_data()`, `analyze_symbol()` |
| `harness/generate_valuation.py` | 集成 `data_quality` 校验联动，显示 ⚠️ 警告 |
| `harness/backtest.py` | 动态加载看板 |
| `harness/backtest-analysis.py` | 动态加载看板 |
| `harness/generate_predictions.py` | 动态加载看板 |
| `harness/validation_framework.py` | 动态加载看板 |
| `harness/daily-summary.sh` | 从 `watchlist.json` 动态加载 |
| `harness/config.yaml` | 移除硬编码看板 |
| `SKILL.md` | 引用 `watchlist.json` 替代内联列表 |
| `CHANGELOG.md` | 本次更新 |

### 破坏性变更

- `harness/config.yaml` 的 `watchlist` 字段默认为空（`[]`），从 `references/watchlist.json` 自动加载
- 要覆盖看板，在 config.yaml 中设置非空列表即可

### 升级指南

无需手动操作。安装依赖：
```bash
cd /Users/Jagger/.agents/skills/stock-analysis
pip install -r analysis/requirements.txt
```

---

### 新增文件

| 文件路径 | 说明 |
|---------|------|
| `analysis/engine.py` | 核心分析引擎（2200+行） |
| `analysis/analyze.py` | 命令行分析脚本 |
| `analysis/requirements.txt` | Python依赖列表 |
| `references/risk-metrics.md` | 风险指标详细文档 |
| `references/valuation-metrics.md` | 估值指标详细文档 |
| `references/technical-indicators.md` | 技术指标详细文档 |
| `references/multi-factor-model.md` | 多因子模型详细文档 |

### Python API

```python
from analysis.engine import StockData, StockAnalysisEngine

# 创建股票数据
stock_data = StockData(
    symbol="NVDA.US",
    prices=[450, 460, 455, 470, 475, 480, 490],
    current_price=490,
    market_cap=1200000000000,
    sector="Technology",
    eps=12.5,
    revenue=60000000000,
    # ... 更多财务数据
)

# 执行综合分析
engine = StockAnalysisEngine()
analysis = engine.analyze_stock(stock_data)

# 生成报告
report = engine.generate_report(analysis, format='markdown')
```

### 分析报告示例

```markdown
# Stock Analysis Report: NVDA.US

## Overall Assessment
**Recommendation:** BUY (MEDIUM-HIGH confidence)
**Overall Score:** 72.5/100

### Score Breakdown:
- Risk Score: 65/100 (Moderate-High Risk)
- Valuation Score: 45/100 (Undervalued)
- Technical Score: 78/100 (Bullish)
- Factor Score: 82/100 (Strong)

## Risk Analysis
- Sharpe Ratio: 1.85
- Maximum Drawdown: -22.5%
- Historical Volatility: 35.2%
- Beta: 1.45 (Aggressive)

## Valuation Analysis
- P/E Ratio: 39.2x
- PEG Ratio: 0.49 (Undervalued given growth)
- FCF Yield: 1.5%

## Technical Analysis
- RSI: 62.5 (Bullish momentum)
- MACD: Bullish crossover confirmed

## Multi-Factor Analysis
- Quality: 85/100
- Value: 55/100
- Growth: 95/100
- Momentum: 88/100
```

### 技术细节

- **计算方法：** NumPy向量化计算，高效快速
- **数据要求：** 风险指标至少60天，技术指标建议200天
- **性能：** 单股分析~1-2秒，自选股分析~10-15秒
- **兼容性：** 与Longbridge CLI无缝集成

### 破坏性变更

无。完全向后兼容。

### 升级指南

1. **安装依赖**
   ```bash
   cd /Users/Jagger/.agents/skills/stock-analysis/analysis
   pip install -r requirements.txt
   ```

2. **测试运行**
   ```bash
   python analyze.py --watchlist
   ```

3. **查看API文档**
   - `references/risk-metrics.md`
   - `references/valuation-metrics.md`
   - `references/technical-indicators.md`
   - `references/multi-factor-model.md`

### 贡献者

- AI Assistant (设计与实现)

---

## v2.1.2 - 2026-04-21 🔧 修正 VIX 符号

### 问题
VIX 指数符号 `.^VIX.US` 无法获取数据。

### 解决方案
改用 `VIXM.US`（VIX Mid-Term Futures ETF），这是 VIX 的可交易代理。

**VIXM 当前数据：**
- 价格: 15.86
- 解释: 追踪 VIX 中期期货，反映市场波动预期

### 修改文件

| 文件 | 修改内容 |
|------|---------|
| SKILL.md | `.^VIX.US` → `VIXM.US` |
| references/multi-factor-sentiment.md | 所有 VIX 引用改为 VIXM |
| references/market-regime.md | VIX → VIXM |

### 使用方法

```bash
# 获取波动率指标
longbridge quote VIXM.US

# 解读
# VIXM < 15: 市场自满/贪婪 → 减仓
# VIXM 15-20: 正常波动 → 中性
# VIXM 20-30: 担忧上升 → 可买入
# VIXM > 30: 恐惧 → 激进买入
```

---

## v2.1.1 - 2026-04-21 🔴 严重Bug修复：缺口检测逻辑错误

### 问题发现
用户报告缺口检测结果错误：
1. PLTR 在 4/17 和 4/20 **没有缺口**，但被错误标记
2. TSLA 在 4/17 和 4/20 **没有缺口**，但被错误标记
3. COIN 只有在 4/13-4/14 有缺口，其他日期被错误标记

### 根因分析

**❌ 错误逻辑（已修复）：**
```
缺口 = (今日开盘价 - 昨日收盘价) / 昨日收盘价 ≥ 1%
```

**问题：**
- Open-Close 差距 ≥ 1% 不等于真正的缺口
- 即使开盘跳空，盘中价格可能重叠，这不是缺口
- 例如：昨日收100，今日开102（+2%），但盘中最低99 → 不是缺口

**✅ 正确逻辑：**
```
向上缺口 = 今日最低价 > 昨日最高价（价格区间无重叠）
向下缺口 = 今日最高价 < 昨日最低价（价格区间无重叠）
```

### 验证结果

| 股票 | 日期 | 昨日High | 今日Low | 是否缺口 | 之前错误 |
|------|------|---------|---------|---------|---------|
| PLTR | 4/17 | 145.55 | 143.30 | ❌ 无 | ✅ 错标 |
| PLTR | 4/20 | 148.28 | 143.83 | ❌ 无 | ✅ 错标 |
| TSLA | 4/17 | 394.06 | 391.65 | ❌ 无 | ✅ 错标 |
| TSLA | 4/20 | 409.28 | 388.33 | ❌ 无 | ✅ 错标 |
| COIN | 4/14 | 175.01 | 180.00 | ✅ 有 | 正确 |

### 修复内容

**修改文件：** `references/gap-theory.md`

**核心修改：**

1. **Gap Definition** - 完全重写，使用 High/Low 逻辑
2. **detect_gaps()** - 改用 `today_low > prev_high` 和 `today_high < prev_low`
3. **detect_all_gaps_systematic()** - 同上
4. **检查清单** - 更新为 High/Low 计算步骤
5. **表格输出** - 显示 High/Low 而不是 Open/Close

### jq 查询模板（已更新）

```bash
longbridge kline history SYMBOL.US --start YYYY-MM-DD --period day --format json | \
jq -r '
  . as $data |
  range(1; $data | length) |
  select(
    (($data[.].low | tonumber) > ($data[.-1].high | tonumber)) or
    (($data[.].high | tonumber) < ($data[.-1].low | tonumber))
  ) |
  {
    date: $data[.].time[0:10],
    prev_high: ($data[.-1].high | tonumber),
    prev_low: ($data[.-1].low | tonumber),
    today_high: ($data[.].high | tonumber),
    today_low: ($data[.].low | tonumber),
    direction: (if ($data[.].low | tonumber) > ($data[.-1].high | tonumber) then "UP" else "DOWN" end)
  }
' | jq -s 'sort_by(.date) | .[]'
```

### 影响

- **严重性：** 高 - 缺口分析是技术分析的重要组成部分
- **受影响功能：** Gap Theory 分析、支撑/阻力判断
- **用户影响：** 之前的缺口分析报告可能包含错误数据

### 建议

- **重新运行** 所有使用缺口分析的股票报告
- **验证** 之前的交易决策是否基于错误数据

---

## v2.1.0 - 2026-04-21 🔧 系统化缺口检测

### 问题
用户两次报告缺口检测遗漏：
1. CEG 4/8 缺口（+3.82%）遗漏
2. BABA 4/8（+7.01%）和 4/17（+1.85%）缺口遗漏

### 根因分析
- 手动观察容易遗漏
- 只关注大缺口
- 没有系统化表格输出
- 缺少验证机制

### 解决方案
在 `references/gap-theory.md` 添加：

1. **缺口检测检查清单**（5步强制流程）
   - 必须逐日计算
   - 必须表格输出
   - 必须验证签名

2. **系统化检测函数**
   ```python
   def detect_all_gaps_systematic(kline_data, threshold=1.0)
   def print_gap_table(gaps, symbol, current_price)
   ```

3. **验证模板**
   - jq 查询模板（已测试通过）
   - 表格输出格式
   - 强制验证签名机制

### 测试结果 ✅

所有股票缺口检测通过：

| 股票 | 4/8 缺口 | 4/17 缺口 | 状态 |
|------|---------|----------|------|
| BABA | +7.01% | +1.85% | ✅ 已捕获 |
| CEG | +3.82% | +1.63% | ✅ 已捕获 |
| NVDA | +3.59% | - | ✅ 已捕获 |
| COIN | +7.26% | +2.69% | ✅ 已捕获 |
| TSLA | +4.94% | +1.81% | ✅ 已捕获 |
| PLTR | +3.13% | +1.79% | ✅ 已捕获 |

### jq 查询模板（已验证）

```bash
longbridge kline history SYMBOL.US --start YYYY-MM-DD --period day --format json | \
jq -r '
  . as $data |
  range(1; $data | length) |
  select(
    (((($data[.].open | tonumber) - ($data[.-1].close | tonumber)) / 
      ($data[.-1].close | tonumber) * 100) | abs) >= 1.0
  ) |
  {
    date: $data[.].time[0:10],
    prev_close: ($data[.-1].close | tonumber | . * 100 | round / 100),
    today_open: ($data[.].open | tonumber | . * 100 | round / 100),
    gap_pct: (((($data[.].open | tonumber) - ($data[.-1].close | tonumber)) / 
      ($data[.-1].close | tonumber) * 100) * 100 | round / 100),
    direction: (if ($data[.].open | tonumber) > ($data[.-1].close | tonumber) 
      then "UP" else "DOWN" end)
  }
' | jq -s 'sort_by(.date) | .[]'
```

### 文件修改
- `references/gap-theory.md` - 添加系统化检测协议

---

## v2.0.0 - 2026-04-20 🎉 重大更新

### 🎯 核心创新：动态仓位管理

**问题：** 原有固定仓位比例（如80%）不适应市场变化，在极端环境下风险控制失效。

**解决方案：** 根据市场情绪动态调整总仓位，实践"逆向投资"原则。

#### 新增功能

**1. 动态仓位模型**

| 市场状态 | 情绪指数 | 总仓位 | 现金储备 | 操作策略 |
|---------|---------|--------|---------|---------|
| 极度贪婪 | 70-100 | 10-30% | 70-90% | 激进卖出 |
| 贪婪 | 60-70 | 30-50% | 50-70% | 选择性卖出 |
| 中性 | 40-60 | 50-70% | 30-50% | 持有观望 |
| 恐惧 | 30-40 | 70-85% | 15-30% | 选择性买入 |
| 极度恐惧 | 0-30 | 85-100% | 0-15% | 激进买入 |

**2. 市场环境分析**
- 新增 `references/market-regime.md` 
- 详细定义5种市场环境
- 提供每种环境下的投资策略

**3. 动态现金管理**
- 现金储备不再固定10%
- 根据市场环境动态调整（5%-90%）
- 在贪婪时积累现金，恐惧时部署现金

**4. 智能仓位调整**
- 自动计算目标仓位与当前仓位差异
- 生成具体的买卖操作建议
- 分批执行，避免市场冲击

---

### 📁 文件更新

#### 新增文件

1. **`references/market-regime.md`** (新建)
   - 市场环境分类
   - 情绪-仓位映射详解
   - 多因子确认机制
   - 仓位调整工作流

#### 修改文件

2. **`references/position-management.md`** (重大修改)
   - 新增"Dynamic Position Sizing Based on Market Sentiment"章节
   - 修改"Rule 3: Cash Reserve"为动态模型
   - 添加详细的实现公式和示例

3. **`SKILL.md`** (重大修改)
   - 重写"Step 5: Position Management Recommendations"
   - 新增"Step 5.1: Determine Market Regime"
   - 新增"Step 5.2: Calculate Target Position"
   - 新增"Step 5.3: Select Stocks for Adjustment"
   - 新增"Step 5.4: Individual Stock Sizing"
   - 新增"Step 5.5: Generate Recommendations"
   - 更新"Configuration"章节

4. **`config.json`** (重大修改)
   - 移除固定的`min_cash_reserve`
   - 新增`dynamic_position_sizing`配置
   - 新增`sentiment_to_position`映射表
   - 新增`risk_management`参数

5. **`README.md`** (重大修改)
   - 新增"动态仓位管理详解"章节
   - 更新核心功能列表
   - 添加实战案例

---

### 🔄 行为变更

#### Before (v1.x)

```
固定规则：
- 现金储备：≥ 10%（硬编码）
- 总仓位：~80%（隐含）
- 不考虑市场环境
```

#### After (v2.0)

```
动态规则：
- 现金储备：5%-90%（根据情绪动态调整）
- 总仓位：10%-100%（根据情绪动态调整）
- 考虑市场环境、情绪、估值等多个因子
```

---

### 💡 使用示例

#### 场景1：市场极度贪婪（情绪=75）

**v1.x行为：**
```
建议：维持80%持仓，保持10%现金
问题：在市场高点风险暴露过大
```

**v2.0行为：**
```
分析：
- 市场状态：极度贪婪
- 目标仓位：20%
- 目标现金：80%

建议：
1. 卖出60%持仓
2. 保留最高质量股票
3. 积累大量现金等待机会
```

#### 场景2：市场极度恐惧（情绪=25）

**v1.x行为：**
```
建议：维持80%持仓，保持10%现金
问题：错过最佳买入机会
```

**v2.0行为：**
```
分析：
- 市场状态：极度恐惧
- 目标仓位：95%
- 目标现金：5%

建议：
1. 部署现金买入优质股票
2. 抓住市场恐慌带来的机会
3. 保留5%应急现金
```

---

### ⚙️ 配置迁移

**v1.x配置：**
```json
{
  "min_cash_reserve": 10,
  "default_allocation": 10
}
```

**v2.0配置：**
```json
{
  "dynamic_position_sizing": {
    "enabled": true,
    "sentiment_to_position": {
      "extreme_fear": {
        "sentiment_range": [0, 30],
        "target_position_pct": 95,
        "target_cash_pct": 5
      },
      ...
    }
  }
}
```

---

### 🎯 核心优势

1. **风险控制更智能**
   - 在市场高点自动减仓
   - 在市场低点自动加仓
   - 避免"追涨杀跌"

2. **收益机会更大**
   - 在恐慌时积累筹码
   - 在狂热时锁定利润
   - 实践逆向投资

3. **心理压力更小**
   - 系统自动提示买卖
   - 减少情绪干扰
   - 提供明确执行计划

4. **适应性更强**
   - 适应不同市场环境
   - 自动调整风险敞口
   - 灵活应对突发变化

---

### ⚠️ 注意事项

1. **渐进式调整**
   - 不要一次性完成所有仓位调整
   - 分3-5个交易日执行
   - 监控市场变化

2. **多因子确认**
   - 不要仅凭情绪指数决策
   - 结合技术、估值、新闻
   - 等待多个信号确认

3. **硬性约束**
   - 始终保持≥5%现金
   - 始终保持≥5%持仓
   - 保留应急储备金

4. **纪律执行**
   - 严格遵守规则
   - 记录决策理由
   - 定期复盘优化

---

### 📚 文档结构

```
stock-analysis/
├── SKILL.md                          # 主文档
├── README.md                         # 使用说明
├── CHANGELOG.md                      # 本文件
└── references/
    ├── market-regime.md              # 🆕 市场环境分析
    ├── position-management.md        # ✏️ 仓位管理（已更新）
    ├── watchlist.json                # 自选股列表
    ├── gap-theory.md                 # 缺口理论
    └── value-zone.md                 # 价值区间
```

---

### 🔜 未来计划

- [ ] 支持用户自定义情绪-仓位映射
- [ ] 添加更多市场环境指标（VIX、A/D等）
- [ ] 实现自动化交易执行
- [ ] 添加历史回测功能
- [ ] 支持多账户管理

---

### 📞 反馈

如有问题或建议，请提交issue或联系开发者。

---

**更新时间：** 2026-04-20  
**版本：** v2.0.0  
**兼容性：** 完全向后兼容v1.x配置（自动迁移）
