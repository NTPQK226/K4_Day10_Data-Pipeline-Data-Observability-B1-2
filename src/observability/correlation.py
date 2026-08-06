"""Correlate corruption log entries with quality signals and metric changes.

Checkpoint 5 deliverable: links each corruption type to:
  - which quality check it triggers (or None if no structural gate covers it)
  - whether that quality check passed or failed after corruption
  - the metric delta it contributed to
  - the worst-degraded individual QA case (with evidence)
  - signals that stayed unchanged (guard against over-conclusion)
"""
from __future__ import annotations

from typing import Any

# Maps each corruption type to the quality-gate check name it should trip.
# None means the corruption is semantic/representational — no structural gate catches it,
# but its impact shows up in evaluation metrics (token_f1, judge_score).
_CORRUPTION_TO_QUALITY_CHECK: dict[str, str | None] = {
    "blank_summary": "summary_not_blank",
    "duplicate_row": "paper_id_unique",
    "drop_latest_record": "row_count",
    "stale_published_date": "freshness_age_days",
    "truncate_title": None,   # breaks exact-title lookup; no structural quality check
    "inject_noise": None,     # degrades token_f1 / judge score; no structural quality check
}

# Metric keys that are expected to be impacted by specific corruption types.
_CORRUPTION_METRIC_IMPACT: dict[str, list[str]] = {
    "blank_summary": ["retrieval_hit_rate", "mean_token_f1"],
    "inject_noise": ["mean_token_f1", "judge_accuracy", "mean_judge_score"],
    "drop_latest_record": ["retrieval_hit_rate"],
    "truncate_title": ["retrieval_hit_rate"],
    "stale_published_date": [],  # freshness signal, not directly a retrieval metric
    "duplicate_row": ["retrieval_hit_rate"],
}

_STABLE_THRESHOLD = 0.02  # |delta| < threshold → signal is stable


def _metric_delta(baseline: dict[str, Any], corrupted: dict[str, Any], key: str) -> dict[str, Any]:
    b = baseline.get(key)
    c = corrupted.get(key)
    if b is None or c is None:
        return {"baseline": b, "corrupted": c, "delta": None, "available": False}
    if isinstance(b, (int, float)) and isinstance(c, (int, float)):
        delta = round(c - b, 4)
    else:
        delta = None
    return {"baseline": b, "corrupted": c, "delta": delta, "available": True}


