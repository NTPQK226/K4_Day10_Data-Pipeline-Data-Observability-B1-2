# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | Nguyễn Tuấn Phong |
| **MSSV** | 2A202601038 |
| **Khóa/Lớp** | K4 |
| **Tên nhóm** | B1-2 |
| **Vai trò chính** | **Role 1 — Pipeline Orchestration (Điều phối, Baseline & Corruption Flow)** |
| **Repository** | https://github.com/NTPQK226/K4_Day10_Data-Pipeline-Data-Observability-B1-2 |
| **Branch** | `phongnt_01038` |
| **Ngày hoàn thành** | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu (Ownership)

| Module / Deliverable | File / Hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :---: |
| **Environment Setup & Handoff Plan (CP0)** | `src/core/config.py`, `src/core/handoff.py`, `src/core/dod.py` | Settings, paths config | Env sẵn sàng, handoff plan rõ | **Hoàn thành (100%)** |
| **Baseline Orchestration (CP3)** | `src/pipelines/phase1.py` | Clean CSV, raw records | Baseline metrics, quality, freshness, report | **Hoàn thành (100%)** |
| **Corruption Flow Orchestration (CP5)** | `src/pipelines/corruption_flow.py` | Clean CSV, baseline metrics | Corrupted/repaired artifacts, comparison report | **Hoàn thành (100%)** |
| **Checkpoint Guides (CP2–CP4)** | `src/core/CP2_GUIDE.md`, `CP3_GUIDE.md`, `CP4_CHECKLIST.md` | — | Team alignment, role separation docs | **Hoàn thành (100%)** |

### Việc hỗ trợ ngoài phạm vi chính
- **Hỗ trợ Role 2 (Data Layer):** Review clean contract, xác nhận schema ổn định trước khi build index.
- **Hỗ trợ Role 3 (RAG/Embeddings):** Fix bug NaN float trong `src/retrieval/index.py` (`_build_documents`) để ChromaDB chấp nhận metadata.
- **Hỗ trợ Role 4 (Evaluation):** Điều phối để đảm bảo test set và evaluator không bị thay đổi giữa 3 trạng thái.

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| **Setup env (CP0)** | `.env.example`, `src/core/config.py` | Env với OpenRouter, paths chuẩn | `python -c "from core.config import load_settings"` |
| **Baseline Flow (CP3)** | `src/pipelines/phase1.py` | 11/11 artifacts, hit_rate=1.000 | `uv run python script/run_phase1.py` |
| **NaN Fix for Chroma (CP3)** | `src/retrieval/index.py` | Metadata float → string, collection papers-baseline OK | Embedding manifest hợp lệ |
| **Corruption Flow (CP5)** | `src/pipelines/corruption_flow.py` | 10-step flow: corrupt→rebuild→evaluate→repair→compare | `uv run python script/run_corruption_flow.py` |
| **Baseline Metrics** | `data/results/baseline_metrics.json` | hit_rate=1.000, token_f1=0.750, judge_acc=0.750 | `cat data/results/baseline_metrics.json` |
| **Corrupted Metrics** | `data/results/corrupted_metrics.json` | hit_rate=0.500 (-50%), token_f1=0.298, judge_acc=0.292 | `cat data/results/corrupted_metrics.json` |
| **Repaired Metrics** | `data/results/repaired_metrics.json` | hit_rate=1.000 (recovered), token_f1=0.750, judge_acc=0.750 | `cat data/results/repaired_metrics.json` |
| **Corruption Report** | `data/reports/corruption_report.md` | 3 trạng thái so sánh đầy đủ | Xem report |

