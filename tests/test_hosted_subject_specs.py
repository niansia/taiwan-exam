"""Every subject's saved-item conventions project to printable specs without retyping.

Synthetic layout fixtures only: placeholder wording, never exam questions.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_hosted_workflow as workflow
from hosted_body_templates import render
from inspect_hosted_pdf import bottom_void

LINE = 'The town library opened a small repair corner and many visitors learned to fix things. '
PARAGRAPH = '合成長段落，用於測試跨頁續排時的段落邊界與題號、配分位置是否正確。' * 12


def figure(root, name):
    path = root / name
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="160" height="110"><path d="M10 100 L150 10" '
                    'stroke="black"/></svg>', encoding='utf-8')
    return {'path': name, 'alt': 'synthetic', 'width_percent': 30, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def choices(labels, prefix='合成選項'):
    return [{'label': label, 'text': f'{prefix} {label}'} for label in labels]


def paper(subject, root):
    """(sections, questions) per subject, in the maintained exam.json conventions."""
    if subject == '英文':
        cloze = f'Families [[11]] old phones. {LINE}The program [[12]] testing.\n\n' \
                '11. (A) donate (B) observe (C) prevent (D) measure\n\n12. (A) helps (B) delays (C) replaces (D) ignores'
        completion = f'One [[21]] table and [[22]] tools. {LINE * 3}\n\n' + ' '.join(f'({chr(65 + i)}) word{i}' for i in range(10))
        discourse = f'Repairs take patience. [[31]] {LINE}\n\n(A) First sentence.\n\n(B) Second sentence.\n\n(C) Third sentence.'
        sections = [{'id': s, 'title': title, 'instructions': ['說明：合成版面說明。']}
                    for s, title in (('v', '一、詞彙題'), ('c', '二、綜合測驗'), ('t', '三、文意選填'), ('d', '四、篇章結構'), ('x', '三、中譯英'))]
        four = lambda words: [{'label': chr(65 + i), 'text': w} for i, w in enumerate(words)]
        questions = [
            {'id': 'q1', 'number': 1, 'section_id': 'v', 'type': 'single_choice', 'option_layout': 'row-4',
             'prompt': 'The volunteers were *very* ______ today.', 'options': four(['glad', 'formal', 'narrow', 'plain'])},
            {'id': 'q11', 'number': 11, 'section_id': 'c', 'type': 'single_choice', 'option_layout': 'row-4',
             'suppress_question_display': True, 'group_stimulus': cloze, 'prompt': 'Gap 11',
             'options': four(['donate', 'observe', 'prevent', 'measure'])},
            {'id': 'q12', 'number': 12, 'section_id': 'c', 'type': 'single_choice', 'option_layout': 'row-4',
             'suppress_question_display': True, 'group_stimulus': cloze, 'prompt': 'Gap 12',
             'options': four(['helps', 'delays', 'replaces', 'ignores'])},
            *[{'id': f'q{n}', 'number': n, 'section_id': 't', 'type': 'single_choice', 'suppress_question_display': True,
               'group_stimulus': completion, 'stimulus_layout': 'completion', 'prompt': f'Gap {n}',
               'options': [{'label': chr(65 + i), 'text': f'word{i}'} for i in range(10)]} for n in (21, 22)],
            *[{'id': f'q{n}', 'number': n, 'section_id': 'd', 'type': 'single_choice', 'suppress_question_display': True,
               'group_stimulus': discourse, 'stimulus_layout': 'discourse', 'prompt': f'Gap {n}',
               'options': choices('ABC')} for n in (31, 32)],
            {'id': 'translation-1', 'number': None, 'number_display': '1.', 'answer_label': '中譯英1', 'section_id': 'x',
             'type': 'constructed_response', 'score': 4, 'prompt': '合成的中譯英版面句子。'},
        ]
    elif subject == '自然':
        sections = [{'id': 'p1', 'title': '第壹部分、選擇題', 'instructions': ['說明：合成版面說明。']},
                    {'id': 'p2', 'title': '第貳部分、混合題或非選擇題', 'instructions': ['說明：合成版面說明。']}]
        material = '合成材料：H₂O 與 CO₂ 混合後測得 SO₄²⁻ 濃度。' * 8
        questions = [
            {'id': 'q7', 'number': 7, 'section_id': 'p1', 'type': 'multiple_choice', 'required_selection_count': 2,
             'prompt': '合成多選題幹：NH₄⁺ 的敘述哪些正確？', 'options': choices('ABCDE')},
            {'id': 'q38-a', 'number': 38, 'subpart_id': 'a', 'section_id': 'p2', 'type': 'constructed_response', 'score': 2,
             'group_stimulus': material, 'number_display': '38.', 'prompt': '(1) 合成子題一。（2分）', 'visual_asset': figure(root, 'n.svg')},
            {'id': 'q38-b', 'number': 38, 'subpart_id': 'b', 'section_id': 'p2', 'type': 'constructed_response', 'score': 2,
             'group_stimulus': material, 'number_display': '', 'prompt': '(2) 合成子題二。（2分）'},
            {'id': 'q41-check', 'number': 41, 'subpart_id': 'check', 'section_id': 'p2', 'type': 'constructed_response',
             'score': 2, 'prompt': '合成勾選理由題：勾選並說明理由。（4分）'},
            {'id': 'q41-reason', 'number': 41, 'subpart_id': 'reason', 'section_id': 'p2', 'type': 'constructed_response',
             'score': 2, 'prompt': '理由', 'suppress_question_display': True},
        ]
    elif subject == '社會':
        sections = [{'id': 'c', 'title': '第壹部分、選擇題', 'instructions': ['說明：合成版面說明。']},
                    {'id': 'm', 'title': '第貳部分、混合題或非選擇題', 'instructions': ['說明：合成版面說明。']}]
        source = '資料甲：合成史料段落。' * 10
        shared = figure(root, 'map.svg')
        questions = [
            *[{'id': f'q{n}', 'number': n, 'section_id': 'c', 'type': 'single_choice', 'option_layout': 'stack',
               'group_stimulus': source, 'visual_asset': shared, 'prompt': f'合成題幹 {n}？', 'options': choices('ABCD')}
              for n in (1, 2)],
            {'id': 'q44-check', 'number': 44, 'subpart_id': 'check', 'section_id': 'm', 'type': 'constructed_response',
             'score': 2, 'prompt': '合成勾選題：勾選並說明理由。（4分）',
             'response_format_table': {'kind': 'social_monitoring_table', 'caption': '表：合成作答格式',
                                       'rows': [{'label': '(1)', 'instruction': '勾選'}, {'label': '(2)', 'instruction': '理由'}]}},
            {'id': 'q44-reason', 'number': 44, 'subpart_id': 'reason', 'section_id': 'm', 'type': 'constructed_response',
             'score': 2, 'prompt': '理由', 'suppress_question_display': True},
        ]
    elif subject == '國綜':
        sections = [{'id': 's3', 'title': '三、混合題或非選擇題', 'instructions': ['說明：合成版面說明。']}]
        passage = '\n\n'.join([PARAGRAPH] * 2)
        questions = [
            {'id': 'q32-1', 'number': 32, 'subpart_id': '1', 'section_id': 's3', 'type': 'constructed_response', 'score': 2,
             'group_stimulus': passage, 'number_display': '32.', 'prompt': '（一）合成子題。（2分）'},
            {'id': 'q32-2', 'number': 32, 'subpart_id': '2', 'section_id': 's3', 'type': 'constructed_response', 'score': 4,
             'group_stimulus': passage, 'number_display': '', 'prompt': '（二）合成子題。（4分）'},
        ]
    elif subject == '國寫':
        sections = [{'id': 'w', 'title': '國寫非選擇題', 'instructions': ['說明：本部分共有二大題，各題配分標於題末。']}]
        questions = [
            {'id': 'q1-1', 'number': 1, 'subpart_id': '1', 'section_id': 'w', 'type': 'guided_writing', 'score': 4,
             'number_display': '一、', 'prompt': '\n\n'.join([PARAGRAPH] * 5) + '\n\n問題（一）：合成題目。（占4分）',
             'continuation_pages': {'3': PARAGRAPH}},
            {'id': 'q1-2', 'number': 1, 'subpart_id': '2', 'section_id': 'w', 'type': 'guided_writing', 'score': 21,
             'number_display': '', 'prompt': '問題（二）：合成題目。（占21分）'},
        ]
    else:  # 數學A / 數學B
        sections = [{'id': 's1', 'title': '一、單選題', 'instructions': ['說明：合成版面說明。']},
                    {'id': 's3', 'title': '三、選填題', 'instructions': ['說明：合成版面說明。']},
                    {'id': 's4', 'title': '四、混合題或非選擇題', 'instructions': ['說明：合成版面說明。']}]
        questions = [
            {'id': 'q1', 'number': 1, 'section_id': 's1', 'type': 'single_choice', 'option_layout': 'row-5',
             'prompt': '設 x² = 4 且 T<sup>3</sup> = 8，合成題幹。', 'options': [{'label': str(i), 'text': f'x = {i}'} for i in range(1, 6)]},
            {'id': 'q13', 'number': 13, 'section_id': 's3', 'type': 'fill_in', 'prompt': '合成選填：所求為 ______（最簡分數）。',
             'answer_format': {'kind': 'fraction', 'numerator_slots': 1, 'denominator_slots': 2}},
            {'id': 'q18', 'number': 18, 'section_id': 's4', 'type': 'constructed_response', 'score': 4,
             'prompt': '合成非選擇題。', 'visual_asset': figure(root, 'm.svg'), 'visual_layout': 'side-right'},
        ]
    answers = [{'question_id': q['id'], 'final_answer': 'A', 'reasoning': [f'合成詳解 {q["id"]}。']} for q in questions]
    return {'metadata': {'subject': subject}, 'sections': sections, 'questions': questions, 'answers': answers}


def project(subject, root, hints=None):
    exam = paper(subject, root)
    return exam, workflow.project_specs(exam, hints or {}, 459.7)


@pytest.fixture(scope='module')
def font(tmp_path_factory):
    path = tmp_path_factory.mktemp('font') / 'font.ttf'
    path.write_bytes(pymupdf.Font('cjk').buffer)
    return path


def rendered(spec, root, name, font):
    layout = render(spec, root / f'{name}.pdf', root / f'{name}.json', font, asset_root=root)
    doc = pymupdf.open(root / f'{name}.pdf')
    return layout, doc


@pytest.mark.parametrize('subject', ['英文', '自然', '社會', '國綜', '國寫', '數學A', '數學B'])
def test_every_subject_projects_prints_and_covers_every_item(subject, tmp_path, font):
    exam, (questions, solutions) = project(subject, tmp_path)
    ids = {q['id'] for q in exam['questions']}
    for name, spec in (('questions', questions), ('solutions', solutions)):
        layout, doc = rendered(spec, tmp_path, name, font)
        covered = {p['id'] for p in layout['parts']} | {c for p in layout['parts'] for c in p.get('covers', [])}
        assert covered == ids
        text = '\n'.join(page.get_text() for page in doc)
        # Conventions are resolved, never printed as markup or missing glyph runs.
        for token in ('[[', '{{', '<sup>', '<i>', '*very*', '₂', '⁺', '²', '應選2項）（應選'):
            assert token not in text
    if subject in {'數學A', '數學B'}:
        assert [o['label'] for o in questions['blocks'][1]['options']][:2] == ['(1)', '(2)']
        fill = next(b for b in questions['blocks'] if b['kind'] == 'fill')
        assert fill['rows'] == [1, 2] and '{{answer}}' in fill['text'] and '______' not in fill['text']


def test_english_sections_keep_passage_gaps_banks_rows_and_type(tmp_path, font):
    exam, (questions, _) = project('英文', tmp_path)
    blocks = questions['blocks']
    rows = [b for b in blocks if b['kind'] == 'choice' and b['id'] in {'q11', 'q12'}]
    assert [b['text'] for b in rows] == ['', ''] and all(b['language'] == 'en' and b['columns'] == 4 for b in rows)
    completion = next(b for b in blocks if b['kind'] == 'passage' and b['id'] == 'q21')
    assert len(completion['bank']) == 10 and completion['columns'] == 5 and completion['covers'] == ['q22']
    assert completion['group_label_style'] == 'underline' and 'indent' not in completion
    discourse = next(b for b in blocks if b['kind'] == 'passage' and b['id'] == 'q31')
    # Candidate sentences print once, after the passage, never as per-gap rows.
    assert [str(p)[:3] for p in discourse['paragraphs'][-3:]] == ['(A)', '(B)', '(C)']
    assert discourse['covers'] == ['q32'] and not any(b.get('id') in {'q31', 'q32'} and b['kind'] == 'choice' for b in blocks)
    cloze = next(b for b in blocks if b['kind'] == 'passage' and b['id'] == 'q11')
    assert cloze['indent'] and all('{{gap:' in str(p) for p in cloze['paragraphs'])
    vocabulary = next(b for b in blocks if b.get('id') == 'q1')
    assert vocabulary['language'] == 'en' and vocabulary['text'] == {'rich': 'The volunteers were <i>very</i> ______ today.'}
    translation = next(b for b in blocks if b.get('id') == 'translation-1')
    assert 'language' not in translation and translation['label'] == '1.'
    layout, doc = rendered(questions, tmp_path, 'english', font)
    page = next(p for p in doc if p.search_for('donate'))
    words = {w[4]: w for w in page.get_text('words')}
    assert abs(words['11.'][3] - words['donate'][3]) < .5  # number and options share one baseline
    fonts = {s['font'] for b in page.get_text('dict')['blocks'] for line in b.get('lines', [])
             for s in line['spans'] if 'donate' in s['text']}
    assert fonts and all('Roman' in name or 'Times' in name or 'Tiro' in name for name in fonts)


def test_natural_selection_count_and_chemistry_scripts(tmp_path, font):
    exam, (questions, _) = project('自然', tmp_path)
    multiple = next(b for b in questions['blocks'] if b.get('id') == 'q7')
    assert multiple['text'] == {'rich': '合成多選題幹：NH<sub>4</sub><sup>+</sup> 的敘述哪些正確？（應選2項）'}
    assert [o['label'] for o in multiple['options']] == ['(A)', '(B)', '(C)', '(D)', '(E)']
    material = next(b for b in questions['blocks'] if b['kind'] == 'stimulus')
    assert 'SO<sub>4</sub><sup>2−</sup>' in material['text']['rich'] and 'group_label' not in material
    assert next(b for b in questions['blocks'] if b.get('id') == 'q41-check')['covers'] == ['q41-reason']
    written = copy.deepcopy(exam)
    written['questions'][0]['prompt'] += '（應選2項）'
    with pytest.raises(ValueError, match='required_selection_count'):
        workflow.project_specs(written, {}, 459.7)
    _, doc = rendered(questions, tmp_path, 'natural', font)
    text = ''.join(page.get_text() for page in doc)
    assert text.count('應選2項') == 1


def test_social_response_table_shared_figure_and_whole_question_score(tmp_path, font):
    _, (questions, _) = project('社會', tmp_path)
    blocks = questions['blocks']
    assert sum('figure' in b for b in blocks) == 1
    check = next(b for b in blocks if b.get('id') == 'q44-check' and b['kind'] == 'constructed')
    assert check['score_in_text'] and check['printed_score'] == 4 and check['keep_with_next']
    table = blocks[blocks.index(check) + 1]
    assert table['kind'] == 'table' and table['headers'] == ['作答格式'] and len(table['rows']) == 2
    _, doc = rendered(questions, tmp_path, 'social', font)
    text = ''.join(page.get_text() for page in doc)
    assert text.count('分）') == 1 and '（4分）' in text


def test_same_number_subparts_print_one_number_without_a_range_label(tmp_path, font):
    _, (questions, solutions) = project('國綜', tmp_path)
    material = next(b for b in questions['blocks'] if b['kind'] == 'stimulus')
    assert 'group_label' not in material and material['split'] == 'paragraphs'
    labels = [b.get('label') for b in questions['blocks'] if b['kind'] == 'constructed']
    assert labels == ['32.', '']
    kinds = [b['kind'] for b in solutions['blocks']]
    assert kinds == ['section', 'solution', 'solution']


def test_long_material_continues_across_pages_at_paragraph_boundaries(tmp_path, font):
    _, (questions, _) = project('國寫', tmp_path)
    item = next(b for b in questions['blocks'] if b.get('id') == 'q1-1')
    assert item['split'] == 'paragraphs' and item['score_in_text'] and PARAGRAPH in item['text']
    layout, doc = rendered(questions, tmp_path, 'writing', font)
    pieces = [b['piece'] for b in layout['blocks'] if b['block'] == questions['blocks'].index(item)]
    assert pieces[0] == 'first' and pieces[-1] == 'last'
    first_page = doc[layout['parts'][0]['page'] - 1].get_text()
    assert '一、' in first_page and '占4分' not in first_page
    last_page = doc[[p for p in layout['parts'] if p['id'] == 'q1-1'][-1]['page'] - 1].get_text()
    assert '占4分' in last_page and last_page.count('一、') == 0
    assert all(bottom_void(page) < .2 for page in list(doc)[:-1])


def test_solution_headings_follow_item_order(tmp_path):
    _, (_, solutions) = project('英文', tmp_path)
    order = [b['title'] if b['kind'] == 'section' else b['id'] for b in solutions['blocks']]
    assert order[:4] == ['一、詞彙題', 'q1', '二、綜合測驗', 'q11']
