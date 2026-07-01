#!/usr/bin/env python3
"""Regression tests for industry thesis and chokepoint behavior."""

import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).parent.parent.parent.parent.resolve()
sys.path.insert(0, str(SKILL_DIR))

from analysis.serenity_chokepoint import Candidate, score_candidate
from harness.generate_valuation import _low_confidence_dcf_reason, calculate_core_value


def _candidate(**overrides):
    data = {
        "symbol": "DUK.US",
        "name": "Duke Energy",
        "sector": "Utilities",
        "description": "美国大型电力公司，稳定分红",
        "moat_notes": "监管垄断+客户无法转换，极稳定的现金流和高分红",
        "moat_score": 7.5,
        "moat_types": ["regulatory_license", "switching_cost"],
    }
    data.update(overrides)
    return Candidate(**data)


def test_user_thesis_does_not_reclassify_unrelated_candidate():
    candidate = _candidate(
        symbol="BORING.US",
        name="Boring Industrial",
        sector="Industrials",
        description="传统工业服务公司",
        moat_notes="区域客户关系稳定",
        moat_score=3.0,
        moat_types=["brand_moat"],
    )

    base = score_candidate(candidate)
    with_ai_power_thesis = score_candidate(
        candidate,
        thesis="AI infrastructure power and compute bottlenecks",
    )

    assert with_ai_power_thesis["layer"] == base["layer"]
    assert with_ai_power_thesis["scores"]["architecture_relevance"] == base["scores"]["architecture_relevance"]


def test_low_evidence_research_thesis_is_not_high_investment_confidence():
    assessment = score_candidate(
        _candidate(
            symbol="NVDA.US",
            name="NVIDIA",
            sector="Technology",
            description="AI芯片龙头，数据中心业务强劲",
            moat_notes="CUDA生态锁定+算力垄断+客户转换成本极高",
            moat_score=8.5,
            moat_types=["technology_moat", "network_effect", "switching_cost"],
        )
    )

    assert assessment["research_priority"] in {"medium", "high"}
    assert assessment["investment_confidence"] != "high"
    assert assessment["evidence_tier"] in {"3 ecosystem mapping", "4 inference"}


def test_core_value_reports_effective_premiums_after_cap():
    analysis = {
        "symbol": "SAMPLE.US",
        "current_price": 100.0,
        "quote_details": {"calc_index": {}},
        "technical_analysis": {},
        "moat_analysis": {
            "moat_width": "Wide",
            "moat_score": 8.0,
        },
    }
    valuation_data = {
        "overview": {"metrics": {"pe": {"metric": "20x"}}},
        "history": {"metrics": {"pe": {"median": "20", "desc": "比近5年 50.0%"}}},
    }
    industry_config = {
        "industries": {
            "sample_growth": {
                "name": "Sample Growth",
                "symbols": ["SAMPLE"],
                "growth_premium": 0.12,
                "thesis": "sample thesis",
            },
            "sample_extra": {
                "name": "Sample Extra",
                "symbols": ["SAMPLE"],
                "growth_premium": 0.08,
                "moat_premium": 0.10,
                "thesis": "extra thesis",
            },
        }
    }

    result = calculate_core_value(analysis, valuation_data, industry_config)

    assert result["raw_growth_premium"] == pytest.approx(0.20)
    assert result["raw_moat_premium"] == pytest.approx(0.15)
    assert result["effective_total_premium"] == pytest.approx(0.15)
    assert result["effective_growth_premium"] + result["effective_moat_premium"] == pytest.approx(0.15)
    assert result["layer2_growth_premium"] == result["effective_growth_premium"]
    assert result["layer3_moat_premium"] == result["effective_moat_premium"]


def test_dcf_only_utility_with_distorted_fcf_is_low_confidence():
    analysis = {
        "valuation_analysis": {
            "p_fcf_ratio": 209.2,
            "fcf_yield": 0.0048,
            "graham_intrinsic_value": 156.71,
        },
        "financial_data": {
            "data_quality": {
                "warnings": [
                    "FCF qf-sum ($-258,750,000) ≠ annual ($268,625,000) — using annual"
                ]
            }
        },
    }
    value_data = {"layer1_value": 199.23}
    dcf_result = {"dcf_value": 11.66}

    reason = _low_confidence_dcf_reason("DUK.US", analysis, value_data, dcf_result, None, 126.58)

    assert reason is not None
    assert reason.startswith("dcf_only_low_confidence")


def test_dcf_with_shiller_is_not_suppressed():
    analysis = {
        "valuation_analysis": {
            "p_fcf_ratio": 80.0,
            "fcf_yield": 0.01,
            "graham_intrinsic_value": 150.0,
        },
        "financial_data": {"data_quality": {"warnings": ["FCF qf-sum mismatch"]}},
    }
    value_data = {"layer1_value": 200.0}
    dcf_result = {"dcf_value": 50.0}
    shiller_result = {"shiller_intrinsic_mid": 120.0}

    reason = _low_confidence_dcf_reason("DUK.US", analysis, value_data, dcf_result, shiller_result, 125.0)

    assert reason is None
