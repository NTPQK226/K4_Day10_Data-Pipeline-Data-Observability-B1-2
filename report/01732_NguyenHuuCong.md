# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | Nguyễn Hữu Công |
| **MSSV** | 01732 |
| **Khóa/Lớp** | K4 |
| **Tên nhóm** | NTPQK226 / Nhóm Day 10 B1-2 |
| **Vai trò chính** | **Role 2 — Data Layer Owner (Ingestion, Cleaning, Corruption, Lineage & Recovery)** |
| **Repository** | `https://github.com/NTPQK226/K4_Day10_Data-Pipeline-Data-Observability-B1-2` |
| **Ngày hoàn thành** | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu (Ownership)

| Module / Deliverable | File / Hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :---: |
| **Source Ingestion & Retry Mechanism (CP0)** | `src/ingestion/crossref.py`<br>- `fetch_source_records`<br>- `parse_crossref_payload`<br>- `load_raw_records` | `Settings` (API URL, query, filter, timeout, max_results) | - `data/raw/crossref_response.json`<br>- `data/raw/crossref_records.json`<br>- Danh sách `PaperRecord` | **Hoàn thành (100%)** |
| **Data Cleaning & Embedding Modeling (CP1)** | `src/ingestion/cleaning.py`<br>- `build_clean_dataframe` | Danh sách `PaperRecord`, `run_date` | - `data/clean/papers_clean.csv`<br>- `data/clean/papers_clean.json`<br>- Clean `pd.DataFrame` có `text_for_embedding`, `age_days` | **Hoàn thành (100%)** |
| **Data Poisoning & Corruption Engine (CP5)** | `src/ingestion/corruption.py`<br>- `corrupt_clean_dataframe` | Clean `pd.DataFrame` | - `data/clean/papers_clean_corrupted.csv`<br>- `data/clean/papers_clean_corrupted.json`<br>- `data/results/corruption_log.json` | **Hoàn thành (100%)** |
| **Data Lineage & Recovery Pipeline (CP6)** | `src/pipelines/corruption_flow.py` & Ingestion Lineage | `data/raw/crossref_records.json` snapshot | - `data/clean/papers_clean_repaired.csv`<br>- `data/clean/papers_clean_repaired.json`<br>- `data/quality/repaired_quality.json`<br>- `data/quality/repaired_freshness.json` | **Hoàn thành (100%)** |

