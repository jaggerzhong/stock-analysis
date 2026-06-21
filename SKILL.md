---
name: stock-analysis
description: 'Comprehensive stock portfolio analyzer with watchlist. TRIGGER on ANY of: (1) watchlist analysis: "分析自选股" / "analyze watchlist" / "my watchlist"; (2) portfolio analysis: "分析我的持仓" / "portfolio analysis" / "stock review"; (3) market sentiment: "大盘情绪" / "market outlook"; (4) technical levels: "缺口分析" / "support/resistance levels"; (5) position sizing: "仓位建议" / "should I buy/sell". Watchlist is defined in references/watchlist.json. Uses Longbridge CLI, multi-factor market regime, valuation, moat, value-trap, technical, and position management frameworks.'
---

# Stock Portfolio Analyzer

## Operating Principle

This skill is decision support, not financial advice. Do not present outputs as certainty or direct instructions to trade.

Default philosophy: value-aware, risk-first investing.

1. Assess business quality and value.
2. Measure price deviation from intrinsic value and technical zones.
3. Check market regime before individual stock signals.
4. Size positions conservatively and rebalance weekly by default.
5. Show data gaps and confidence before any action label.

## Canonical Commands

Use the Python entrypoint when possible. It keeps the watchlist source, Longbridge fetches, scoring, data-quality gate, and report format aligned.

```bash
cd /Users/Jagger/.agents/skills/stock-analysis

# Analyze the authoritative watchlist from references/watchlist.json
python3 analysis/analyze.py --watchlist

# Analyze current Longbridge positions, including option positions when present
python3 analysis/analyze.py --portfolio

# Analyze specific symbols
python3 analysis/analyze.py BABA.US NVDA.US TSLA.US

# JSON output for downstream processing
python3 analysis/analyze.py AAPL.US --format json -o analysis.json
```

Quick data commands are allowed for lightweight user questions:

```bash
longbridge market-temp
longbridge quote SPY.US QQQ.US VIXM.US --format json
longbridge positions --format json
python3 -c "from watchlist_utils import load_watchlist; print(' '.join(load_watchlist()))"
```

## Required Workflow

For watchlist, portfolio, or buy/sell requests, follow this order:

1. Market regime: sentiment, temperature, valuation, SPY/QQQ, VIXM proxy, major divergences.
2. Data quality: quote freshness, k-line availability, financial statement completeness, EPS/FCF reliability.
3. Business quality: moat, ROIC/WACC, recurring revenue or sector fallback, quality trend.
4. Value trap detection: FCF, leverage, earnings quality, dividend sustainability, structural risk.
5. Valuation: DCF and Shiller/CAPE when data exists; PE/PEG/P-FCF/EV-EBITDA as fallbacks; Graham is reference-only.
6. Technical timing: RSI, MA trend, momentum, support/resistance, gap analysis, ATR stop.
7. Conflict resolution: market regime > business quality > valuation > technicals > short-term news.
8. Position management: total exposure target first, then individual symbol sizing.

## Recommendation Wording

Keep the model signal internally compatible (`STRONG BUY`, `BUY`, `HOLD`, `SELL`), but present user-facing actions conservatively:

| Model Signal | User-Facing Action |
|--------------|--------------------|
| STRONG BUY | 小仓位试探 / 等待确认 |
| BUY | 观察买点 / 分批小仓位 |
| HOLD / WEAK HOLD | 持有观察 |
| SELL / STRONG SELL | 减仓 / 避免新增 |

If `data_quality.is_clean == false`, cap aggressive entries: downgrade buy-style signals to `HOLD`, lower confidence, and show the data-quality warnings.

## Position Management

The authoritative score-to-position mapping is `analysis/config.yaml` under `overall.score_to_position` and is implemented by `comprehensive_score_to_position()`.

| Comprehensive Score | Market State | Raw Target Position | Target Cash | Default Action |
|---------------------|--------------|---------------------|-------------|----------------|
| 80-100 | Extreme Greed | 10-25% | 75-90% | Reduce risk aggressively |
| 70-80 | Greed | 25-40% | 60-75% | Selective sell |
| 60-70 | Neutral-Bullish | 40-55% | 45-60% | Hold, trim weak names |
| 40-60 | Neutral | 50-65% | 35-50% | Hold / selective buy |
| 30-40 | Fear | 65-80% | 20-35% | Selective buy |
| 0-30 | Extreme Fear | 80-95% | 5-20% | Buy high-conviction names gradually |

Execution discipline:

- Rebalance weekly by default, not daily.
- Ignore target changes below 5 percentage points.
- Move about 35% of the gap toward target per rebalance unless hard risk caps are breached.
- Keep at least 5% cash and never exceed 95% total position.
- Single stock max target is 15%; sector concentration target max is 30% unless explicitly justified.

## Output Structure

Use this structure for user-facing reports:

```markdown
# 股票分析报告
日期: YYYY-MM-DD HH:MM

## 结论
- 用户动作: 持有观察 / 分批小仓位 / 减仓 / 避免新增
- 模型信号: BUY / HOLD / SELL
- 置信度: HIGH / MEDIUM / LOW
- 数据质量: Clean / Incomplete, with warnings

## 市场环境
- 综合分数 / 市场状态 / 目标总仓位
- 关键风险: 估值、ATH、VIXM、情绪背离

## 标的概览
| Symbol | Price | Change | Score | Action | Risk | Data |
|--------|-------|--------|-------|--------|------|------|

## 重点分析
- 业务质量 / 护城河
- 估值区间 / 安全边际
- 技术位置 / 支撑阻力 / 缺口
- 风险和触发条件

## 仓位建议
- 当前总仓位 vs 目标总仓位
- 本周调整金额
- 优先买入、持有、减仓列表
```

## Data Sources

- Market, quote, k-line, positions, news: Longbridge CLI.
- Watchlist source of truth: `references/watchlist.json` via `watchlist_utils.load_watchlist()`.
- Engine config: `analysis/config.yaml`.
- Harness config: `harness/config.yaml`.
- Generated reports and data: `harness/data/` and `data/` are ignored by git.

## Reference Files

- Market regime and position sizing: `references/market-regime.md`, `references/position-management.md`.
- Value framework: `references/moat-analysis.md`, `references/roic-analysis.md`, `references/value-trap-detection.md`, `references/value-zone.md`.
- Technical framework: `references/gap-theory.md`, `references/technical-indicators.md`.
- Quant engine details: `analysis/README.md`, `references/risk-metrics.md`, `references/valuation-metrics.md`, `references/multi-factor-model.md`.
- Validation and harness: `harness/README.md`, `harness/FINAL_OPTIMIZATION_REPORT.md`.

## Daily Harness

```bash
cd /Users/Jagger/.agents/skills/stock-analysis/harness
./harness-run.sh --daily
./harness-run.sh --backtest
./harness-run.sh --adjust
./harness-run.sh --report
```

Use the harness for continuous review, not as an auto-trading system. Review generated reports before making portfolio decisions.

## Disclaimer

This skill is for education and research. It does not provide personalized financial advice. Market data can be delayed or incomplete, and past performance does not imply future returns.
