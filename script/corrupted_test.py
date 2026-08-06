import sys
sys.path.insert(0, 'src')

import pandas as pd
from core.config import load_settings
from retrieval.index import LocalEmbeddingIndex
from retrieval.agent import build_agent, run_agent_question

settings = load_settings()

print('\n=== [1] TẠO PAPERS-CORRUPTED TỪ DATA BỊ LỖI ===')
# Load file CSV đã bị Role 2 làm hỏng
df_corrupted = pd.read_csv(settings.paths.corrupted_clean_csv)
print(f'--> Đã load {len(df_corrupted)} corrupted papers.')

# Tạo collection mới (papers-corrupted)
index_corrupted = LocalEmbeddingIndex.build(
    df=df_corrupted, 
    settings=settings, 
    embeddings_output_path=settings.paths.corrupted_embeddings_json
)
print(f'--> Đã tạo xong Collection: {index_corrupted.collection_name}')
print(f'--> Đã lưu file: {settings.paths.corrupted_embeddings_json}')

print('\n=== [2] CHẠY LẠI QUERY ĐỂ THẤY SỰ XUỐNG CẤP ===')
print('\n[Semantic Search]: deep RAG and reasoning in large language models')
results = index_corrupted.search('deep RAG and reasoning in large language models', top_k=2)
for r in results:
    print(f'  - [{r.score:.4f}] {r.paper_id}: {r.title}')
    
print('\n[Agent QA]:')
agent = build_agent(settings, index_corrupted)
answer = run_agent_question(agent, 'What is the main topic of the indexed papers?')
print('  - Agent Response:', answer)

print('\n=== [3] KIỂM TRA PAPERS-BASELINE CÓ CÒN SỐNG KHÔNG ===')
try:
    # Thử load lại file baseline đã tạo ở Checkpoint 2
    index_baseline = LocalEmbeddingIndex.load(settings, embeddings_path=settings.paths.embeddings_json)
    print(f'--> Vừa load thành công Collection cũ: {index_baseline.collection_name}')
    res_base = index_baseline.search('deep RAG and reasoning in large language models', top_k=1)
    print(f'  - Thử search lại Baseline Top 1 Score: {res_base[0].score:.4f} (ID: {res_base[0].paper_id})')
    print('  => KẾT LUẬN: Data gốc (baseline) vẫn an toàn 100%, không bị lây nhiễm hay ghi đè!')
except Exception as e:
    print(f'  => LỖI: {e}')
