#!/usr/bin/env python3
"""Reject under-filled or materially under-written GSAT 國綜/自然 papers.

This validator is intentionally conservative: it checks both where each page's
content ends and how much extractable text the complete paper contains against
official ROC 111–115 PDFs.  The second check prevents empty containers or large
spacing from masquerading as substantive content.  It is a rejection gate, not
a substitute for visual review.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
CONTENT_VOLUME_FLOOR = 0.80


def load_analyzer() -> Any:
    path = ROOT / "scripts" / "analyze_current_chinese_natural_form.py"
    spec = importlib.util.spec_from_file_location("current_form_analyzer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load current-form analyzer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def content_volume_metrics(pages: list[dict[str, Any]], reference_papers: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_chars = sum(int(page.get("compact_chars", 0)) for page in pages)
    # When one official year controls the layout, compare with that paper.  If
    # a year was not selected, use the smallest official total so the gate does
    # not demand more prose than every valid recent form.
    reference_chars = min(int(p["aggregate"]["compact_chars"]) for p in reference_papers)
    minimum_chars = int(reference_chars * CONTENT_VOLUME_FLOOR)
    ratio = candidate_chars / reference_chars if reference_chars else 0.0
    return {
        "candidate_compact_chars": candidate_chars,
        "reference_compact_chars": reference_chars,
        "minimum_compact_chars": minimum_chars,
        "content_volume_floor": CONTENT_VOLUME_FLOOR,
        "content_volume_ratio": round(ratio, 3),
        "content_volume_pass": candidate_chars >= minimum_chars,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--subject", required=True, choices=("國綜", "自然"))
    parser.add_argument("--reference", type=Path, default=ROOT / "exam_packs" / "學測" / "shared-data" / "current-chinese-natural-density.json")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--reference-year", type=int, choices=range(111, 116), help="Controlling official ROC year; otherwise use the five-year page-count envelope")
    args = parser.parse_args()

    analyzer = load_analyzer()
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    subject = next(x for x in reference["subjects"] if x["subject"] == args.subject)
    reference_papers = [p for p in subject['papers'] if args.reference_year is None or p['roc_year'] == args.reference_year]
    expected_counts = {p['page_count'] for p in reference_papers}
    # User-facing operational rule: no content page, including the terminal
    # page, may end above 78% of the printable frame.  Official envelopes are
    # retained for comparison, but a low historical outlier must not weaken
    # this project's explicit anti-blank-page gate.
    floor = 0.78

    doc = pymupdf.open(args.pdf)
    pages = [analyzer.page_metrics(page, i + 1) for i, page in enumerate(doc)]
    volume = content_volume_metrics(pages, reference_papers)
    # Candidate PDFs include a cover.  The final question page is checked too;
    # No filler, gratuitous source notes or artificial answer space may be used
    # to reach the floor. Page count is a separate check against short previews.
    interior = pages[1:]
    failures = [
        {
            "page": p["page"],
            "used_bottom_ratio": p["used_bottom_ratio"],
            "compact_chars": p["compact_chars"],
            "minimum": round(floor, 3),
        }
        for p in interior
        if float(p["used_bottom_ratio"]) < floor
    ]
    page_count_pass = len(pages) in expected_counts
    report = {
        "status": "pass" if not failures and volume["content_volume_pass"] else "fail",
        "subject": args.subject,
        "reference": "official GSAT ROC 111-115",
        "candidate_page_count": len(pages),
        "expected_page_counts": sorted(expected_counts),
        "page_count_pass": page_count_pass,
        "page_count_note": "informational only; review candidate pages by functional role when the count differs",
        "content_page_floor": round(floor, 3),
        **volume,
        "failed_pages": failures,
        "note": "Text volume is an anti-padding floor, not a writing target. A pass still requires inspection of every rasterized page at readable scale.",
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
