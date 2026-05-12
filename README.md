# Stock Analysis Skill

智能股票分析系统，整合市场情绪、缺口理论、价值区间和仓位管理策略。

## 文件结构

```
stock-analysis/
├── SKILL.md                          # 主文档 - 完整的分析流程
├── README.md                         # 本文件
├── CHANGELOG.md                      # 更新日志
├── analysis/                         # 分析引擎 (v3.0: 三层估值)
│   ├── engine.py                     # 核心分析引擎
│   ├── analyze.py                    # 命令行分析脚本
│   └── requirements.txt              # Python依赖
├── harness/                          # 持续改进系统
│   ├── harness-run.sh                # 主运行脚本
│   ├── daily-summary.sh              # 每日总结
│   ├── backtest.py                   # 回测脚本
│   └── adjust-metrics.py             # 指标调整
├── data/                             # 数据存储
│   ├── daily/                        # 每日报告
│   ├── predictions/                  # 预测记录
│   ├── backtests/                    # 回测结果
│   └── metrics/                      # 性能指标
└── references/                       # 参考文档
    ├── watchlist.json                # 固定自选股列表
    ├── gap-theory.md                 # 缺口理论详细说明
    ├── value-zone.md                 # 价值区间分析方法
    ├── position-management.md        # 仓位管理策略
    ├── risk-metrics.md               # 风险指标详解 (v2.0新增)
    ├── valuation-metrics.md          # 估值指标详解 (v2.0新增)
    ├── technical-indicators.md       # 技术指标详解 (v2.0新增)
    ├── multi-factor-model.md         # 多因子模型详解 (v2.0新增)
    ├── moat-analysis.md              # 护城河分析
    ├── roic-analysis.md              # ROIC分析
    ├── value-trap-detection.md       # 价值陷阱检测
    ├── multi-factor-sentiment.md     # 多因子市场情绪
    ├── market-regime.md              # 市场状态分析
    └── conflict-resolution.md        # 策略冲突解决
```

## 🎯 固定自选股列表

本skill维护一个固定的自选股列表，包含6只重点关注的股票：

| 代码 | 名称 | 行业 | 描述 |
|------|------|------|------|
| BABA.US | 阿里巴巴 | Technology | 中国电商和云计算巨头，AI布局领先 |
| NVDA.US | 英伟达 | Technology | AI芯片龙头，数据中心业务强劲 |
| TSLA.US | 特斯拉 | Consumer Discretionary | 电动车龙头，自动驾驶和储能业务 |
| CEG.US | 星座能源 | Utilities | 核能发电公司，AI数据中心供电合作 |
| COIN.US | Coinbase | Financials | 加密货币交易所，受益于加密市场回暖 |
| PLTR.US | Palantir | Technology | 大数据分析公司，AI平台增长强劲 |

**修改自选股列表：**
编辑 `references/watchlist.json` 文件，添加或删除股票。

**行业分布：**
- Technology: 3只 (BABA, NVDA, PLTR)
- Consumer Discretionary: 1只 (TSLA)
- Utilities: 1只 (CEG)
- Financials: 1只 (COIN)

## 快速开始

### 1. 确保已安装 Longbridge CLI

```bash
# 检查是否安装
longbridge --version

# 如果未安装，请访问：https://open.longbridge.com
```

### 2. 配置参数（可选）

编辑 `~/.config/stock-analysis/config.json` 调整参数：

```json
{
  "gap_threshold": 1.0,          // 缺口识别阈值（%）
  "max_position_pct": 15,        // 单只股票最大仓位（%）
  "sector_max_pct": 30,          // 行业最大集中度（%）
  "min_cash_reserve": 10,        // 最小现金储备（%）
  "default_allocation": 10,      // 默认仓位配置（%）
  "analysis_period_days": 90     // K线分析周期（天）
}
```

### 3. 使用 Skill

在任何支持 AI 的环境中，使用以下触发词：

**🎯 快速自选股分析（推荐）：**
- "分析自选股"
- "analyze watchlist"
- "我的自选股"

