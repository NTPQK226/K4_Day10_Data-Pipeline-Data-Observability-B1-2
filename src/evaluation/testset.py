from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json

# Minimum papers required before building a test set
_MIN_DOCS = 5

# Number of representative papers to sample questions from
_SAMPLE_SIZE = 6


def _pick_papers(df: pd.DataFrame) -> pd.DataFrame:
    """Return a subset of papers suitable for question generation."""
    # Prefer papers with non-blank summary, known authors, known date
    mask = (
        df["summary"].fillna("").str.len().ge(50)
        & df["authors_joined"].fillna("").str.len().gt(0)
        & df["published"].fillna("").str.len().gt(0)
    )
    candidates = df[mask]
    if candidates.empty:
        candidates = df
    n = min(_SAMPLE_SIZE, len(candidates))
    return candidates.head(n)


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if len(df) < _MIN_DOCS:
        raise ValueError(
            f"Dataset has only {len(df)} documents; need at least {_MIN_DOCS} to build a test set."
        )

    papers = _pick_papers(df)
    samples: list[dict[str, Any]] = []

    for i, (_, row) in enumerate(papers.iterrows()):
        paper_id: str = str(row["paper_id"])
        title: str = str(row["title"])
        doc_ids: list[str] = [paper_id]
        base_id = f"q{i + 1:03d}"

        # --- summary ---
        # _extract_answer default branch: first_sentence(metadata["summary"])
        summary_gt = first_sentence(str(row.get("summary", "")))
        if summary_gt:
            samples.append({
                "id": f"{base_id}_summary",
                "question_type": "summary",
                "question": f"What is '{title}' about?",
                "ground_truth": summary_gt,
                "ground_truth_doc_ids": doc_ids,
            })

        # --- authors ---
        # _extract_answer triggers on "who authored"
        authors_gt = str(row.get("authors_joined", "")).strip()
        if authors_gt:
            samples.append({
                "id": f"{base_id}_authors",
                "question_type": "authors",
                "question": f"Who authored '{title}'?",
                "ground_truth": authors_gt,
                "ground_truth_doc_ids": doc_ids,
            })

        # --- date ---
        # _extract_answer triggers on "when was"
        date_gt = str(row.get("published", "")).strip()
        if date_gt:
            samples.append({
                "id": f"{base_id}_date",
                "question_type": "date",
                "question": f"When was '{title}' published?",
                "ground_truth": date_gt,
                "ground_truth_doc_ids": doc_ids,
            })

        # --- categories ---
        # _extract_answer triggers on "what categories"
        categories_gt = str(row.get("categories_joined", "")).strip()
        if categories_gt:
            samples.append({
                "id": f"{base_id}_categories",
                "question_type": "categories",
                "question": f"What categories does '{title}' belong to?",
                "ground_truth": categories_gt,
                "ground_truth_doc_ids": doc_ids,
            })

    write_json(Path(output_path), samples)
    return samples
