"""Reject production captions while retaining student-facing diagram labels."""
from pathlib import Path
import sys
import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_math_context import production_caption_samples, validate
from inspect_hosted_pdf import audit


@pytest.mark.parametrize('value', ['第15題圖：', '第 14 題附圖：', 'Question 15 figure:'])
def test_production_labels_rejected(value):
    assert production_caption_samples(value)
    assert any('production captions' in e for e in validate({'metadata': {'subject':'數學A'},
        'questions': [{'prompt': value}]}))


@pytest.mark.parametrize('value', ['如圖，求三角形面積。', '圖一、圖二表示兩個不同模型。', '時間（秒）', '實驗組濃度隨時間變化'])
def test_meaningful_labels_retained(value):
    assert not production_caption_samples(value)


def test_actual_pdf_caption_is_a_blocking_math_issue(tmp_path):
    pdf = tmp_path/'caption.pdf'
    with pymupdf.open() as d:
        p = d.new_page(width=595.28, height=841.89)
        p.insert_text((70, 130), 'Question 15 figure:')
        d.save(pdf)
    report = audit(pdf, tmp_path/'rasters', math=True)
    assert 'printed-math-production-caption' in report['pages'][0]['issues']
