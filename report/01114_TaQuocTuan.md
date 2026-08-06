# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung |
| ------------------ | --------- |
| **Họ và tên**   | Tạ Quốc Tuấn |
| **MSSV**           | 01114 |
| **Khóa/Lớp**     | K4 |
| **Tên nhóm**     | NTPQK226 / Nhóm Day 10 B1-2 |
| **Vai trò chính** | **Role 4 — Evaluation & Observability Owner** |
| **Repository**     | `https://github.com/NTPQK226/K4_Day10_Data-Pipeline-Data-Observability` |
| **Branch**         | `Role4_CP5` |
| **Ngày hoàn thành** | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module / Deliverable | File / Hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :---: |
| **Evaluation engine** | `src/evaluation/metrics.py`<br>— `evaluate_pipeline`<br>— `_judge_answer`, `_token_f1` | Index (ChromaDB), test set JSON | `baseline/corrupted/repaired_metrics.json`<br>`baseline/corrupted/repaired_answers.json` | **Hoàn thành (100%)** |
| **Data quality checks** | `src/observability/quality.py`<br>— `run_data_quality_checks`<br>— `build_freshness_report` | `pd.DataFrame` (clean/corrupted/repaired) | `data/quality/*.json` (6 reports) | **Hoàn thành (100%)** |
| **Report generation** | `src/observability/reporting.py`<br>— `generate_phase1_report`<br>— `generate_corruption_report`<br>— `generate_cp5_report`<br>— `generate_cp6_report` | Metrics, quality, freshness dicts | `data/reports/phase1_report.md`<br>`data/reports/corruption_report.md`<br>`data/reports/cp5_report.md`<br>`data/reports/cp6_report.md` | **Hoàn thành (100%)** |
| **CP5 — Corruption signal correlation** | `src/observability/correlation.py`<br>— `correlate_corruption_signals`<br>`script/run_cp5_analysis.py` | corruption_log.json, quality/freshness JSONs, metrics/answers | `data/results/cp5_analysis.json`<br>`data/reports/cp5_report.md` | **Hoàn thành (100%)** |
| **CP6 — 3-state recovery analysis** | `src/observability/recovery.py`<br>— `analyze_recovery`<br>`script/run_cp6_analysis.py` | baseline/corrupted/repaired metrics, quality, freshness, answers | `data/results/cp6_analysis.json`<br>`data/reports/cp6_report.md` | **Hoàn thành (100%)** |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên / module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| Định nghĩa 6 quality check gates (row_count, paper_id_not_null, paper_id_unique, title_not_null, summary_not_blank, freshness_age_days) | Role 1 (phase1.py, corruption_flow.py) — sử dụng kết quả để so sánh | Quality reports được dùng trực tiếp trong comparison report của Role 1 |
| Xác minh format `retrieval_hit`, `token_f1`, `judge` trong answers JSON | Role 1 — cần artifact để đưa vào `generate_corruption_report` | Contract ổn định, Role 1 chạy được pipeline end-to-end |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File / hàm / artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Thiết kế và ghi test set 24 câu hỏi (summary/authors/date/categories) từ cleaned dataframe | `data/eval/test_set.json`<br>`src/evaluation/metrics.py` | 24 QA entries với `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids` hợp lệ | `python -c "import json; d=json.load(open('data/eval/test_set.json')); print(len(d), d[0].keys())"` |
| Chạy evaluate baseline — tạo metrics và answers | `data/results/baseline_metrics.json`<br>`data/results/baseline_answers.json` | retrieval_hit_rate=1.0, mean_token_f1=0.75, judge_accuracy=0.75, mean_judge_score=4 | `cat data/results/baseline_metrics.json` |
| Chạy 6 quality checks và freshness baseline | `data/quality/baseline_quality.json`<br>`data/quality/freshness_report.json` | 6/6 PASS, is_fresh=true, stale_ratio=0.0 | `cat data/quality/baseline_quality.json` |
| Generate phase1 report | `data/reports/phase1_report.md` | Báo cáo Markdown gồm metrics, quality table, freshness block | Mở file và đối chiếu với JSON |
| CP5 — Nối corruption log với quality signal và metrics | `src/observability/correlation.py`<br>`script/run_cp5_analysis.py`<br>`data/reports/cp5_report.md` | 6 corruption types → quality gate map; 1 fallback judge detected; worst case q001_authors Δf1=−1.0 | `.venv\Scripts\python.exe script\run_cp5_analysis.py` |
| CP6 — 3-state recovery analysis với data thật | `src/observability/recovery.py`<br>`script/run_cp6_analysis.py`<br>`data/reports/cp6_report.md` | 4/4 metrics FULL recovery; 3/3 quality gates recovered; 12/24 questions recovered; 0 consistent_miss | `.venv\Scripts\python.exe script\run_cp6_analysis.py` |

