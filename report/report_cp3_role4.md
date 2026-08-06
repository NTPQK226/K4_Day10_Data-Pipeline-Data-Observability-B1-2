# CP3 Report — Role 4: Evaluation & Observability

**Ngày thực hiện:** 2026-08-06  
**Phạm vi:** evaluator · baseline_metrics · hit/miss · metric interpretation · phase1 report · cross-check · baseline snapshot  
**LLM Judge:** OpenRouter / `~deepseek/deepseek-v4-flash-latest` (18/18 samples LLM-judged, 0 fallback)

---

## Task 1 — Chạy evaluator → baseline_metrics.json + baseline_answers.json

Gọi `evaluate_pipeline()` với:
- `index`: `LocalEmbeddingIndex.load()` — collection `papers-baseline`, 24 docs
- `test_set_path`: `data/eval/test_set.json` — 18 samples
- Output: `data/results/baseline_metrics.json` + `data/results/baseline_answers.json`

### Kết quả baseline_metrics.json

| Metric | Giá trị |
|---|---|
| `samples` | 18 |
| `retrieval_hit_rate` | **1.000** |
| `mean_token_f1` | **1.000** |
| `judge_accuracy` | **1.000** |
| `mean_judge_score` | **5.0 / 5** |
| `ragas` | skipped (RUN_RAGAS not set) |

---

## Task 2 — Đọc hit/miss; kiểm tra ground truth/doc ID hợp lệ

### HIT mẫu 1 — `q001_summary` (type: summary)

```
Question        : What is 'Hi‐ RAG : A Hierarchical Retrieval‐Augmented Generation
                  Framework for Scalable and Generalisable Tool Selection in Large
                  Language Model Agents' about?
Ground truth    : ABSTRACT As tool repositories for Large Language Model (LLM) agents
                  grow from dozens to hundreds of endpoints...
Answer          : ABSTRACT As tool repositories for Large Language Model (LLM) agents
                  grow from dozens to hundreds of endpoints...    ← khớp chính xác
ground_truth_doc_ids : ['10.1111/exsy.70341']
retrieved_doc_ids    : ['10.1111/exsy.70341', '10.36227/techrxiv...']  ← ID khớp ở vị trí 1
retrieval_hit   : True
token_f1        : 1.000
judge_score     : 5 | correct: True
judge_reasoning : "The model answer exactly matches the reference answer..."
```

### HIT mẫu 2 — `q001_authors` (type: authors)

```
Question        : Who authored 'Hi‐ RAG : ...'?
Ground truth    : Wei Tian, Yuhao Zhou
Answer          : Wei Tian, Yuhao Zhou                           ← khớp chính xác
ground_truth_doc_ids : ['10.1111/exsy.70341']
retrieved_doc_ids    : ['10.1111/exsy.70341', ...]
retrieval_hit   : True  | token_f1: 1.000 | judge_score: 5
```

### MISS samples: **0**

Không có miss nào trong 18 samples.

### Tại sao 100% hit rate?

Pipeline dùng **exact title lookup** trước khi semantic search:

```python
# qa.py — answer_question()
title_match = re.search(r"'([^']+)'", question)  # extract title từ câu hỏi
exact = index.lookup(title_match.group(1))        # lookup chính xác theo title
```

Câu hỏi trong test set đều chứa title trong ngoặc đơn → `index.lookup()` tìm được paper chính xác → `ground_truth_doc_ids` luôn nằm trong `retrieved_doc_ids`.

---

## Task 3 — Giải thích các metric hiện có

### retrieval_hit_rate = 1.000

**Cách tính:** `mean(retrieval_hit)` — `retrieval_hit = True` khi ít nhất 1 `retrieved_doc_id` nằm trong `ground_truth_doc_ids`.

**Ý nghĩa baseline:** Pipeline retrieve đúng paper cho 100% câu hỏi. Đây là điều kiện cần để agent có thể trả lời đúng — nếu retrieval miss, câu trả lời sai không phụ thuộc LLM mà do corpus.

**Sẽ giảm khi nào:** Corruption drop records → paper trong test set bị xóa khỏi index → `retrieval_hit = False`.

---

### mean_token_f1 = 1.000

**Cách tính:** Bag-of-words F1 giữa `ground_truth` và `answer`:

```
precision = |pred_tokens ∩ ref_tokens| / |pred_tokens|
recall    = |pred_tokens ∩ ref_tokens| / |ref_tokens|
f1        = 2 × precision × recall / (precision + recall)
```

**Ý nghĩa baseline:** Answer khớp từng token với ground truth. Do ground truth được lấy trực tiếp từ metadata (`authors_joined`, `published`, `first_sentence(summary)`), và answer cũng đọc từ cùng metadata đó → f1 = 1.0.

**Sẽ giảm khi nào:** Corruption blank summary / noise injection → `first_sentence(summary)` trả về chuỗi rác → token overlap giảm.

---

### judge_accuracy = 1.000 | mean_judge_score = 5.0

**Cách tính judge:**  
LLM (`deepseek-v4-flash`) nhận prompt so sánh `ground_truth` vs `answer`, trả về `JudgeVerdict(score: 1–5, correct: bool, reasoning: str)`.

- `judge_accuracy = mean(correct)` — tỷ lệ answer được đánh giá đúng
- `mean_judge_score = mean(score)` — điểm trung bình 1–5

**Kết quả:** 18/18 samples LLM-judged (0 fallback heuristic). Judge xác nhận tất cả answer đều khớp chính xác với reference.