**中文触发词：**
- "分析我的持仓"
- "大盘怎么样"
- "这个股票能买吗"
- "要不要减仓"
- "缺口在哪里"
- "自选股分析"

**英文触发词：**
- "Analyze my portfolio"
- "Market sentiment"
- "Should I buy [SYMBOL]"
- "Position sizing"
- "Gap analysis"
- "Watchlist review"

## 核心功能

### 1. 动态仓位管理 🎯 **核心创新**
- **根据市场情绪动态调整总仓位**
- 极度贪婪 → 总仓位10-30%，现金70-90%
- 贪婪 → 总仓位30-50%，现金50-70%
- 中性 → 总仓位50-70%，现金30-50%
- 恐惧 → 总仓位70-85%，现金15-30%
- 极度恐惧 → 总仓位85-100%，现金0-15%
- **逆向投资原则：在他人贪婪时恐惧，在他人恐惧时贪婪**

### 2. 市场情绪分析
- 获取市场情绪指数（0-100）
- 分析主要指数走势
- 汇总市场关键新闻
- **作为仓位调整的核心依据**

### 3. 自选股分析（固定列表）
- 分析固定的6只自选股（BABA, NVDA, TSLA, CEG, COIN, PLTR）
- 获取实时行情和最新新闻
- 分析技术形态和催化剂
- 提供买入/持有/卖出建议

### 4. 持仓价值区间分析
- 技术面：支撑/阻力/公允价值
- 基本面：P/E、P/B估值区间
- 综合分析当前价格位置

### 5. 缺口理论分析
- 自动识别≥1%的缺口
- 分类缺口类型（突破/中继/衰竭/普通）
- 判断缺口支撑/阻力作用
- 计算缺口填充概率

### 6. 风险管理
- 严格止损纪律
- 分批建仓/减仓策略
- 行业分散化
- 单股仓位限制（≤15%）

---

## 🎯 动态仓位管理详解

### 核心理念

**传统问题：** 固定仓位比例（如80%）不适应市场变化，在极端环境下风险极高。

**解决方案：** 根据市场情绪动态调整总仓位，实践逆向投资原则。

### 情绪-仓位映射表

| 市场状态 | 情绪指数 | 总仓位 | 现金储备 | 操作策略 |
|---------|---------|--------|---------|---------|
| 🔴 **极度贪婪** | 70-100 | **10-30%** | 70-90% | 激进卖出，保留最高质量股票 |
| 🟡 **贪婪** | 60-70 | **30-50%** | 50-70% | 选择性卖出，逐步减仓 |
| ⚪ **中性** | 40-60 | **50-70%** | 30-50% | 持有观望，择机调整 |
| 🟢 **恐惧** | 30-40 | **70-85%** | 15-30% | 选择性买入，逢低布局 |
| 🟢 **极度恐惧** | 0-30 | **85-100%** | 0-15% | 激进买入，抓住机会 |

### 实战案例

#### 案例1：市场从贪婪转向恐惧

**场景：**
- 当前情绪：70（贪婪）
- 持仓：20%（$31,444）
- 现金：80%（$125,776）

**市场突变：情绪跌至30（恐惧）**

**分析：**
```
情绪变化：70 → 30 (下跌40点)
目标仓位：20% → 80%
需要调整：增加持仓60%

可部署资金：$125,776 × (60% / 80%) = $94,332
保留现金：$125,776 - $94,332 = $31,444

新持仓：$31,444 + $94,332 = $125,776 (80%)
新现金：$31,444 (20%)
```

**操作步骤：**
1. 第1天：买入$30,000（优质股）
2. 第2天：买入$30,000
3. 第3天：买入$34,332
4. 总计：买入$94,332

#### 案例2：市场从恐惧转向贪婪

**场景：**
- 当前情绪：25（极度恐惧）
- 持仓：95%（$149,359）
- 现金：5%（$7,861）

**市场突变：情绪涨至75（极度贪婪）**

