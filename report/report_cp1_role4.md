# CP1 Report — Role 4: Evaluation & Observability

**Ngày thực hiện:** 2026-08-06  
**Phạm vi:** test set · metrics · quality · freshness · reports  
**Nguồn dữ liệu:** `data/clean/papers_clean.json` (cleaned dataframe, không dùng raw)

---

## Mục 1 — Chọn paper đại diện từ cleaned dataframe

Paper được chọn từ `papers_clean.json` qua hàm `_pick_papers` với điều kiện lọc:

- `summary_chars >= 50` (đảm bảo nội dung có thể embed và kiểm chứng)
- `authors_joined` không rỗng
- `published` không rỗng

Kết quả: **6 papers đại diện** được chọn từ tổng 24 papers trong cleaned dataframe.

| # | paper_id | Tiêu đề (rút gọn) | Published | age_days |
|---|---|---|---|---|
| 1 | `10.1111/exsy.70341` | Hi‑RAG: Hierarchical RAG for Tool Selection | 2026-08-01 | 5 |
| 2 | `10.2118/234689-pa` | SafeRAG: Multistage RAG for Oil & Gas Safety Reports | 2026-08-01 | 5 |
| 3 | `10.1007/s10278-026-02086-9` | JADE-Plus: Multimodal Agentic RAG for Jawbone Diagnosis | 2026-07-13 | 24 |
| 4 | `10.21203/rs.3.rs-10178277/v1` | RAG-Based Time-Series Forecasting for Equity Analysis | 2026-07-10 | 27 |
| 5 | `10.2196/preprints.106157` | RAG Impact on Medical Students' Perceptions of LLMs | 2026-07-03 | 34 |
| 6 | `10.3390/buildings16132637` | Agentic AI for Roof Design Compliance Using RAG | 2026-07-02 | 35 |

> **Lưu ý:** Toàn bộ 24 papers từ Crossref không có trường `categories` (Crossref API không trả về subject categories ở format này). Do đó test set chỉ có 3 loại câu hỏi: `summary`, `authors`, `date`.

---

## Mục 2 — Draft question / ground truth kiểm chứng được từ nội dung paper

Mỗi câu hỏi dùng đúng keyword mà `qa.py:_extract_answer` cần để chọn đúng trường metadata. **Ground truth lấy trực tiếp từ cột cleaned dataframe**, không viết tay.

### Paper 1 — Hi‑RAG (DOI: `10.1111/exsy.70341`)

| question_type | Câu hỏi | Ground truth |
|---|---|---|
| `summary` | What is 'Hi‐ RAG : A Hierarchical Retrieval‐Augmented Generation Framework for Scalable and Generalisable Tool Selection in Large Language Model Agents' about? | ABSTRACT As tool repositories for Large Language Model (LLM) agents grow from dozens to hundreds of endpoints, flat retrieval paradigms that treat the repository as an unstructured list suffer from context overload... |
| `authors` | Who authored 'Hi‐ RAG : ...'? | **Wei Tian, Yuhao Zhou** |
| `date` | When was 'Hi‐ RAG : ...' published? | **2026-08-01** |

### Paper 2 — SafeRAG (DOI: `10.2118/234689-pa`)

| question_type | Câu hỏi | Ground truth |
|---|---|---|
| `summary` | What is 'SafeRAG: ...' about? | Summary In high-risk industrial settings, leveraging large language models (LLMs) for automated accident analysis... |
| `authors` | Who authored 'SafeRAG: ...'? | **Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li** |
| `date` | When was 'SafeRAG: ...' published? | **2026-08-01** |

### Paper 3 — JADE-Plus (DOI: `10.1007/s10278-026-02086-9`)

| question_type | Ground truth |
|---|---|
| `summary` | Abstract Diagnosing jawbone lesions in oral and maxillofacial radiology remains challenging due to overlapping radiological features... |
| `authors` | **Soroush Baseri Saadi, Jonas Ver Berne, Rocharles Cavalcante Fontenele, Peter Claes, Reinhilde Jacobs** |
| `date` | **2026-07-13** |

### Paper 4 — RAG Time-Series (DOI: `10.21203/rs.3.rs-10178277/v1`)

| question_type | Ground truth |
|---|---|
| `summary` | Abstract Time-series foundation models and retrieval-based augmentation have recently emerged as relevant tools for financial forecasting... |
| `authors` | **Novanto Yudistira, Yanuar Putra Kharisma Adhiyasa** |
| `date` | **2026-07-10** |

### Paper 5 — RAG & Medical Students (DOI: `10.2196/preprints.106157`)

| question_type | Ground truth |
|---|---|
| `summary` | BACKGROUND There is evidence of rapid adoption of large language models (LLMs) in undergraduate medical education... |
| `authors` | **Rohin Athavale, Alexander Cresswell, Alice Huffman** |
| `date` | **2026-07-03** |

### Paper 6 — Roof Compliance AI (DOI: `10.3390/buildings16132637`)

| question_type | Ground truth |
|---|---|
| `summary` | Designers, engineers, and building officials face increasing pressure to accelerate and improve the accuracy of design review... |
| `authors` | **Nawari O. Nawari, Oluwatoyin O. Lawal** |
| `date` | **2026-07-02** |

**Tổng test set:** 18 samples — 6 summary, 6 authors, 6 date.  
**File đầu ra:** `data/eval/test_set.json`

---

## Mục 3 — paper_id stable trước khi ghi test set

`paper_id` là **DOI từ Crossref API** — ổn định theo chuẩn quốc tế, không thay đổi giữa các lần chạy:

