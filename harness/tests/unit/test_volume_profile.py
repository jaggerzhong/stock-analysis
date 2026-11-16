"""Observable volume, cutoff and input invariants for the offline profile helper."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.volume_profile import analyze, load_bars, timestamp, volume_profile


def record(day="01", **overrides):
    row = dict(open_time=f"2026-01-{day}T00:00:00Z",
               close_time=f"2026-01-{day}T01:00:00Z",
               open=100, high=102, low=100, close=102, volume=40)
    row.update(overrides)
    return row


@pytest.mark.parametrize("method", ["uniform", "typical"])
@pytest.mark.parametrize("width", [0.1, 1, 3])
@pytest.mark.parametrize("offset", [0, 0.5])
def test_volume_conserved_across_methods_and_bins(method, width, offset):
    bars = load_bars([record(), record("02", volume=17)])
    result = volume_profile(bars, width, method, offset)
    assert sum(b["estimated_volume"] for b in result["bins"]) == pytest.approx(57)
    assert sum(b["share_pct"] for b in result["bins"]) == pytest.approx(100)


def test_uniform_overlap_and_typical_price_have_different_meaning():
    bars = load_bars([record()])
    assert [b["estimated_volume"] for b in volume_profile(bars, 1)["bins"]] == [20, 20]
    typical = volume_profile(bars, 1, "typical")["bins"]
    assert [(b["low"], b["estimated_volume"]) for b in typical] == [(101, 40)]


def test_flat_bar_on_decimal_boundary_preserves_all_volume():
    bars = load_bars([record(open=0.3, high=0.3, low=0.3, close=0.3)])
    assert volume_profile(bars, 0.1)["bins"][0] == {
        "low": 0.3, "high": 0.4, "estimated_volume": 40, "share_pct": 100}


def test_cutoff_and_calendar_window_do_not_count_bars_as_hours():
    # Irregular trading sessions and a future/unclosed bar, as with stock data.
    bars = load_bars([record("02"), record("05"), record("06", volume=999)])
    result = analyze(bars, timestamp("2026-01-06T00:30:00Z"), [2, 10], [1])
    assert result["excluded_unclosed_or_future_bars"] == 1
    short, long = result["windows"]
    assert short["bar_count"] == 1
    assert short["profiles"][0]["total_volume"] == 40
    assert long["bar_count"] == 2
    assert long["input_reaches_window_start"] is False


def test_binance_end_boundary_excludes_unfinished_bar():
    start = 1767225600000  # 2026-01-01 00:00 UTC
    bars = load_bars([[start, "100", "102", "100", "102", "40", start + 3599999]], "binance")
    before = analyze(bars, timestamp("2026-01-01T00:59:59.999Z"), [1], [1])
    at_end = analyze(bars, timestamp("2026-01-01T01:00:00Z"), [1], [1])
    assert before["windows"][0]["bar_count"] == 0
    assert at_end["windows"][0]["bar_count"] == 1


@pytest.mark.parametrize("override", [
    {"volume": -1}, {"volume": "NaN"}, {"high": float("inf")},
    {"low": 101}, {"open_time": "2026-01-01T00:00:00"},
    {"close_time": "2025-12-31T23:00:00Z"},
])
def test_invalid_market_data_fails_instead_of_silent_coercion(override):
    with pytest.raises(ValueError):
        load_bars([record(**override)])


def test_duplicate_and_overlapping_bars_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        load_bars([record(), record()])
    with pytest.raises(ValueError, match="overlap"):
        load_bars([record(), record(open_time="2026-01-01T00:30:00Z",
                                  close_time="2026-01-01T01:30:00Z")])


def test_zero_volume_and_invalid_width_are_explicit():
    bars = load_bars([record(volume=0)])
    result = analyze(bars, timestamp("2026-01-02T00:00:00Z"), [1], [1])
    assert result["windows"][0]["status"] == "no_positive_volume"
    with pytest.raises(ValueError, match="width"):
        volume_profile(bars, 0)