**分析：**
```
情绪变化：25 → 75 (上涨50点)
目标仓位：95% → 20%
需要调整：减少持仓75%

需要卖出：$157,220 × 75% = $117,915
保留持仓：$149,359 - $117,915 = $31,444

新持仓：$31,444 (20%)
新现金：$7,861 + $117,915 = $125,776 (80%)
```

**操作步骤：**
1. 第1天：卖出$40,000（低质量股）
2. 第2天：卖出$40,000
3. 第3天：卖出$37,915
4. 总计：卖出$117,915

### 关键原则

**1. 渐进式调整**
- 不要一次性完成所有调整
- 分3-5个交易日逐步执行
- 减少市场冲击成本

**2. 多重确认**
- 不要仅凭情绪指数决策
- 结合技术指标、估值、新闻
- 等待多个信号共振

**3. 风险硬约束**
- 即使在极度恐惧时，也保持5%现金
- 即使在极度贪婪时，也保持至少5%持仓
- 永远保留应急储备金

**4. 情绪纪律**
- 严格遵守规则，不被情绪左右
- 记录每次决策理由，定期复盘
- 相信系统，不要试图择时

---

## 📊 快速自选股分析示例

**使用方法：** 说"分析自选股"或"analyze watchlist"

**示例输出：**

```markdown
# 📊 自选股快速分析报告
日期: 2026-04-20

## 市场概况
- 情绪指数: 48 (中性)
- 主要指数: S&P 500 +1.2%, NASDAQ +1.8%

## 自选股概览
| 股票 | 价格 | 涨跌 | 成交量 | 区间 | 建议 | 评分 |
|------|------|------|--------|------|------|------|
| BABA.US | $141.01 | +1.7% | 12.8M | 支撑区 | 买入 | 8/10 |
| NVDA.US | $875.32 | +2.3% | 45.2M | 阻力区 | 持有 | 7/10 |
| TSLA.US | $175.89 | -0.8% | 98.5M | 公允价值 | 持有 | 6/10 |
| CEG.US | $245.67 | +1.2% | 3.2M | 支撑区 | 买入 | 8/10 |
| COIN.US | $215.34 | +3.5% | 15.7M | 超买区 | 减持 | 5/10 |
| PLTR.US | $22.45 | +0.5% | 28.9M | 支撑区 | 买入 | 7/10 |

## 详细分析

### BABA.US - 阿里巴巴 ⭐⭐⭐⭐
**价格状态:** $141.01 (+1.7%)
- 52周区间: $66 - $125
- 成交量: 12.8M (高于均值)

**催化剂:**
- AI大模型密集发布（Qwen3.6-Max, Fun-ASR1.5）
- 蚂蚁消金年报超预期
- 4月22日重要消息待公布

**建议:** 🟢 买入
- 理由: 基本面改善，AI布局领先，催化剂密集
- 入场价: $138-142
- 止损: $130
- 目标价: $150-155

---

### NVDA.US - 英伟达 ⭐⭐⭐⭐
[详细分析...]

---

[其他股票分析...]
```

**分析时间：** 约3-5分钟
**数据来源：** Longbridge CLI实时数据

## 完整持仓分析示例

