# Clean Contract — CP1 Checkpoint

**Ngày:** 2026-08-06
**Checkpoint:** CP1
**Lead:** Phong
**Trạng thái:** APPROVED — không có blocker

---

## Contract

| Field | Type | Nullable | Mô tả |
|---|---|---|---|
| `paper_id` | string | ❌ | Stable ID từ DOI + year, unique, dùng xuyên suốt raw→clean→index |
| `doi` | string | ✅ | DOI gốc, có prefix `https://doi.org/` |
| `title` | string | ❌ | Tiêu đề paper đã normalize whitespace |
| `authors` | list[str] | ✅ | Danh sách tác giả |
| `published` | string (ISO date) | ✅ | Ngày xuất bản gốc |
| `age_days` | int | ❌ | Số ngày từ published đến hôm nay |
| `categories` | list[str] | ✅ | Chủ đề/topic |
| `abstract` | string | ✅ | Abstract gốc |
| `summary` | string | ✅ | Summary/description đã normalize |
| `text_for_embedding` | string | ❌ | Chuỗi ghép title + summary, dùng làm embedding input, không được rỗng |
| `url` | string | ✅ | Link đến paper |

---

## Evidence (2026-08-06)

```
Raw records:  24
Clean records: 24
Chênh lệch:   0 (0.0%)  ← không có filter/dedupe ở CP1
paper_id:     unique (đã xác minh)
text_for_embedding: không rỗng (đã xác minh)
age_days:     present (đã xác minh)
```

---

## Data Quality Baseline (từ Tuấn)

- `data/quality/baseline_quality.json` — đã tồn tại
- `data/quality/freshness_report.json` — đã tồn tại

---

## Artifacts

| File | Owner |
|---|---|
| `data/clean/papers_clean.csv` | Công |
| `data/clean/papers_clean.json` | Công |

---

## Next: CP2 — Test Set & RAG Index

- Handoff clean → Dương (index)
- Handoff clean → Tuấn (test set)
- Công đã giao clean xong → **CÓ THỂ CHUYỂN CP2**
