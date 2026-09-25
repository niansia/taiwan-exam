"""英文 1-20 print four options four abreast, or two by two when one overruns its tab (115: 17, 20),
never one per line: a hosted paper stacked 14 「On the contrary / In this way / By accident / At the
same time」 because the item asked for a stack."""
from pathlib import Path
import sys

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import run_hosted_workflow as workflow

ROWS = {13: ['Therefore', 'Likewise', 'Nevertheless', 'For example'],
        14: ['On the contrary', 'In this way', 'By accident', 'At the same time'],
        17: ['would hardly develop', 'had yet to develop', 'was fast developing', 'had almost developed'],
        19: ['the committee had never formally approved the plan', 'nobody in the village had expected such a result',
             'the harbor was closed for most of that winter', 'several families moved away before the spring']}


def rendered(tmp_path):
    passage = 'Reading aloud was once common. [[13]] people read. [[14]] it spread. [[17]] cities grew. [[19]] too.'
    text = passage + '\n\n' + '\n\n'.join(f'{n}. ' + ' '.join(f'({l}) {w}' for l, w in zip('ABCD', words))
                                          for n, words in ROWS.items())
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 'cloze', 'type': 'single_choice', 'group_stimulus': text,
                  'score': 1, 'suppress_question_display': True, 'option_layout': 'stack',
                  'options': [{'label': l, 'text': w} for l, w in zip('ABCD', words)]} for n, words in ROWS.items()]
    exam = {'metadata': {'subject': '英文'}, 'sections': [{'id': 'cloze', 'title': '二、綜合測驗（占10分）'}],
            'questions': questions, 'answers': [{'question_id': q['id'], 'final_answer': 'A', 'reasoning': ['r']} for q in questions]}
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec, _ = workflow.project_specs(exam, {}, 459.7)
    hb.render(spec, tmp_path / 'q.pdf', tmp_path / 'q.json', font, asset_root=tmp_path, kai_font=font, balance_last_page=False)
    with pymupdf.open(tmp_path / 'q.pdf') as pdf:
        lines = [(round(line['bbox'][0]), round(line['bbox'][1]), ''.join(s['text'] for s in line['spans']))
                 for block in pdf[0].get_text('dict')['blocks'] for line in block.get('lines', [])]
    return {n: [(x, y) for x, y, t in lines if any(t.lstrip().startswith(p) for p in (f'{n}. ', '(')) and
                any(w in t for w in words)] for n, words in ROWS.items()}


def test_rows_follow_the_official_arrangement(tmp_path):
    rows = rendered(tmp_path)
    assert len({y for _, y in rows[13]}) == 1 and len({y for _, y in rows[14]}) == 1   # four abreast
    assert len({y for _, y in rows[17]}) == 2 and len({x for x, _ in rows[17]}) == 3   # two by two
    assert len({y for _, y in rows[19]}) == 4                                            # too long: one per line
