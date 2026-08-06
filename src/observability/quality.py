from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    # 1. Row count
    row_count = len(df)
    checks.append({
        "check": "row_count",
        "value": row_count,
        "passed": row_count >= 5,
        "detail": f"{row_count} rows in dataset",
    })

    # 2. paper_id not null
    null_ids = int(df["paper_id"].isnull().sum())
    checks.append({
        "check": "paper_id_not_null",
        "value": null_ids,
        "passed": null_ids == 0,
        "detail": f"{null_ids} rows with null paper_id",
    })

    # 3. paper_id unique
    dup_ids = int(df["paper_id"].duplicated().sum())
    checks.append({
        "check": "paper_id_unique",
        "value": dup_ids,
        "passed": dup_ids == 0,
        "detail": f"{dup_ids} duplicate paper_id rows",
    })

    # 4. title not null
    null_titles = int(df["title"].isnull().sum()) if "title" in df.columns else row_count
    checks.append({
        "check": "title_not_null",
        "value": null_titles,
        "passed": null_titles == 0,
        "detail": f"{null_titles} rows with null title",
    })

    # 5. summary length — blank/very short summary breaks embedding
    if "summary_chars" in df.columns:
        blank_summaries = int((df["summary_chars"] < 50).sum())
    elif "summary" in df.columns:
        blank_summaries = int((df["summary"].fillna("").str.len() < 50).sum())
    else:
        blank_summaries = row_count
    checks.append({
        "check": "summary_not_blank",
        "value": blank_summaries,
        "passed": blank_summaries == 0,
        "detail": f"{blank_summaries} rows with summary shorter than 50 chars",
    })

    # 6. Freshness via age_days
    if "age_days" in df.columns:
        stale = int((df["age_days"] > settings.freshness_threshold_days).sum())
        stale_pct = round(stale / row_count * 100, 1) if row_count else 0.0
        freshness_ok = stale_pct <= 50.0
    else:
        stale = 0
        stale_pct = 0.0
        freshness_ok = True
    checks.append({
        "check": "freshness_age_days",
        "value": stale,
        "passed": freshness_ok,
        "detail": f"{stale} rows ({stale_pct}%) older than {settings.freshness_threshold_days} days",
    })

    passed = sum(1 for c in checks if c["passed"])
    report: dict[str, Any] = {
        "report_name": report_name,
        "total_rows": row_count,
        "checks_total": len(checks),
        "checks_passed": passed,
        "checks_failed": len(checks) - passed,
        "all_passed": passed == len(checks),
        "checks": checks,
    }

    out_path = settings.paths.quality_dir / f"{report_name}.json"
    write_json(out_path, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    total_rows = len(df)

    if "published" in df.columns:
        dates = pd.to_datetime(df["published"], errors="coerce").dropna()
        latest_published = dates.max().date().isoformat() if not dates.empty else None
        oldest_published = dates.min().date().isoformat() if not dates.empty else None
    else:
        latest_published = None
        oldest_published = None

    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0

    # Fresh = at least one recent record AND majority not stale
    stale_ratio = stale_rows / total_rows if total_rows else 1.0
    is_fresh = (latest_published is not None) and (stale_ratio <= 0.5)

    report: dict[str, Any] = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": round(stale_ratio, 3),
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": is_fresh,
    }

    write_json(Path(report_path), report)
    return report
