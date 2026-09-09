#!/usr/bin/env python3
"""Measure current GSAT 國綜/自然 page geometry and item-surface patterns.

The report contains aggregate measurements only.  It never exports question
wording, option wording, numeric tuples, or source-question identifiers, so it
is safe to use as an authoring reference after the analysis pass is locked.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
ROC_YEARS = tuple(range(111, 116))
ITEM_RE = re.compile(r"(?m)^\s*(\d{1,2})\s*[\.、]\s+")
OPTION_RE = re.compile(r"\([A-E]\)")
SOURCE_CUE_RE = re.compile(r"改寫自|節錄自|資料來源|引自|出自|據.+?(?:報告|資料|研究|網站)")
PROMPT_CUES = {
    "依據／根據": re.compile(r"依據|根據|依圖|依表|由圖|由表"),
    "最適當": re.compile(r"最適當|最合理|最可能"),
    "可推知": re.compile(r"可推知|推論|研判"),
    "證據評估": re.compile(r"支持|證據|限制|無法|不足"),
    "實驗設計": re.compile(r"實驗|控制變因|對照|重複|操作變因|應變變因"),
    "計算／估算": re.compile(r"計算|估計|估算|最接近|約為"),
    "跨文本": re.compile(r"甲、乙|甲乙|二文|兩文|共同|比較"),
}


def quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "p10": None, "p25": None, "median": None, "p75": None, "p90": None, "max": None}
    values = sorted(values)

    def q(p: float) -> float:
        pos = (len(values) - 1) * p
        lo, hi = math.floor(pos), math.ceil(pos)
        if lo == hi:
            return values[lo]
        return values[lo] + (values[hi] - values[lo]) * (pos - lo)

    return {
        "min": round(values[0], 3),
        "p10": round(q(0.10), 3),
        "p25": round(q(0.25), 3),
        "median": round(q(0.50), 3),
        "p75": round(q(0.75), 3),
        "p90": round(q(0.90), 3),
        "max": round(values[-1], 3),
    }


def official_question_files(subject: str) -> list[tuple[int, Path, str]]:
    metadata = ROOT / "exam_packs" / "學測" / "subjects" / subject / "metadata" / "papers.jsonl"
    rows = [json.loads(line) for line in metadata.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    selected: list[tuple[int, Path, str]] = []
    for row in rows:
        if row.get("source_kind") != "official_past_exam":
            continue
        gregorian = int(row.get("year") or 0)
        roc = gregorian - 1911
        if roc not in ROC_YEARS:
            continue
        question_files = [x for x in row.get("source_files") or [] if x.get("role") == "question"]
        if not question_files:
            continue
        # 國文 metadata also contains 國寫.  國綜 is the 12-page question file.
        if subject == "國文" and max(int(x.get("page_count") or 0) for x in question_files) < 10:
            continue
        entry = max(question_files, key=lambda x: int(x.get("page_count") or 0))
        selected.append((roc, ROOT / entry["relative_path"], row["paper_id"]))
    return sorted(selected)


def page_metrics(page: pymupdf.Page, page_number: int) -> dict[str, Any]:
    text = page.get_text("text") or ""
    compact = re.sub(r"\s+", "", text)
    height = float(page.rect.height)
    content_top = 65.0
    # Keep running footers/page numbers out of the density measurement.  The
    # earlier 52 pt cut still admitted the footer rule in Chromium output and
    # falsely made a nearly empty page look 100% full.
    content_bottom = height - 78.0
    blocks = []
    for block in page.get_text("blocks"):
        x0, y0, x1, y1, block_text = block[:5]
        block_compact = re.sub(r"\s+", "", str(block_text))
        if y1 <= content_top or y0 >= content_bottom:
            continue
        if not block_compact:
            continue
        # Fixed running furniture is short, small and repeated at the page
        # edges.  It is not question content and must never satisfy density.
        if y0 > height - 115.0 and len(block_compact) < 70:
            continue
        blocks.append((max(content_top, y0), min(content_bottom, y1)))
    # Purposeful response lines and figures occupy the printable frame even
    # when they carry no PDF text.  Count their geometry, while retaining the
    # same header/footer clipping window so a repeated page rule cannot make a
    # blank page appear full.
    drawings = page.get_drawings()
    for drawing in drawings:
        rect = drawing.get("rect")
        if rect is None or rect.y1 <= content_top or rect.y0 >= content_bottom:
            continue
        fill = drawing.get("fill")
        stroke = drawing.get("color")
        # Chromium paints white page/background rectangles into the PDF.  They
        # are not visible content and must never satisfy the density gate.
        if stroke is None and isinstance(fill, tuple) and fill and min(fill) >= 0.98:
            continue
        blocks.append((max(content_top, float(rect.y0)), min(content_bottom, float(rect.y1))))
    images = page.get_images(full=True)
    for image in images:
        try:
            rects = page.get_image_rects(image[0])
        except Exception:
            rects = []
        for rect in rects:
            if rect.y1 <= content_top or rect.y0 >= content_bottom:
                continue
            blocks.append((max(content_top, float(rect.y0)), min(content_bottom, float(rect.y1))))
    used_bottom = max((b[1] for b in blocks), default=content_top)
    used_top = min((b[0] for b in blocks), default=content_top)
    used_ratio = max(0.0, min(1.0, (used_bottom - content_top) / (content_bottom - content_top)))
    occupied_span_ratio = max(0.0, min(1.0, (used_bottom - used_top) / (content_bottom - content_top)))
    item_numbers = [int(x) for x in ITEM_RE.findall(text)]
    item_starts = list(ITEM_RE.finditer(text))
    item_lengths: list[int] = []
    for index, match in enumerate(item_starts):
        end = item_starts[index + 1].start() if index + 1 < len(item_starts) else len(text)
        item_lengths.append(len(re.sub(r"\s+", "", text[match.start():end])))
    return {
        "page": page_number,
        "compact_chars": len(compact),
        "item_start_count": len(item_numbers),
        "item_lengths": item_lengths,
        "option_marker_count": len(OPTION_RE.findall(text)),
        "source_cue_count": len(SOURCE_CUE_RE.findall(text)),
        "used_bottom_ratio": round(used_ratio, 3),
        "occupied_span_ratio": round(occupied_span_ratio, 3),
        "vector_drawing_count": len(drawings),
        "embedded_image_count": len(images),
        "prompt_cue_counts": {name: len(pattern.findall(text)) for name, pattern in PROMPT_CUES.items()},
    }


def paper_metrics(roc: int, path: Path) -> dict[str, Any]:
    doc = pymupdf.open(path)
    pages = [page_metrics(page, i + 1) for i, page in enumerate(doc)]
    # The first PDF page is the first numbered content page in official files.
    return {
        "roc_year": roc,
        "page_count": len(doc),
        "pages": pages,
        "aggregate": {
            "compact_chars": sum(p["compact_chars"] for p in pages),
            "item_starts": sum(p["item_start_count"] for p in pages),
            "option_markers": sum(p["option_marker_count"] for p in pages),
            "source_cues": sum(p["source_cue_count"] for p in pages),
            "pages_with_visual_signal": sum(bool(p["vector_drawing_count"] or p["embedded_image_count"]) for p in pages),
            "pages_below_60pct_used": sum(p["used_bottom_ratio"] < 0.60 for p in pages),
        },
    }


def subject_report(subject: str) -> dict[str, Any]:
    files = official_question_files(subject)
    papers = [paper_metrics(roc, path) for roc, path, _ in files]
    all_pages = [page for paper in papers for page in paper["pages"]]
    # Official files include their cover as PDF page 1.  Geometry envelopes for
    # question pages must exclude it; otherwise the cover masks under-filled
    # interior pages in a candidate.
    content_pages = [page for paper in papers for page in paper["pages"][1:]]
    non_terminal_pages = [page for paper in papers for page in paper["pages"][1:-1]]
    item_lengths = [length for page in content_pages for length in page["item_lengths"] if length > 0]
    cue_totals = Counter()
    for page in all_pages:
        cue_totals.update(page["prompt_cue_counts"])
    return {
        "subject": "國綜" if subject == "國文" else subject,
        "corpus": "official GSAT ROC 111-115 question papers",
        "paper_count": len(papers),
        "page_count": len(all_pages),
        "papers": papers,
        "page_compact_chars": quantiles([float(p["compact_chars"]) for p in content_pages]),
        "page_used_bottom_ratio": quantiles([float(p["used_bottom_ratio"]) for p in content_pages]),
        "non_terminal_page_used_bottom_ratio": quantiles([float(p["used_bottom_ratio"]) for p in non_terminal_pages]),
        "item_surface_chars": quantiles([float(x) for x in item_lengths]),
        "item_starts_per_page": quantiles([float(p["item_start_count"]) for p in content_pages]),
        "pages_with_visual_signal_ratio": round(sum(bool(p["vector_drawing_count"] or p["embedded_image_count"]) for p in content_pages) / max(1, len(content_pages)), 3),
        "prompt_cue_totals": dict(cue_totals),
        "method_limits": [
            "PDF text-layer segmentation is heuristic and must be paired with rendered-page review.",
            "Vector drawings include page rules and therefore indicate visual signal, not semantic figure type.",
            "The report exports aggregate geometry only; it is not a source-text substitute.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Current GSAT 國綜 and 自然 Form Envelope",
        "",
        "This file is generated from the official ROC 111–115 question PDFs. It contains aggregate measurements only and is safe for the writing pass.",
        "",
        "## Release-blocking implications",
        "",
        "- A page whose body ends unusually early is not acceptable merely because the PDF has the official page count. Compare every non-terminal page against the subject envelope below and inspect it visually.",
        "- New materials must be traceable to a frozen source record. Originality means a new selection, evidence combination, representation, and question mechanism; it does not authorize unattributed model-authored reading passages.",
        "- A source title or distinctive phrase must be screened against the full local official/mock corpus before selection. A source previously used in a supplied paper is ineligible unless the new excerpt and operation are independently approved.",
        "- Student-facing wording must not contain `自擬`, `本卷自擬`, or a fabricated-source label. Derived values require an audit-only transformation record tied to published input data.",
        "",
    ]
    for subject in report["subjects"]:
        lines.extend([
            f"## {subject['subject']}",
            "",
            f"- Corpus: {subject['paper_count']} papers / {subject['page_count']} pages.",
            f"- Compact characters per page: `{subject['page_compact_chars']}`.",
            f"- Used-bottom ratio, all pages: `{subject['page_used_bottom_ratio']}`.",
            f"- Used-bottom ratio, excluding each paper's final page: `{subject['non_terminal_page_used_bottom_ratio']}`.",
            f"- Heuristic item surface length: `{subject['item_surface_chars']}`.",
            f"- Item starts per page: `{subject['item_starts_per_page']}`.",
            f"- Pages with a visual signal: `{subject['pages_with_visual_signal_ratio']}`.",
            f"- Prompt cue totals: `{subject['prompt_cue_totals']}`.",
            "",
            "Per-year density checks:",
            "",
        ])
        for paper in subject["papers"]:
            a = paper["aggregate"]
            lines.append(
                f"- ROC {paper['roc_year']}: {paper['page_count']} pages; {a['compact_chars']} compact characters; "
                f"{a['item_starts']} item starts; {a['pages_below_60pct_used']} pages below 60% used; "
                f"{a['pages_with_visual_signal']} pages with visual signal."
            )
        lines.append("")
    lines.extend([
        "## How to use this envelope",
        "",
        "During drafting, use only these aggregates plus the subject blueprint and source registry. During QA, render the candidate, measure it with the companion density validator, then inspect every page. Density is a rejection signal, not permission to cram or shrink type.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, default=ROOT / "output" / "analysis" / "current-chinese-natural-form.json")
    parser.add_argument("--markdown", type=Path, default=ROOT / "references" / "current-gsat-chinese-natural-form.md")
    args = parser.parse_args()
    report = {
        "schema_version": 1,
        "years": list(ROC_YEARS),
        "subjects": [subject_report("國文"), subject_report("自然")],
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "json": str(args.json), "markdown": str(args.markdown)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
