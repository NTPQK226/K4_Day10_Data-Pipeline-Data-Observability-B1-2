# CP2 Report — Role 4: Evaluation & Observability

**Ngày thực hiện:** 2026-08-06  
**Phạm vi:** test set · embedding index audit · quality/freshness baseline · phase1 report skeleton  
**Nguồn dữ liệu:** `data/clean/papers_clean.json` → `data/embeddings/papers_embeddings.json`

---

## Task 1 — build_test_set hoàn thiện

File: [src/evaluation/testset.py](../src/evaluation/testset.py)

Hàm `build_test_set` đã implement đủ 5 trường bắt buộc cho mỗi sample:

| Trường | Nguồn | Ghi chú |
|---|---|---|
| `id` | `q{i:03d}_{question_type}` | Định danh duy nhất, ổn định qua lần chạy |
| `question_type` | `"summary"` / `"authors"` / `"date"` | `categories` bị bỏ — Crossref không trả categories |
| `question` | Template cố định + title từ df | Keyword khớp `_extract_answer` trong `qa.py` |
| `ground_truth` | Cột tương ứng trong cleaned df | Lấy trực tiếp, không viết tay |
| `ground_truth_doc_ids` | `[df["paper_id"]]` | DOI thật, không fabricate |

**Kết quả ghi file:** `data/eval/test_set.json` — 18 samples (6 summary + 6 authors + 6 date)

```
Test set size  : 18 samples
Papers sampled : 6 / 24
Types          : summary=6, authors=6, date=6
```

> **Lý do không có `categories`:** Toàn bộ 24 papers từ Crossref API có `categories_joined = ""`. `_pick_papers()` lọc loại paper không có categories, nên type này bị bỏ — đây là dữ liệu thật, không sửa.

---

## Task 2 — Xác minh tất cả paper_id trong test set tồn tại trong index

### Verification script output

```
Unique IDs trong test set : 6
Unique IDs trong index     : 24
Missing from index         : NONE — all present
```

### Chi tiết 6 paper_id được kiểm tra

| paper_id (DOI) | Có trong index? | Kiểm tra qua |
|---|---|---|
| `10.1111/exsy.70341` | ✓ | `manifest["documents"]` |
| `10.2118/234689-pa` | ✓ | `manifest["documents"]` |
| `10.1007/s10278-026-02086-9` | ✓ | `manifest["documents"]` |
| `10.21203/rs.3.rs-10178277/v1` | ✓ | `manifest["documents"]` |
| `10.2196/preprints.106157` | ✓ | `manifest["documents"]` |
| `10.3390/buildings16132637` | ✓ | `manifest["documents"]` |

**Kết luận:** `ground_truth_doc_ids` trong mọi sample đều resolve được trong ChromaDB — `retrieval_hit` có thể được tính đúng khi evaluation chạy.

---

## Task 3 — Test set cố định — đọc thử các row trước evaluation

Test set đã ghi vào `data/eval/test_set.json` (7,657 bytes). Đọc thử 3 row đầu:

### Row 1 — `q001_summary`
```
question_type : summary
question      : What is 'Hi‐ RAG : A Hierarchical Retrieval‐Augmented Generation
                Framework for Scalable and Generalisable Tool Selection in Large
                Language Model Agents' about?
ground_truth  : ABSTRACT As tool repositories for Large Language Model (LLM) agents
                grow from dozens to hundreds of endpoints, flat retrieval paradigms
                that treat the repository as an unstructured list suffer from context
                overload...
doc_ids       : ["10.1111/exsy.70341"]
```

### Row 2 — `q001_authors`
```
question_type : authors
question      : Who authored 'Hi‐ RAG : ...'?
ground_truth  : Wei Tian, Yuhao Zhou
doc_ids       : ["10.1111/exsy.70341"]
```

