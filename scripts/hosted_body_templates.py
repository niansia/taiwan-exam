#!/usr/bin/env python3
"""Flow-layout components only. Never generate, select or reuse exam questions."""
from __future__ import annotations
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import inspect
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

import pymupdf
from fetch_hosted_template_assets import DEFAULT_MAP
from hosted_math_typeset import Typesetter, math_tokens, identifier_markup
from hosted_density import page_void_limit
from hosted_item_layout import draw_rail

HTML_OPTIONS = {'_scale_word_width':False} if '_scale_word_width' in inspect.signature(pymupdf.Page.insert_htmlbox).parameters else {}

KINDS = ('section', 'choice', 'multiple', 'fill', 'constructed', 'stimulus', 'solution', 'passage', 'table')
# Blocks and crop edges sit on a 0.5 pt grid (one pixel at the 2 px/pt review
# scale), so crops carry no partial-pixel clip noise and a proof crop matches the
# final crop of the same block. Figure leading adds 0.025 pt so image edges avoid
# device-pixel boundaries, where float32 noise otherwise flips image gridfitting.
BLOCK_GRID_PT = 0.5
FIGURE_LEADING_PT = 4.05
# A last page filled below this fraction triggers a retry with closer blocks.
TRAILING_PAGE_FILL = 0.2
TIGHTER_GAPS = (0.75, 0.5)
OPTION_COLUMNS = (1, 2, 3, 4, 5)


def snap_block_top(value):
    return math.ceil(value / BLOCK_GRID_PT - 1e-9) * BLOCK_GRID_PT


# MuPDF applies a cell's vertical-align to every inline run inside it: top-aligned
# text cells flattened <sup> onto the baseline, so T<sup>2</sup> printed like a
# subscript. Text cells align first baselines instead; figure cells stay on top.
# Measured on the ROC 115 booklets (option-line pitch / item-to-item gap, pt):
# 國綜 16-17 / 19-20, 英文 16-17 / 17-18, 社會 and 自然 17-18 / 20-21, 數學 20 / 31.
# A generated 國綜 paper at the old uniform 1.65 leading printed 23 pt option
# rows and 42 pt item gaps, 17 pages against the official 12. Prose subjects
# therefore use the official leading; mathematics keeps room for scripts.
TYPOGRAPHY = {'國綜': (1.5, 0, 3, 1, 4), '國寫': (1.667, 0, 3, 1, 4), '英文': (1.5, 0, 3, 1, 4),
              '社會': (1.6, 0, 3, 1, 4), '自然': (1.6, 0, 3, 1, 4)}
DEFAULT_TYPOGRAPHY = (1.65, 3, 5, 3, 12)  # line-height, cell padding, paragraph margin, options top, item gap
# The official 國寫 booklet sets its body at 12 pt on a 20 pt line (111-115 measured);
# every other subject prints 11 pt.
BODY_SIZE_PT = {'國寫': 12}
# Official booklets set the bordered 說明 box and the 國寫 reading materials in 標楷體
# (DFKai-SB, 111-115 measured) while 問題（一）／（二）, 「請分項回答下列問題」, part labels
# and every other subject's body stay in 明體. The Kai face is the preflight's pinned
# download; without it these blocks fall back to the serif body face.
CSS_TEMPLATE = '''
@font-face {font-family:Body;src:url(body-font.ttf)}
* {box-sizing:border-box} body {font-family:Body;font-size:BODY_SIZEpt;line-height:LINE_HEIGHT;margin:0;color:#000;background:transparent}
p {margin:0 0 P_MARGINpt} table {border-collapse:collapse;border-spacing:0;width:100%;margin:0} td {padding:0 4pt CELL_PADpt 0;vertical-align:baseline}
td.figure {vertical-align:top}
.direction {border:0.6pt solid black;padding:3pt DIR_RIGHTpt 3pt DIR_PADpt;text-indent:-DIR_INDENTpt;font-size:DIR_SIZEpt;line-height:1.3;font-family:Kai,Body}
.material {font-family:Kai,Body} p.hanging {padding-left:6em;text-indent:-6em;text-align:justify} p.plain {text-indent:0}
table.material-label {width:auto;margin:2pt 0 4pt} table.material-label td {border:0.6pt solid black;padding:0;line-height:1.4}
p.part {font-size:13pt;margin-bottom:2pt}
.heading {font-size:13pt;font-weight:bold;margin-bottom:4pt}
.figure {text-align:center} .score {font-size:11pt}
u {text-decoration:underline} .kai {font-family:Kai,Body}
p.task {text-align:justify} p.hint {padding-left:28.6pt;text-indent:-28.6pt;text-align:justify}
p.hang {padding-left:18pt;text-indent:-18pt}
p.subpart {padding-left:30pt;text-indent:-30pt;margin:0}
sup,sub {font-size:70%} .options {margin-top:OPTIONS_TOPpt}
.optionlist {margin-left:NUMBER_PITCHpt;margin-top:OPTIONS_TOPpt} .optionlist p {margin:0;padding-left:18pt;text-indent:-18pt} .optionlist td {padding-bottom:0}
.passage {font-family:Reading,Body} .english {font-family:Latin,Body} .latin {font-family:Latin,Body} .var {font-family:LatinItalic,Body}
.data td,.data th {border:0.6pt solid black;padding:5pt;text-align:left;font-weight:normal}
.group-label {font-weight:bold;margin-bottom:3pt} .group-label.underline {font-weight:normal;text-decoration:underline}
.group-label.plain {font-weight:normal}
.cn-material {margin-left:18.2pt;font-family:Kai,Body;text-align:justify} .cn-material p {margin:0}
.cn-material.inline {margin-left:0} .cn-material p.indent {text-indent:24pt} .cn-material p.hang {padding-left:22.8pt;text-indent:-22.8pt}
p.indent {text-indent:2em;text-align:justify} .english .score {font-family:Body}
.social-material p {margin:0;text-indent:24pt;text-align:justify} .social-material p.flush {text-indent:0}
.figcaption {text-align:center;margin-top:1pt;line-height:1.3}
'''


def typography(subject):
    return TYPOGRAPHY.get(subject, DEFAULT_TYPOGRAPHY)


def subject_css(subject):
    line_height, cell_pad, p_margin, options_top, _ = typography(subject)
    direction = DIRECTION_SIZE_PT.get(subject, 12)
    pad_left, indent, pad_right = DIRECTION_BOX_PT.get(subject, (5 + 3 * direction, 3 * direction, 5))
    return (CSS_TEMPLATE.replace('LINE_HEIGHT', f'{line_height:g}').replace('CELL_PAD', f'{cell_pad:g}')
            .replace('P_MARGIN', f'{p_margin:g}').replace('OPTIONS_TOP', f'{options_top:g}')
            .replace('BODY_SIZE', f'{BODY_SIZE_PT.get(subject, 11):g}')
            .replace('DIR_PAD', f'{pad_left:g}').replace('DIR_INDENT', f'{indent:g}').replace('DIR_RIGHT', f'{pad_right:g}')
            .replace('DIR_SIZE', f'{direction:g}').replace('NUMBER_PITCH', f'{number_pitch(subject):g}'))


# Item geometry measured on the ROC 115 booklets of every subject: the number sits
# at the body margin and the stem and every option start 18 pt later (自然 19.5);
# option columns tab at 90 pt (five abreast), 120 (four), 150 (three) and 180 (two),
# 自然 2 pt narrower. Part headings are 13 pt, letter-spaced and stroke-bold; the
# bordered 說明 hangs its continuation lines under the text after 「說明：」 and
# breaks before the sentences the booklets start on a new line.
_subject = None  # the booklet being rendered; set by render()
NUMBER_PITCH_PT = {'自然': 19.5}
HEADING_SPACING_PT = {'國綜': 2.15, '國寫': 4.56, '英文': 4.56, '社會': 4.56, '數學A': 2.0, '數學B': 2.0, '自然': 2.4}
HEADING_SIZE_PT = {'數學A': 13.02, '數學B': 13.02, '自然': 13.02}
DIRECTION_SIZE_PT = {}
# 國寫 115 condenses the first 說明 paragraph to an 11.4 pt advance so its 41 characters
# fill line one up to 「答題卷」 and the box edge; the second paragraph is plain 12 pt.
# Text starts 5.2 pt inside the box and continuation lines hang at 40 pt.
DIRECTION_BOX_PT = {'國寫': (39.4, 34.8, 0)}   # padding-left, hanging indent, padding-right
DIRECTION_BREAKS = re.compile(r'。(?=作答使用筆尖|選擇（填）題與|選擇題與「非選擇題|選擇題使用)')


MATH_GAP_EXTRA_PT = 60


def number_pitch(subject=None):
    return NUMBER_PITCH_PT.get(subject if subject is not None else _subject, 18.0)


