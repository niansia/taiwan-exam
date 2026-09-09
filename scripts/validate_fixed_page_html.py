#!/usr/bin/env python3
"""Reject fixed-page HTML when content is clipped by its printable frame."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from render_pdf import find_browser
from safe_rendering import browser_flags, prepare_html


REPORT_ID = "codex-fixed-page-layout-report"
REPORT_RE = re.compile(
    rf'<pre[^>]+id=["\']{REPORT_ID}["\'][^>]*>(.*?)</pre>',
    re.IGNORECASE | re.DOTALL,
)

INSTRUMENTATION = rf"""
<script>
(() => {{
  const tolerance = 0.75;
  const describe = (node) => {{
    const q = node.closest('.question');
    const qno = q ? q.querySelector('.qno') : null;
    const classes = Array.from(node.classList || []).join('.');
    return `${{node.tagName.toLowerCase()}}${{classes ? '.' + classes : ''}}${{qno ? '[q=' + qno.textContent.trim() + ']' : ''}}`;
  }};
  const run = () => {{
    const pages = Array.from(document.querySelectorAll('.sheet')).map((sheet, sheetIndex) => {{
      const bounded = [
        sheet,
        ...Array.from(sheet.querySelectorAll('.content,.notice,.cover-fill-example,.mark-example,.section-rule,.options,.fill-format,.figure')),
      ];
      const frames = bounded.map((container) => {{
        const frame = container.getBoundingClientRect();
        const tracked = new Set([
          ...Array.from(container.children),
          ...(container.matches('.content')
            ? Array.from(container.querySelectorAll('.question,.stimulus,.options,.fill-format,.answer-lines,.figure,.figure img,table'))
            : []),
        ]);
        const clipped = Array.from(tracked).flatMap((node) => {{
          const box = node.getBoundingClientRect();
          const overTop = frame.top - box.top;
          const overRight = box.right - frame.right;
          const overBottom = box.bottom - frame.bottom;
          const overLeft = frame.left - box.left;
          if (overTop > tolerance || overRight > tolerance || overBottom > tolerance || overLeft > tolerance) {{
            return [{{
              frame: describe(container),
              element: describe(node),
              overTopPx: Math.max(0, overTop),
              overRightPx: Math.max(0, overRight),
              overBottomPx: Math.max(0, overBottom),
              overLeftPx: Math.max(0, overLeft),
            }}];
          }}
          return [];
        }});
        return {{
          frame: describe(container),
          horizontalOverflowPx: Math.max(0, container.scrollWidth - container.clientWidth),
          overflowPx: Math.max(0, container.scrollHeight - container.clientHeight),
          clipped,
        }};
      }});
      const content = sheet.querySelector('.content');
      let contentUsedRatio = null;
      if (content) {{
        const contentBox = content.getBoundingClientRect();
        const visibleChildren = Array.from(content.children).filter((node) => {{
          const style = getComputedStyle(node);
          const box = node.getBoundingClientRect();
          return style.display !== 'none' && style.visibility !== 'hidden' && box.height > 0.5;
        }});
        const usedBottom = visibleChildren.length
          ? Math.max(...visibleChildren.map((node) => node.getBoundingClientRect().bottom))
          : contentBox.top;
        contentUsedRatio = Math.max(0, Math.min(1, (usedBottom - contentBox.top) / contentBox.height));
      }}
      return {{
        page: sheetIndex + 1,
        horizontalOverflowPx: Math.max(...frames.map((frame) => frame.horizontalOverflowPx)),
        overflowPx: Math.max(...frames.map((frame) => frame.overflowPx)),
        clipped: frames.flatMap((frame) => frame.clipped),
        contentUsedRatio,
        frames,
      }};
    }});
    const pre = document.createElement('pre');
    pre.id = '{REPORT_ID}';
    pre.hidden = true;
    pre.textContent = JSON.stringify({{ pages }});
    document.body.appendChild(pre);
  }};
  // The probe is injected immediately before </body>; all page nodes and
  // intrinsic SVG dimensions are already present. Reading bounding boxes
  // forces a synchronous layout, which also makes --dump-dom deterministic.
  run();
}})();
</script>
"""


def _instrument(source: str) -> str:
    if REPORT_ID in source:
        raise ValueError('Input must not contain the reserved layout report identifier')
    script = INSTRUMENTATION.strip().removeprefix('<script>').removesuffix('</script>')
    return prepare_html(source, measurement_script=script)


def validate_html(path: Path, browser: Path | None = None) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8-sig")
    executable = find_browser(browser)
    with tempfile.TemporaryDirectory(prefix="fixed-page-layout-") as tmp:
        probe = Path(tmp) / "probe.html"
        probe.write_text(_instrument(source), encoding="utf-8")
        completed = subprocess.run(
            [
                str(executable),
                *browser_flags(Path(tmp)),
                "--virtual-time-budget=2000",
                "--dump-dom",
                probe.as_uri(),
            ],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    match = REPORT_RE.search(completed.stdout)
    if not match:
        diagnostic = (completed.stderr or completed.stdout)[-1200:]
        raise RuntimeError(f"browser did not return fixed-page measurements: {diagnostic}")
    payload = json.loads(html_lib.unescape(match.group(1)))
    pages = payload.get("pages") or []
    if not pages:
        raise RuntimeError("no fixed .sheet page frames were found")
    _finalize_pages(pages)
    return {
        "status": "pass" if all(page["status"] == "pass" for page in pages) else "fail",
        "source": str(path),
        "pages": pages,
    }


def _finalize_pages(pages: list[dict[str, Any]]) -> None:
    for page in pages:
        page["status"] = (
            "fail"
            if page.get("overflowPx", 0) > 1
            or page.get("horizontalOverflowPx", 0) > 1
            or page.get("clipped")
            else "pass"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    parser.add_argument("--browser", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = validate_html(args.html, args.browser)
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