### Row 3 — `q001_date`
```
question_type : date
question      : When was 'Hi‐ RAG : ...' published?
ground_truth  : 2026-08-01
doc_ids       : ["10.1111/exsy.70341"]
```

**Xác nhận:** Keyword câu hỏi khớp đúng branch trong `_extract_answer`:
- `"What is ... about?"` → default branch → `first_sentence(summary)`
- `"Who authored"` → `metadata["authors_joined"]`
- `"When was"` → `metadata["published"]`

---

## Task 4 — Audit embedding manifest và ChromaDB

### Manifest (`data/embeddings/papers_embeddings.json`)

| Trường | Giá trị |
|---|---|
| `backend` | `chroma` |
| `embedding_model` | `sentence-transformers/all-MiniLM-L6-v2` |
| `persist_path` | `data/chroma/` |
| `collection_name` | `papers-baseline` |
| `documents` (count) | **24** |

### ChromaDB live audit

```
Collection name         : papers-baseline
Live document count     : 24  (khớp manifest)
record_id format        : {paper_id}::{index}   (ví dụ: 10.1111/exsy.70341::0)
```

### Metadata keys trong mỗi document

```
paper_id · title · published · authors_joined · categories_joined
summary · abs_url · pdf_url
```

Đây là các trường mà `_extract_answer` đọc khi trả lời câu hỏi — đủ để resolve cả 4 question types.

### Sample search để xác nhận retrieval hoạt động

Query: `"agentic retrieval augmented generation"`

```
[0.593] 10.63646/kpqm1958            | The Age of Autonomous Agents: A Bibliometric Review...
[0.582] 10.32473/flairs.39.1.141782  | An Exploratory Study of Agentic Retrieval Augmented...
[0.555] 10.36227/techrxiv.177272...  | A Survey of (Deep RAG) Deep Retrieval Augmented...
```

**Kết luận audit:** ChromaDB hoạt động, 24 documents indexed, cosine similarity hoạt động đúng, top-k retrieval trả về kết quả ngữ nghĩa phù hợp.

---

## Task 5 — Baseline quality/freshness signals (để đối chiếu sau corruption)

### Quality signals — `data/quality/baseline_quality.json`

| Signal | Giá trị baseline | Ngưỡng | Status |
|---|---|---|---|
| `row_count` | 24 | ≥ 5 | PASS |
| `paper_id_not_null` | 0 null | = 0 | PASS |
| `paper_id_unique` | 0 duplicate | = 0 | PASS |
| `title_not_null` | 0 null | = 0 | PASS |
| `summary_not_blank` | 0 rows < 50 chars | = 0 | PASS |
| `freshness_age_days` | 0 rows stale (0.0%) | ≤ 50% | PASS |

**Tổng:** 6/6 PASS — `all_passed = True`

### Freshness signals — `data/quality/freshness_report.json`

| Signal | Giá trị baseline | Ghi chú |
|---|---|---|
| `latest_published` | `2026-08-01` | Paper mới nhất trong corpus |
| `oldest_published` | `2026-02-12` | Paper cũ nhất — vẫn trong 180 ngày |
| `stale_rows` | 0 | Không có paper nào vượt ngưỡng |
| `total_rows` | 24 | |
| `stale_ratio` | 0.0 (0%) | |
| `freshness_threshold_days` | 180 | Từ `settings.freshness_threshold_days` |
| `is_fresh` | `True` | |

### Nguồn timestamp

| Trường | Nguồn | Cách tính |
|---|---|---|
| `published` | Crossref `published.date-parts` | Parse tại ingestion |
| `age_days` | Cleaning pipeline | `(run_date - published).days` — cố định trong df |
| `stale_rows` | `age_days > 180` | Không dùng `datetime.now()` tại report time |

> `age_days` đã được tính và lưu vào cleaned CSV/JSON — freshness report **chỉ đọc lại từ cột này**, không tính lại runtime. Điều này đảm bảo kết quả reproducible.

