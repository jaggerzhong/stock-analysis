# Stock Analysis Harness

Automated testing and evaluation system for stock analysis strategies.

## 🎯 Overview

This harness system implements continuous evaluation and improvement of stock analysis strategies, following OpenAI's harness engineering best practices.

## 📊 Current Status

| Component | Status | Score |
|-----------|--------|-------|
| Core Functionality | ✅ Implemented | B |
| Testing | ⚠️ In Progress | D |
| Documentation | ⚠️ In Progress | C |
| CI/CD | ❌ Not Started | F |
| Monitoring | ❌ Not Started | F |

**Overall Score: C+ (Needs Improvement)**

## 🚀 Quick Start

### Run Full Harness

```bash
cd /Users/Jagger/.agents/skills/stock-analysis/harness

# Run all components
./harness-run.sh

# Run specific component
./harness-run.sh --daily      # Daily summary
./harness-run.sh --backtest   # Backtest analysis
./harness-run.sh --adjust     # Metrics adjustment
```

### Run Tests

```bash
# Run unit tests
pytest tests/unit/ -v

# Run specific test
pytest tests/unit/test_backtest.py -v

# Run with coverage
pytest tests/unit/ --cov=backtest --cov-report=html
```

### Validate Golden Examples

```bash
python validate_golden_examples.py
```

## 📁 Directory Structure

```
harness/
├── README.md                      # This file
├── HARNESS_AUDIT.md              # Detailed audit report
├── config.yaml                   # Configuration
├── harness-run.sh                # Main runner script
├── daily-summary.sh              # Daily report generator
├── backtest.py                   # Backtest logic
├── adjust-metrics.py             # Metrics adjustment
├── backtest-analysis.py          # Historical date analysis
│
├── golden_examples/              # Test scenarios
│   ├── scenarios/
│   │   └── bull_market_2026_04.json
│   └── expected_outputs/
│
├── tests/                        # Test suite
│   ├── unit/
│   │   └── test_backtest.py
│   ├── integration/
│   └── fixtures/
│
├── data/                         # Data storage
│   ├── daily/
│   ├── predictions/
│   ├── backtests/
│   └── metrics/
│
└── docs/                         # Documentation
    ├── api/
    └── guides/
```

## 🔧 Components

### 1. Daily Summary (daily-summary.sh)

Runs at 9:00 AM Beijing Time (after US market close).

**What it does:**
- Fetches market sentiment
- Gets quotes for watchlist
- Collects news for each symbol
- Generates daily report
- Saves predictions for tomorrow

**Output:**
- `data/daily/report-YYYY-MM-DD.md`
- `data/predictions/prediction-YYYY-MM-DD.json`

### 2. Backtest (backtest.py)

Runs at 9:30 AM Beijing Time.

**What it does:**
- Compares yesterday's predictions vs actual
- Calculates accuracy metrics:
  - Price direction accuracy
  - Target price accuracy
  - Recommendation accuracy
- Updates cumulative metrics

**Output:**
- `data/backtests/backtest-YYYY-MM-DD.json`
- `data/metrics/cumulative_metrics.json`

### 3. Metrics Adjustment (adjust-metrics.py)

Runs weekly on Friday at 10:00 AM Beijing Time.

**What it does:**
- Analyzes backtest performance trends
- Identifies poorly performing metrics
- Suggests weight adjustments
- Recommends new metrics to add

**Output:**
- `data/metrics/metric_weights.json`
- `data/metrics/adjustments_applied.json`

### 4. Backtest Analysis (backtest-analysis.py)

Analyze stocks as of a specific historical date.

**Usage:**
```bash
python backtest-analysis.py 2026-04-07 --symbols BABA.US NVDA.US
```

**Use case:**
- Evaluate how strategy would have performed on past dates
- Compare predictions with actual outcomes
- Identify strategy weaknesses

## 📈 Metrics

### Primary Metrics