```
# 投资组合分析报告
日期: 2026-04-20 15:30

## 市场概况
- 情绪指数: 45 (谨慎乐观)
- 主要指数: 标普500 +1.2%, 纳指 +1.8%, 道指 +0.9%
- 关键催化剂: 美联储维持利率不变，科技股财报超预期

## 持仓概览
| 股票 | 数量 | 价值 | 盈亏 | 仓位% | 区间 | 建议 |
|------|------|------|------|-------|------|------|
| AAPL.US | 100 | $18,500 | +12% | 12.3% | 阻力区 | 减持 |
| TSLA.US | 50 | $12,000 | -5% | 8.0% | 支撑区 | 持有 |
| NVDA.US | 30 | $9,500 | +25% | 6.3% | 公允价值 | 持有 |

## 详细分析

### AAPL.US
**当前状态：**
- 价格: $185.50 (+0.8%)
- 52周区间: $164 - $199
- 成交量: 52M (20日均值 48M)

**价值区间：**
- 支撑: $170-175 (成交量聚集区)
- 公允价值: $175-182 (均线交汇)
- 阻力: $188-195 (前高区域)

**缺口分析：**
- 最近缺口: $182-$185 (向上，突破型，未填补)
- 距离: 当前价格已超过缺口
- 作用: 支撑
- 缺口类型: 突破缺口
- 填补概率: 低

**估值：**
- 市盈率: 28.5 (行业均值 25.2)
- 市净率: 47.8
- EPS增长: +8%

**新闻催化剂：**
1. [04-18] 苹果发布AI新功能，市场反应积极
2. [04-15] 供应链报告显示iPhone销量稳定

**建议：**
- 操作: 减持
- 目标仓位: $12,000 (8% of 组合)
- 行动: 卖出约 $6,500 (35股)
- 理由: 接近阻力区，市盈率略高，建议部分获利了结
- 止损: 不适用（减仓而非清仓）

---

## 组合层面建议

1. **风险评估：**
   - 集中度风险: 中等
   - 行业敞口: 科技 70%, 消费 20%, 金融 10%
   - 现金仓位: 15%

2. **建议再平衡：**
   - 卖出: AAPL $6,500 (接近阻力，估值偏高)
   - 买入: 可考虑增加防御性股票（现金充足）
   - 保留现金: $15,000 (等待机会)

3. **自选股关注：**
   - MSFT.US: 技术面形成支撑，基本面稳健
   - GOOGL.US: 回调至公允价值区间，可考虑建仓
```

## 技术细节

### 数据来源
- **市场数据：** Longbridge CLI (`longbridge quote`, `longbridge kline history`)
- **持仓数据：** Longbridge CLI (`longbridge positions`, `longbridge portfolio`)
- **新闻资讯：** Longbridge CLI (`longbridge news`, `longbridge topics`)
- **情绪指数：** Longbridge CLI (`longbridge market-temp`)

### 缺口识别算法
详见 [references/gap-theory.md](references/gap-theory.md)

### 价值区间计算
详见 [references/value-zone.md](references/value-zone.md)

### 仓位管理规则
详见 [references/position-management.md](references/position-management.md)

## 注意事项

1. **教育用途：** 本skill提供的分析和建议仅供参考，不构成投资建议
2. **数据延迟：** Longbridge数据可能有延迟，请以券商实际数据为准
3. **风险提示：** 投资有风险，决策需谨慎
4. **配置调整：** 请根据个人风险承受能力调整配置参数

## 🚀 高级分析引擎 (v2.0新增)

### 概述

v2.0版本新增完整的量化分析引擎，提供专业级的风险、估值、技术和多因子分析。

### 安装

```bash
cd /Users/Jagger/.agents/skills/stock-analysis/analysis
pip install -r requirements.txt
```

### 快速使用

**命令行：**
```bash
# 分析单个股票
python analyze.py AAPL.US

# 分析自选股
python analyze.py --watchlist

# 分析持仓
python analyze.py --portfolio

# 保存报告
python analyze.py NVDA.US -o report.md
```

**Python API：**
```python
from analysis.engine import StockData, StockAnalysisEngine

stock_data = StockData(
    symbol="AAPL.US",
    prices=[150, 152, 151, 153, 155],  # 历史价格
    current_price=155,
    market_cap=2500000000000,
    sector="Technology",
    eps=6.5
)

engine = StockAnalysisEngine()
analysis = engine.analyze_stock(stock_data)
report = engine.generate_report(analysis, format='markdown')
```

### 新增功能

#### 1. 风险指标
- **Sharpe Ratio** - 风险调整后收益
- **Maximum Drawdown** - 最大回撤
- **Sortino Ratio** - 下行风险调整收益
- **Beta Coefficient** - 市场敏感性
- **Value at Risk (VaR)** - 风险价值
- **Historical Volatility** - 历史波动率
- **Calmar Ratio** - 回撤调整收益

