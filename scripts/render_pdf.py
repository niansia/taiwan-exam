#!/usr/bin/env python3
"""Render exam JSON to an A4 PDF through an installed Chromium browser."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from render_exam import render_exam
from pdf_provenance import publish_pdf


WINDOWS_BROWSERS = (
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
)


def find_browser(override: Path | None = None) -> Path:
    if override:
        if override.is_file():
            return override.resolve()
        raise ValueError(f"找不到瀏覽器：{override}")
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge"):
        found = shutil.which(name)
        if found:
            return Path(found)
    for path in WINDOWS_BROWSERS:
        if path.is_file():
            return path
    raise ValueError("找不到 Chrome、Chromium 或 Edge；請先輸出 HTML，再用瀏覽器列印成 A4 PDF。")


def render_pdf(input_path: Path, output_path: Path, browser: Path | None = None, include_answers: bool = True, *, provenance: bool = True) -> None:
    exam = json.loads(input_path.read_text(encoding="utf-8-sig"))
    rendered = render_exam(exam, include_answers=include_answers, asset_base=input_path.parent)
    executable = find_browser(browser)
    with tempfile.TemporaryDirectory(prefix="taiwan-exam-render-") as directory:
        temporary = Path(directory)
        html_path = temporary / "exam.html"
        pdf_path = temporary / "exam.pdf"
        html_path.write_text(rendered, encoding="utf-8")
        command = [
            str(executable),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=90, check=False)
        if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
            details = (completed.stderr or completed.stdout or "瀏覽器未產生 PDF").strip()
            raise RuntimeError(details)
        if not pdf_path.read_bytes().startswith(b"%PDF"):
            raise RuntimeError("瀏覽器輸出不是有效 PDF。")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        publish_pdf(pdf_path, output_path, provenance=provenance)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="將 exam.json 轉成正式 A4 PDF")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--browser", type=Path, help="Chrome、Chromium 或 Edge 執行檔")
    parser.add_argument("--student-only", action="store_true", help="不附答案頁")
    parser.add_argument("--no-provenance", action="store_true", help="不加入非可見文件識別資訊")
    args = parser.parse_args(argv)
    try:
        render_pdf(args.input.resolve(), args.output.resolve(), args.browser, not args.student_only, provenance=not args.no_provenance)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    print(f"已輸出 A4 PDF：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
