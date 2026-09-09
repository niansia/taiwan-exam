#!/usr/bin/env python3
"""Inspect source-note conventions in the user-provided 國寫 PDF corpus.

The script is intentionally read-only.  It de-duplicates PDFs by SHA-256,
extracts text with PyMuPDF, and prints one JSON record per unique paper so an
editor can audit source language, source genre, and placement conventions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import pymupdf


SOURCE_MARKER = re.compile(
    r"(?:圖文)?(?:改寫|節錄|摘錄|摘|取材|引|翻譯)自|資料來源|資料改寫自|來源[：:]"
)


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def source_snippets(text: str, radius: int = 170) -> list[str]:
    normalized = compact(text)
    snippets: list[str] = []
    for match in SOURCE_MARKER.finditer(normalized):
        start = max(0, match.start() - radius)
        end = min(len(normalized), match.end() + radius)
        snippet = normalized[start:end]
        if snippet not in snippets:
            snippets.append(snippet)
    return snippets


def year_hint(path: Path) -> int | None:
    matches = re.findall(r"(?<!\d)(10[0-9]|11[0-6])(?!\d)", str(path))
    return int(matches[0]) if matches else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ocr-low-text", action="store_true")
    parser.add_argument("--max-ocr-pages", type=int, default=6)
    parser.add_argument("--ocr-scale", type=float, default=1.5)
    parser.add_argument("--ocr-crop-top-fraction", type=float, default=0.0)
    args = parser.parse_args()

    candidates: list[Path] = []
    for root in args.roots:
        for path in root.rglob("*.pdf"):
            if re.search(r"國寫|寫作", path.name) or re.search(r"國寫|寫作", str(path.parent)):
                candidates.append(path)

    ocr_engine = None
    if args.ocr_low_text:
        try:
            import numpy as np
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:  # pragma: no cover - environment diagnostic
            print(f"OCR unavailable: {exc}", file=sys.stderr)
            return 2
        ocr_engine = RapidOCR()

    seen: set[str] = set()
    records: list[dict[str, object]] = []
    for path in sorted(candidates):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        try:
            with pymupdf.open(path) as doc:
                page_count = len(doc)
                pages = [page.get_text() for page in doc]
                native_text = "\n".join(pages)
                used_ocr = False
                if ocr_engine is not None and len(compact(native_text)) < 300:
                    pages = []
                    for page in list(doc)[: args.max_ocr_pages]:
                        clip = None
                        if args.ocr_crop_top_fraction:
                            clip = pymupdf.Rect(
                                0,
                                page.rect.height * args.ocr_crop_top_fraction,
                                page.rect.width,
                                page.rect.height,
                            )
                        pix = page.get_pixmap(
                            matrix=pymupdf.Matrix(args.ocr_scale, args.ocr_scale),
                            clip=clip,
                            alpha=False,
                        )
                        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                            pix.height, pix.width, pix.n
                        )
                        result, _ = ocr_engine(image)
                        pages.append("\n".join(line[1] for line in (result or [])))
                    used_ocr = True
        except Exception as exc:  # pragma: no cover - corpus diagnostics
            records.append({"path": str(path), "sha256": digest, "error": str(exc)})
            continue

        text = "\n".join(pages)
        records.append(
            {
                "path": str(path),
                "sha256": digest,
                "year_hint": year_hint(path),
                "pages": page_count,
                "text_chars": len(compact(text)),
                "used_ocr": used_ocr,
                "source_note_count": len(SOURCE_MARKER.findall(text)),
                "material_heading_count": len(re.findall(r"材料[一二三四甲乙丙丁]", text)),
                "source_snippets": source_snippets(text),
            }
        )

    summary = {
        "candidate_pdf_count": len(candidates),
        "unique_pdf_count": len(records),
        "extractable_pdf_count": sum(int(r.get("text_chars", 0)) >= 300 for r in records),
        "low_text_pdf_count": sum(int(r.get("text_chars", 0)) < 300 for r in records),
        "papers_with_source_markers": sum(bool(r.get("source_note_count")) for r in records),
        "papers_with_material_headings": sum(bool(r.get("material_heading_count")) for r in records),
    }
    payload = json.dumps({"summary": summary, "papers": records}, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(args.output)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
