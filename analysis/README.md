# Stock Analysis Engine

完整的量化分析引擎，提供风险、估值、技术和多因子分析能力。

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 命令行使用

```bash
# 分析单个股票
python analyze.py AAPL.US

# 分析自选股
python analyze.py --watchlist

# 分析持仓
python analyze.py --portfolio

# 保存报告
python analyze.py NVDA.US -o report.md

# JSON格式输出
python analyze.py AAPL.US --format json -o analysis.json
```

### Python API使用

```python
from analysis.engine import StockData, StockAnalysisEngine

# 创建股票数据
stock_data = StockData(
    symbol="AAPL.US",
    prices=[150, 152, 151, 153, 155],  # 历史价格
    current_price=155,
    market_cap=2500000000000,
    sector="Technology",
    eps=6.5
)

# 执行分析
engine = StockAnalysisEngine()
analysis = engine.analyze_stock(stock_data)

# 生成报告
report = engine.generate_report(analysis, format='markdown')
print(report)
```

## 功能模块

### 1. 风险指标 (RiskMetricsCalculator)
- Sharpe Ratio
- Maximum Drawdown
- Sortino Ratio
- Beta Coefficient
- Value at Risk (VaR)
- Historical Volatility
- Calmar Ratio

### 2. 估值指标 (ValuationMetricsCalculator)
- P/E Ratio
- PEG Ratio
- EV/EBITDA
- P/FCF
- FCF Yield
- Graham Intrinsic Value

### 3. 技术指标 (TechnicalIndicatorsCalculator)
- Moving Averages (SMA/EMA)
- RSI
- MACD
- Bollinger Bands
- Stochastic Oscillator
- ATR

### 4. 多因子模型 (MultiFactorCalculator)
- Quality Factor
- Value Factor
- Growth Factor
- Momentum Factor
- Low Volatility Factor

## 文档

详细文档请参考：
- `../references/risk-metrics.md`
- `../references/valuation-metrics.md`
- `../references/technical-indicators.md`
- `../references/multi-factor-model.md`

## 依赖

- numpy>=1.20.0
- scipy>=1.7.0 (可选，用于高级统计函数)

## 许可

MIT License
