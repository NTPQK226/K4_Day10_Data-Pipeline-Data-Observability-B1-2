"""3-state recovery analysis: baseline → corrupted → repaired.

CP6 deliverable:
  - Delta table for all three states on every metric
  - Per-answer recovery classification (recovered / consistent_hit / consistent_miss / newly_broken)
  - Representative demo cases: one honest hit (recovery worked) and one honest miss (still broken)
  - Recovery completeness verdict per metric
  - Explicit limitations to guard against over-conclusion
"""
from __future__ import annotations

from typing import Any

_FULL_RECOVERY_THRESHOLD = 0.02   # |repaired - baseline| < this → "full"
_PARTIAL_THRESHOLD = 0.0          # repaired > corrupted (any improvement) → "partial"


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def _three_state_delta(
    baseline: dict[str, Any],
    corrupted: dict[str, Any],
    repaired: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    b = baseline.get(key)
    c = corrupted.get(key)
    r = repaired.get(key)
    available = all(isinstance(v, (int, float)) for v in [b, c, r] if v is not None)
    if not available or b is None or c is None or r is None:
        return {
            "baseline": b, "corrupted": c, "repaired": r,
            "delta_corrupt": None, "delta_repair": None, "delta_recover": None,
            "available": False, "recovery_status": "unknown",
        }
    delta_corrupt = round(c - b, 4)   # baseline → corrupted (negative = degraded)
    delta_repair = round(r - b, 4)    # baseline → repaired  (0 = full recovery)
    delta_recover = round(r - c, 4)   # corrupted → repaired (positive = improved)

    if abs(delta_repair) < _FULL_RECOVERY_THRESHOLD:
        recovery_status = "full"
    elif delta_recover > _PARTIAL_THRESHOLD:
        recovery_status = "partial"
    else:
        recovery_status = "none"

    return {
        "baseline": b,
        "corrupted": c,
        "repaired": r,
        "delta_corrupt": delta_corrupt,
        "delta_repair": delta_repair,
        "delta_recover": delta_recover,
        "available": True,
        "recovery_status": recovery_status,
    }


# ---------------------------------------------------------------------------
# Quality gate 3-state comparison
# ---------------------------------------------------------------------------

def _quality_three_state(
    baseline_quality: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
) -> list[dict[str, Any]]:
    b_checks = {ch["check"]: ch for ch in baseline_quality.get("checks", [])}
    c_checks = {ch["check"]: ch for ch in corrupted_quality.get("checks", [])}
    r_checks = {ch["check"]: ch for ch in repaired_quality.get("checks", [])}
    all_names = sorted(set(b_checks) | set(c_checks) | set(r_checks))
    result = []
    for name in all_names:
        b_ok = b_checks.get(name, {}).get("passed")
        c_ok = c_checks.get(name, {}).get("passed")
        r_ok = r_checks.get(name, {}).get("passed")
        # Recovery: was it broken by corruption and fixed by repair?
        if c_ok is False and r_ok is True:
            gate_recovery = "recovered"
        elif c_ok is False and r_ok is False:
            gate_recovery = "still_failing"
        elif c_ok is True and r_ok is True:
            gate_recovery = "stable"
        else:
            gate_recovery = "unknown"
        result.append({
            "check": name,
            "baseline": b_ok,
            "corrupted": c_ok,
            "repaired": r_ok,
            "gate_recovery": gate_recovery,
            "corrupted_detail": c_checks.get(name, {}).get("detail", ""),
            "repaired_detail": r_checks.get(name, {}).get("detail", ""),
        })
    return result


# ---------------------------------------------------------------------------
# Per-answer recovery classification
# ---------------------------------------------------------------------------

_ANSWER_RECOVERY_LABELS = {
    (True, True): "consistent_hit",      # good in both states
    (False, False): "consistent_miss",   # broken in both states — repair didn't fix
    (False, True): "recovered",          # corruption caused miss, repair fixed it
    (True, False): "newly_broken",       # repair made it worse (should be rare)
}


def _classify_answers(
    corrupted_answers: list[dict[str, Any]],
    repaired_answers: list[dict[str, Any]],
    baseline_answers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Per-question 3-state classification."""
    corrupted_map = {a["id"]: a for a in corrupted_answers if "id" in a}
    repaired_map = {a["id"]: a for a in repaired_answers if "id" in a}
    baseline_map = {a["id"]: a for a in baseline_answers if "id" in a}

    all_ids = sorted(set(corrupted_map) | set(repaired_map))
    classified = []
    for qid in all_ids:
        ca = corrupted_map.get(qid, {})
        ra = repaired_map.get(qid, {})
        ba = baseline_map.get(qid, {})
        c_hit = ca.get("retrieval_hit", False)
        r_hit = ra.get("retrieval_hit", False)
        label = _ANSWER_RECOVERY_LABELS.get((c_hit, r_hit), "unknown")
        classified.append({
            "id": qid,
            "question": ca.get("question") or ra.get("question"),
            "question_type": ca.get("question_type") or ra.get("question_type"),
            "baseline_token_f1": round(ba.get("token_f1", 0.0), 4) if ba else None,
            "corrupted_token_f1": round(ca.get("token_f1", 0.0), 4),
            "repaired_token_f1": round(ra.get("token_f1", 0.0), 4),
            "corrupted_retrieval_hit": c_hit,
            "repaired_retrieval_hit": r_hit,
            "corrupted_judge_score": ca.get("judge", {}).get("score"),
            "repaired_judge_score": ra.get("judge", {}).get("score"),
            "recovery_label": label,
        })
    return classified


def _pick_demo_cases(
    classified: list[dict[str, Any]],
    corrupted_answers: list[dict[str, Any]],
    repaired_answers: list[dict[str, Any]],
    baseline_answers: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Pick one honest representative demo case for each outcome:
    - demo_hit: a case that RECOVERED (corrupted miss → repaired hit)
    - demo_miss: a case that STILL FAILS (consistent_miss even after repair)
    - demo_stable: a case that was always correct (consistent_hit, shows baseline held)
    """
    corrupted_map = {a["id"]: a for a in corrupted_answers if "id" in a}
    repaired_map = {a["id"]: a for a in repaired_answers if "id" in a}
    baseline_map = {a["id"]: a for a in baseline_answers if "id" in a}

    demo_hit = None
    demo_miss = None
    demo_stable = None

    # Sort by token_f1 improvement for most illustrative case
    recovered = sorted(
        [c for c in classified if c["recovery_label"] == "recovered"],
        key=lambda x: (x["repaired_token_f1"] or 0) - (x["corrupted_token_f1"] or 0),
        reverse=True,
    )
    consistent_miss = [c for c in classified if c["recovery_label"] == "consistent_miss"]
    consistent_hit = sorted(
        [c for c in classified if c["recovery_label"] == "consistent_hit"],
        key=lambda x: x["repaired_token_f1"] or 0,
        reverse=True,
    )

    def _build_demo(entry: dict) -> dict[str, Any]:
        qid = entry["id"]
        ca = corrupted_map.get(qid, {})
        ra = repaired_map.get(qid, {})
        ba = baseline_map.get(qid, {})
        return {
            **entry,
            "baseline_answer_excerpt": (ba.get("answer") or "")[:300] if ba else None,
            "corrupted_answer_excerpt": (ca.get("answer") or "")[:300],
            "repaired_answer_excerpt": (ra.get("answer") or "")[:300],
            "baseline_judge_reasoning": (ba.get("judge", {}).get("reasoning") or "") if ba else None,
            "corrupted_judge_reasoning": (ca.get("judge", {}).get("reasoning") or "")[:200],
            "repaired_judge_reasoning": (ra.get("judge", {}).get("reasoning") or "")[:200],
            "ground_truth_excerpt": (ca.get("ground_truth") or ra.get("ground_truth") or "")[:200],
        }

    if recovered:
        demo_hit = _build_demo(recovered[0])
    if consistent_miss:
        demo_miss = _build_demo(consistent_miss[0])
    if consistent_hit:
        demo_stable = _build_demo(consistent_hit[0])

    return {"demo_hit": demo_hit, "demo_miss": demo_miss, "demo_stable": demo_stable}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def analyze_recovery(
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    baseline_quality: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    baseline_freshness: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
    baseline_answers: list[dict[str, Any]],
    corrupted_answers: list[dict[str, Any]],
    repaired_answers: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Full 3-state recovery analysis.

    Returns:
    - metric_recovery: per-metric 3-state deltas + recovery_status
    - quality_recovery: per-check 3-state comparison
    - freshness_recovery: is_fresh for all 3 states
    - answer_classification: per-question recovery label
    - demo_cases: representative hit / miss / stable cases
    - recovery_summary: overall verdict and limitations
    """
    metric_keys = ["retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"]
    metric_recovery = {
        k: _three_state_delta(baseline_metrics, corrupted_metrics, repaired_metrics, k)
        for k in metric_keys
    }

    quality_recovery = _quality_three_state(baseline_quality, corrupted_quality, repaired_quality)

    freshness_recovery = {
        "baseline_fresh": baseline_freshness.get("is_fresh"),
        "corrupted_fresh": corrupted_freshness.get("is_fresh"),
        "repaired_fresh": repaired_freshness.get("is_fresh"),
        "baseline_stale_ratio": baseline_freshness.get("stale_ratio"),
        "corrupted_stale_ratio": corrupted_freshness.get("stale_ratio"),
        "repaired_stale_ratio": repaired_freshness.get("stale_ratio"),
        "freshness_recovered": (
            corrupted_freshness.get("is_fresh") is False
            and repaired_freshness.get("is_fresh") is True
        ),
    }

    answers_available = bool(corrupted_answers and repaired_answers)
    answer_classification: list[dict[str, Any]] = []
    demo_cases: dict[str, Any] = {}
    if answers_available:
        answer_classification = _classify_answers(corrupted_answers, repaired_answers, baseline_answers)
        demo_cases = _pick_demo_cases(
            answer_classification, corrupted_answers, repaired_answers, baseline_answers
        )

    # Recovery counts across quality gates
    gate_recovered = sum(1 for g in quality_recovery if g["gate_recovery"] == "recovered")
    gate_still_failing = sum(1 for g in quality_recovery if g["gate_recovery"] == "still_failing")
    gate_stable = sum(1 for g in quality_recovery if g["gate_recovery"] == "stable")

    # Metric recovery summary
    metrics_available = all(v["available"] for v in metric_recovery.values())
    full_recovered_metrics = [k for k, v in metric_recovery.items() if v["recovery_status"] == "full"]
    partial_recovered_metrics = [k for k, v in metric_recovery.items() if v["recovery_status"] == "partial"]
    not_recovered_metrics = [k for k, v in metric_recovery.items() if v["recovery_status"] == "none"]

    # Answer recovery counts
    label_counts: dict[str, int] = {}
    for entry in answer_classification:
        label_counts[entry["recovery_label"]] = label_counts.get(entry["recovery_label"], 0) + 1

    # Limitations
    limitations: list[str] = []
    if not metrics_available:
        limitations.append(
            "Metric files (baseline_metrics.json, corrupted_metrics.json, repaired_metrics.json) "
            "are not available — run `run_corruption_flow.py` to generate them. "
            "Metric recovery verdict is 'unknown' until then."
        )
    if not answers_available:
        limitations.append(
            "Answer files not available — per-question recovery classification and demo cases "
            "cannot be computed. Run the full corruption flow to generate answer artifacts."
        )
    if gate_still_failing > 0:
        limitations.append(
            f"{gate_still_failing} quality gate(s) still failing after repair — "
            "repair is not complete on quality dimension."
        )
    if partial_recovered_metrics:
        limitations.append(
            f"Metrics {partial_recovered_metrics} only partially recovered — "
            "repaired index performs better than corrupted but not as well as baseline."
        )
    if not_recovered_metrics:
        limitations.append(
            f"Metrics {not_recovered_metrics} did not recover — "
            "repair from raw source was insufficient to restore these signals."
        )

    return {
        "metric_recovery": metric_recovery,
        "quality_recovery": quality_recovery,
        "freshness_recovery": freshness_recovery,
        "answer_classification": answer_classification,
        "demo_cases": demo_cases,
        "recovery_summary": {
            "metrics_available": metrics_available,
            "answers_available": answers_available,
            "full_recovered_metrics": full_recovered_metrics,
            "partial_recovered_metrics": partial_recovered_metrics,
            "not_recovered_metrics": not_recovered_metrics,
            "gate_recovered": gate_recovered,
            "gate_still_failing": gate_still_failing,
            "gate_stable": gate_stable,
            "freshness_recovered": freshness_recovery["freshness_recovered"],
            "answer_label_counts": label_counts,
            "limitations": limitations,
        },
    }
