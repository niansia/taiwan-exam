#!/usr/bin/env python3
"""Measured item blocks, flow rails and readable final-PDF crops (no questions)."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import pymupdf


def reserve_rail(content_boxes, *, x, slots, bottom_limit, gap=8, diameter=24,
                 label_height=12, after=12):
    """Reserve AFTER the union of actual laid-out stem, math, options and figure.

    None means move/reflow the whole item before drawing anything. Callers must
    measure wrapped text and figures, not estimate bottom from line counts.
    """
    if not content_boxes or slots < 1 or gap < 6 or after < 6:
        raise ValueError('Measured content and positive rail clearance required')
    top = max(pymupdf.Rect(b).y1 for b in content_boxes) + gap
    box = [x, top, x + slots * (diameter + 10), top + label_height + 3 + diameter]
    return None if box[3] + after > bottom_limit else {'bbox': box, 'next_y': box[3] + after}


def draw_rail(page, reservation, number, slots, diameter=24, label_height=12):
    """Draw into the reserved block; never overlay a rail onto completed stems."""
    box = pymupdf.Rect(reservation['bbox'])
    if slots * (diameter + 10) > box.width or label_height + 3 + diameter > box.height:
        raise ValueError('Rail exceeds its reservation')
    for index in range(slots):
        x = box.x0 + index * (diameter + 10)
        page.insert_text((x, box.y0 + 10), f'({number}-{index+1})', fontsize=9, fontname='tiro')
        y = box.y0 + label_height + 3
        page.draw_circle((x + diameter / 2, y + diameter / 2), diameter / 2, width=.7)
    page.draw_line((box.x0, box.y1), (box.x1, box.y1), width=.7)


def geometry_errors(doc, parts):
    """Non-overlapping block boxes: inline math belongs INSIDE its stem block.

    Boxes are supplied by the renderer and still require visual verification;
    this cannot discover undeclared/omitted content by itself.
    """
    errors, blocks = [], []
    for part in parts:
        page_no = part['page']
        box = pymupdf.Rect(part['bbox'])
        if not 1 <= page_no <= len(doc) or box.is_empty or box.is_infinite:
            errors.append('invalid item page/box')
            continue
        if not doc[page_no-1].rect.contains(box) or box.width < 100 or box.height < 20:
            errors.append('item crop outside page or unreadably small')
        components = part.get('components', [])
        if not components:
            errors.append('missing measured layout components')
        for component in components:
            r = pymupdf.Rect(component['bbox'])
            if r.is_empty or not box.contains(r):
                errors.append('component outside item crop')
            blocks.append((page_no, part['id'], component['role'], r))
    for i, (p, item, role, a) in enumerate(blocks):
        for q, other, other_role, b in blocks[i+1:]:
            if p != q:
                continue
            overlap = a & b
            if overlap.width > .5 and overlap.height > .5:
                errors.append(f'page {p}: {item}/{role} overlaps {other}/{other_role}')
            if (role == 'answer_rail' or other_role == 'answer_rail') and min(a.x1,b.x1) > max(a.x0,b.x0):
                vertical_gap = max(b.y0-a.y1, a.y0-b.y1)
                if vertical_gap < 6:
                    errors.append(f'page {p}: answer rail clearance below 6 pt')
    return errors


def crop_bytes(page, bbox):
    return page.get_pixmap(clip=pymupdf.Rect(bbox), matrix=pymupdf.Matrix(2,2), alpha=False).tobytes('png')


def crop_items(pdf, layout, output):
    raw = pdf.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if layout.get('pdf_sha256') != digest:
        raise ValueError('Layout does not describe this final PDF')
    with pymupdf.open(stream=raw, filetype='pdf') as doc:
        errors = geometry_errors(doc, layout['parts'])
        if errors:
            raise ValueError('; '.join(errors))
        target = output / digest[:16]
        target.mkdir(parents=True, exist_ok=True)
        parts = []
        for index, part in enumerate(layout['parts']):
            data = crop_bytes(doc[part['page']-1], part['bbox'])
            path = target / f'item-part-{index+1:03}.png'
            path.write_bytes(data)
            parts.append({**part, 'raster_path': str(path), 'raster_sha256': hashlib.sha256(data).hexdigest(),
                          'status': 'pending', 'observations': ''})
    return {'pdf_sha256': digest, 'parts': parts}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pdf', 'layout', 'output', 'report'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    result = crop_items(args.pdf, json.loads(args.layout.read_text(encoding='utf-8')), args.output)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
