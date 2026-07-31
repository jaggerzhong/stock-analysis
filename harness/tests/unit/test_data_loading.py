#!/usr/bin/env python3
"""Regression tests for quote-cache and watchlist normalization."""

import json

import watchlist_utils
from analysis.analyze import LongbridgeDataFetcher


class StubCache:
    def __init__(self, value):
        self.value = value

    def get(self, _prefix, _key):
        return self.value


def test_batch_quote_cache_normalizes_raw_quote_lists(monkeypatch):
    cached_quotes = json.dumps(
        [
            {"symbol": "MSFT.US", "last": "510.00"},
            {"symbol": "NVDA.US", "last": "180.00"},
        ]
    )
    monkeypatch.setattr(
        LongbridgeDataFetcher,
        "run_command",
        lambda _command: (_ for _ in ()).throw(AssertionError("cache miss")),
    )

    quotes = LongbridgeDataFetcher.fetch_batch_quotes(
        ["MSFT.US", "NVDA.US"], StubCache(cached_quotes)
    )

    assert set(quotes) == {"MSFT.US", "NVDA.US"}
    assert quotes["MSFT.US"]["last"] == "510.00"


def test_empty_batch_quote_map_is_a_valid_cached_result(monkeypatch):
    monkeypatch.setattr(
        LongbridgeDataFetcher,
        "run_command",
        lambda _command: (_ for _ in ()).throw(AssertionError("cache miss")),
    )

    assert LongbridgeDataFetcher.fetch_batch_quotes(["MSFT.US"], StubCache("{}")) == {}


def test_watchlist_helpers_share_one_json_source(tmp_path, monkeypatch):
    watchlist_path = tmp_path / "watchlist.json"
    watchlist_path.write_text(
        json.dumps(
            {
                "watchlist": [
                    {"symbol": "MSFT.US", "priority": 1},
                    {
                        "symbol": "VIXM.US",
                        "priority": 3,
                        "valuation_enabled": False,
                    },
                ],
                "metadata": {"total_count": 2},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(watchlist_utils, "WATCHLIST_PATH", watchlist_path)

    assert watchlist_utils.load_watchlist() == ["MSFT.US", "VIXM.US"]
    assert watchlist_utils.load_valuation_watchlist() == ["MSFT.US"]
    assert watchlist_utils.load_valuation_disabled_symbols() == {"VIXM.US"}
    assert watchlist_utils.load_watchlist_symbols_by_priority(1) == ["MSFT.US"]
    assert watchlist_utils.load_watchlist_full()["metadata"]["total_count"] == 2
