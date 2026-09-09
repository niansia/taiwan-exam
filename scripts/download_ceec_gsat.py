#!/usr/bin/env python3
"""Download and index official CEEC GSAT PDFs from ROC year 100 onward."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://www.ceec.edu.tw/xmfile?xsmsid=0J052424829869345634"
SITE = "https://www.ceec.edu.tw"
USER_AGENT = "TaiwanExamSkill/0.1 (+local educational metadata indexing)"
DOWNLOAD_LABELS = {"試題內容", "選擇題答案", "選擇(填)題答案", "非選擇題評分原則"}


def get_bytes(url: str, timeout: int = 60, attempts: int = 4) -> bytes:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"download failed after {attempts} attempts: {url}: {last_error}")


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def safe_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return value[:180] or "official-file"


def subject_info(title: str, roc_year: int) -> tuple[str, str | None]:
    raw = clean(title.split("－", 1)[-1])
    if "國綜" in raw:
        return "國文", "國綜"
    if "國寫" in raw:
        return "國文", "國寫"
    if "國文" in raw:
        return "國文", None
    if "數學A" in raw or "數學Ａ" in raw:
        return "數學A", None
    if "數學B" in raw or "數學Ｂ" in raw:
        return "數學B", None
    if "數學" in raw:
        return "數學（舊制）" if roc_year <= 110 else "數學（共同範圍模考）", None
    for subject in ("英文", "社會", "自然"):
        if subject in raw:
            return subject, subject if subject == "英文" else None
    raise ValueError(f"無法辨識科目：{title}")


def role_for(label: str) -> str:
    if label == "試題內容":
        return "question"
    if "答案" in label and "評分" not in label:
        return "answer"
    if "評分原則" in label:
        return "scoring_rule"
    if label == "答題卷":
        return "answer_sheet"
    return "other"


def parse_catalog(min_roc_year: int) -> list[dict[str, Any]]:
    first = get_bytes(BASE_URL).decode("utf-8", errors="replace")
    match = re.search(r"共\s*(\d+)\s*頁", first)
    page_count = int(match.group(1)) if match else 19
    rows: list[dict[str, Any]] = []
    for page in range(1, page_count + 1):
        html = first if page == 1 else get_bytes(f"{BASE_URL}&page={page}").decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        for tr in soup.select("div.ListTable table tr"):
            title_cell = tr.select_one("td.title")
            if not title_cell:
                continue
            title = clean(title_cell.get_text(" ", strip=True))
            year_match = re.match(r"(\d{2,3})\s*學年度", title)
            if not year_match:
                continue
            roc_year = int(year_match.group(1))
            if roc_year < min_roc_year:
                continue
            try:
                subject, section = subject_info(title, roc_year)
            except ValueError:
                continue
            for anchor in tr.select("td.download a[href]"):
                label = clean(anchor.get_text(" ", strip=True))
                url = urljoin(SITE, anchor.get("href", ""))
                extension = Path(urlparse(url).path).suffix.lower()
                rows.append({
                    "catalog_page": page,
                    "roc_year": roc_year,
                    "year": roc_year + 1911,
                    "title": title,
                    "subject": subject,
                    "section": section,
                    "label": label,
                    "role": role_for(label),
                    "file_title": clean(anchor.get("title") or ""),
                    "extension": extension,
                    "url": url,
                    "selected": extension == ".pdf" and label in DOWNLOAD_LABELS,
                })
        print(f"已讀取官方清單 {page}/{page_count} 頁", flush=True)
    return sorted({item["url"]: item for item in rows}.values(), key=lambda item: (-item["roc_year"], item["subject"], item["url"]))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pdf_probe(path: Path) -> tuple[int | None, int | None, str, str | None]:
    try:
        reader = PdfReader(path, strict=False)
        pages = len(reader.pages)
        text = "".join((reader.pages[i].extract_text() or "") for i in range(min(2, pages)))
        count = len(text.strip())
        return pages, count, "extractable" if count >= 80 else "image_or_outline", None
    except Exception as exc:
        return None, None, "probe_failed", f"{type(exc).__name__}: {exc}"[:300]


def destination_for(item: dict[str, Any]) -> Path:
    name = item["file_title"] or Path(urlparse(item["url"]).path).name
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    folder = ROOT / "exam_packs" / "學測" / "subjects" / item["subject"] / "歷屆試題" / str(item["roc_year"])
    return folder / safe_filename(name)


def download_one(item: dict[str, Any]) -> dict[str, Any]:
    destination = destination_for(item)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        data = destination.read_bytes()
        download_status = "existing"
    else:
        data = get_bytes(item["url"], timeout=90)
        if not data.startswith(b"%PDF"):
            raise RuntimeError(f"response is not a PDF: {item['url']}")
        part = destination.with_suffix(destination.suffix + ".part")
        part.write_bytes(data)
        part.replace(destination)
        download_status = "downloaded"
    pages, text_chars, text_status, probe_error = pdf_probe(destination)
    return {
        "bundle": f"official-{item['roc_year']}",
        "roc_year": item["roc_year"],
        "year": item["year"],
        "series": "OFFICIAL",
        "publisher": "大學入學考試中心",
        "scope": "正式學測",
        "exam": "學測",
        "curriculum": "108" if item["roc_year"] >= 111 else "99",
        "regime": "111學年度起" if item["roc_year"] >= 111 else "100-110學年度舊制",
        "subject": item["subject"],
        "section": item["section"],
        "role": item["role"],
        "source_kind": "official_past_exam",
        "classification_basis": "official-title",
        "official_title": item["title"],
        "official_label": item["label"],
        "source_url": item["url"],
        "extension": ".pdf",
        "size_bytes": len(data),
        "sha256": sha256(data),
        "pdf_pages": pages,
        "text_chars_first_two_pages": text_chars,
        "text_layer_status": text_status,
        "probe_error": probe_error,
        "download_status": download_status,
        "destination_relative_path": destination.relative_to(ROOT).as_posix(),
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-roc-year", type=int, default=100)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--catalog-only", action="store_true")
    args = parser.parse_args()
    metadata = ROOT / "exam_packs" / "學測" / "metadata"
    catalog = parse_catalog(args.min_roc_year)
    write_jsonl(metadata / "official-download-catalog.jsonl", catalog)
    selected = [item for item in catalog if item["selected"]]
    print(f"民國 {args.min_roc_year} 年起共找到 {len(catalog)} 個連結，選取 {len(selected)} 個 PDF。", flush=True)
    if args.catalog_only:
        return 0

    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(download_one, item): item for item in selected}
        for index, future in enumerate(as_completed(futures), 1):
            item = futures[future]
            try:
                records.append(future.result())
            except Exception as exc:
                failures.append({"url": item["url"], "error": f"{type(exc).__name__}: {exc}"[:500]})
            if index % 10 == 0 or index == len(selected):
                print(f"已處理官方 PDF {index}/{len(selected)}；失敗 {len(failures)}", flush=True)

    records.sort(key=lambda item: (-item["roc_year"], item["subject"], item["section"] or "", item["role"], item["source_url"]))
    write_jsonl(metadata / "official-source-registry.jsonl", records)
    report = {
        "schema_version": 1,
        "source_page": BASE_URL,
        "minimum_roc_year": args.min_roc_year,
        "catalog_links": len(catalog),
        "selected_pdf_count": len(selected),
        "indexed_pdf_count": len(records),
        "download_failures": failures,
        "total_bytes": sum(item["size_bytes"] for item in records),
        "by_roc_year": dict(sorted(Counter(item["roc_year"] for item in records).items())),
        "by_subject": dict(sorted(Counter(item["subject"] for item in records).items())),
        "by_role": dict(sorted(Counter(item["role"] for item in records).items())),
        "by_text_layer": dict(sorted(Counter(item["text_layer_status"] for item in records).items())),
    }
    (metadata / "official-ingestion-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
