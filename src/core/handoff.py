"""Handoff plan & ownership cho Data Pipeline Lab (Day 10).

File nay thuoc role LEAD (Pipeline Integrator) - Phong.
Muc dich:
- Chot ownership cho tung artifact giua 4 thanh vien.
- Lapan so do handoff: raw -> clean -> index -> evaluate -> report.
- Tranh trung lap bien / path giua cac role.

Khong sua, khong override file cua cac role khac.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# Thanh vien nhom (anh xa MSSV)
MEMBERS: dict[str, str] = {
    "phong": "Nguyen Tuan Phong | 2A202601038 | Lead - Pipeline Integrator",
    "cong":  "Nguyen Huu Cong  | 2A202601732 | Data Foundation & Recovery",
    "duong": "Nguyen Tuan Duong | 2A202601966 | RAG & Agent Owner",
    "tuan":  "Ta Quoc Tuan     | 2A202601114 | Evaluation & Observability",
}


@dataclass(frozen=True)
class ArtifactOwner:
    """Mot artifact trong pipeline + nguoi phu trach + role doc lap."""

    name: str          # Ten hien thi (vd: "raw records JSON")
    path: str          # Path tuong doi tu project root
    owner: str         # Key trong MEMBERS (phong | cong | duong | tuan)
    depends_on: tuple[str, ...] = ()  # Artifact can co truoc khi tao
    notes: str = ""    # Ly do / canh bao


# Danh sach artifact trong 3 trang thai (baseline / corrupted / repaired).
# Moi trang thai giu collection/path rieng -> khong ghi de baseline.
ARTIFACTS: tuple[ArtifactOwner, ...] = (
    # ====== INGESTION (Công - Data Foundation) ======
    ArtifactOwner(
        name="raw Crossref API response",
        path="data/raw/crossref_response.json",
        owner="cong",
        notes="Snapshot goc, khong sua; dung lam diem phuc hoi khi repair.",
    ),
    ArtifactOwner(
        name="raw records JSON (parsed)",
        path="data/raw/crossref_records.json",
        owner="cong",
        depends_on=("raw Crossref API response",),
        notes="Schema thong nhat: paper_id (stable ID), doi, title, abstract, authors, published, categories.",
    ),
    ArtifactOwner(
        name="clean CSV (baseline)",
        path="data/clean/papers_clean.csv",
        owner="cong",
        depends_on=("raw records JSON (parsed)",),
    ),
    ArtifactOwner(
        name="clean JSON (baseline)",
        path="data/clean/papers_clean.json",
        owner="cong",
        depends_on=("raw records JSON (parsed)",),
        notes="Bat buoc co text_for_embedding va age_days.",
    ),
    ArtifactOwner(
        name="clean CSV (corrupted)",
        path="data/clean/papers_clean_corrupted.csv",
        owner="cong",
        depends_on=("clean CSV (baseline)",),
        notes="Phai co log: record ID, type, parameter, before/after count.",
    ),
    ArtifactOwner(
        name="clean JSON (corrupted)",
        path="data/clean/papers_clean_corrupted.json",
        owner="cong",
        depends_on=("clean JSON (baseline)",),
    ),
    ArtifactOwner(
        name="clean CSV (repaired)",
        path="data/clean/papers_clean_repaired.csv",
        owner="cong",
        depends_on=("clean CSV (corrupted)", "raw records JSON (parsed)"),
        notes="Repair bang cach re-run cleaning tu raw, KHONG sua tay tu baseline.",
    ),
    ArtifactOwner(
        name="clean JSON (repaired)",
        path="data/clean/papers_clean_repaired.json",
        owner="cong",
        depends_on=("clean JSON (corrupted)", "raw records JSON (parsed)"),
    ),

    # ====== RAG (Dương - RAG & Agent) ======
    ArtifactOwner(
        name="embedding manifest (baseline)",
        path="data/embeddings/papers_embeddings.json",
        owner="duong",
        depends_on=("clean JSON (baseline)",),
        notes="MiniLM-L6-v2 + collection 'papers-baseline'.",
    ),
    ArtifactOwner(
        name="embedding manifest (corrupted)",
        path="data/embeddings/papers_embeddings_corrupted.json",
        owner="duong",
        depends_on=("clean JSON (corrupted)",),
        notes="Collection 'papers-corrupted', khong anh huong baseline.",
    ),
    ArtifactOwner(
        name="embedding manifest (repaired)",
        path="data/embeddings/papers_embeddings_repaired.json",
        owner="duong",
        depends_on=("clean JSON (repaired)",),
        notes="Collection 'papers-repaired'.",
    ),
    ArtifactOwner(
        name="Chroma collection papers-baseline",
        path="data/chroma/papers-baseline",
        owner="duong",
        depends_on=("embedding manifest (baseline)",),
    ),
    ArtifactOwner(
        name="Chroma collection papers-corrupted",
        path="data/chroma/papers-corrupted",
        owner="duong",
        depends_on=("embedding manifest (corrupted)",),
    ),
    ArtifactOwner(
        name="Chroma collection papers-repaired",
        path="data/chroma/papers-repaired",
        owner="duong",
        depends_on=("embedding manifest (repaired)",),
    ),

    # ====== EVALUATION (Tuấn - Eval & Observability) ======
    ArtifactOwner(
        name="evaluation test set",
        path="data/eval/test_set.json",
        owner="tuan",
        depends_on=("clean JSON (baseline)",),
        notes="Khoa test set ngay sau CP2; KHONG doi khi qua corrupted/repaired.",
    ),
    ArtifactOwner(
        name="baseline metrics JSON",
        path="data/results/baseline_metrics.json",
        owner="tuan",
        depends_on=("Chroma collection papers-baseline", "evaluation test set"),
    ),
    ArtifactOwner(
        name="baseline answers JSON",
        path="data/results/baseline_answers.json",
        owner="tuan",
        depends_on=("Chroma collection papers-baseline", "evaluation test set"),
    ),
    ArtifactOwner(
        name="corrupted metrics JSON",
        path="data/results/corrupted_metrics.json",
        owner="tuan",
        depends_on=("Chroma collection papers-corrupted", "evaluation test set"),
    ),
    ArtifactOwner(
        name="corrupted answers JSON",
        path="data/results/corrupted_answers.json",
        owner="tuan",
        depends_on=("Chroma collection papers-corrupted", "evaluation test set"),
    ),
    ArtifactOwner(
        name="repaired metrics JSON",
        path="data/results/repaired_metrics.json",
        owner="tuan",
        depends_on=("Chroma collection papers-repaired", "evaluation test set"),
    ),
    ArtifactOwner(
        name="repaired answers JSON",
        path="data/results/repaired_answers.json",
        owner="tuan",
        depends_on=("Chroma collection papers-repaired", "evaluation test set"),
    ),
    ArtifactOwner(
        name="corruption log",
        path="data/results/corruption_log.json",
        owner="tuan",
        depends_on=("clean CSV (corrupted)",),
        notes="Moi loai corruption: record ID, type, parameter, before/after count.",
    ),
    ArtifactOwner(
        name="freshness report",
        path="data/quality/freshness_report.json",
        owner="tuan",
        depends_on=("clean JSON (baseline)",),
    ),
    ArtifactOwner(
        name="quality (GX) outputs",
        path="data/quality/gx",
        owner="tuan",
        depends_on=("clean JSON (baseline)",),
    ),
    ArtifactOwner(
        name="phase1 report",
        path="data/reports/phase1_report.md",
        owner="tuan",
        depends_on=("baseline metrics JSON", "freshness report"),
    ),
    ArtifactOwner(
        name="comparison report",
        path="data/reports/corruption_report.md",
        owner="tuan",
        depends_on=("baseline metrics JSON", "corrupted metrics JSON", "repaired metrics JSON"),
    ),

    # ====== LEAD (Phong - Pipeline Integrator) ======
    ArtifactOwner(
        name="baseline orchestrator entrypoint",
        path="script/run_phase1.py",
        owner="phong",
        depends_on=("raw records JSON (parsed)",),
        notes="Orchestration, khong xu ly logic rieng.",
    ),
    ArtifactOwner(
        name="corruption flow orchestrator",
        path="script/run_corruption_flow.py",
        owner="phong",
        depends_on=("raw records JSON (parsed)", "clean CSV (baseline)"),
    ),
    ArtifactOwner(
        name="settings & paths",
        path="src/core/config.py",
        owner="phong",
        notes="Chinh sua cac path/setting lien quan den orchestration nhu: collection name, source query, refresh flag.",
    ),
)


@dataclass(frozen=True)
class HandoffEdge:
    """Canh trong so do handoff: tu upstream -> downstream."""

    upstream: str
    downstream: str
    trigger: str  # Khi nao can chuyen (vd: "sau khi parse", "sau khi clean", "sau khi test set bi khoa")


# Edge giua artifact (chi dinh thu tu can thiet de chay pipeline)
HANDOFF_EDGES: tuple[HandoffEdge, ...] = (
    HandoffEdge("raw records JSON (parsed)", "clean CSV (baseline)", "sau khi parse xong records"),
    HandoffEdge("clean CSV (baseline)", "clean JSON (baseline)", "sau khi clean schema on dinh"),
    HandoffEdge("clean JSON (baseline)", "embedding manifest (baseline)", "sau khi build text_for_embedding"),
    HandoffEdge("clean JSON (baseline)", "evaluation test set", "sau khi paper_id stable"),
    HandoffEdge("Chroma collection papers-baseline", "baseline metrics JSON", "sau khi build collection"),
    HandoffEdge("baseline metrics JSON", "phase1 report", "sau khi evaluate xong"),
    HandoffEdge("clean CSV (baseline)", "clean CSV (corrupted)", "sau khi baseline checklist PASS"),
    HandoffEdge("clean CSV (corrupted)", "embedding manifest (corrupted)", "sau khi log du count"),
    HandoffEdge("clean CSV (corrupted)", "clean CSV (repaired)", "sau khi repair tu raw"),
    HandoffEdge("clean JSON (repaired)", "embedding manifest (repaired)", "sau khi repaired schema re-validated"),
    HandoffEdge("baseline metrics JSON", "comparison report", "sau khi co repaired metrics"),
)


def artifacts_by_owner(owner: str) -> list[ArtifactOwner]:
    return [a for a in ARTIFACTS if a.owner == owner]


def handoff_summary() -> dict[str, list[str]]:
    """Tom tat ngan gon cho tung owner: artifact ho phu trach."""
    summary: dict[str, list[str]] = {key: [] for key in MEMBERS}
    for a in ARTIFACTS:
        summary[a.owner].append(f"{a.name} -> {a.path}")
    return summary


def render_pipeline_diagram() -> str:
    """ASCII diagram cua luong raw -> clean -> index -> evaluate -> report.

    Dung de in ra terminal hoac chen vao CHECKPOINT log.
    """
    lines = [
        "================================================================",
        "   DAY 10 - DATA PIPELINE HANDOFF DIAGRAM (Lead: Phong)",
        "================================================================",
        "",
        "  [Công] Crossref API",
        "        |",
        "        v",
        "  data/raw/crossref_response.json  (raw snapshot - KHONG sua)",
        "        |",
        "        v",
        "  data/raw/crossref_records.json   (raw records - paper_id stable)",
        "        |",
        "        v",
        "  [Công] Cleaning + text_for_embedding + age_days",
        "        |",
        "        v",
        "  data/clean/papers_clean.{csv,json}        (BASELINE)",
        "        |                                        |",
        "        |                                        +-> [Tuấn] build test_set.json",
        "        |                                        |",
        "        v                                        v",
        "  [Dương] MiniLM + Chroma 'papers-baseline'   [Tuấn] evaluate -> baseline_metrics.json",
        "                                                          |",
        "                                                          v",
        "                                            [Tuấn] quality + freshness -> phase1_report.md",
        "",
        "  ===== CP4 NGHI 15 PHUT =====",
        "",
        "  data/clean/papers_clean_corrupted.{csv,json}  (BASELINE -> CORRUPTED)",
        "        |",
        "        v",
        "  [Dương] Chroma 'papers-corrupted'  (collection rieng, KHONG dung baseline)",
        "        |",
        "        v",
        "  [Tuấn] evaluate -> corrupted_metrics.json",
        "        |",
        "        v",
        "  [Công] Repair: re-run cleaning tu raw records ->",
        "        |",
        "        v",
        "  data/clean/papers_clean_repaired.{csv,json}  (REPAIRED)",
        "        |",
        "        v",
        "  [Dương] Chroma 'papers-repaired' (collection rieng)",
        "        |",
        "        v",
        "  [Tuấn] evaluate -> repaired_metrics.json",
        "        |",
        "        v",
        "  [Tuấn] So sanh baseline vs corrupted vs repaired -> corruption_report.md",
        "",
        "================================================================",
        "  QUY TAC (ap dung moi CP):",
        "  - 3 trang thai co PATH / COLLECTION rieng -> khong ghi de.",
        "  - Test set, ground truth, evaluator, top-k khong doi.",
        "  - Repair = chay lai tu raw, KHONG sua tay answer/metric.",
        "  - Report phai tro toi artifact that; khong commit .env/secret.",
        "  - Moi filter / dedupe / corruption phai de lai count hoac log.",
        "================================================================",
    ]
    return "\n".join(lines)


def print_handoff() -> None:
    """In ra diagram + ownership bang cho ca team (dung cuoi moi CP)."""
    print(render_pipeline_diagram())
    print()
    print("OWNERSHIP:")
    for key, label in MEMBERS.items():
        print(f"  - {key}: {label}")
        for line in handoff_summary().get(key, []):
            print(f"      * {line}")
    print()


__all__ = [
    "MEMBERS",
    "ArtifactOwner",
    "ARTIFACTS",
    "HandoffEdge",
    "HANDOFF_EDGES",
    "artifacts_by_owner",
    "handoff_summary",
    "render_pipeline_diagram",
    "print_handoff",
]
