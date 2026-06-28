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
    qqq_spy: str | None = None
    smh_spy: str | None = None
    rsp_spy: str | None = None
    xlu_spy: str | None = None
    xlp_spy: str | None = None

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

    @property
    def is_defensive_rotation(self) -> bool:
        return (
            self.qqq_spy == "down"
            and (self.xlu_spy == "up" or self.xlp_spy == "up")
            and (self.rsp_spy == "up" or self.smh_spy == "down")
        )

    @property
    def is_tech_rotation(self) -> bool:
        return self.qqq_spy == "down" and self.smh_spy == "down"


def _text_fields(assessment: Mapping[str, Any]) -> str:
    values: list[str] = []
    for key in ("symbol", "moat_width"):
        value = assessment.get(key)
        if value:
            values.append(str(value))
    for key in ("matched_industries", "thesis"):
        value = assessment.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value:
            values.append(str(value))
    return " ".join(values).lower()


def _float_value(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_growth_beta(assessment: Mapping[str, Any]) -> bool:
    text = _text_fields(assessment)
    symbols = {"NVDA.US", "PLTR.US", "TSLA.US", "COIN.US", "HOOD.US"}
    return (
        str(assessment.get("symbol", "")).upper() in symbols
        or "ai" in text
        or "semiconductor" in text
        or "crypto" in text
        or "fintech" in text
        or "trading" in text
    )


def _is_defensive_candidate(assessment: Mapping[str, Any]) -> bool:
    text = _text_fields(assessment)
    symbol = str(assessment.get("symbol", "")).upper()
    return symbol in {"DUK.US"} or "utility" in text or "regulated" in text


def _has_unstable_valuation(assessment: Mapping[str, Any]) -> bool:
    if assessment.get("has_fundamental_update"):
        return False
    current = assessment.get("core_value")
    previous = assessment.get("previous_core_value")
    current_value = _float_value(current)
    previous_value = _float_value(previous)
    if current_value is None or previous_value is None:
        return False
    if current_value <= 0 or previous_value <= 0:
        return False
    return abs(current_value / previous_value - 1) > 0.30


def downgrade_action(
    action: str,
    environment: MarketEnvironment | None,
    assessment: Mapping[str, Any] | None = None,
) -> str:
    """Downgrade buy actions when sentiment is weak and valuation is elevated."""
    action = (action or "HOLD").upper()
    assessment = assessment or {}

    if _has_unstable_valuation(assessment) and action in BUY_ACTIONS:
        return "HOLD_REVIEW"

    if (
        action == "BUY_SMALL"
        and assessment.get("technical_confirmed") is False
        and (_float_value(assessment.get("deviation_pct")) or 0) <= -5
    ):
        return "WAIT_FOR_CONFIRMATION"

    if not environment:
        return action

    if environment.is_defensive_rotation and _is_defensive_candidate(assessment):
        if action in {"AVOID", "HOLD", "WAIT"}:
            return "DEFENSIVE_HOLD"

    if environment.is_tech_rotation and _is_growth_beta(assessment):
        action = {
            "GET_ON_BOARD": "BUY_SMALL",
            "BUY": "BUY_SMALL",
            "BUY_SMALL": "WAIT",
        }.get(action, action)

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
    adjusted_action = downgrade_action(str(assessment.get("action", "HOLD")), environment, assessment)
    moat_score = float(assessment.get("moat_score") or 0)
    trap_score = float(assessment.get("value_trap_score") or 0)
    moat_width = str(assessment.get("moat_width", "")).lower()

    if adjusted_action == "DEFENSIVE_HOLD":
        return 0.25 if trap_score < 15 and (moat_score >= 6 or moat_width == "wide") else 0.0

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
    return downgrade_action(str(assessment.get("action", "HOLD")), environment, assessment)
