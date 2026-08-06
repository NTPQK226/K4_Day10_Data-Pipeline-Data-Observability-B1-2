# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4              |
| Tên nhóm         | B1-2     |
| Repository         | `https://github.com/NTPQK226/K4_Day10_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành | 2026-08-06               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Tuấn Phong | 01038 | Role 1 — Pipeline Orchestration | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `src/core/config.py`, `src/core/handoff.py`, `src/core/dod.py` |
| 2 | Nguyễn Hữu Công | 01732 | Role 2 — Data Layer Owner | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/ingestion/corruption.py`, lineage & repair |
| 3 | Nguyễn Tuấn Dương | 01966 | Role 3 — RAG & Agent Owner | `src/retrieval/index.py` (LocalEmbeddingIndex), `src/retrieval/agent.py`, 3 ChromaDB collections |
| 4 | Tạ Quốc Tuấn | 01114 | Role 4 — Evaluation & Observability | `src/evaluation/metrics.py`, `src/observability/quality.py`, `src/observability/reporting.py`, `src/observability/correlation.py`, `src/observability/recovery.py`, `src/evaluation/testset.py` |

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**

Nhóm đã hoàn thành toàn bộ pipeline từ CP0 đến CP6. Baseline pipeline tạo ra 24 bài báo khoa học sạch từ Crossref API (chủ đề RAG & Agentic LLM), xây dựng 3 ChromaDB collections độc lập và đánh giá bằng 24 câu hỏi thuộc 4 loại (summary/authors/date/categories). Artifact baseline đạt: `retrieval_hit_rate = 1.000`, `mean_token_f1 = 0.750`, `judge_accuracy = 0.750`, `mean_judge_score = 4.0`, quality 6/6 PASS, freshness FRESH (0% stale).

Corruption gây tác động mạnh nhất là `drop_latest_record` (xóa 3 bài mới nhất khỏi index) kết hợp `blank_summary` (2 bài rỗng abstract), làm `retrieval_hit_rate` giảm 50% (1.000 → 0.500) và `mean_token_f1` giảm 45.2 pp. Ba quality gate FAIL: `paper_id_unique`, `summary_not_blank`, `freshness_age_days`. Freshness chuyển sang STALE 52.2% do `stale_published_date` injection trên 12 records.

Repair từ raw lineage snapshot (`crossref_records.json`) phục hồi hoàn toàn: tất cả 4 metrics về đúng baseline, 6/6 quality gates PASS, freshness FRESH. Per-answer: 12/24 questions recovered, 12/24 consistent_hit, 0 consistent_miss, 0 newly_broken — recovery COMPLETE.

