#!/usr/bin/env python3
"""Download and index official CEEC GSAT statistics from ROC year 100 onward.

The script keeps the original spreadsheets unchanged.  It selects the tables
needed for item- and paper-level difficulty calibration and writes a small
JSONL registry beside them so later parsers can prove where every value came
from.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
INDEX_URL = "https://www.ceec.edu.tw/xmdoc?xsmsid=0J018604485538810196"
SITE = "https://www.ceec.edu.tw"
USER_AGENT = "TaiwanExamSkill/0.2 (+local educational calibration indexing)"


def get_bytes(url: str, timeout: int = 60, attempts: int = 4) -> bytes:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - network failure path
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"download failed after {attempts} attempts: {url}: {last_error}")


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def safe_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return value[:180] or "official-statistics"


def table_kind(label: str) -> str | None:
    normalized = clean(label)
    if ("答對率" in normalized or "通過率" in normalized) and (
        "鑑別度" in normalized or "鑑別指數" in normalized
    ):
        return "item_metrics_distribution" if "分布圖" in normalized else "item_metrics_table"
    if "選項分析" in normalized:
        return "option_analysis"
    if "原始分數與級分" in normalized or "原得總分與級分" in normalized:
        return "raw_score_grade_conversion"
    if "成績標準一覽表" in normalized:
        return "score_standards"
    if "分數人數統計表" in normalized:
        return "constructed_response_score_distribution"
    return None


def parse_index(min_roc_year: int, max_roc_year: int) -> list[dict[str, Any]]:
    first = get_bytes(INDEX_URL).decode("utf-8", errors="replace")
    page_match = re.search(r"共\s*(\d+)\s*頁", first)
    page_count = int(page_match.group(1)) if page_match else 3
    years: dict[int, str] = {}
    for page in range(1, page_count + 1):
        html = first if page == 1 else get_bytes(f"{INDEX_URL}&page={page}").decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.select("a[href]"):
            label = clean(anchor.get_text(" ", strip=True))
            match = re.search(r"(\d{2,3})\s*學年度學科能力測驗統計", label)
            if not match:
                continue
            roc_year = int(match.group(1))
            if min_roc_year <= roc_year <= max_roc_year:
                years[roc_year] = urljoin(SITE, anchor.get("href", ""))
        print(f"已讀取統計索引 {page}/{page_count} 頁", flush=True)

    rows: list[dict[str, Any]] = []
    for index, (roc_year, page_url) in enumerate(sorted(years.items()), 1):
        html = get_bytes(page_url).decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        for anchor in soup.select("a[href]"):
            label = clean(anchor.get_text(" ", strip=True))
            kind = table_kind(label)
            if not kind:
                continue
            url = urljoin(SITE, anchor.get("href", ""))
            extension = Path(urlparse(url).path).suffix.lower()
            if extension not in {".xls", ".xlsx", ".csv"}:
                continue
            rows.append(
                {
                    "roc_year": roc_year,
                    "year": roc_year + 1911,
                    "label": label,
                    "table_kind": kind,
                    "page_url": page_url,
                    "url": url,
                    "extension": extension,
                }
            )
        print(f"已讀取年度統計頁 {index}/{len(years)}（{roc_year}）", flush=True)
    return sorted({item["url"]: item for item in rows}.values(), key=lambda item: (-item["roc_year"], item["table_kind"], item["url"]))


def destination_for(item: dict[str, Any]) -> Path:
    source_name = Path(urlparse(item["url"]).path).name
    filename = safe_filename(source_name or f"{item['roc_year']}-{item['table_kind']}{item['extension']}")
    if not filename.lower().endswith(item["extension"]):
        filename += item["extension"]
    return ROOT / "exam_packs" / "學測" / "shared-data" / "official-statistics" / str(item["roc_year"]) / filename


def download_one(item: dict[str, Any]) -> dict[str, Any]:
    destination = destination_for(item)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        data = destination.read_bytes()
        status = "existing"
    else:
        data = get_bytes(item["url"], timeout=90)
        part = destination.with_suffix(destination.suffix + ".part")
        part.write_bytes(data)
        part.replace(destination)
        status = "downloaded"
    return {
        **item,
        "source_kind": "official_statistics",
        "publisher": "大學入學考試中心",
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
        "download_status": status,
        "destination_relative_path": destination.relative_to(ROOT).as_posix(),
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-roc-year", type=int, default=100)
    parser.add_argument("--max-roc-year", type=int, default=115)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--catalog-only", action="store_true")
    args = parser.parse_args()
    if args.min_roc_year > args.max_roc_year:
        raise SystemExit("--min-roc-year 不可大於 --max-roc-year")

    metadata_root = ROOT / "exam_packs" / "學測" / "metadata"
    catalog = parse_index(args.min_roc_year, args.max_roc_year)
    write_jsonl(metadata_root / "official-statistics-catalog.jsonl", catalog)
    print(f"共找到 {len(catalog)} 個校準用官方統計檔。", flush=True)
    if args.catalog_only:
        return 0

    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(download_one, item): item for item in catalog}
        for index, future in enumerate(as_completed(futures), 1):
            item = futures[future]
            try:
                records.append(future.result())
            except Exception as exc:  # pragma: no cover - network failure path
                failures.append({"url": item["url"], "error": f"{type(exc).__name__}: {exc}"[:500]})
            if index % 10 == 0 or index == len(catalog):
                print(f"已處理統計檔 {index}/{len(catalog)}；失敗 {len(failures)}", flush=True)

    records.sort(key=lambda item: (-item["roc_year"], item["table_kind"], item["url"]))
    write_jsonl(metadata_root / "official-statistics-registry.jsonl", records)
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_index": INDEX_URL,
        "minimum_roc_year": args.min_roc_year,
        "maximum_roc_year": args.max_roc_year,
        "catalog_count": len(catalog),
        "downloaded_or_existing_count": len(records),
        "failures": failures,
        "by_year": dict(sorted(Counter(item["roc_year"] for item in records).items())),
        "by_table_kind": dict(sorted(Counter(item["table_kind"] for item in records).items())),
    }
    (metadata_root / "official-statistics-ingestion-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