#### 2. 估值指标
- **P/E Ratio** - 市盈率（行业调整）
- **PEG Ratio** - 市盈增长比
- **EV/EBITDA** - 企业价值倍数
- **P/FCF** - 自由现金流倍数
- **FCF Yield** - 自由现金流收益率
- **Graham Intrinsic Value** - 格雷厄姆内在价值
- **Valuation Score** - 综合估值评分

#### 3. 技术指标
- **Moving Averages** - 移动平均线（SMA/EMA）
- **RSI** - 相对强弱指标
- **MACD** - 指数平滑异同移动平均线
- **Bollinger Bands** - 布林带
- **Stochastic Oscillator** - 随机指标
- **ATR** - 平均真实波幅
- **Technical Score** - 技术评分

#### 4. 多因子模型
- **Quality Factor** - 质量因子（ROE、毛利率、盈利稳定性）
- **Value Factor** - 价值因子（P/E、EV/EBITDA、FCF Yield）
- **Growth Factor** - 成长因子（营收增长、EPS增长）
- **Momentum Factor** - 动量因子（价格动量、盈利动量）
- **Low Volatility Factor** - 低波动因子
- **Composite Factor Score** - 综合因子评分

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
- Sharpe Ratio: 1.85 (Good)
- Maximum Drawdown: -22.5%
- Historical Volatility: 35.2%
- Beta: 1.45 (Aggressive)
- 95% VaR: -3.2%

## Valuation Analysis
- P/E Ratio: 39.2x (High for sector)
- PEG Ratio: 0.49 (Undervalued given growth)
- FCF Yield: 1.5%

## Technical Analysis
- RSI: 62.5 (Bullish momentum)
- MACD: Bullish crossover
- Price above 50-day and 200-day MA

