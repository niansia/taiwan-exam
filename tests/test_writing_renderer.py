"""國寫 body geometry measured on ROC 111–115: kai materials indented two characters, part labels on
their own line, ask lines at the margin, 問題（一）／（二） hanging six characters, 12 pt on 20 pt."""
from pathlib import Path
import sys

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import hosted_body_templates as hb
from hosted_body_templates import render

MATERIAL = '人們習慣使用標籤將複雜的事物簡化、分類，再附上標記，然而有時我們也將標籤使用在人的身上，形成刻板印象，其中真假對錯值得深思。'
TASK_ONE = '問題（一）：請依據甲、乙二文，說明「標籤」概念使用於人身上的正面與負面作用，並比較兩文的立場差異。文長限80字以內（至多4行）。（占4分）'


def spec():
    text_one = '甲\n\n' + MATERIAL * 2 + '\n\n乙\n\n' + MATERIAL * 2 + '（改寫自某作者《某書》）\n\n請分項回答下列問題：\n\n' + TASK_ONE
    return {'subject': '國寫', 'booklet_role': 'questions', 'blocks': [
        {'kind': 'section', 'title': '非選擇題（共二大題，占50分）', 'directions': '說明：本部分共有二大題，各題配分標於題末。'},
        {'kind': 'constructed', 'id': 'q1-1', 'number': 1, 'label': '一、', 'text': text_one, 'score': 4, 'score_in_text': True},
        {'kind': 'constructed', 'id': 'q1-2', 'number': 1, 'label': '', 'text': '問題（二）：日常生活中不乏貼標籤的實例，請寫一篇短文，舉例說明你對標籤現象的看法，並提出可行的因應之道。文長限400字以內（至多19行）。（占21分）', 'score': 21, 'score_in_text': True},
        {'kind': 'constructed', 'id': 'q2', 'number': 2, 'label': '二、', 'text': MATERIAL * 2 + '（改寫自蔣勳《給青年藝術家的信》）\n\n請回答下列問題：\n\n氣味透過嗅覺喚起記憶和感受。請以「花草樹木的氣味記憶」為題，寫一篇文章，書寫你熟悉的花草樹木的氣味，及其所召喚的記憶和感受。（占25分）', 'score': 25, 'score_in_text': True},
    ]}


@pytest.fixture(scope='module')
def fonts(tmp_path_factory):
    folder = tmp_path_factory.mktemp('fonts')
    body = folder / 'body.ttf'
    body.write_bytes(pymupdf.Font('cjk').buffer)
    kai = folder / 'kai.ttf'
    kai.write_bytes(pymupdf.Font('cjk').buffer)
    return body, kai


def lines(doc):
    out = []
    for pno, page in enumerate(doc):
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                spans = [s for s in line['spans'] if s['text'].strip()]
                if spans:
                    out.append((pno, round(line['bbox'][0], 1), round(line['bbox'][1], 1), ''.join(s['text'] for s in spans), spans[0]['size']))
    return out


