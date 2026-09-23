"""英文 booklet form measured on ROC 111-115 (2026-09-23 audit of two hosted 116 papers).

A hosted paper printed 47-48 between the mixed material's paragraphs, its table between
47 and 48, 「（4分）」 after each translation sentence and 「（20分）」 after 提示; the cloze and
文意選填 gaps had no underline under PyMuPDF 1.26 and the bank squeezed into half the page.
"""
import hashlib
import importlib.util
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import run_hosted_workflow as workflow

SPEC = importlib.util.spec_from_file_location('english_contract', ROOT / 'scripts' / 'validate_english_layout_contract.py')
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)

PARAGRAPH = 'The ferry archive opened in 2019 and volunteers still sort its timetables every week. ' * 5
SECTIONS = [
    {'id': 'part1', 'title': '第壹部分、選擇題（占62分）'},
    {'id': 'cloze', 'title': '二、綜合測驗（占10分）', 'instructions': ['說明︰第11題至第20題為單選題，每題1分。']},
    {'id': 'completion', 'title': '三、文意選填（占10分）', 'instructions': ['說明︰第21題至第30題為單選題，每題1分。']},
    {'id': 'mixed', 'title': '第貳部分、混合題（占10分）', 'instructions': ['說明︰本部分共有1題組，每一子題配分標於題末。']},
    {'id': 'part3', 'title': '第參部分、非選擇題（占28分）', 'instructions': ['說明︰本部分共有二大題。']},
    {'id': 'translation', 'title': '一、中譯英（占8分）', 'instructions': ['說明︰依題號將以下中文句子譯成正確、通順、達意的英文。每題4分，共8分。']},
    {'id': 'composition', 'title': '二、英文作文（占20分）', 'instructions': ['說明︰依提示寫一篇英文作文，文長至少120個單詞（words）。']},
]
HINT = ('提示︰近年來養寵物的風氣在臺灣日漸普遍，而寵物在人們生活中的角色也與過去不同。請以此為主題，並參照下列圖片，'
        '寫一篇英文作文，文分兩段。第一段描述這些圖片中所呈現的現象；第二段則根據你自身的經驗或觀察，說明此現象的原因以及可能的影響。')


def options(*texts):
    return [{'label': label, 'text': text} for label, text in zip('ABCDE', texts)]


def exam(chart):
    cloze = ('Trust should [[11]] from clear responsibility, and teachers need time to [[12]] it.\n\n'
             '11. (A) had yet to develop (B) was fast developing (C) would hardly develop (D) had almost developed\n\n'
             '12. (A) adapt (B) ignore (C) delay (D) weigh')
    bank = ('Volunteers [[21]] the old timetables and [[22]] every name.\n\n(A) retain (B) depend on (C) atmosphere '
            '(D) delay (E) unproductive (F) risk (G) function (H) minimal (I) dramatic (J) point to')
    mixed = '\n\n'.join([PARAGRAPH, PARAGRAPH, 'Visitors call the archive one of a kind among harbor museums.'])
    questions = [
        {'id': 'q11', 'number': 11, 'section_id': 'cloze', 'type': 'single_choice', 'group_stimulus': cloze, 'score': 1,
         'suppress_question_display': True, 'option_layout': 'row-4',
         'options': options('had yet to develop', 'was fast developing', 'would hardly develop', 'had almost developed')},
        {'id': 'q12', 'number': 12, 'section_id': 'cloze', 'type': 'single_choice', 'group_stimulus': cloze, 'score': 1,
         'suppress_question_display': True, 'option_layout': 'row-4', 'options': options('adapt', 'ignore', 'delay', 'weigh')},
        {'id': 'q21', 'number': 21, 'section_id': 'completion', 'type': 'single_choice', 'group_stimulus': bank,
         'suppress_question_display': True, 'score': 1},
        {'id': 'q22', 'number': 22, 'section_id': 'completion', 'type': 'single_choice', 'group_stimulus': bank,
         'suppress_question_display': True, 'score': 1},
        {'id': 'q47', 'number': 47, 'number_display': '47-48', 'section_id': 'mixed', 'type': 'fill_in', 'score': 2,
         'group_stimulus': mixed, 'group_stimulus_page_splits': {'9': PARAGRAPH, '10': PARAGRAPH},
         'visual_asset': {'path': chart.name, 'sha256': hashlib.sha256(chart.read_bytes()).hexdigest(), 'width_percent': 50},
         'prompt': '請從文章中找出兩個單詞，並視句型結構需要做適當的字形變化。<u>每格限填一個單詞</u>（word）。（填充題，4分）'
                   '\n\nThe archive is [[47]] by volunteers and remains [[48]] among harbor museums.'},
        {'id': 'q48', 'number': 48, 'section_id': 'mixed', 'type': 'fill_in', 'score': 2, 'group_stimulus': mixed,
         'suppress_question_display': True, 'prompt': 'x', 'page': 10},
        {'id': 'q49', 'number': 49, 'section_id': 'mixed', 'type': 'multiple_choice', 'score': 4, 'group_stimulus': mixed,
         'page': 9, 'option_layout': 'stack', 'options': options('Room A', 'Room B', 'Room C', 'Room D', 'Room E'),
         'prompt': 'From (A) to (E), which ONES are quiet rooms?（多選題，4分）'},
        {'id': 'q50', 'number': 50, 'section_id': 'mixed', 'type': 'short_answer', 'score': 2, 'group_stimulus': mixed,
         'prompt': 'Which phrase describes the archive’s uniqueness?（簡答題，2分）'},
        {'id': 't1', 'number_display': '1.', 'section_id': 'translation', 'type': 'constructed_response', 'score': 4,
         'prompt': '現在越來越多高中英文老師已經增加在課堂上使用英文的百分比。'},
        {'id': 't2', 'number_display': '2.', 'section_id': 'translation', 'type': 'constructed_response', 'score': 4,
         'prompt': '他們將學生依英語能力分成不同組別，進行多樣的聽、說活動。'},
        {'id': 'w', 'section_id': 'composition', 'type': 'guided_writing', 'score': 20, 'number_display': '', 'prompt': HINT},
    ]
    return {'metadata': {'subject': '英文'}, 'sections': SECTIONS, 'questions': questions,
            'answers': [{'question_id': q['id'], 'final_answer': 'A', 'reasoning': ['synthetic']} for q in questions]}


