#!/usr/bin/env python3
"""Compare a fixed-page candidate with the verified official page profile.

This is a rejection gate for unexplained lower-page voids and materially short
papers.  It deliberately uses matching official page numbers for page geometry
and also compares per-page and complete-paper extractable text volume.  A page
may legitimately substitute prose for a large official figure, so sufficient
same-role text can explain an earlier bottom edge.  Empty containers or expanded
spacing satisfy neither branch.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
SUBJECT_CAPS = {"國綜": 0.80, "國寫": 0.80, "數學A": 0.78, "數學B": 0.78, "英文": 0.82, "社會": 0.80, "自然": 0.80}
CONTENT_VOLUME_FLOOR = 0.80


def load_analyzer() -> Any:
    path = ROOT / "scripts" / "analyze_current_chinese_natural_form.py"
    spec = importlib.util.spec_from_file_location("current_form_analyzer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load page-density analyzer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(candidate: Path, reference: Path, subject: str, tolerance: float) -> dict[str, Any]:
    analyzer = load_analyzer()
    candidate_doc = pymupdf.open(candidate)
    reference_doc = pymupdf.open(reference)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if len(candidate_doc) != len(reference_doc):
        warnings.append({
            "code": "page_count_differs_review_page_roles",
            "candidate": len(candidate_doc),
            "reference": len(reference_doc),
        })
    page_count = min(len(candidate_doc), len(reference_doc))
    rows: list[dict[str, Any]] = []
    cap = SUBJECT_CAPS[subject]
    candidate_chars = sum(
        int(analyzer.page_metrics(candidate_doc[index], index + 1).get("compact_chars", 0))
        for index in range(1, len(candidate_doc))
    )
    reference_chars = sum(
        int(analyzer.page_metrics(reference_doc[index], index + 1).get("compact_chars", 0))
        for index in range(1, len(reference_doc))
    )
    # Page 1 is the cover.  Compare all numbered pages, including the final
    # page, because the matching official role already allows its intentional
    # white space.
    for index in range(1, page_count):
        candidate_metric = analyzer.page_metrics(candidate_doc[index], index + 1)
        reference_metric = analyzer.page_metrics(reference_doc[index], index + 1)
        reference_ratio = float(reference_metric["used_bottom_ratio"])
        candidate_ratio = float(candidate_metric["used_bottom_ratio"])
        candidate_page_chars = int(candidate_metric.get("compact_chars", 0))
        reference_page_chars = int(reference_metric.get("compact_chars", 0))
        floor = max(0.0, min(cap, reference_ratio - tolerance))
        page_text_floor = int(reference_page_chars * CONTENT_VOLUME_FLOOR)
        geometry_pass = candidate_ratio >= floor
        page_text_pass = candidate_page_chars >= page_text_floor
        row = {
            "page": index + 1,
            "candidate_used_bottom_ratio": round(candidate_ratio, 3),
            "reference_used_bottom_ratio": round(reference_ratio, 3),
            "minimum": round(floor, 3),
            "candidate_compact_chars": candidate_page_chars,
            "reference_compact_chars": reference_page_chars,
            "minimum_compact_chars": page_text_floor,
            "geometry_pass": geometry_pass,
            "page_text_volume_pass": page_text_pass,
            "status": "pass" if geometry_pass or page_text_pass else "fail",
        }
        rows.append(row)
        if row["status"] == "fail":
            errors.append({"code": "unexplained_lower_page_void", **row})
    minimum_chars = int(reference_chars * CONTENT_VOLUME_FLOOR)
    content_volume_ratio = candidate_chars / reference_chars if reference_chars else 0.0
    content_volume_pass = candidate_chars >= minimum_chars
    if not content_volume_pass:
        errors.append({
            "code": "insufficient_substantive_text_volume",
            "candidate_compact_chars": candidate_chars,
            "reference_compact_chars": reference_chars,
            "minimum_compact_chars": minimum_chars,
            "ratio": round(content_volume_ratio, 3),
        })
    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "subject": subject,
        "candidate": str(candidate),
        "reference": str(reference),
        "comparison": "matching official page role",
        "tolerance": tolerance,
        "operational_cap": cap,
        "candidate_compact_chars": candidate_chars,
        "reference_compact_chars": reference_chars,
        "minimum_compact_chars": minimum_chars,
        "content_volume_floor": CONTENT_VOLUME_FLOOR,
        "content_volume_ratio": round(content_volume_ratio, 3),
        "content_volume_pass": content_volume_pass,
        "pages": rows,
        "errors": errors,
        "warnings": warnings,
        "note": "Page count is informational. Text volume is an anti-padding floor, not a writing target. Passing this metric does not replace page-role mapping, typography comparison, or full-page raster inspection at readable scale.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--subject", required=True, choices=tuple(SUBJECT_CAPS))
    parser.add_argument("--tolerance", type=float, default=0.12)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.candidate, args.reference, args.subject, args.tolerance)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