**Output tiêu biểu — CP6 analysis log (số liệu thực tế):**

```
retrieval_hit_rate  baseline=1.000  corrupted=0.500  repaired=1.000  Δcorrupt=-0.500  Δrepair=+0.000  → FULL
mean_token_f1       baseline=0.750  corrupted=0.298  repaired=0.750  Δcorrupt=-0.452  Δrepair=+0.000  → FULL
judge_accuracy      baseline=0.750  corrupted=0.292  repaired=0.750  Δcorrupt=-0.458  Δrepair=+0.000  → FULL
mean_judge_score    baseline=4.000  corrupted=2.125  repaired=4.000  Δcorrupt=-1.875  Δrepair=+0.000  → FULL
Quality gates: 3 recovered · 0 still failing · 3 stable
Per-answer: recovered=12  consistent_hit=12  consistent_miss=0  newly_broken=0
```

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Role 4 phải trả lời ba câu hỏi:
1. **Baseline đang đứng ở đâu?** — cần evaluation engine tạo metrics đáng tin cậy.
2. **Data corruption làm hỏng gì và bằng chứng nào chứng minh?** — cần liên kết corruption log với quality gate và metric delta (CP5).
3. **Repair có phục hồi hoàn toàn không?** — cần so sánh 3 trạng thái trên cùng test set, cùng từng câu trả lời (CP6).

### Cách triển khai

#### `evaluate_pipeline` — Evaluation engine

Hàm nhận `index` (ChromaDB collection) và `test_set_path`, chạy từng câu qua `answer_question()` rồi tính:

- **Token F1** (`_token_f1`): overlap token giữa `ground_truth` và `answer` — đo similarity mà không cần LLM.
- **Judge** (`_judge_answer`): gọi LLM với structured output `JudgeVerdict(score 1–5, correct bool, reasoning str)`. Nếu LLM lỗi → fallback heuristic dựa trên token_f1, **ghi rõ vào `reasoning`** để có thể detect sau.
- **retrieval_hit**: `True` nếu ít nhất một `retrieved_doc_id` khớp với `ground_truth_doc_ids`.

Test set được giữ **cố định** và không rebuild để ba trạng thái (baseline/corrupted/repaired) đều đánh giá trên cùng bộ câu hỏi — điều kiện bắt buộc để phép so sánh có ý nghĩa.

#### `correlate_corruption_signals` — CP5

Module `correlation.py` dùng hai dict tĩnh:

```python
_CORRUPTION_TO_QUALITY_CHECK = {
    "blank_summary":        "summary_not_blank",
    "duplicate_row":        "paper_id_unique",
    "drop_latest_record":   "row_count",
    "stale_published_date": "freshness_age_days",
    "truncate_title":       None,   # không có gate cấu trúc
    "inject_noise":         None,   # impact chỉ thấy qua metric
}
```

Tại runtime: đọc `corruption_log.json` → group theo type → lookup trạng thái gate tương ứng trong `corrupted_quality.json` → tính `delta = corrupted_metric - baseline_metric`. Phát hiện fallback judge bằng cách scan `judge.reasoning` tìm chuỗi `"Fallback heuristic judge"`.

**Kết quả CP5 với data thật**: 4/4 metrics đều DEGRADED, 1 fallback judge (`q001_authors`), worst case token_f1 delta = −1.0.

#### `analyze_recovery` — CP6

Module `recovery.py` tính ba loại delta cho mỗi metric:
- `delta_corrupt = corrupted - baseline` (tác động của corruption)
- `delta_repair = repaired - baseline` (khoảng cách còn lại so baseline)
- `delta_recover = repaired - corrupted` (mức cải thiện của repair)

Phân loại recovery: **FULL** khi `|delta_repair| < 0.02`, **PARTIAL** khi có cải thiện nhưng chưa đủ, **NONE** khi không cải thiện.