## Multi-Factor Analysis
- Quality: 85/100 (Excellent ROE and margins)
- Value: 55/100 (Fair given growth)
- Growth: 95/100 (Exceptional growth)
- Momentum: 88/100 (Strong price momentum)
- Low Volatility: 45/100 (Higher volatility)
```

### 投资策略支持

| Strategy | Best For | Key Characteristics |
|----------|----------|---------------------|
| **Quality-Value** | Long-term investors | Focus on quality and value, conservative |
| **Growth-Momentum** | Growth investors | High growth focus, trend following |
| **Balanced** | Most investors | Diversified factor exposure |
| **Defensive** | Risk-averse | Low volatility, quality focus |
| **Aggressive Growth** | High-risk tolerance | Maximum growth exposure |

### 文件结构

```
stock-analysis/
├── analysis/
│   ├── engine.py           # 核心分析引擎
│   ├── analyze.py          # 命令行分析脚本
│   └── requirements.txt    # Python依赖
├── references/
│   ├── risk-metrics.md     # 风险指标详解
│   ├── valuation-metrics.md # 估值指标详解
│   ├── technical-indicators.md # 技术指标详解
│   └── multi-factor-model.md # 多因子模型详解
├── SKILL.md                # 主文档
└── README.md               # 本文件
```

### 性能指标

- **单股分析时间：** ~1-2秒
- **自选股分析（6只）：** ~10-15秒
- **数据要求：** 200天历史数据最佳
- **计算方法：** NumPy向量化计算

### API参考

详细API文档请参考：
- [references/risk-metrics.md](references/risk-metrics.md)
- [references/valuation-metrics.md](references/valuation-metrics.md)
- [references/technical-indicators.md](references/technical-indicators.md)
- [references/multi-factor-model.md](references/multi-factor-model.md)

---

## 扩展建议

### 添加更多指标
可以在 `SKILL.md` 中添加：
- RSI/MACD等技术指标
- 期权PCR比率
- 机构持仓变化

### 集成其他数据源
- 财报数据（SEC filings）
- 社交媒体情绪
- 宏观经济指标

### 自动化执行
- 连接交易API自动下单
- 设置价格提醒
- 生成定期报告
- **每日harness系统** - 自动复盘和指标调整 (见SKILL.md中Harness部分)

## 更新日志

- **v3.0** (2026-05-12): 🎯 三层估值引擎 + 行业调整 + 回测修复
  - ✨ 三层估值模型：PE百分位锚点 + 增长溢价 + 护城河溢价（加法，25%上限）
  - ✨ 增长/护城河溢价从乘法(+56%)改为加法(+25%上限)，消除系统性高估
  - ✨ PE锚点缺失时P/S比率→行业PE中位数fallback链
  - ✨ PE百分位逻辑修正：高PE历史=谨慎信号，非"便宜"信号
  - ✨ watchlist.json添加`moat_override`字段：NVDA(8.5)、AAPL(9.0)、MSFT(9.5)
  - ✨ 公用事业(DUK)行业调整：PE百分位-15点，价值陷阱阈值+20
  - ✨ backtest.py支持assessment格式回测，回测准确率83.3%/91.7%
  - 🔧 修复4个P0系统性Bug，回测方向准确率41.7%→83.3%
  - 📊 industry_config.yaml扩展至11个行业+6种护城河类型

- **v2.3.0** (2026-05-09): 🎯 财报数据集成 + 自迭代校验层
  - ✨ 真实财报数据集成 — 从 `longbridge financial-report` 获取利润表/资产负债表/现金流量表
  - ✨ 新增 `fetch_financials()` 财报拉取、`_validate_financial_data()` 数据质量校验层
  - ✨ 非干净数据（error）自动降级买入信号为 HOLD
  - ✨ 新增 `watchlist_utils.py` — 统一看板加载模块，所有模块动态加载
  - 🔧 修复循环 EPS 推导问题，修复季度数据缺失导致的 FCF 误判
  - 🔧 修复 PE 分位 N/A 时虚假买入信号

- **v2.1.2** (2026-04-21): 🔧 修正 VIX 符号
  - `.^VIX.US` 无法获取数据，改用 `VIXM.US`（VIX Mid-Term Futures ETF）

- **v2.1.1** (2026-04-21): 🔴 严重Bug修复：缺口检测逻辑错误
  - 修复 Open-Close 误判为缺口的问题，改用 High/Low 区间无重叠判定
  - 所有缺口分析报告需重新运行验证

- **v2.1.0** (2026-04-21): 🔧 系统化缺口检测
  - 新增缺口检测检查清单（5步强制流程）
  - 新增系统化检测函数和表格输出模板
  - 新增 jq 查询验证模板

- **v2.0** (2026-04-21): 重大升级 - 量化分析引擎
  - ✨ 新增风险指标计算（Sharpe Ratio、最大回撤、Beta、VaR等）
  - ✨ 新增估值指标体系（P/E、PEG、EV/EBITDA、Graham内在价值等）
  - ✨ 扩展技术指标（RSI、MACD、布林带、随机指标、ATR等）
  - ✨ 实现多因子模型（Quality、Value、Growth、Momentum、Low Volatility）
  - ✨ 创建综合分析引擎和Python API
  - ✨ 支持命令行和Python两种使用方式
  - ✨ 生成专业级Markdown分析报告
  - 📚 新增4个详细参考文档
  - 🎯 综合评分系统（0-100分）和投资建议

- **v1.1** (2026-04-21): 增加Harness系统
  - 每日总结和复盘机制
  - 预测准确率回测
  - 跟踪指标自动调整
  - 持续改进框架

- **v1.0** (2026-04-20): 初始版本
  - 实现完整分析流程
  - 缺口理论支持
  - 价值区间分析
  - 仓位管理建议

## 反馈与贡献

如有问题或建议，请联系开发者或提交issue。

---

**免责声明：** 本工具仅供教育和研究目的，不构成任何投资建议。投资决策应基于个人情况并咨询专业顾问。过往表现不代表未来收益。市场有风险，投资需谨慎。
