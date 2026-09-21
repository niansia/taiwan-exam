"""The hosted checker now runs every subject's structural validators; fixtures are synthetic."""
from pathlib import Path
import sys

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import append_items as appender
import hosted_body_templates as templates
import hosted_subject_gates as gates
import run_hosted_workflow as workflow
from hosted_run_timing import transition
from validate_english_layout_contract import OFFICIAL_HEADINGS, validate_exam as english_layout


def english_paper(boilerplate=False):
    questions, answers = [], []
    for n in range(1, 51):
        options = [{'label': l, 'text': f'word{n}{l}'} for l in 'ABCD']
        questions.append({'id': f'q{n}', 'number': n, 'section_id': 'vocabulary' if n <= 10 else 'reading',
                          'type': 'single_choice', 'prompt': f'Synthetic stem {n} ______.', 'options': options,
                          'option_layout': 'row-4' if n <= 20 else 'stack'})
        answers.append({'question_id': f'q{n}', 'final_answer': 'B',
                        'reasoning': ['Choice B is the only option consistent with all clues.'] if boilerplate
                        else [f'Only word{n}B collocates with the verb in clause two.']})
    return {'metadata': {'subject': '英文', 'paper_subject': '英文', 'generation_mode': 'full-paper'},
            'sections': [{'id': 'vocabulary', 'title': '第壹部分、選擇題（占62分）\n一、詞彙題（占10分）'},
                         {'id': 'reading', 'title': '五、閱讀測驗（占24分）'}],
            'questions': questions, 'answers': answers}


def test_hosted_gate_runs_the_english_validators_and_names_official_headings():
    errors = gates.subject_gate_errors(english_paper())
    assert any('english-layout' in e and '第貳部分、混合題（占10分）' in e for e in errors)
    assert any('english-design' in e for e in errors)
    assert any('literacy' in e for e in errors)


def test_boilerplate_explanations_and_unlabelled_keys_are_rejected():
    paper = english_paper(boilerplate=True)
    found = gates.answer_explanation_errors(paper)
    assert any('identical explanation' in e for e in found)
    assert any('never names the selected option' in e for e in found)
    paper = english_paper()
    paper['answers'][0]['final_answer'] = '2'
    assert any("key '2' is not a printed option label" in e for e in gates.answer_explanation_errors(paper))
    assert gates.answer_explanation_errors({'metadata': {'subject': '英文'}, 'questions': [], 'answers': []}) == []


def test_english_layout_contract_names_gpt_style_defects():
    paper = english_paper()
    for q in paper['questions'][:10]:
        q['options'] = [{'label': str(i), 'text': f'w{i}'} for i in range(1, 5)]
    paper['questions'].append({'id': 'composition', 'number': None, 'section_id': 'composition', 'type': 'guided_writing',
                               'prompt': 'A 2025 fact sheet identifies exercise as important. Write a two-paragraph English composition of at least 120 words.',
                               'item_spec': {}})
    paper['questions'].append({'id': 't1', 'number': None, 'number_display': '中譯英1', 'section_id': 'translation',
                               'prompt': '越來越多社區設置共享工具站。'})
    paper['sections'].append({'id': 'translation', 'title': '一、中譯英（占8分）'})
    errors = english_layout(paper)
    assert any('英文第1題選項標記須為(A)(B)(C)(D)' in e for e in errors)
    assert any('以英文句子開頭' in e for e in errors)
    assert any('提示' in e for e in errors)
    assert any('「中譯英1」不是官方題號' in e for e in errors)
    assert len(OFFICIAL_HEADINGS) == 10


def test_long_task_labels_lead_the_text_instead_of_stacking_in_the_number_column(tmp_path):
    font = tmp_path/'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec = {'subject': '英文', 'blocks': [{'kind': 'section', 'title': '二、英文作文（占20分）'},
            {'kind': 'constructed', 'id': 'composition', 'label': '英文作文', 'score': 20,
             'text': '提示：近年來養寵物的風氣日漸普遍。請以此為主題寫一篇英文作文，文分兩段。'},
            {'kind': 'constructed', 'id': 't1', 'label': '1.', 'score': 4, 'text': '越來越多社區設置共享工具站。'}]}
    templates.render(spec, tmp_path/'body.pdf', tmp_path/'layout.json', font, asset_root=tmp_path)
    with pymupdf.open(tmp_path/'body.pdf') as doc:
        lines = [l for b in doc[0].get_text('dict')['blocks'] for l in b.get('lines', [])]
        texts = [''.join(s['text'] for s in l['spans']) for l in lines]
    assert any(t.startswith('英文作文') and '提示' in t for t in texts), texts
    assert not any(t.strip() in {'英', '文', '作'} for t in texts)
    assert any(t.strip().startswith('1.') for t in texts)