```
10.1111/exsy.70341
10.2118/234689-pa
10.1007/s10278-026-02086-9
10.21203/rs.3.rs-10178277/v1
10.2196/preprints.106157
10.3390/buildings16132637
```

Xác nhận từ `papers_clean.json`:
- **Unique IDs**: 24/24 (không trùng)
- **Null paper_id**: 0
- `ground_truth_doc_ids` trong mỗi sample ghi DOI thật, không fabricate

---

## Mục 4 — Quality checks đã hoàn thiện

File: `src/observability/quality.py` — `run_data_quality_checks()`

### Kết quả chạy thực tế trên baseline (`data/quality/baseline_quality.json`)

| Check | Giá trị | Kết quả | Chi tiết |
|---|---|---|---|
| `row_count` | 24 | **PASS** | 24 rows in dataset (ngưỡng ≥ 5) |
| `paper_id_not_null` | 0 | **PASS** | 0 rows with null paper_id |
| `paper_id_unique` | 0 | **PASS** | 0 duplicate paper_id rows |
| `title_not_null` | 0 | **PASS** | 0 rows with null title |
| `summary_not_blank` | 0 | **PASS** | 0 rows with summary shorter than 50 chars |
| `freshness_age_days` | 0 | **PASS** | 0 rows (0.0%) older than 180 days |

**Tổng kết:** 6/6 checks PASS — `all_passed = True`

> Đây là baseline sạch. Sau khi chạy corruption flow, các check `summary_not_blank`, `paper_id_unique` và `freshness_age_days` dự kiến sẽ **FAIL** — đó là bằng chứng corruption đã có tác động.

---

## Mục 5 — Freshness input từ published/age_days

File: `src/observability/quality.py` — `build_freshness_report()`

### Nguồn timestamp

| Trường | Nguồn | Cách tính |
|---|---|---|
| `published` | Crossref API field `published.date-parts` | ISO date string từ API response |
| `age_days` | Cleaning pipeline | `(run_date - published_date).days` tính tại thời điểm `build_clean_dataframe()` chạy |
| `stale_rows` | `age_days > freshness_threshold_days` | threshold = 180 ngày (từ `settings.freshness_threshold_days`) |
| `is_fresh` | Logic tổng hợp | True khi có dữ liệu gần đây VÀ `stale_ratio ≤ 50%` |

> `age_days` **không dùng ngày hiện tại giả định** — được tính cố định tại thời điểm pipeline chạy và lưu vào cleaned dataframe. Freshness report đọc lại từ cột `age_days` đã có sẵn, không tính lại runtime.

### Kết quả freshness baseline (`data/quality/freshness_report.json`)

```json
{
  "latest_published": "2026-08-01",
  "oldest_published": "2026-02-12",
  "stale_rows": 0,
  "total_rows": 24,
  "stale_ratio": 0.0,
  "freshness_threshold_days": 180,
  "is_fresh": true
}
```

**Nhận xét:**
- Tất cả 24 papers được publish trong 175 ngày gần nhất (2026-02-12 đến 2026-08-01)
- Không có paper nào vượt ngưỡng 180 ngày
- `is_fresh = True` — corpus đang ở trạng thái tươi mới

---

## Mục 6 — Quality report baseline (bằng chứng baseline)

### Artifact đã tạo

| File | Nội dung |
|---|---|
| `data/quality/baseline_quality.json` | 6 checks, 6 PASS, all_passed=True |
| `data/quality/freshness_report.json` | latest=2026-08-01, stale=0, is_fresh=True |
| `data/eval/test_set.json` | 18 samples từ 6 papers, ground_truth_doc_ids là DOI thật |

### Ý nghĩa baseline

Report này là **điểm gốc** (baseline) để so sánh sau khi corruption:

```
Baseline state:
  - row_count          : 24  ✓
  - null paper_id      : 0   ✓
  - duplicate paper_id : 0   ✓
  - null title         : 0   ✓
  - blank summary      : 0   ✓
  - stale_rows         : 0   ✓
  - is_fresh           : True ✓

Expected corrupted state (dự đoán):
  - blank summary      : N rows  ← FAIL
  - duplicate paper_id : M rows  ← FAIL
  - stale_rows         : K rows  ← FAIL
  - is_fresh           : False   ← FAIL
```

Khi corruption flow chạy, các check trên sẽ FAIL và metric RAG (`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`) sẽ giảm — **bằng chứng định lượng** rằng data quality ảnh hưởng trực tiếp đến RAG.

---

## Tóm tắt CP1

| Task | Trạng thái | Output |
|---|---|---|
| Chọn paper từ cleaned dataframe | Done | 6 papers, lọc qua `_pick_papers()` |
| Draft question/ground_truth kiểm chứng được | Done | 18 samples, ground_truth từ đúng cột df |
| paper_id stable (DOI thật) | Done | `ground_truth_doc_ids` là DOI Crossref |
| Quality checks hoàn thiện | Done | 6 checks, tất cả PASS baseline |
| Freshness từ published/age_days | Done | `is_fresh=True`, stale=0/24 |
| Quality report baseline | Done | `data/quality/baseline_quality.json` |

**Files đã tạo/cập nhật:**
- `src/evaluation/testset.py` — implement `build_test_set`
- `src/observability/quality.py` — implement `run_data_quality_checks` + `build_freshness_report`
- `src/observability/reporting.py` — implement `generate_phase1_report` + `generate_corruption_report`
- `data/eval/test_set.json` — 18 samples từ dữ liệu thật
- `data/quality/baseline_quality.json` — 6/6 PASS
- `data/quality/freshness_report.json` — is_fresh=True