| Metric | Description | Target | Current |
|--------|-------------|--------|---------|
| Price Direction Accuracy | % correct up/down predictions | ≥60% | 0% |
| Target Price Accuracy | % within 5% of target | ≥30% | 0% |
| Recommendation Accuracy | % correct buy/hold/sell | ≥70% | 0% |

### Risk Metrics

- Maximum Drawdown
- Sharpe Ratio
- Historical Volatility
- Risk Score (0-100)

### Technical Indicators

- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume Analysis

## 🧪 Testing

### Golden Examples

Golden examples are high-quality test scenarios that validate strategy behavior.

**Location:** `golden_examples/scenarios/`

**Example scenarios:**
- Bull market rally
- Bear market crash
- Oversold bounce
- High volatility period

**Run validation:**
```bash
python validate_golden_examples.py
```

### Unit Tests

Test individual functions in isolation.

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_backtest.py -v

# Run specific test
pytest tests/unit/test_backtest.py::TestBacktest::test_price_direction_accuracy_correct_prediction -v
```

### Integration Tests

Test complete workflows.

```bash
pytest tests/integration/ -v
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
# Watchlist
watchlist:
  - BABA.US
  - NVDA.US
  - TSLA.US

# Backtest thresholds
backtest:
  thresholds:
    price_direction_accuracy: 0.6
    target_price_accuracy: 0.3

# Adjustment settings
adjustment:
  enabled: false
  min_observations: 10
```

## 🤖 Automation

### Cron Jobs (Beijing Time)

```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily summary at 9:00 AM Beijing Time
0 9 * * * cd /Users/Jagger/.agents/skills/stock-analysis/harness && ./harness-run.sh --daily

# Backtest at 9:30 AM Beijing Time
30 9 * * * cd /Users/Jagger/.agents/skills/stock-analysis/harness && ./harness-run.sh --backtest

# Weekly adjustment on Friday at 10:00 AM Beijing Time
0 10 * * 5 cd /Users/Jagger/.agents/skills/stock-analysis/harness && ./harness-run.sh --adjust
```

## 📊 Monitoring (Planned)

### Health Checks

```python
# Check data freshness
python -m monitoring.health_check

# Check backtest performance
python -m monitoring.performance_monitor
```

### Alerts

Configure email/Slack alerts in `config.yaml`:

```yaml
monitoring:
  alerts:
    email:
      enabled: true
      recipient: "admin@example.com"
    slack:
      enabled: true
      webhook_url: "https://hooks.slack.com/..."
```

## 🔍 Known Issues

See [HARNESS_AUDIT.md](./HARNESS_AUDIT.md) for detailed analysis.

### Critical Issues

1. **No Golden Examples** - Cannot validate strategy accuracy
2. **No Unit Tests** - Cannot guarantee code quality
3. **No CI/CD** - Manual testing and deployment
4. **No Monitoring** - Cannot detect issues proactively

### Improvement Priority

1. **Immediate:** Add golden examples and unit tests
2. **Short-term:** Add CI/CD and monitoring
3. **Medium-term:** Add caching and performance optimization
4. **Long-term:** Add A/B testing and dashboard

## 📚 Documentation

- [HARNESS_AUDIT.md](./HARNESS_AUDIT.md) - Detailed audit report
- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) - System architecture (planned)
- [TESTING.md](./docs/TESTING.md) - Testing guide (planned)

## 🤝 Contributing

1. Add golden examples for new scenarios
2. Write tests for new features
3. Update documentation
4. Run tests before committing

## 📝 Changelog

### v0.1.0 (2026-04-21)
- Initial harness implementation
- Daily summary, backtest, adjustment components
- Basic golden examples
- Unit test framework

### Planned
- v0.2.0: Full test coverage, CI/CD
- v0.3.0: Monitoring and alerting
- v0.4.0: Performance dashboard

## 📄 License

MIT License - See LICENSE file for details.

---

**Last Updated:** 2026-04-21  
**Maintainer:** AI Assistant  
**Status:** Active Development
