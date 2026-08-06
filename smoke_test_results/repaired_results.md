# Repaired Smoke Test Results (Checkpoint 6)

Lưu trữ kết quả truy vấn từ tập dữ liệu đã được phục hồi (repaired data) để chứng minh hệ thống RAG đã được khôi phục 100% phong độ, đồng thời 3 phiên bản dữ liệu chạy độc lập không xung đột.

## 1. Dữ liệu đầu vào
- Số lượng repaired papers: `24` (Đã lấy lại được 1 bài báo bị mất ở pha Corrupted, trở về nguyên trạng số lượng của Baseline).
- Vector Collection sinh ra: `papers-repaired`.

## 2. Sự phục hồi của Semantic Search
**Query:** `"deep RAG and reasoning in large language models"`
**Top 2 Results:**
1. `[0.5738]` 10.36227/techrxiv.177272838.89432844/v1: A Survey of (Deep RAG) Deep Retrieval Augmented Generation and Reasoning in Large Language Models *(Điểm số đã phục hồi chính xác mức 0.5738 của baseline)*
2. `[0.5396]` 10.22214/ijraset.2026.82233: Hybrid Graph Neural Network and Large Language Model Framework for Robust Knowledge Graph Question Answering via Retrieval-Augmented Generation *(Phục hồi chuẩn xác mức 0.5396 của baseline)*

## 3. Sự khôi phục của Agent QA
Agent đã lấy lại được sự sắc bén, phân loại các chủ đề cực kỳ mạch lạc (Core Themes, Agentic AI, Domain-Specific Applications, AI Governance).
👉 **Đặc biệt:** Hoàn toàn không còn cảnh báo về dữ liệu rác *"Lorem ipsum"* như ở pha Corrupted nữa. Dữ liệu đã hoàn toàn sạch sẽ!

## 4. Kiểm tra tính độc lập của 3 Collection (Yêu cầu 3)
Cả 3 Vector Database đều tải lên thành công và chạy song song độc lập:
✅ `1. papers-baseline`
✅ `2. papers-corrupted`
✅ `3. papers-repaired`
👉 **Báo cáo:** Ba trạng thái dữ liệu (Sạch, Lỗi, Phục hồi) được quản lý ở 3 bộ Vector Index hoàn toàn tách biệt, không bao giờ ghi đè lẫn nhau. Có thể tái lập lại bất cứ lúc nào!
