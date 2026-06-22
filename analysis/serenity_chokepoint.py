#!/usr/bin/env python3
"""
Architecture-first chokepoint research tool.

This is isolated from analysis/analyze.py and harness/. It produces a Serenity-style
research overlay: architecture position, chokepoint pressure, evidence tiers,
negative screens, and next verification work.
"""

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from watchlist_utils import load_watchlist_full  # noqa: E402


AI_INFRA_LAYERS = {
    "compute": ["gpu", "chip", "semiconductor", "ai芯片", "算力", "英伟达", "nvidia"],
    "cloud/platform": ["cloud", "azure", "云", "平台", "software", "软件", "data", "数据"],
    "power": ["power", "energy", "electric", "utility", "nuclear", "电力", "能源", "核能", "公用事业"],
    "ai application": ["ai", "agent", "autonomous", "自动驾驶", "大模型", "analytics"],
    "financial rails": ["crypto", "exchange", "broker", "交易所", "券商", "加密"],
    "consumer/device": ["consumer", "device", "ev", "iphone", "电动车", "消费", "苹果"],
}

CHOKEPOINT_TERMS = [
    "leading", "leader", "dominant", "scarce", "license", "regulatory", "switching",
    "cost_advantage", "technology_moat", "垄断", "龙头", "稀缺", "牌照", "锁定", "领先",
]

NEGATIVE_TERMS = [
    "competition", "竞争", "policy", "政策", "cyclical", "周期", "ceo", "风险",
]


@dataclass
class Candidate:
    symbol: str
    name: str
    sector: str
    description: str
    moat_notes: str
    moat_score: float
    moat_types: List[str]


def load_candidates(symbols: Optional[Iterable[str]]) -> List[Candidate]:
    data = load_watchlist_full()
    requested = {s.upper() for s in symbols or []}
    result = []
    for item in data.get("watchlist", []):
        symbol = item.get("symbol", "").upper()
        if requested and symbol not in requested:
            continue
        moat = item.get("moat_override", {}) or {}
        result.append(
            Candidate(
                symbol=symbol,
                name=item.get("name_en") or item.get("name") or symbol,
                sector=item.get("sector", ""),
                description=item.get("description", ""),
                moat_notes=moat.get("notes", ""),
                moat_score=float(moat.get("moat_score", 0) or 0),
                moat_types=list(moat.get("moat_types", []) or []),
            )
        )
    return result


def text_blob(candidate: Candidate, thesis: str = "") -> str:
    return " ".join(
        [candidate.symbol, candidate.name, candidate.sector, candidate.description, candidate.moat_notes, " ".join(candidate.moat_types), thesis]
    ).lower()


def infer_layer(candidate: Candidate, thesis: str = "") -> str:
    blob = text_blob(candidate, thesis)
    matches = []
    for layer, terms in AI_INFRA_LAYERS.items():
        score = sum(1 for term in terms if term.lower() in blob)
        if score:
            matches.append((score, layer))
    if not matches:
        return "unclassified architecture node"
    matches.sort(reverse=True)
    return matches[0][1]


def score_candidate(candidate: Candidate, thesis: str = "") -> Dict:
    blob = text_blob(candidate, thesis)
    layer = infer_layer(candidate, thesis)

    architecture = 4 if layer in {"compute", "cloud/platform", "power", "ai application"} else 2
    if "unclassified" in layer:
        architecture = 1

    scarcity_hits = sum(1 for term in CHOKEPOINT_TERMS if term.lower() in blob)
    chokepoint = min(5, max(1, scarcity_hits + (1 if candidate.moat_score >= 7 else 0)))

    misunderstanding = 3
    if candidate.sector in {"Utilities", "Financials", "Consumer Discretionary"} and "ai" in blob:
        misunderstanding = 4
    if candidate.moat_score < 4:
        misunderstanding = max(1, misunderstanding - 1)

    evidence_quality = 2
    if candidate.moat_score >= 8:
        evidence_quality = 3
    if "cooperation" in blob or "合作" in blob or "contract" in blob:
        evidence_quality = 3

    financial_validation = 2
    if any(term in blob for term in ["growth", "增长", "strong", "强劲", "stable", "稳定"]):
        financial_validation = 3

    capital_flow = 3 if candidate.symbol.endswith(".US") else 2

    negative_hits = sum(1 for term in NEGATIVE_TERMS if term.lower() in blob)
    negative_screen = max(1, 5 - negative_hits)

    scores = {
        "architecture_relevance": architecture,
        "chokepoint_scarcity": chokepoint,
        "market_misunderstanding": misunderstanding,
        "evidence_quality": evidence_quality,
        "financial_validation": financial_validation,
        "capital_flow_unlock": capital_flow,
        "negative_screen": negative_screen,
    }
    total = sum(scores.values())
    if total >= 28:
        tier = "high-conviction candidate"
    elif total >= 21:
        tier = "research thesis"
    elif total >= 14:
        tier = "watchlist only"
    else:
        tier = "info-only / avoid"

    return {"layer": layer, "scores": scores, "total": total, "tier": tier}


