#!/usr/bin/env python3
"""Official-style mathematics and heading typography for the hosted body renderer.

The ROC 111–115 booklets stack every fraction, draw a vinculum over each radicand,
put arrows over vectors and bars over segments, and letter-space their bold part
headings. MuPDF's HTML engine can do none of this, and the pinned hosted PyMuPDF
1.26.0 also ignores inline vertical alignment, so two hosted 116 數A booklets printed
「27/64」「2√6」 and plain headings. Each construct is reserved in the HTML flow as a
transparent placeholder image of its exact width and above-baseline height (an
inline image's bottom sits on the text baseline in every version); once the block is
laid out, the placeholder is removed and the construct is painted there as real,
searchable glyphs and rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import re

import pymupdf

TOKEN = re.compile(r'\{\{(frac|sqrt|vec|seg)(\.s)?:([^{}]*)\}\}')
FUNCTIONS = {'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'log', 'ln', 'lim', 'max', 'min', 'exp', 'gcd', 'lcm', 'deg', 'mod'}
# A fraction or radical operand: coefficient radicals, π multiples, coefficient
# variables, decimals, a single letter, or one parenthesised group.
ATOM = r'(?:\d*√(?:\d+(?:\.\d+)?|[A-Za-z]|\([^()]{1,24}\))|\d*π|\d+[A-Za-z]|\d+(?:\.\d+)?|[A-Za-zπθ]|\([^()]{1,24}\))'
FRACTION = re.compile(rf'(?<![A-Za-z0-9_.)√/])({ATOM})/({ATOM})(?![A-Za-z0-9_(√/])')
RADICAL = re.compile(r'√(\d+(?:\.\d+)?|[A-Za-z]|\([^()]{1,24}\))')
MARKUP_SPLIT = re.compile(r'(<[^>]+>|&[a-z#0-9]+;|\{\{[^{}]*\}\})')
CHILD_SCALE = .86          # fraction operands, as the official booklets set them
SCRIPT_SCALE = .7          # tokens inside <sup>/<sub>, matching sup,sub {font-size:70%}
FONT_KEYS = {'roman': 'MR', 'italic': 'MI', 'bold': 'MB', 'cjk': 'MC'}


def _strip_group(text: str) -> str:
    return text[1:-1] if text.startswith('(') and text.endswith(')') else text


def math_tokens(markup: str) -> str:
    """Rewrite plain 「a/b」 and 「√x」 in already-escaped markup as typeset tokens."""
    parts = MARKUP_SPLIT.split(markup)
    depth = 0
    for index, part in enumerate(parts):
        if not part:
            continue
        if part.startswith('<'):
            tag = part.strip('</>').split()[0].lower() if part.strip('</>') else ''
            if tag in {'sup', 'sub'}:
                depth += -1 if part.startswith('</') else 1
            continue
        if part.startswith(('&', '{{')):
            continue
        flag = '.s' if depth > 0 else ''
        part = FRACTION.sub(lambda m: f'{{{{frac{flag}:{_strip_group(m.group(1))}|{_strip_group(m.group(2))}}}}}', part)
        pieces = re.split(r'(\{\{[^{}]*\}\})', part)
        pieces = [p if p.startswith('{{') else RADICAL.sub(lambda m: f'{{{{sqrt{flag}:{_strip_group(m.group(1))}}}}}', p)
                  for p in pieces]
        parts[index] = ''.join(pieces)
    return ''.join(parts)


class Fonts:
    """Metrics of the faces a construct is painted with."""
    def __init__(self, cjk: pymupdf.Font | None):
        self.faces = {'roman': pymupdf.Font('tiro'), 'italic': pymupdf.Font('tiit'), 'bold': pymupdf.Font('tibo'),
                      'cjk': cjk or pymupdf.Font('cjk')}

    def face_for(self, char: str, style: str) -> str:
        if style == 'bold' and self.faces['bold'].has_glyph(ord(char)):
            return 'bold'
        if style == 'italic' and char.isascii() and char.isalpha():
            return 'italic'
        if self.faces['roman'].has_glyph(ord(char)):
            return 'roman'
        return 'cjk'

    def width(self, char: str, face: str, size: float) -> float:
        return self.faces[face].text_length(char, fontsize=size)


@dataclass
class Glyphs:
    """A run of characters; letters that name variables print italic."""
    text: str
    size: float
    fonts: Fonts
    bold: bool = False
    spacing: float = 0.0
    runs: list = field(default_factory=list)

    def __post_init__(self):
        x = 0.0
        for chunk in re.findall(r'[A-Za-z]+|.', self.text):
            style = 'bold' if self.bold else (
                'roman' if chunk in FUNCTIONS or (len(chunk) > 1 and not chunk.isupper()) else 'italic')
            for char in chunk:
                face = self.fonts.face_for(char, style)
                self.runs.append((x, char, face))
                x += self.fonts.width(char, face, self.size) + self.spacing
        self.w = max(0.0, x - self.spacing) if self.runs else 0.0
        self.asc = .72 * self.size if not self.bold else .9 * self.size
        self.desc = .22 * self.size

    def paint(self, page, x, base):
        for dx, char, face in self.runs:
            extra = {'render_mode': 2, 'border_width': .045, 'color': (0, 0, 0), 'fill': (0, 0, 0)} if self.bold else {}
            page.insert_text((x + dx, base), char, fontname=FONT_KEYS[face], fontsize=self.size, **extra)


def parse(text: str, size: float, fonts: Fonts) -> list:
    """Operand text as boxes: radicals nest; everything else is glyphs."""
    boxes, buffer, i = [], '', 0
    while i < len(text):
        if text[i] == '√':
            match = RADICAL.match(text, i)
            if match:
                if buffer:
                    boxes.append(Glyphs(buffer, size, fonts))
                    buffer = ''
                boxes.append(Radical(parse(_strip_group(match.group(1)), size, fonts), size))
                i = match.end()
                continue
        buffer += text[i]
        i += 1
    if buffer:
        boxes.append(Glyphs(buffer, size, fonts))
    return boxes


class Row:
    def __init__(self, boxes):
        self.boxes = boxes
        self.w = sum(b.w for b in boxes)
        self.asc = max((b.asc for b in boxes), default=0)
        self.desc = max((b.desc for b in boxes), default=0)

    def paint(self, page, x, base):
        for box in self.boxes:
            box.paint(page, x, base)
            x += box.w


class Radical:
    def __init__(self, inner, size):
        self.inner, self.size = Row(inner), size
        self.sign = .56 * size
        self.w = self.sign + self.inner.w + .08 * size
        self.asc = self.inner.asc + .2 * size
        self.desc = max(self.inner.desc, .12 * size)

    def paint(self, page, x, base):
        s, top = self.size, base - self.inner.asc - .13 * self.size
        shape = page.new_shape()
        shape.draw_polyline([(x + .04 * s, base - .32 * s), (x + .13 * s, base - .38 * s),
                             (x + .27 * s, base + .08 * s), (x + self.sign - .03 * s, top),
                             (x + self.w, top)])
        shape.finish(color=(0, 0, 0), width=.05 * s, closePath=False, lineCap=0, lineJoin=1)
        shape.commit()
        self.inner.paint(page, x + self.sign, base)


class Fraction:
    def __init__(self, num, den, size):
        self.size = size
        self.num, self.den = Row(num), Row(den)
        pad = .12 * size
        self.w = max(self.num.w, self.den.w) + 2 * pad
        self.axis = .27 * size
        self.gap = .12 * size
        self.asc = self.axis + self.gap + self.num.desc * .4 + self.num.asc
        self.desc = self.den.asc + self.gap - self.axis + self.den.desc * .4

    def paint(self, page, x, base):
        axis = base - self.axis
        page.draw_line((x + .04 * self.size, axis), (x + self.w - .04 * self.size, axis), color=(0, 0, 0), width=.05 * self.size)
        self.num.paint(page, x + (self.w - self.num.w) / 2, axis - self.gap - self.num.desc * .4)
        self.den.paint(page, x + (self.w - self.den.w) / 2, axis + self.gap + self.den.asc)


class Accent:
    """Arrow (vector) or bar (segment) over italic point or vector names."""
    def __init__(self, inner, size, arrow):
        self.inner, self.size, self.arrow = Row(inner), size, arrow
        self.w = self.inner.w + .1 * size
        self.asc = self.inner.asc + (.32 if arrow else .2) * size
        self.desc = self.inner.desc

    def paint(self, page, x, base):
        s = self.size
        y = base - self.inner.asc - .14 * s
        left, right = x + .04 * s, x + self.w - .02 * s
        page.draw_line((left, y), (right - (.05 * s if self.arrow else 0), y), color=(0, 0, 0), width=.05 * s)
        if self.arrow:
            head = page.new_shape()
            head.draw_polyline([(right - .22 * s, y - .1 * s), (right, y), (right - .22 * s, y + .1 * s)])
            head.finish(color=(0, 0, 0), fill=(0, 0, 0), width=.03 * s, closePath=True)
            head.commit()
        self.inner.paint(page, x + .05 * s, base)


class Heading:
    """A part heading: 13 pt, letter-spaced and stroke-bold, as the booklets print it."""
    def __init__(self, text, size, spacing, fonts):
        self.glyphs = Glyphs(text, size, fonts, bold=True, spacing=spacing)
        self.w, self.asc, self.desc = self.glyphs.w, .92 * size, .2 * size

    def paint(self, page, x, base):
        self.glyphs.paint(page, x, base)


def build(kind: str, body: str, size: float, fonts: Fonts):
    if kind == 'frac':
        num, _, den = body.partition('|')
        child = size * CHILD_SCALE
        return Fraction(parse(num, child, fonts), parse(den, child, fonts), size)
    if kind == 'sqrt':
        return Radical(parse(body, size, fonts), size)
    return Accent(parse(body, size, fonts), size, arrow=kind == 'vec')


class Typesetter:
    """Placeholders for one render: HTML images now, painted constructs after layout."""
    def __init__(self, cjk_font_path=None, size=11.0):
        self.cjk_path = cjk_font_path
        self.fonts = Fonts(pymupdf.Font(fontfile=str(cjk_font_path)) if cjk_font_path else None)
        self.size = size
        self.boxes = {}

    def _placeholder(self, box, archive) -> str:
        name = f'mph-{len(self.boxes)}.png'
        # MuPDF lays inline images out at whole points; the construct is centred in its box.
        width, height = max(1, math.ceil(box.w)), max(1, math.ceil(box.asc))
        dims = (width * 4, height * 4)
        self.boxes[name] = (box, dims)
        pixels = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, *dims), 1)
        pixels.clear_with(0)
        archive.add((pixels.tobytes('png'), name))
        return f'<img src="{name}" width="{width}" height="{height}">'

    def tokens(self, markup: str, archive) -> str:
        def replace(match):
            size = self.size * (SCRIPT_SCALE if match.group(2) else 1)
            return self._placeholder(build(match.group(1), match.group(3), size, self.fonts), archive)
        return TOKEN.sub(replace, markup)

    def heading(self, text: str, size: float, spacing: float, archive) -> str:
        return self._placeholder(Heading(text, size, spacing, self.fonts), archive)

    def paint(self, page, markup: str):
        """Replace this block's placeholders with painted constructs; fail loudly on a mismatch."""
        names = re.findall(r'<img src="(mph-\d+\.png)"', markup)
        if not names:
            return page
        doc = page.parent
        # Placeholders are recognised by their pixel size, in paint order. PyMuPDF
        # 1.26 merges identical placeholder images, so every image resource of a
        # placeholder size is removed, not only the one an info record names.
        sizes = {self.boxes[name][1] for name in names}
        placeholders = {(name, referencer) for _xref, _smask, w, h, *_rest, name, _filter, referencer
                        in page.get_images(full=True) if (w, h) in sizes}
        pending, order = list(names), []
        for info in page.get_image_info(xrefs=True):
            if pending and (info['width'], info['height']) == self.boxes[pending[0]][1]:
                order.append(info)
                pending.pop(0)
        if pending:
            raise ValueError(f'Typeset placeholders: expected {len(names)}, found {len(order)} on the measured page')
        for key, face in FONT_KEYS.items():
            if key == 'cjk':
                if self.cjk_path:
                    page.insert_font(fontname=face, fontfile=str(self.cjk_path))
                else:
                    page.insert_font(fontname=face, fontbuffer=pymupdf.Font('cjk').buffer)
            else:
                page.insert_font(fontname=face, fontbuffer=self.fonts.faces[key].buffer)
        for name, info in zip(names, order):
            box, rect = self.boxes[name][0], pymupdf.Rect(info['bbox'])
            if abs(rect.width - max(1, math.ceil(box.w))) > .3:
                raise ValueError(f'Typeset placeholder {name} laid out {rect.width:.2f} pt wide, expected {math.ceil(box.w)}')
            box.paint(page, rect.x0 + (rect.width - box.w) / 2, rect.y1)
        for name, referencer in placeholders:
            stream = doc.xref_stream(referencer)
            doc.update_stream(referencer, re.sub(rb'/' + re.escape(name.encode()) + rb'\s+Do\b', b'', stream))
        # The page caches its parsed content; later checks must see the painted result.
        return doc.reload_page(page)


