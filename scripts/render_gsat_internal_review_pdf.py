#!/usr/bin/env python3
"""Print an internal GSAT review proof to PDF with local Chromium."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from render_gsat_internal_review import render
from render_pdf import find_browser
from validate_fixed_page_html import validate_html
from pdf_provenance import publish_pdf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--answers-only", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--browser", type=Path)
    parser.add_argument("--no-provenance", action="store_true", help="不加入非可見文件識別資訊")
    args = parser.parse_args(argv)
    try:
        exam = json.loads(args.input.read_text(encoding="utf-8-sig"))
        html = render(exam, answers_only=args.answers_only, base=args.input.resolve().parent, run_contract=args.contract)
        browser = find_browser(args.browser)
        with tempfile.TemporaryDirectory(prefix="gsat-internal-review-") as tmp:
            tmp_path = Path(tmp)
            html_path = tmp_path / "paper.html"
            pdf_path = tmp_path / "paper.pdf"
            html_path.write_text(html, encoding="utf-8")
            if not args.answers_only:
                layout_report = validate_html(html_path, browser)
                if layout_report["status"] != "pass":
                    failures = [
                        f"page {page['page']}: vertical={page['overflowPx']}px, horizontal={page['horizontalOverflowPx']}px, clipped={page['clipped']}"
                        for page in layout_report["pages"]
                        if page["status"] != "pass"
                    ]
                    raise RuntimeError("fixed-page layout check failed: " + "; ".join(failures))
            completed = subprocess.run(
                [str(browser), "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
                raise RuntimeError(completed.stderr or completed.stdout or "PDF output missing")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            publish_pdf(pdf_path, args.output, provenance=not args.no_provenance)
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    print(f"已輸出內部校樣 PDF：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
