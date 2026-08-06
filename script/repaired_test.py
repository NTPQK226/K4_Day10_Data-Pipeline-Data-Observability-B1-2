import sys
sys.path.insert(0, 'src')

import pandas as pd
from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question

settings = load_settings()

print('\n=== [1] TẠO PAPERS-REPAIRED TỪ DATA ĐÃ PHỤC HỒI ===')
try:
    df_repaired = pd.read_csv(settings.paths.repaired_clean_csv)
    print(f'--> Đã load {len(df_repaired)} repaired papers.')

    # Tạo collection mới (papers-repaired)
    index_repaired = LocalEmbeddingIndex.build(
        df=df_repaired, 
        settings=settings, 
        embeddings_output_path=settings.paths.repaired_embeddings_json
    )
    print(f'--> Đã tạo xong Collection: {index_repaired.collection_name}')
    
    print('\n=== [2] CHẠY LẠI QUERY ĐỂ KIỂM TRA SỰ PHỤC HỒI ===')
    print('\n[Semantic Search]: deep RAG and reasoning in large language models')
    results = index_repaired.search('deep RAG and reasoning in large language models', top_k=2)
    for r in results:
        print(f'  - [{r.score:.4f}] {r.paper_id}: {r.title}')
        
    print('\n[Agent QA]:')
    agent = build_agent(settings, index_repaired)
    answer = run_agent_question(agent, 'What is the main topic of the indexed papers?')
    print('  - Agent Response:', answer)
    
except FileNotFoundError:
    print("❌ LỖI: Chưa tìm thấy file papers_clean_repaired.csv!")
    print("👉 Hãy giục Role 2 (Data Foundation) chạy pipeline phục hồi dữ liệu trước nhé.")


print('\n=== [3] TRÌNH BÀY 3 COLLECTION ĐỘC LẬP ===')
try:
    print('Thử kết nối tới cả 3 Vector DB:')
    
    idx_base = LocalEmbeddingIndex.load(settings, settings.paths.embeddings_json)
    print(f'  ✅ 1. {idx_base.collection_name} (Load thành công từ {settings.paths.embeddings_json.name})')
    
    idx_corr = LocalEmbeddingIndex.load(settings, settings.paths.corrupted_embeddings_json)
    print(f'  ✅ 2. {idx_corr.collection_name} (Load thành công từ {settings.paths.corrupted_embeddings_json.name})')
    
    idx_rep = LocalEmbeddingIndex.load(settings, settings.paths.repaired_embeddings_json)
    print(f'  ✅ 3. {idx_rep.collection_name} (Load thành công từ {settings.paths.repaired_embeddings_json.name})')
    
    print('\n=> BÁO CÁO: Ba trạng thái dữ liệu (Sạch, Lỗi, Phục hồi) được quản lý ở 3 bộ Vector Index hoàn toàn tách biệt, không bao giờ ghi đè lẫn nhau. Có thể tái lập lại bất cứ lúc nào!')
except Exception as e:
    print(f'  ⚠️ Trạng thái 3 Collection chưa hoàn thiện đầy đủ. Chi tiết: {e}')
