#!/usr/bin/env python3
"""Backtest deployable strategy rules against stored harness data."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

try:
    from .strategy_rules import MarketEnvironment, action_weight, adjusted_action
except ImportError:  # pragma: no cover - direct script execution
    from strategy_rules import MarketEnvironment, action_weight, adjusted_action


HARNESS_DIR = Path(__file__).resolve().parent


def _load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _quote_price(quote: dict[str, Any]) -> float | None:
    for key in ("last", "last_done", "current_price"):
        value = _number(quote.get(key))
        if value is not None:
            return value
    return None


def _quote_prev_close(quote: dict[str, Any]) -> float | None:
    for key in ("prev_close", "previous_close"):
        value = _number(quote.get(key))
        if value is not None:
            return value
    return None


def _extract_market_environment(report_path: Path) -> MarketEnvironment:
    env_path = report_path.with_name(report_path.name.replace("report-", "market-environment-").replace(".md", ".json"))
    if env_path.exists():
        try:
            data = _load_json(env_path)
            market_temp = data.get("market_temp", {})
            assessment = data.get("assessment", {})
            dims = assessment.get("dimension_breakdown", {})
            sentiment = market_temp.get("sentiment")
            valuation = market_temp.get("valuation")
            if sentiment is None:
                sentiment = dims.get("sentiment_modifier", {}).get("raw")
            if valuation is None:
                valuation = dims.get("valuation", {}).get("raw")
            return MarketEnvironment(
                sentiment=float(sentiment) if sentiment is not None else None,
                valuation=float(valuation) if valuation is not None else None,
                temperature=float(market_temp.get("temperature")) if market_temp.get("temperature") is not None else None,
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    if not report_path.exists():
        return MarketEnvironment()

    text = report_path.read_text()
    values: dict[str, float] = {}
    for key in ("Temperature", "Valuation", "Sentiment"):
        match = re.search(rf"\|\s*{key}\s*\|\s*([0-9.]+)\s*\|", text)
        if match:
            values[key.lower()] = float(match.group(1))

    return MarketEnvironment(
        sentiment=values.get("sentiment"),
        valuation=values.get("valuation"),
        temperature=values.get("temperature"),
    )


def _load_assessment(path: Path) -> list[dict[str, Any]] | None:
    data = _load_json(path)
    assessments = data.get("watchlist_assessments")
    return assessments if isinstance(assessments, list) else None


def _load_quotes(path: Path) -> dict[str, dict[str, Any]]:
    data = _load_json(path)
    if isinstance(data, dict) and "quotes" in data:
        data = data["quotes"]
    if not isinstance(data, list):
        return {}
    return {item["symbol"]: item for item in data if isinstance(item, dict) and item.get("symbol")}


def _next_available_date(date: str, quote_dates: list[str]) -> str | None:
    for quote_date in quote_dates:
        if quote_date > date:
            return quote_date
    return None


def _base_weight(assessment: dict[str, Any]) -> float:
    return {"GET_ON_BOARD": 1.0, "BUY": 1.0, "BUY_SMALL": 0.5}.get(
        str(assessment.get("action", "")).upper(),
        0.0,
    )


def _portfolio_return(
    assessments: list[dict[str, Any]],
    quotes: dict[str, dict[str, Any]],
    environment: MarketEnvironment,
    optimized: bool,
) -> tuple[float, list[str], float]:
    weighted_returns: list[tuple[float, float]] = []
    all_returns: list[float] = []
    picks: list[str] = []

    for assessment in assessments:
        symbol = assessment.get("symbol")
        quote = quotes.get(symbol)
        if not quote:
            continue

        price = _quote_price(quote)
        prev_close = _quote_prev_close(quote)
        if price is None or prev_close is None or prev_close <= 0:
            continue

        actual_return = price / prev_close - 1
        all_returns.append(actual_return)

        weight = action_weight(assessment, environment) if optimized else _base_weight(assessment)
        if weight <= 0:
            continue

        action = adjusted_action(assessment, environment) if optimized else assessment.get("action")
        picks.append(f"{symbol}:{action}:{weight:g}")
        weighted_returns.append((weight, actual_return))

    total_weight = sum(weight for weight, _ in weighted_returns)
    strategy_return = (
        sum(weight * actual_return for weight, actual_return in weighted_returns) / total_weight
        if total_weight > 0
        else 0.0
    )
    benchmark_return = mean(all_returns) if all_returns else 0.0
    return strategy_return, picks, benchmark_return


def run_backtest(data_dir: Path = HARNESS_DIR / "data") -> dict[str, Any]:
    predictions_dir = data_dir / "predictions"
    daily_dir = data_dir / "daily"

    assessment_dates = sorted(
        path.name.removeprefix("assessment-").removesuffix(".json")
        for path in predictions_dir.glob("assessment-*.json")
    )
    quote_dates = sorted(
        path.name.removeprefix("quotes-").removesuffix(".json")
        for path in daily_dir.glob("quotes-*.json")
    )

    rows: list[dict[str, Any]] = []
    base_equity = optimized_equity = benchmark_equity = 1.0
    optimized_peak = 1.0
    optimized_max_drawdown = 0.0

    for assessment_date in assessment_dates:
        assessment_path = predictions_dir / f"assessment-{assessment_date}.json"
        assessments = _load_assessment(assessment_path)
        if not assessments:
            continue

        actual_date = _next_available_date(assessment_date, quote_dates)
        if not actual_date:
            continue

        quotes = _load_quotes(daily_dir / f"quotes-{actual_date}.json")
        environment = _extract_market_environment(daily_dir / f"report-{assessment_date}.md")

        base_return, base_picks, benchmark_return = _portfolio_return(
            assessments, quotes, environment, optimized=False
        )
        optimized_return, optimized_picks, _ = _portfolio_return(
            assessments, quotes, environment, optimized=True
        )

        base_equity *= 1 + base_return
        optimized_equity *= 1 + optimized_return
        benchmark_equity *= 1 + benchmark_return
        optimized_peak = max(optimized_peak, optimized_equity)
        optimized_max_drawdown = min(optimized_max_drawdown, optimized_equity / optimized_peak - 1)

        rows.append(
            {
                "assessment_date": assessment_date,
                "actual_date": actual_date,
                "environment": asdict(environment),
                "base_return": base_return,
                "optimized_return": optimized_return,
                "benchmark_return": benchmark_return,
                "base_picks": base_picks,
                "optimized_picks": optimized_picks,
            }
        )

    optimized_returns = [row["optimized_return"] for row in rows]
    base_returns = [row["base_return"] for row in rows]
    benchmark_returns = [row["benchmark_return"] for row in rows]

    def avg(values: list[float]) -> float:
        return mean(values) if values else 0.0

    return {
        "periods": len(rows),
        "base_total_return": base_equity - 1,
        "optimized_total_return": optimized_equity - 1,
        "benchmark_total_return": benchmark_equity - 1,
        "optimized_excess_vs_base": (optimized_equity - 1) - (base_equity - 1),
        "optimized_excess_vs_benchmark": (optimized_equity - 1) - (benchmark_equity - 1),
        "optimized_avg_period_return": avg(optimized_returns),
        "base_avg_period_return": avg(base_returns),
        "benchmark_avg_period_return": avg(benchmark_returns),
        "optimized_win_rate": sum(1 for value in optimized_returns if value > 0) / len(rows) if rows else 0.0,
        "optimized_outperform_rate": (
            sum(1 for value, benchmark in zip(optimized_returns, benchmark_returns) if value > benchmark) / len(rows)
            if rows
            else 0.0
        ),
        "optimized_period_volatility": pstdev(optimized_returns) if len(optimized_returns) > 1 else 0.0,
        "optimized_max_drawdown": optimized_max_drawdown,
        "rows": rows,
    }


def _rounded_result(result: dict[str, Any]) -> dict[str, Any]:
    rounded = dict(result)
    for key, value in list(rounded.items()):
        if isinstance(value, float):
            rounded[key] = round(value, 4)
    rounded["rows"] = [
        {
            **row,
            "base_return": round(row["base_return"], 4),
            "optimized_return": round(row["optimized_return"], 4),
            "benchmark_return": round(row["benchmark_return"], 4),
        }
        for row in result["rows"]
    ]
    return rounded


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest strategy rules against harness data")
    parser.add_argument("--latest", type=int, default=0, help="Only print the latest N rows")
    args = parser.parse_args()

    result = _rounded_result(run_backtest())
    if args.latest > 0:
        result["rows"] = result["rows"][-args.latest :]
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
