r"""Corruption Flow Pipeline: Corrupt -> Evaluate -> Repair -> Compare.

Run: uv run python script/run_corruption_flow.py
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    log.info("=== Phase 2: Corruption, Observability & Self-Healing Pipeline ===")
    settings = load_settings()

    # 1. Load baseline dataset & metrics
    clean_csv_path = settings.paths.clean_csv
    if not clean_csv_path.exists():
        log.error("Clean CSV not found at %s. Please run Phase 1 baseline first.", clean_csv_path)
        raise FileNotFoundError(f"Clean CSV not found: {clean_csv_path}")

    log.info("[Step 1] Loading clean baseline dataset: %s", clean_csv_path)
    clean_df = pd.read_csv(clean_csv_path)
    log.info("  Baseline clean rows: %d", len(clean_df))

    baseline_metrics = {}
    if settings.paths.baseline_metrics.exists():
        baseline_metrics = read_json(settings.paths.baseline_metrics)
    else:
        log.warning("Baseline metrics not found at %s; continuing with empty baseline summary.", settings.paths.baseline_metrics)

    # 2. Corrupt dataset
    log.info("[Step 2] Corrupting clean dataset with 6 controlled error scenarios...")
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    log.info("  Saved corrupted clean artifacts: %s (%d rows)", settings.paths.corrupted_clean_csv, len(corrupted_df))

    # 3. Build corrupted Chroma index
    log.info("[Step 3] Building corrupted RAG index (collection: %s)...", settings.corrupted_collection_name)
    corrupted_idx = LocalEmbeddingIndex.build(
        df=corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    log.info("  Corrupted index built: %d documents", len(corrupted_idx.documents))

    # 4. Evaluate corrupted index
    log.info("[Step 4] Evaluating corrupted RAG pipeline on test set...")
    corrupted_eval = evaluate_pipeline(
        settings=settings,
        index=corrupted_idx,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    c_m = corrupted_eval.summary
    log.info(
        "  Corrupted Metrics: hit_rate=%.3f  token_f1=%.3f  judge_acc=%.3f  judge_score=%.2f",
        c_m.get("retrieval_hit_rate", 0),
        c_m.get("mean_token_f1", 0),
        c_m.get("judge_accuracy", 0),
        c_m.get("mean_judge_score", 0),
    )

    # 5. Quality & Freshness checks on corrupted data
    log.info("[Step 5] Running Observability checks on corrupted data...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted_quality")
    corrupted_freshness_path = settings.paths.quality_dir / "corrupted_freshness.json"
    corrupted_freshness = build_freshness_report(corrupted_df, settings, corrupted_freshness_path)
    log.info(
        "  Corrupted Quality: %d/%d passed (%s) | Freshness: %s (stale=%.1f%%)",
        corrupted_quality["checks_passed"],
        corrupted_quality["checks_total"],
        "PASS" if corrupted_quality["all_passed"] else "FAIL",
        "FRESH" if corrupted_freshness["is_fresh"] else "STALE",
        corrupted_freshness.get("stale_ratio", 0) * 100,
    )

    # 6. Repair dataset from raw lineage snapshot
    log.info("[Step 6] Self-Healing: Repairing dataset from raw lineage snapshot...")
    raw_records = fetch_source_records(settings)
    repaired_df = build_clean_dataframe(raw_records)
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    log.info("  Repaired dataset restored: %s (%d rows)", settings.paths.repaired_clean_csv, len(repaired_df))

    # 7. Build repaired Chroma index
    log.info("[Step 7] Building repaired RAG index (collection: %s)...", settings.repaired_collection_name)
    repaired_idx = LocalEmbeddingIndex.build(
        df=repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    log.info("  Repaired index built: %d documents", len(repaired_idx.documents))

    # 8. Evaluate repaired index
    log.info("[Step 8] Evaluating repaired RAG pipeline on test set...")
    repaired_eval = evaluate_pipeline(
        settings=settings,
        index=repaired_idx,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    r_m = repaired_eval.summary
    log.info(
        "  Repaired Metrics: hit_rate=%.3f  token_f1=%.3f  judge_acc=%.3f  judge_score=%.2f",
        r_m.get("retrieval_hit_rate", 0),
        r_m.get("mean_token_f1", 0),
        r_m.get("judge_accuracy", 0),
        r_m.get("mean_judge_score", 0),
    )

    # 9. Quality & Freshness checks on repaired data
    log.info("[Step 9] Running Observability checks on repaired data...")
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired_quality")
    repaired_freshness_path = settings.paths.quality_dir / "repaired_freshness.json"
    repaired_freshness = build_freshness_report(repaired_df, settings, repaired_freshness_path)
    log.info(
        "  Repaired Quality: %d/%d passed (%s) | Freshness: %s (stale=%.1f%%)",
        repaired_quality["checks_passed"],
        repaired_quality["checks_total"],
        "ALL PASS" if repaired_quality["all_passed"] else "SOME FAILED",
        "FRESH" if repaired_freshness["is_fresh"] else "STALE",
        repaired_freshness.get("stale_ratio", 0) * 100,
    )

    # 10. Generate comparison report
    log.info("[Step 10] Generating comparison & corruption impact report...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=c_m,
        repaired_metrics=r_m,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    log.info("  Comparison report saved to: %s", settings.paths.comparison_report)

    log.info("=== Phase 2 Corruption & Recovery Flow COMPLETE ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error("Corruption flow failed: %s", exc)
        raise SystemExit(1)
