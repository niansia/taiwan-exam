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
    label = next(x for _, x, _, t, _ in rows if t.strip() == '甲')
    assert abs(label - margin) < 2, 'a lone 甲 label is not indented'
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
    assert '<p class="plain">甲</p>' in html_out and '<p class="plain">請分項回答下列問題：</p>' in html_out
    assert html_out.count('<p class="hanging">') == 1
    essay = hb._writing_stem({'text': spec()['blocks'][3]['text']})
    assert essay.count('<p class="indent">') == 1 and essay.count('<p class="material indent">') == 1