def evidence_table(candidate: Candidate, assessment: Dict) -> List[Dict[str, str]]:
    return [
        {
            "claim": f"{candidate.name} maps to {assessment['layer']} in the next infrastructure stack",
            "tier": "3 ecosystem mapping",
            "confidence": "medium",
            "source_needed": "Confirm with filings, transcripts, product pages, and customer disclosures.",
        },
        {
            "claim": f"Moat signals: {', '.join(candidate.moat_types) or 'not specified'}",
            "tier": "4 inference",
            "confidence": "medium" if candidate.moat_score >= 5 else "low",
            "source_needed": "Tie moat labels to public financial or operational evidence.",
        },
    ]


def format_markdown(candidates: List[Candidate], thesis: str = "") -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = ["# Serenity Chokepoint Overlay", f"Date: {now}", "", "This is a research overlay, not a trade instruction.", ""]
    if thesis:
        lines.extend(["## User Thesis", thesis, ""])

    lines.extend([
        "## Summary",
        "| Symbol | Layer | Score | Tier | Key Read |",
        "|--------|-------|-------|------|----------|",
    ])

    assessments = []
    for candidate in candidates:
        assessment = score_candidate(candidate, thesis)
        assessments.append((candidate, assessment))
        key_read = candidate.description or candidate.moat_notes or "needs manual thesis input"
        lines.append(
            f"| {candidate.symbol} | {assessment['layer']} | {assessment['total']}/35 | {assessment['tier']} | {key_read} |"
        )

    for candidate, assessment in assessments:
        lines.extend([
            "",
            f"## {candidate.symbol} - {candidate.name}",
            f"- Architecture position: {assessment['layer']}",
            f"- Conviction tier: {assessment['tier']} ({assessment['total']}/35)",
            f"- Description: {candidate.description or 'N/A'}",
            f"- Moat notes: {candidate.moat_notes or 'N/A'}",
            "",
            "### Scorecard",
        ])
        for key, value in assessment["scores"].items():
            lines.append(f"- {key}: {value}/5")

        lines.extend([
            "",
            "### Evidence Tiers",
            "| Claim | Tier | Confidence | Verification Needed |",
            "|-------|------|------------|---------------------|",
        ])
        for row in evidence_table(candidate, assessment):
            lines.append(f"| {row['claim']} | {row['tier']} | {row['confidence']} | {row['source_needed']} |")

        lines.extend([
            "",
            "### Next Checks",
            "- Find tier 1 or tier 2 evidence for customer, order, qualification, capacity, or partnership claims.",
            "- Test whether the market category is wrong, not merely whether the stock is popular.",
            "- Run the normal stock-analysis tool after this overlay for market regime, valuation, technical timing, and position sizing.",
        ])

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serenity-style architecture chokepoint overlay")
    parser.add_argument("symbols", nargs="*", help="Symbols to analyze from references/watchlist.json")
    parser.add_argument("--watchlist", action="store_true", help="Analyze the full watchlist")
    parser.add_argument("--thesis", default="", help="Optional user thesis or theme to score against")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    symbols = None if args.watchlist else args.symbols
    candidates = load_candidates(symbols)
    if not candidates:
        raise SystemExit("No matching symbols found in references/watchlist.json")

    if args.format == "json":
        payload = []
        for candidate in candidates:
            assessment = score_candidate(candidate, args.thesis)
            payload.append({
                "symbol": candidate.symbol,
                "name": candidate.name,
                "sector": candidate.sector,
                "description": candidate.description,
                "assessment": assessment,
                "evidence": evidence_table(candidate, assessment),
            })
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(candidates, args.thesis))


if __name__ == "__main__":
    main()
