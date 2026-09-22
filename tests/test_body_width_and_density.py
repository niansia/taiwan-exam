"""A generated 國綜 booklet wrapped every option at its stem's width and ran 17 pages.

These fixtures pin the measured official geometry (option pitch 16-17 pt, item gap
19-20 pt, full-width options) and the mechanical guards that catch a body typeset
by any other route. Synthetic text only; no exam content or acceptance.
"""
import glob
import json
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import inspect_hosted_pdf as inspector
import prepare_hosted_run as preflight
from compose_hosted_pdf import compose, COMPOSER, compact_fonts
from fetch_hosted_template_assets import DEFAULT_MAP, ROOT as TEMPLATE_ROOT


def _lines(page):
    rows = []
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            text = ''.join(s['text'] for s in line['spans']).strip()
            if text:
                rows.append((round(line['bbox'][1]), round(line['bbox'][0]), round(line['bbox'][2]), text))
    return sorted(rows)


def _render(tmp_path, spec, name='body'):
    font = tmp_path / 'font.ttf'
    if not font.exists():
        font.write_bytes(pymupdf.Font('cjk').buffer)
    out, layout = tmp_path / f'{name}.pdf', tmp_path / f'{name}.json'
    hb.render(spec, out, layout, font, asset_root=tmp_path, proof=True)
    return out


def test_chinese_options_fill_the_body_width_and_keep_official_pitch(tmp_path):
    long = '他反覆「咀」嚼這段話／山路旁堆著乾枯的「沮」澤草，這是一個很長的選項，用來確認換行發生在正文右界而不是題幹寬度'
    spec = {'subject': '國綜', 'blocks': [
        {'kind': 'choice', 'id': 'q1', 'number': 1, 'text': '下列「」內的字，讀音前後相同的是：', 'columns': 1,
         'options': [{'label': '(A)', 'text': long}, {'label': '(B)', 'text': '短乙'},
                     {'label': '(C)', 'text': '短丙'}, {'label': '(D)', 'text': '短丁'}]},
        {'kind': 'choice', 'id': 'q2', 'number': 2, 'text': '下列文句，完全沒有錯別字的是：', 'columns': 2,
         'options': [{'label': l, 'text': '既瘖且「痺」／彈箏搏「髀」'} for l in ('(A)', '(B)', '(C)', '(D)')]},
    ]}
    page = pymupdf.open(_render(tmp_path, spec))[0]
    rows = _lines(page)
    first_a = next(r for r in rows if r[3].startswith('(A)'))
    stem = next(r for r in rows if r[3].startswith('下列「」'))
    body_right = 519  # the 國綜 body rect less the renderer's 4 pt inset
    # The option's first line runs to the body edge, far past the stem's own width.
    assert first_a[2] >= body_right - 15 and first_a[2] > stem[2] + 150
    number_two = next(r for r in rows if r[3] == '2.')
    options = [r for r in rows if r[3][:3] in {'(B)', '(C)', '(D)'} and r[1] < 200 and r[0] < number_two[0]]
    pitches = [b[0] - a[0] for a, b in zip(options, options[1:])]
    assert pitches and all(15 <= p <= 18 for p in pitches), pitches  # official 16-17 pt
    last_option_before = max(r for r in rows if r[0] < number_two[0])
    assert 17 <= number_two[0] - last_option_before[0] <= 22  # official item gap 19-20 pt
    two_abreast = [r for r in rows if r[0] > number_two[0] and r[3].startswith('(')]
    assert {r[0] for r in two_abreast} and len({r[0] for r in two_abreast}) == 2  # two rows of two options
    assert inspector.narrow_wrap_samples(page, pymupdf.Rect(64, 87, 531, 775)) == []


def test_mathematics_keeps_its_wider_leading(tmp_path):
    assert hb.typography('數學A') == hb.DEFAULT_TYPOGRAPHY
    assert hb.typography('國綜')[0] == 1.5 and hb.item_gap_pt('國綜') < hb.item_gap_pt('數學A')
    assert 'line-height:1.5;' in hb.subject_css('國綜') and 'line-height:1.65;' in hb.subject_css('數學A')


