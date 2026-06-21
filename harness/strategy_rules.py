"""Reusable portfolio rules for value-action strategy backtests.

These rules sit on top of the valuation engine. They do not change intrinsic
value estimates; they translate signals into deployable position weights.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


BUY_ACTIONS = {"GET_ON_BOARD", "BUY", "BUY_SMALL"}


@dataclass(frozen=True)
class MarketEnvironment:
    sentiment: float | None = None
    valuation: float | None = None
    temperature: float | None = None

    @property
    def is_hostile(self) -> bool:
        return (
            self.sentiment is not None
            and self.valuation is not None
            and self.sentiment < 30
            and self.valuation > 70
        )

    @property
    def is_cautious(self) -> bool:
        if self.is_hostile:
            return False
        return (
            self.sentiment is not None
            and self.valuation is not None
            and self.sentiment < 35
            and self.valuation > 75
        )


def downgrade_action(action: str, environment: MarketEnvironment | None) -> str:
    """Downgrade buy actions when sentiment is weak and valuation is elevated."""
    action = (action or "HOLD").upper()
    if not environment:
        return action

    if environment.is_hostile:
        return {
            "GET_ON_BOARD": "BUY_SMALL",
            "BUY": "BUY_SMALL",
            "BUY_SMALL": "WAIT",
        }.get(action, action)

    if environment.is_cautious:
        return {
            "GET_ON_BOARD": "BUY",
            "BUY": "BUY_SMALL",
        }.get(action, action)

    return action


def action_weight(
    assessment: Mapping[str, Any],
    environment: MarketEnvironment | None = None,
) -> float:
    """Return deployable portfolio weight for one assessment signal.

    The returned value is relative weight, not portfolio percentage. It is meant
    to be normalized across selected positions by the portfolio simulator.
    """
    adjusted_action = downgrade_action(str(assessment.get("action", "HOLD")), environment)
    moat_score = float(assessment.get("moat_score") or 0)
    trap_score = float(assessment.get("value_trap_score") or 0)
    moat_width = str(assessment.get("moat_width", "")).lower()

    if adjusted_action == "GET_ON_BOARD":
        if trap_score < 10 and (moat_score >= 8 or moat_width == "wide"):
            return 1.0
        if trap_score < 15 and moat_score >= 6:
            return 0.75
        return 0.5 if trap_score < 25 else 0.0

    if adjusted_action == "BUY":
        if trap_score < 15 and moat_score >= 6:
            return 0.75
        if trap_score < 25 and moat_score >= 5:
            return 0.5
        return 0.0

    if adjusted_action == "BUY_SMALL":
        if trap_score >= 25:
            return 0.0
        return 0.5 if trap_score < 15 and moat_score >= 6 else 0.25

    return 0.0


def adjusted_action(
    assessment: Mapping[str, Any],
    environment: MarketEnvironment | None = None,
) -> str:
    """Return the action after market-environment adjustment."""
    return downgrade_action(str(assessment.get("action", "HOLD")), environment)
