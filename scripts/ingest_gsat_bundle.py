#!/usr/bin/env python3
"""Audit and safely organize downloaded GSAT mock-exam bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "exam_packs" / "學測"
GUIDANCE_NAMES = {"放資料到這裡.md", "放詳解格式到這裡.md", "放格式範例到這裡.md"}
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".doc", ".xls", ".htm", ".html"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize(text: str) -> str:
    return text.replace("Ａ", "A").replace("Ｂ", "B").replace("（", "(").replace("）", ")")


def classify_subject(relative: Path) -> tuple[str, str | None, str]:
    text = normalize(relative.as_posix())
    filename = normalize(relative.name)
    if re.search(r"五標|級距|級分|統計|平均分數|分數對應", filename):
        return "shared", None, "score-statistics"
    if re.search(r"更正", filename) and not re.search(r"國文|國綜|國寫|英文|英語|英聽|數學|數A|數B|社會|自然", text):
        return "shared", None, "cross-subject-correction"
    if re.search(r"國寫|國語文寫作|(?<!英文)寫作", text) or re.search(r"(?:^|[_-])(?:題目|解析)?國作(?:[_.-]|$)", filename):
        return "國文", "國寫", "path-token"
    if "國綜" in text:
        return "國文", "國綜", "path-token"
    if "國文" in text:
        return "國文", "國綜", "path-token"
    if re.search(r"英文|英語|英聽", text) or re.search(r"(?:^|[_-])(?:題目|解析)?英(?:[_.-]|$)", filename):
        section = "聽力" if "英聽" in text else "英文"
        return "英文", section, "path-token"
    if "自然" in text or re.search(r"(?:^|[_-])(?:題目|解析)?自(?:[_.-]|$)", filename):
        return "自然", None, "path-token"
    if "社會" in text or re.search(r"(?:^|[_-])(?:題目|解析)?社(?:[_.-]|$)", filename):
        return "社會", None, "path-token"
    if re.search(r"數A[.\u00b7・/]?B|數學A[.\u00b7・/]?B", text, re.IGNORECASE):
        return "shared", None, "combined-math-a-b"
    if re.search(r"數學\s*A|數A", text):
        return "數學A", None, "path-token"
    if re.search(r"數學\s*B|數B", text):
        return "數學B", None, "path-token"
    if "數學" in text or re.search(r"(?:^|[_-])(?:題目|解析)?數(?:[_.-]|$)", filename):
        return "數學（共同範圍模考）", None, "unlabeled-current-math"
    if re.search(r"(?:^|[_-])(?:題目|解析)?國(?:[_.-]|$)", filename):
        return "國文", "國綜", "path-token"
    if re.search(r"參考解答暨詳解|詳解", filename):
        return "shared", None, "combined-multi-subject-solution"
    return "shared", None, "unresolved-shared"


def classify_role(relative: Path) -> str:
    text = normalize(relative.as_posix())
    name = normalize(relative.name)
    if re.search(r"五標|級距|級分|統計|平均分數|分數對應", name):
        return "score_statistics"
    if "更正" in name or "更新答案" in name:
        return "correction"
    has_question = bool(re.search(r"題目|試題|(?:^|[_-])Q(?:[_.-]|$)", name, re.IGNORECASE))
    has_solution = bool(re.search(r"解析|詳解|解答|答案|(?:^|[_-])A(?:[_.-]|$)", text, re.IGNORECASE))
    if re.search(r"含詳解|含解答|附答|試題[-_ ]*解析|參考解答暨詳解|考科暨答案", text) or (has_question and has_solution):
        return "question_and_solution"
    if has_question:
        return "question"
    if has_solution:
        return "solution"
    if re.search(r"國文|國綜|國寫|寫作|英文|英語|英聽|數學|數A|數B|社會|自然|(?:^|[_-])(?:國|英|數|社|自)(?:[_.-]|$)", name):
        return "question"
    return "unspecified_exam_material"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def bundle_metadata(name: str) -> dict[str, Any]:
    normalized = normalize(name)
    match = re.search(r"(?<!\d)(?P<roc>\d{3})\s*[-_]?\s*(?P<series>[A-Z]\d+)", normalized, re.IGNORECASE)
    old_match = re.search(r"(?<!\d)(?P<roc>\d{3})\s*學?年度?.*?(?:試題|模考|[上下])\s*0?(?P<number>[1-9])(?:\D|$)", normalized)
    roc_year = int(match.group("roc")) if match else int(old_match.group("roc")) if old_match else None
    series = match.group("series").upper() if match else None
    if series is None and old_match:
        region_code = (
            "B" if re.search(r"北模|台北區|北市|新北基", normalized)
            else "C" if "中模" in normalized or "中區" in normalized
            else "S" if "南模" in normalized
            else "N" if re.search(r"全國|全模", normalized)
            else "M"
        )
        series = f"{region_code}{old_match.group('number')}"
    publisher_match = re.search(r"\(([^)]+)\)", normalized)
    publisher = publisher_match.group(1) if publisher_match else None
    if publisher:
        publisher = re.sub(r"(?:.+[_ ]+)?(南一|翰林|銓達|文昌)版?$", r"\1", publisher)
    scope = (
        "北模" if re.search(r"北模|台北區|北市|新北基", normalized)
        else "中模" if "中模" in normalized or "中區" in normalized
        else "南模" if "南模" in normalized
        else "全模" if re.search(r"全國|全模", normalized)
        else None
    )
    return {
        "bundle": name,
        "roc_year": roc_year,
        "year": roc_year + 1911 if roc_year is not None else None,
        "series": series,
        "publisher": publisher,
        "scope": scope,
    }


def resolve_bundle_metadata(
    relative: Path,
    existing: list[dict[str, Any]],
    explicit_bundle: str | None,
    explicit_publisher: str | None,
    explicit_scope: str | None,
) -> dict[str, Any]:
    if explicit_bundle:
        candidate = bundle_metadata(explicit_bundle)
    else:
        top = bundle_metadata(relative.parts[0])
        candidate = top if top["roc_year"] is not None else bundle_metadata(relative.as_posix())
    roc_year = candidate["roc_year"]
    series = candidate["series"]
    matches = [
        row for row in existing
        if row.get("roc_year") == roc_year and str(row.get("series") or "").upper() == str(series or "").upper()
    ]
    if candidate.get("publisher"):
        publisher_matches = [row for row in matches if row.get("publisher") == candidate["publisher"]]
        matches = publisher_matches
    if candidate.get("scope"):
        scope_matches = [row for row in matches if row.get("scope") == candidate["scope"]]
        if scope_matches:
            matches = scope_matches
    known_bundles = {str(row.get("bundle")) for row in matches if row.get("bundle")}
    if not explicit_bundle and len(known_bundles) == 1:
        candidate = bundle_metadata(next(iter(known_bundles)))
    if candidate["roc_year"] is None or candidate["series"] is None:
        raise ValueError(f"無法從路徑辨識學年度與模考代碼：{relative.as_posix()}")
    if not candidate.get("publisher"):
        publishers = {row.get("publisher") for row in matches if row.get("publisher")}
        candidate["publisher"] = next(iter(publishers)) if len(publishers) == 1 else None
    if not candidate.get("scope"):
        scopes = {row.get("scope") for row in matches if row.get("scope")}
        candidate["scope"] = next(iter(scopes)) if len(scopes) == 1 else None
    if explicit_publisher:
        candidate["publisher"] = explicit_publisher
    if explicit_scope:
        candidate["scope"] = explicit_scope
    if not explicit_bundle and len(known_bundles) != 1:
        suffix = f" {candidate['scope']}" if candidate.get("scope") else ""
        publisher = f" ({candidate['publisher']})" if candidate.get("publisher") else ""
        candidate["bundle"] = f"{candidate['roc_year']}-{candidate['series']}{suffix}{publisher}"
    return candidate


def pdf_probe(path: Path) -> tuple[int | None, int | None, str | None]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, None, "pypdf-unavailable"
    try:
        reader = PdfReader(str(path), strict=False)
        chars = 0
        for page in reader.pages[:2]:
            chars += len(page.extract_text() or "")
        return len(reader.pages), chars, None
    except Exception as exc:  # corrupted/encrypted PDFs remain indexed for manual review
        return None, None, f"{type(exc).__name__}: {exc}"


def destination_for(entry: dict[str, Any], source_root: Path) -> Path:
    relative = Path(entry["original_relative_path"])
    top = relative.parts[0]
    top_subject, _, _ = classify_subject(Path(top))
    top_is_bundle = bundle_metadata(top)["roc_year"] is not None
    strip_top = top_is_bundle or top_subject != "shared"
    remainder = Path(*relative.parts[1:]) if strip_top and len(relative.parts) > 1 else Path(relative.name)
    bundle = str(entry["bundle"])
    if entry["subject"] == "shared":
        return PACK / "shared-data" / "模擬考" / bundle / remainder
    return PACK / "subjects" / entry["subject"] / "模擬考" / bundle / remainder


def audit(
    source_root: Path,
    probe_pdfs: bool,
    existing: list[dict[str, Any]],
    explicit_bundle: str | None = None,
    explicit_publisher: str | None = None,
    explicit_scope: str | None = None,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    existing_by_hash = {
        str(row.get("sha256")): row for row in existing if row.get("sha256")
    }
    occupied = {
        str(row.get("destination_relative_path")): str(row.get("sha256"))
        for row in existing
        if row.get("destination_relative_path") and row.get("sha256")
    }
    for path in sorted(p for p in source_root.rglob("*") if p.is_file()):
        relative = path.relative_to(source_root)
        suffix = path.suffix.lower()
        subject, section, classification_basis = classify_subject(relative)
        bundle = resolve_bundle_metadata(
            relative, existing, explicit_bundle, explicit_publisher, explicit_scope
        )
        pages = text_chars = probe_error = None
        if probe_pdfs and suffix == ".pdf":
            pages, text_chars, probe_error = pdf_probe(path)
        entry: dict[str, Any] = {
            **bundle,
            "exam": "學測",
            "curriculum": "108" if (bundle["roc_year"] or 0) >= 111 or subject in {"數學A", "數學B"} else "historical-pre-111",
            "evidence_role": "current-form-primary" if (bundle["roc_year"] or 0) >= 111 or subject in {"數學A", "數學B"} else "historical-content-only",
            "subject": subject,
            "section": section,
            "role": classify_role(relative),
            "classification_basis": classification_basis,
            "original_relative_path": relative.as_posix(),
            "extension": suffix,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "pdf_pages": pages,
            "text_chars_first_two_pages": text_chars,
            "text_layer_status": (
                "not_pdf" if suffix != ".pdf" else "probe_failed" if probe_error else "extractable" if (text_chars or 0) >= 80 else "image_or_outline"
            ),
            "probe_error": probe_error,
        }
        prior = existing_by_hash.get(entry["sha256"])
        if prior and not probe_pdfs:
            for field in ("pdf_pages", "text_chars_first_two_pages", "text_layer_status", "probe_error"):
                if field in prior:
                    entry[field] = prior[field]
        destination = (
            Path(str(prior["destination_relative_path"]))
            if prior and prior.get("destination_relative_path")
            else destination_for(entry, source_root).relative_to(ROOT)
        )
        destination_key = destination.as_posix()
        if destination_key in occupied and occupied[destination_key] != entry["sha256"]:
            destination = destination.with_name(f"{destination.stem}__{entry['sha256'][:10]}{destination.suffix}")
            destination_key = destination.as_posix()
        if destination_key in occupied and occupied[destination_key] != entry["sha256"]:
            raise FileExistsError(f"無法為同名異檔建立唯一目的地：{destination_key}")
        entry["destination_relative_path"] = destination_key
        occupied[destination_key] = entry["sha256"]
        entries.append(entry)
    return entries


def summarize(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(entries),
        "total_bytes": sum(entry["size_bytes"] for entry in entries),
        "by_subject": dict(sorted(Counter(entry["subject"] for entry in entries).items())),
        "by_role": dict(sorted(Counter(entry["role"] for entry in entries).items())),
        "by_year": dict(sorted(Counter(str(entry["year"]) for entry in entries).items())),
        "by_publisher": dict(sorted(Counter(str(entry["publisher"]) for entry in entries).items())),
        "by_text_layer": dict(sorted(Counter(entry["text_layer_status"] for entry in entries).items())),
    }


def merge_registry(existing: list[dict[str, Any]], entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_hash = {str(entry["sha256"]): entry for entry in existing if entry.get("sha256")}
    by_destination = {
        str(entry["destination_relative_path"]): entry
        for entry in existing if entry.get("destination_relative_path")
    }
    for entry in entries:
        sha256 = str(entry["sha256"])
        destination = str(entry["destination_relative_path"])
        if sha256 in by_hash:
            prior = by_hash[sha256]
            prior_destination = str(prior.get("destination_relative_path") or destination)
            refreshed = {**prior, **entry, "destination_relative_path": prior_destination}
            by_hash[sha256] = refreshed
            by_destination[prior_destination] = refreshed
            continue
        if destination in by_destination and by_destination[destination].get("sha256") != sha256:
            raise FileExistsError(f"來源索引已有不同內容的同名目的地：{destination}")
        by_hash[sha256] = entry
        by_destination[destination] = entry
    return sorted(
        by_hash.values(),
        key=lambda item: (
            item.get("year") or 0,
            str(item.get("bundle") or ""),
            str(item.get("subject") or ""),
            str(item.get("destination_relative_path") or ""),
        ),
    )


def write_reports(entries: list[dict[str, Any]], intake_entries: list[dict[str, Any]]) -> tuple[Path, Path]:
    metadata_dir = PACK / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    registry = metadata_dir / "source-registry.jsonl"
    report = metadata_dir / "ingestion-report.json"
    registry.write_text("".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries), encoding="utf-8")
    payload = summarize(entries)
    payload["latest_intake"] = summarize(intake_entries)
    report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return registry, report


def ingest_files(source_root: Path, entries: list[dict[str, Any]], mode: str, delete_source: bool) -> None:
    resolved_root = source_root.resolve()
    resolved_workspace = ROOT.resolve()
    if mode == "move" and resolved_root.parent != resolved_workspace:
        raise ValueError("搬移來源資料夾時，來源必須是此 repository 根目錄的直接子資料夾。")
    resolved_pack = PACK.resolve()
    for entry in entries:
        source = resolved_root / Path(entry["original_relative_path"])
        destination = (ROOT / Path(entry["destination_relative_path"])).resolve()
        if resolved_pack not in destination.parents:
            raise ValueError(f"目的地超出學測 Exam Pack：{destination}")
        if not source.exists():
            if destination.exists() and sha256_file(destination) == entry["sha256"]:
                continue
            raise FileNotFoundError(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if sha256_file(destination) != entry["sha256"]:
                raise FileExistsError(f"目的地已有不同內容：{destination}")
            if mode == "move":
                source.unlink()
            continue
        if mode == "copy":
            shutil.copy2(str(source), str(destination))
        else:
            shutil.move(str(source), str(destination))
        if destination.stat().st_size != entry["size_bytes"] or sha256_file(destination) != entry["sha256"]:
            raise RuntimeError(f"{mode} 後驗證失敗：{destination}")
    remaining_files = [p for p in resolved_root.rglob("*") if p.is_file()]
    if mode == "move" and remaining_files:
        raise RuntimeError(f"仍有 {len(remaining_files)} 個來源檔未搬移，拒絕刪除來源資料夾。")
    if mode == "move" and delete_source:
        for directory in sorted((p for p in resolved_root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            directory.rmdir()
        resolved_root.rmdir()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="盤點並整理學測模擬考下載資料夾")
    parser.add_argument("source", type=Path)
    parser.add_argument("--probe-pdfs", action="store_true", help="讀取 PDF 頁數與前兩頁文字層狀態")
    parser.add_argument("--execute", action="store_true", help="依分類結果搬入 Exam Pack（會移除來源檔）")
    parser.add_argument("--copy", action="store_true", help="複製到 Exam Pack 並保留來源檔")
    parser.add_argument("--delete-source", action="store_true", help="全部搬移並驗證後刪除空來源資料夾")
    parser.add_argument("--bundle", help="所有檔案共用的正式套卷名稱，例如：115-X1 區域模考 (出版社)")
    parser.add_argument("--publisher", help="出版者覆寫值")
    parser.add_argument("--scope", choices=("北模", "全模"), help="模考範圍覆寫值")
    args = parser.parse_args(argv)
    try:
        source = args.source.resolve()
        if not source.is_dir():
            raise ValueError(f"找不到來源資料夾：{source}")
        if args.execute and args.copy:
            raise ValueError("--execute 與 --copy 不能同時使用。")
        if args.delete_source and not args.execute:
            raise ValueError("--delete-source 只能和 --execute 一起使用。")
        registry_path = PACK / "metadata" / "source-registry.jsonl"
        existing = read_jsonl(registry_path)
        entries = audit(
            source,
            args.probe_pdfs,
            existing,
            explicit_bundle=args.bundle,
            explicit_publisher=args.publisher,
            explicit_scope=args.scope,
        )
        unsupported = [entry for entry in entries if entry["extension"] not in SUPPORTED_EXTENSIONS]
        if unsupported:
            raise ValueError(f"發現 {len(unsupported)} 個未支援副檔名，請先人工檢查。")
        summary = summarize(entries)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if args.execute or args.copy:
            mode = "move" if args.execute else "copy"
            ingest_files(source, entries, mode, args.delete_source)
            merged = merge_registry(existing, entries)
            registry, report = write_reports(merged, entries)
            print(f"來源清單：{registry.relative_to(ROOT)}")
            print(f"盤點報告：{report.relative_to(ROOT)}")
            print(f"全部檔案已{'搬移' if mode == 'move' else '複製'}並通過 SHA-256 驗證。")
            if args.delete_source:
                print("來源資料夾已刪除。")
        else:
            print("目前是 dry-run，未複製、搬移、刪除或改寫來源索引。")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