### Snapshot tín hiệu sẽ dùng để đối chiếu sau corruption

```
BASELINE SNAPSHOT (2026-08-06)
================================
row_count          : 24   → sau corruption: dự kiến giảm (drop rows)
summary_not_blank  : 0    → sau corruption: dự kiến tăng (blank summary)
paper_id_unique    : 0    → sau corruption: dự kiến tăng (add duplicates)
freshness_age_days : 0    → sau corruption: dự kiến tăng (stale dates)
is_fresh           : True → sau corruption: dự kiến False
stale_rows         : 0    → sau corruption: dự kiến > 0
```

---

## Task 6 — Skeleton phase1 report cho CP3

File: `data/reports/phase1_report.md`

Skeleton đã được tạo bằng `generate_phase1_report()` với:
- Section 1 (Data Source): thông tin thật từ settings + ingestion
- Section 2 (Metrics): placeholder `TBD_CP3` — sẽ điền số thật sau khi evaluation chạy
- Section 3 (Quality): kết quả thật từ `baseline_quality.json`
- Section 4 (Freshness): kết quả thật từ `freshness_report.json`

### Nội dung skeleton (trích)

```markdown
# Phase 1 — Baseline Report

## 1. Data Source
- api: Crossref REST API
- query: agentic retrieval augmented generation large language model
- records_fetched: 24 / records_after_cleaning: 24
- embedding_model: sentence-transformers/all-MiniLM-L6-v2
- collection_name: papers-baseline / indexed_documents: 24

## 2. Evaluation Metrics
| Metric             | Value    |
| samples            | 18       |
| retrieval_hit_rate | TBD_CP3  |   ← điền sau khi evaluate_pipeline() chạy
| mean_token_f1      | TBD_CP3  |
| judge_accuracy     | TBD_CP3  |
| mean_judge_score   | TBD_CP3  |

## 3. Data Quality → 6/6 PASS (thật)
## 4. Freshness   → is_fresh=True, stale=0/24 (thật)
```

**Tại CP3:** chỉ cần gọi lại `generate_phase1_report()` với `metrics` thật từ `baseline_metrics.json` — mọi section khác đã có đủ dữ liệu.

---

## Tổng kết CP2

| Task | Kết quả | Artifact |
|---|---|---|
| 1. build_test_set hoàn thiện | Done — 18 samples, 5 trường đủ | `data/eval/test_set.json` |
| 2. Xác minh ID tồn tại trong index | Done — 6/6 present, NONE missing | verified vs manifest |
| 3. Test set cố định, đọc thử row | Done — 3 rows verified, keyword khớp qa.py | `data/eval/test_set.json` |
| 4. Audit embedding manifest | Done — 24 docs, cosine search hoạt động | `data/embeddings/papers_embeddings.json` |
| 5. Baseline quality/freshness signals | Done — 6/6 PASS, is_fresh=True, snapshot ghi | `data/quality/*.json` |
| 6. Skeleton phase1 report | Done — Section 1/3/4 thật, Section 2 TBD | `data/reports/phase1_report.md` |

### Danh sách artifact đã có sau CP2

```
data/eval/test_set.json                    7,657 bytes — 18 samples
data/embeddings/papers_embeddings.json     manifest + 24 documents
data/chroma/                               ChromaDB, collection papers-baseline, 24 docs
data/quality/baseline_quality.json         1,012 bytes — 6/6 PASS
data/quality/freshness_report.json           200 bytes — is_fresh=True
data/reports/phase1_report.md             skeleton, metrics TBD_CP3
```

### Việc cần làm ở CP3

- Chạy `evaluate_pipeline()` với LLM provider → sinh `baseline_metrics.json` + `baseline_answers.json`
- Gọi lại `generate_phase1_report()` với metrics thật → hoàn thiện `phase1_report.md`
- Test set **không thay đổi** — dùng file hiện tại làm input cố định