### Mô tả Output cụ thể:
1. **Baseline Metrics (`baseline_metrics.json`):** 24 samples, retrieval_hit_rate=1.000 (perfect), mean_token_f1=0.750, judge_accuracy=0.750, mean_judge_score=4.00. Quality 6/6 PASS, Freshness FRESH 0% stale.
2. **Corrupted Metrics (`corrupted_metrics.json`):** retrieval_hit_rate giảm 50% (1.000→0.500) do drop latest records. Quality chỉ 3/6 PASS (fail: freshness_age_days, paper_id_unique, summary_not_blank). Freshness STALE 52.2%.
3. **Repaired Metrics (`repaired_metrics.json`):** Phục hồi hoàn toàn về baseline: hit_rate=1.000, token_f1=0.750, judge_acc=0.750. Quality 6/6 PASS, Freshness FRESH 0% stale.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **NaN float làm ChromaDB crash:** CSV đọc NaN thành float, Chroma không chấp nhận float trong metadata.
2. **Thứ tự chạy đúng giữa 4 vai trò:** Phong cần điều phối để Công→Tuấn→Dương→Phong không chờ nhau quá lâu.
3. **Corruption report thiếu baseline metrics:** Code đọc `.get("summary", {})` nhưng JSON top-level không có key `"summary"`.

### Cách triển khai

1. **NaN Fix (`src/retrieval/index.py`):**
   ```python
   "metadata": {
       "paper_id": str(row["paper_id"]) if pd.notna(row["paper_id"]) else "",
       "categories_joined": str(row["categories_joined"]) if pd.notna(row["categories_joined"]) else "",
       ...
   }
   ```
   Đảm bảo mọi giá trị metadata là string, không có float NaN.

2. **Baseline Flow (`src/pipelines/phase1.py`):**
   - Step 1: Load/fetch raw records (24 records)
   - Step 2: Load clean CSV (24 rows)
   - Step 3: Build Chroma index papers-baseline
   - Step 4: Load test set (24 questions)
   - Step 5: Evaluate (LLM judge)
   - Step 6: Quality checks (6/6 PASS)
   - Step 7: Freshness report (FRESH)
   - Step 8: Generate phase1_report.md

3. **Corruption Flow (`src/pipelines/corruption_flow.py`):**
   - Step 1: Load clean baseline CSV
   - Step 2: Gọi `corrupt_clean_dataframe()` → corrupted CSV
   - Step 3: Build Chroma papers-corrupted
   - Step 4: Evaluate corrupted (cùng test set cũ)
   - Step 5: Quality + freshness corrupted
   - Step 6: Repair từ raw source → rebuilt CSV
   - Step 7: Build Chroma papers-repaired
   - Step 8: Evaluate repaired
   - Step 9: Quality + freshness repaired
   - Step 10: Generate corruption_report.md

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | Clean CSV, raw records, test set |
| **Output** | 3 bộ metrics (baseline/corrupted/repaired), quality, freshness, reports |
| **Module phụ thuộc** | `src/ingestion/corruption.py` (Công), `src/retrieval/index.py` (Dương), `src/evaluation/metrics.py` (Tuấn) |
| **Điều kiện lỗi cần xử lý** | NaN float metadata, conflict merge git, missing baseline artifacts |

### Cách xác minh
```bash
# Baseline
uv run python script/run_phase1.py
# → artifacts: 11/11 OK, hit_rate=1.000

# Corruption
uv run python script/run_corruption_flow.py
# → artifacts: 12/12 OK, hit_rate=0.500 (-50%)
# Repaired: hit_rate=1.000 (recovered)
```

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** 3 trạng thái (baseline / corrupted / repaired) dùng chung một evaluation set và test set để so sánh công bằng.
- **Phương án đã chọn:** Giữ `data/eval/test_set.json` cố định, không thay đổi ground_truth_doc_ids giữa 3 trạng thái.
- **Lý do:** Đảm bảo A/B testing đáng tin cậy. Nếu test set thay đổi, không thể so sánh hit_rate giữa baseline và corrupted một cách có ý nghĩa.
- **Bằng chứng:** Cùng 24 câu hỏi, baseline hit_rate=1.000, corrupted hit_rate=0.500 — chênh lệch hoàn toàn do dữ liệu, không do test set.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** `expected string or bytes-like object, got 'float'` — ChromaDB từ chối metadata chứa NaN.
- **Nguyên nhân gốc:** CSV đọc vào pandas, giá trị NaN thành `float('nan')`, đẩy vào Chroma metadata.
- **Cách xử lý:** Sửa `_build_documents` trong `src/retrieval/index.py` dùng `pd.notna()` và `str()` cho mọi trường metadata.
- **Cách xác minh sau khi sửa:** Embedding manifest `papers_embeddings.json` có `categories_joined: ""` (string) thay vì `categories_joined: nan` (float).
- **Điều học được:** Pandas NaN là kẻ thù của các hệ thống serialization (JSON, Chroma, LLM). Luôn fillna/stringify ở tầng gần nhất trước khi lưu/truyền.

