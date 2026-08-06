# CP3 (01:35–02:00) — Baseline End-to-End & Report

**Ngày:** 2026-08-06
**Lead:** Phong

## Trạng thái hoàn thành

| Artifact | Trạng thái |
|---|---|
| `data/raw/crossref_response.json` | ✅ |
| `data/raw/crossref_records.json` | ✅ |
| `data/clean/papers_clean.csv` | ✅ |
| `data/clean/papers_clean.json` | ✅ |
| `data/embeddings/papers_embeddings.json` | ✅ |
| `data/eval/test_set.json` | ✅ |
| `data/results/baseline_metrics.json` | ✅ |
| `data/results/baseline_answers.json` | ✅ |
| `data/quality/baseline_quality.json` | ✅ |
| `data/quality/freshness_report.json` | ✅ |
| `data/reports/phase1_report.md` | ✅ |

## Baseline Metrics

```
samples:            24
retrieval_hit_rate: 1.000  (24/24 hit — perfect)
mean_token_f1:      0.750
judge_accuracy:    0.750
mean_judge_score:   4.00
```

## Giải thích metrics bằng artifact

**Retrieval hit rate = 1.000 (perfect):**
- Lookup chính xác theo `paper_id` → extracted answer đúng ground truth
- Semantic search top-k đủ để retrieval hit luôn đúng doc

**Token F1 = 0.750 (tốt):**
- Answer extracted từ metadata (summary/authors/date/categories) khớp tốt với ground truth
- Không phải generation tự do → F1 không bằng 1.0 vì format có thể khác (tên đầy đủ vs abbreviated)

**Judge accuracy = 0.750:**
- 75% câu trả lời được LLM judge đánh giá "correct"
- 25% câu có thể thiếu precision (trả lời quá ngắn hoặc format khác ground truth)

## Quality & Freshness

- **Quality**: 6/6 checks PASS — ALL PASS ✅
- **Freshness**: FRESH ✅ — latest=2026-08-01, stale=0/24 (0%)

## Pass Criteria

- ✅ `baseline_metrics.json` tồn tại
- ✅ `baseline_answers.json` tồn tại
- ✅ Quality + Freshness tồn tại
- ✅ `phase1_report.md` tồn tại
- ✅ Team giải thích được hit/miss bằng artifact

## CP3 PASS — Tiếp theo: NGHỈ 15 phút (CP4)
