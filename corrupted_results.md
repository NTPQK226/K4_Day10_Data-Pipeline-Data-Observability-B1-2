# Corrupted Smoke Test Results (Checkpoint 5)

Lưu trữ kết quả truy vấn từ tập dữ liệu bị lỗi (corrupted data) để chứng minh sự xuống cấp của hệ thống RAG và tính an toàn của baseline.

## 1. Dữ liệu đầu vào
- Số lượng corrupted papers: `23` (Đã mất đi 1 bài so với 24 bài của baseline sạch).
- Vector Collection sinh ra: `papers-corrupted` (Hoạt động độc lập).

## 2. Sự xuống cấp của Semantic Search
**Query:** `"deep RAG and reasoning in large language models"`
**Top 2 Results:**
1. `[0.5482]` 10.36227/techrxiv.177272838.89432844/v1: A Survey of (Deep RAG) Deep Retrieval Augmented Generation and Reasoning in Large Language Models *(Giảm so với 0.5738 của baseline)*
2. `[0.5260]` 10.22214/ijraset.2026.82233: Hybrid Graph Neural Network and Large Language Model Framework for Robust Knowledge Graph Question Answering via Retrieval-Augmented Generation *(Giảm so với 0.5396 của baseline)*

## 3. Sự suy giảm chất lượng Agent QA
Agent vẫn trả lời được cấu trúc chính, nhưng đã phát hiện ra rác trong dữ liệu và đưa ra cảnh báo:
> *"Note: A few papers in the corpus appear to have corrupted or synthetic "noise" injected into their summaries (e.g., "Lorem ipsum" text), which may affect the reliability of some retrieved content."*
*(Dữ liệu bẩn "Lorem ipsum" đã lọt vào Context của RAG, khiến câu trả lời của AI kém tin cậy hơn).*

## 4. Kiểm tra tính toàn vẹn của Baseline
**Kết quả Load Baseline cũ:** `Thành công`
**Test Search trên Baseline cũ:** `Score: 0.5738` (Vẫn giữ nguyên phong độ ban đầu).
**Kết luận:** Data gốc (baseline) vẫn an toàn 100%, không bị lây nhiễm hay ghi đè.
