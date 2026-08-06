r"""Phase 1: Baseline pipeline end-to-end.

Run: uv run python script/run_phase1.py
"""
from __future__ import annotations

import logging
import sys

import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _load_or_build_clean(settings) -> pd.DataFrame:
    """Load clean CSV nếu tồn tại, nếu không thì build từ raw."""
    csv_path = settings.paths.clean_csv
    if csv_path.exists():
        log.info("Loading existing clean CSV: %s", csv_path)
        return pd.read_csv(csv_path)

    log.info("Clean CSV not found, building from raw records...")
    records = fetch_source_records(settings)
    df = build_clean_dataframe(records)

    # Save clean artifacts
    write_csv(df, csv_path)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))
    log.info("Clean data saved: %s", csv_path)
    return df


def _load_or_build_index(settings, df: pd.DataFrame) -> LocalEmbeddingIndex:
    """Load existing index nếu tồn tại, nếu không thì build mới."""
    manifest_path = settings.paths.embeddings_json
    if manifest_path.exists():
        log.info("Loading existing embedding manifest: %s", manifest_path)
        return LocalEmbeddingIndex.load(settings, manifest_path)

    log.info("Building new embedding index...")
    idx = LocalEmbeddingIndex.build(
        df=df,
        settings=settings,
        embeddings_output_path=manifest_path,
    )
    log.info("Index built: collection=%s, documents=%d", idx.collection_name, len(idx.documents))
    return idx


def _load_or_build_test_set(settings, df: pd.DataFrame):
    """Load existing test set nếu refresh_test_set=False."""
    path = settings.paths.eval_testset
    if not settings.refresh_test_set and path.exists():
        log.info("Loading existing test set: %s", path)
        return
    log.info("Building new test set from %d rows...", len(df))
    build_test_set(df, path)


def main() -> None:
    log.info("=== Phase 1: Baseline Pipeline ===")
    settings = load_settings()

    # 1. Raw records (fetch hoặc load snapshot)
    log.info("[Step 1] Fetching/loading raw records...")
    records = fetch_source_records(settings)
    log.info("  Raw records: %d", len(records))

    # 2. Clean data
    log.info("[Step 2] Building clean dataset...")
    df = _load_or_build_clean(settings)
    log.info("  Clean rows: %d", len(df))

    # 3. Embedding index
    log.info("[Step 3] Building RAG index...")
    idx = _load_or_build_index(settings, df)
    log.info("  Collection: %s", idx.collection_name)

    # 4. Test set
    log.info("[Step 4] Building test set...")
    _load_or_build_test_set(settings, df)

    # 5. Evaluate
    log.info("[Step 5] Evaluating on test set...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=idx,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    m = bundle.summary
    log.info(
        "  Metrics: hit_rate=%.3f  token_f1=%.3f  judge_acc=%.3f  judge_score=%.2f",
        m.get("retrieval_hit_rate", 0),
        m.get("mean_token_f1", 0),
        m.get("judge_accuracy", 0),
        m.get("mean_judge_score", 0),
    )

    # 6. Quality checks
    log.info("[Step 6] Running data quality checks...")
    quality = run_data_quality_checks(df, settings, "baseline_quality")
    log.info(
        "  Quality: %d/%d passed — %s",
        quality["checks_passed"],
        quality["checks_total"],
        "ALL PASS" if quality["all_passed"] else "SOME FAILED",
    )

    # 7. Freshness report
    log.info("[Step 7] Building freshness report...")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    log.info(
        "  Freshness: %s (latest=%s, stale=%.1f%%)",
        "FRESH" if freshness["is_fresh"] else "STALE",
        freshness.get("latest_published"),
        freshness.get("stale_ratio", 0) * 100,
    )

    # 8. Phase1 markdown report
    log.info("[Step 8] Generating phase1_report.md...")
    source_summary = {
        "source": settings.source_api,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "max_results": settings.max_results,
        "embedding_model": settings.embedding_model,
        "llm_provider": f"{settings.llm_provider} / {settings.model_name}",
        "raw_records": len(records),
        "clean_records": len(df),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=m,
        quality=quality,
        freshness=freshness,
    )
    log.info("  Report: %s", settings.paths.baseline_report)

    log.info("=== Phase 1 COMPLETE ===")
    log.info("  artifacts:")
    for path in [
        settings.paths.raw_api_response,
        settings.paths.raw_records_json,
        settings.paths.clean_csv,
        settings.paths.clean_json,
        settings.paths.embeddings_json,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
        settings.paths.quality_dir / "baseline_quality.json",
        settings.paths.freshness_report,
        settings.paths.baseline_report,
    ]:
        log.info("    %s  %s", "OK" if path.exists() else "MISSING", path)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error("Phase 1 failed: %s", exc)
        raise SystemExit(1)