---

## 7. Hiểu biết về luồn end-to-end

1. **Dữ liệu đi từ Crossref đến Vector Index như thế nào?**
   Crossref API → `raw_response.json` → Parse → `raw_records.json` → Clean (`build_clean_dataframe`) → `papers_clean.csv` → Embedding (MiniLM) → ChromaDB `papers-baseline`.

2. **Tại sao corruption làm giảm retrieval_hit_rate từ 1.000 xuống 0.500?**
   Scenario 1 (Drop latest records) xóa 3 bài mới nhất. Test set chứa DOI của những bài bị xóa → retrieval không tìm thấy doc → hit miss → hit_rate giảm 50%.

3. **Repair phục hồi được bao nhiêu phần trăm performance?**
   100%. Repaired hit_rate quay về 1.000, token_f1 về 0.750, judge_acc về 0.750. Chứng minh pipeline có khả năng self-healing từ raw snapshot.

4. **Tại sao quality check 3/6 failed ở corrupted nhưng repaired 6/6 pass?**
   Corrupted: `summary_not_blank` fail (blank abstract), `paper_id_unique` fail (duplicate rows), `freshness_age_days` fail (stale date). Repair chạy lại từ raw → khôi phục 100% trường bị corrupt.

5. **Observability gates có thực sự catch được corruption không?**
   Có. Freshness check phát hiện STALE 52.2%, quality check phát hiện 3/6 fail. Hai gate này cảnh báo trước khi người dùng nhận câu trả lời sai.

---

## 8. Phân tích kết quả

### So sánh Metrics qua 3 trạng thái:

| Metric / Signal | Baseline | Corrupted | Repaired | Nhận xét |
| :--- | :---: | :---: | :---: | :--- |
| **retrieval_hit_rate** | **1.000** | **0.500** | **1.000** | Corruption giảm 50% → Repair phục hồi 100% |
| **mean_token_f1** | **0.750** | **0.298** | **0.750** | Noise injection phá vỡ semantic similarity |
| **judge_accuracy** | **0.750** | **0.292** | **0.750** | Judge LLM đánh giá answer từ corrupted data kém |
| **mean_judge_score** | **4.00** | **2.08** | **4.00** | Score phục hồi hoàn toàn |
| **Quality checks** | **6/6 PASS** | **3/6 FAIL** | **6/6 PASS** | Freshness, paper_id_unique, summary_not_blank fail |
| **Freshness** | **FRESH 0%** | **STALE 52.2%** | **FRESH 0%** | Date corruption bị phát hiện và phục hồi |

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất:
1. **Orchestration đi trước implementation:** Biết ai làm gì, khi nào, phụ thuộc ai trước khi viết code — tránh đợi nhau và conflict.
2. **Artifacts > Terminal:** "Chạy thành công" không đủ. Phải verify artifact tồn tại và khớp với report trước khi coi checkpoint hoàn tất.
3. **Self-healing chỉ hoạt động khi có raw lineage:** Nếu corrupt clean data mà không có raw snapshot gốc, repair không thể khôi phục 100%.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồn end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Phong
**Ngày xác nhận:** 2026-08-06
