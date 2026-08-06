from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord

logger = logging.getLogger(__name__)


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime | None = None) -> pd.DataFrame:
    """Clean raw records thành dataframe chuẩn cho embedding, QA retrieval và evaluation.

    Quy trình:
    1. Chuẩn hoá text: title, summary, authors, categories.
    2. Bóc tách và parse ngày xuất bản (`published`), tính toán `age_days`.
    3. Tạo các trường helper:
       - `authors_joined`
       - `categories_joined`
       - `summary_chars`
       - `text_for_embedding`
    4. Deduplicate theo stable `paper_id`.
    5. Lọc bỏ các record không hợp lệ (thiếu id, title rỗng, summary quá ngắn < 50 chars) và ghi log truy vết.
    6. Sắp xếp theo ngày xuất bản mới nhất và trả về DataFrame.
    """
    effective_run_date = run_date or datetime.now(UTC)
    run_date_val = effective_run_date.date() if isinstance(effective_run_date, datetime) else effective_run_date

    raw_count = len(records)
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    dropped_reasons: dict[str, int] = {
        "missing_paper_id": 0,
        "duplicate_paper_id": 0,
        "empty_title": 0,
        "short_or_empty_summary": 0,
    }

    for record in records:
        # 1. Paper ID
        paper_id = (record.paper_id or "").strip()
        if not paper_id:
            dropped_reasons["missing_paper_id"] += 1
            logger.warning("Dropped record due to missing paper_id: %s", record)
            continue

        if paper_id in seen_ids:
            dropped_reasons["duplicate_paper_id"] += 1
            logger.warning("Dropped duplicate record for paper_id: %s", paper_id)
            continue

        # 2. Title
        title = normalize_whitespace(record.title or "")
        if not title:
            dropped_reasons["empty_title"] += 1
            logger.warning("Dropped record due to empty title for paper_id: %s", paper_id)
            continue

        # 3. Summary (Abstract)
        summary = normalize_whitespace(record.summary or "")
        summary_chars = len(summary)
        if summary_chars < 50:
            dropped_reasons["short_or_empty_summary"] += 1
            logger.warning(
                "Dropped record due to short summary (%d chars < 50) for paper_id: %s",
                summary_chars,
                paper_id,
            )
            continue

        # 4. Authors & Categories
        cleaned_authors = [normalize_whitespace(a) for a in (record.authors or []) if normalize_whitespace(a)]
        authors_joined = compact_join(cleaned_authors, ", ")

        cleaned_categories = [normalize_whitespace(c) for c in (record.categories or []) if normalize_whitespace(c)]
        categories_joined = compact_join(cleaned_categories, ", ")
        primary_cat = record.primary_category or (cleaned_categories[0] if cleaned_categories else "")

        # 5. Published date & age_days
        pub_str = (record.published or "").strip()
        age_days = 0
        if pub_str:
            try:
                pub_dt = datetime.strptime(pub_str[:10], "%Y-%m-%d").date()
                age_days = max(0, (run_date_val - pub_dt).days)
            except Exception:
                age_days = 0
        else:
            pub_str = run_date_val.isoformat()
            age_days = 0

        # 6. Text for Embedding
        text_parts: list[str] = [f"Title: {title}"]
        if authors_joined:
            text_parts.append(f"Authors: {authors_joined}")
        if categories_joined:
            text_parts.append(f"Categories: {categories_joined}")
        text_parts.append(f"Summary: {summary}")
        text_for_embedding = "\n".join(text_parts).strip()

        seen_ids.add(paper_id)
        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "summary_chars": summary_chars,
                "authors": cleaned_authors,
                "authors_joined": authors_joined,
                "categories": cleaned_categories,
                "categories_joined": categories_joined,
                "primary_category": primary_cat,
                "published": pub_str,
                "updated": (record.updated or pub_str).strip(),
                "age_days": int(age_days),
                "text_for_embedding": text_for_embedding,
                "abs_url": (record.abs_url or "").strip(),
                "pdf_url": (record.pdf_url or "").strip(),
                "comment": (record.comment or "").strip(),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        # Sort by published date descending, then paper_id
        df.sort_values(by=["published", "paper_id"], ascending=[False, True], inplace=True)
        df.reset_index(drop=True, inplace=True)

    clean_count = len(df)
    total_dropped = raw_count - clean_count
    logger.info(
        "Cleaning complete: raw=%d -> clean=%d (dropped=%d: %s)",
        raw_count,
        clean_count,
        total_dropped,
        dropped_reasons,
    )

    return df