def option_pitch(columns, subject=None):
    subject = subject if subject is not None else _subject
    if subject == '國綜' and columns == 2:
        return 221.1  # 115 prints the second column at x 303.2 (114: 298)
    if subject == '社會' and columns in (2, 4):
        return {2: 225.0, 4: 112.6}[columns]  # 111-115: (B) at 306.8 two abreast, 194.4 four abreast
    pitch = 30 * (8 - columns) if 2 <= columns <= 5 else 0
    return pitch - (2 if subject == '自然' else 0)


def material_markup(value, inline=False):
    """國綜 reading material as 111-115 print it: 標楷體 indented 18 pt, each paragraph's first
    line 24 pt further, 「甲、」 paragraphs hanging, a lone source line at the margin."""
    if isinstance(value, dict):
        pieces = [{'rich': piece} for piece in re.split(r'(?:<br>\s*){2,}', value['rich']) if piece.strip()]
    else:
        pieces = [piece for piece in PARAGRAPH_BREAK.split(str(value)) if piece.strip()]
    rows = []
    for piece in pieces:
        plain = html.unescape(re.sub('<[^>]+>', '', piece['rich'] if isinstance(piece, dict) else piece)).strip()
        cls = 'hang' if re.match(r'[甲乙丙丁戊]、', plain) else '' if re.match(r'[（(]', plain) else 'indent'
        rows.append(f'<p class="{cls}">{text(piece)}</p>')
    return f'<div class="cn-material{" inline" if inline else ""}">' + ''.join(rows) + '</div>'


def social_material_markup(value):
    """社會 題組 material as 111-115 print it: at the margin, each paragraph's first line 24 pt
    in (115 26-27: 「在某大城市」 at x 87.8, the margin 63.8); a 甲、 or （一） line stays flush."""
    if isinstance(value, dict):
        pieces = [{'rich': piece} for piece in re.split(r'(?:<br>\s*){2,}', value['rich']) if piece.strip()]
    else:
        pieces = [piece for piece in PARAGRAPH_BREAK.split(str(value)) if piece.strip()]
    rows = []
    for piece in pieces:
        plain = html.unescape(re.sub('<[^>]+>', '', piece['rich'] if isinstance(piece, dict) else piece)).strip()
        flush = re.match(r'[甲乙丙丁戊己]、|[（(][一二三四五1-9]', plain)
        rows.append(('<p class="flush">' if flush else '<p>') + text(piece) + '</p>')
    return '<div class="social-material">' + ''.join(rows) + '</div>'


def item_gap_pt(subject):
    return typography(subject)[4]


CSS = subject_css(None)
# Long text may continue on the next page at paragraph (or solution-step)
# boundaries when a block opts in with split: paragraphs. The label/heading
# stays with the first piece; options, bank, figure and score with the last.
SPLITTABLE = {'stimulus', 'passage', 'constructed', 'solution', 'choice', 'multiple'}
PARAGRAPH_BREAK = re.compile(r'\n\s*\n|(?:<br>\s*){2,}')


