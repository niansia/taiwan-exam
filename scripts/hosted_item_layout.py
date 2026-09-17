#!/usr/bin/env python3
"""Measured item blocks, flow rails and readable final-PDF crops (no questions)."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import pymupdf


def reserve_rail(content_boxes, *, x, slots, bottom_limit, gap=8, diameter=25.98,
                 label_height=12, after=12):
    """Reserve AFTER the union of actual laid-out stem, math, options and figure.

    None means move/reflow the whole item before drawing anything. Callers must
    measure wrapped text and figures, not estimate bottom from line counts.
    """
    if not content_boxes or slots < 1 or gap < 6 or after < 6:
        raise ValueError('Measured content and positive rail clearance required')
    top = max(pymupdf.Rect(b).y1 for b in content_boxes) + gap
    box = [x, top, x + slots * (diameter + 3), top + diameter + 3]
    return None if box[3] + after > bottom_limit else {'bbox': box, 'next_y': box[3] + after}


def draw_rail(page, reservation, number, slots, diameter=25.98, label_height=12):
    """Draw into the reserved block; never overlay a rail onto completed stems."""
    box = pymupdf.Rect(reservation['bbox'])
    if slots * (diameter + 3) > box.width + .01 or diameter + 3 > box.height + .01:
        raise ValueError('Rail exceeds its reservation')
    for index in range(slots):
        x = box.x0 + index * (diameter + 3)
        label = f'{number}-{index+1}'
        font = pymupdf.Font('tiro')
        size = 10.02
        width = font.text_length(label, fontsize=size)
        if width > diameter - 2:
            raise ValueError('Position identifier does not fit the measured circle')
        y = box.y0
        # Official row identifiers belong INSIDE their circles, not beside/above
        # an unrelated answer blank. These are new body rails, not fixed assets.
        baseline = y + diameter / 2 + size * (font.ascender + font.descender) / 2
        page.insert_text((x + (diameter - width) / 2, baseline), label, fontsize=size, fontname='tiro')
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


SIGNATURE_TOLERANCE_PT = 0.02
_SPACE = frozenset(b' \t\r\n\f\x00')
_DELIMITER = frozenset(b'()<>[]{}/%')


def _content_tokens(data):
    """Operators, numbers and names of a content stream; strings are opaque."""
    i, n = 0, len(data)
    while i < n:
        byte = data[i]
        if byte in _SPACE:
            i += 1
        elif byte == 0x25:  # % comment
            end = data.find(b'\n', i)
            i = n if end < 0 else end + 1
        elif byte == 0x28:  # (literal string) with nesting and escapes
            depth, i = 1, i + 1
            while i < n and depth:
                if data[i] == 0x5C:
                    i += 2
                    continue
                depth += (data[i] == 0x28) - (data[i] == 0x29)
                i += 1
            yield 'value', None
        elif data.startswith(b'<<', i) or data.startswith(b'>>', i):
            i += 2
            yield 'value', None
        elif byte == 0x3C:  # <hex string>
            end = data.find(b'>', i)
            i = n if end < 0 else end + 1
            yield 'value', None
        elif byte in b'[]{}':
            i += 1
            yield 'value', None
        else:
            start = i + (byte == 0x2F)
            i = start
            while i < n and data[i] not in _SPACE and data[i] not in _DELIMITER:
                i += 1
            word = data[start:i]
            if byte == 0x2F:
                yield 'name', word.decode('latin-1')
                continue
            try:
                yield 'number', float(word)
            except ValueError:
                if word == b'ID':  # inline image bytes end at a delimited EI
                    end = data.find(b'EI', i)
                    while end >= 0 and not (data[end - 1] in _SPACE and (end + 2 == n or data[end + 2] in _SPACE)):
                        end = data.find(b'EI', end + 2)
                    i = n if end < 0 else end + 2
                    yield 'inline-image', None
                else:
                    yield 'operator', word.decode('latin-1')


def image_placements(page):
    """(xref, rect) of every image XObject actually painted, following q/Q/cm/Do.

    PyMuPDF's image-info xref lookup matches images by a digest of their colour
    layer only. Answer rails are identical black layers with different masks, so
    that lookup can name another rail; the content streams name the real object.
    Returns None when any placement cannot be resolved or cross-checked.
    """
    document = page.parent
    found = []

    def xobject(owner, name):
        for holder in (owner, page.xref):
            kind, value = document.xref_get_key(holder, 'Resources/XObject/' + name)
            if kind == 'xref':
                return int(value.split()[0])
        raise ValueError('Unresolved XObject ' + name)

    def run(data, owner, ctm, depth):
        if depth > 24:
            raise ValueError('XObject nesting too deep')
        stack, operands = [], []
        for kind, value in _content_tokens(data):
            if kind == 'inline-image':
                raise ValueError('Inline image cannot be identified')
            if kind != 'operator':
                operands.append(value)
                continue
            if value == 'q':
                stack.append(ctm)
            elif value == 'Q' and stack:
                ctm = stack.pop()
            elif value == 'cm' and len(operands) >= 6 and all(type(v) is float for v in operands[-6:]):
                ctm = pymupdf.Matrix(*operands[-6:]) * ctm
            elif value == 'Do' and operands and isinstance(operands[-1], str):
                xref = xobject(owner, operands[-1])
                subtype = document.xref_get_key(xref, 'Subtype')[1]
                if subtype == '/Image':
                    corners = [pymupdf.Point(x, y) * ctm * page.transformation_matrix
                               for x, y in ((0, 0), (1, 0), (0, 1), (1, 1))]
                    found.append((xref, pymupdf.Rect(min(p.x for p in corners), min(p.y for p in corners),
                                                     max(p.x for p in corners), max(p.y for p in corners))))
                elif subtype == '/Form':
                    kind_, matrix = document.xref_get_key(xref, 'Matrix')
                    form = (pymupdf.Matrix(*map(float, matrix.strip('[]').split()))
                            if kind_ == 'array' else pymupdf.Identity)
                    run(document.xref_stream(xref) or b'', xref, form * ctm, depth + 1)
            operands = []

    try:
        run(page.read_contents(), page.xref, pymupdf.Identity, 0)
    except (ValueError, RuntimeError, TypeError):
        return None
    # Cross-check every placement against MuPDF's own image boxes.
    unmatched = [rect for _, rect in found]
    for image in page.get_image_info():
        box = pymupdf.Rect(image['bbox'])
        match = next((rect for rect in unmatched if all(abs(a - b) <= .05 for a, b in zip(rect, box))), None)
        if match is None:
            return None
        unmatched.remove(match)
    return None if unmatched else found


def render_signature(page, bbox):
    """Printed primitives reaching a crop, positioned relative to each other.

    Used only to recognise the SAME reviewed block after reflow. Fixed templates
    are 594.96 pt wide, so composition scales the body slightly and a moved block
    never lands on the same pixel phase or crop offset; its glyphs, rules and
    images still keep their mutual geometry. Page-sized template backgrounds are
    ignored; everything else inside the crop, including a neighbour's intrusion,
    stays in the signature.
    """
    rect = pymupdf.Rect(bbox)
    outer = rect + (-1, -1, 1, 1)
    rows = []  # [kind, identity, style, scalars, absolute x/y pairs]
    for block in page.get_text('rawdict')['blocks']:
        for line in block.get('lines', []):
            for span in line['spans']:
                for char in span['chars']:
                    if rect.intersects(pymupdf.Rect(char['bbox'])):
                        rows.append(['t', char['c'] + '\x00' + span['font'], [span['color'], span['flags']],
                                     [span['size']], list(char['origin'])])
    for drawing in page.get_drawings():
        area = drawing['rect']
        if not rect.intersects(area) or area.contains(outer):
            continue
        points = []
        for item in drawing['items']:
            for value in item[1:]:
                if isinstance(value, pymupdf.Point):
                    points += [value.x, value.y]
                elif isinstance(value, pymupdf.Rect):
                    points += [value.x0, value.y0, value.x1, value.y1]
                elif isinstance(value, pymupdf.Quad):
                    points += [c for p in (value.ul, value.ur, value.ll, value.lr) for c in (p.x, p.y)]
        rows.append(['d', drawing['type'] + ''.join(item[0] for item in drawing['items']),
                     [str(drawing.get('color')), str(drawing.get('fill'))], [drawing.get('width') or 0], points])
    document = page.parent
    placements = image_placements(page)
    if placements is None:
        return None  # Unidentifiable image objects are never treated as unchanged.
    for xref, area in placements:
        if not rect.intersects(area) or area.contains(outer):
            continue
        # Hash decoded pixels AND soft mask: rails are black-on-transparent.
        digest = hashlib.sha256()
        for xref in (xref, document.xref_get_key(xref, 'SMask')):
            if isinstance(xref, tuple):
                if xref[0] != 'xref':
                    continue
                xref = int(xref[1].split()[0])
            pixels = pymupdf.Pixmap(document, xref)
            digest.update(f'{pixels.width}x{pixels.height}x{pixels.n}'.encode())
            digest.update(pixels.samples)
        rows.append(['i', digest.hexdigest(), [], [], [area.x0, area.y0, area.x1, area.y1]])
    xs = [v for row in rows for v in row[4][0::2]]
    ys = [v for row in rows for v in row[4][1::2]]
    anchor = (min(xs, default=0), min(ys, default=0))
    for row in rows:
        row[4] = [v - anchor[i % 2] for i, v in enumerate(row[4])]
    rows.sort(key=lambda row: (row[0], row[1], str(row[2]), [round(v, 1) for v in row[4]]))
    return {'size': [round(rect.width, 3), round(rect.height, 3)], 'primitives': rows}


def equivalent_render(first, second, tolerance=SIGNATURE_TOLERANCE_PT):
    """Same primitives within sub-pixel noise; any glyph/rule/image change differs."""
    if not first or not second or first['size'] != second['size']:
        return False
    if not first['primitives'] or len(first['primitives']) != len(second['primitives']):
        return False
    for a, b in zip(first['primitives'], second['primitives']):
        if a[:3] != b[:3] or len(a[3]) != len(b[3]) or len(a[4]) != len(b[4]):
            return False
        if any(abs(x - y) > tolerance for x, y in zip(a[3] + a[4], b[3] + b[4])):
            return False
    return True


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
