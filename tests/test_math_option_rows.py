"""數學A/B options that overrun their tab print one per line (official 111-115: five abreast or
one per line). A hosted 數A paper set 13-15-character options three abreast and wrapped
「相／等」 and a fraction inside their cells."""
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import run_hosted_workflow as workflow

LONG = ['原資料的 x 與 y 平均數相等', '原資料的相關係數為 1', '將 y 換成 5−y 後，相關係數仍為正',
        'X 與 Y 的相關係數為 4/5', '四個點全落在直線 y=x 上']
SHORT = ['1', '2', '3', '4', '5']


def rendered(tmp_path, subject, texts, layout):
    q = {'id': 'q7', 'number': 7, 'type': 'multiple_choice', 'score': 5, 'section_id': 's', 'option_layout': layout,
         'prompt': '四筆配對資料依次為 (x,y)=(1,1)、(2,3)、(3,2)、(4,4)。試選出正確的選項。',
         'options': [{'label': str(n), 'text': t} for n, t in enumerate(texts, 1)]}
    exam = {'metadata': {'subject': subject}, 'sections': [{'id': 's', 'title': '二、多選題'}], 'questions': [q],
            'answers': [{'question_id': 'q7', 'final_answer': '1,4', 'reasoning': ['r']}]}
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec, _ = workflow.project_specs(exam, {}, 459.7)
    hb.render(spec, tmp_path / 'q.pdf', tmp_path / 'q.json', font, asset_root=tmp_path, kai_font=font,
              balance_last_page=False)
    with pymupdf.open(tmp_path / 'q.pdf') as pdf:
        return [(round(line['bbox'][0]), round(line['bbox'][1]), ''.join(s['text'] for s in line['spans']))
                for block in pdf[0].get_text('dict')['blocks'] for line in block.get('lines', [])]


@pytest.mark.parametrize('subject', ['數學A', '數學B'])
@pytest.mark.parametrize('layout', ['grid-3-2', 'row-5', 'grid-2'])
def test_overrunning_options_print_one_per_line(tmp_path, subject, layout):
    lines = rendered(tmp_path, subject, LONG, layout)
    starts = [(x, y) for x, y, t in lines if t.lstrip().startswith(tuple(f'({n})' for n in range(1, 6)))]
    assert len(starts) == 5 and len({x for x, _ in starts}) == 1 and len({y for _, y in starts}) == 5
    assert not any(t.strip() in {'等', '仍為正'} for _, _, t in lines)  # nothing wraps inside a cell
    four = next(y for x, y, t in lines if t.lstrip().startswith('(4)'))
    assert all(four - 8 < y < four + 12 for x, y, t in lines if t.strip() in {'4', '5'})  # the stacked 4/5 stays on its row


def test_short_options_keep_the_chosen_row(tmp_path):
    lines = rendered(tmp_path, '數學A', SHORT, 'grid-3-2')
    starts = [(x, y) for x, y, t in lines if t.lstrip()[:3] in {f'({n})' for n in range(1, 6)}]
    assert len({y for _, y in starts}) <= 2