Per-answer classification: dựa trên cặp `(corrupted_retrieval_hit, repaired_retrieval_hit)`:

| Cặp | Nhãn | Ý nghĩa |
| :--- | :--- | :--- |
| (False, True) | `recovered` | Corruption gây miss, repair sửa được |
| (True, True) | `consistent_hit` | Câu hỏi ổn định, không bị corrupt ảnh hưởng |
| (False, False) | `consistent_miss` | Repair không đủ để khôi phục |
| (True, False) | `newly_broken` | Repair làm hỏng thêm (cờ đỏ) |

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input của evaluate_pipeline** | `LocalEmbeddingIndex` (từ Role 3), `data/eval/test_set.json` (từ Role 4 tự tạo), `Settings` |
| **Output của evaluate_pipeline** | `*_metrics.json` (summary), `*_answers.json` (per-question detail) |
| **Input của correlate / analyze_recovery** | Tất cả JSON artifacts từ Role 1–4: corruption_log, quality, freshness, metrics, answers |
| **Output của correlate / analyze_recovery** | `cp5_analysis.json`, `cp6_analysis.json`, `cp5_report.md`, `cp6_report.md` |
| **Module phụ thuộc** | `retrieval.qa.answer_question` (Role 3), `retrieval.llm.build_llm` (Role 3) |
| **Module sử dụng output** | `pipelines.corruption_flow.generate_corruption_report` (Role 1) |
| **Điều kiện lỗi** | LLM quota → fallback judge được kích hoạt và ghi trong reasoning (không im lặng fail) |

### Cách xác minh

```bash
# CP5 — correlation analysis
.venv\Scripts\python.exe script\run_cp5_analysis.py

# CP6 — 3-state recovery analysis
.venv\Scripts\python.exe script\run_cp6_analysis.py
```

- **Kết quả mong đợi:** File JSON analysis và Markdown report được tạo, log in 3-state deltas và per-answer counts.
- **Kết quả thực tế:** Cả hai script chạy thành công, tạo đủ `cp5_analysis.json`, `cp6_analysis.json`, `cp5_report.md`, `cp6_report.md`.
- **Artifacts:** `data/results/cp5_analysis.json`, `data/results/cp6_analysis.json`, `data/reports/cp5_report.md`, `data/reports/cp6_report.md`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** CP5 và CP6 đều cần đọc nhiều artifact (corruption_log, quality, freshness, metrics, answers) và tổng hợp thành báo cáo. Ban đầu tôi định gộp tất cả logic vào `reporting.py`.

- **Các phương án đã cân nhắc:**
  1. Gộp hết vào `reporting.py` — một file nhưng khó test từng phần riêng biệt.
  2. Tách thành `correlation.py` (CP5 — phân tích tác động corruption) và `recovery.py` (CP6 — phân tích phục hồi), chỉ để render Markdown trong `reporting.py`.

- **Phương án đã chọn:** Phương án 2 — tách module theo trách nhiệm.

- **Lý do:** `correlation.py` trả về dict có cấu trúc (`type_analysis`, `metric_changes`, `stable_signals`, `worst_degraded_case`…) mà script, report renderer, hoặc downstream tool khác đều có thể consume mà không cần parse Markdown. `recovery.py` tương tự trả về `answer_classification` và `demo_cases`. Nếu gộp vào reporting, logic trộn lẫn với string formatting khiến khó debug và khó tái sử dụng.

- **Bằng chứng quyết định phù hợp:** Script CP5 được re-run sau khi metric files xuất hiện — không cần thay đổi code, chỉ chạy lại là tự lấy dữ liệu mới và in kết quả cập nhật với 1 fallback judge detected và worst case đúng.

---

## 6. Một lỗi / blocker đã xử lý

- **Triệu chứng:** Khi chạy `script\run_cp5_analysis.py`, nhận `ModuleNotFoundError: No module named 'observability.correlation'` mặc dù file `src/observability/correlation.py` đã tồn tại trong dự án.

- **Lệnh tái hiện:**
  ```bash
  .venv\Scripts\python.exe script\run_cp5_analysis.py
  ```

