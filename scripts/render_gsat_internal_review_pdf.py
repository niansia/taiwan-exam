#!/usr/bin/env python3
"""Print an internal GSAT review proof to PDF with local Chromium."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from render_gsat_internal_review import render
from render_pdf import find_browser
from validate_fixed_page_html import validate_html
from pdf_provenance import publish_pdf
from safe_rendering import browser_flags, prepare_html


def print_proof_html(html: str, output: Path, browser: Path | None = None, *,
                     fixed_pages: bool = True, provenance: bool = True) -> None:
    """Print static proof markup; this helper does not certify exam acceptance."""
    executable = find_browser(browser)
    with tempfile.TemporaryDirectory(prefix="gsat-internal-review-") as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "paper.html"
        pdf_path = tmp_path / "paper.pdf"
        html_path.write_text(html, encoding="utf-8")
        if fixed_pages:
            layout_report = validate_html(html_path, executable)
            if layout_report["status"] != "pass":
                failures = [
                    f"page {page['page']}: vertical={page['overflowPx']}px, horizontal={page['horizontalOverflowPx']}px, clipped={page['clipped']}"
                    for page in layout_report["pages"] if page["status"] != "pass"
                ]
                raise RuntimeError("fixed-page layout check failed: " + "; ".join(failures))
        html_path.write_text(prepare_html(html), encoding="utf-8")
        completed = subprocess.run(
            [str(executable), *browser_flags(tmp_path), "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", html_path.as_uri()],
            capture_output=True, text=True, errors="replace", timeout=120,
        )
        if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
            raise RuntimeError(completed.stderr or completed.stdout or "PDF output missing")
        if not pdf_path.read_bytes().startswith(b"%PDF"):
            raise RuntimeError("Browser output is not a PDF")
        output.parent.mkdir(parents=True, exist_ok=True)
        publish_pdf(pdf_path, output, provenance=provenance)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--answers-only", action="store_true")
    parser.add_argument("--include-answers", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--browser", type=Path)
    parser.add_argument("--no-provenance", action="store_true", help="不加入非可見文件識別資訊")
    args = parser.parse_args(argv)
    try:
        exam = json.loads(args.input.read_text(encoding="utf-8-sig"))
        if args.answers_only and args.include_answers:
            raise ValueError("--answers-only 與 --include-answers 不可同時使用")
        html = render(exam, answers_only=args.answers_only, include_answers=args.include_answers,
                      base=args.input.resolve().parent, run_contract=args.contract)
        meta = exam.get("metadata") or {}
        fixed_answers = (meta.get("paper_subject") or meta.get("subject")) in {"數學A", "數學B", "社會"} and int(meta.get("layout_contract_version") or 0) >= 4
        print_proof_html(html, args.output, args.browser, fixed_pages=not args.answers_only or fixed_answers,
                         provenance=not args.no_provenance)
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    print(f"已輸出內部校樣 PDF：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
