# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Tuấn Dương             |
| MSSV               | 01966                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | B1-2     |
| Vai trò chính    | Role 3 - RAG & Agent Owner                 |
| Repository         | https://github.com/NTPQK226/K4_Day10_Data-Pipeline-Data-Observability-B1-2 |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Xây dựng Vector Index | `src/retrieval/index.py` (LocalEmbeddingIndex) | Dữ liệu sạch `papers_clean.csv` | `papers-baseline` collection & `papers_embeddings.json` manifest | Hoàn thành |
| Kiểm thử RAG (Baseline) | `script/smoke-test.py` | Vector Index Baseline | Báo cáo `report/baseline_results.md` | Hoàn thành |
| Tạo và test Corrupted Index | `script/corrupted_test.py` | Dữ liệu hỏng `papers_clean_corrupted.csv` | Báo cáo `report/corrupted_results.md` | Hoàn thành |
| Phục hồi & test Repaired Index | `script/repaired_test.py` | Dữ liệu phục hồi `papers_clean_repaired.csv` | Báo cáo `report/repaired_results.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Tổ chức lại thư mục dự án | Cả team | Đưa các script chạy test vào `script/` và báo cáo kết quả vào `report/` gọn gàng. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Khởi tạo Embeddings | `data/chroma/`, `data/embeddings/` | 3 collection chạy độc lập: baseline, corrupted, repaired | Chạy script kiểm tra thấy 3 file manifest JSON tồn tại |
| Khởi tạo Agent & Tools | `src/retrieval/agent.py` | AI Agent biết dùng Tool để trả lời câu hỏi chuyên sâu | In ra câu trả lời xuất sắc ở các file kết quả `_results.md` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:
Các file `report/baseline_results.md`, `report/corrupted_results.md` và `report/repaired_results.md` ghi nhận bằng chứng rõ ràng sự thay đổi điểm số Semantic Search (từ 0.5738 rớt xuống 0.5482 do rác, rồi phục hồi về 0.5738) cũng như sự nhiễu loạn của Agent (phát hiện ra rác "Lorem ipsum").

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Hệ thống AI (LLM) nếu chỉ hỏi - đáp thông thường sẽ bịa ra kiến thức (hallucinate) vì không có chuyên môn về tập dữ liệu bài báo của dự án. Cần một Data Pipeline để nhúng (embed) các bài báo thành dạng Vector để AI có thể tra cứu và lấy đúng bối cảnh trước khi trả lời.

### Cách triển khai
Tôi sử dụng mô hình nhúng `sentence-transformers/all-MiniLM-L6-v2` thông qua thư viện HuggingFace. Dữ liệu từ cột `text_for_embedding` (đã được Role 2 chuẩn bị) sẽ được nhúng thành vector 384 chiều và lưu vào cơ sở dữ liệu `ChromaDB`. Hệ thống lưu trạng thái độc lập thành 3 collections riêng biệt để so sánh các pha Data Observability. Agent sẽ sử dụng hàm `search` của Index này như một Tool.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Pandas DataFrame từ `papers_clean*.csv` (cần 9 cột cơ bản như paper_id, text_for_embedding) |
| Output                         | Vector Collection (ChromaDB) và 1 file Manifest JSON (`papers_embeddings.json`) |
| Module phụ thuộc             | `src/core/config.py` (để lấy đường dẫn) và file CSV do Role 2 tạo. |
| Module sử dụng output        | `src/retrieval/agent.py` và `src/evaluation/testset.py` (của Role 4). |
| Điều kiện lỗi cần xử lý | Lỗi `Collection does not exist` nếu file database bị xóa nhầm, hoặc `FileNotFoundError` nếu Role 2 chưa tạo CSV. |

### Cách xác minh

```bash
$env:PYTHONPATH="src"; python script/smoke-test.py
```

- **Kết quả mong đợi:** Tải đúng 24 bài báo, Top 1 search có score cao > 0.5. Agent trả lời đúng nội dung bài báo, không bịa.
- **Kết quả thực tế:** Hệ thống tạo thành công index, Search trả về `0.5738` cho bài báo Deep RAG. Agent trả lời xuất sắc.
- **Artifact/log:** `report/baseline_results.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần xử lý việc lưu trữ cùng lúc 3 bộ dữ liệu (Baseline, Corrupted, Repaired) cho pha Data Observability mà không bị nhầm lẫn.
- **Các phương án đã cân nhắc:** (1) Dùng 3 thư mục ChromaDB hoàn toàn khác nhau. (2) Dùng chung 1 thư mục ChromaDB nhưng chia làm 3 Collection khác nhau.
- **Phương án đã chọn:** Phương án (2) - dùng 3 Collection: `papers-baseline`, `papers-corrupted`, `papers-repaired`.
- **Lý do:** Giúp tiết kiệm dung lượng ổ cứng, dễ dàng truyền vào cùng một `PersistentClient` của ChromaDB, chỉ khác tên Collection (được hàm `_derive_collection_name` xử lý tự động qua path của manifest).
- **Bằng chứng quyết định phù hợp:** Script `repaired_test.py` kết nối và in ra thành công cả 3 Vector DB chạy song song, dữ liệu không đụng chạm nhau.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'core'`
- **Lệnh hoặc bước tái hiện:** Chạy `python smoke-test.py` ở thư mục gốc.
- **Nguyên nhân gốc:** Trình biên dịch Python theo mặc định chỉ tìm kiếm code (`core`, `retrieval`) trong thư mục hiện tại, không tự động đi sâu vào thư mục `src/`.
- **Cách xử lý:** Bổ sung `import sys; sys.path.insert(0, 'src')` vào đầu file script HOẶC dùng biến môi trường `$env:PYTHONPATH="src"` trước khi chạy python.
- **Cách xác minh sau khi sửa:** Chạy lại lệnh không còn báo lỗi ModuleNotFoundError.
- **Điều học được:** Khi cấu trúc thư mục phức tạp (tách src và script riêng), luôn phải quản lý cẩn thận `sys.path` hoặc khai báo đường dẫn môi trường.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
   - API Crossref -> Role 2 (Data Foundation) kéo về tạo Raw -> Làm sạch và nối các chuỗi thành `text_for_embedding` lưu ra `papers_clean.csv` -> Role 3 load CSV lên, chạy MiniLM biến thành Vector nhúng -> Đưa vào Collection trong ChromaDB.
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
   - Hệ thống dùng câu hỏi trong Test Set chọc vào Retrieval (Vector Index). Nếu Top K bài báo trả về có chứa `ground-truth document IDs` thì tính là Hit (trúng đích).
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
   - Quality checks tập trung vào tính đúng đắn của cấu trúc, schema (VD: summary có bị thiếu, bị null, hay bị điền rác không). Freshness monitoring chỉ quan tâm đến tính thời sự (bài báo có xuất bản cách đây > 180 ngày không).
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
   - Để đảm bảo bài kiểm tra là công bằng (apple-to-apple comparison). Nếu dùng Test set khác nhau, ta sẽ không biết Agent trả lời kém đi là do dữ liệu bẩn (corrupted) hay do câu hỏi mới quá khó.
5. Repair được xem là thành công dựa trên artifact và metric nào?
   - Dựa trên việc điểm số (Semantic search score / F1 Score) phải quay trở lại bằng đúng (hoặc tương đương) với mức điểm ở pha Baseline.

## 8. Phân tích kết quả

### Metrics chính (Từ kiểm thử thủ công - Trích xuất từ Script)

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `semantic_search_top1` |   0.5738 |    0.5482 |   0.5738 | Khôi phục chính xác phong độ ban đầu |
| Quality checks         |   [Sạch] |  [Có rác] |   [Sạch] | Role 2 đã mô phỏng thành công Data Corruption |
| `agent_response`       | [Chuẩn] | [Cảnh báo]|  [Chuẩn] | Rác "Lorem ipsum" đã bị loại trừ triệt để ở bản Repaired |

### Kết luận từ số liệu

1. [Data corruption] → [Nhiễu dữ liệu / Score tụt xuống 0.5482] → [Agent nhận ra rác Lorem ipsum].
2. [Repair action] → [Quality/freshness signal sạch sẽ] → [Semantic Search hồi phục về 0.5738 và Agent trả lời chuẩn].

Corruption nào ảnh hưởng rõ nhất và vì sao?
Việc trộn text rác ("Lorem ipsum") vào trường `summary` đã làm méo mó bộ vector nhúng của bài báo, khiến khoảng cách vector thay đổi (Score bị tụt đi rõ rệt), từ đó khiến AI Agent phải đưa ra cảnh báo về dữ liệu giả định.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Tầm quan trọng của Data Clean: Dữ liệu bẩn đầu vào (Garbage in) sẽ sinh ra rác đầu ra (Garbage out) khiến RAG bị suy giảm chất lượng rõ rệt.
2. Sức mạnh của Architecture: Việc phân tách thành các Collection độc lập trên ChromaDB giúp Roll-back / So sánh các phiên bản dữ liệu an toàn và linh hoạt.
3. Việc Agent tự động gọi Tools (Function Calling) giúp AI được gắn chặt vào ngữ cảnh của Vector DB thay vì bịa chuyện vô cớ.

### Nếu có thêm thời gian
Sẽ bổ sung thêm cơ chế Hybrid Search (BM25 + Semantic Search) vào file `index.py` để gia tăng khả năng tìm kiếm từ khóa chính xác (Exact Keyword Matching), giúp khắc phục những hạn chế mà Semantic Search thuần túy bỏ lỡ.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Tuấn Dương
**Ngày xác nhận:** 2026-08-06