def _detect_fallback_judges(answers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return entries where the judge silently fell back to the heuristic."""
    marker = "Fallback heuristic judge"
    return [
        {
            "id": a.get("id"),
            "question": a.get("question"),
            "token_f1": a.get("token_f1"),
            "judge_score": a.get("judge", {}).get("score"),
            "judge_correct": a.get("judge", {}).get("correct"),
            "judge_reasoning": a.get("judge", {}).get("reasoning", ""),
        }
        for a in answers
        if marker in a.get("judge", {}).get("reasoning", "")
    ]


def _find_worst_degraded_case(
    baseline_answers: list[dict[str, Any]],
    corrupted_answers: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return the QA item with the largest token_f1 drop (baseline → corrupted)."""
    baseline_map = {a["id"]: a for a in baseline_answers if "id" in a}
    worst: dict[str, Any] | None = None
    worst_delta = 0.0

    for ca in corrupted_answers:
        item_id = ca.get("id")
        ba = baseline_map.get(item_id)
        if ba is None:
            continue
        delta = ca.get("token_f1", 0.0) - ba.get("token_f1", 0.0)
        if delta < worst_delta:
            worst_delta = delta
            worst = {
                "id": item_id,
                "question": ca.get("question"),
                "question_type": ca.get("question_type"),
                "baseline_token_f1": round(ba.get("token_f1", 0.0), 4),
                "corrupted_token_f1": round(ca.get("token_f1", 0.0), 4),
                "token_f1_delta": round(delta, 4),
                "baseline_judge_score": ba.get("judge", {}).get("score"),
                "corrupted_judge_score": ca.get("judge", {}).get("score"),
                "baseline_retrieval_hit": ba.get("retrieval_hit"),
                "corrupted_retrieval_hit": ca.get("retrieval_hit"),
                "baseline_answer_excerpt": (ba.get("answer") or "")[:300],
                "corrupted_answer_excerpt": (ca.get("answer") or "")[:300],
                "baseline_judge_reasoning": ba.get("judge", {}).get("reasoning", ""),
                "corrupted_judge_reasoning": ca.get("judge", {}).get("reasoning", ""),
            }

    return worst


def correlate_corruption_signals(
    corruption_log: dict[str, Any],
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    corrupted_answers: list[dict[str, Any]],
    baseline_answers: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Link each corruption type to the quality signal it trips and the metric it changes.

    Returns a structured dict with:
    - corruption_type_analysis: per-type breakdown
    - metric_changes: baseline vs corrupted deltas for each metric
    - stable_signals: metric keys where |delta| < threshold (no meaningful change)
    - changed_signals: metric keys with meaningful degradation
    - worst_degraded_case: individual QA item with the largest token_f1 drop
    - evaluator_fallback_cases: answers where judge used heuristic fallback
    - freshness_signal: summary from corrupted freshness report
    """
    corruptions = corruption_log.get("corruptions", [])
    quality_checks = {ch["check"]: ch for ch in corrupted_quality.get("checks", [])}

    # Group corruption entries by type
    by_type: dict[str, list[dict]] = {}
    for entry in corruptions:
        by_type.setdefault(entry["type"], []).append(entry)

    # Per-type analysis: quality gate + expected metric impact
    type_analysis: list[dict[str, Any]] = []
    for ctype, entries in sorted(by_type.items()):
        check_name = _CORRUPTION_TO_QUALITY_CHECK.get(ctype)
        check = quality_checks.get(check_name) if check_name else None
        type_analysis.append({
            "corruption_type": ctype,
            "count": len(entries),
            "quality_gate": check_name,
            "quality_gate_passed": check.get("passed") if check else None,
            "quality_gate_detail": check.get("detail") if check else "No structural quality gate — impact visible in evaluation metrics only.",
            "expected_metric_impact": _CORRUPTION_METRIC_IMPACT.get(ctype, []),
            "affected_paper_ids": [e.get("paper_id") for e in entries],
        })

    # Metric deltas: baseline → corrupted
    metric_keys = ["retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"]
    metric_changes = {k: _metric_delta(baseline_metrics, corrupted_metrics, k) for k in metric_keys}

    # Classify signals as stable vs changed
    stable_signals: list[str] = []
    changed_signals: list[str] = []
    for k, v in metric_changes.items():
        if not v["available"]:
            continue  # can't classify without both values
        delta = v["delta"]
        if delta is None:
            continue
        if abs(delta) < _STABLE_THRESHOLD:
            stable_signals.append(k)
        else:
            changed_signals.append(k)

    # Freshness signal summary
    freshness_signal = {
        "is_fresh": corrupted_freshness.get("is_fresh"),
        "stale_ratio": corrupted_freshness.get("stale_ratio"),
        "stale_rows": corrupted_freshness.get("stale_rows"),
        "total_rows": corrupted_freshness.get("total_rows"),
        "threshold_days": corrupted_freshness.get("freshness_threshold_days"),
        "changed": not corrupted_freshness.get("is_fresh", True),
    }

    # Worst degraded individual case
    worst_case = _find_worst_degraded_case(baseline_answers, corrupted_answers)

    # Evaluator fallback detection (item 3 of checkpoint)
    fallback_cases = _detect_fallback_judges(corrupted_answers)

    return {
        "corruption_type_analysis": type_analysis,
        "metric_changes": metric_changes,
        "stable_signals": stable_signals,
        "changed_signals": changed_signals,
        "worst_degraded_case": worst_case,
        "evaluator_fallback_cases": fallback_cases,
        "evaluator_fallback_count": len(fallback_cases),
        "evaluator_fallback_detected": len(fallback_cases) > 0,
        "freshness_signal": freshness_signal,
        "summary": {
            "total_corruptions": len(corruptions),
            "corruption_types": list(by_type.keys()),
            "quality_gates_failed": corrupted_quality.get("checks_failed", 0),
            "quality_gates_total": corrupted_quality.get("checks_total", 0),
            "metrics_available": all(v["available"] for v in metric_changes.values()),
        },
    }
