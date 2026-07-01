#!/usr/bin/env python3
"""Tests for daily reliability cockpit metadata."""

from __future__ import annotations

import json
from argparse import Namespace

from harness import reliability_cockpit as rc


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def test_classify_auth_failure():
    failure = rc.classify_failure(
        1,
        "Longbridge token expired, please login again",
        "",
        "watchlist_quotes",
    )

    assert failure == "auth_or_session"
    assert "credentials" in rc.next_action_for(failure, "watchlist_quotes")


def test_init_manifest_records_skip_reason(tmp_path):
    manifest_path = tmp_path / "run-manifest-2026-06-28.json"

    rc.init_manifest(Namespace(
        date="2026-06-28",
        mode="daily",
        manifest=manifest_path,
        skip_reason="No completed US trading session",
    ))

    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == "skipped"
    assert manifest["skip_reason"] == "No completed US trading session"


def test_compute_action_deltas_against_previous_assessment(tmp_path):
    predictions = tmp_path / "predictions"
    write_json(predictions / "assessment-2026-06-26.json", {
        "watchlist_assessments": [
            {"symbol": "BABA.US", "action": "HOLD"},
            {"symbol": "NVDA.US", "action": "AVOID"},
        ]
    })
    current = predictions / "assessment-2026-06-27.json"
    write_json(current, {
        "watchlist_assessments": [
            {"symbol": "BABA.US", "action": "BUY_SMALL", "deviation_pct": -8.7, "status": "undervalued"},
            {"symbol": "NVDA.US", "action": "AVOID"},
        ]
    })

    deltas, output = rc.compute_action_deltas("2026-06-27", predictions, current)

    baba = next(delta for delta in deltas if delta["symbol"] == "BABA.US")
    nvda = next(delta for delta in deltas if delta["symbol"] == "NVDA.US")
    assert baba["previous_action"] == "HOLD"
    assert baba["current_action"] == "BUY_SMALL"
    assert baba["change_type"] == "changed"
    assert nvda["change_type"] == "unchanged"
    assert output.exists()


def test_compute_data_quality_marks_partial_and_failed(tmp_path):
    quotes = tmp_path / "quotes.json"
    assessment = tmp_path / "assessment.json"
    write_json(quotes, [{"symbol": "BABA.US", "last": "95.07"}])
    write_json(assessment, {
        "watchlist_assessments": [
            {
                "symbol": "BABA.US",
                "action": "BUY_SMALL",
                "data_quality_clean": True,
                "data_quality_warnings": ["FCF mismatch"],
            }
        ]
    })

    quality = rc.compute_data_quality(
        ["BABA.US", "NVDA.US"],
        quotes,
        assessment,
        {"failures": []},
    )

    assert quality["BABA.US"]["status"] == "Partial"
    assert "FCF mismatch" in quality["BABA.US"]["warnings"]
    assert quality["NVDA.US"]["status"] == "Failed"
    assert "missing_quote" in quality["NVDA.US"]["warnings"]


def test_render_sections_includes_trust_backtest_and_failures(tmp_path):
    manifest = tmp_path / "manifest.json"
    output = tmp_path / "sections.md"
    write_json(manifest, {
        "status": "partial",
        "generated_at": "2026-06-28T09:40:00",
        "failures": [
            {
                "label": "watchlist_quotes",
                "failure_class": "timeout",
                "next_action": "Rerun later",
                "error_summary": "request timed out",
            }
        ],
        "data_quality": {
            "BABA.US": {"status": "Clean", "warnings": []},
            "NVDA.US": {"status": "Failed", "warnings": ["missing_quote"]},
        },
        "action_deltas": [
            {
                "symbol": "BABA.US",
                "previous_action": "HOLD",
                "current_action": "BUY_SMALL",
                "change_type": "changed",
                "reason": "deviation -8.7%",
            }
        ],
        "backtest_truth": {
            "status": "available",
            "prediction_date": "2026-06-26",
            "actual_date": "2026-06-26",
            "report_path": "/tmp/backtest.json",
            "metrics": {
                "price_direction_accuracy": 0.6364,
                "target_price_accuracy": 0,
                "recommendation_accuracy": 0.6364,
            },
        },
    })

    rc.render_sections(Namespace(manifest=manifest, output=output))

    text = output.read_text()
    assert "## Trust Header" in text
    assert "**Run Status:** Partial" in text
    assert "## Backtest Truth Strip" in text
    assert "63.6%" in text
    assert "HOLD -> BUY_SMALL" in text
    assert "watchlist_quotes" in text
