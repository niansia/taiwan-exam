#!/usr/bin/env python3
"""Check final saved PDF bytes against canonical fixed GSAT layers, offline.

This verifies template reuse and page furniture, not item quality or authorship.
No supplied composition report, output metadata or author-selected mask is trusted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import pymupdf
from fetch_hosted_template_assets import DEFAULT_MAP, PRODUCTION_COMPONENTS, ROOT, verify


def masked_pixels(page, regions, *, alpha=False):
    matrix = pymupdf.Matrix(1.5, 1.5)
    pix = page.get_pixmap(matrix=matrix, colorspace=pymupdf.csGRAY, alpha=alpha)
    samples = bytearray(pix.samples)
    for region in regions:
        rect = (pymupdf.Rect(region) * matrix).irect & pix.irect
        if rect.is_empty:
            continue
        # PyMuPDF's set_rect currently loops through every sample in Python.
        # Whole scanline replacement preserves exactly the same integer bounds,
        # pixel values and comparison resolution without millions of callbacks.
        row = bytes([0 if alpha else 255]) * (rect.width * pix.n)
        for y in range(rect.y0, rect.y1):
            start = (y-pix.y)*pix.stride + (rect.x0-pix.x)*pix.n
            samples[start:start+len(row)] = row
    return bytes(samples)


def streams(page):
    # Page content plus nested Form XObjects reachable from this page; document
    # attachments and unused objects elsewhere are not evidence of composition.
    refs = page.get_contents() + [row[0] for row in page.get_xobjects()]
    return {hashlib.sha256(page.parent.xref_stream(x)).hexdigest() for x in refs}


def field_pixels(page, box):
    return page.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=pymupdf.Rect(box),
                           colorspace=pymupdf.csGRAY).samples


def expected_counter(box, text, size):
    # Compare rendered digits. PDF text extraction can include invisible text
    # outside a clipped Form XObject, including the formula's original header.
    font = pymupdf.Font('tiro')
    rect = pymupdf.Rect(box)
    x = rect.x0 + (rect.width-font.text_length(text,fontsize=size))/2
    y = rect.y0 + (rect.height-size*(font.ascender-font.descender))/2 + size*font.ascender
    with pymupdf.open() as doc:
        page = doc.new_page(width=595.28,height=841.89)
        page.insert_font(fontname='Counter',fontbuffer=font.buffer)
        for character in text:
            page.insert_text((x,y),character,fontname='Counter',fontsize=size)
            x += font.text_length(character,fontsize=size)
        return field_pixels(page,box)


def verify_pdf(pdf: Path, subject: str, kind: str, asset_dir: Path | None = None) -> dict:
    errors, pages, assets = [], [], {}
    report = {'status': 'fail-fixed-template', 'subject': subject, 'kind': kind,
              'errors': errors, 'pages': pages, 'scope': 'Fixed PDF layers only; no academic acceptance.'}
    try:
        if kind not in {'questions', 'answers'}:
            raise ValueError('kind must be questions or answers')
        manifest = json.loads(DEFAULT_MAP.read_text(encoding='utf-8-sig'))
        record = next((r for r in manifest['subjects'] if r['subject'] == subject), None)
        if record is None:
            raise ValueError('unsupported fixed-template subject')
        geometry = record['overlay_geometry_pt']
        for asset in record['assets']:
            component = asset['component']
            if component not in PRODUCTION_COMPONENTS:
                continue
            path = asset_dir / (component + '.pdf') if asset_dir else ROOT / asset['repository_path']
            data = path.read_bytes()
            verify(asset, data)
            assets[component] = pymupdf.open(stream=data, filetype='pdf')
        data = pdf.read_bytes()
        report['pdf_sha256'] = hashlib.sha256(data).hexdigest()
        math_formula = subject in {'數學A', '數學B'} and kind == 'questions'
        offset = int(kind == 'questions')
        with pymupdf.open(stream=data, filetype='pdf') as doc:
            total = len(doc) - offset
            if total < 1 + int(math_formula):
                errors.append('missing cover/body/formula pages')
            baselines = {}
            for index, page in enumerate(doc):
                number = index + 1 - offset
                cover = offset and index == 0
                parity = 'odd' if number % 2 else 'even'
                component = 'cover-blank' if cover else f'inner-{parity}-blank'
                base = assets[component][0]
                fields = {} if cover else geometry[parity]
                masks = [geometry['cover_title']] if cover else [geometry['body'], *fields.values()]
                findings = []
                if page.rotation or abs(page.rect.width-base.rect.width) > .01 or abs(page.rect.height-base.rect.height) > .01:
                    findings.append('page-size-or-rotation')
                if component not in baselines:
                    baselines[component] = masked_pixels(base, masks)
                if masked_pixels(page, masks) != baselines[component]:
                    findings.append('locked-pixels-changed')
                reachable = streams(page)
                if not streams(base).issubset(reachable):
                    findings.append('original-template-stream-missing')
                if cover:
                    if not page.get_textbox(pymupdf.Rect(geometry['cover_title'])).strip():
                        findings.append('missing-dynamic-cover-title')
                else:
                    for key, box in fields.items():
                        text = ''.join(page.get_textbox(pymupdf.Rect(box)).split())
                        expected = str(total) if key == 'total_pages' else str(number)
                        wrong = (not text or field_pixels(page,box)==field_pixels(base,box)) if key == 'year_name' else (
                            field_pixels(page,box) != expected_counter(box,expected,8 if key=='footer' else 10))
                        if wrong:
                            findings.append('incorrect-dynamic-' + key)
                formula = math_formula and index == len(doc)-1
                if formula:
                    original = assets['formula-blank'][0]
                    box = pymupdf.Rect(geometry['body'])
                    def pixels(p):
                        return p.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), clip=box,
                                            colorspace=pymupdf.csGRAY).samples
                    if pixels(page) != pixels(original):
                        findings.append('original-formula-body-changed')
                    if not streams(original).issubset(reachable):
                        findings.append('original-formula-stream-missing')
                pages.append({'page': index+1, 'component': component, 'formula': bool(formula), 'errors': findings})
                errors.extend(f'page-{index+1}: {finding}' for finding in findings)
        report['status'] = 'pass-fixed-template' if not errors else 'fail-fixed-template'
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        errors.append(f'cannot verify fixed template: {exc}')
    finally:
        for doc in assets.values():
            doc.close()
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--subject', required=True)
    parser.add_argument('--kind', required=True, choices=('questions', 'answers'))
    parser.add_argument('--asset-dir', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify_pdf(args.pdf, args.subject, args.kind, args.asset_dir)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text)
    raise SystemExit(0 if result['status'] == 'pass-fixed-template' else 2)