def test_writing_geometry_matches_the_official_booklets(tmp_path, fonts):
    body, kai = fonts
    layout = render(spec(), tmp_path / 'w.pdf', tmp_path / 'w.json', body, asset_root=tmp_path, kai_font=kai)
    doc = pymupdf.open(tmp_path / 'w.pdf')
    rows = lines(doc)
    margin = min(x for _, x, _, _, _ in rows)
    by_text = {t: (x, y, size) for _, x, y, t, size in rows}
    part = next((x, y, size) for _, x, y, t, size in rows if t.strip() == '一、')
    assert abs(part[0] - margin) < 2, '「一、」 stands alone at the margin'
    material_first = next(x for _, x, _, t, _ in rows if t.startswith('人們習慣'))
    assert 22 <= material_first - margin <= 27, 'materials indent two characters at 12 pt'
    label = next((x, y) for _, x, y, t, _ in rows if t.strip() == '甲')
    edges = [d['rect'] for d in doc[0].get_drawings() if abs(d['rect'].y0 - label[1]) < 8 and d['rect'].x1 < margin + 30]
    box = pymupdf.Rect(edges[0])
    for edge in edges[1:]:
        box |= edge  # MuPDF draws each cell border as its own filled strip
    assert 16 <= box.width <= 20 and 16 <= box.height <= 20 and abs(box.x0 - margin) < 2 and box.x0 < label[0] < box.x1, \
        'a lone 甲 label sits in an 18 pt box at the margin (113 and 115 measured)'
    ask = next(x for _, x, _, t, _ in rows if t.startswith('請分項回答'))
    assert abs(ask - margin) < 2
    task = [(x, y) for _, x, y, t, _ in rows if t.startswith('問題（一）')]
    assert task and abs(task[0][0] - margin) < 2, '問題（一） starts at the margin'
    continuation = [x for _, x, y, t, _ in rows if y > task[0][1] and y < task[0][1] + 25 and not t.startswith('問題')]
    assert continuation and 69 <= continuation[0] - margin <= 75, 'continuation lines hang six characters (72 pt)'
    task_two = next(x for _, x, _, t, _ in rows if t.startswith('問題（二）'))
    assert abs(task_two - margin) < 2, '問題（二） aligns with 問題（一）'
    essay = next(x for _, x, _, t, _ in rows if t.startswith('氣味透過'))
    assert 22 <= essay - margin <= 27, 'the 第二大題 task paragraph indents two characters'
    sizes = {round(size) for _, _, _, t, size in rows if t.startswith('人們習慣') or t.startswith('問題')}
    assert sizes == {12}
    ys = sorted(y for _, x, y, t, _ in rows if t.startswith('人們習慣') or (abs(x - margin) < 2 and len(t) > 30))
    pitches = [round(b - a) for a, b in zip(ys, ys[1:]) if 0 < b - a < 30]
    assert pitches and all(19 <= p <= 21 for p in pitches), pitches
    text = ''.join(page.get_text() for page in doc).replace('\n', '')
    assert '占4分' in text and '占21分' in text and '占25分' in text
    assert text.count('（占4分）') == 1
    fonts_used = {f[3] for page in doc for f in page.get_fonts()}
    assert any('kai' in name.lower() or 'droid' in name.lower() for name in fonts_used)


def test_writing_stem_classifies_paragraphs():
    html_out = hb._writing_stem({'text': spec()['blocks'][1]['text']})
    assert html_out.count('<p class="material indent">') == 2
    assert '<table class="material-label"><tr><td class="optcell" data-pitch="18.00"' in html_out and '>甲</td>' in html_out
    assert '<p class="plain">請分項回答下列問題：</p>' in html_out
    assert html_out.count('<p class="hanging">') == 1
    essay = hb._writing_stem({'text': spec()['blocks'][3]['text']})
    assert essay.count('<p class="indent">') == 1 and essay.count('<p class="material indent">') == 1


def test_a_writing_passage_block_prints_as_kai_material(tmp_path, fonts):
    """A hosted 國寫 paper carried its materials in passage blocks and printed them in 明體."""
    body, kai = fonts
    source = MATERIAL * 2 + '（改寫自某作者《某書》）'
    passage = {'subject': '國寫', 'booklet_role': 'questions', 'blocks': [
        {'kind': 'section', 'title': '非選擇題（共二大題，占50分）', 'directions': '說明：本部分共有二大題，各題配分標於題末。'},
        {'kind': 'passage', 'id': 'p1', 'heading': '一、', 'paragraphs': ['甲', source, '乙', MATERIAL * 2, '（改寫自某機構〈某文〉）']},
        {'kind': 'constructed', 'id': 'q1-1', 'number': 1, 'label': '', 'text': '請分項回答下列問題：\n\n' + TASK_ONE, 'score': 4, 'score_in_text': True},
    ]}
    markup = hb._fragment_html(passage['blocks'][1], None, 0, 470, None, {}, {})
    assert markup.startswith('<p class="part">一、</p>') and 'class="passage"' not in markup
    assert markup.count('<p class="material indent">') == 2 and markup.count('class="material-label"') == 2
    assert '<p class="material plain">（改寫自某機構〈某文〉）</p>' in markup
    render(passage, tmp_path / 'p.pdf', tmp_path / 'p.json', body, asset_root=tmp_path, kai_font=kai)
    rows = lines(pymupdf.open(tmp_path / 'p.pdf'))
    margin = min(x for _, x, _, _, _ in rows)
    assert 22 <= next(x for _, x, _, t, _ in rows if t.startswith('人們習慣')) - margin <= 27
    assert abs(next(x for _, x, _, t, _ in rows if t.startswith('（改寫自某機構')) - margin) < 2


class _Page:
    rect = pymupdf.Rect(0, 0, 595.28, 841.89)

    def __init__(self, rows):
        self.rows = rows

    def get_text(self, kind):
        return {'blocks': [{'lines': [{'bbox': (row[2] if len(row) > 2 else (68, row[0], 520, row[0] + 14)), 'spans': [
            {'text': text, 'font': font, 'size': size} for text, font, size in row[1]]} for row in self.rows]}]}


