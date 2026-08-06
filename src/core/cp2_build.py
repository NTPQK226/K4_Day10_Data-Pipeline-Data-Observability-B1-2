"""CP2: Build test set + RAG index (Lead: Phong).

Chay: python src/core/cp2_build.py
"""
from __future__ import annotations

import pandas as pd

from src.evaluation.testset import build_test_set
from src.retrieval.index import LocalEmbeddingIndex
from src.core.config import load_settings


def main() -> None:
    settings = load_settings()

    # 1. Build test set
    print("=== Building test set ===")
    df = pd.read_csv("data/clean/papers_clean.csv")
    samples = build_test_set(df, settings.paths.eval_testset)
    print(f"Test set: {len(samples)} questions saved to {settings.paths.eval_testset}")
    for s in samples:
        q = s["question"]
        print(f"  {s['id']} [{s['question_type']}] {q}")

    # 2. Build RAG index
    print("\n=== Building RAG index ===")
    idx = LocalEmbeddingIndex.build(
        df=df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"RAG index: collection={idx.collection_name}, documents={len(idx.documents)}")
    print(f"Manifest saved to {settings.paths.embeddings_json}")

    # 3. Smoke test: semantic search + lookup
    print("\n=== Smoke test ===")
    test_queries = [
        "retrieval augmented generation for large language model agents",
        "hierarchical retrieval tool selection",
    ]
    for q in test_queries:
        results = idx.search(q, top_k=2)
        print(f"Query: {q}")
        for r in results:
            print(f"  -> [{r.paper_id}] score={r.score:.3f} title={r.title[:60]}")

    lookup_result = idx.lookup(df.iloc[0]["paper_id"])
    if lookup_result:
        print(f"\nLookup by paper_id OK: {lookup_result['title'][:60]}")
    else:
        print("\nLookup FAILED - paper_id not found")


if __name__ == "__main__":
    main()
