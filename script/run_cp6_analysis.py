"""Checkpoint 6 — 3-state recovery analysis runner.

Loads baseline / corrupted / repaired artifacts (all files now present in
data/results/ and data/quality/) and produces:
  - data/results/cp6_analysis.json   (structured analysis with all deltas)
  - data/reports/cp6_report.md       (full comparison + demo cases report)

Run:
    uv run python script/run_cp6_analysis.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure this project's src takes precedence over the editable-install path.
_this_src = Path(__file__).resolve().parents[1] / "src"
if str(_this_src) not in sys.path:
    sys.path.insert(0, str(_this_src))

from core.config import load_settings
from core.utils import read_json, write_json
from observability.recovery import analyze_recovery
from observability.reporting import generate_cp6_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _load(path: Path):
    log.info("  Load: %s", path)
    return read_json(path)


def _load_optional(path: Path, default):
    if path.exists():
        return _load(path)
    log.warning("  Not found (optional): %s", path)
    return default


def main() -> None:
    log.info("=== Checkpoint 6: 3-State Recovery Analysis ===")
    settings = load_settings()
    paths = settings.paths
    quality_dir = paths.quality_dir

    log.info("[1] Loading quality & freshness — all 3 states...")
    baseline_quality = _load(quality_dir / "baseline_quality.json")
    baseline_freshness = _load(paths.freshness_report)
    corrupted_quality = _load(quality_dir / "corrupted_quality.json")
    corrupted_freshness = _load(quality_dir / "corrupted_freshness.json")
    repaired_quality = _load(quality_dir / "repaired_quality.json")
    repaired_freshness = _load(quality_dir / "repaired_freshness.json")

    log.info("[2] Loading metrics — all 3 states...")
    # metrics files are flat dicts (no "summary" wrapper)
    baseline_metrics = _load(paths.baseline_metrics)
    corrupted_metrics = _load(paths.corrupted_metrics)
    repaired_metrics = _load(paths.repaired_metrics)

    log.info("[3] Loading answers — all 3 states...")
    baseline_answers = _load(paths.baseline_answers)
    corrupted_answers = _load(paths.corrupted_answers)
    repaired_answers = _load(paths.repaired_answers)

    log.info("[4] Running 3-state recovery analysis...")
    result = analyze_recovery(
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        baseline_quality=baseline_quality,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        baseline_freshness=baseline_freshness,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
        baseline_answers=baseline_answers,
        corrupted_answers=corrupted_answers,
        repaired_answers=repaired_answers,
    )

    analysis_path = paths.quality_dir.parent / "results" / "cp6_analysis.json"
    write_json(analysis_path, result)
    log.info("[5] Saved analysis JSON: %s", analysis_path)

    report_path = paths.baseline_report.parent / "cp6_report.md"
    generate_cp6_report(report_path=report_path, recovery=result)
    log.info("[6] Saved Markdown report: %s", report_path)

    # ── Print summary ──────────────────────────────────────────────────────
    summary = result.get("recovery_summary", {})
    fr = result.get("freshness_recovery", {})
    mr = result.get("metric_recovery", {})

    log.info("=== 3-State Metric Deltas ===")
    for key, v in mr.items():
        log.info(
            "  %-25s  baseline=%.3f  corrupted=%.3f  repaired=%.3f  "
            "Δcorrupt=%+.3f  Δrepair=%+.3f  → %s",
            key,
            v.get("baseline", 0), v.get("corrupted", 0), v.get("repaired", 0),
            v.get("delta_corrupt", 0), v.get("delta_repair", 0),
            v.get("recovery_status", "?").upper(),
        )

    log.info("=== Quality Gates ===")
    log.info(
        "  %d recovered · %d still failing · %d stable",
        summary.get("gate_recovered", 0),
        summary.get("gate_still_failing", 0),
        summary.get("gate_stable", 0),
    )

    log.info("=== Freshness ===")
    log.info(
        "  baseline=%s  corrupted=%s  repaired=%s  | freshness_recovered=%s",
        fr.get("baseline_fresh"), fr.get("corrupted_fresh"),
        fr.get("repaired_fresh"), fr.get("freshness_recovered"),
    )

    log.info("=== Per-Answer Recovery ===")
    lc = summary.get("answer_label_counts", {})
    log.info(
        "  recovered=%d  consistent_hit=%d  consistent_miss=%d  newly_broken=%d",
        lc.get("recovered", 0), lc.get("consistent_hit", 0),
        lc.get("consistent_miss", 0), lc.get("newly_broken", 0),
    )

    limits = summary.get("limitations", [])
    if limits:
        log.warning("=== Limitations (%d) ===", len(limits))
        for lim in limits:
            log.warning("  - %s", lim)
    else:
        log.info("=== No limitations — full data available ===")

    log.info("=== Checkpoint 6 COMPLETE ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error("CP6 analysis failed: %s", exc)
        raise SystemExit(1)