- **Nguyên nhân gốc:** Venv trong project này được cài editable install trỏ đến thư mục **sibling** `F:\K4_Day10_Data-Pipeline-Data-Observability-B1-2\src` (workspace chung của team), không phải `src/` của project hiện tại. Xác nhận bằng:
  ```python
  import observability; print(observability.__file__)
  # → F:\K4_Day10_Data-Pipeline-Data-Observability-B1-2\src\observability\__init__.py
  ```
  File `correlation.py` mới tạo nằm ở project Role 4, không được editable install đăng ký.

- **Cách xử lý:** Thêm dòng sau vào đầu mỗi script CP5/CP6, **trước** tất cả import nội bộ:
  ```python
  _this_src = Path(__file__).resolve().parents[1] / "src"
  if str(_this_src) not in sys.path:
      sys.path.insert(0, str(_this_src))
  ```
  Cách này ưu tiên `src/` của project Role 4 mà không phá vỡ editable install của workspace chung.

- **Cách xác minh sau khi sửa:**
  ```bash
  .venv\Scripts\python.exe script\run_cp5_analysis.py
  # → 2026-08-06 ... INFO === Checkpoint 5 COMPLETE ===
  ```

- **Điều học được:** Trong monorepo hoặc multi-workspace, editable install path không tự động bao gồm project con. Cần kiểm tra `sys.path` và `__file__` của package ngay khi gặp `ModuleNotFoundError` cho file mới tạo.

---

## 7. Hiểu biết về luồng end-to-end

**1. Dữ liệu đi từ Crossref đến vector index như thế nào?**

Crossref REST API → `fetch_source_records()` parse JSON thành list `PaperRecord` → `build_clean_dataframe()` normalize, tính `age_days`, tạo `text_for_embedding` (title + authors + summary) → `LocalEmbeddingIndex.build()` encode bằng MiniLM-L6-v2, lưu vào ChromaDB collection và ghi manifest JSON. Ba collection độc lập: `papers-baseline`, `papers-corrupted`, `papers-repaired`.

**2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**

Test set được sinh từ cleaned dataframe: mỗi paper cho ra 4 câu hỏi (summary/authors/date/categories) với `ground_truth_doc_ids = [paper_id]`. Khi evaluate: `answer_question()` retrieve top-k docs → nếu `paper_id` xuất hiện trong `retrieved_doc_ids` thì `retrieval_hit = True`. Token F1 đo overlap giữa text trả lời và ground_truth text. Judge LLM cho điểm 1–5 về semantic correctness.

**3. Quality checks khác freshness monitoring ở điểm nào?**

Quality checks (6 rules) kiểm tra tính toàn vẹn cấu trúc của dataset tại một thời điểm: có đủ hàng không, ID có null không, có trùng lặp không, summary có quá ngắn không. Freshness monitoring kiểm tra chiều thời gian: `age_days` của từng record so với ngưỡng 180 ngày — câu hỏi không phải "dữ liệu có hợp lệ không" mà là "dữ liệu có còn cập nhật không".

**4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**

Nếu test set thay đổi, không thể biết metric thay đổi là do chất lượng index hay do câu hỏi khó hơn/dễ hơn. Cùng test set là điều kiện cần để phép so sánh ba trạng thái có ý nghĩa nhân quả: mọi thay đổi metric đều chỉ từ dữ liệu/index, không phải từ evaluation setup.

**5. Repair được xem là thành công dựa trên artifact và metric nào?**

Repair thành công khi: (a) quality gates từng FAIL sau corruption đều trở lại PASS trong `repaired_quality.json`, (b) `repaired_freshness.json` cho `is_fresh = true`, (c) metric deltas `delta_repair ≈ 0` cho tất cả metrics trong `cp6_analysis.json`, (d) `consistent_miss = 0` trong per-answer classification. Với data thật của nhóm: tất cả bốn điều kiện đều thỏa — recovery COMPLETE.

---

## 8. Phân tích kết quả

### Metrics chính — số liệu thực tế từ artifact