class RichText(HTMLParser):
    """Only inline typographic tags; layout, images and CSS belong to components."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in {'sup','sub','i','em','b','strong','u','br'} or attrs:
            raise ValueError('Use only sup/sub/i/em/b/strong/u/br without attributes in rich text')
        self.output.append('<'+tag+'>')
        if tag != 'br': self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise ValueError('Unbalanced rich-text tags')
        self.output.append('</'+tag+'>')

    def handle_data(self, data): self.output.append(html.escape(data.translate(FULLWIDTH_MATH) if _math_mode else data))


# Official booklets set digits, Latin letters and the radical sign in Times for every
# subject; the CJK body font draws √ one em wide, so 「√5」 printed with a visible
# gap and a hosted run rewrote every radical by hand.
MATH_SUBJECTS = {'數學A', '數學B'}
LATIN_RUN = re.compile(r'[A-Za-z0-9√][A-Za-z0-9√.,()+\-−=/%:]*[A-Za-z0-9√)]|[A-Za-z0-9√]')
_latin_runs_enabled = False
_writing_mode = False
# English booklets (111-115 measured) set every Chinese line inside an item in 標楷體:
# the 47-48 and 49 directions, 「（多選題，4分）」, the translation sentences and 提示.
_item_kai = False
_measure_css = None  # the running booklet's CSS, for measuring option cells
_math_mode = False
_typesetter = None
WRITING_TASK_LINE = re.compile(r'^\s*問題[（(]')
WRITING_ASK_LINE = re.compile(r'^\s*請.{0,14}問題[：:]\s*$')
WRITING_MATERIAL_LABEL = re.compile(r'^\s*[甲乙丙丁戊]\s*$')
# A score group never breaks inside (國寫 111 wraps 「（占4分）」 whole; 數學 prints
# 「（非選擇題，8分）」): hosted papers printed 「（占」 or 「（4」 at a line end and 「分）」
# on the next. 115 國寫 does break 「（至多／19 行）」, so only scores are kept whole.
SCORE_GROUP = re.compile(r'（(?:占|(?:單選題|多選題|選填題|非選擇題)，)?(?:\s|<[^>]+>|[0-9])+分）')


def lstripped(value):
    """A leading full-width space printed as a gap after the item number (「13.　」)."""
    if isinstance(value, dict):
        return {'rich': value['rich'].lstrip(' \u3000')}
    return value.lstrip(' \u3000') if isinstance(value, str) else value


def split_tail(markup, chars=2):
    """(head, tail): tail is the last visible token, a whole top-level span or the last
    few plain characters, so it can stay on one line with what follows."""
    if markup.endswith('</span>'):
        depth = 0
        for match in reversed(list(re.finditer(r'<(/?)span\b[^>]*>', markup))):
            depth += 1 if match.group(1) else -1
            if depth == 0:
                return markup[:match.start()], markup[match.start():]
        return markup, ''
    match = re.search(r'(?:&[a-z#0-9]+;|[^<>&\s]){1,%d}$' % chars, markup)
    return (markup[:match.start()], match.group(0)) if match else (markup, '')


def no_short_last_line(markup):
    """The last three characters of a stem stay together: the booklets never end an item on
    a line of one or two characters (hosted 數B papers printed 「個？」, 「的？」 and 「元？」)."""
    if not markup or markup.endswith('</span>') or markup.endswith('>'):
        return markup
    head, tail = split_tail(markup, 3)
    if not tail or '{' in tail or '}' in tail:  # never split an {{answer}} or {{gap}} token
        return markup
    return head + f'<span style="white-space:nowrap">{tail}</span>'


def keep_scores_whole(markup):
    return SCORE_GROUP.sub(lambda m: f'<span style="white-space:nowrap">{m.group(0)}</span>', markup)


def _writing_stem(block):
    """國寫 paragraphs as the official booklets print them.

    Reading material: 楷體, first line indented two characters; a lone 甲／乙 label
    sits on its own line in an 18 pt box (113 and 115 measured), and a source line
    printed as its own paragraph stays at the margin. 「請分項回答下列問題：」 prints at the margin;
    問題（一）／（二） hang six characters (the width of 「問題（一）：」) so their
    continuation lines align under the text; the 第二大題 task paragraph is an
    ordinary indented 明體 paragraph.
    """
    value = block.get('text', '')
    if isinstance(value, dict):
        pieces = [{'rich': p} for p in re.split(r'(?:<br>\s*){2,}', value['rich']) if p.strip()]
        plains = [html.unescape(re.sub('<[^>]+>', '', p['rich'])) for p in pieces]
    else:
        pieces = [p for p in PARAGRAPH_BREAK.split(str(value)) if p.strip()]
        plains = list(pieces)
    return ''.join(_writing_paragraph(piece, plain) for piece, plain in zip(pieces, plains))


def _writing_paragraph(piece, plain):
    plain = plain.strip()
    if WRITING_MATERIAL_LABEL.match(plain):
        return f'<table class="material-label"><tr>{padded_cell(text(piece), 18, mode="center")}</tr></table>'
    if WRITING_ASK_LINE.match(plain):
        cls = 'plain'
    elif WRITING_TASK_LINE.match(plain):
        cls = 'hanging'
    elif '為題' in plain or '（占' in plain or '文長' in plain:
        cls = 'indent'
    elif re.match(r'[（(]', plain):
        cls = 'material plain'
    else:
        cls = 'material indent'
    markup = text(piece)
    if 'material' not in cls:
        markup = keep_scores_whole(markup)
    return f'<p class="{cls}">{markup}</p>'


MATH_SYMBOL = r'[−+=×÷±≤≥()\[\]αβγδθλμσφωπ·°]'
# A Latin run keeps the spaces inside and around it, so an English sentence stays one
# Times span. Spaces take the Times width everywhere: a CJK face such as 全字庫正宋體
# draws U+0020 a full em wide, which opened 「為 2/3」 and 「sin x」 like a tab.
LATIN_SPACED = rf'[ \u00a0]*(?:{LATIN_RUN.pattern})(?:[ \u00a0]+(?:{LATIN_RUN.pattern}))*[ \u00a0]*'
TEXT_RUNS = re.compile(rf'(?P<run>{LATIN_SPACED})|(?P<space>[ \u00a0]+)')
# Mathematics also sets operators, brackets and Greek letters standing between CJK text
# in Times, as the booklets do (the CJK face drew a full-width 「−」).
MATH_RUNS = re.compile(rf'(?P<run>{LATIN_SPACED})|(?P<space>[ \u00a0]+)|(?P<sym>{MATH_SYMBOL}|&lt;|&gt;|[<>≤≥≠≈|])')
FORMULA_TOKEN = rf'(?:{LATIN_SPACED}|{MATH_SYMBOL}|&lt;|&gt;|[<>≤≥≠≈|])'
FORMULA_RUN = re.compile(rf'{FORMULA_TOKEN}(?:[ \u00a0]*{FORMULA_TOKEN})*')


def unligated(markup):
    """MuPDF joins f+f/i/l of the Times face into ﬀ ﬁ ﬂ glyphs; the booklets print them
    apart (no ligature in any 111-115 English text layer), and a ligature breaks search
    and copy. A lone 「f」 span ends the run the engine would ligate."""
    parts = re.split(r'(<[^>]+>)', markup)
    return ''.join(part if part.startswith('<') else re.sub(r'f(?=[fil])', '<span>f</span>', part) for part in parts)


# Official mathematics sets 「＝＋－＜＞」 as half-width Times/Symbol operators; hosted papers
# typed the full-width forms, which the CJK face draws an em wide and which break lines.
FULLWIDTH_MATH = str.maketrans({'＝': '=', '＋': '+', '－': '−', '＜': '<', '＞': '>'})
FORMULA_OPERATOR = re.compile(r'[=+−<>≤≥≠≈×÷±]|&lt;|&gt;')
FORMULA_MAX_CHARS = 40


def keep_formulas_whole(part, wrap):
    """Mathematics: a formula such as 「30p₁ + 60q₁ = 2700」 or 「|x − 2| &lt; 3」 stays on one
    line, as in the booklets; hosted solutions broke about twenty of them at = + ≤ (."""
    out, cursor = [], 0
    for formula in FORMULA_RUN.finditer(part):
        out.append(MATH_RUNS.sub(wrap(0), part[cursor:formula.start()]))
        chunk = MATH_RUNS.sub(wrap(formula.start()), formula.group(0))
        visible = len(re.sub(r'&[a-z#0-9]+;', '.', formula.group(0).strip()))
        if FORMULA_OPERATOR.search(formula.group(0)) and visible <= FORMULA_MAX_CHARS:
            chunk = f'<span style="white-space:nowrap">{chunk}</span>'
        out.append(chunk)
        cursor = formula.end()
    out.append(MATH_RUNS.sub(wrap(0), part[cursor:]))
    return ''.join(out)


def latin_runs(markup):
    """Wrap Latin/digit/radical runs of already-escaped markup in the Latin font, leaving tags alone."""
    # Tags, entities and {{tokens}} stay untouched; mathematics keeps &lt; and &gt; inside
    # its formulas.
    entity = r'&(?!lt;|gt;)[a-z#0-9]+;' if _math_mode else r'&[a-z#0-9]+;'
    parts = re.split(rf'(<[^>]+>|{entity}|\{{\{{[^{{}}]*\}}\}})', markup)
    for index, part in enumerate(parts):
        if not part or part.startswith(('<', '&', '{{')):
            continue
        # Escaped markup printed literally (&lt;script&gt;) stays one visible token.
        if (index and parts[index - 1] == '&lt;') or (index + 1 < len(parts) and parts[index + 1] == '&gt;'):
            continue

        def wrap(match, part=part, base=0):
            chunk = match.group(0)
            if match.lastgroup == 'run' and _math_mode:
                # Variables print italic, as in every mathematics booklet; function
                # names, words and acronyms stay upright.
                chunk = identifier_markup(chunk, part, base + match.start())
            return f'<span class="latin">{unligated(chunk)}</span>'
        if _math_mode:
            parts[index] = keep_formulas_whole(part, lambda base, part=part: (lambda m: wrap(m, part, base)))
        else:
            parts[index] = TEXT_RUNS.sub(wrap, part)
    return ''.join(parts)


def text(value):
    if isinstance(value, dict) and set(value) == {'rich'}:
        parser = RichText(); parser.feed(value['rich']); parser.close()
        if parser.stack: raise ValueError('Unclosed rich-text tag')
        result = ''.join(parser.output)
        result = math_tokens(result) if _math_mode else result
        return kai_runs(latin_runs(result) if _latin_runs_enabled else result)
    if not isinstance(value, str): raise ValueError('Text must be a string or {rich: inline HTML}')
    if re.search(r'\\(?:frac|sqrt|begin|\()|\$\$', value):
        raise ValueError('Render complex math to a verified inline asset; do not print raw LaTeX')
    result = html.escape(value.translate(FULLWIDTH_MATH) if _math_mode else value).replace('\n','<br>')
    result = math_tokens(result) if _math_mode else result
    return kai_runs(latin_runs(result) if _latin_runs_enabled else result)


CJK_RUN = re.compile('[\u3000-\u303f\u3400-\u9fff\uf900-\ufaff\ufe10-\ufe4f\uff00-\uffef]+')
# Western punctuation inside an English booklet's items stays in Times: the CJK face
# draws “ ” ; ? ! and dashes full width.
WESTERN_PUNCTUATION = re.compile('[\u2018\u2019\u201c\u201d;?!\u2013\u2014\u2026]+')


def kai_runs(markup):
    if not _item_kai:
        return markup
    parts = re.split(r'(<[^>]+>|&[a-z#0-9]+;|\{\{[^{}]*\}\})', markup)
    for index, part in enumerate(parts):
        if part and not part.startswith(('<', '&', '{{')):
            part = CJK_RUN.sub(lambda m: f'<span class="kai">{m.group(0)}</span>', part)
            parts[index] = WESTERN_PUNCTUATION.sub(lambda m: f'<span class="latin">{m.group(0)}</span>', part)
    return ''.join(parts)


def gap_markup(content):
    """Numbered answer gaps: the number in Times inside a 33 pt underline (111-115)."""
    content = re.sub(r'\{\{gap:(\d{1,2})\}\}', r'<u>　<span class="latin">\1</span>　</u>', content)
    if '{{gap:' in content: raise ValueError('Invalid passage gap number')
    return content


def rail_image(number, rows):
    if not isinstance(rows,list) or not 1 <= len(rows) <= 2 or any(type(n) is not int or not 1<=n<=6 for n in rows):
        raise ValueError('Use one integer row or two fraction rows; specify other response forms as verified assets')
    width = max(rows)*28.98 + 4
    height = len(rows)*32.98 + 4
    with pymupdf.open() as doc:
        page = doc.new_page(width=width, height=height)
        ordinal = 1
        for index, count in enumerate(rows):
            # draw_rail starts row IDs at 1, so shift subsequent fraction labels
            # in this local body-only component before rasterizing.
            x = (width-count*28.98)/2
            reservation = {'bbox':[x,2+index*32.98,x+count*28.98,30.98+index*32.98]}
            if ordinal == 1:
                draw_rail(page,reservation,number,count)
            else:
                font=pymupdf.Font('tiro')
                for j in range(count):
                    cx=x+j*28.98+12.99;cy=2+index*32.98+12.99
                    label=f'{number}-{ordinal+j}';size=10.02
                    page.draw_circle((cx,cy),12.99,width=.7)
                    page.insert_text((cx-font.text_length(label,fontsize=size)/2,
                                      cy+size*(font.ascender+font.descender)/2),label,fontname='tiro',fontsize=size)
                page.draw_line((x,30.98+index*32.98),(x+count*28.98,30.98+index*32.98),width=.7)
            ordinal += count
        return page.get_pixmap(matrix=pymupdf.Matrix(4,4),alpha=True).tobytes('png'),width,height


def fragment(block, archive, asset_root, index, width=467.7, font_metric=None, scaled=None):
    """Resolve verified inline assets after ALL authored fields are escaped.

    Choices, table cells, passages and solution steps use the same substitution
    as stems. Resolving only stems silently printed formula tokens in options
    and skipped early-return blocks, forcing callers to rebuild valid layouts.
    """
    images={};image_heights={}
    # Numbered blocks print beside a 28pt number column plus cell padding.
    column_width=width-number_pitch()-4 if block.get('kind') in {'choice','multiple','constructed','solution'} else width
    for key,asset in block.get('assets',{}).items():
        path=(asset_root/asset['path']).resolve()
        if not path.is_relative_to(asset_root.resolve()): raise ValueError('Asset outside current run')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=asset['sha256']:raise ValueError('Changed body asset')
        asset_width=asset['width_pt']
        if type(asset_width) not in (int,float) or not 1<=asset_width<=460:raise ValueError('Invalid asset width')
        if asset_width>column_width:
            # A figure wider than its text column would overflow the body; print
            # it at the column width instead of failing after a full render.
            if scaled is not None:
                scaled[(index,key)]={'block':index,'asset':key,'requested_pt':asset_width,'printed_pt':round(column_width,2)}
            asset_width=column_width
        extension=path.suffix
        with pymupdf.open(stream=raw) as image_doc:
            rect=image_doc[0].rect
            if image_doc.is_pdf or extension.lower()=='.svg':
                if len(image_doc)!=1:raise ValueError('Inline body PDF asset must have exactly one page')
                # MuPDF's HTML img does not render PDF sources: without this it
                # silently prints [image]. It rasterizes SVG at about 96 dpi,
                # which printed visibly blurred lines and labels. Convert only
                # newly authored body artwork, never the immutable
                # fixed-template PDF layers.
                scale=3*asset_width/rect.width
                raw=image_doc[0].get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=True).tobytes('png')
                extension='.png'
        height=asset_width*rect.height/rect.width
        name=f'asset-{index}-{len(images)}'+extension
        archive.add((raw,name))
        images[key]=f'<img src="{html.escape(name,quote=True)}" width="{asset_width}" height="{height}">'
        image_heights[key]=height
    content=_fragment_html(block,archive,index,width,font_metric,images,image_heights)
    for key,image in images.items():
        content=content.replace(html.escape('{{asset:'+key+'}}'),image)
    if '{{asset:' in content:raise ValueError('Missing inline asset')
    if _typesetter is not None:
        content=_typesetter.tokens(content,archive)
    return _pad_option_cells(content,archive)


# Option columns sit on a fixed pitch, as the official booklets tab them (數學 five
# abreast at 90 pt, 111-115 measured). The pinned hosted PyMuPDF 1.26.0 ignores every
# table/cell width (style, attribute, percentage, fixed layout, spacer images) and
# shrank each cell to its text, so a hosted 數A printed 「(1) 6 (2) 8 (3) 9」 run
# together. Padding is honored by every version: each cell's natural advance is
# measured in the running engine with the booklet's CSS and padded to the pitch.
OPTION_CELL = re.compile(r'<td class="optcell" data-pitch="([0-9.]+)" data-alt="([0-9.]+)" data-wrap="(\w*)" data-mode="(\w*)">(.*?)</td>', re.S)
OPTION_TABLE = re.compile(r'<table class="options" style="width:auto">.*?</table>', re.S)
OPTION_MARK = 'QZXJ'
_cell_advances = {}


def padded_cell(inner, pitch, *, alt=None, wrap='', mode=''):
    """A cell the renderer pads to a measured pitch (every PyMuPDF version honours padding)."""
    return (f'<td class="optcell" data-pitch="{pitch:.2f}" data-alt="{(alt or pitch):.2f}" data-wrap="{wrap}" '
            f'data-mode="{mode}">{inner}</td>')


def _mark_positions(page, html_text, top, archive):
    page.insert_htmlbox(pymupdf.Rect(0, top, 3000, top + 180), html_text, css=_measure_css,
                        archive=archive, **HTML_OPTIONS)
    # search_for, not words: a CJK option ending 「」」 joins the marker into one word.
    return sorted(r.x0 for r in page.search_for(OPTION_MARK) if top <= r.y0 < top + 180)


def _cell_advance(inner, archive, wrap=''):
    key = (inner, wrap, _measure_css)
    if key not in _cell_advances:
        with pymupdf.open() as doc:
            page = doc.new_page(width=3000, height=400)
            mark = f'<td>{OPTION_MARK}</td>'
            opened, closed = (f'<div class="{wrap}">', '</div>') if wrap else ('', '')
            marks = _mark_positions(page, f'{opened}<table class="options" style="width:auto"><tr>{mark}<td>{inner}</td>{mark}'
                                          f'</tr></table>{closed}', 0, archive)
            pair = _mark_positions(page, f'{opened}<table class="options" style="width:auto"><tr>{mark}{mark}</tr></table>{closed}',
                                   200, archive)
        _cell_advances[key] = (marks[1] - marks[0]) - (pair[1] - pair[0]) if len(marks) == 2 and len(pair) == 2 else None
    return _cell_advances[key]


def _pad_option_cells(content, archive):
    """Pad every marked cell to its pitch; an option table keeps the official pitch only if all its options fit."""
    def advance(match):
        return _cell_advance(match.group(5), archive, match.group(3)) if _measure_css is not None else None

    def cell(match, pitch=None):
        official, alt, mode, inner = float(match.group(1)), float(match.group(2)), match.group(4), match.group(5)
        pitch = pitch or official
        width = advance(match)
        if width is None:
            return f'<td style="width:{pitch - 4:g}pt">{inner}</td>'
        if mode == 'center':
            side = max(0, (pitch - (width - 4)) / 2)
            return f'<td style="padding:0 {side:.2f}pt 0 {side:.2f}pt">{inner}</td>'
        fits = ';white-space:nowrap' if width <= pitch else ''
        # PyMuPDF 1.28 also honours a content width: it gives the content half a point of
        # room, since a box exactly as wide as its text wrapped a stacked fraction under
        # its label. 1.26 ignores the width and lays the padded cell out exactly.
        if mode == 'last':
            return f'<td style="padding-right:4pt;width:{width - 3:.2f}pt{fits}">{inner}</td>'
        # Half a point of slack, and an option that fits its pitch never wraps: the
        # engine otherwise shrank a nearly full row and broke 「(B) donation」 in two.
        room = f';width:{width - 3.5:.2f}pt' if width <= pitch else ''
        return f'<td style="padding-right:{max(4, 4 + pitch - width - .5):.2f}pt{room}{fits}">{inner}</td>'

    def table(match):
        cells = [m for m in OPTION_CELL.finditer(match.group(0)) if m.group(4) != 'number']
        widths = [advance(m) for m in cells]
        official = {float(m.group(1)) for m in cells}
        fits = all(w is not None and w <= float(m.group(1)) for m, w in zip(cells, widths)
                   if m.group(4) != 'last')
        chosen = None if fits else max((float(m.group(2)) for m in cells), default=None)
        return OPTION_CELL.sub(lambda m: cell(m, None if m.group(4) == 'number' else chosen), match.group(0))

    content = OPTION_TABLE.sub(table, content)
    return OPTION_CELL.sub(cell, content)


def _group_label(block):
    if not block.get('group_label') or not block.get('_head', True):
        return ''
    style = block.get('group_label_style', 'bold')
    if style not in {'bold', 'underline', 'plain'}: raise ValueError('group_label_style must be bold, underline or plain')
    global _item_kai
    kai, _item_kai = _item_kai, False  # 「第 47 至 50 題為題組」 is 明體 (115 measured)
    try:
        label = text(block["group_label"])
    finally:
        _item_kai = kai
    return f'<div class="group-label{" underline" if style=="underline" else " plain" if style=="plain" else ""}">{label}</div>'


def _fragment_html(block, archive, index, width, font_metric, images, image_heights):
    kind=block.get('kind')
    if kind not in KINDS: raise ValueError('Unknown body block kind')
    head,tail=block.get('_head',True),block.get('_tail',True)
    global _item_kai
    _item_kai=_subject=='英文' and kind not in {'section','solution'}
    if kind=='section':
        heading=f'<div class="heading">{heading_markup(block["title"],archive)}</div>'
        # Answer booklets may print a plain part heading; question-booklet
        # directions stay explicit and are never invented here.
        if 'directions' not in block:return heading
        notes=DIRECTION_BREAKS.sub("。<br>",plain_text(block["directions"]))
        if _subject=='國寫' and '<br>' in notes:
            first,rest=notes.split('<br>',1)
            notes=f'<span style="font-size:11.4pt">{first}</span><br>{rest}'
        return heading+f'<div class="direction">{notes}</div>'
    if kind=='passage':
        paragraphs=block.get('paragraphs',[])
        if not paragraphs:raise ValueError('Passage needs actual paragraphs')
        writing=_writing_mode and block.get('language')!='en'
        def paragraph(value):
            plain=value['rich'] if isinstance(value,dict) else value
            if writing:
                # 國寫 materials print in 楷體 whichever block carries them: a passage
                # once fell back to the 明體 body face because only stems were classified.
                return _writing_paragraph(value,html.unescape(re.sub('<[^>]+>','',str(plain))))
            # Source lines and option/bank rows are never first-line indented.
            indent=block.get('indent') and not re.match(r'\s*[(（]',str(plain))
            if re.match(r'\s*\([A-J]\)\s',str(plain)):
                return '<p class="hang">'+text(value)+'</p>'  # a lettered candidate hangs under its text
            return ('<p class="indent">' if indent else '<p>')+text(value)+'</p>'
        content=''.join(paragraph(p) for p in paragraphs)
        content=gap_markup(content)
        cls='english' if block.get('language')=='en' else 'writing' if writing else 'passage'
        heading=f'<div class="heading">{text(block["heading"])}</div>' if block.get('heading') and head else ''
        if writing and heading:heading=f'<p class="part">{heading_markup(block["heading"],archive,spacing=0)}</p>'
        bank=block.get('bank',[]) if tail else []
        if bank:
            columns=block.get('columns',2)
            if columns not in (1,2,5):raise ValueError('Unsupported option-bank columns')
            if columns==1:
                # Candidate sentences hang under their text when they wrap.
                content+=''.join('<p class="hang">'+bank_entry(o)+'</p>' for o in bank)
            else:
                # PyMuPDF 1.26 ignores cell widths: pad each cell to the official pitch
                # (the 115 bank tabs every 96 pt from the margin, five abreast).
                pitch=96 if columns==5 else width/columns
                cells=[padded_cell(bank_entry(o),pitch,alt=width/columns,wrap='english' if block.get('language')=='en' else '',
                                   mode='last' if (i+1)%columns==0 or i==len(bank)-1 else '') for i,o in enumerate(bank)]
                content+=('<table class="options" style="width:auto">'
                          +''.join('<tr>'+''.join(cells[i:i+columns])+'</tr>' for i in range(0,len(cells),columns))+'</table>')
        return _group_label(block)+heading+f'<div class="{cls}">{content}</div>'
    if kind=='table':
        headers=block.get('headers',[]);rows=block.get('rows',[])
        if not headers or not rows or any(len(r)!=len(headers) for r in rows):
            raise ValueError('Table rows must match nonempty headers')
        content='<tr>'+''.join('<th>'+text(c)+'</th>' for c in headers)+'</tr>'
        content+=''.join('<tr>'+''.join('<td>'+text(c)+'</td>' for c in r)+'</tr>' for r in rows)
        return '<p>'+text(block.get('text',''))+'</p><table class="data">'+content+'</table>'
    numbered=type(block.get('number')) is int and block['number']>=1
    if kind!='stimulus' and not numbered and not (kind in {'choice','multiple','constructed','solution'} and 'label' in block):
        raise ValueError('Supply a positive integer question number, or a printed label for an unnumbered task')
    stem=gap_markup(keep_scores_whole(text(lstripped(block.get('text','')))))
    if kind in {'choice','multiple','constructed','fill'} and not _writing_mode:
        stem=no_short_last_line(stem)
    if kind=='constructed' and _writing_mode:
        stem=_writing_stem(block)
    if block.get('material') is True and kind=='stimulus':
        stem=material_markup(block.get('text',''))
    elif kind=='stimulus' and _subject=='社會' and re.sub(r'<[^>]+>|\s','',str((block.get('text') or {}).get('rich','') if isinstance(block.get('text'),dict) else block.get('text') or '')):
        stem=social_material_markup(block['text'])
    elif block.get('material') and head:
        stem+=material_markup(block['material'],inline=True)  # already in the item's text column
    if kind=='solution':
        steps=block.get('steps')
        if not steps:raise ValueError('Supply actual authored solution steps')
        stem=''.join('<p>'+text(p)+'</p>' for p in [*([block.get('text','')] if head else []),*steps])
    if kind=='fill':
        if stem.count('{{answer}}')!=1: raise ValueError('Place exactly one {{answer}} at the semantic answer position')
        data,w,h=rail_image(block['number'],block['rows'])
        name=f'rail-{index}.png';archive.add((data,name))
        before,after=stem.split('{{answer}}')
        # Use paragraph flow: MuPDF top-aligned table cells paint their inline
        # image below the text despite a valid non-colliding bounding box.
        rail=f'<img src="{name}" width="{w}" height="{h}" style="vertical-align:middle">'
        # The grid never starts a line alone or leaves 「。」 for the next one: it keeps
        # the token before it (「Q =」, 「為」) and the punctuation after it (hosted 數B
        # papers dropped 13, 14 and 17's grids to a new line with a lone 「。」).
        head,tail=split_tail(before)
        lead=re.match(r'(?:[。，、．.；：）)！？]|<span class="latin">[.,;:)]+</span>)*',after).group(0)
        stem=head+f'<span style="white-space:nowrap">{tail}{rail}{lead}</span>'+after[len(lead):]
    elif '{{answer}}' in stem: raise ValueError('Answer position token requires a fill block')
    if 'label' in block:
        label=text(block['label']) if head else ''
    elif kind=='solution':
        label=f'第{block["number"]}題'
    else:
        label=f'{block["number"]}.' if head and numbered else ''
    if kind=='constructed':
        score=block.get('score')
        if type(score) not in (int,float) or score<=0:raise ValueError('Constructed response must show its actual positive score')
        if block.get('score_in_text'):
            # The authored text already prints the official score wording,
            # possibly the whole printed question's total across subparts.
            printed_score=block.get('printed_score',score)
            if not block.get('_score_checked') and not re.search(rf'(?<![0-9.]){printed_score:g}\s*分',html.unescape(re.sub('<[^>]+>','',stem))):
                raise ValueError('score_in_text requires the printed text to state the actual score')
        elif tail and not block.get('english_task'):
            # The score closes the item text, before any figure or response area.
            stem+=f'<span class="score">（{score:g}分）</span>'
        if block.get('english_task'):
            stem=english_task_markup(block,label if head else '',stem)
    if block.get('subpart'):
        # （1）（2） hang their continuation lines under their text (115: label x 82.1, text 112.1).
        lead=f'<p style="margin:0">{keep_scores_whole(text(block["lead"]))}</p>' if block.get('lead') and head else ''
        stem=lead+f'<p class="subpart">{text(block["subpart"]) if head else ""}{stem}</p>'
    if block.get('answer_line') and tail:
        # 簡答 50 (113-115): one ruled line of Times underscores across the item column.
        count=int((width-number_pitch()-8)/5.52)
        stem+=f'<p style="margin:2pt 0 0 4pt"><span class="latin">{"_"*count}</span></p>'
    figure=block.get('figure') if tail else None
    column=kind in {'choice','multiple','constructed'}
    if figure:
        if figure not in images:raise ValueError('Figure must name a hash-verified asset')
        image_box=f'<div style="line-height:{image_heights[figure]+FIGURE_LEADING_PT:g}pt">{images[figure]}</div>'
        if block.get('figure_caption'):
            image_box+=f'<div class="figcaption">{text(block["figure_caption"])}</div>'
        if block.get('figure_position','below')=='right':
            if kind=='fill':raise ValueError('Fill figures use below placement; keep answer rails in paragraph flow')
            if block['assets'][figure]['width_pt']>180:raise ValueError('Right-hand figure exceeds reserved column')
            # Numbered items keep their hanging number column beside the pair.
            text_width=width-189-(number_pitch() if column else 0)
            stem=f'<table><tr><td style="width:{text_width:g}pt">{stem}</td><td style="width:185pt" class="figure">{image_box}</td></tr></table>'
        elif kind=='fill':
            stem=numbered_row(label,stem,width)+f'<div class="figure">{image_box}</div>'
        else:stem+=f'<div class="figure">{image_box}</div>'
    option_block=''
    if kind in {'choice','multiple'} and tail:
        options=block.get('options',[])
        if len(options)<2:raise ValueError('Choice block needs authored options')
        columns=block.get('columns',1)
        if columns not in OPTION_COLUMNS:raise ValueError('Use 1-5 option columns; never shrink font to fit')
        if not stem.strip() and not figure and head:
            # Option-only rows (English cloze): the number shares the first
            # option row so both sit on one baseline.
            wrap='english' if block.get('language')=='en' else ''
            inners=[f'<span class="latin">{html.escape(str(o["label"]))}\u00a0</span>{text(o["text"])}' for o in options]
            columns=english_columns(inners,columns,archive,wrap,width)
            alt=(width-number_pitch())/columns
            cells=[padded_cell(inner,option_pitch(columns) if columns>2 else alt,alt=alt,wrap=wrap,
                               mode='last' if (j+1)%columns==0 or j==len(options)-1 else '') for j,inner in enumerate(inners)]
            rows=[''.join(cells[j:j+columns]) for j in range(0,len(cells),columns)]
            result=('<table class="options" style="width:auto">'+''.join(
                f'<tr>{padded_cell(label if n==0 else "",number_pitch(),wrap=wrap,mode="number")}{row}</tr>'
                for n,row in enumerate(rows))+'</table>')
            return f'<div class="english">{result}</div>' if block.get('language')=='en' else result
        # Never nest the option table inside the stem cell: MuPDF's HTML engine
        # shrank that nested table to the stem's width in a hosted runtime, so a
        # 國綜 booklet wrapped every option at 40% of the page. Options print as a
        # sibling block: paragraphs for one column, a top-level table otherwise.
        rows=[f'<span class="latin">{html.escape(str(o["label"]))}\u00a0</span>{text(o["text"])}' for o in options]
        wrap='english' if block.get('language')=='en' else ''
        if columns>1:
            columns=english_columns(rows,columns,archive,wrap,width)
        if columns==1:
            option_block='<div class="optionlist">'+''.join(f'<p>{row}</p>' for row in rows)+'</div>'
        else:
            alt=(width-number_pitch())/columns
            cells=[padded_cell(row,option_pitch(columns) if columns>2 or _subject!='英文' else alt,alt=alt,wrap=wrap,
                               mode='last' if (j+1)%columns==0 or j==len(rows)-1 else '') for j,row in enumerate(rows)]
            option_block=(f'<div class="optionlist"><table class="options" style="width:auto">'
                          +''.join('<tr>'+''.join(cells[j:j+columns])+'</tr>' for j in range(0,len(cells),columns))+'</table></div>')
    if kind=='solution':
        result=(f'<div class="heading">{label}</div>' if head else '')+stem
    elif kind=='fill':
        result=stem if figure else numbered_row(label,stem,width)
    elif kind=='stimulus':
        result=_group_label(block)+stem
    elif kind=='constructed' and block.get('english_task'):
        result=stem
    elif kind=='constructed' and _writing_mode:
        # 國寫 prints no number column: 「一、」 stands on its own line above the material.
        result=(f'<p class="part">{heading_markup(html.unescape(re.sub("<[^>]+>","",label)),archive,spacing=0)}</p>' if label else '')+stem
    else:
        # An explicit stem width keeps option rows full width when the stem is
        # empty (English cloze option rows print only their number).
        # The 24 pt number column holds "12." or "（一）"; a longer label such
        # as 英文作文 would stack one glyph per line, so it leads the text instead.
        plain_label=html.unescape(re.sub('<[^>]+>','',label))
        if RANGE_LABEL.fullmatch(plain_label):
            # 「47-48」 (英文 112-115) prints in Times at the margin; its text hangs 27.9 pt in.
            result=numbered_row(f'<span class="latin">{html.escape(plain_label)}</span>',stem,width,pitch=27.9)+option_block
            return f'<div class="english">{result}</div>' if block.get('language')=='en' else result
        if len(plain_label)>3:
            stem=f'<b>{label}</b>　'+stem;label=''
        result=numbered_row(label,stem,width)+option_block
    return f'<div class="english">{result}</div>' if block.get('language')=='en' else result


def plain_text(value):
    """Instructions: Latin runs in Times but no variable italics or typeset fractions (「2B鉛筆」)."""
    global _math_mode
    mode, _math_mode = _math_mode, False
    try:
        return text(value)
    finally:
        _math_mode = mode


def numbered_row(label, stem, width, pitch=None):
    """Number at the margin, text and options on the measured stem line (18 pt later)."""
    pitch = pitch or number_pitch()
    if re.fullmatch(r'[\w.()（）]+', html.unescape(re.sub('<[^>]+>', '', label or ''))) and label.isascii():
        label = f'<span class="latin">{label}</span>'
    if not html.unescape(re.sub('<[^>]+>', '', label or '')).strip():
        # PyMuPDF 1.26 drops an empty cell with its padding: a hosted 國綜 printed 32（2） and a
        # continued item's next page at the margin, 18 pt left of （1）. A no-break space
        # keeps the number column, padded to the same pitch as a printed number.
        label = '&nbsp;'
    return (f'<table><tr>{padded_cell(label, pitch, mode="number")}'
            f'<td style="width:{width-pitch:g}pt">{stem}</td></tr></table>')


RANGE_LABEL = re.compile(r'\d{1,2}\s*[-–]\s*\d{1,2}')
HINT_LABEL = re.compile(r'^((?:<span class="kai">)?)提示[：︰]')


def english_columns(inners, columns, archive, wrap, width):
    """Columns that hold every option on one line at the official tab.

    英文: a row of four whose longest choice overruns its 120 pt tab breaks into two columns
    of two, as 115 prints 17 (had yet to develop) and 20 (an intimate romantic dinner) with
    (B) and (D) at the half-width tab. 數學A/B 111-115 print options five abreast or one per
    line (once three and two, all short); a hosted 數A paper set 13-15-character options
    three abreast and wrapped 「相／等」 and a fraction inside their cells, so options that
    overrun their tab print one per line."""
    minimum = 3 if _subject == '英文' else 2 if _subject in {'數學A', '數學B'} else None
    if minimum is None or columns < minimum or _measure_css is None:
        return columns
    widths = [_cell_advance(inner, archive, wrap) for inner in inners]
    if any(w is None for w in widths):
        return columns
    pitch = option_pitch(columns)
    last = width - number_pitch() - (columns - 1) * pitch  # the right column ends at the margin
    if all(w <= (last if (j + 1) % columns == 0 else pitch) for j, w in enumerate(widths)):
        return columns
    return 2 if _subject == '英文' else 1


def bank_entry(option):
    return f'<span class="latin">{html.escape(str(_plain(option["label"])))}\u00a0</span>{text(option["text"])}'


def english_task_markup(block, label, stem):
    """英文 中譯英 and 作文 as 111-115 print them: 「1.」 in Times followed by the 楷體
    sentence, and 「提示︰」 at 9.96 pt with the prompt hanging under its text. Neither
    prints a score or a number column."""
    if block['english_task'] == 'composition':
        body = HINT_LABEL.sub(lambda m: f'{m.group(1)}<span style="font-size:9.96pt">提示︰</span>', stem, count=1)
        return f'<p class="hint">{body}</p>' if body != stem else f'<p class="task">{stem}</p>'
    plain = html.unescape(re.sub('<[^>]+>', '', label or '')).strip()
    number = f'<span class="latin">{html.escape(plain)}\u00a0</span>' if plain else ''
    return f'<p class="task">{number}{stem}</p>'


def _plain(value):
    raw = value['rich'] if isinstance(value, dict) else str(value)
    return html.unescape(re.sub(r'<[^>]+>', '', raw))


def heading_markup(value, archive, spacing=None):
    """Part headings as the booklets set them: 13 pt, letter-spaced, stroke-bold."""
    plain = _plain(value).strip()
    if _typesetter is None or archive is None or not plain or '\n' in plain or '{{' in plain:
        return text(value)
    size = HEADING_SIZE_PT.get(_subject, 12.96)
    gap = HEADING_SPACING_PT.get(_subject, 2.0) if spacing is None else spacing
    return _typesetter.heading(plain, size, gap, archive)


def _units(block):
    """Paragraph/step units of a block that opted into page continuation."""
    if block.get('split')!='paragraphs' or block['kind'] not in SPLITTABLE:
        return None,[]
    if block['kind']=='passage':
        return 'paragraphs',list(block.get('paragraphs',[]))
    if block['kind']=='solution':
        return 'steps',list(block.get('steps',[]))
    if block.get('figure'):
        return None,[]  # A figure keeps its measured place with the item.
    value=block.get('text','')
    rich=isinstance(value,dict)
    pieces=[piece for piece in PARAGRAPH_BREAK.split(value['rich'] if rich else value) if piece.strip()]
    if rich:
        try:
            for piece in pieces:text({'rich':piece})
        except ValueError:
            return None,[]  # An inline tag spanning paragraphs cannot be divided.
        pieces=[{'rich':piece} for piece in pieces]
    return 'text',pieces


def _chunk(block,key,units,head,tail):
    chunk={k:v for k,v in block.items() if k!='keep_with_next' or tail}
    chunk.update(_head=head and block.get('_head',True),_tail=tail and block.get('_tail',True),_score_checked=True)
    if key=='text':
        if isinstance(units[0],dict):
            chunk['text']={'rich':'<br><br>'.join(unit['rich'] for unit in units)}
        else:
            chunk['text']='\n\n'.join(units)
    else:
        chunk[key]=units
    return chunk


def render(spec, output, layout_path, font, *, asset_root, proof=False, reading_font=None,
           balance_last_page=True, progress_path=None, kai_font=None):
    started=time.monotonic()
    if output.exists() or layout_path.exists():raise ValueError('Use new output names; preserve previous reviewable bytes')
    if spec.get('purpose')=='layout-reference-only' and not proof:raise ValueError('Placeholder gallery cannot become a production exam')
    if not proof and any(str(b.get('id','')).startswith('layout-') for b in spec.get('blocks',[])):
        raise ValueError('Placeholder gallery IDs cannot become production questions')
    manifest=json.loads(DEFAULT_MAP.read_text(encoding='utf-8'))
    subject=next(s for s in manifest['subjects'] if s['subject']==spec['subject'])
    global _latin_runs_enabled, _writing_mode, _measure_css, _math_mode, _typesetter, _subject
    # Official booklets set digits and Latin letters in Times for every subject
    # (國綜, 社會, 自然, 英文 and 數學 all measured); the CJK face keeps the CJK glyphs.
    _latin_runs_enabled = True
    _writing_mode = spec['subject'] == '國寫'
    _math_mode = spec['subject'] in {'數學A', '數學B'}
    _subject = spec['subject']
    _typesetter = Typesetter(font, size=BODY_SIZE_PT.get(spec['subject'], 11))
    allowed=pymupdf.Rect(subject['overlay_geometry_pt']['body'])
    # Text starts on the measured official margins (the number of item 1 at x 63.8).
    body=allowed+(.05,4,-.3,-4)
    archive=pymupdf.Archive();archive.add((font.read_bytes(),'body-font.ttf'))
    archive.add((pymupdf.Font('tiro').buffer,'latin-font.ttf'))
    archive.add((pymupdf.Font('tiit').buffer,'latin-italic.ttf'))
    css=(subject_css(spec['subject'])+'\n@font-face {font-family:Latin;src:url(latin-font.ttf)}'
         '\n@font-face {font-family:LatinItalic;src:url(latin-italic.ttf)}')
    if reading_font:
        archive.add((reading_font.read_bytes(),'reading-font.ttf'))
        css+='\n@font-face {font-family:Reading;src:url(reading-font.ttf)}'
    if kai_font:
        archive.add((Path(kai_font).read_bytes(),'kai-font.ttf'))
        css+='\n@font-face {font-family:Kai;src:url(kai-font.ttf)}'
    if not spec['blocks']:raise ValueError('No authored blocks')
    _measure_css=css
    font_metric=pymupdf.Font(fontfile=str(font))
    blocks=[]
    for index,block in enumerate(spec['blocks']):
        if block['kind']!='section':
            ids=block.get('ids') or [block['id']]
            if len(ids)!=1:raise ValueError('Assign a shared block one owner ID; list other printed items in covers')
            covers=block.get('covers',[])
            if (not isinstance(covers,list) or len(set(covers))!=len(covers) or ids[0] in covers or
                    any(not isinstance(item,str) or not item.strip() for item in covers)):
                raise ValueError(f'Block {index}: covers must list other distinct item IDs printed in this block')
        blocks.append({**block,'_source':index})
    prepared={};scaled={}
    measurements=[]

    def prepare(block):
        """Measure a whole block or piece once with the SAME engine, width and font.

        Production painting never clips, scales, or estimates height from lines.
        A block taller than a page reports infinite height so it can continue.
        """
        # Content key, not id(): discarded trial pieces must never alias.
        key=json.dumps(block,sort_keys=True,ensure_ascii=False)
        if key in prepared:return prepared[key]
        index=block['_source']
        if progress_path:
            progress_path.write_text(json.dumps({'block':index,'question_id':block.get('id'),
                'operation':'measure full-page block','available_height_pt':body.height,
                'assets':block.get('assets',{})}),encoding='utf-8')
        content=fragment(block,archive,asset_root,index,body.width,font_metric,scaled)
        # A grafted source PDF must stay immutable: MuPDF caches its xref map.
        measured=pymupdf.open()
        measurements.append(measured)
        sample=measured.new_page(width=595.28,height=841.89)
        spare,scale=sample.insert_htmlbox(body,content,css=css,archive=archive,scale_low=1,**HTML_OPTIONS)
        if spare<0 or scale!=1:
            prepared[key]=(content,0,math.inf)
            return prepared[key]
        # Fractions, radicals, accents and headings reserved in the flow are painted
        # now, at the positions the engine gave their placeholders.
        sample=_typesetter.paint(sample,content)
        native=sample.get_text('dict')['blocks']
        for text_block in sample.get_text('rawdict')['blocks']:
            for line in text_block.get('lines',[]):
                for span in line['spans']:
                    for left,right in zip(span['chars'],span['chars'][1:]):
                        if (all(0x4e00<=ord(c['c'])<=0x9fff for c in (left,right)) and
                            abs(left['origin'][1]-right['origin'][1])<.1 and
                            right['origin'][0]-left['origin'][0]<span['size']*.75):
                            raise ValueError('Font collapses adjacent CJK glyph advances; use a verified compatible font')
        ink=[pymupdf.Rect(b['bbox']) for b in native]
        if any(not allowed.contains(rect) for rect in ink):
            raise ValueError(f'Block {index}: actual painted content exceeds the body')
        images=[pymupdf.Rect(b['bbox']) for b in native if b['type']==1]
        spans=[pymupdf.Rect(s['bbox']) for b in native for line in b.get('lines',[]) for s in line['spans']]
        if any((a & b).width>1 and (a & b).height>1 for a in images for b in spans):
            raise ValueError(f'Block {index}: image overlaps actual text; use a reserved figure block')
        top=min(0,min((r.y0-body.y0 for r in ink),default=0))-1
        # Retain the actual measured page. Painting reuses these glyphs and images
        # at 1:1 scale instead of asking HTML exact-fit to lay them out again.
        prepared[key]=(measured,top,max(20,body.height-spare,max((r.y1-body.y0+2 for r in ink),default=0)))
        return prepared[key]

    def split_to_fit(block,available):
        """Largest leading paragraphs that fit; None keeps the block whole."""
        key,units=_units(block)
        # A short remainder is left blank rather than stranding one line.
        if available<body.height*.12:
            return None
        # `split_keep_tail`: the last n units never part (國寫 問題（一） stays with 問題（二）).
        last=len(units)-max(1,int(block.get('split_keep_tail') or 1))
        for count in range(last,0,-1):
            first=_chunk(block,key,units[:count],True,False)
            if prepare(first)[2]<=available:
                return [first,_chunk(block,key,units[count:],False,True)]
        return None

    # Official 數學 pages leave working room between items (111-115 median gap about 52 pt,
    # upper quartile 72-83 pt); the renderer's 12 pt gap piled every blank at the page foot.
    spread=spec['subject'] in {'數學A','數學B'} and not any(b.get('kind')=='solution' for b in spec['blocks'])

    def paginate(tightness,capacity=None):
        """One pagination pass. Gaps scale with tightness; `capacity` breaks pages early to spread content evenly."""
        def gap_after(block):
            return (8 if block['kind']=='section' else item_gap_pt(spec['subject']))*tightness

        work=list(blocks)
        parts=[];pages=[];pending=[]

        def close_page():
            """Place the page's measured blocks; mathematics question pages share their
            leftover space among the item gaps, as the booklets leave working room."""
            if not pending:
                return
            extras=[0.0]*len(pending)
            bottom=pending[-1]['y']+pending[-1]['used']
            void=(body.y1-bottom)/body.height
            gaps=[n for n in range(len(pending)-1)
                  if pending[n]['block']['kind']!='section' and not pending[n]['block'].get('keep_with_next')]
            limit=page_void_limit(spec['subject'],'body',False)
            if spread and gaps and (limit is None or void<=limit):
                # Whole grid steps, so a moved block keeps the crop it had on the grid.
                share=math.floor(min(MATH_GAP_EXTRA_PT,(body.y1-bottom)/len(gaps))/BLOCK_GRID_PT)*BLOCK_GRID_PT
                for n in gaps:extras[n+1]=share
            shift_total=0.0
            for row,extra in zip(pending,extras):
                shift_total+=extra
                place(row['page'],row['block'],row['measured'],row['block_top'],row['used'],row['y']+shift_total,row['number'])
            pending.clear()

        def place(page,block,measured,block_top,used,y,number):
            shift=y-body.y0
            page.show_pdf_page(pymupdf.Rect(0,shift,595.28,841.89+shift),
                               measured,0,keep_proportion=False)
            # Crop edges on the same grid avoid partial-pixel clip noise.
            box=[math.floor(allowed.x0/BLOCK_GRID_PT)*BLOCK_GRID_PT,
                 math.floor((y+block_top)/BLOCK_GRID_PT+1e-9)*BLOCK_GRID_PT,
                 math.ceil(allowed.x1/BLOCK_GRID_PT)*BLOCK_GRID_PT,
                 snap_block_top(y+used)]
            piece='whole' if block.get('_head',True) and block.get('_tail',True) else (
                'first' if block.get('_head',True) else 'last' if block.get('_tail',True) else 'middle')
            if block['kind']!='section':
                owner=(block.get('ids') or [block['id']])[0]
                covers=sorted(block.get('covers',[]))
                previous=parts[-1] if parts else None
                if (previous and pages and pages[-1]['kind']!='section' and previous['page']==number and
                        previous['id']==owner and previous.get('covers',[])==covers):
                    # One crop per owner per page: shared material and its
                    # item, or paragraphs continued on the same page.
                    previous['bbox']=[min(previous['bbox'][0],box[0]),min(previous['bbox'][1],box[1]),
                                      max(previous['bbox'][2],box[2]),max(previous['bbox'][3],box[3])]
                    previous['components'].append({'role':'flow-content','bbox':box})
                else:
                    part={'id':owner,'page':number,'bbox':box,'components':[{'role':'flow-content','bbox':box}]}
                    if covers:part['covers']=covers
                    parts.append(part)
            pages.append({'block':block['_source'],'kind':block['kind'],'piece':piece,'page':number,'bbox':box,
                          'id':block.get('id'), 'measured_height_pt':used,
                          'keep_with_next':bool(block.get('keep_with_next') or block['kind']=='section'),
                          'remaining_height_pt':body.y1-(y+used)})

        with pymupdf.open() as doc:
            top=snap_block_top(body.y0)
            page=doc.new_page(width=595.28,height=841.89);y=top
            fresh_page=True
            i=0
            while i<len(work):
                y=snap_block_top(y)
                chain=[work[i]]
                while chain[-1]['kind']=='section' or chain[-1].get('keep_with_next'):
                    if i+len(chain)==len(work):raise ValueError('A kept heading or block must precede content')
                    chain.append(work[i+len(chain)])
                heights=[prepare(block)[2] for block in chain]
                # A kept block may start up to one grid step lower.
                required=sum(heights)+sum(gap_after(block)+BLOCK_GRID_PT for block in chain[:-1])
                # Even-fill passes stop at the capacity line unless the page is still
                # empty; a block that fits the real page is never pushed off it.
                bound=body.y1 if capacity is None or fresh_page else min(body.y1,top+capacity)
                if y+required>bound:
                    # Fill this page with leading paragraphs of the first block in
                    # the kept chain that allows continuation, instead of leaving
                    # a terminal void or failing on an over-long block.
                    offset=0;split=None
                    for position,block in enumerate(chain):
                        if _units(block)[1]:
                            split=split_to_fit(block,bound-y-offset)
                            if split:
                                work[i+position:i+position+1]=split
                            break
                        if heights[position]==math.inf:break
                        offset+=heights[position]+gap_after(block)+BLOCK_GRID_PT
                    if split:continue
                    if not fresh_page:
                        close_page()
                        page=doc.new_page(width=595.28,height=841.89);y=top;fresh_page=True
                        continue
                    if math.inf in heights:
                        raise ValueError(f'Block {chain[heights.index(math.inf)]["_source"]} exceeds a page; explicitly split its continuation')
                    raise ValueError('Section and following item exceed page; split the item explicitly')
                block=work[i]
                measured,block_top,used=prepare(block)
                if progress_path:
                    progress_path.write_text(json.dumps({'block':block['_source'],'question_id':block.get('id'),
                        'operation':'place measured block','remaining_height_pt':body.y1-y,
                        'block_height_pt':used}),encoding='utf-8')
                pending.append({'page':page,'block':block,'measured':measured,'block_top':block_top,'used':used,
                                'y':y,'number':len(doc)})
                y+=used+gap_after(block)
                fresh_page=False
                i+=1
            close_page()
            last=max(row['bbox'][3] for row in pages if row['page']==len(doc))
            return doc.tobytes(garbage=4,deflate=True),parts,pages,len(doc),(last-top)/body.height

    def voids(pages_,count_):
        return [round((body.y1-max(row['bbox'][3] for row in pages_ if row['page']==n))/body.height,3) for n in range(1,count_+1)]

    def over_limit(voids_):
        limits=[page_void_limit(spec['subject'],'solutions' if spec.get('booklet_role')=='solutions' else 'body',n==len(voids_))
                for n in range(1,len(voids_)+1)]
        return sum(1 for v,l in zip(voids_,limits) if l is not None and v>l),max(voids_) if voids_ else 0

    try:
        raw,parts,pages,count,fill=paginate(1)
        tightness=1;pagination='greedy'
        if balance_last_page and count>1 and fill<TRAILING_PAGE_FILL:
            # A last page holding a line or two fails the density check and costs
            # a rewrite; closer block spacing may pull it back onto earlier pages.
            for trial in TIGHTER_GAPS:
                attempt=paginate(trial)
                if attempt[3]<count:
                    raw,parts,pages,count,fill=attempt;tightness=trial;pagination='tighter-gaps'
                    break
        best_voids=voids(pages,count)
        if balance_last_page and count>1 and over_limit(best_voids)[0]:
            # Greedy filling piles every remainder onto the last page and leaves a
            # tall block's page half empty. Spread the same content evenly across
            # the same number of pages and keep the pass with the fewest pages
            # over the fixed limit, then the smallest worst void.
            used=sum(row['measured_height_pt'] for row in pages)+sum(
                (8 if row['kind']=='section' else item_gap_pt(spec['subject']))*tightness for row in pages)
            best=(over_limit(best_voids),count)
            for slack in (1.02,1.05,1.08,1.12):
                attempt=paginate(tightness,capacity=used/count*slack)
                if attempt[3]>count:continue
                candidate=(over_limit(voids(attempt[2],attempt[3])),attempt[3])
                if candidate<best:
                    raw,parts,pages,count,fill=attempt;best=candidate;pagination=f'balanced-{slack:g}'
                    best_voids=voids(pages,count)
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(raw)
    finally:
        for measured in measurements:measured.close()
    layout={'pdf_sha256':hashlib.sha256(raw).hexdigest(),'parts':parts,'blocks':pages,
            'measurement_count':len(prepared), 'paint_basis':'reuse measured PDF blocks at full scale',
            'page_plan':{'body_bbox':list(body),'page_count':count,
                         'pages':[{'page':n,'question_ids':list(dict.fromkeys(
                             p['id'] for p in parts if p['page']==n)),
                             'bottom_safety_pt':round(body.y1-max(b['bbox'][3] for b in pages if b['page']==n),3)}
                             for n in range(1,count+1)]},
            'gap_scale':tightness,'pagination':pagination,'bottom_void_ratios':best_voids,
            'scaled_assets':[scaled[key] for key in sorted(scaled)],
            'scope':'Body layout only; compose onto original fixed PDFs and perform actual QA',
            'elapsed_seconds':round(time.monotonic()-started,3)}
    layout_path.parent.mkdir(parents=True,exist_ok=True)
    layout_path.write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
    return layout


def guarded_render(spec, output, layout_path, font, *, asset_root, proof=False,
                   reading_font=None, balance_last_page=True, timeout=20, kai_font=None):
    """Bound native renderer stalls in a disposable process, including on Windows.

    Each measured/placed block renews the deadline. Never shrink or certify a
    timed-out block; report its ID and dimensions for a focused repair/proof.
    """
    if timeout <= 0 or not math.isfinite(timeout):
        raise ValueError('Render timeout must be positive and finite')
    if Path(output).exists() or Path(layout_path).exists():
        raise ValueError('Use new output names; preserve previous reviewable bytes')
    with tempfile.TemporaryDirectory(prefix='exam-render-') as directory:
        scratch=Path(directory)
        spec_path=scratch/'spec.json';progress=scratch/'progress.json'
        spec_path.write_text(json.dumps(spec,ensure_ascii=False),encoding='utf-8')
        command=[sys.executable,str(Path(__file__).resolve()),str(spec_path),
                 '--output',str(Path(output).resolve()),'--layout',str(Path(layout_path).resolve()),
                 '--font',str(Path(font).resolve()),'--asset-root',str(Path(asset_root).resolve()),
                 '--progress',str(progress)]
        if proof:command.append('--proof')
        if reading_font:command.extend(['--reading-font',str(Path(reading_font).resolve())])
        if kai_font:command.extend(['--kai-font',str(Path(kai_font).resolve())])
        if not balance_last_page:command.append('--no-balance')
        with (scratch/'worker.log').open('w+b') as log:
            worker=subprocess.Popen(command,stdout=log,stderr=log,
                                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            last=time.monotonic();stamp=None
            try:
                while worker.poll() is None:
                    current=progress.stat().st_mtime_ns if progress.exists() else None
                    if current!=stamp:last=time.monotonic();stamp=current
                    if time.monotonic()-last>timeout:
                        detail=progress.read_text(encoding='utf-8') if progress.exists() else 'renderer startup'
                        raise ValueError(f'Render stalled for {timeout:g}s: {detail}. '
                                         'Preserve prior PDFs; repair or split this block and run its proof.')
                    time.sleep(.05)
            finally:
                if worker.poll() is None:worker.kill()
                worker.wait()
            if worker.returncode:
                log.seek(0)
                raise ValueError('Body renderer failed: '+log.read().decode('utf-8',errors='replace')[-3000:])
        return json.loads(Path(layout_path).read_text(encoding='utf-8'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('spec',type=Path)
    for name in ('output','layout','font'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--proof',action='store_true')
    p.add_argument('--reading-font',type=Path)
    p.add_argument('--kai-font',type=Path)
    p.add_argument('--asset-root',type=Path)
    p.add_argument('--progress',type=Path)
    p.add_argument('--no-balance',action='store_true')
    args=p.parse_args()
    result=render(json.loads(args.spec.read_text(encoding='utf-8')),args.output,args.layout,args.font,
                  asset_root=args.asset_root or args.spec.resolve().parent,proof=args.proof,
                  reading_font=args.reading_font,balance_last_page=not args.no_balance,progress_path=args.progress,
                  kai_font=args.kai_font)
    print(json.dumps({'body_pdf':str(args.output),'layout':str(args.layout),'elapsed_seconds':result['elapsed_seconds']}))