@pytest.fixture
def run(tmp_path):
    workflow.save(tmp_path/'preflight.json', {'status': 'ready-for-authoring', 'paper_id': 'p',
        'subject': '英文', 'review_mode': 'single-context', 'require_independent_review': False,
        'calibration': {}, 'template_asset_dir': 'templates'})
    transition(tmp_path/'generation-timing.json', 'p', 'reference_preflight')
    workflow.save(tmp_path/'plan.json', {'metadata': {'title': 'Synthetic', 'exam': '學測',
        'calibration_level': 'exploratory-uncalibrated'}, 'sections': [{'id': 'vocabulary', 'title': '一、詞彙題（占10分）'}],
        'instructions': ['Not an exam.']})
    return tmp_path


def test_saving_a_batch_reports_the_subject_gate_messages_for_those_items(run):
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 'vocabulary', 'type': 'single_choice',
                  'prompt': f'Synthetic stem {n} ______.', 'options': [{'label': str(i), 'text': f'w{i}'} for i in range(1, 5)]}
                 for n in (1, 2)]
    workflow.save(run/'batch.json', {'questions': questions, 'answers': [
        {'question_id': q['id'], 'final_answer': '2', 'reasoning': ['Choice 2 fits.'], 'verification_status': 'unverified'}
        for q in questions]})
    report = appender.append(run, run/'batch.json', plan=run/'plan.json')
    assert report['status'] == 'items-saved'
    assert any('english-design' in m for m in report['subject_gate_pending']['q1'])
    assert report['subject_gate_paper_pending']['count'] >= 1


def keyed(sequence, labels='ABCD', start=1, stimulus=None):
    questions, answers = [], []
    for offset, answer in enumerate(sequence):
        n = start + offset
        q = {'id': f'q{n}', 'number': n, 'section_id': 's', 'type': 'single_choice', 'prompt': f'stem {n}',
             'options': [{'label': l, 'text': f'w{n}{l}'} for l in labels]}
        if stimulus:
            q['group_stimulus'] = stimulus
        questions.append(q)
        answers.append({'question_id': q['id'], 'final_answer': answer, 'reasoning': [f'w{n}{answer} fits']})
    return questions, answers


def test_mechanical_answer_keys_from_the_gpt_paper_are_rejected():
    from answer_key_patterns import answer_pattern_errors
    q, a = keyed(list('1432143214'), labels='1234')
    cycle = {'metadata': {'subject': '英文', 'generation_mode': 'full-paper'}, 'questions': q, 'answers': a}
    assert any('period-4 cycle' in e for e in answer_pattern_errors(cycle))
    q, a = keyed(list('ABCDEFGHIJ'), labels='ABCDEFGHIJ', start=21)
    bank = {'metadata': {'subject': '英文', 'generation_mode': 'full-paper'}, 'questions': q, 'answers': a}
    found = answer_pattern_errors(bank)
    assert any('keyed in label order' in e for e in found) and any('runs through the labels in order' in e for e in found)
    q1, a1 = keyed(list('3214'), labels='1234', start=35, stimulus='Passage one text')
    q2, a2 = keyed(list('3214'), labels='1234', start=39, stimulus='Passage two text')
    q3, a3 = keyed(list('2431'), labels='1234', start=43, stimulus='Passage three text')
    groups = {'metadata': {'subject': '英文', 'generation_mode': 'full-paper'}, 'questions': q1 + q2 + q3, 'answers': a1 + a2 + a3}
    assert any('share the same answer sequence 3-2-1-4' in e for e in answer_pattern_errors(groups))
    q, a = keyed(list('BDACCABDBADC'))
    fine = {'metadata': {'subject': '英文', 'generation_mode': 'full-paper'}, 'questions': q, 'answers': a}
    assert answer_pattern_errors(fine) == []
    assert answer_pattern_errors({**cycle, 'metadata': {'subject': '英文'}}) == []
    assert answer_pattern_errors({**cycle, 'metadata': {'subject': '英文'}}, require_full=False)
    assert any('answer-key' in e for e in gates.subject_gate_errors(cycle))
