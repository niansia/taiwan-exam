#!/usr/bin/env python3
"""Rasterize a saved PDF and report mechanical layout risks; never self-approve it.

Text extraction cannot prove a missing symbol was intended, nor can this tool
judge difficulty, novelty, diagrams, or mathematical truth. Every page still
requires visual review against the authored content and the subject profile.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import pymupdf
from validate_math_context import source_note_samples, production_caption_samples


RAW_MATH = re.compile(r"[A-Za-z0-9)]\s*[\^_]\s*[A-Za-z0-9{(]|\[\[")
HARD_FAILURES = {"non-A4-or-rotated", "replacement-or-null-glyph", "text-outside-page",
                 "answer-rail-content-collision", "printed-math-source-note", "answer-rail-format",
                 "printed-math-production-caption"}


def rail_format_samples(page):
    """Catch native numbered circle IDs printed outside circles or without rules.

    Only check recognizable circles near plain or parenthesized position labels. Unknown
    outlines/special response formats still need actual item visual review.
    """
    labels = [w for w in page.get_text('words') if re.fullmatch(r'(?:\(\d{1,2}[-–]\d{1,2}\)|\d{1,2}[-–]\d{1,2})', w[4])]
    drawings = page.get_drawings()
    circles = [d['rect'] for d in drawings if 12 <= d['rect'].width <= 35
               and abs(d['rect'].width - d['rect'].height) < 1
               and sum(item[0] == 'c' for item in d['items']) >= 4]
    lines = [(min(a.x,b.x), max(a.x,b.x), a.y) for d in drawings for item in d['items']
             if item[0] == 'l' for a,b in [item[1:3]] if abs(a.y-b.y)<.2 and abs(a.x-b.x)>12]
    findings = []
    for word in labels:
        label = pymupdf.Rect(word[:4])
        near = [r for r in circles if abs((r.y0+r.y1-label.y0-label.y1)/2)<35
                and abs((r.x0+r.x1-label.x0-label.x1)/2)<80]
        if not near:
            continue
        inside = [r for r in near if (r + (-1,-1,1,1)).contains(label)]
        if not inside:
            findings.append({'label':word[4], 'issue':'position-id-outside-circle'})
            continue
        circle = min(inside, key=lambda r:r.width)
        if not any(left<=circle.x0+1 and right>=circle.x1-1 and 0<=y-circle.y1<=8 for left,right,y in lines):
            findings.append({'label':word[4], 'issue':'position-row-missing-answer-rule'})
    return findings


def rail_collision_samples(page) -> list[dict]:
    """Detect answer-position labels crossing native text or outlined math.

    Deliberately local to numbered rails: global glyph intersection would flag
    legitimate kerning, radicals and fractions. This is not a general proof of
    collision-free layout. Outline-only labels still require component review.
    """
    labels = [w for w in page.get_text('words')
              if re.fullmatch(r'(?:\(\d{1,2}[-–]\d{1,2}\)|\d{1,2}[-–]\d{1,2})', w[4])]
    chars = [c for b in page.get_text('rawdict')['blocks'] for l in b.get('lines', [])
             for s in l['spans'] for c in s['chars'] if not c['c'].isspace()]
    outlines = [d for d in page.get_drawings()
                if d.get('fill') is not None and min(d['fill']) < .5
                and 0 < d['rect'].width < 35 and 0 < d['rect'].height < 35]
    findings = []
    for word in labels:
        label = pymupdf.Rect(word[:4])
        candidates = []
        for c in chars:
            r = pymupdf.Rect(c['bbox'])
            # Label characters and the rail's circle are expected components.
            if label.contains(r) or c['c'] in {'○', '◯'}:
                continue
            candidates.append((r, 'text', c['c']))
        candidates.extend((d['rect'], 'outlined-math', '') for d in outlines)
        for rect, kind, text in candidates:
            overlap = rect & label
            if overlap.width > .7 and overlap.height > .7:
                findings.append({'label': word[4], 'label_bbox': list(label),
                                 'kind': kind, 'text': text, 'content_bbox': list(rect),
                                 'intersection': list(overlap)})
    return findings


def bottom_void(page, body_box=None):
    body = pymupdf.Rect(body_box or [64, 87, page.rect.width - 64, 775])
    pix = page.get_pixmap(clip=body, colorspace=pymupdf.csGRAY, alpha=False)
    samples = pix.samples
    last = next((r for r in range(pix.height - 1, -1, -1)
                 if min(samples[r * pix.stride:r * pix.stride + pix.width]) < 240), -1)
    return round((pix.height - last - 1) / pix.height, 3)


def table_collision_samples(page) -> list[dict]:
    """Find glyphs crossing vertical rules in multi-row grids, not just page edges.

    A review heuristic, not proof that all tables fit: borderless tables and
    overflow beyond a short rule still need source/visual containment checks.
    """
    lines = []
    for drawing in page.get_drawings():
        if drawing.get("color") is None or min(drawing["color"]) > .9:
            continue
        for item in drawing["items"]:
            if item[0] == "l":
                lines.append((item[1], item[2]))
            elif item[0] == "re":
                r = item[1]
                lines.extend([(r.tl, r.tr), (r.tr, r.br), (r.br, r.bl), (r.bl, r.tl)])
    horizontal = [(min(a.x, b.x), max(a.x, b.x), a.y) for a, b in lines
                  if abs(a.y - b.y) < .05 and abs(a.x - b.x) > 80]
    vertical = [(a.x, min(a.y, b.y), max(a.y, b.y)) for a, b in lines
                if abs(a.x - b.x) < .05 and abs(a.y - b.y) > 25]
    grids = [(x, top, bottom) for x, top, bottom in vertical
             if len({round(y, 1) for left, right, y in horizontal
                     if left - .1 <= x <= right + .1 and top - .1 <= y <= bottom + .1}) >= 3]
    chars = [c for b in page.get_text("rawdict")["blocks"] for l in b.get("lines", [])
             for s in l["spans"] for c in s["chars"] if not c["c"].isspace()]
    findings = []
    for x, top, bottom in grids:
        for char in chars:
            left, y0, right, y1 = char["bbox"]
            if left + .3 < x < right - .3 and top < y0 and y1 < bottom:
                findings.append({"character": char["c"], "bbox": list(char["bbox"]), "rule_x": x})
    return findings[:20]


def audit(pdf: Path, raster_dir: Path, *, body_box=None, math: bool = False) -> dict:
    data = pdf.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    target = raster_dir / digest[:16]
    target.mkdir(parents=True, exist_ok=True)
    pages = []
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        for number, page in enumerate(doc, 1):
            issues = []
            rect = page.rect
            if page.rotation or abs(rect.width - 595.28) > 1 or abs(rect.height - 841.89) > 1:
                issues.append("non-A4-or-rotated")
            body = pymupdf.Rect(body_box or [64, 87, rect.width - 64, 775])
            spans = [s for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]
            all_text = page.get_text()
            if "\ufffd" in all_text or "\x00" in all_text:
                issues.append("replacement-or-null-glyph")
            leaked = sorted(set(RAW_MATH.findall(all_text))) if math else []
            if math and source_note_samples(all_text):
                issues.append('printed-math-source-note')
            if math and production_caption_samples(all_text):
                issues.append('printed-math-production-caption')
            if leaked:
                issues.append("raw-math-markup-review")
            table_collisions = table_collision_samples(page)
            rail_collisions = rail_collision_samples(page)
            if rail_collisions:
                issues.append('answer-rail-content-collision')
            rail_formats = rail_format_samples(page) if math else []
            if rail_formats:
                issues.append('answer-rail-format')
            if table_collisions:
                issues.append("table-grid-text-collision-review")
            for span in spans:
                if not rect.contains(pymupdf.Rect(span["bbox"])):
                    issues.append("text-outside-page")
                    break
            # Measure visible pixels, not PDF object bounds: fixed templates
            # include white page-size rectangles that are NOT printed content.
            # The same applies to white image margins and clipped Form XObjects.
            void = bottom_void(page, body)
            if void > .32:
                issues.append("large-bottom-void-review")
            risk_reasons=list(issues)
            if page.get_image_info():risk_reasons.append('embedded-image-or-answer-rail')
            if any(body.contains(d['rect']) and d['rect'].width>5 and d['rect'].height>5
                   and (d.get('color') is not None or d.get('fill') not in (None,(1,1,1)))
                   for d in page.get_drawings()):
                risk_reasons.append('body-vector-artwork-or-table')
            if any(s['size']<9 and body.intersects(pymupdf.Rect(s['bbox'])) for s in spans):
                risk_reasons.append('small-body-type-or-script')
            if math and re.search(r'[∑∫√⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉]',all_text):
                risk_reasons.append('math-script-or-complex-symbol')
            needs_full_resolution=bool(risk_reasons)
            raster_scale=2.5 if needs_full_resolution else 1.5
            raster = target / f"page-{number:03}.png"
            page.get_pixmap(matrix=pymupdf.Matrix(raster_scale, raster_scale), alpha=False).save(raster)
            pages.append({"page": number, "raster_path": str(raster),
                          "raster_sha256": hashlib.sha256(raster.read_bytes()).hexdigest(),
                          "issues": sorted(set(issues)), "raw_math_samples": leaked,
                          "table_collision_samples": table_collisions,
                          "rail_collision_samples": rail_collisions,
                          "rail_format_samples": rail_formats,
                          "bottom_void_ratio": void,
                          "needs_full_resolution_review":needs_full_resolution,
                          "full_resolution_reasons":sorted(set(risk_reasons)),
                          "raster_scale":raster_scale,
                          "fonts": sorted({s["font"] for s in spans}),
                          "sizes_pt": sorted({round(s["size"], 2) for s in spans}),
                          "visual_review": "not-performed-by-this-tool"})
    return {"inspector_version": 3, "status": "mechanical-review-only", "pdf_sha256": digest, "pdf_path": str(pdf),
            "page_count": len(pages), "pages": pages,
            "blocking_pages": [p["page"] for p in pages if HARD_FAILURES.intersection(p["issues"])],
            "review_flag_pages": [p["page"] for p in pages if p["issues"]],
            "full_resolution_review_pages":[p['page'] for p in pages if p['needs_full_resolution_review']],
            "review_policy":"Inspect every final page and required item crop. Risk flags prioritize magnification; false never means reviewed or safe.",
            "cannot_certify": ["missing intended math symbols", "complete table cell containment",
                               "formula and diagram semantics", "template provenance",
                               "editorial difficulty and originality", "formal acceptance"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--rasters", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--math", action="store_true")
    parser.add_argument("--body-box", type=float, nargs=4)
    args = parser.parse_args()
    report = audit(args.pdf, args.rasters, body_box=args.body_box, math=args.math)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    raise SystemExit(2 if report["blocking_pages"] else 0)
