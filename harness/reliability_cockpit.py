#!/usr/bin/env python3
"""Reliability metadata for daily stock-analysis harness runs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from harness.backtest import Backtest  # noqa: E402
from watchlist_utils import load_valuation_disabled_symbols, load_watchlist  # noqa: E402


FAILURE_CLASSES = {
    "auth_or_session",
    "provider_unavailable",
    "timeout",
    "empty_response",
    "invalid_json",
    "missing_cli",
    "unknown",
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def load_manifest(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if isinstance(data, dict):
        return data
    return {}


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now_iso()
    write_json(path, manifest)


def classify_failure(exit_code: int, stderr: str, output: str, label: str) -> str | None:
    if exit_code == 0 and output.strip():
        if label.endswith("_json") or label in {"watchlist_quotes", "positions"}:
            try:
                json.loads(output)
            except json.JSONDecodeError:
                return "invalid_json"
        return None
    combined = f"{stderr}\n{output}".lower()
    if "command not found" in combined or "no such file" in combined or "not found" in combined:
        return "missing_cli"
    if "auth" in combined or "token" in combined or "login" in combined or "permission" in combined:
        return "auth_or_session"
    if "timeout" in combined or "timed out" in combined:
        return "timeout"
    if exit_code == 0 and not output.strip():
        return "empty_response"
    if "json" in combined and ("decode" in combined or "parse" in combined):
        return "invalid_json"
    if "unavailable" in combined or "429" in combined or "rate" in combined or "temporary" in combined:
        return "provider_unavailable"
    return "unknown"


def next_action_for(failure_class: str | None, label: str) -> str:
    if failure_class == "auth_or_session":
        return "Check Longbridge credentials/session, then rerun the daily harness."
    if failure_class == "missing_cli":
        return "Install or expose the Longbridge CLI before rerunning."
    if failure_class == "timeout":
        return "Treat this data as partial and rerun after the provider recovers."
    if failure_class == "empty_response":
        return "Treat this data as unavailable; verify provider output before acting."
    if failure_class == "invalid_json":
        return "Inspect raw output; parser or provider format may have changed."
    if failure_class == "provider_unavailable":
        return "Keep prior market context stale and rerun later."
    if label == "market_environment":
        return "Do not change the position cap from this run alone."
    return "Inspect the command stderr and avoid acting on this partial run."


def init_manifest(args: argparse.Namespace) -> None:
    manifest = {
        "date": args.date,
        "generated_at": now_iso(),
        "updated_at": now_iso(),
        "mode": args.mode,
        "status": "running",
        "skip_reason": args.skip_reason,
        "commands": [],
        "artifacts": {},
        "failures": [],
        "data_quality": {},
        "action_deltas": [],
        "backtest_truth": None,
        "notes": [],
    }
    if args.skip_reason:
        manifest["status"] = "skipped"
        manifest["notes"].append(f"Skipped: {args.skip_reason}")
    save_manifest(args.manifest, manifest)


def record_command(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    output = args.output.read_text(errors="replace") if args.output and args.output.exists() else ""
    stderr = args.stderr.read_text(errors="replace") if args.stderr and args.stderr.exists() else ""
    failure_class = classify_failure(args.exit_code, stderr, output, args.label)
    event = {
        "label": args.label,
        "command": args.command,
        "exit_code": args.exit_code,
        "status": "ok" if failure_class is None else "failed",
        "output_path": str(args.output) if args.output else None,
        "stderr_path": str(args.stderr) if args.stderr else None,
        "failure_class": failure_class,
        "error_summary": stderr.strip()[:500] or (output.strip()[:500] if failure_class else ""),
        "next_action": next_action_for(failure_class, args.label) if failure_class else None,
    }
    manifest.setdefault("commands", []).append(event)
    if args.output:
        manifest.setdefault("artifacts", {})[args.label] = str(args.output)
    if failure_class:
        failure = {k: event[k] for k in ("label", "failure_class", "error_summary", "next_action")}
        manifest.setdefault("failures", []).append(failure)
    save_manifest(args.manifest, manifest)


def assessment_items(path: Path) -> list[dict[str, Any]]:
    data = read_json(path)
    if not isinstance(data, dict):
        return []
    items = data.get("watchlist_assessments")
    return items if isinstance(items, list) else []


def quote_symbols(path: Path) -> set[str]:
    data = read_json(path)
    if isinstance(data, dict) and isinstance(data.get("quotes"), list):
        data = data["quotes"]
    if not isinstance(data, list):
        return set()
    return {str(item.get("symbol")) for item in data if isinstance(item, dict) and item.get("symbol")}


def latest_prior_assessment(predictions_dir: Path, today: str) -> tuple[str | None, Path | None, dict[str, str]]:
    actions: dict[str, str] = {}
    for path in sorted(predictions_dir.glob("assessment-*.json"), reverse=True):
        date = path.name.removeprefix("assessment-").removesuffix(".json")
        if date >= today:
            continue
        items = assessment_items(path)
        if not items:
            continue
        for item in items:
            symbol = item.get("symbol")
            action = item.get("action")
            if symbol and action:
                actions[str(symbol)] = str(action)
        return date, path, actions
    return None, None, actions


def compute_data_quality(
    watchlist: list[str],
    quotes_path: Path,
    assessment_path: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    available_quotes = quote_symbols(quotes_path)
    by_symbol = {str(item.get("symbol")): item for item in assessment_items(assessment_path) if item.get("symbol")}
    valuation_disabled = load_valuation_disabled_symbols()
    failed_labels = {failure.get("label") for failure in manifest.get("failures", [])}
    result: dict[str, Any] = {}
    for symbol in watchlist:
        warnings: list[str] = []
        if "watchlist_quotes" in failed_labels or symbol not in available_quotes:
            warnings.append("missing_quote")
        item = by_symbol.get(symbol)
        if not item and symbol.upper() in valuation_disabled:
            warnings.append("valuation_skipped")
        elif not item:
            warnings.append("missing_assessment")
        else:
            if item.get("data_quality_clean") is False:
                warnings.append("assessment_marked_unclean")
            for warning in item.get("data_quality_warnings") or []:
                if warning:
                    warnings.append(str(warning))
            if item.get("no_pe_anchor"):
                warnings.append("no_pe_anchor")
            if item.get("core_value_source") in {"current_price", "fallback"}:
                warnings.append("valuation_fallback_used")
        if warnings == ["valuation_skipped"]:
            status = "Skipped"
        elif not warnings:
            status = "Clean"
        elif "missing_quote" in warnings or "missing_assessment" in warnings:
            status = "Failed"
        else:
            status = "Partial"
        result[symbol] = {
            "status": status,
            "warnings": warnings,
        }
    return result


def compute_action_deltas(today: str, predictions_dir: Path, assessment_path: Path) -> tuple[list[dict[str, Any]], Path]:
    previous_date, previous_path, previous_actions = latest_prior_assessment(predictions_dir, today)
    deltas: list[dict[str, Any]] = []
    for item in assessment_items(assessment_path):
        symbol = item.get("symbol")
        action = item.get("action")
        if not symbol or not action:
            continue
        prev = previous_actions.get(str(symbol))
        change_type = "new" if prev is None else "changed" if prev != action else "unchanged"
        deltas.append({
            "symbol": symbol,
            "previous_action": prev,
            "current_action": action,
            "change_type": change_type,
            "previous_date": previous_date,
            "reason": action_delta_reason(item),
        })
    output = predictions_dir.parent / "daily" / f"action-delta-{today}.json"
    write_json(output, {"date": today, "previous_date": previous_date, "previous_source": str(previous_path) if previous_path else None, "deltas": deltas})
    return deltas, output


def action_delta_reason(item: dict[str, Any]) -> str:
    deviation = item.get("deviation_pct")
    status = item.get("status")
    source = item.get("core_value_source") or item.get("value_methods")
    bits = []
    if deviation is not None:
        bits.append(f"deviation {deviation}%")
    if status:
        bits.append(str(status))
    if source:
        bits.append(f"source {source}")
    return "; ".join(bits) if bits else "No structured reason available"


def latest_backtest_truth() -> dict[str, Any]:
    try:
        bt = Backtest()
        pair = bt.resolve_latest_backtest_pair()
        if not pair:
            return {"status": "missing", "summary": "No prediction/quote pair available"}
        prediction_date, actual_date = pair
        report_path = bt.backtests_dir / f"backtest-{prediction_date}-{actual_date}.json"
        report = read_json(report_path)
        if not isinstance(report, dict):
            report = bt.generate_backtest_report(prediction_date, actual_date)
        if not isinstance(report, dict):
            return {"status": "missing", "prediction_date": prediction_date, "actual_date": actual_date, "summary": "Backtest report unavailable"}
        return {
            "status": "available",
            "prediction_date": prediction_date,
            "actual_date": actual_date,
            "report_path": str(report_path),
            "metrics": report.get("metrics", {}),
            "passed_thresholds": report.get("passed_thresholds", {}),
            "symbols_matched": sorted(report.get("symbols_matched", [])),
        }
    except Exception as exc:  # Defensive: report generation must not break daily reporting.
        return {"status": "failed", "summary": str(exc)[:500]}


def finalize_manifest(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    watchlist = load_watchlist()
    if args.report.exists():
        manifest.setdefault("artifacts", {})["report"] = str(args.report)
    if args.market_environment.exists():
        manifest.setdefault("artifacts", {})["market_environment"] = str(args.market_environment)
    if args.assessment.exists():
        manifest.setdefault("artifacts", {})["assessment"] = str(args.assessment)
    if args.positions.exists():
        manifest.setdefault("artifacts", {})["positions"] = str(args.positions)
    if args.options and args.options.is_file():
        manifest.setdefault("artifacts", {})["options"] = str(args.options)

    manifest["data_quality"] = compute_data_quality(watchlist, args.quotes, args.assessment, manifest)
    deltas, delta_path = compute_action_deltas(args.date, args.predictions_dir, args.assessment)
    manifest["action_deltas"] = deltas
    manifest.setdefault("artifacts", {})["action_delta"] = str(delta_path)
    manifest["backtest_truth"] = latest_backtest_truth()

    failures = manifest.get("failures", [])
    if failures:
        manifest["status"] = "partial"
    elif manifest.get("status") == "running":
        manifest["status"] = "fresh"
    save_manifest(args.manifest, manifest)


def trust_status(manifest: dict[str, Any]) -> str:
    status = manifest.get("status", "unknown")
    if status == "fresh":
        return "Fresh"
    if status == "partial":
        return "Partial"
    if status == "skipped":
        return "Skipped"
    if status == "failed":
        return "Failed"
    return "Unknown"


def short_action(action: Any) -> str:
    if action in (None, ""):
        return "N/A"
    return str(action)


def render_sections(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    trust = trust_status(manifest)
    failures = manifest.get("failures", [])
    dq = manifest.get("data_quality", {})
    partial_count = sum(1 for value in dq.values() if value.get("status") == "Partial")
    failed_count = sum(1 for value in dq.values() if value.get("status") == "Failed")
    skipped_count = sum(1 for value in dq.values() if value.get("status") == "Skipped")
    clean_count = len(dq) - partial_count - failed_count - skipped_count
    lines = [
        "## Trust Header",
        f"- **Run Status:** {trust}",
        f"- **Manifest:** {args.manifest}",
        f"- **Generated At:** {manifest.get('generated_at', 'N/A')}",
    ]
    if manifest.get("skip_reason"):
        lines.append(f"- **Skip Reason:** {manifest['skip_reason']}")
    quality_line = f"- **Data Quality:** {clean_count} clean / {partial_count} partial / {failed_count} failed"
    if skipped_count:
        quality_line += f" / {skipped_count} skipped"
    lines.append(quality_line)
    if failures:
        lines.append(f"- **Data Source Failures:** {len(failures)}")
    else:
        lines.append("- **Data Source Failures:** none")

    lines.extend(["", "## Backtest Truth Strip"])
    truth = manifest.get("backtest_truth") or {}
    if truth.get("status") == "available":
        metrics = truth.get("metrics", {})
        lines.append(f"- **Latest Pair:** {truth.get('prediction_date')} -> {truth.get('actual_date')}")
        lines.append(f"- **Direction Accuracy:** {percent(metrics.get('price_direction_accuracy'))}")
        lines.append(f"- **Target Accuracy:** {percent(metrics.get('target_price_accuracy'))}")
        lines.append(f"- **Recommendation Accuracy:** {percent(metrics.get('recommendation_accuracy'))}")
        lines.append(f"- **Backtest Report:** {truth.get('report_path')}")
    else:
        lines.append(f"- **Status:** {truth.get('status', 'missing')}")
        lines.append(f"- **Summary:** {truth.get('summary', 'No recent backtest truth available')}")

    lines.extend(["", "## Action Deltas"])
    changed = [d for d in manifest.get("action_deltas", []) if d.get("change_type") != "unchanged"]
    if changed:
        for delta in changed:
            lines.append(
                f"- **{delta['symbol']}**: {short_action(delta.get('previous_action'))} -> "
                f"{short_action(delta.get('current_action'))} ({delta.get('reason', 'N/A')})"
            )
    else:
        lines.append("- No action changes versus the previous valid assessment.")

    if failures:
        lines.extend(["", "## Data Source Failures"])
        for failure in failures:
            lines.append(f"- **{failure.get('label')}**: {failure.get('failure_class')} — {failure.get('next_action')}")
            if failure.get("error_summary"):
                lines.append(f"  - Error: `{clean_inline(failure['error_summary'])}`")

    args.output.write_text("\n".join(lines) + "\n")


def percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def clean_inline(value: str) -> str:
    return re.sub(r"\s+", " ", value).replace("`", "'")[:220]


def data_badge(args: argparse.Namespace) -> None:
    manifest = load_manifest(args.manifest)
    item = manifest.get("data_quality", {}).get(args.symbol, {})
    status = item.get("status", "Unknown")
    warnings = item.get("warnings") or []
    if warnings:
        print(f"{status}: {', '.join(str(w) for w in warnings[:2])}")
    else:
        print(status)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily harness reliability cockpit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init-manifest")
    p.add_argument("--date", required=True)
    p.add_argument("--mode", default="daily")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--skip-reason")
    p.set_defaults(func=init_manifest)

    p = sub.add_parser("record-command")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--command", required=True)
    p.add_argument("--exit-code", type=int, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--stderr", type=Path)
    p.set_defaults(func=record_command)

    p = sub.add_parser("finalize-manifest")
    p.add_argument("--date", required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--quotes", type=Path, required=True)
    p.add_argument("--assessment", type=Path, required=True)
    p.add_argument("--market-environment", type=Path, required=True)
    p.add_argument("--positions", type=Path, required=True)
    p.add_argument("--options", type=Path)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--predictions-dir", type=Path, required=True)
    p.set_defaults(func=finalize_manifest)

    p = sub.add_parser("render-sections")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.set_defaults(func=render_sections)

    p = sub.add_parser("data-badge")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--symbol", required=True)
    p.set_defaults(func=data_badge)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
