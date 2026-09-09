#!/usr/bin/env python3
"""Compare a fixed-page candidate with the verified official page profile.

This is a rejection gate for unexplained lower-page voids.  It deliberately
uses the matching official page number instead of one global threshold because
large evidence graphics, mixed-section continuations, and the final writing
page have different legitimate densities.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
SUBJECT_CAPS = {"英文": 0.82, "社會": 0.80}


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
    if len(candidate_doc) != len(reference_doc):
        errors.append({
            "code": "page_count_mismatch",
            "candidate": len(candidate_doc),
            "reference": len(reference_doc),
        })
    page_count = min(len(candidate_doc), len(reference_doc))
    rows: list[dict[str, Any]] = []
    cap = SUBJECT_CAPS[subject]
    # Page 1 is the cover.  Compare all numbered pages, including the final
    # page, because the matching official role already allows its intentional
    # white space.
    for index in range(1, page_count):
        candidate_metric = analyzer.page_metrics(candidate_doc[index], index + 1)
        reference_metric = analyzer.page_metrics(reference_doc[index], index + 1)
        reference_ratio = float(reference_metric["used_bottom_ratio"])
        candidate_ratio = float(candidate_metric["used_bottom_ratio"])
        floor = max(0.0, min(cap, reference_ratio - tolerance))
        row = {
            "page": index + 1,
            "candidate_used_bottom_ratio": round(candidate_ratio, 3),
            "reference_used_bottom_ratio": round(reference_ratio, 3),
            "minimum": round(floor, 3),
            "status": "pass" if candidate_ratio >= floor else "fail",
        }
        rows.append(row)
        if row["status"] == "fail":
            errors.append({"code": "unexplained_lower_page_void", **row})
    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "subject": subject,
        "candidate": str(candidate),
        "reference": str(reference),
        "comparison": "matching official page role",
        "tolerance": tolerance,
        "operational_cap": cap,
        "pages": rows,
        "errors": errors,
        "note": "Passing this metric does not replace full-page raster inspection at readable scale.",
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
