"""（2） starts under （1） (a hosted 國綜 printed 32（2） and 33（2） 18 pt left of （1）).

The second subpart prints no number, so its number cell was empty; PyMuPDF 1.26, which the
hosted runs use, drops an empty cell together with its padding and the text slid to the margin.
"""
from pathlib import Path
import sys

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import run_hosted_workflow as workflow


def exam():
    questions = [
        {'id': 'a', 'number': 32, 'type': 'constructed_response', 'score': 2, 'number_stem': '依據甲文的觀點，請回答下列問題：',
         'prompt': '（1）甲文中，作者用哪一句話概括趣味的性質？請直接摘錄。（占2分，作答字數：10字以內。）'},
        {'id': 'b', 'number': 32, 'type': 'constructed_response', 'score': 4,
         'prompt': '（2）甲文提出嘗到學問趣味的四個方法。乙文「好讀書，不求甚解；每有會意，便欣然忘食」，'
                   '最能體現其中哪一個方法？（占4分，作答字數：10字以內。）'},
    ]
    return {'metadata': {'subject': '國綜'}, 'questions': [dict(q, section_id='s') for q in questions],
            'sections': [{'id': 's', 'title': '第貳部分、混合題'}],
            'answers': [{'question_id': q['id'], 'final_answer': 'x', 'reasoning': ['y']} for q in questions]}


def test_an_unnumbered_row_keeps_its_number_column():
    row = hb.numbered_row('', '（2）文字', 459.7)
    assert '<td class="optcell"' in row and 'data-mode="number">&nbsp;</td>' in row


def test_second_subpart_starts_under_the_first(tmp_path):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec, _ = workflow.project_specs(exam(), {}, 459.7)
    hb.render(spec, tmp_path / 'q.pdf', tmp_path / 'q.json', font, asset_root=tmp_path, kai_font=font,
              balance_last_page=False)
    with pymupdf.open(tmp_path / 'q.pdf') as pdf:
        lines = [(line['bbox'][0], ''.join(s['text'] for s in line['spans']).strip())
                 for block in pdf[0].get_text('dict')['blocks'] for line in block.get('lines', [])]
    first = next(x for x, t in lines if t.startswith('（1）'))
    second = next(x for x, t in lines if t.startswith('（2）'))
    assert abs(first - second) < 1
