from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
import time
from typing import Any
import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json

CROSSREF_API_URL = "https://api.crossref.org/works"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _strip_xml_tags(text: str) -> str:
    """Loại bỏ các tag XML/HTML (như <jats:p>, <i>, ...) thường có trong abstract Crossref."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(clean)


def _format_date(date_obj: dict[str, Any] | None) -> str:
    """Parse date-parts [[YYYY, MM, DD]] từ Crossref thành format YYYY-MM-DD."""
    if not date_obj or not isinstance(date_obj, dict):
        return ""
    parts = date_obj.get("date-parts", [])
    if parts and isinstance(parts[0], list) and len(parts[0]) > 0:
        year = parts[0][0]
        month = parts[0][1] if len(parts[0]) > 1 else 1
        day = parts[0][2] if len(parts[0]) > 2 else 1
        return f"{year:04d}-{month:02d}-{day:02d}"
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref API payload thành danh sách PaperRecord."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        # 1. Stable paper_id từ DOI
        doi = item.get("DOI", "").strip()
        if not doi:
            continue
        paper_id = doi

        # 2. Title
        title_raw = item.get("title", [""])
        title = title_raw[0] if isinstance(title_raw, list) and title_raw else str(title_raw)
        title = _strip_xml_tags(title)
        if not title:
            continue

        # 3. Summary (Abstract)
        abstract_raw = item.get("abstract", "")
        summary = _strip_xml_tags(abstract_raw)

        # 4. Authors
        authors_raw = item.get("author", [])
        authors: list[str] = []
        for a in authors_raw:
            if isinstance(a, dict):
                given = a.get("given", "").strip()
                family = a.get("family", "").strip()
                name = a.get("name", "").strip()
                full_name = f"{given} {family}".strip() or name
                if full_name:
                    authors.append(full_name)

        # 5. Categories / Subjects
        categories = item.get("subject", [])
        if not isinstance(categories, list):
            categories = [str(categories)] if categories else []
        primary_category = categories[0] if categories else ""

        # 6. Dates (published & updated)
        pub_date = (
            _format_date(item.get("published-print"))
            or _format_date(item.get("published-online"))
            or _format_date(item.get("issued"))
            or _format_date(item.get("created"))
        )
        updated_date = (
            _format_date(item.get("deposited"))
            or _format_date(item.get("indexed"))
            or pub_date
        )

        # 7. URLs & Comment
        abs_url = item.get("URL", f"https://doi.org/{doi}")
        pdf_url = ""
        for link in item.get("link", []):
            if isinstance(link, dict) and link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", "")
                break

        container_titles = item.get("container-title", [])
        comment = container_titles[0] if container_titles else item.get("publisher", "")

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=pub_date,
                updated=updated_date,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Gọi source API với retry/backoff, lưu raw response và parse thành records."""
    if not settings.refresh_source and settings.paths.raw_records_json.exists():
        return load_raw_records(settings.paths.raw_records_json)

    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {
        "User-Agent": "DataObservabilityLab/1.0 (mailto:student@example.com)"
    }

    max_retries = 3
    backoff = 2.0
    payload: dict | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                CROSSREF_API_URL,
                params=params,
                headers=headers,
                timeout=25,
            )
            if response.status_code == 200:
                payload = response.json()
                break
            elif response.status_code in (429, 500, 502, 503, 504):
                time.sleep(backoff * attempt)
            else:
                response.raise_for_status()
        except requests.RequestException:
            if attempt == max_retries:
                raise
            time.sleep(backoff * attempt)

    if not payload:
        raise RuntimeError("Failed to fetch data from Crossref API after retries.")

    # 1. Lưu raw API response
    write_json(settings.paths.raw_api_response, payload)

    # 2. Parse payload
    records = parse_crossref_payload(payload)

    # 3. Lưu raw records đã parse
    write_json(
        settings.paths.raw_records_json,
        [asdict(r) for r in records],
    )

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Đọc JSON snapshot và map thành `PaperRecord`."""
    raw_data = read_json(path)
    return [PaperRecord(**item) for item in raw_data]
