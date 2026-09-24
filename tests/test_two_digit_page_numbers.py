"""Booklets of ten or more inner pages compose on the fixed templates.

The page-number boxes were measured on one-digit pages; 「10」 advances 0.40 pt wider than the
footer box in every subject, so a hosted 國綜 run (official 115 國綜 has 11 inner pages) was
refused at page 10. The locked-pixel comparison still guards the template.
"""
import json
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from compose_hosted_pdf import compose, write_field
from pdf_provenance import publish_pdf
from verify_fixed_template_pdf import DEFAULT_MAP, verify_pdf


@pytest.fixture(scope='module')
def long_body(tmp_path_factory):
    folder = tmp_path_factory.mktemp('two-digit')
    body = folder / 'body.pdf'
    with pymupdf.open() as doc:
        for i in range(11):
            doc.new_page(width=595.28, height=841.89).insert_text((75, 120), f'Layout proof page {i + 1}.')
        doc.save(body)
    font = folder / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    return body, font


@pytest.mark.parametrize('kind', ['questions', 'answers'])
@pytest.mark.parametrize('subject', ['國綜', '國寫', '英文', '數學A', '數學B', '社會', '自然'])
def test_eleven_inner_pages_compose_and_verify(subject, kind, long_body, tmp_path):
    body, font = long_body
    record = next(r for r in json.loads(DEFAULT_MAP.read_text(encoding='utf-8'))['subjects'] if r['subject'] == subject)
    assets = ROOT / Path(record['assets'][0]['repository_path']).parent
    out, final = tmp_path / 'out.pdf', tmp_path / 'final.pdf'
    compose(subject, body, assets, out, year='116', title='模擬試題', running_name='學測', font_path=font,
            kai_path=font, kind=kind)
    publish_pdf(out, final)
    assert verify_pdf(final, subject, kind)['status'] == 'pass-fixed-template'
    with pymupdf.open(final) as doc:
        text = doc[-1].get_text().split()
    total = 11 + (subject in {'數學A', '數學B'} and kind == 'questions')
    assert str(total) in text and text.count(str(total)) >= 2  # 「第 N 頁」 and 「共 N 頁」 on the last page


def test_titles_keep_their_strict_width():
    with pymupdf.open() as doc:
        page = doc.new_page()
        with pytest.raises(ValueError, match='shorter test title'):
            write_field(page, (0, 0, 9.68, 16), '10', pymupdf.Font('tiro'), 10.08)
        with pytest.raises(ValueError, match='page-number field'):
            write_field(page, (0, 0, 9.68, 16), '100', pymupdf.Font('tiro'), 10.08, slack=1.0)