_standalone_cache: dict = {}


UNITS = frozenset({'cm', 'mm', 'km', 'kg', 'mg', 'ml', 'mL', 'am', 'pm', 'hr', 'min', 'sec'})


def identifier_markup(run: str, context: str, start: int) -> str:
    """Italicise variable names inside one escaped Latin run of mathematics text."""
    # One scan per text, not per run: a long passage has thousands of runs.
    if _standalone_cache.get('context') is not context:
        _standalone_cache.update(context=context,
                                 letters=set(re.findall(r'(?<![A-Za-z])([A-Z])(?![A-Za-z])', context)),
                                 lower=set(re.findall(r'(?<![A-Za-z])([a-z])(?![A-Za-z])', context)))
    standalone = _standalone_cache['letters']
    lower = _standalone_cache['lower']
    geometric = re.search(r'(?:三角形|四邊形|梯形|線段|直線|射線|平面|弧|△|∠|點|正方形|長方形|菱形|四面體|六面體|多邊形)\s*$',
                          context[max(0, start - 12):start])

    def letters(match):
        word = match.group(0)
        if word in FUNCTIONS or word in UNITS:
            return word
        if len(word) > 1 and word.islower() and len(word) <= 3 and all(c in lower for c in word):
            # A product of variables used alone elsewhere (「a+b=7 與 ab=10」) is italic,
            # as the booklets print it; other lowercase words (units, labels) stay upright.
            return f'<span class="var">{word}</span>'
        if len(word) > 1 and not word.isupper():
            return word
        if len(word) == 1 or (len(word) <= 4 and (all(c in standalone for c in word) or geometric)):
            return f'<span class="var">{word}</span>'
        return word
    return re.sub(r'[A-Za-z]+', letters, run)
