"""A section title saved as two lines prints both as letter-spaced part headings: a hosted 英文
booklet printed 「第壹部分、選擇題（占62分）」 and 「一、詞彙題（占10分）」 in plain body text."""
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import run_hosted_workflow as workflow


def pitches(tmp_path, title):
    question = {'id': 'q1', 'number': 1, 'section_id': 'v', 'type': 'single_choice', 'score': 1, 'option_layout': 'row-4',
                'prompt': 'The council called the market plan ______ because the site might flood.',
                'options': [{'label': l, 'text': w} for l, w in zip('ABCD', ['tentative', 'urgent', 'permanent', 'practical'])]}
    exam = {'metadata': {'subject': '英文'}, 'questions': [question],
            'sections': [{'id': 'v', 'title': title, 'instructions': ['說明：第1題至第10題為單選題，每題1分。']}],
            'answers': [{'question_id': 'q1', 'final_answer': 'A', 'reasoning': ['r']}]}
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec, _ = workflow.project_specs(exam, {}, 459.7)
    hb.render(spec, tmp_path / 'q.pdf', tmp_path / 'q.json', font, asset_root=tmp_path, kai_font=font, balance_last_page=False)
    found = {}
    with pymupdf.open(tmp_path / 'q.pdf') as pdf:
        for block in pdf[0].get_text('rawdict')['blocks']:
            for line in block.get('lines', []):
                chars = [c for span in line['spans'] for c in span['chars']]
                text = ''.join(c['c'] for c in chars)
                if text.startswith(('第壹部分', '一、')):
                    found[text[:4]] = chars[1]['origin'][0] - chars[0]['origin'][0]
    return found


@pytest.mark.parametrize('separator', ['\n', '<br>'])
def test_each_line_of_a_two_line_title_is_a_spaced_heading(tmp_path, separator):
    found = pitches(tmp_path, f'第壹部分、選擇題（占62分）{separator}一、詞彙題（占10分）')
    assert set(found) == {'第壹部分', '一、詞彙'}
    assert all(pitch > 16 for pitch in found.values())   # 13 pt glyphs plus the 英文 heading spacing