Blocker lớn nhất đã xử lý: editable install của venv trỏ vào workspace sibling gây `ModuleNotFoundError` cho module mới tạo; giải quyết bằng `sys.path.insert` tại entry point. Không còn blocker tồn đọng.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API (works.crossref.org)
    -> raw_response.json / crossref_records.json  [Role 2]
    -> cleaning, dedup, XML strip, age_days, text_for_embedding  [Role 2]
    -> papers_clean.csv / papers_clean.json  [Role 2]
    -> LocalEmbeddingIndex (all-MiniLM-L6-v2) -> ChromaDB papers-baseline  [Role 3]
    -> data/quality/baseline_quality.json, freshness_report.json  [Role 4]
    -> evaluate_pipeline (24 câu hỏi) -> baseline_metrics.json, baseline_answers.json  [Role 4]
    -> phase1_report.md  [Role 1 orchestrate, Role 4 generate]
    ---
    -> corrupt_clean_dataframe (6 scenarios) -> papers_clean_corrupted.csv, corruption_log.json  [Role 2]
    -> ChromaDB papers-corrupted  [Role 3]
    -> corrupted_metrics.json, corrupted_quality.json, corrupted_freshness.json  [Role 4]
    -> correlate_corruption_signals -> cp5_analysis.json, cp5_report.md  [Role 4]
    ---
    -> repair từ crossref_records.json (raw lineage) -> papers_clean_repaired.csv  [Role 2]
    -> ChromaDB papers-repaired  [Role 3]
    -> repaired_metrics.json, repaired_quality.json, repaired_freshness.json  [Role 4]
    -> analyze_recovery -> cp6_analysis.json, cp6_report.md  [Role 4]
    -> corruption_report.md (comparison)  [Role 1 orchestrate, Role 4 generate]
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref API (URL, query, filter) | fetch + retry (3x exp backoff), parse PaperRecord, XML strip | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json` | Nguyễn Hữu Công |
| Cleaning          | `crossref_records.json` | dedup DOI, normalize whitespace, filter abstract <50 chars, tính `age_days`, tổng hợp `text_for_embedding` | `data/clean/papers_clean.csv`<br>`data/clean/papers_clean.json` | Nguyễn Hữu Công |
| Embedding/index   | `papers_clean*.csv` | encode MiniLM-L6-v2 (384-dim), upsert ChromaDB, ghi manifest JSON | `data/chroma/` (3 collections)<br>`data/embeddings/papers_embeddings.json` | Nguyễn Tuấn Dương |
| Evaluation        | ChromaDB index, `test_set.json` | answer_question, token_f1, LLM judge (score 1-5), fallback heuristic | `data/results/*_metrics.json`<br>`data/results/*_answers.json` | Tạ Quốc Tuấn |
| Observability     | `pd.DataFrame` (clean/corrupted/repaired) | 6 quality checks, freshness (age_days vs 180-day threshold) | `data/quality/*.json` (6 files) | Tạ Quốc Tuấn |
| Corruption/repair | `papers_clean.csv`, `crossref_records.json` | 6 corruption scenarios + audit log; repair = re-run cleaning từ raw snapshot | `data/clean/papers_clean_corrupted.csv`<br>`data/clean/papers_clean_repaired.csv`<br>`data/results/corruption_log.json` | Nguyễn Hữu Công |
| Orchestration     | Toàn bộ artifacts từ Role 2–4 | Điều phối thứ tự chạy, gọi generate_phase1_report / generate_corruption_report | `data/reports/phase1_report.md`<br>`data/reports/corruption_report.md` | Nguyễn Tuấn Phong |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | OpenRouter |
| `LLM_MODEL`                | Theo `.env` (không ghi vào report) |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval `top_k`           | Theo `Settings` (configurable) |
| Freshness threshold          | 180 ngày |
| Random seed, nếu có        | N/A |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

CP5 — correlation analysis:

```bash
.venv\Scripts\python.exe script\run_cp5_analysis.py
```

CP6 — 3-state recovery analysis:

```bash
.venv\Scripts\python.exe script\run_cp6_analysis.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 | `data/results/baseline_metrics.json` — hit_rate=1.000 |
| Corruption flow   | Thành công | 2026-08-06 | `data/results/corrupted_metrics.json` — hit_rate=0.500; `data/results/repaired_metrics.json` — hit_rate=1.000 |
| CP5 analysis      | Thành công | 2026-08-06 | `data/results/cp5_analysis.json`, `data/reports/cp5_report.md` |
| CP6 analysis      | Thành công | 2026-08-06 | `data/results/cp6_analysis.json`, `data/reports/cp6_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API (`api.crossref.org/works`) |
| Query/filter                | Chủ đề "Retrieval-Augmented Generation & Agentic LLM", filter năm 2026 |
| Thời điểm lấy dữ liệu | 2026-08-01 (theo freshness report) |
| Số record nhận được    | 24 bài báo |
| Cơ chế retry/backoff      | Exponential backoff, tối đa 3 lần; retry khi HTTP 429/500/502/503/504 |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` (DOI) | string | Có | Khóa định danh duy nhất; dùng làm `ground_truth_doc_ids` trong evaluation | Loại record nếu thiếu |
| `title` | string | Có | Tiêu đề bài báo; đưa vào `text_for_embedding` | Loại record nếu rỗng |
| `authors_joined` | string | Không | Danh sách tác giả nối bằng dấu phẩy | Để trống nếu thiếu |
| `summary` | string | Có | Abstract sau khi strip XML/JATS; đưa vào `text_for_embedding` | Loại nếu < 50 ký tự |
| `published_date` | date (YYYY-MM-DD) | Không | Ngày xuất bản; dùng tính `age_days` | Dùng run_date nếu thiếu |
| `categories_joined` | string | Không | Chủ đề/category nối bằng dấu phẩy | Chuỗi rỗng nếu thiếu |
| `age_days` | int | Tính toán | Số ngày từ `published_date` đến `run_date`; dùng cho freshness check | Tính từ published_date |
| `summary_chars` | int | Tính toán | Độ dài abstract sau cleaning | Dùng cho quality gate `summary_not_blank` |
| `text_for_embedding` | string | Tính toán | Ghép: `"Title: ...\nAuthors: ...\nCategories: ...\nSummary: ..."` | Rebuilt sau mọi thay đổi |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Strip XML/JATS tags từ abstract (`<jats:p>`, ...) | Validity | 24 (tất cả records từ Crossref có tags) | `papers_clean.csv` không còn ký tự `<>` |
| Dedup theo `paper_id` (DOI chuẩn hoá) | Uniqueness | 0 duplicate trong baseline | `paper_id_unique` quality check PASS |
| Loại record thiếu `paper_id` hoặc `title` rỗng | Completeness | 0 record bị loại trong baseline | `paper_id_not_null`, `title_not_null` PASS |
| Loại record có `summary_chars < 50` | Validity | 0 record bị loại trong baseline | `summary_not_blank` PASS |
| Normalize whitespace (gom khoảng trắng thừa) | Consistency | 24 (áp dụng toàn bộ) | Text trong CSV không có double space |

`text_for_embedding` = `f"Title: {title}\nAuthors: {authors_joined}\nCategories: {categories_joined}\nSummary: {summary}"` — tổng hợp từ bốn trường ngữ nghĩa để MiniLM encode đủ context. `paper_id` = DOI gốc từ Crossref (stable key, không tự sinh UUID). `age_days = (run_date.date() - published_date).days` — làm nền cho freshness gate (ngưỡng 180 ngày).

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 24 |
| Các `question_type`                    | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID                 | DOI của từng bài báo (`paper_id`); mỗi câu hỏi có `ground_truth_doc_ids = [paper_id]` |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Vector store/collection                  | ChromaDB PersistentClient; 3 collections: `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k`                       | Theo `Settings` (configurable) |
| LLM provider/model                       | OpenRouter (model theo `.env`) |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` — frozen, không rebuild giữa các trạng thái |

Test set được giữ **cố định** vì đây là điều kiện bắt buộc để so sánh ba trạng thái có ý nghĩa nhân quả. Nếu test set thay đổi, không thể biết metric thay đổi là do chất lượng index hay do câu hỏi khó hơn/dễ hơn — hai nguồn biến động sẽ lẫn vào nhau và phép so sánh mất tính khách quan.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/crossref_response.json` (239 KB)<br>`data/raw/crossref_records.json` (59 KB) | Có | 24 PaperRecord |
| Cleaned dataset          | `data/clean/papers_clean.csv` (99 KB)<br>`data/clean/papers_clean.json` | Có | 24 rows, 0 duplicate |
| Embedding manifest/index | `data/chroma/` (ChromaDB)<br>`data/embeddings/papers_embeddings.json` | Có | Collection `papers-baseline` |
| Evaluation set           | `data/eval/test_set.json` | Có | 24 câu hỏi, 4 types |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | hit_rate=1.000 |
| Baseline answers         | `data/results/baseline_answers.json` | Có | 24 per-question entries |
| Quality/freshness        | `data/quality/baseline_quality.json`<br>`data/quality/freshness_report.json` | Có | 6/6 PASS, FRESH 0% |
| Baseline report          | `data/reports/phase1_report.md` | Có | Metrics + quality + freshness |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |         1.000 | Pipeline retrieve đúng document cho 24/24 câu hỏi |
| `mean_token_f1`      |         0.750 | Câu trả lời overlap từ khá tốt với ground truth |
| `judge_accuracy`     |         0.750 | LLM judge xác nhận 18/24 câu trả lời là đúng |
| `mean_judge_score`   |         4.000 | Điểm đánh giá trung bình 4/5 (semantic correctness) |
| Ragas, nếu có        | N/A | Không chạy RAGAS; dùng token_f1 và LLM judge thay thế |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `row_count` | Completeness | ≥ 1 row | PASS — 24 rows | `data/quality/baseline_quality.json` |
| `paper_id_not_null` | Completeness | 0 null paper_id | PASS — 0 null | `data/quality/baseline_quality.json` |
| `paper_id_unique` | Uniqueness | 0 duplicate paper_id | PASS — 0 duplicate | `data/quality/baseline_quality.json` |
| `title_not_null` | Completeness | 0 null/empty title | PASS — 0 null | `data/quality/baseline_quality.json` |
| `summary_not_blank` | Validity | summary_chars ≥ 50 | PASS — tất cả ≥ 50 chars | `data/quality/baseline_quality.json` |
| `freshness_age_days` | Timeliness | stale_ratio < ngưỡng (180 ngày) | PASS — 0% stale | `data/quality/freshness_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Clean DataFrame (papers_clean.csv) tại mỗi trạng thái |
| Timestamp mới nhất       | 2026-08-01 |
| Ngưỡng freshness         | 180 ngày |
| Trạng thái baseline      | Fresh |
| Lý do                     | 24/24 records có `age_days` < 180; `stale_ratio = 0.0%` |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| `drop_latest_record` | Xóa 3 bài báo mới nhất khỏi DataFrame | 3 records | `row_count` giảm | `retrieval_hit_rate` giảm 50%; các câu hỏi liên quan miss hoàn toàn | Reload từ raw snapshot |
| `blank_summary` | Đặt abstract = "" trên 2 records | 2 records | `summary_not_blank` FAIL | RAG retrieve doc nhưng context vô nghĩa; `mean_token_f1` giảm | Reload từ raw snapshot |
| `inject_noise` | Chèn "CORRUPTED NOISE: Lorem ipsum..." vào abstract | N records | Không có gate (impact chỉ qua metric) | `mean_token_f1` và `judge_accuracy` giảm; agent phát hiện rác | Reload từ raw snapshot |
| `truncate_title` | Cắt ngắn title còn 8 ký tự | N records | Không có gate (impact chỉ qua metric) | `retrieval_hit_rate` giảm nhẹ; title lookup sai | Reload từ raw snapshot |
| `stale_published_date` | Đẩy ngày xuất bản về 2018 (age_days > 3000) | 12 records | `freshness_age_days` FAIL | Freshness STALE 52.2%; metric retrieval không thay đổi | Reload từ raw snapshot |
| `duplicate_row` | Nhân bản 2 dòng với cùng paper_id | 2 records | `paper_id_unique` FAIL | ChromaDB có duplicate entry; retrieval có thể ambiguous | Reload từ raw snapshot |

Corruption log:
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log đủ 6 loại corruption với từng record bị tác động, loại lỗi, tham số cụ thể và số lượng rows trước/sau.

Repair sử dụng chiến lược **Raw-first Lineage**: tải lại `data/raw/crossref_records.json` (snapshot raw gốc từ Crossref API, giữ nguyên từ CP0) rồi thực thi toàn bộ quy trình cleaning chuẩn (`build_clean_dataframe`) từ đầu. Cách này đảm bảo dữ liệu phục hồi từ nguồn đáng tin cậy, không phải vá thủ công — nếu có sai sót ẩn trong quá trình repair, cleaning pipeline sẽ phát hiện qua quality checks.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |    1.000 |     0.500 |    1.000 |                   −0.500 |          +0.500 | Giảm 50% do 3 docs bị xóa + 2 blank summary → FULL recovery |
| `mean_token_f1`        |    0.750 |     0.298 |    0.750 |                   −0.452 |          +0.452 | inject_noise + wrong retrieval → FULL recovery |
| `judge_accuracy`       |    0.750 |     0.292 |    0.750 |                   −0.458 |          +0.458 | LLM judge xác nhận sai nghĩa; FULL recovery |
| `mean_judge_score`     |    4.000 |     2.125 |    4.000 |                   −1.875 |          +1.875 | Score giảm từ 4/5 xuống 2.125/5; FULL recovery |
| Quality checks pass/fail |     6/6 |      3/6 |     6/6 | 3 gate FAIL | 3 gate recovered | COMPLETE — paper_id_unique, summary_not_blank, freshness_age_days |
| Freshness status         | FRESH 0% | STALE 52.2% | FRESH 0% | 12 records stale | +52.2% | COMPLETE — repaired_freshness is_fresh=True |

**Hai kết luận nhân quả được hỗ trợ bởi artifacts:**

1. `drop_latest_record` (3 papers) + `blank_summary` (2 papers) → `row_count` giảm 24→23, `summary_not_blank` FAIL (`data/quality/corrupted_quality.json`) → `retrieval_hit_rate` giảm từ 1.000 xuống 0.500 (`data/results/corrupted_metrics.json`): pipeline không tìm được đúng document vì docs bị xóa khỏi index hoặc embedding vô nghĩa. Bằng chứng trực tiếp: `q001_authors` corrupted trả lời "Lihui Liu" thay vì "Wei Tian, Yuhao Zhou" vì Hi-RAG paper bị drop.

2. Repair reload `crossref_records.json` → rebuild clean DataFrame (24 rows, summary đầy đủ, dates gốc 2026) → `repaired_quality.json` 6/6 PASS, `repaired_freshness.json` is_fresh=True → rebuild index `papers-repaired` → re-evaluate: 4/4 metrics trở về đúng baseline (`data/results/repaired_metrics.json`). Per-answer: `q001_authors` repaired trả lời "Wei Tian, Yuhao Zhou" (token_f1=1.0, judge_score=5) — bằng chứng trong `data/results/cp6_analysis.json` demo cases.

**Kết quả khác kỳ vọng:** `stale_published_date` (12 records) — kỳ vọng làm giảm `retrieval_hit_rate` nhưng thực tế không tác động vì date không ảnh hưởng embedding. Impact chỉ ở freshness gate. Đây là ví dụ cho "stable signal" — không kết luận stale_date làm giảm retrieval khi metric không thay đổi.

## 11. Vấn đề tích hợp quan trọng

**Vấn đề:** NaN float trong ChromaDB metadata gây crash khi build index từ cleaned dataframe.

- **Triệu chứng:** `expected string or bytes-like object, got 'float'` — ChromaDB từ chối upsert khi metadata chứa `float('nan')`.
- **Nguyên nhân:** Pandas đọc CSV và điền `float('nan')` cho các cell rỗng (ví dụ `categories_joined` thiếu). ChromaDB metadata yêu cầu string — không chấp nhận float.
- **Cách xử lý:** Sửa `_build_documents` trong `src/retrieval/index.py` dùng `pd.notna()` kiểm tra trước khi cast:
  ```python
  "categories_joined": str(row["categories_joined"]) if pd.notna(row["categories_joined"]) else "",
  ```
  Áp dụng cho tất cả trường metadata.
- **Cách xác minh:** Embedding manifest `papers_embeddings.json` có `"categories_joined": ""` (string) thay vì `"categories_joined": NaN` (float); collection build thành công 24 documents.

Vấn đề thứ hai: venv editable install trỏ đến workspace sibling (`F:\K4_Day10_Data-Pipeline-Data-Observability-B1-2\src`) khiến module mới tạo trong project Role 4 không được nhận diện. Giải quyết bằng `sys.path.insert(0, str(_this_src))` tại đầu mỗi script runner.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Test set 24 câu hỏi là nhỏ; `consistent_miss = 0` không chứng minh không có repair failure — có thể do test set dễ | Per-answer recovery stats không phân biệt "repair hoạt động tốt" với "test set toàn câu dễ" | Mở rộng test set lên 100+ câu, thêm câu hỏi multi-hop và negative examples |
| `stale_published_date` không làm giảm retrieval metric (date không ảnh hưởng embedding) — nhưng pipeline báo STALE | Freshness gate và metric không nhất quán: gate FAIL nhưng retrieval không suy giảm | Thêm date-aware retrieval: filter hoặc re-rank docs theo `age_days` để freshness có tác động thực tế |
| Hybrid search chưa được triển khai; chỉ dùng semantic search | Câu hỏi keyword chính xác (author name, DOI) có thể bị miss nếu embedding không capture đủ | Thêm BM25 + semantic search hybrid trong `LocalEmbeddingIndex.search()` |
| LLM judge có thể gặp quota limit và fallback sang heuristic (phát hiện 1 fallback trong corrupted_answers) | `judge_accuracy` và `mean_judge_score` có thể không phản ánh đúng nếu tỷ lệ fallback cao | Implement retry với rate limiting; log fallback rate như metric độc lập |
| Per-question-type recovery chưa được phân tách trong CP6 | Không biết loại câu hỏi nào khó recover hơn (hypothesis: `date` type bị ảnh hưởng bởi stale_date) | Thêm breakdown theo `question_type` trong `analyze_recovery()` |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set (`data/eval/test_set.json`).
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
