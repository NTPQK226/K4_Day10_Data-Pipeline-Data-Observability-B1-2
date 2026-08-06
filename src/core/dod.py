"""Definition of Done (DoD) cho Day 10 Data Pipeline Lab.

File nay thuoc role LEAD (Pipeline Integrator) - Phong.
Muc dich: chot tieu chi "xong" cho moi checkpoint + rule khong trung lap
giua cac role.

Nguon: rubric trong HTML 'phan-cong-day-10-data-pipeline-4h(2).html',
muc CHECKPOINTS[*].pass.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CheckpointDoD:
    cp_id: str                       # Vi du: "CP0"
    minutes: int                     # Thoi luong checkpoint
    pass_criteria: tuple[str, ...]   # Tat ca item phai PASS de chuyen CP
    per_role: dict[str, tuple[str, ...]] = field(default_factory=dict)


# ===== DoD cho tung checkpoint =====
DOD: tuple[CheckpointDoD, ...] = (
    CheckpointDoD(
        cp_id="CP0",
        minutes=30,
        pass_criteria=(
            "Raw response va raw records JSON ton tai.",
            "PaperRecord co stable paper_id (khong phai raw DOI list).",
            "Moi nguoi biet ro artifact minh ban giao (xem src/core/handoff.py).",
            "Python 3.11-3.13 + 'uv sync' OK; .env cua provider da chuan bi.",
            "Pipeline diagram (raw -> clean -> index -> evaluate -> report) da chot.",
        ),
        per_role={
            "phong": (
                "Da chot ownership, branch, DoD theo file nay.",
                "Da chay 'uv sync' thanh cong (khong commit .env).",
                "Da in ra print_handoff() cho team xem.",
            ),
            "cong": (
                "Da doc Crossref payload va PaperRecord.",
                "Da chon field tao stable paper_id (vd: concat doi + year hash, hoac DOI lower).",
                "Da chuan bi parse_crossref_payload + retry/backoff cho 429/503.",
            ),
            "duong": (
                "Da doc LocalEmbeddingIndex, embeddings, agent de biet input/output.",
                "Da chot embedding model (MiniLM-L6-v2), collection naming, metadata toi thieu.",
                "Da chuan bi smoke query/lookup se dung sau khi index.",
            ),
            "tuan": (
                "Da doc testset.py, qa.py, metrics.py de hieu format answer + metric.",
                "Da thiet ke question summary/authors/date/categories tu du lieu that.",
                "Da noi ground_truth_doc_ids lay tu paper_id clean (khong tu bia ID).",
            ),
        },
    ),
    CheckpointDoD(
        cp_id="CP1",
        minutes=35,
        pass_criteria=(
            "Clean CSV/JSON doc duoc; paper_id unique.",
            "text_for_embedding va age_days co mat.",
            "count/ly do record bi loai co the truy vet (log hoac metadata).",
        ),
        per_role={
            "phong": (
                "Da chot clean contract: input, output, ten file, dieu kien dung.",
                "Da review raw count -> clean count; ghi bat thuong thanh blocker co evidence.",
            ),
            "cong": (
                "Da normalize title/summary/authors/categories; parse published date.",
                "Da dedupe theo stable ID; tinh age_days; build text_for_embedding.",
                "Da ghi clean artifacts + log/count ly do filter hoac dedupe.",
            ),
            "duong": (
                "Da vai text_for_embedding that: du title/summary, khong rong.",
                "Da xac nhan dataframe co paper_id, title, content, metadata index can.",
                "Da chuan bi config index tu clean path, chua build collection final.",
            ),
            "tuan": (
                "Da implement check row count, paper_id unique, title/summary missing, duplicate.",
                "Da tao freshness input tu published/age_days (khong dung ngay hien tai gia dinh).",
                "Da ghi quality report dau tien lam evidence baseline.",
            ),
        },
    ),
    CheckpointDoD(
        cp_id="CP2",
        minutes=30,
        pass_criteria=(
            "test_set.json, embedding manifest va collection baseline ton tai.",
            "semantic search, exact lookup va agent deu tra ve ket qua co nguon.",
            "neu smoke test khong tim thay tai lieu -> sua contract index/clean truoc.",
        ),
        per_role={
            "phong": (
                "Da khoa clean schema va dieu phoi handoff clean -> test set/index.",
                "Da kiem tra collection/path baseline dat rieng, de tai lap.",
            ),
            "cong": (
                "Da xac minh khong con text_for_embedding rong va paper_id bi trung.",
                "Da review row duoc chon vao test set de dam bao noi dung sach.",
            ),
            "duong": (
                "Da build MiniLM embeddings + Chroma 'papers-baseline' tu clean data.",
                "Da test semantic_search va lookup voi query co the kiem chung.",
                "Da build agent yeu cau tool truoc khi tra loi factual.",
            ),
            "tuan": (
                "Da implement build_test_set voi id, type, question, ground_truth, ground_truth_doc_ids.",
                "Da tao question tu cleaned data; ID deu ton tai trong index.",
                "Da luu test set co dinh va doc thu vai row truoc evaluation.",
            ),
        },
    ),
    CheckpointDoD(
        cp_id="CP3",
        minutes=25,
        pass_criteria=(
            "baseline_metrics.json, answers, quality/freshness va phase1_report.md ton tai.",
            "Team giai thich duoc it nhat mot hit/miss bang artifact.",
            "Baseline chi hoan tat khi artifacts + metrics + report khop nhau.",
        ),
        per_role={
            "phong": (
                "Da implement phase1.py theo pseudo-code (raw -> clean -> index -> test set -> evaluate -> quality -> report).",
                "Da chay baseline entrypoint end-to-end; khong chi nhin terminal bao done.",
            ),
            "cong": (
                "Da xac minh raw response, raw records, lineage sample van doc duoc.",
                "Da so sanh raw/clean count; neu chenh lech phai co ly do ghi trong log.",
            ),
            "duong": (
                "Da xac nhan 'papers-baseline' va embedding manifest khop clean dataset.",
                "Da demo mot semantic search va mot exact lookup cho team.",
            ),
            "tuan": (
                "Da run evaluator tao answers + baseline_metrics.json.",
                "Da giai thich retrieval_hit_rate, token F1 va judge metric hien co.",
                "Da generate phase1_report.md (noi dung that, khong hard-code).",
            ),
        },
    ),
    CheckpointDoD(
        cp_id="CP4",
        minutes=15,
        pass_criteria=(
            "Da nghi du 15 phut (thoi gian nay nam trong tong phien 4h).",
            "Quay lai voi corruption scenario da co raw source, signal ky vong va cach repair.",
        ),
        per_role={
            "phong": ("Da ghi baseline checklist + mot blocker con lai, roi nghi.",),
            "cong":  ("Nghi; sau do dung raw source lam diem khoi phuc.",),
            "duong": ("Nghi; sau do ghi vi du query baseline de doi chieu.",),
            "tuan":  ("Nghi; sau do dung lai test set da khoa + du bao quality/freshness signal se thay doi.",),
        },
    ),
    CheckpointDoD(
        cp_id="CP5",
        minutes=60,
        pass_criteria=(
            "Corruption log, corrupted clean/index/answers/metrics/quality va report co du.",
            "Baseline KHONG bi ghi de (path/collection rieng).",
            "Loi data phai co chu dich, co log va do duoc tac dong.",
        ),
        per_role={
            "phong": (
                "Da implement corruption_flow: corrupt -> rebuild -> evaluate -> quality -> repair -> compare.",
                "Da stop de sua data contract thay vi va JSON ket qua.",
            ),
            "cong": (
                "Da implement corrupt_clean_dataframe: missing / latest drop / noise / old date / duplicate.",
                "Da log record ID, type, parameter, before/after count cho tung corruption.",
                "Da xac nhan corrupted dataset khac baseline dung nhu log mo ta.",
            ),
            "duong": (
                "Da build 'papers-corrupted' rieng tu corrupted clean data.",
                "Da chay lai query baseline de quan sat retrieval doi the nao.",
                "Da kiem tra 'papers-baseline' con doc duoc va khong bi mutate.",
            ),
            "tuan": (
                "Da evaluate corrupted voi test set cu (khong doi test set).",
                "Da so answer va metric voi baseline; tim mot case xau di co evidence.",
                "Da run quality/freshness cho corrupted dataset va luu report rieng.",
            ),
        },
    ),
    CheckpointDoD(
        cp_id="CP6",
        minutes=45,
        pass_criteria=(
            "Repaired artifacts va comparison report co baseline-corrupted-repaired/delta.",
            "Repo khong co secret (.env khong commit, khong hard-code path).",
            "Demo dung artifact that; khong to dep so lieu.",
        ),
        per_role={
            "phong": (
                "Da chay checklist cuoi: artifacts du, reports match outputs, no secret.",
                "Da chi cong bo recovery khi so lieu va report chung minh.",
            ),
            "cong": (
                "Da re-run cleaning tu raw tao repaired dataset (khong copy sua tay tu baseline).",
                "Da kiem tra repaired schema, row count, quality signals.",
                "Da demo khac biet clean/corrupted/repaired cho team.",
            ),
            "duong": (
                "Da build 'papers-repaired' rieng va smoke test cung query baseline.",
                "Da kiem tra agent dung tools va retrieval tra ve document repaired.",
                "Da demo ba collection/path tach biet, tai lap duoc.",
            ),
            "tuan": (
                "Da evaluate repaired voi test set cu va tinh delta ba trang thai.",
                "Da generate comparison report tu metrics/quality/freshness that.",
                "Da noi recovery chua hoan toan neu signals hoac metrics con xau.",
            ),
        },
    ),
)


def all_passed(cp_id: str, completed: set[str]) -> bool:
    """Kiem tra cac item PASS da duoc tick het cho 1 checkpoint."""
    dod = next((d for d in DOD if d.cp_id == cp_id), None)
    if dod is None:
        raise ValueError(f"Unknown checkpoint: {cp_id}")
    return set(dod.pass_criteria).issubset(completed)


def render_dod(cp_id: str) -> str:
    """Render DoD cho 1 checkpoint thanh dang text de in ra / chen vao log."""
    dod = next(d for d in DOD if d.cp_id == cp_id)
    lines = [
        f"=== DoD for {dod.cp_id} ({dod.minutes} min) ===",
        "Pass criteria (toan team):",
    ]
    for i, item in enumerate(dod.pass_criteria, start=1):
        lines.append(f"  {i}. {item}")
    if dod.per_role:
        lines.append("")
        lines.append("Per-role:")
        for owner, items in dod.per_role.items():
            lines.append(f"  [{owner}]")
            for item in items:
                lines.append(f"    - {item}")
    return "\n".join(lines)


__all__ = ["CheckpointDoD", "DOD", "all_passed", "render_dod"]