def _narrow_column_page(tmp_path):
    """A body whose options were set in a column as wide as the stem, as the hosted run printed."""
    doc = pymupdf.open()
    page = doc.new_page(width=595.28, height=841.89)
    css = '@font-face {font-family:B;src:url(f.ttf)} body {font-family:B;font-size:11pt;line-height:1.5}'
    archive = pymupdf.Archive()
    archive.add((pymupdf.Font('cjk').buffer, 'f.ttf'))
    html = ('<p>1. 下列「」內的字，讀音前後相同的是：</p>'
            '<p>(A) 他反覆「咀」嚼這段話／山路旁堆著乾枯的「沮」澤草</p>'
            '<p>(B) 晨霧沿著「堤」岸散開／新店鋪已正式開「幕」</p>'
            '<p>(C) 他把杯中茶一飲而「盡」／鄰里皆知其為人謹「慎」</p>'
            '<p>(D) 泉水清「冽」可鑑／寒風凜「冽」逼人</p>')
    page.insert_htmlbox(pymupdf.Rect(70, 100, 260, 400), html, css=css, archive=archive)
    path = tmp_path / 'narrow.pdf'
    doc.save(path)
    return path


def test_inspector_flags_a_narrow_wrapped_column_but_not_official_pages(tmp_path):
    narrow = _narrow_column_page(tmp_path)
    scan = inspector.audit(narrow, tmp_path / 'rasters')
    page = scan['pages'][0]
    assert 'narrow-wrap-column' in page['issues'] and len(page['narrow_wrap_samples']) >= 2
    assert 'narrow-wrap-column' in inspector.HARD_FAILURES
    official = sorted(p for p in glob.glob(str(ROOT / 'exam_packs/學測/subjects/國文/歷屆試題/115/*.pdf')) if '試卷' in p)
    if official:
        doc = pymupdf.open(official[0])
        for number in (1, 2, 5):
            body = pymupdf.Rect(64, 87, doc[number].rect.width - 64, 775)
            assert inspector.narrow_wrap_samples(doc[number], body) == []


def test_composed_booklets_carry_the_composer_stamp_through_compaction(tmp_path):
    body = tmp_path / 'body.pdf'
    with pymupdf.open() as doc:
        page = doc.new_page(width=595.28, height=841.89)
        page.insert_text((80, 120), 'stamp fixture')
        doc.save(body)
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    record = next(s for s in json.loads(DEFAULT_MAP.read_text(encoding='utf-8'))['subjects'] if s['subject'] == '國綜')
    assets = TEMPLATE_ROOT / Path(record['assets'][0]['repository_path']).parent
    out = tmp_path / 'out.pdf'
    compose('國綜', body, assets, out, year='116', title='模擬試題', running_name='學測', font_path=font, kind='questions')
    with pymupdf.open(out) as doc:
        assert doc.metadata['creator'] == COMPOSER
    compact, _ = compact_fonts(out.read_bytes())
    with pymupdf.open(stream=compact, filetype='pdf') as doc:
        assert doc.metadata['creator'] == COMPOSER


def test_preflight_downloads_the_pinned_serif_font_or_falls_back(tmp_path, monkeypatch):
    import urllib.request
    monkeypatch.delenv('TAIWAN_EXAM_NO_FONT_DOWNLOAD', raising=False)

    class Response:
        def __init__(self, data):
            self.data = data

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, limit=None):
            return self.data

    monkeypatch.setattr(urllib.request, 'urlopen', lambda request, timeout: Response(b'not a font'))
    result, note = preflight.downloaded_serif_font(tmp_path)
    assert result is None and 'pinned digest' in note

    def refuse(request, timeout):
        raise OSError('network disabled')
    monkeypatch.setattr(urllib.request, 'urlopen', refuse)
    path, record = preflight.body_font(tmp_path)
    assert record['source'] == preflight.BUILTIN_FONT and 'network disabled' in record['serif_download']
    # A matching cached copy is used without any download.
    cached = tmp_path / 'fonts' / 'NotoSerifTC-Regular.ttf'
    cached.write_bytes(pymupdf.Font('cjk').buffer)
    monkeypatch.setattr(preflight, 'SERIF_FONT_SHA256', preflight.digest(cached))
    path, record = preflight.body_font(tmp_path)
    assert record['source'] == 'downloaded-noto-serif-tc' and path == cached
