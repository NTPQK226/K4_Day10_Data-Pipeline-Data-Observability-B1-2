# Baseline Smoke Test Results (Checkpoint 2)

Lưu trữ kết quả truy vấn chuẩn (baseline) từ tập dữ liệu sạch (clean data) để đối chiếu ở các pha tiếp theo (ví dụ: Pha Data Corruption).

## 1. Semantic Search
**Query:** `"deep RAG and reasoning in large language models"`
**Top 2 Results:**
1. `[0.5738]` 10.36227/techrxiv.177272838.89432844/v1: A Survey of (Deep RAG) Deep Retrieval Augmented Generation and Reasoning in Large Language Models
2. `[0.5396]` 10.22214/ijraset.2026.82233: Hybrid Graph Neural Network and Large Language Model Framework for Robust Knowledge Graph Question Answering via Retrieval-Augmented Generation

## 2. Exact Lookup
**Query ID:** `10.1111/exsy.70341`
**Result:** `FOUND`

## 3. Agent QA
**Question:** `"What is the main topic of the indexed papers?"`
**Agent Response:**
> Based on my exploration of the indexed corpus, the papers are strongly centered on a cohesive set of topics in modern artificial intelligence. Here's a summary of the main themes:
> 
> ## Core Focus: Large Language Models (LLMs) & Retrieval-Augmented Generation (RAG)
> The dominant theme across the corpus is **large language models (LLMs)** and **retrieval-augmented generation (RAG)** — techniques that ground LLM outputs in external, verifiable knowledge sources to improve accuracy and reduce hallucination. Many papers explore:
> - **RAG architectures** — hybrid retrieval, deep RAG, GraphRAG, agentic RAG, and multi-stage retrieval frameworks
> - **Agentic AI** — autonomous agents with reasoning, memory, tool use, and multi-agent collaboration
> - **Fine-tuning and adaptation** of LLMs for specialized domains
> - **AI governance** — frameworks for governing GenAI, RAG, and agentic systems (e.g., NIST, ISO, EU AI Act alignment)
> 
> ## Application Domains
> The corpus applies these AI techniques across a wide range of fields:
> - **Healthcare/Medicine** — clinical decision support systems, medical education, sleep medicine, diagnostic support (e.g., jawbone lesion diagnosis), biomedical RAG
> - **Engineering & Construction** — building code compliance (roof design), oil & gas safety report generation
> - **Legal/Religious/Regulatory** — Islamic fatwa chatbots, insurance information delivery in regulated low-resource domains
> - **Scientific research** — automated literature review generation
> - **Enterprise/Governance** — AI platform risk assessment and governance prioritization      
> 
> ## Key Technical Themes
> - **Hallucination mitigation** and factual grounding
> - **Hybrid retrieval** (semantic + structural/sparse)
> - **Knowledge graphs** and question answering (KGQA)
> - **Multimodal systems** (vision-language models combined with RAG)
> - **Evaluation metrics** (BERTScore, BARTScore, accuracy, faithfulness)
> 
> In short, the corpus is unified around **applied LLM research — particularly RAG and agentic AI — and its deployment across healthcare, engineering, legal/regulatory, and enterprise domains**, with a strong emphasis on improving reliability, accuracy, and governance of these systems.
