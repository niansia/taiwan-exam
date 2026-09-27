"""英文 綜合測驗 page contract (112 and 115 measured).

「二、綜合測驗」 and its 說明 close the 詞彙題 page, and both cloze groups print whole on the
next page. A hosted run declared `section_header_previews` and `page: 3` and still printed
the heading on the cloze page and ran the 16-20 passage over the page foot, away from its
options: a heading always travelled with its first item and a long passage could split.
"""
import importlib.util
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import run_hosted_workflow as workflow
from hosted_item_layout import geometry_errors

SPEC = importlib.util.spec_from_file_location('english_contract', ROOT / 'scripts' / 'validate_english_layout_contract.py')
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)

SENTENCES = (
    'Many coastal towns have begun to rethink how they welcome visitors during the busy summer months',
    'Residents often say that crowded streets and rising prices make daily life harder for families',
    'Several councils now collect a small fee that pays for road repairs and cleaner beaches',
    'Supporters argue that the fee persuades travelers to stay longer and spend more in local shops',
    'Critics worry that the charge may keep students and young people away from the coast',
)


def options(*texts):
    return [{'label': label, 'text': text} for label, text in zip('ABCD', texts)]


def passage(first, sentences):
    chosen = [SENTENCES[n % len(SENTENCES)] for n in range(sentences)]
    words = []
    for n, sentence in enumerate(chosen):
        parts = sentence.split()
        if n < 5:
            parts.insert(len(parts) // 2, f'[[{first + n}]]')
        words.append(' '.join(parts) + '.')
    third = len(words) // 3
    return [' '.join(words[:third]), ' '.join(words[third:2 * third]), ' '.join(words[2 * third:])]


def cloze_options(number):
    return (options('had yet to develop', 'was fast developing', 'would hardly develop', 'had almost developed')
            if number % 5 == 2 else options('adapt', 'ignore', 'delay', 'weigh'))


def paper(sentences=11):
    sections = [
        {'id': 'vocabulary', 'title': '第壹部分、選擇題（占62分）\n一、詞彙題（占10分）',
         'instructions': ['說明︰第1題至第10題為單選題，每題1分。']},
        {'id': 'cloze', 'title': '二、綜合測驗（占10分）', 'instructions': ['說明︰第11題至第20題為單選題，每題1分。']},
        {'id': 'completion', 'title': '三、文意選填（占10分）', 'instructions': ['說明︰第21題至第30題為單選題，每題1分。']},
    ]
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 'vocabulary', 'type': 'single_choice', 'score': 1,
                  'option_layout': 'row-4', 'options': options('hectic', 'modest', 'vacant', 'rigid'),
                  'prompt': 'The mayor has such a ______ schedule that ordinary citizens wait weeks for a meeting.'}
                 for n in range(1, 11)]
    for first in (11, 16):
        rows = [f'{n}. ' + ' '.join(f'({o["label"]}) {o["text"]}' for o in cloze_options(n)) for n in range(first, first + 5)]
        stimulus = '\n\n'.join(passage(first, sentences) + rows)
        questions += [{'id': f'q{n}', 'number': n, 'section_id': 'cloze', 'type': 'single_choice', 'score': 1, 'page': 3,
                       'group_stimulus': stimulus, 'suppress_question_display': True, 'option_layout': 'row-4',
                       'options': cloze_options(n)} for n in range(first, first + 5)]
    bank = '\n\n'.join(passage(21, 16)) + ('\n\n(A) retain (B) depend on (C) atmosphere (D) delay (E) unproductive '
                                          '(F) risk (G) function (H) minimal (I) dramatic (J) point to')
    questions += [{'id': f'q{n}', 'number': n, 'section_id': 'completion', 'type': 'single_choice', 'score': 1,
                   'group_stimulus': bank, 'suppress_question_display': True} for n in range(21, 31)]
    return {'metadata': {'subject': '英文', 'section_header_previews': {'2': 'cloze'}}, 'sections': sections,
            'questions': questions,
            'answers': [{'question_id': q['id'], 'final_answer': 'A', 'reasoning': ['synthetic']} for q in questions]}


