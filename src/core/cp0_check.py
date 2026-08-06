"""CP0 verification script - Phong (Lead).

Kiem tra nhanh truoc khi chuyen sang CP1. KHONG sua file role khac.
Kiem tra:
  - Python version trong khoang 3.11-3.13 (pyproject yeu cau).
  - File .env ton tai (key that khong bi in ra).
  - Source cua Crossref API dang dung.
  - Settings load duoc khong (paths, provider).
  - So do handoff va DoD CP0 render duoc.

Chay:  uv run python -m src.core.cp0_check
hoac:   python -m src.core.cp0_check
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path


def check_python_version() -> tuple[bool, str]:
    v = sys.version_info
    msg = f"Python {v.major}.{v.minor}.{v.micro}"
    ok = (3, 11) <= (v.major, v.minor) <= (3, 13)
    msg += "  (OK)" if ok else "  (NGOAI KHOANG 3.11-3.13 YEU CAU)"
    return ok, msg


def check_dependencies() -> tuple[bool, str]:
    missing: list[str] = []
    for pkg in ("chromadb", "pandas", "requests", "sentence_transformers", "dotenv"):
        try:
            importlib.import_module(pkg)
        except Exception:
            missing.append(pkg)
    if missing:
        return False, f"Missing: {', '.join(missing)} (chay: uv sync)"
    return True, "All key deps present"


def check_env_file(root: Path) -> tuple[bool, str]:
    env_path = root / ".env"
    workspace_env = root.parent / ".env"
    locations = [p for p in (env_path, workspace_env) if p.exists()]
    if not locations:
        return False, ".env khong tim thay - copy tu .env.example roi dien API key"
    return True, f".env found: {[str(p) for p in locations]}"


def check_settings() -> tuple[bool, str]:
    try:
        from src.core.config import load_settings
    except Exception as exc:
        return False, f"Cannot import src.core.config: {exc}"
    try:
        settings = load_settings()
    except Exception as exc:
        return False, f"load_settings() failed: {exc}"
    lines = [
        f"  provider: {settings.llm_provider}",
        f"  model:    {settings.model_name}",
        f"  source:   {settings.source_api}",
        f"  query:    {settings.source_query!r}",
        f"  filter:   {settings.source_filter}",
        f"  embedding: {settings.embedding_model}",
        f"  collection baseline:   {settings.baseline_collection_name}",
        f"  collection corrupted:  {settings.corrupted_collection_name}",
        f"  collection repaired:   {settings.repaired_collection_name}",
        f"  max_results: {settings.max_results}, top_k: {settings.top_k}",
        f"  freshness_threshold_days: {settings.freshness_threshold_days}",
    ]
    return True, "\n".join(lines)


def check_handoff_renders() -> tuple[bool, str]:
    try:
        from src.core.handoff import handoff_summary  # noqa: F401  (re-exported for smoke)
        from src.core.dod import DOD
    except Exception as exc:
        return False, f"Cannot import handoff/dod: {exc}"
    summary = handoff_summary()
    owners_ok = all(len(items) > 0 for items in summary.values())
    if not owners_ok:
        return False, "Mot owner chua co artifact nao - check src/core/handoff.py"
    cp0 = next((d for d in DOD if d.cp_id == "CP0"), None)
    return (cp0 is not None), f"DoD entries: {len(DOD)}, CP0: {bool(cp0)}"


def main() -> int:
    print("=" * 70)
    print("CP0 verification - Lead: Phong")
    print("=" * 70)
    project_root = Path(__file__).resolve().parents[2]

    failures: list[str] = []

    for name, fn in [
        ("Python version",         check_python_version),
    ]:
        ok, msg = fn()
        print(f"  [PASS] {msg}" if ok else f"  [FAIL] {msg}")
        if not ok:
            failures.append(name)

    for name, fn in [
        ("Dependencies",           lambda: check_dependencies()),
        ("Env file",               lambda: check_env_file(project_root)),
        ("Settings load",          check_settings),
        ("Handoff + DoD render",   check_handoff_renders),
    ]:
        ok, msg = fn()
        print(f"  [PASS] {name}:\n{msg}" if ok else f"  [FAIL] {name}:\n{msg}")
        if not ok:
            failures.append(name)

    print("=" * 70)
    if failures:
        print(f"CP0 chua dat - can fix: {', '.join(failures)}")
        return 1

    # In diagram + DoD cho team xem cuoi CP0
    from src.core.handoff import print_handoff
    print_handoff()
    from src.core.dod import render_dod
    print(render_dod("CP0"))
    print("=" * 70)
    print("CP0 PASS - san sang chuyen CP1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