def _booklet(material_font, task_font='NotoSerifTC-Regular'):
    return [_Page([]), _Page([
        (90, [('非選擇題（共二大題，占', 'NotoSerifTC-Regular', 13), ('50', 'NimbusRoman-Regular', 13), ('分）', 'NotoSerifTC-Regular', 13)]),
        (120, [('説明：本部分共有二大題。', 'LXGWWenKaiTC-Regular', 12)]),
        (190, [('一、', 'NotoSerifTC-Regular', 13)]),
        (215, [('甲', 'NotoSerifTC-Regular', 12)]),
        (240, [('當搜尋引擎放入', material_font, 12), ('AI', 'NimbusRoman-Regular', 12), ('摘要', material_font, 12)]),
        (300, [('我說什麼', 'NotoSerifTC-Regular', 11)]),
        (330, [('請分項回答下列問題：', 'NotoSerifTC-Regular', 12)]),
        (355, [('問題（一）：請說明兩項研究共同呈現的現象。', task_font, 12)]),
    ])]


def test_the_final_pdf_font_roles_are_read_from_embedded_fonts():
    from inspect_hosted_pdf import writing_font_role_samples
    assert writing_font_role_samples(_booklet('LXGWWenKaiTC-Regular')) == []
    assert writing_font_role_samples(_booklet('TW-Kai-98_1')) == []
    ming = writing_font_role_samples(_booklet('NotoSerifTC-Regular'))
    assert [(s['page'], s['expected']) for s in ming] == [(2, '標楷體')]
    kai_task = writing_font_role_samples(_booklet('DFKaiShu-SB-Estd-BF', task_font='LXGWWenKaiTC-Regular'))
    assert [s['expected'] for s in kai_task] == ['明體']


def test_lines_reaching_past_the_nominal_body_box_still_set_the_role():
    """A hosted 國寫 run: the 說明 line ran to x 536.8 and 「一、」 began at 63.9, outside the
    fixed 64-531 pt box; skipping them reported every correct 標楷體 line under them."""
    from inspect_hosted_pdf import writing_font_role_samples
    booklet = [_Page([]), _Page([
        (165, [('非選擇題（共二大題，占50分）', 'TW-Sung-98_1', 13)], (64.2, 165, 309.4, 183)),
        (193, [('說明：第一大題於答題卷正面作答；第二大題於背面', 'TW-Kai-98_1', 12)], (69.1, 193, 536.8, 205)),
        (209, [('作答。', 'TW-Kai-98_1', 12)], (103.9, 209, 151.8, 221)),
        (241, [('一、', 'TW-Sung-98_1', 13)], (63.9, 241, 89.8, 254)),
        (262, [('荷蘭學校禁用手機後，各校回報注意力提升。', 'TW-Kai-98_1', 12)], (87.9, 262, 495.6, 274)),
        (315, [('（一）', 'TW-Sung-98_1', 13)], (63.9, 315, 102.8, 328)),
        (333, [('比較兩項研究觀察的面向。', 'TW-Sung-98_1', 12)], (87.9, 333, 339.7, 349)),
        (393, [('二、', 'TW-Sung-98_1', 13)], (63.9, 393, 89.8, 406)),
        (414, [('那年夏天，外婆把舊信封收進鐵盒。', 'TW-Kai-98_1', 12)], (87.9, 414, 496, 426)),
        (438, [('請以「陌生人留下的痕跡」為題，寫一篇完整的文章。', 'TW-Sung-98_1', 12)], (87.9, 438, 496, 454)),
        (456, [('（占25分）', 'TW-Sung-98_1', 12)], (63.9, 456, 110, 468)),
    ])]
    assert writing_font_role_samples(booklet) == []


def test_score_and_line_limit_groups_never_break_inside():
    """W116M1 printed 「（占」 at a line end and 「4分）」 on the next line."""
    hb._latin_runs_enabled = True
    try:
        markup = hb._writing_paragraph('問題（一）：說明現象。文長限80字以內（至多4行）。（占4分）', '問題（一）：')
    finally:
        hb._latin_runs_enabled = False
    assert markup.count('white-space:nowrap') == 1, '115 breaks inside （至多19行）; only the score group is kept whole'
    assert '<span style="white-space:nowrap">（占<span class="latin">4</span>分）</span>' in markup
    material = hb._writing_paragraph('他說（至多三次）就好。', '他說（至多三次）就好。')
    assert 'nowrap' not in material
