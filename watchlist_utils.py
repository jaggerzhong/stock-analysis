"""
Watchlist Loader — single source of truth for the stock watchlist.

Loads from references/watchlist.json. All modules (SKILL.md harness, analysis)
should use this module instead of hardcoding stock symbols.
"""

import json
from pathlib import Path
from typing import List, Dict


WATCHLIST_PATH = Path(__file__).parent / "references" / "watchlist.json"


def load_watchlist() -> List[str]:
    """
    Load watchlist symbols from references/watchlist.json.
    Returns list of symbol strings (e.g. ['BABA.US', 'NVDA.US', ...]).
    """
    with open(WATCHLIST_PATH, 'r') as f:
        data = json.load(f)
    return [item['symbol'] for item in data.get('watchlist', [])]


def load_watchlist_full() -> Dict:
    """
    Load the full watchlist data including metadata.
    Returns the parsed JSON dict.
    """
    with open(WATCHLIST_PATH, 'r') as f:
        return json.load(f)


def load_watchlist_symbols_by_priority(priority: int = None) -> List[str]:
    """
    Load watchlist symbols filtered by priority.
    priority=1 returns high priority, =2 returns medium, =3 returns low.
    If None, returns all symbols.
    """
    with open(WATCHLIST_PATH, 'r') as f:
        data = json.load(f)
    items = data.get('watchlist', [])
    if priority is not None:
        items = [item for item in items if item.get('priority') == priority]
    return [item['symbol'] for item in items]
