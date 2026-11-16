#!/usr/bin/env python3
"""Offline candle-based volume profiles; candidates, not resistance predictions."""

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path


def timestamp(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class Bar:
    start: datetime
    end: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_bars(records, input_format="normalized"):
    if not isinstance(records, list) or not records:
        raise ValueError("input must be a nonempty JSON array of bars")
    bars = []
    seen = set()
    for index, row in enumerate(records):
        try:
            if input_format == "binance":
                epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
                start = epoch + timedelta(milliseconds=int(row[0]))
                end = epoch + timedelta(milliseconds=int(row[6]) + 1)
                values = [float(row[i]) for i in (1, 2, 3, 4, 5)]
            else:
                start, end = timestamp(row["open_time"]), timestamp(row["close_time"])
                values = [float(row[k]) for k in ("open", "high", "low", "close", "volume")]
            o, h, l, c, v = values
            if not all(math.isfinite(x) for x in values):
                raise ValueError("prices and volume must be finite")
            if not (0 < l <= min(o, c) <= max(o, c) <= h) or v < 0:
                raise ValueError("invalid OHLC bounds or negative volume")
            if end <= start or start in seen:
                raise ValueError("invalid time range or duplicate bar")
            seen.add(start)
            bars.append(Bar(start, end, o, h, l, c, v))
        except (KeyError, IndexError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"bar {index}: {exc}") from exc
    bars.sort(key=lambda bar: bar.start)
    if any(left.end > right.start for left, right in zip(bars, bars[1:])):
        raise ValueError("bars overlap; use one series with a consistent period")
    return bars


def volume_profile(bars, width, method="uniform", offset_fraction=0):
    if not math.isfinite(width) or width <= 0:
        raise ValueError("bin width must be finite and positive")
    if method not in ("uniform", "typical"):
        raise ValueError("method must be uniform or typical")
    if not math.isfinite(offset_fraction) or not 0 <= offset_fraction < 1:
        raise ValueError("offset fraction must be in [0, 1)")
    # Decimal boundaries avoid losing flat bars or boundary points to float rounding.
    step = Decimal(str(width))
    offset = step * Decimal(str(offset_fraction))

    def bucket(price):
        return int(((price - offset) / step).to_integral_value(rounding=ROUND_FLOOR))

    volumes = {}
    for bar in bars:
        if bar.volume == 0:
            continue
        low, high, close = (Decimal(str(x)) for x in (bar.low, bar.high, bar.close))
        if method == "typical" or low == high:
            key = bucket((low + high + close) / 3)
            volumes[key] = volumes.get(key, 0.0) + bar.volume
            continue
        first, last = bucket(low), bucket(high)
        if last - first > 100000:
            raise ValueError("bin width too small for candle range")
        for key in range(first, last + 1):
            lower = offset + key * step
            overlap = min(high, lower + step) - max(low, lower)
            if overlap > 0:
                allocated = bar.volume * float(overlap / (high - low))
                volumes[key] = volumes.get(key, 0.0) + allocated
    total = math.fsum(bar.volume for bar in bars)
    if total <= 0 or not math.isfinite(total):
        raise ValueError("selected window must have positive finite total volume")
    bins = [
        {"low": float(offset + key * step), "high": float(offset + (key + 1) * step),
         "estimated_volume": value, "share_pct": value / total * 100}
        for key, value in sorted(volumes.items())
    ]
    if not math.isclose(math.fsum(x["estimated_volume"] for x in bins), total, rel_tol=1e-9):
        raise ValueError("allocated volume does not reconcile to input volume")
    ranked = sorted(bins, key=lambda item: (-item["estimated_volume"], item["low"]))
    return {"bin_width": width, "offset_fraction": offset_fraction, "method": method,
            "total_volume": total, "poc_bins": [x for x in ranked if x["estimated_volume"] == ranked[0]["estimated_volume"]],
            "top_bins": ranked[:10], "bins": bins}


def analyze(bars, as_of, lookbacks, widths):
    if as_of.tzinfo is None:
        raise ValueError("as_of must include a timezone")
    if not lookbacks or any(not math.isfinite(d) or d <= 0 for d in lookbacks):
        raise ValueError("lookbacks must be positive finite calendar days")
    if not widths or any(not math.isfinite(w) or w <= 0 for w in widths):
        raise ValueError("bin widths must be positive and finite")
    completed = [b for b in bars if b.end <= as_of]
    windows = []
    for days in lookbacks:
        start = as_of - timedelta(days=days)
        selected = [b for b in completed if b.start >= start]
        window = {"lookback_calendar_days": days, "requested_start": start.isoformat(),
                  "requested_end": as_of.isoformat(), "bar_count": len(selected),
                  "input_reaches_window_start": bool(completed and completed[0].start <= start),
                  "first_bar_start": selected[0].start.isoformat() if selected else None,
                  "last_bar_end": selected[-1].end.isoformat() if selected else None}
        if not selected or not any(b.volume > 0 for b in selected):
            window.update(status="no_positive_volume", profiles=[])
        else:
            window.update(status="ok", profiles=[
                volume_profile(selected, width, method, offset)
                for width in widths for offset in (0, 0.5) for method in ("uniform", "typical")
            ])
        windows.append(window)
    return {"as_of": as_of.isoformat(), "input_bars": len(bars),
            "excluded_unclosed_or_future_bars": len(bars) - len(completed),
            "estimation": "candle approximation; not trade-level volume or current holder cost",
            "coverage_note": "boundary coverage does not verify missing bars or all-market coverage",
            "windows": windows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="normalized OHLCV or Binance kline JSON array")
    parser.add_argument("--input-format", choices=("normalized", "binance"), default="normalized")
    parser.add_argument("--as-of", required=True, help="explicit cutoff with timezone")
    parser.add_argument("--lookbacks", nargs="+", type=float, required=True, help="calendar days")
    parser.add_argument("--bin-widths", nargs="+", type=float, required=True)
    parser.add_argument("--source", required=True, help="provider, symbol, venue and session/adjustment")
    parser.add_argument("--volume-unit", required=True, help="e.g. BTC, shares or contracts")
    args = parser.parse_args()
    try:
        bars = load_bars(json.loads(args.input.read_text()), args.input_format)
        result = analyze(bars, timestamp(args.as_of), args.lookbacks, args.bin_widths)
    except (OSError, TypeError, ValueError, OverflowError) as exc:
        parser.error(str(exc))
    result.update(source=args.source, volume_unit=args.volume_unit, input_format=args.input_format)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
