# CP2 (01:05–01:35) — Hướng dẫn đúng cho Phong

## Ai làm gì — PHÂN BIỆT RÕ

| Ai | Việc | Pass criteria |
|---|---|---|
| **Phong (Lead)** | Điều phối, khóa contract, review handoff | Lead xác nhận được artifact tồn tại |
| **Công** | Handoff clean schema ổn định | Clean schema không đổi sau CP1 |
| **Dương** | Build RAG index (MiniLM + Chroma) | collection `papers-baseline`, semantic search OK |
| **Tuấn** | Build test set (`test_set.json`) | 24 câu hỏi, `ground_truth_doc_ids` đúng |

> **Phong KHÔNG tự build index/test set** — đó là việc của Dương/Tuấn.
> Phong chỉ **xác nhận** chúng tồn tại sau khi họ xong.

---

## Việc CỦA PHONG ở CP2

### 1. Khóa clean schema

Clean schema đã xác nhận ở CP1. Không cần làm lại — chỉ ghi nhận:

```powershell
# Xác nhận clean artifact không đổi
python -c "
import json, pandas as pd
df = pd.read_csv('data/clean/papers_clean.csv')
clean = json.load(open('data/clean/papers_clean.json'))
print(f'CSV rows: {len(df)}')
print(f'JSON rows: {len(clean)}')
print(f'paper_id unique: {df[\"paper_id\"].nunique() == len(df)}')
print(f'text_for_embedding not null: {df[\"text_for_embedding\"].notna().all()}')
"
```

### 2. Gửi handoff cho Dương

> **@Dương** — CP2 bắt đầu. Em cần làm:
> 1. Build Chroma collection `papers-baseline` từ `data/clean/papers_clean.csv`
> 2. Test semantic search với query "retrieval augmented generation"
> 3. Test exact lookup bằng `paper_id`
> 4. Báo Phong khi collection và smoke test OK

### 3. Gửi handoff cho Tuấn

> **@Tuấn** — CP2 bắt đầu. Em cần làm:
> 1. Build `data/eval/test_set.json` từ 6 papers đại diện (summary/authors/date/categories)
> 2. Đọc thử vài câu hỏi — đảm bảo `ground_truth_doc_ids` trùng `paper_id` trong clean
> 3. Báo Phong khi test set cố định

### 4. Sau khi Dương + Tuấn xong — xác nhận pass criteria

```powershell
# Check Dương: index
python -c "
from pathlib import Path
p = Path('data/embeddings/papers_embeddings.json')
print('Embedding manifest:', 'OK' if p.exists() else 'MISSING')
if p.exists():
    import json
    m = json.load(open(p))
    print(f'Collection: {m.get(\"collection_name\")}')
    print(f'Documents: {len(m.get(\"documents\", []))}')
"

# Check Dương: Chroma
python -c "
from pathlib import Path
db = Path('data/chroma/chroma.sqlite3')
print('Chroma DB:', 'OK' if db.exists() else 'MISSING')
"

# Check Tuấn: test set
python -c "
from pathlib import Path
p = Path('data/eval/test_set.json')
print('Test set:', 'OK' if p.exists() else 'MISSING')
if p.exists():
    import json
    ts = json.load(open(p))
    print(f'Questions: {len(ts)}')
    types = {}
    for q in ts:
        t = q['question_type']
        types[t] = types.get(t, 0) + 1
    print(f'Types: {types}')
"
```

### 5. Ghi blocker (nếu có)

- Nếu Dương chưa xong index → ghi "Blocked: waiting for RAG index"
- Nếu Tuấn chưa xong test set → ghi "Blocked: waiting for test set"
- Nếu semantic search không tìm thấy gì → ghi blocker cho Dương sửa contract

### 6. Tài liệu hóa CP2

Tạo `src/core/cp2_contract.md`:

```markdown
# CP2 Contract — Test Set & RAG Index

**Ngày:** 2026-08-06
**Lead:** Phong
**Trạng thái:** ĐANG CHỜ DƯƠNG + TUẤN

## Handoff nhận

- `data/clean/papers_clean.csv` — 24 rows, schema ổn định từ CP1
- `data/clean/papers_clean.json` — tương đương CSV

## Artifact chờ từ Dương

- `data/embeddings/papers_embeddings.json` — manifest
- `data/chroma/papers-baseline/` — collection

## Artifact chờ từ Tuấn

- `data/eval/test_set.json` — 24 câu hỏi (6 papers × 4 types)

## Pass criteria (sẽ verify khi Dương + Tuấn báo xong)

- [ ] Embedding manifest tồn tại
- [ ] Chroma collection `papers-baseline` tồn tại
- [ ] Semantic search trả kết quả (Dương smoke test)
- [ ] Exact lookup hoạt động (Dương smoke test)
- [ ] Test set có 24 câu hỏi
- [ ] `ground_truth_doc_ids` khớp `paper_id` trong clean data
```

---

## CHECKLIST PHONG CP2

```
[ ] Clean schema ổn định (từ CP1, không đổi)
[ ] Đã gửi handoff cho Dương (build RAG index)
[ ] Đã gửi handoff cho Tuấn (build test set)
[ ] Dương báo index + smoke test OK
[ ] Tuấn báo test set cố định
[ ] Embedding manifest tồn tại
[ ] Chroma collection tồn tại
[ ] Test set 24 câu hỏi đúng format
[ ] Ghi rõ 1 blocker (nếu có)
[ ] Cập nhật cp2_contract.md
```

---

## Sau CP2 — Phong tiếp tục CP3

Khi Dương + Tuấn báo xong → Phong:
1. Verify pass criteria
2. Chuyển sang CP3 (01:35–02:00): implement `phase1.py` end-to-end
3. Gộp tất cả: raw → clean → index → evaluate → quality → freshness → report
