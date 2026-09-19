#!/usr/bin/env python3
"""Compose existing body pages onto verified fixed PDFs; never author questions.

PyMuPDF is the only required non-standard dependency; fontTools, when present,
only trims unused glyphs. Inputs are transparent A4 body-only PDF pages. No
template text, figures, formulas or grids are recreated here.
Output and reports are layout proofs, never educational release approvals.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re

import pymupdf

from fetch_hosted_template_assets import DEFAULT_MAP, PRODUCTION_COMPONENTS, verify
from inspect_hosted_pdf import rail_collision_samples
from verify_fixed_template_pdf import verify_pdf, masked_pixels

# Only whole CJK body fonts are this large; fixed-template fonts are small subsets.
LARGE_FONT_PROGRAM = 1_000_000
REFERENCE = re.compile(r'(\d+) 0 R')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def font_programs(doc):
    """{program xref: base font names} for embedded fonts larger than LARGE_FONT_PROGRAM."""
    found = {}
    for page in doc:
        for xref, _, _, basefont, *_ in page.get_fonts(full=True):
            if not xref:
                continue
            descendant = REFERENCE.search(doc.xref_get_key(xref, 'DescendantFonts')[1] or '')
            owner = int(descendant.group(1)) if descendant else xref
            descriptor = REFERENCE.search(doc.xref_get_key(owner, 'FontDescriptor')[1] or '')
            if not descriptor:
                continue
            for key in ('FontFile3', 'FontFile2', 'FontFile'):
                program = REFERENCE.search(doc.xref_get_key(int(descriptor.group(1)), key)[1] or '')
                if program and len(doc.xref_stream_raw(int(program.group(1)))) > LARGE_FONT_PROGRAM:
                    found.setdefault(int(program.group(1)), set()).add(re.sub(r'^[A-Z]{6}\+', '', basefont))
    return found


def merge_duplicate_fonts(data: bytes) -> bytes:
    """One copy of a font embedded twice (body and header fields): same pages, half the bytes."""
    with pymupdf.open(stream=data, filetype='pdf') as doc:
        return doc.tobytes(garbage=4, deflate=True)  # identical copies collapse once both are compressed


def compact_fonts(data: bytes) -> tuple[bytes, dict]:
    """Merge duplicate font copies and drop glyphs no page draws; never change a pixel.

    A whole CJK font is ~20 MB and was embedded twice (body and header fields),
    making an 8-page paper 40 MB. Page content streams are never rewritten: a
    CID-keyed CFF font keeps each glyph's CID, other fonts keep glyph ids. Any
    rendering or text difference keeps the unsubsetted fonts. This takes seconds
    per booklet, so it runs once on the checked booklets, not on every build.
    """
    merged = merge_duplicate_fonts(data)
    report = {'bytes_before': len(data), 'bytes_after': len(merged), 'status': 'duplicates-merged'}
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        return merged, {**report, 'note': 'fontTools unavailable; unused glyphs kept'}
    with pymupdf.open(stream=merged, filetype='pdf') as doc:
        programs = font_programs(doc)
        if not programs:
            return merged, report
        used = {}
        for page in doc:
            for span in page.get_texttrace():
                used.setdefault(span['font'], set()).update(char[1] for char in span['chars'])
        before = [(page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False).samples, page.get_text())
                  for page in doc]
        for xref, names in programs.items():
            font = TTFont(io.BytesIO(doc.xref_stream(xref)), lazy=True)
            # Text tracing reports the program's own PostScript name, which can
            # differ from the PDF BaseFont (e.g. "Noto Serif CJK TC Regular").
            names = set(names)
            if 'name' in font:
                names |= {font['name'].getDebugName(number) for number in (4, 6)} - {None}
            cid_keyed = False
            if 'CFF ' in font:
                cff = font['CFF '].cff
                names |= set(cff.fontNames)
                cid_keyed = hasattr(cff[cff.fontNames[0]], 'ROS')
            glyphs = set().union(*(used.get(name, set()) for name in names))
            if not glyphs:
                continue  # No drawn glyph matched this program: keep it whole.
            glyphs.add(0)
            options = subset.Options()
            # CID-keyed glyphs are found by CID, so renumbering them is safe and
            # far faster than writing 65,000 empty glyph slots.
            options.retain_gids = not cid_keyed
            options.notdef_outline = True
            options.name_IDs = ['*']
            options.layout_features = []  # the PDF already holds positioned glyphs
            options.drop_tables = [*options.drop_tables, 'GSUB', 'GPOS', 'GDEF', 'BASE', 'JSTF', 'MATH']
            subsetter = subset.Subsetter(options)
            subsetter.populate(gids=sorted(glyphs))
            subsetter.subset(font)
            buffer = io.BytesIO()
            font.save(buffer)
            doc.update_stream(xref, buffer.getvalue())
            doc.xref_set_key(xref, 'Length1', str(len(buffer.getvalue())))
        compact = doc.tobytes(garbage=4, deflate=True)
    with pymupdf.open(stream=compact, filetype='pdf') as check:
        same = [(page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False).samples, page.get_text())
                for page in check] == before
    if not same:
        return merged, {**report, 'note': 'subset changed rendering or text; full fonts kept'}
    return compact, {**report, 'bytes_after': len(compact), 'status': 'unused-glyphs-dropped'}


def check_body(page, box) -> None:
    if page.rotation or abs(page.rect.width - 595.28) > 1 or abs(page.rect.height - 841.89) > 1:
        raise ValueError("Body pages must be unrotated A4, not automatically scaled")
    # Alpha catches opaque white full-page backgrounds as well as visible ink.
    # Such backgrounds would erase the locked cover/header even if text fits.
    pixels = masked_pixels(page, [box], alpha=True)
    if any(pixels[1::2]):
        raise ValueError("Body overlay paints outside measured body box; remove headers/backgrounds, do not clip them away")


def write_field(page, box, text: str, font, size: float, *, align: str = "center", resource=None) -> None:
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
    buffer, font_name = resource if resource else field_resource(font)
    if not any(row[4] == font_name for row in page.get_fonts()):
        page.insert_font(fontname=font_name, fontbuffer=buffer)
    for character in text:
        # Explicit per-glyph origins avoid defective mono-font run coalescing;
        # one reusable font resource avoids embedding a font for every glyph.
        page.insert_text((x, y), character, fontname=font_name, fontsize=size)
        x += font.text_length(character, fontsize=size)


def field_resource(font):
    buffer = font.buffer
    return buffer, 'TEField' + sha(buffer)[:12]


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
        font_resource, digit_resource = field_resource(font), field_resource(digits)
        base_pixels = {}
        with pymupdf.open(body) as body_doc, pymupdf.open() as out:
            if not len(body_doc):
                raise ValueError("Empty body")
            for page in body_doc:
                check_body(page, geometry["body"])
                if rail_collision_samples(page):
                    raise ValueError('Body answer-rail-content-collision; reflow before fixed-template composition')
            has_formula = subject in {"數學A", "數學B"} and kind == "questions"
            total = len(body_doc) + int(has_formula)
            proofs = []
            if kind == "questions":
                page = page_base(out, assets["cover-blank"])
                box = geometry["cover_title"]
                write_field(page, box, f"{year}學年度{title}", font, 19.98 if has_formula else 18, resource=font_resource)
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
                            align="right" if parity == "odd" else "left", resource=font_resource)
                write_field(page, fields["current_page"], str(number), digits, 10, resource=digit_resource)
                write_field(page, fields["total_pages"], str(total), digits, 10, resource=digit_resource)
                write_field(page, fields["footer"], str(number), digits, 8, resource=digit_resource)
                masks = [*fields.values(), geometry["body"]]
                if component not in base_pixels:
                    base_pixels[component] = masked_pixels(assets[component][0], masks)
                if masked_pixels(page, masks) != base_pixels[component]:
                    raise ValueError(f"Page {number} changed locked header/footer pixels")
                proofs.append({"page": len(out), "inner_number": number, "component": component,
                               "formula_component": "formula-blank" if formula else None,
                               "locked_pixels_match": True})
            output.parent.mkdir(parents=True, exist_ok=True)
            data = merge_duplicate_fonts(out.tobytes(garbage=4, deflate=True))
            output.write_bytes(data)
        saved_check = verify_pdf(output, subject, kind, asset_dir)
        if saved_check['errors']:
            raise ValueError('Saved fixed-template verification failed: ' + '; '.join(saved_check['errors']))
        return {"fixed_template_verification": saved_check, "status": "layout-proof-only", "subject": subject, "kind": kind,
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
