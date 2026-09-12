#!/usr/bin/env python3
"""Compose existing body pages onto verified fixed PDFs; never author questions.

PyMuPDF is the only non-standard dependency. Inputs are transparent A4 body-only
PDF pages. No template text, figures, formulas or grids are recreated here.
Output and reports are layout proofs, never educational release approvals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pymupdf

from fetch_hosted_template_assets import DEFAULT_MAP, PRODUCTION_COMPONENTS, verify


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def masked_pixels(page, regions: list, *, alpha: bool = False) -> bytes:
    pix = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), colorspace=pymupdf.csGRAY, alpha=alpha)
    for region in regions:
        rect = pymupdf.Rect(region) * pymupdf.Matrix(1.5, 1.5)
        pix.set_rect(rect.irect, (0, 0) if alpha else (255,))
    return pix.samples


def check_body(page, box) -> None:
    if page.rotation or abs(page.rect.width - 595.28) > 1 or abs(page.rect.height - 841.89) > 1:
        raise ValueError("Body pages must be unrotated A4, not automatically scaled")
    # Alpha catches opaque white full-page backgrounds as well as visible ink.
    # Such backgrounds would erase the locked cover/header even if text fits.
    pixels = masked_pixels(page, [box], alpha=True)
    if any(pixels[1::2]):
        raise ValueError("Body overlay paints outside measured body box; remove headers/backgrounds, do not clip them away")


def write_field(page, box, text: str, font, size: float, *, align: str = "center") -> None:
    rect = pymupdf.Rect(box)
    if any(not font.has_glyph(ord(c)) for c in text):
        raise ValueError(f"Dynamic-field font lacks a glyph in {text!r}")
    width = font.text_length(text, fontsize=size)
    if width > rect.width:
        raise ValueError(f"Dynamic field too long: {text!r}; supply a shorter test title")
    x = rect.x0 if align == "left" else rect.x1 - width if align == "right" else rect.x0 + (rect.width - width) / 2
    y = rect.y0 + (rect.height - size * (font.ascender - font.descender)) / 2 + size * font.ascender
    # Some DFKai/Ming font versions are misclassified as mono by MuPDF: the
    # PDF run advances every Chinese glyph by a Latin half-width even though
    # glyph_advance/text_length correctly return a full em. Place each glyph
    # explicitly using those actual advances. Only short dynamic fields use
    # this helper; it is not a general complex-script text shaper.
    # Browser-produced templates leave a content transformation in their
    # stream. Isolate it before appending anything in page-point coordinates.
    page.wrap_contents()
    buffer = font.buffer
    font_name = "TEField" + sha(buffer)[:12]
    if not any(row[4] == font_name for row in page.get_fonts()):
        page.insert_font(fontname=font_name, fontbuffer=buffer)
    for character in text:
        # Explicit per-glyph origins avoid defective mono-font run coalescing;
        # one reusable font resource avoids embedding a font for every glyph.
        page.insert_text((x, y), character, fontname=font_name, fontsize=size)
        x += font.text_length(character, fontsize=size)


def page_base(out, asset, source_page=0):
    out.insert_pdf(asset, from_page=source_page, to_page=source_page)
    return out[-1]


def compose(subject: str, body: Path, asset_dir: Path, output: Path, *, year: str,
            title: str, running_name: str, font_path: Path, map_path: Path = DEFAULT_MAP,
            kind: str = "questions") -> dict:
    if kind not in {"questions", "answers"}:
        raise ValueError("Unknown paper kind")
    if output.exists():
        raise ValueError("Preserve existing output; use a new proof filename")
    manifest = json.loads(map_path.read_text(encoding="utf-8-sig"))
    subject_record = next(s for s in manifest["subjects"] if s["subject"] == subject)
    geometry = subject_record["overlay_geometry_pt"]
    assets = {}
    hashes = {}
    try:
        for record in subject_record["assets"]:
            if record["component"] in PRODUCTION_COMPONENTS:
                data = (asset_dir / (record["component"] + ".pdf")).read_bytes()
                verify(record, data)
                assets[record["component"]] = pymupdf.open(stream=data, filetype="pdf")
                hashes[record["component"]] = sha(data)
        font = pymupdf.Font(fontfile=str(font_path))
        digits = pymupdf.Font("tiro")
        with pymupdf.open(body) as body_doc, pymupdf.open() as out:
            if not len(body_doc):
                raise ValueError("Empty body")
            for page in body_doc:
                check_body(page, geometry["body"])
            has_formula = subject in {"數學A", "數學B"} and kind == "questions"
            total = len(body_doc) + int(has_formula)
            proofs = []
            if kind == "questions":
                page = page_base(out, assets["cover-blank"])
                box = geometry["cover_title"]
                write_field(page, box, f"{year}學年度{title}", font, 19.98 if has_formula else 18)
                if masked_pixels(page, [box]) != masked_pixels(assets["cover-blank"][0], [box]):
                    raise ValueError("Cover title changed locked pixels")
                proofs.append({"page": 1, "component": "cover-blank", "locked_pixels_match": True})
            for index in range(total):
                number = index + 1
                parity = "odd" if number % 2 else "even"
                component = f"inner-{parity}-blank"
                page = page_base(out, assets[component])
                formula = index == len(body_doc)
                if formula:
                    # Reuse the formula's unchanged vector body with the correct
                    # odd/even header; the formula asset itself has an odd header.
                    box = pymupdf.Rect(geometry["body"])
                    page.show_pdf_page(box, assets["formula-blank"], 0, clip=box)
                else:
                    page.show_pdf_page(page.rect, body_doc, index)
                fields = geometry[parity]
                write_field(page, fields["year_name"], f"{year}年{running_name}", font, 10,
                            align="right" if parity == "odd" else "left")
                write_field(page, fields["current_page"], str(number), digits, 10)
                write_field(page, fields["total_pages"], str(total), digits, 10)
                write_field(page, fields["footer"], str(number), digits, 8)
                masks = [*fields.values(), geometry["body"]]
                if masked_pixels(page, masks) != masked_pixels(assets[component][0], masks):
                    raise ValueError(f"Page {number} changed locked header/footer pixels")
                proofs.append({"page": len(out), "inner_number": number, "component": component,
                               "formula_component": "formula-blank" if formula else None,
                               "locked_pixels_match": True})
            output.parent.mkdir(parents=True, exist_ok=True)
            data = out.tobytes(garbage=4, deflate=True)
            output.write_bytes(data)
        return {"status": "layout-proof-only", "subject": subject, "kind": kind,
                "body_sha256": sha(body.read_bytes()), "pdf_sha256": sha(data),
                "template_hashes": hashes, "pages": proofs,
                "remaining": ["body typography and all-page visual review", "content and independent answers",
                              "difficulty, originality and answer-bearing visuals", "final saved-PDF inspection"]}
    finally:
        for asset in assets.values():
            asset.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("subject", "year", "title", "running-name"):
        parser.add_argument("--" + name, required=True)
    for name in ("body", "asset-dir", "output", "font"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--kind", choices=("questions", "answers"), default="questions")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = compose(args.subject, args.body, args.asset_dir, args.output, year=args.year,
                     title=args.title, running_name=args.running_name, font_path=args.font,
                     map_path=args.map, kind=args.kind)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))