**Sẽ giảm khi nào:** Noise injection → answer trả về text nhiễu → judge score thấp dù retrieval hit.

---

### Per-type breakdown

| Type | n | hit_rate | mean_tf1 |
|---|---|---|---|
| `summary` | 6 | 1.000 | 1.000 |
| `authors` | 6 | 1.000 | 1.000 |
| `date` | 6 | 1.000 | 1.000 |

---

## Task 4 — Chạy quality, freshness và generate_phase1_report

### Data quality (`data/quality/baseline_quality.json`)

| Check | Giá trị | Status |
|---|---|---|
| `row_count` | 24 | **PASS** |
| `paper_id_not_null` | 0 | **PASS** |
| `paper_id_unique` | 0 | **PASS** |
| `title_not_null` | 0 | **PASS** |
| `summary_not_blank` | 0 | **PASS** |
| `freshness_age_days` | 0 stale (0.0%) | **PASS** |

**Tổng:** 6/6 PASS — `all_passed = True`

### Freshness (`data/quality/freshness_report.json`)

| Signal | Giá trị |
|---|---|
| `latest_published` | `2026-08-01` |
| `oldest_published` | `2026-02-12` |
| `stale_rows` | 0 / 24 |
| `stale_ratio` | 0.0 |
| `is_fresh` | **True** |

### phase1_report.md

`data/reports/phase1_report.md` đã được cập nhật với số liệu thật (không còn TBD_CP3).  
Metrics, quality checks và freshness đều là dữ liệu real — không hardcode.

---

## Task 5 — Đối chiếu report với JSON/CSV thật

| Giá trị | Trong report | Tính lại từ nguồn | Khớp |
|---|---|---|---|
| `samples` | 18 | `len(baseline_answers.json)` = 18 | ✅ |
| `retrieval_hit_rate` | 1.000 | recompute từ answers = 1.000 | ✅ |
| `mean_token_f1` | 1.000 | recompute từ answers = 1.000 | ✅ |
| `row_count` | 24 | `len(papers_clean.csv)` = 24 | ✅ |
| `latest_published` | `2026-08-01` | `max(df["published"])` = `2026-08-01` | ✅ |

**Kết luận:** Tất cả 5 giá trị khớp — baseline hoàn tất, report đáng tin cậy.

---

## Task 6 — Baseline tín hiệu/metrics làm mốc

### Metrics snapshot (2026-08-06)

```
BASELINE METRICS — papers-baseline — 2026-08-06
================================================
samples              : 18
retrieval_hit_rate   : 1.000   ← mốc so sánh sau corruption
mean_token_f1        : 1.000   ← mốc so sánh sau corruption
judge_accuracy       : 1.000   ← mốc so sánh sau corruption
mean_judge_score     : 5.000   ← mốc so sánh sau corruption
judge_engine         : LLM (deepseek-v4-flash, 0 fallback)
```

### Quality snapshot

```
BASELINE QUALITY — 2026-08-06
==============================
row_count          : 24    → sau corruption: dự kiến giảm (drop rows)
paper_id_unique    : 0     → sau corruption: dự kiến tăng (add duplicates)
summary_not_blank  : 0     → sau corruption: dự kiến tăng (blank summary)
freshness_age_days : 0     → sau corruption: dự kiến tăng (stale dates)
is_fresh           : True  → sau corruption: dự kiến False
```

### Dự báo impact corruption → metric

| Loại corruption | Signal FAIL | Metric giảm |
|---|---|---|
| Drop latest records | `row_count` giảm | `retrieval_hit_rate` ↓ |
| Blank summary | `summary_not_blank` FAIL | `mean_token_f1` ↓, `judge_accuracy` ↓ |
| Noise injection | không fail check nhưng text xấu | `mean_token_f1` ↓, `judge_score` ↓ |
| Stale dates | `freshness_age_days` FAIL, `is_fresh=False` | freshness gate alert |
| Duplicate rows | `paper_id_unique` FAIL | precision giảm, embedding nhiễu |

---

## Tổng kết CP3

| Task | Kết quả | Artifact |
|---|---|---|
| 1. Chạy evaluator | Done | `data/results/baseline_metrics.json` · `baseline_answers.json` |
| 2. Đọc hit/miss + verify doc ID | Done — 18 hit, 0 miss, 100% doc ID hợp lệ | — |
| 3. Giải thích metrics | Done — retrieval/f1/judge đều 1.000, LLM-judged | — |
| 4. Quality + freshness + report | Done — 6/6 PASS, is_fresh=True | `data/reports/phase1_report.md` |
| 5. Cross-check report vs CSV/JSON | Done — 5/5 giá trị khớp | — |
| 6. Baseline snapshot | Done — mốc so sánh sau corruption ghi rõ | — |

### Danh sách artifact sau CP3

```
data/results/baseline_metrics.json     217 bytes  — 4 metrics thật
data/results/baseline_answers.json  168,390 bytes  — 18 answers chi tiết
data/quality/baseline_quality.json    1,012 bytes  — 6/6 PASS
data/quality/freshness_report.json      200 bytes  — is_fresh=True
data/reports/phase1_report.md         1,157 bytes  — report hoàn chỉnh
data/eval/test_set.json               7,657 bytes  — 18 samples cố định
data/embeddings/papers_embeddings.json            — manifest 24 docs
data/chroma/                                      — ChromaDB papers-baseline
```

**Baseline hoàn tất. Pipeline sẵn sàng cho corruption flow.**