@pytest.fixture(scope='module')
def booklet(tmp_path_factory):
    folder = tmp_path_factory.mktemp('english')
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=100)
    page.draw_rect(pymupdf.Rect(10, 10, 290, 90), color=(0, 0, 0))
    chart = folder / 'chart.png'
    page.get_pixmap(dpi=100).save(str(chart))
    body = folder / 'body.ttf'
    body.write_bytes(pymupdf.Font('cjk').buffer)
    paper = exam(chart)
    spec, _ = workflow.project_specs(paper, {}, 459.7)
    hb.render(spec, folder / 'q.pdf', folder / 'q.json', body, asset_root=folder, kai_font=body, balance_last_page=False)
    with pymupdf.open(folder / 'q.pdf') as pdf:
        lines = []
        for number, page in enumerate(pdf, 1):
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines', []):
                    text = ''.join(span['text'] for span in line['spans'])
                    lines.append((number, round(line['bbox'][1], 1), round(line['spans'][0]['bbox'][0], 1), text))
        text = ''.join(page.get_text() for page in pdf)
    return spec, sorted(lines), text


def test_mixed_material_prints_whole_with_its_chart_before_the_questions(booklet):
    spec, _, _ = booklet
    order = [(b['kind'], b.get('id'), bool(b.get('figure'))) for b in spec['blocks'] if b.get('id') in {'q47', 'q49', 'q50'}]
    first_question = next(i for i, (kind, _, _) in enumerate(order) if kind in {'constructed', 'multiple'})
    assert all(kind in {'passage', 'stimulus'} for kind, _, _ in order[:first_question])
    assert order[first_question - 1] == ('stimulus', 'q47', True)  # the chart closes the material
    assert [i for kind, i, _ in order[first_question:]] == ['q47', 'q49', 'q50']


def test_english_tasks_print_official_labels_without_scores(booklet):
    spec, lines, text = booklet
    tasks = {b['id']: b for b in spec['blocks'] if b['kind'] == 'constructed'}
    assert tasks['t1']['english_task'] == 'translation' and tasks['w']['english_task'] == 'composition'
    assert tasks['q50']['answer_line'] and tasks['q47']['score_in_text'] and tasks['q47']['printed_score'] == 4
    assert '（4分）' not in text and '（20分）' not in text and '（2分）' not in text
    translation = [line for line in lines if line[3].startswith('1.') and '課堂' in line[3]]
    hint = [line for line in lines if line[3].startswith('提示︰')]
    assert translation and translation[0][2] < 66 and hint and hint[0][2] < 66
    following = [line for line in lines if line[0] == hint[0][0] and line[1] > hint[0][1] and '圖片' in line[3]
                 or line[0] == hint[0][0] and line[1] > hint[0][1] and '可能的影響' in line[3]]
    assert following and 85 < following[0][2] < 100  # 提示 hangs under its text (115: 92.4)
    pair = next(line for line in lines if line[3].startswith('47-48'))
    assert pair[2] < 66
    assert any(set(line[3].strip()) == {'_'} and len(line[3].strip()) > 60 for line in lines)  # 50's answer line


def test_bank_tabs_and_long_cloze_rows(booklet):
    _, lines, _ = booklet
    cell = lambda word: next(line for line in lines if word in line[3])
    first, fifth = cell('retain'), cell('unproductive')
    assert first[1] == fifth[1] and first[2] < 66 and abs(fifth[2] - first[2] - 4 * 96) < 1  # 115: 96 pt tabs
    # A row of long phrases breaks into two columns of two (115 items 17 and 20).
    a, b, c = cell('had yet to develop'), cell('was fast developing'), cell('would hardly develop')
    assert a[1] == b[1] and c[1] > a[1] and abs(c[2] - (a[2] + 18)) < 1  # (C) under (A), after 「11.」


