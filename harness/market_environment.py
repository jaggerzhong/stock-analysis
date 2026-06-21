#!/usr/bin/env python3
"""Generate structured market-environment inputs for the harness."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from analysis.engine import MarketEnvironmentAnalyzer  # noqa: E402


DEFAULT_MARKET_SYMBOLS = [
    "SPY.US",
    "QQQ.US",
    "RSP.US",
    "SMH.US",
    "XLU.US",
    "XLP.US",
    "HYG.US",
    "JNK.US",
    "UUP.US",  # US dollar ETF proxy when DXY is unavailable
    "VIXM.US",
]


def run_command(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def parse_market_temp(output: str) -> dict[str, float | str]:
    result: dict[str, float | str] = {}
    for line in output.splitlines():
        match = re.match(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip()
        if key in ("field", "-------------"):
            continue
        number = re.search(r"-?\d+(?:\.\d+)?", value)
        if number and key in ("temperature", "valuation", "sentiment"):
            result[key] = float(number.group(0))
        elif key:
            result[key] = value
    return result


def parse_quotes(output: str) -> list[dict[str, Any]]:
    if not output.strip():
        return []
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and "quotes" in data:
        data = data["quotes"]
    return data if isinstance(data, list) else []


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def quote_change_pct(quote: dict[str, Any]) -> float | None:
    for key in ("change_percentage", "change_rate"):
        value = to_float(quote.get(key))
        if value is not None:
            return value
    last = to_float(quote.get("last") or quote.get("last_done"))
    prev = to_float(quote.get("prev_close") or quote.get("previous_close"))
    if last is not None and prev and prev > 0:
        return (last / prev - 1) * 100
    return None


def quote_last(quote: dict[str, Any]) -> float | None:
    return to_float(quote.get("last") or quote.get("last_done"))


def fetch_quotes(symbols: list[str]) -> dict[str, dict[str, Any]]:
    output = run_command(["longbridge", "quote", *symbols, "--format", "json"])
    return {item["symbol"]: item for item in parse_quotes(output) if item.get("symbol")}


def fetch_kline(symbol: str, days: int = 260) -> list[dict[str, Any]]:
    end = datetime.now().date()
    start = end - timedelta(days=days * 2)
    output = run_command([
        "longbridge",
        "kline",
        "history",
        symbol,
        "--start",
        start.isoformat(),
        "--end",
        end.isoformat(),
        "--period",
        "day",
        "--format",
        "json",
    ])
    try:
        data = json.loads(output)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def moving_average(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def trend_from_klines(symbol: str, klines: list[dict[str, Any]]) -> dict[str, Any]:
    closes = [to_float(item.get("close")) for item in klines]
    prices = [value for value in closes if value is not None]
    if not prices:
        return {}
    current = prices[-1]
    ma50 = moving_average(prices, 50)
    ma200 = moving_average(prices, 200)
    result: dict[str, Any] = {
        f"{symbol.lower().split('.')[0]}_last": current,
    }
    prefix = symbol.lower().split(".")[0]
    if ma50:
        result[f"{prefix}_above_50"] = current > ma50
    if ma200:
        result[f"{prefix}_above_200"] = current > ma200
        result[f"{prefix}_200d_deviation_pct"] = round((current / ma200 - 1) * 100, 2)
    return result


def relative_trend(quotes: dict[str, dict[str, Any]], numerator: str, denominator: str) -> str | None:
    n = quote_change_pct(quotes.get(numerator, {}))
    d = quote_change_pct(quotes.get(denominator, {}))
    if n is None or d is None:
        return None
    spread = n - d
    if spread > 0.25:
        return "up"
    if spread < -0.25:
        return "down"
    return "flat"


def generate_environment(watchlist_quotes_path: Path | None = None) -> dict[str, Any]:
    market_temp_raw = run_command(["longbridge", "market-temp"])
    market_temp = parse_market_temp(market_temp_raw)

    quotes = fetch_quotes(DEFAULT_MARKET_SYMBOLS)
    trend_data: dict[str, Any] = {}
    trend_data.update(trend_from_klines("SPY.US", fetch_kline("SPY.US")))
    trend_data.update(trend_from_klines("QQQ.US", fetch_kline("QQQ.US")))

    breadth_data: list[float] = []
    if watchlist_quotes_path and watchlist_quotes_path.exists():
        watchlist_quotes = parse_quotes(watchlist_quotes_path.read_text())
        breadth_data = [value for value in (quote_change_pct(item) for item in watchlist_quotes) if value is not None]

    risk_appetite_data = {
        "qqq_spy": relative_trend(quotes, "QQQ.US", "SPY.US"),
        "smh_spy": relative_trend(quotes, "SMH.US", "SPY.US"),
        "rsp_spy": relative_trend(quotes, "RSP.US", "SPY.US"),
        "xlu_spy": relative_trend(quotes, "XLU.US", "SPY.US"),
        "xlp_spy": relative_trend(quotes, "XLP.US", "SPY.US"),
        "hyg_trend": "up" if (quote_change_pct(quotes.get("HYG.US", {})) or 0) > 0 else "down",
    }
    liquidity_data = {
        "dxy_trend": "up" if (quote_change_pct(quotes.get("UUP.US", {})) or 0) > 0 else "down",
        "credit_spread_trend": "narrowing" if (quote_change_pct(quotes.get("HYG.US", {})) or 0) > 0 else "widening",
    }
    vixm = quote_last(quotes.get("VIXM.US", {}))

    assessment = MarketEnvironmentAnalyzer.assess_market_environment(
        vix=vixm,
        market_sentiment=to_float(market_temp.get("sentiment")),
        market_valuation=to_float(market_temp.get("valuation")),
        breadth_data=breadth_data,
        trend_data=trend_data,
        risk_appetite_data=risk_appetite_data,
        liquidity_data=liquidity_data,
    )

    return {
        "generated_at": datetime.now().isoformat(),
        "market_temp": market_temp,
        "market_quotes": quotes,
        "inputs": {
            "vix": vixm,
            "breadth_data": breadth_data,
            "trend_data": trend_data,
            "risk_appetite_data": risk_appetite_data,
            "liquidity_data": liquidity_data,
        },
        "assessment": assessment,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate market environment JSON")
    parser.add_argument("--quotes", type=Path, help="Watchlist quotes JSON for breadth")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON path")
    args = parser.parse_args()

    result = generate_environment(args.quotes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
