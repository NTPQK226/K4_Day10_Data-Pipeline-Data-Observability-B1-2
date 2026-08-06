from __future__ import annotations

from datetime import UTC, datetime
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json

logger = logging.getLogger(__name__)


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Mô phỏng 6 kịch bản Data Corruption có kiểm soát và ghi log chi tiết.

    Kịch bản:
    1. Drop latest records: Xóa một số bản ghi mới nhất để kiểm tra Freshness drop & Missing docs.
    2. Blank summary: Xóa abstract về chuỗi rỗng ở một số bản ghi để kiểm tra Quality check `summary_not_blank`.
    3. Inject noise: Chèn văn bản rác vào abstract để làm giảm chất lượng Semantic Retrieval & Token F1.
    4. Truncate title: Cắt ngắn tiêu đề (còn 5-10 ký tự) để làm hỏng Exact Lookup.
    5. Stale published date: Làm cũ ngày xuất bản về năm 2018-2020 (tăng `age_days` > 1800) để kiểm tra Freshness Gate.
    6. Add duplicate rows: Chèn bản ghi trùng lặp `paper_id` để kiểm tra Quality check `paper_id_unique`.
    7. Tự động tính toán lại `summary_chars` và `text_for_embedding` cho toàn bộ các bản ghi bị biến đổi.
    8. Ghi nhật ký lỗi có cấu trúc chi tiết vào `output_log_path`.
    """
    if df.empty:
        logger.warning("Empty dataframe provided to corrupt_clean_dataframe.")
        return df.copy()

    corrupted_df = df.copy()
    initial_row_count = len(corrupted_df)
    corruptions: list[dict[str, Any]] = []

    # 1. Drop latest records (ví dụ 3 bài báo mới nhất)
    drop_count = min(3, max(1, initial_row_count // 8))
    dropped_rows = corrupted_df.iloc[:drop_count]
    dropped_ids = dropped_rows["paper_id"].tolist()
    corrupted_df = corrupted_df.iloc[drop_count:].copy().reset_index(drop=True)

    for idx, row in dropped_rows.iterrows():
        corruptions.append(
            {
                "type": "drop_latest_record",
                "paper_id": row["paper_id"],
                "original_title": row["title"],
                "original_published": row["published"],
                "detail": "Deleted latest record to trigger freshness drop and missing document retrieval failure.",
            }
        )

    # Đảm bảo còn đủ dòng để thực hiện các kịch bản tiếp theo
    n_rows = len(corrupted_df)

    # 2. Blank summary (làm rỗng summary ở 2 bản ghi đầu tiên còn lại)
    blank_targets = min(2, n_rows)
    for i in range(blank_targets):
        pid = corrupted_df.at[i, "paper_id"]
        old_summary = corrupted_df.at[i, "summary"]
        corrupted_df.at[i, "summary"] = ""
        corrupted_df.at[i, "summary_chars"] = 0
        corruptions.append(
            {
                "type": "blank_summary",
                "paper_id": pid,
                "row_index": i,
                "original_summary_len": len(old_summary),
                "new_summary_len": 0,
                "detail": "Set abstract to empty string to test summary_not_blank quality gate.",
            }
        )

    # 3. Inject noise into summary (ở 3 bản ghi tiếp theo)
    noise_start = blank_targets
    noise_end = min(noise_start + 3, n_rows)
    noise_text = " [CORRUPTED NOISE: Lorem ipsum dolor sit amet, synthetic adversarial random text injected to degrade semantic relevance and hallucinate retrieval.]"
    for i in range(noise_start, noise_end):
        pid = corrupted_df.at[i, "paper_id"]
        old_summary = corrupted_df.at[i, "summary"]
        corrupted_summary = noise_text + " " + old_summary[: len(old_summary) // 2]
        corrupted_df.at[i, "summary"] = corrupted_summary
        corrupted_df.at[i, "summary_chars"] = len(corrupted_summary)
        corruptions.append(
            {
                "type": "inject_noise",
                "paper_id": pid,
                "row_index": i,
                "injected_noise": noise_text,
                "detail": "Injected synthetic noise and truncated abstract to degrade token F1 and LLM judge score.",
            }
        )

    # 4. Truncate title (ở 2 bản ghi tiếp theo)
    trunc_start = noise_end
    trunc_end = min(trunc_start + 2, n_rows)
    for i in range(trunc_start, trunc_end):
        pid = corrupted_df.at[i, "paper_id"]
        old_title = corrupted_df.at[i, "title"]
        truncated_title = old_title[:8] + "..." if len(old_title) > 8 else "Trunc..."
        corrupted_df.at[i, "title"] = truncated_title
        corruptions.append(
            {
                "type": "truncate_title",
                "paper_id": pid,
                "row_index": i,
                "original_title": old_title,
                "new_title": truncated_title,
                "detail": "Severely truncated title to break exact title lookup.",
            }
        )

    # 5. Stale published date (làm cũ ngày xuất bản về năm 2018 cho đa số bản ghi để kích hoạt Freshness Warning)
    stale_start = trunc_end
    stale_targets = min(n_rows - stale_start, max(4, int(n_rows * 0.6)))
    stale_end = stale_start + stale_targets
    for i in range(stale_start, stale_end):
        pid = corrupted_df.at[i, "paper_id"]
        old_pub = corrupted_df.at[i, "published"]
        stale_date = "2018-01-01"
        stale_age_days = (datetime.now(UTC).date() - datetime.strptime(stale_date, "%Y-%m-%d").date()).days
        corrupted_df.at[i, "published"] = stale_date
        corrupted_df.at[i, "age_days"] = stale_age_days
        corruptions.append(
            {
                "type": "stale_published_date",
                "paper_id": pid,
                "row_index": i,
                "original_published": old_pub,
                "new_published": stale_date,
                "new_age_days": stale_age_days,
                "detail": f"Modified publication date to 2018 (age={stale_age_days} days) to trigger freshness failure.",
            }
        )

    # 6. Add duplicate rows (nhân bản 2 bản ghi)
    dup_sources = corrupted_df.iloc[-2:].copy() if len(corrupted_df) >= 2 else corrupted_df.iloc[:1].copy()
    corrupted_df = pd.concat([corrupted_df, dup_sources], ignore_index=True)
    for _, dup_row in dup_sources.iterrows():
        corruptions.append(
            {
                "type": "duplicate_row",
                "paper_id": dup_row["paper_id"],
                "title": dup_row["title"],
                "detail": "Appended duplicate record to violate uniqueness constraint (paper_id_unique).",
            }
        )

    # 7. Rebuild `text_for_embedding` cho toàn bộ dataframe
    rebuilt_texts: list[str] = []
    for _, row in corrupted_df.iterrows():
        title = str(row.get("title", ""))
        authors = str(row.get("authors_joined", ""))
        cats = str(row.get("categories_joined", ""))
        summary = str(row.get("summary", ""))

        parts: list[str] = [f"Title: {title}"]
        if authors:
            parts.append(f"Authors: {authors}")
        if cats:
            parts.append(f"Categories: {cats}")
        parts.append(f"Summary: {summary}")
        rebuilt_texts.append("\n".join(parts).strip())

    corrupted_df["text_for_embedding"] = rebuilt_texts

    # 8. Ghi log kiểm toán có cấu trúc ra file
    log_data: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "initial_rows": initial_row_count,
        "corrupted_rows": len(corrupted_df),
        "total_corruptions_applied": len(corruptions),
        "dropped_paper_ids": dropped_ids,
        "corruptions": corruptions,
    }

    log_path = Path(output_log_path)
    write_json(log_path, log_data)
    logger.info(
        "Corrupted dataframe generated: %d -> %d rows (%d corruption events logged to %s)",
        initial_row_count,
        len(corrupted_df),
        len(corruptions),
        log_path,
    )

    return corrupted_df