def test_times_prints_f_ligatures_apart():
    marked = hb.unligated('office <span class="x">flow</span> fifty')
    assert marked == 'o<span>f</span><span>f</span>ice <span class="x"><span>f</span>low</span> <span>f</span>ifty'


def test_mixed_contract_follows_112_115():
    by_number = {
        47: {'id': 'a', 'type': 'fill_in', 'score': 2, 'prompt': 'Which room opens at 11:00?'},
        48: {'id': 'b', 'type': 'fill_in', 'score': 2, 'prompt': 'Which room is quiet?'},
        49: {'id': 'c', 'type': 'multiple_choice', 'score': 4, 'prompt': 'Choose TWO rooms.'},
        50: {'id': 'd', 'type': 'short_answer', 'score': 2, 'prompt': 'In ONE sentence, explain why.', 'group_stimulus': 'x'},
    }
    by_number[47]['group_stimulus'] = 'The archive is one of a kind.'
    answers = {'a': {'final_answer': 'Archive Hall'}, 'd': {'final_answer': 'It is noisy because of drilling.'}}
    errors = contract.mixed_section_errors(by_number, answers)
    for expected in ('「47-48」', '[[47]]', 'suppress_question_display', '（多選題，4分）', '不得寫出應選數量',
                     '一個英文單詞', '文章中的一個單詞或片語'):
        assert any(expected in error for error in errors), expected
    official = {
        47: {'id': 'a', 'type': 'fill_in', 'score': 2, 'number_display': '47-48', 'group_stimulus': 'The archive is one of a kind.',
             'prompt': '請從文章中找出兩個單詞，每格限填一個單詞（word）。（填充題，4分）\n\nIt was [[47]] and [[48]].'},
        48: {'id': 'b', 'type': 'fill_in', 'score': 2, 'suppress_question_display': True},
        49: {'id': 'c', 'type': 'multiple_choice', 'score': 4, 'prompt': 'From (A) to (F), which ONES are true?（多選題，4分）'},
        50: {'id': 'd', 'type': 'short_answer', 'score': 2, 'prompt': 'Which phrase means “unique”?（簡答題，2分）'},
    }
    assert contract.mixed_section_errors(official, {'a': {'final_answer': 'blended'}, 'd': {'final_answer': 'one of a kind'}}) == []


def test_selection_floors_are_measured():
    by_number = {n: {'id': f'q{n}', 'options': options('grow', 'spread', 'rise', 'fade')} for n in range(11, 21)}
    for n in range(35, 47):
        by_number[n] = {'id': f'q{n}', 'options': options('short', 'tiny', 'a much longer correct option', 'brief')}
    by_number.update({n: {'id': f'q{n}', 'item_spec': {'target_part_of_speech': 'verb'}} for n in range(1, 11)})
    by_number[21] = {'id': 'q21', 'item_spec': {'bank_parts_of_speech': {**{l: 'noun' for l in 'ABCDEFGHI'}, 'J': 'verb-past'}}}
    answers = {f'q{n}': {'final_answer': 'C'} for n in range(35, 47)}
    errors = contract.selection_design_errors(by_number, answers)
    assert any('片語或句構' in e for e in errors)
    assert any('唯一最長選項' in e for e in errors)
    assert any('詞性' in e and '過於集中' in e for e in errors)
    assert any("['verb-past']" in e for e in errors)


def test_composition_and_translation_print_no_score_and_rubrics_are_official():
    prompt = '說明：請依據下列兩張圖片寫作。提示：第一段描述圖片，第二段說明看法，文長至少120個單詞，英文作文。（20分）' + '內容' * 20
    paper = {'metadata': {'subject': '英文'}, 'sections': [{'id': 'translation', 'title': '一、中譯英（占8分）'}],
             'questions': [{'id': 'w', 'section_id': 'composition', 'type': 'guided_writing', 'prompt': prompt},
                           {'id': 't1', 'number_display': '1.', 'section_id': 'translation', 'prompt': '現在越來越多高中英文老師已經增加在課堂上使用英文。（4分）'}],
             'answers': [{'question_id': 't1', 'final_answer': 'x', 'explanation': '兩個語意區塊各2分'},
                         {'question_id': 'w', 'final_answer': 'x', 'explanation': '內容8分、組織4分'}]}
    errors = contract.validate_exam(paper)
    assert any('須以「提示︰」開頭' in e for e in errors)
    assert any('英文作文提示不印配分' in e for e in errors)
    assert any('中譯英第1句不印配分' in e for e in errors)
    assert any('扣0.5分' in e for e in errors)
    assert any('字彙拼字整體評分' in e for e in errors)
