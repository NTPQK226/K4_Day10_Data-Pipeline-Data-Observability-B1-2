# Checkpoint 5 — Corruption Signal Correlation Report

> Liên kết từng loại corruption trong log với quality gate bị kích hoạt và metric thay đổi. Ghi rõ signal nào **không** đổi để tránh kết luận quá mức.

## 1. Quality & Freshness — Corrupted Dataset

**Result**: 3/6 quality checks passed — SOME FAILED

| Check | Value | Status |
|---|---|---|
| row_count | 23 | PASS |
| paper_id_not_null | 0 | PASS |
| paper_id_unique | 2 | FAIL |
| title_not_null | 0 | PASS |
| summary_not_blank | 2 | FAIL |
| freshness_age_days | 12 | FAIL |

### Freshness

- **Status**: Stale
- Latest published: `2026-07-10`
- Oldest published: `2018-01-01`
- Stale rows: 12 / 23 (threshold: 180 days)


## 2. Metric Comparison — Baseline vs Corrupted

| Metric | Baseline | Corrupted | Delta | Status |
|---|---|---|---|---|
| retrieval_hit_rate | 1.000 | 0.500 | -0.5000 | DEGRADED |
| mean_token_f1 | 0.750 | 0.298 | -0.4524 | DEGRADED |
| judge_accuracy | 0.750 | 0.292 | -0.4583 | DEGRADED |
| mean_judge_score | 4 | 2.125 | -1.8750 | DEGRADED |

## 3. Evaluator Fallback Detection

**WARNING**: 1 answer(s) used the heuristic fallback judge (LLM evaluator unavailable). These scores are based on token overlap, not semantic correctness — they may appear as 'pass' even when the answer is wrong.

| ID | Token F1 | Judge Score | Correct | Reasoning excerpt |
|---|---|---|---|---|
| q006_summary | 0.691 | 3 | True | Fallback heuristic judge used because the LLM evaluator was unavailable.… |

## 4. Worst Degraded Case (Evidence)

**Question ID**: `q001_authors`  
**Type**: `authors`

> Who authored 'Hi‐ RAG : A Hierarchical Retrieval‐Augmented Generation Framework for Scalable and Generalisable Tool Selection in Large Language Model Agents'?

| Metric | Baseline | Corrupted | Delta |
|---|---|---|---|
| token_f1 | 1.000 | 0.000 | -1.0000 |
| judge_score | 5 | 1 | — |
| retrieval_hit | True | False | — |

**Baseline answer excerpt**:
> Wei Tian, Yuhao Zhou

**Corrupted answer excerpt**:
> Lihui Liu


## 5. Corruption Log ↔ Quality Signal ↔ Metric Linkage

| Corruption type | Count | Quality gate | Gate status | Expected metric impact |
|---|---|---|---|---|
| `blank_summary` | 2 | summary_not_blank | FAIL | retrieval_hit_rate, mean_token_f1 |
| `drop_latest_record` | 3 | row_count | PASS | retrieval_hit_rate |
| `duplicate_row` | 2 | paper_id_unique | FAIL | retrieval_hit_rate |
| `inject_noise` | 3 | _(none — semantic impact only)_ | — | mean_token_f1, judge_accuracy, mean_judge_score |
| `stale_published_date` | 12 | freshness_age_days | FAIL | _(freshness only)_ |
| `truncate_title` | 2 | _(none — semantic impact only)_ | — | retrieval_hit_rate |

### Detail per Corruption Type

#### `blank_summary` (2 records)

- **Quality gate**: `summary_not_blank`
- **Gate detail**: 2 rows with summary shorter than 50 chars
- **Affected paper IDs**: `10.21203/rs.3.rs-10178277/v1`, `10.2196/preprints.106157`

#### `drop_latest_record` (3 records)

- **Quality gate**: `row_count`
- **Gate detail**: 23 rows in dataset
- **Affected paper IDs**: `10.1111/exsy.70341`, `10.2118/234689-pa`, `10.1007/s10278-026-02086-9`

#### `duplicate_row` (2 records)

- **Quality gate**: `paper_id_unique`
- **Gate detail**: 2 duplicate paper_id rows
- **Affected paper IDs**: `10.35314/3y9hy151`, `10.20944/preprints202602.0996.v1`

#### `inject_noise` (3 records)

- **Quality gate**: `None`
- **Gate detail**: No structural quality gate — impact visible in evaluation metrics only.
- **Affected paper IDs**: `10.3390/buildings16132637`, `10.21079/11681/50309`, `10.63646/kpqm1958`

#### `stale_published_date` (12 records)

- **Quality gate**: `freshness_age_days`
- **Gate detail**: 12 rows (52.2%) older than 180 days
- **Affected paper IDs**: `10.21203/rs.3.rs-9882260/v1`, `10.52060/juptik.v4i1.4318`, `10.54254/2753-8818/2026.dl34055`, `10.22214/ijraset.2026.82233`, `10.21203/rs.3.rs-9770645/v1`, `10.1093/sleep/zsag091.0346`, `10.32473/flairs.39.1.141782`, `10.55041/isjem07213`, `10.20944/preprints202604.0339.v1`, `10.70121/001c.158711`, `10.36227/techrxiv.177272838.89432844/v1`, `10.3390/app16052244`

#### `truncate_title` (2 records)

- **Quality gate**: `None`
- **Gate detail**: No structural quality gate — impact visible in evaluation metrics only.
- **Affected paper IDs**: `10.21203/rs.3.rs-10012178/v1`, `10.47576/2949-1894.2026.7.7.023`

## 6. Stable Signals (No Meaningful Change)

All measured metrics changed significantly. No stable signals identified.

## 7. Root Cause Map

| Corruption | Quality gate triggered | Metric degraded | Freshness degraded |
|---|---|---|---|
| `blank_summary` | `summary_not_blank` FAIL | `retrieval_hit_rate`, `mean_token_f1` ↓ | No |
| `inject_noise` | _(none)_ | `mean_token_f1`, `judge_score` ↓ | No |
| `drop_latest_record` | `row_count` ↓ | `retrieval_hit_rate` ↓ | Yes (fewer recent records) |
| `stale_published_date` | `freshness_age_days` FAIL | _(none directly)_ | Yes |
| `truncate_title` | _(none)_ | `retrieval_hit_rate` ↓ (exact lookup fails) | No |
| `duplicate_row` | `paper_id_unique` FAIL | `retrieval_hit_rate` ↓ (index diluted) | No |


## 8. Conclusion

- Structural corruptions (`blank_summary`, `duplicate_row`) are caught **immediately** by quality gates.
- Semantic corruptions (`inject_noise`, `truncate_title`) pass quality gates but show up in evaluation metrics.
- Freshness corruption (`stale_published_date`, `drop_latest_record`) is detected by the freshness gate.
- Stable signals (if any) show that not every metric is sensitive to every corruption type — over-attributing a stable metric to a specific corruption is a false conclusion.
- The evaluator fallback check ensures silent heuristic-as-success is surfaced, not hidden.

---
_Generated by data pipeline observability module — Checkpoint 5._
