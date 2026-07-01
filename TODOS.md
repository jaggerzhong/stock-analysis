# Stock Analysis TODOs

## Deferred From Reliability Cockpit CEO Review

### Full local UI dashboard
- Priority: P2
- Why: A dashboard could make freshness, action deltas, data quality, and backtest truth easier to scan than markdown.
- Context: The current pass keeps output in daily markdown plus JSON artifacts. Build a UI only after the manifest schema stabilizes.
- Depends on: `harness/data/daily/run-manifest-YYYY-MM-DD.json` and action delta artifacts being stable for several runs.

### New stock scoring model
- Priority: P3
- Why: More scoring may improve recommendations, but the current bottleneck is trust, freshness, and failure visibility.
- Context: Do not add another model layer until the system reliably reports data quality and recent accuracy beside every recommendation.
- Depends on: Backtest Truth Strip proving where current scoring fails by symbol/regime.

### ML model training
- Priority: P3
- Why: ML could help later, but it will amplify bad labels and stale data if introduced before data-quality gates mature.
- Context: Treat ML as a research project after point-in-time data, feature provenance, and out-of-sample validation are explicit.
- Depends on: Reliable historical datasets and documented leakage controls.

### Split `analysis/engine.py`
- Priority: P2
- Why: `analysis/engine.py` is large and increasingly risky to modify.
- Context: Avoid a broad rewrite. Extract only when a focused feature or bugfix naturally creates a stable boundary.
- Depends on: Identifying repeated seams through future changes.

### Trading automation
- Priority: P3
- Why: Automatic trading would change the product from decision support into execution software with much higher risk.
- Context: Explicitly out of scope. Reports must remain decision support, not financial advice or auto-trading.
- Depends on: Separate risk, compliance, authorization, and rollback design if ever reconsidered.
