"""
Watchlist Loader — single source of truth for the stock watchlist.

Loads from references/watchlist.json. All modules (SKILL.md harness, analysis)
should use this module instead of hardcoding stock symbols.
"""

import json
from pathlib import Path
from typing import Dict, List

WATCHLIST_PATH = Path(__file__).parent / "references" / "watchlist.json"


def _load_watchlist_data() -> Dict:
    """Read and parse the watchlist source of truth."""
    with WATCHLIST_PATH.open(encoding="utf-8") as watchlist_file:
        return json.load(watchlist_file)


def load_watchlist() -> List[str]:
    """
    Load watchlist symbols from references/watchlist.json.
    Returns list of symbol strings (e.g. ['BABA.US', 'NVDA.US', ...]).
    """
    data = _load_watchlist_data()
    return [item["symbol"] for item in data.get("watchlist", [])]


def load_valuation_watchlist() -> List[str]:
    """
    Load symbols that should go through the stock valuation engine.
    ETF/index/watch-only entries can set valuation_enabled=false in watchlist.json.
    """
    data = _load_watchlist_data()
    return [
        item["symbol"]
        for item in data.get("watchlist", [])
        if item.get("valuation_enabled", True)
    ]


def load_valuation_disabled_symbols() -> set[str]:
    """
    Load symbols intentionally excluded from stock valuation.
    These remain in quote/report views but are not treated as failed assessments.
    """
    data = _load_watchlist_data()
    return {
        str(item["symbol"]).upper()
        for item in data.get("watchlist", [])
        if not item.get("valuation_enabled", True)
    }


def load_watchlist_full() -> Dict:
    """
    Load the full watchlist data including metadata.
    Returns the parsed JSON dict.
    """
    return _load_watchlist_data()


def load_watchlist_symbols_by_priority(priority: int = None) -> List[str]:
    """
    Load watchlist symbols filtered by priority.
    priority=1 returns high priority, =2 returns medium, =3 returns low.
    If None, returns all symbols.
    """
    data = _load_watchlist_data()
    items = data.get("watchlist", [])
    if priority is not None:
        items = [item for item in items if item.get("priority") == priority]
    return [item["symbol"] for item in items]
