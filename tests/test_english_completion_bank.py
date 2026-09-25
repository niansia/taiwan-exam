"""文意選填 21-30 carry the shared (A)-(J) bank as their options (a hosted run stopped: the layout
contract allowed only A-D there while the answer check required the key among the item's labels)."""
from pathlib import Path
import sys

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import run_hosted_workflow as workflow
from answer_key_patterns import answer_pattern_errors
from hosted_subject_gates import subject_gate_errors
from validate_english_layout_contract import validate_exam as layout

WORDS = ['retain', 'depend on', 'atmosphere', 'delay', 'unproductive', 'risk', 'function', 'minimal', 'dramatic', 'point to']
BANK = ('Volunteers [[21]] the old timetables and [[22]] every name. They [[23]], [[24]], [[25]], [[26]], [[27]], '
        '[[28]], [[29]] and [[30]].\n\n' + ' '.join(f'({l}) {w}' for l, w in zip('ABCDEFGHIJ', WORDS)))
KEY = 'HCJAFDIBGE'


def exam(options=True, words=WORDS):
    bank = [{'label': l, 'text': w} for l, w in zip('ABCDEFGHIJ', words)]
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 'completion', 'type': 'single_choice', 'group_stimulus': BANK,
                  'suppress_question_display': True, 'score': 1, **({'options': bank} if options else {})}
                 for n in range(21, 31)]
    return {'metadata': {'subject': '英文', 'generation_mode': 'full-paper'},
            'sections': [{'id': 'completion', 'title': '三、文意選填（占10分）'}], 'questions': questions,
            'answers': [{'question_id': f'q{n}', 'final_answer': k, 'reasoning': [f'({k}) {WORDS["ABCDEFGHIJ".index(k)]} fits']}
                        for n, k in zip(range(21, 31), KEY)]}


def option_errors(errors):
    return [e for e in errors if '選項標記' in e or '選項庫不一致' in e]


def test_the_shared_bank_passes_the_layout_and_key_checks():
    paper = exam()
    assert not option_errors(layout(paper))
    assert not [e for e in subject_gate_errors(paper) if 'not a printed option label' in e]


def test_banks_must_match_and_other_items_keep_a_to_d():
    paper = exam()
    paper['questions'][4]['options'] = [dict(o, text='other') if o['label'] == 'B' else o for o in paper['questions'][4]['options']]
    assert any('選項庫不一致' in e for e in layout(paper))
    paper = exam()
    paper['questions'].append({'id': 'q12', 'number': 12, 'type': 'single_choice',
                               'options': [{'label': l, 'text': w} for l, w in zip('ABCDEFGHIJ', WORDS)]})
    assert any('英文第12題選項標記須為' in e for e in layout(paper))


def test_a_bank_keyed_in_label_order_is_still_caught():
    paper = exam()
    for answer, label in zip(paper['answers'], 'ABCDEFGHIJ'):
        answer['final_answer'] = label
    assert any('bank is keyed in label order' in e for e in answer_pattern_errors(paper))


def test_the_bank_prints_once(tmp_path):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec, _ = workflow.project_specs(exam(), {}, 459.7)
    hb.render(spec, tmp_path / 'q.pdf', tmp_path / 'q.json', font, asset_root=tmp_path, kai_font=font, balance_last_page=False)
    with pymupdf.open(tmp_path / 'q.pdf') as pdf:
        assert ''.join(page.get_text() for page in pdf).count('unproductive') == 1