### Việc hỗ trợ ngoài phạm vi chính
- **Hỗ trợ Role 3 (RAG/Embeddings):** Cung cấp cấu trúc `text_for_embedding` và metadata null-safe giúp Role 3 index thành công vào ChromaDB collections (`papers-baseline`, `papers-corrupted`, `papers-repaired`) mà không bị lỗi NaN hay type mismatch.
- **Hỗ trợ Role 4 & 5 (Observability & Evaluation):** Chạy và kiểm thử trực tiếp 6 bài kiểm tra Data Quality (`run_data_quality_checks`) và Freshness Report (`build_freshness_report`), bàn giao dataset sạch giúp sinh tự động 24 câu hỏi evaluation trong `data/eval/test_set.json`.

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| **Ingestion Crossref API (CP0)** | `src/ingestion/crossref.py` | 24 records raw với đầy đủ DOI, abstract, authors, publish date | `python -c "from ingestion.crossref import *; ..."` |
| **Raw Snapshot Persistence (CP0)** | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json` | Snapshot raw 239 KB & 59 KB dùng cho reproducible pipeline | `ls -lh data/raw` |
| **Cleaning & Normalization (CP1)** | `src/ingestion/cleaning.py` | Clean dataset 24 bài, deduplicate 0 trùng lặp, tạo `text_for_embedding` | `pd.read_csv('data/clean/papers_clean.csv')` |
| **Data Quality Gate (CP1)** | `data/quality/baseline_quality.json` | **6/6 bài kiểm tra passed (100%)** | `cat data/quality/baseline_quality.json` |
| **Freshness Observability (CP1)** | `data/quality/freshness_report.json` | `is_fresh=True`, `stale_ratio=0.0%`, latest date: `2026-08-01` | `cat data/quality/freshness_report.json` |
| **Controlled Corruption (CP5)** | `src/ingestion/corruption.py`<br>`data/results/corruption_log.json` | 6 kịch bản lỗi có chủ đích, 24 corruption events được log chi tiết | `cat data/results/corruption_log.json` |
| **Corrupted Artifacts (CP5)** | `data/clean/papers_clean_corrupted.csv`<br>`data/clean/papers_clean_corrupted.json` | 23 rows (3 dropped + 2 duplicate), abstract rỗng & nhiễu noise | `ls -lh data/clean/*corrupted*` |
| **Self-Healing & Data Repair (CP6)** | `data/clean/papers_clean_repaired.csv`<br>`data/clean/papers_clean_repaired.json` | Khôi phục 24/24 records hoàn toàn từ raw lineage snapshot gốc | `python -c "from ingestion.cleaning import *; ..."` |
| **Repaired Observability (CP6)** | `data/quality/repaired_quality.json`<br>`data/quality/repaired_freshness.json` | **Quality 6/6 PASS (100%)**, **Freshness is_fresh=True (0.0% stale)** | `cat data/quality/repaired_quality.json` |

### Mô tả Output cụ thể:
1. **Bộ dữ liệu Baseline (`papers_clean.csv`, 99 KB):** 24 bài báo khoa học về *"Retrieval-Augmented Generation & Agentic LLM"* xuất bản từ 2026-01 đến 2026-08. Toàn bộ text đã được bóc thẻ XML (`<jats:p>`), chuẩn hoá khoảng trắng, tính toán `age_days` chuẩn xác và tổng hợp sẵn `text_for_embedding` cho `all-MiniLM-L6-v2`.
2. **Bộ dữ liệu Corrupted (`papers_clean_corrupted.csv`, 83 KB):** Chứa 23 records mô phỏng 6 kịch bản lỗi thực tế (xóa bài mới nhất, abstract rỗng, chèn noise văn bản rác, cắt cụt title, làm cũ date về 2018, duplicate rows), làm suy giảm có kiểm soát các chỉ số RAG và kích hoạt fail 3 bài kiểm tra Quality.
3. **Bộ dữ liệu Repaired (`papers_clean_repaired.csv`, 99 KB):** Tái tạo 100% nguyên trạng từ snapshot raw JSON, đưa hệ thống trở lại trạng thái sạch hoàn hảo (6/6 quality checks pass).

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Dữ liệu Crossref thô nhiều rác:** Abstract từ API Crossref thường chứa các thẻ XML/JATS lồng nhau (`<jats:p>`, `<jats:sec>`, `<b>`, `<i>`), format ngày tháng phân mảnh theo mảng lồng `date-parts: [[2026, 6, 15]]`, và tác giả phân rã theo `given`/`family`.
2. **Nguy cơ làm hỏng vector embeddings:** Nếu abstract rỗng, tiêu đề trống hoặc text quá ngắn, vector embeddings sẽ bị nhiễu hoặc sụp đổ (embedding collapse).
3. **Mất dấu nguồn gốc (Broken Data Lineage):** Nếu làm sạch hoặc lọc dữ liệu mà không có cơ chế log/truy vết, các bản ghi bị loại bỏ âm thầm sẽ gây mất cân đối dữ liệu mà không ai biết lý do.
4. **Kiểm thử tác động của Data Drift/Poisoning (CP5):** Cần cơ chế tạo lỗi có chủ đích, có log kiểm toán (audit log) rõ ràng để đo lường định lượng mức độ sụt giảm của RAG agent và observability gates.
5. **Khả năng tự phục hồi (Self-Healing - CP6):** Chứng minh hệ thống có thể khôi phục 100% dữ liệu gốc dựa trên lineage snapshot mà không cần vá thủ công (hardcode/copy-paste).

### Cách triển khai

1. **Ingestion Layer (`src/ingestion/crossref.py`):**
   - Triển khai hàm `_strip_xml_tags(text)` dùng Regex `re.sub(r"<[^>]+>", " ", text)` kết hợp unescape HTML để bóc tách triệt để toàn bộ thẻ XML.
   - Triển khai `_format_date(date_dict)` ghép an toàn chuỗi ISO `YYYY-MM-DD`.
   - Sử dụng cơ chế **Retry với Exponential Backoff** (tối đa 3 lần) cho các lỗi mạng và HTTP status `429`, `500`, `502`, `503`, `504`.
   - Tự động nạp từ cache snapshot nếu `refresh_source=False` để đảm bảo tính lặp lại (reproducibility).

2. **Cleaning Layer (`src/ingestion/cleaning.py`):**
   - Chuẩn hoá khoảng trắng bằng `normalize_whitespace`.
   - **Deduplication:** Kiểm tra tập `seen_ids` theo `paper_id` (DOI chuẩn hoá).
   - **Quality Filtering:** Lọc bỏ các record thiếu `paper_id`, `title` rỗng hoặc `summary_chars < 50`.
   - **Freshness Calculation:** Tính `age_days = (run_date.date() - pub_date).days`.
   - **Synthesis:** Ghép trường tổng hợp chuẩn cho RAG:
     ```python
     text_for_embedding = f"Title: {title}\nAuthors: {authors_joined}\nCategories: {categories_joined}\nSummary: {summary}"
     ```

3. **Corruption Engine (`src/ingestion/corruption.py`):**
   - **Scenario 1 (Drop latest records):** Xóa 3 bài mới nhất để kiểm tra Freshness drop & Missing docs retrieval.
   - **Scenario 2 (Blank summary):** Làm rỗng abstract ở 2 bản ghi để kích hoạt fail Quality check `summary_not_blank`.
   - **Scenario 3 (Inject noise):** Chèn đoạn văn bản rác đối kháng (`CORRUPTED NOISE: ...`) để phá vỡ độ tương đồng ngữ nghĩa vector.
   - **Scenario 4 (Truncate title):** Cắt ngắn tiêu đề còn 8 ký tự để phá hỏng Exact Title Lookup.
   - **Scenario 5 (Stale published date):** Đẩy lùi ngày xuất bản về năm 2018 (`age_days > 3000`) để kích hoạt Freshness Warning (`is_fresh=False`).
   - **Scenario 6 (Add duplicate rows):** Nhân bản 2 dòng để kích hoạt fail Quality check `paper_id_unique`.
   - **Rebuild Synthesis:** Tự động tính toán lại `summary_chars` và `text_for_embedding` cho toàn bộ các dòng bị biến đổi.
   - **Audit Logging:** Ghi nhật ký có cấu trúc ra [data/results/corruption_log.json](file:///var/home/nguyenhuucong/PycharmProjects/K4_Day10_Data-Pipeline-Data-Observability-B1-2/data/results/corruption_log.json) ghi rõ ID, loại lỗi, tham số và số lượng dòng trước/sau.

4. **Data Lineage & Recovery Pipeline (CP6):**
   - Nạp lại (Reload) 24 records thô nguyên bản từ `data/raw/crossref_records.json`.
   - Thực thi lại toàn bộ quy trình cleaning chuẩn hóa để sinh ra `data/clean/papers_clean_repaired.csv`.
   - Xác minh các bản ghi bị drop/lỗi ở CP5 đã được khôi phục 100% về nguyên trạng, bảo toàn trọn vẹn data contract.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | JSON raw từ Crossref API (`WorksMessageItem` format) hoặc snapshot JSON trên đĩa |
| **Output** | `pd.DataFrame` và file `papers_clean.csv` / `papers_clean_corrupted.csv` / `papers_clean_repaired.csv` |
| **Module phụ thuộc** | `src/core/config.py` (`Settings`), `src/core/utils.py` |
| **Module sử dụng output** | `src/retrieval/index.py` (Role 3), `src/evaluation/testset.py` (Role 4), `src/observability/quality.py` (Role 5) |
| **Điều kiện lỗi cần xử lý** | Mất kết nối API, payload thiếu abstract, tác giả thiếu family name, abstract có thẻ XML rác, DOI bị duplicate |

### Cách xác minh
```bash
uv run python -c "
from core.config import load_settings
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from observability.quality import run_data_quality_checks, build_freshness_report

settings = load_settings()

# 1. Kiểm tra Ingestion & Cleaning
records = load_raw_records(settings.paths.raw_records_json)
df_clean = build_clean_dataframe(records)
q_base = run_data_quality_checks(df_clean, settings, 'baseline_quality')
assert q_base['all_passed'] is True

# 2. Kiểm tra Corruption
df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
q_corr = run_data_quality_checks(df_corrupted, settings, 'corrupted_quality')
assert q_corr['checks_failed'] == 3

# 3. Kiểm tra Repair từ Raw Snapshot
df_repaired = build_clean_dataframe(records)
q_rep = run_data_quality_checks(df_repaired, settings, 'repaired_quality')
assert q_rep['all_passed'] is True
print('ALL VERIFICATION SUITE PASSED SUCCESSFULLY!')
"
```
- **Kết quả mong đợi:** Clean 24 records (6/6 PASS) ➔ Corrupted 23 records (3/6 FAIL) ➔ Repaired 24 records (6/6 PASS).
- **Kết quả thực tế:** Đúng 100% kỳ vọng (toàn bộ assertions đều PASS).

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn khóa định danh chính (`paper_id`) cho từng tài liệu khoa học giữa 2 phương án: (A) Sinh UUID/Hash tự động ngẫu nhiên, hoặc (B) Dùng DOI chính thức của bài báo từ Crossref.
- **Các phương án đã cân nhắc:**
  1. *Phương án 1 (UUID/Auto-increment):* Đơn giản, đảm bảo không bao giờ trùng chuỗi, nhưng làm đứt gãy Data Lineage vì mỗi lần chạy sẽ sinh ra ID khác nhau, khiến `test_set.json` và ChromaDB không thể đối soát chéo.
  2. *Phương án 2 (DOI chuẩn hoá làm Stable Key):* Dùng DOI nguyên bản (ví dụ `10.47576/2949-1894.2026.7.7.023`).
- **Phương án đã chọn:** **Phương án 2 (Dùng DOI làm Stable `paper_id`)**.
- **Lý do:** Đảm bảo **Data Reproducibility** tuyệt đối. Một bài báo có ID cố định xuyên suốt cả 3 giai đoạn: Baseline ➔ Corrupted ➔ Repaired. Nhờ đó, evaluator của Role 4 có thể kiểm tra chính xác `ground_truth_doc_ids` xem RAG có retrieve đúng tài liệu gốc đó hay không.
- **Bằng chứng quyết định phù hợp:** `data/eval/test_set.json` đã ánh xạ chuẩn xác 24 câu hỏi với 24 DOI thực tế.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Abstract thô từ Crossref chứa nhiều thẻ JATS XML dạng `<jats:p>The article examines...</jats:p>` khiến embedding model bị phân tán trọng số vào các ký tự rác và giảm độ tương đồng ngữ nghĩa.
- **Lệnh tái hiện:** Xem trực tiếp raw payload trong `data/raw/crossref_response.json`.
- **Nguyên nhân gốc:** Crossref API trả về text trong schema XML định dạng tài liệu xuất bản của các nhà xuất bản khoa học.
- **Cách xử lý:** Bổ sung regex pipeline đa tầng trong `_strip_xml_tags`:
  1. Thay thế toàn bộ `<[^>]+>` thành khoảng trắng.
  2. Unescape các ký tự HTML (`&amp;`, `&lt;`, `&gt;`, `&quot;`).
  3. Gom cụm khoảng trắng thừa bằng `normalize_whitespace`.
- **Cách xác minh sau khi sửa:** Toàn bộ abstract trong `data/clean/papers_clean.csv` là plain text 100%, không còn sót bất kỳ thẻ XML nào.
- **Điều học được:** Data Cleaning cho LLM/RAG phải loại bỏ noise cấu trúc (structural noise) ngay từ tầng Ingestion trước khi đưa vào embedding.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến Vector Index như thế nào?**
   - Crossref API (HTTP REST) ➔ `raw_response.json` ➔ Parse thành `PaperRecord` (`raw_records.json`) ➔ Clean text & tính `age_days` ➔ `papers_clean.csv` ➔ Trích xuất `text_for_embedding` ➔ Mô hình MiniLM sinh vector 384 chiều ➔ Lưu vào ChromaDB Collection `papers-baseline`.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Bộ câu hỏi trong `test_set.json` chứa `ground_truth_doc_ids` (chính là DOI bài báo). Khi Agent trả lời, hệ thống đo xem tài liệu được retrieve có chứa đúng DOI đó không (`retrieval_hit_rate`), và đo độ khớp từ giữa câu trả lời với `ground_truth` (`token_f1`, `judge_score`).
3. **Quality checks khác Freshness monitoring ở điểm nào?**
   - *Quality checks:* Kiểm tra tính toàn vẹn tĩnh (Schema integrity: không null, không duplicate, độ dài abstract hợp lệ).
   - *Freshness monitoring:* Kiểm tra tính tươi mới động theo thời gian (độ trễ `age_days`, tỷ lệ bài báo cũ quá ngưỡng `freshness_threshold_days`).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Để đảm bảo tính khách quan của phép thử A/B testing. Cùng 1 tập câu hỏi chuẩn mới đo lường chính xác sự suy giảm điểm số khi dữ liệu bị lỗi (corrupted) và sự phục hồi điểm số sau khi repair.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - *Artifact:* `papers_clean_repaired.csv` khớp 100% schema và dữ liệu từ raw snapshot.
   - *Metric:* Quality checks đạt `6/6 PASS`, Freshness đạt `is_fresh: True`, và `retrieval_hit_rate` phục hồi về mức baseline.

---

## 8. Phân tích kết quả

### So sánh tín hiệu Observability & Data Quality qua 3 trạng thái:

| Metric / Tín hiệu | Baseline (Gốc) | Corrupted (Lỗi kiểm soát) | Repaired (Phục hồi từ Raw) | Nhận xét chi tiết |
| :--- | :---: | :---: | :---: | :--- |
| **Row count** | **24 records** | **23 records** (Drop 3, Add 2 dup) | **24 records** | Khôi phục 100% số lượng records từ snapshot gốc |
| **Quality Checks** | **6/6 PASS (100%)** | **3/6 PASS (3 FAILED)** | **6/6 PASS (100%)** | CP5 kích hoạt fail đúng 3 gate (`paper_id_unique`, `summary_not_blank`, `freshness_age_days`). Repaired vượt qua toàn bộ |
| **Freshness Status** | **FRESH (100%)** | **STALE (52.2% stale)** | **FRESH (100%)** | CP5 đẩy stale date về 2018; Repaired phục hồi date 2026 với `stale_ratio = 0.0%` |
| **Duplicate IDs** | **0** | **2** | **0** | Không còn hiện tượng trùng lặp khóa chính |
| **Blank Abstracts** | **0** | **2** | **0** | Đã khôi phục toàn bộ abstract đầy đủ |
| **Raw Lineage** | Độc lập từ API | Độc lập (`papers_clean_corrupted`) | Tái tạo từ `crossref_records.json` | Minh chứng Self-healing khả thi nhờ kiến trúc Raw-first |

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất:
1. **Garbage In, Garbage Out:** Dữ liệu sạch, định danh duy nhất (stable DOI) và text embedding chuẩn là nền tảng sống còn quyết định 80% hiệu năng của hệ thống RAG.
2. **Observability là tấm lưới an toàn:** Các bài kiểm tra Data Quality & Freshness giúp phát hiện sớm sự suy giảm chất lượng dữ liệu trước khi người dùng cuối nhận thấy câu trả lời của AI bị sai lệch.
3. **Data Lineage & Reproducibility:** Việc lưu trữ raw snapshot nguyên bản cho phép hệ thống tự phục hồi (self-healing) một cách tự động và đáng tin cậy.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Hữu Công  
**Ngày xác nhận:** 2026-08-06
