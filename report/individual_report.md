# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | Nguyễn Hữu Công |
| **MSSV** | [Điền MSSV của bạn tại đây] |
| **Khóa/Lớp** | K4 |
| **Tên nhóm** | NTPQK226 / Nhóm Day 10 B1-2 |
| **Vai trò chính** | **Role 2 — Data Layer Owner (Ingestion, Cleaning, Lineage & Data Recovery)** |
| **Repository** | `https://github.com/NTPQK226/K4_Day10_Data-Pipeline-Data-Observability-B1-2` |
| **Ngày hoàn thành** | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu (Ownership)

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Source Ingestion & Retry Mechanism** | `src/ingestion/crossref.py`<br>- `fetch_source_records`<br>- `parse_crossref_payload`<br>- `load_raw_records` | `Settings` (API URL, query, filter, timeout, max_results) | - `data/raw/crossref_response.json`<br>- `data/raw/crossref_records.json`<br>- Danh sách `PaperRecord` | **Hoàn thành (100%)** |
| **Data Cleaning & Embedding Modeling** | `src/ingestion/cleaning.py`<br>- `build_clean_dataframe` | Danh sách `PaperRecord`, `run_date` | - `data/clean/papers_clean.csv`<br>- `data/clean/papers_clean.json`<br>- Clean `pd.DataFrame` có `text_for_embedding`, `age_days` | **Hoàn thành (100%)** |
| **Data Poisoning & Corruption Engine** | `src/ingestion/corruption.py`<br>- `corrupt_clean_dataframe` | Clean `pd.DataFrame` | - `data/corrupted/papers_corrupted.csv`<br>- `data/corrupted/corruption_log.json` | **Hoàn thành** |
| **Data Lineage & Recovery Verification** | Lineage tracing & replay | `data/raw/crossref_records.json` snapshot | `data/clean/papers_clean_repaired.csv` (100% tái hiện từ snapshot) | **Hoàn thành** |

### Việc hỗ trợ ngoài phạm vi chính
- **Hỗ trợ Role 3 (RAG/Embeddings):** Cung cấp cấu trúc `text_for_embedding` và metadata null-safe giúp Role 3 index thành công vào ChromaDB collection `papers-baseline` mà không bị lỗi NaN hay type mismatch.
- **Hỗ trợ Role 4 (Observability):** Chạy và kiểm thử trực tiếp 6 bài kiểm tra Data Quality (`run_data_quality_checks`) và Freshness Report (`build_freshness_report`), bàn giao dataset sạch giúp Role 4 sinh tự động 24 câu hỏi evaluation trong `data/eval/test_set.json`.

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| **Ingestion Crossref API** | `src/ingestion/crossref.py` | 24 records raw với đầy đủ DOI, abstract, authors, publish date | `python -c "from ingestion.crossref import *; ..."` |
| **Raw Snapshot Persistence** | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json` | Snapshot raw 239 KB & 59 KB dùng cho reproducible pipeline | `ls -lh data/raw` |
| **Cleaning & Normalization** | `src/ingestion/cleaning.py` | Clean dataset 24 bài, deduplicate 0 trùng lặp, tạo `text_for_embedding` | `pd.read_csv('data/clean/papers_clean.csv')` |
| **Data Quality Gate (CP1)** | `data/quality/baseline_quality.json` | **6/6 bài kiểm tra passed (100%)** | `cat data/quality/baseline_quality.json` |
| **Freshness Observability** | `data/quality/freshness_report.json` | `is_fresh=True`, `stale_ratio=0.0%`, latest date: `2026-08-01` | `cat data/quality/freshness_report.json` |

### Mô tả Output cụ thể:
File `data/clean/papers_clean.csv` (99 KB) và `data/clean/papers_clean.json` (114 KB) chứa 24 bài báo khoa học về chủ đề *"Retrieval-Augmented Generation & Agentic LLM"* xuất bản từ 2026-01 đến 2026-08. Toàn bộ text đã được bóc thẻ XML (`<jats:p>`), chuẩn hoá khoảng trắng, tính toán `age_days` chuẩn xác và tổng hợp sẵn `text_for_embedding` phục vụ trực tiếp cho mô hình `all-MiniLM-L6-v2`.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Dữ liệu Crossref thô nhiều rác:** Abstract từ API Crossref thường chứa các thẻ XML/JATS lồng nhau (`<jats:p>`, `<jats:sec>`, `<b>`, `<i>`), format ngày tháng phân mảnh theo mảng lồng `date-parts: [[2026, 6, 15]]`, và tác giả phân rã theo `given`/`family`.
2. **Nguy cơ làm hỏng vector embeddings:** Nếu abstract rỗng, tiêu đề trống hoặc text quá ngắn, vector embeddings sẽ bị nhiễu hoặc sụp đổ (embedding collapse).
3. **Mất dấu nguồn gốc (Broken Data Lineage):** Nếu làm sạch hoặc lọc dữ liệu mà không có cơ chế log/truy vết, các bản ghi bị loại bỏ âm thầm sẽ gây mất cân đối dữ liệu mà không ai biết lý do.

### Cách triển khai
1. **Ingestion Layer (`src/ingestion/crossref.py`):**
   - Triển khai hàm `_strip_xml_tags(text)` dùng Regex `re.sub(r"<[^>]+>", " ", text)` để bóc tách triệt để toàn bộ thẻ XML.
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

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | JSON raw từ Crossref API (`WorksMessageItem` format) hoặc snapshot JSON trên đĩa |
| **Output** | `pd.DataFrame` và file `papers_clean.csv` / `papers_clean.json` chuẩn 16 cột |
| **Module phụ thuộc** | `src/core/config.py` (`Settings`), `src/core/utils.py` |
| **Module sử dụng output** | `src/retrieval/index.py` (Role 3), `src/evaluation/testset.py` (Role 4) |
| **Điều kiện lỗi cần xử lý** | Mất kết nối API, payload thiếu abstract, tác giả thiếu family name, abstract có thẻ XML rác, DOI bị duplicate |

### Cách xác minh
```bash
uv run python -c "
from core.config import load_settings
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe
from observability.quality import run_data_quality_checks, build_freshness_report

settings = load_settings()
records = load_raw_records(settings.paths.raw_records_json)
df = build_clean_dataframe(records)
q_report = run_data_quality_checks(df, settings, 'baseline_quality')
f_report = build_freshness_report(df, settings, settings.paths.freshness_report)

assert q_report['all_passed'] is True
assert f_report['is_fresh'] is True
print('VERIFICATION PASSED: Clean count =', len(df))
"
```
- **Kết quả mong đợi:** 24 clean records, 0 duplicate, 6/6 quality checks `PASS`, Freshness `is_fresh: True`.
- **Kết quả thực tế:** Đúng 100% kỳ vọng (xem log trong `data/quality/baseline_quality.json`).

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