def render(exam, folder):
    body = folder / 'body.ttf'
    body.write_bytes(pymupdf.Font('cjk').buffer)
    spec, _ = workflow.project_specs(exam, {}, 459.7)
    layout = hb.render(spec, folder / 'q.pdf', folder / 'q.json', body, asset_root=folder, kai_font=body)
    return spec, layout


@pytest.fixture(scope='module')
def booklet(tmp_path_factory):
    folder = tmp_path_factory.mktemp('cloze')
    exam = paper()
    spec, layout = render(exam, folder)
    with pymupdf.open(folder / 'q.pdf') as pdf:
        texts = {n + 1: page.get_text() for n, page in enumerate(pdf, 1)}  # after the cover
        overlaps = geometry_errors(pdf, layout['parts'])
    return exam, spec, layout, texts, overlaps


def test_heading_closes_the_vocabulary_page_and_both_groups_share_the_next(booklet):
    exam, spec, layout, texts, _ = booklet
    heading = next(row for row in layout['blocks'] if spec['blocks'][row['block']].get('title') == '二、綜合測驗（占10分）')
    ten = next(row for row in layout['blocks'] if spec['blocks'][row['block']].get('number') == 10)
    assert heading['page'] == ten['page'] == 1 and heading['bbox'][1] > ten['bbox'][3]
    cloze = [row for row in layout['blocks'] if row.get('id') in {'q11', 'q16'}]
    assert {row['page'] for row in cloze} == {2} and all(row['piece'] == 'whole' for row in cloze)
    parts = [{**part, 'page': part['page'] + 1} for part in layout['parts']]
    assert contract.placement_errors(exam, parts, texts) == []


def test_each_cloze_group_is_one_crop_at_the_official_row_pitch(booklet):
    _, spec, layout, _, overlaps = booklet
    assert overlaps == []
    groups = [part for part in layout['parts'] if part['id'] in {'q11', 'q16'}]
    assert [(part['id'], part['covers']) for part in groups] == [
        ('q11', ['q12', 'q13', 'q14', 'q15']), ('q16', ['q17', 'q18', 'q19', 'q20'])]
    rows = [row for row in layout['blocks'] if spec['blocks'][row['block']].get('option_row')]
    pitches = [b['bbox'][1] - a['bbox'][1] for a, b in zip(rows, rows[1:])
               if a['measured_height_pt'] < 20 and spec['blocks'][a['block']].get('row_follows')]
    assert rows and all(row['measured_height_pt'] < 18 or row['measured_height_pt'] > 30 for row in rows)
    assert pitches and max(pitches) <= 18  # 115: 17 pt; separate 20 pt crops printed 24


def test_an_overlong_pair_stops_with_the_page_budget(tmp_path):
    with pytest.raises(ValueError, match='英文綜合測驗兩組題組依 115 版型同頁.*超出'):
        render(paper(sentences=15), tmp_path)


def test_placement_check_reads_the_printed_pages():
    exam = paper()
    split = [{'id': 'q11', 'covers': ['q12', 'q13', 'q14', 'q15'], 'page': 3},
             {'id': 'q16', 'covers': ['q17', 'q18', 'q19', 'q20'], 'page': 3},
             {'id': 'q16', 'covers': ['q17', 'q18', 'q19', 'q20'], 'page': 4}]
    errors = contract.placement_errors(exam, split, {2: '一、詞彙題', 3: '二、綜 合 測 驗（占10分）'})
    assert any('16（第3、4頁）' in error for error in errors)
    assert any('實際在第[3]頁' in error for error in errors)


def test_the_contract_caps_the_pair_before_rendering():
    long_pair = paper(sentences=14)
    assert any('兩篇綜合測驗正文合計' in error for error in contract.validate_exam(long_pair))
    assert not any('兩篇綜合測驗正文合計' in error for error in contract.validate_exam(paper()))