| Metric / signal | Baseline | Corrupted | Repaired | Nhận xét |
| :--- | ---: | ---: | ---: | :--- |
| `retrieval_hit_rate` | 1.000 | 0.500 | 1.000 | Giảm 50% do drop_latest_record (3 docs) + blank_summary (2 docs) → pipeline không tìm được doc đúng |
| `mean_token_f1` | 0.750 | 0.298 | 0.750 | Giảm 45.2 pp — inject_noise + wrong retrieval tạo ra câu trả lời sai nội dung |
| `judge_accuracy` | 0.750 | 0.292 | 0.750 | Giảm 45.8 pp — LLM judge xác nhận câu trả lời sai nghĩa, không chỉ sai token |
| `mean_judge_score` | 4.000 | 2.125 | 4.000 | Giảm từ 4/5 xuống 2.125/5 — mức độ sai nghiêm trọng |
| Quality checks (pass/total) | 6/6 | 3/6 | 6/6 | 3 gates FAIL: `paper_id_unique`, `summary_not_blank`, `freshness_age_days` |
| Freshness (`is_fresh`) | True (0%) | False (52.2%) | True (0%) | 12/23 rows stale do stale_published_date injection |

### Kết luận từ số liệu

**1. Nhân quả — corruption → quality signal → metric:**

`drop_latest_record` (3 papers) + `blank_summary` (2 papers) → `row_count` giảm từ 24→23, `summary_not_blank` FAIL → `retrieval_hit_rate` giảm từ 1.000 xuống 0.500: pipeline không tìm được đúng document vì doc bị xóa khỏi index hoặc embedding vô nghĩa. Bằng chứng: `q001_summary` corrupted trả lời bằng nội dung của paper khác (Deep RAG survey) vì Hi-RAG paper bị drop, `q001_authors` trả lời "Lihui Liu" thay vì "Wei Tian, Yuhao Zhou".

**2. Nhân quả — repair → signal phục hồi → metric phục hồi:**

Repair từ raw lineage snapshot (`crossref_records.json`) → rebuild clean DataFrame với đủ 24 rows, summary đầy đủ, dates gốc → `repaired_quality.json` 6/6 PASS, `repaired_freshness.json` is_fresh=True → rebuild index `papers-repaired` → re-evaluate: tất cả 4 metrics về đúng baseline. `q001_authors` repaired trả lời "Wei Tian, Yuhao Zhou" (token_f1=1.0, judge_score=5).

**Corruption ảnh hưởng rõ nhất:**

`drop_latest_record` — trực tiếp làm 3 documents biến mất khỏi index, gây retrieval miss hoàn toàn cho các câu hỏi liên quan. `inject_noise` — đưa "Lorem ipsum" vào context, khiến LLM tổng hợp câu trả lời sai nghĩa dù có retrieve được gần đúng doc.

**Kết quả khác kỳ vọng:**

`stale_published_date` (12 records) — kỳ vọng làm giảm `retrieval_hit_rate` nhưng thực tế không tác động vì date không ảnh hưởng embedding. Tác động thực tế chỉ ở freshness gate. Đây là ví dụ cho mục "stable signal" — không nên kết luận stale_date làm giảm retrieval.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** Test set phải được tạo từ clean data với paper_id ổn định và frozen trước khi chạy bất kỳ evaluation nào. Nếu paper_id thay đổi giữa các lần chạy (Crossref là nguồn sống), `retrieval_hit` sẽ cho kết quả sai ngay cả khi retrieval đang hoạt động tốt.

2. **Về data quality / observability:** Không phải mọi corruption đều có quality gate bắt được. `inject_noise` và `truncate_title` vượt qua toàn bộ 6 structural checks — impact của chúng chỉ phát hiện được qua evaluation metrics. Điều này cho thấy quality gate và evaluation metrics là hai lớp phòng thủ bổ sung cho nhau, không thay thế được nhau.

3. **Về ảnh hưởng của data đến RAG agent:** Retrieval miss do mất document (drop_latest_record) gây hại nhiều hơn noise injection vì agent hoàn toàn không có đúng context để trả lời. Noise chỉ làm câu trả lời kém hơn, còn mất doc làm agent tìm sai hoàn toàn. Implication: prioritize document coverage trước content quality khi triage corruption.

### Nếu có thêm thời gian

Triển khai **per-question-type recovery breakdown** trong CP6: phân tách 12 `recovered` cases ra theo `question_type` (summary/authors/date/categories) để biết loại câu hỏi nào khó recover hơn. Đo bằng cách đếm `recovered` vs `consistent_miss` theo từng type và so sánh token_f1 delta trung bình. Hypothesis: câu hỏi `date` sẽ khó recover hơn nếu stale_published_date injection vẫn ảnh hưởng đến context ngầm.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Tạ Quốc Tuấn
**Ngày xác nhận:** 2026-08-06
