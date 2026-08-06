# CP4 (02:00–02:15) — Nghỉ 15 phút

**Lead:** Phong

---

## Baseline Checklist — đã hoàn thành

```
[OK] Raw response + raw records JSON tồn tại (24 records)
[OK] paper_id stable, unique, xuyên suốt raw→clean→index
[OK] text_for_embedding không rỗng, đủ cho embedding
[OK] Chroma papers-baseline collection tồn tại (24 docs)
[OK] Test set 24 câu hỏi cố định (không đổi qua CP5/CP6)
[OK] baseline_metrics.json: hit_rate=1.000, token_f1=0.750, judge_acc=0.750
[OK] 6/6 quality checks PASS
[OK] Freshness: FRESH (0% stale)
[OK] phase1_report.md khớp artifact
[OK] src/pipelines/phase1.py hoàn chỉnh
```

---

## Blocker còn lại

**Không có blocker nghiêm trọng.**

Nhỏ: `categories_joined` có giá trị rỗng ở 1 số paper → metadata NaN → đã fix bằng fillna string trong `_build_documents`. Manifest rebuild OK.

---

## Sau nghỉ — CP5 cần chuẩn bị

| Ai | Chuẩn bị trước CP5 |
|---|---|
| **Công** | Chọn corruption scenario có chủ đích, ghi log format (ID, type, param, before/after) |
| **Dương** | Giữ ví dụ query baseline để đối chiếu sau corruption |
| **Tuấn** | Dự báo quality/freshness signal sẽ thay đổi thế nào |
| **Phong** | Implement `corruption_flow.py` trong `src/pipelines/` |

---

**→ NGHỈ 15 PHÚT. Hẹn gặp lại lúc 02:15.**
