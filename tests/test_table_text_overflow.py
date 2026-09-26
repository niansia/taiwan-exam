"""A table figure whose text runs past its cell borders is caught from its pixels, so a PNG drawn by
the model counts too (a hosted 社會 table printed 「生態最低量（萬噸）」 past its right edge)."""
import hashlib
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from hosted_evidence_refresh import figure_selfcheck, table_text_overflow
from validate_visual_item_contract import table_overflow_errors

CJK = pymupdf.Font('cjk')


def table_png(path, header, *, shift=0.0):
    """A four-column table, gray header, as a PNG. `shift` moves the last header past its cell."""
    doc = pymupdf.open()
    page = doc.new_page(width=420, height=150)
    page.insert_font(fontname='cjk', fontbuffer=CJK.buffer)
    xs, ys = [10, 110, 210, 310, 410], [10, 50, 90, 130]
    page.draw_rect(pymupdf.Rect(10, 10, 410, 50), color=None, fill=(0.85, 0.85, 0.85))
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]), width=1)
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y), width=1)
    for i, text in enumerate(header):
        page.insert_text((xs[i] + 12 + (shift if i == len(header) - 1 else 0), 36), text, fontname='cjk', fontsize=14)
    for r, row in enumerate([['甲', '150', '35', '80'], ['乙', '120', '30', '75']]):
        for i, text in enumerate(row):
            page.insert_text((xs[i] + 12, ys[r + 1] + 26), text, fontname='cjk', fontsize=14)
    page.get_pixmap(dpi=144).save(path)
    return path


def first_page(path):
    return pymupdf.open(path)[0]


def test_a_tidy_table_passes(tmp_path):
    assert table_text_overflow(first_page(table_png(tmp_path / 't.png', ['區域', '可用水量', '民生用水', '農業'])) ) == []


def test_header_past_the_right_edge_is_caught(tmp_path):
    found = table_text_overflow(first_page(table_png(tmp_path / 't.png', ['區域', '可用水量', '民生用水', '生態最低量'], shift=40)))
    assert found and 'right edge' in found[0]


def test_text_across_an_inner_border_is_caught(tmp_path):
    found = table_text_overflow(first_page(table_png(tmp_path / 't.png', ['區域', '可用水量與調度', '民生', '農業'])))
    assert found and 'cell border' in found[0]


def asset_for(path, **extra):
    return {'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **extra}


def test_check_figures_and_the_final_gate_report_tables_only(tmp_path):
    bad = table_png(tmp_path / 'bad.png', ['區域', '可用水量', '民生用水', '生態最低量'], shift=40)
    table = asset_for(bad, caption='表1', visual_spec={'kind': 'data_table'})
    photo = asset_for(bad, caption='照片1', visual_spec={'kind': 'photo'})
    exam = {'metadata': {'subject': '社會'}, 'answers': [],
            'questions': [{'id': 'q41', 'number': 41, 'visual_asset': table}, {'id': 'q42', 'number': 42, 'visual_asset': photo}]}
    figures = figure_selfcheck(tmp_path, exam)['figures']
    assert any('runs past its cell borders' in e for e in figures[0]['errors'])
    assert not any('runs past its cell borders' in e for e in figures[1]['errors'])
    assert table_overflow_errors(41, table, bad) and not table_overflow_errors(42, photo, bad)
