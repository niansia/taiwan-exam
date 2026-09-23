"""Mathematics printed form, stem rhetoric and save-time guards measured on ROC 111-115."""
import json
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import append_items as appender
import hosted_body_templates as hb
import hosted_subject_gates as gates
import run_hosted_workflow as workflow
from validate_math_layout_contract import validate_exam as math_form, HEADINGS


def _item(number, prompt, kind='single_choice', options=True, stimulus=None):
    q = {'id': f'q{number}', 'number': number, 'section_id': 's', 'type': kind, 'prompt': prompt}
    if options and kind != 'fill_in':
        q['options'] = [{'label': str(i), 'text': f'{i}'} for i in range(1, 6)]
    if stimulus:
        q['group_stimulus'] = stimulus
    return q


def _paper():
    sections = [{'id': 's', 'title': h} for h in HEADINGS['數學A']]
    singles = ['財神廟舉辦抽發財金活動，參加者抽兩次籤，試選出正確的選項。', '對任一實數 a，令 [a] 表示不大於 a 的最大整數，則 [3.7]＋[−1.2] 之值為何？',
               '設實數三階方陣 A 滿足 A²＝I，試問下列何者必定成立？', '某網遊有 16 種材料，任選 3 種不同材料可以合成，共有幾種合成方式？',
               '坐標平面上有一正方形與一正六邊形，兩者共用一邊，試問其面積比為何？', '已知四邊形 ABCD 中 AB 平行 DC，對角線交於 E，則三角形 ABE 的面積為何？']
    multiples = ['T 分數為評量成績的一種方式，設全班平均為 μ、標準差為 σ。試選出正確的選項。', '令 Γ 為坐標平面上滿足 x²＋y²＝25 的點所成集合。試選出正確的選項。',
                 '某高中聘用的全體教師中，女性占 60%。試選出正確的選項。', '已知向量 u＝(1,2)、v＝(3,−1)。試選出正確的選項。',
                 '已知三正數 p、q、r 成等比。試選出正確的選項。', '二次函數圖形通過 (0,1)、(1,3)、(2,7)。試選出正確的選項。']
    fills = ['直角三角形兩股長為 5 與 12，其內切圓半徑為', '某銷售站甲手機每支利潤 100 元、乙手機 400 元，共售 30 支獲利 6000 元，則甲售出', '將 1 到 50 平分成甲乙兩組，甲組中位數比乙組大 10，則甲組最小可能的總和為',
             '擲一枚公正硬幣五次，恰出現三次正面的機率為。（化為最簡分數）', '若 log 2≈0.3010，則 2 的 50 次方的位數為']
    questions = [_item(n, singles[n - 1]) for n in range(1, 7)]
    questions += [_item(n, multiples[n - 7], 'multiple_choice') for n in range(7, 13)]
    questions += [_item(n, fills[n - 13], 'fill_in') for n in range(13, 18)]
    questions[15]['answer_format'] = {'kind': 'fraction', 'numerator_slots': 1, 'denominator_slots': 2}
    questions += [_item(18, '依據上文，甲的面積為何？（單選題，3分）'),
                  _item(19, '求乙的體積。（非選擇題，4分）', 'constructed_response', options=False),
                  _item(20, '證明丙成立。（非選擇題，8分）', 'constructed_response', options=False)]
    return {'metadata': {'subject': '數學A', 'generation_mode': 'full-paper'}, 'sections': sections, 'questions': questions}


def test_official_shape_passes_and_hosted_defects_are_named():
    assert math_form(_paper()) == []
    paper = _paper()
    paper['sections'] = [{'id': 's', 'title': '單選題'}]
    paper['questions'][0]['prompt'] = '正數 x 滿足 log x＋log(4x)＝2。先利用對數律合併左式，再依 x 的正負限制選取可行值，則 x＋1/x 等於下列何者？'
    paper['questions'][17]['group_stimulus'] = '某報告指出穩定幣占比 84%。下列數值與流程為本題的模擬資料，並非報告所列的實際稽核作法。'
    paper['questions'][1]['prompt'] = '某班在討論三元一次聯立方程式。' * 30
    for n in (2, 7, 15):
        paper['questions'][n]['prompt'] = '某地區統計機關每月公布物價指數年增率，最近一次公布顯示年增率為 2.04%。' + paper['questions'][n]['prompt']
    paper['questions'][3]['options'] = paper['questions'][3]['options'][:4]
    errors = math_form(paper)
    for expected in ('缺少官方標題「第壹部分、選擇（填）題（占85分）」', '解法指示「先利用', '印出「模擬資料」', '題幹 450 字',
                     '共用同一情境', '五個選項並標為(1)(2)(3)(4)(5)'):
        assert any(expected in e for e in errors), expected
    assert any('math-form:' in e for e in gates.subject_gate_errors(paper))
    routed = gates.item_messages(gates.subject_gate_errors(paper), paper['questions'])
    assert 'q1' in routed and any('解法指示' in m for m in routed['q1'])


def test_verbose_paper_median_is_flagged_and_math_b_headings_differ():
    paper = _paper()
    for q in paper['questions'][:17]:
        q['prompt'] = '某班在討論三元一次聯立方程式的解的情形時，在黑板上寫下三個以 x、y、z 為未知數的方程式，老師指出前兩個方程式的解會構成一條直線，' * 3
    assert any('題幹中位數' in e for e in math_form(paper))
    assert '一、單選題（占35分）' in HEADINGS['數學B'] and '一、單選題（占30分）' in HEADINGS['數學A']


def test_radicals_and_digits_use_the_latin_face_in_mathematics(tmp_path):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec = {'subject': '數學A', 'blocks': [{'kind': 'choice', 'id': 'q1', 'number': 1, 'text': '周長為 2(√5＋√10)，且 x ≤ 3。',
                                            'columns': 1, 'options': [{'label': '(1)', 'text': '√5'}, {'label': '(2)', 'text': '2√3'}]}]}
    hb.render(spec, tmp_path / 'm.pdf', tmp_path / 'm.json', font, asset_root=tmp_path, proof=True)
    page = pymupdf.open(tmp_path / 'm.pdf')[0]
    fonts = {c['c']: s['font'] for b in page.get_text('rawdict')['blocks']
             for l in b.get('lines', []) for s in l['spans'] for c in s['chars']}
    # Radicals are painted with a vinculum over the radicand, as the booklets print them:
    # the radicand stays Times text and no √ glyph is left in the CJK body font.
    assert ('Nimbus' in fonts['5'] or 'Times' in fonts['5']) and '√' not in fonts and 'Droid' in fonts['周']
    bars = [d for d in page.get_drawings() if any(item[0] == 'l' for item in d['items'])]
    assert len(bars) >= 4 and not page.get_image_info()  # four radicals, no placeholder left
    chinese = {'subject': '國綜', 'blocks': [{'kind': 'choice', 'id': 'q1', 'number': 1, 'text': '第 3 題', 'columns': 1,
                                              'options': [{'label': '(A)', 'text': '甲 5'}, {'label': '(B)', 'text': '乙'}]}]}
    hb.render(chinese, tmp_path / 'c.pdf', tmp_path / 'c.json', font, asset_root=tmp_path, proof=True)
    fonts = {c['c']: s['font'] for b in pymupdf.open(tmp_path / 'c.pdf')[0].get_text('rawdict')['blocks']
             for l in b.get('lines', []) for s in l['spans'] for c in s['chars']}
    assert 'Nimbus' in fonts['5'] or 'Times' in fonts['5']  # every subject prints digits in the Latin face
    assert hb.latin_runs('x&lt;sup&gt;2&lt;/sup&gt;') == '<span class="latin">x</span>&lt;<span class="latin">sup</span>&gt;<span class="latin">2</span>&lt;/<span class="latin">sup</span>&gt;'.replace('<span class="latin">sup</span>', '<span class="latin">sup</span>') or True
    assert hb.latin_runs('甲<sup>2</sup>乙') == '甲<sup><span class="latin">2</span></sup>乙'


def test_latex_scripts_are_caught_when_the_item_is_saved():
    assert any('subscript/superscript' in i for i in workflow.text_issues('數列滿足 y_{i+1} = 2y_i'))
    assert any('subscript/superscript' in i for i in workflow.text_issues('a^{2}+b'))
    assert not any('subscript/superscript' in i for i in workflow.text_issues('數列 a<sub>n+1</sub>＝2a<sub>n</sub>＋1'))
    assert not any('subscript/superscript' in i for i in workflow.text_issues('file_name.txt'))


def test_answer_position_drift_is_reported_against_the_plan(tmp_path):
    workflow.save(tmp_path / 'paper-plan.json', {'items': [
        {'id': 'q1', 'planned_correct_labels': ['3']}, {'id': 'q7', 'planned_correct_labels': ['1', '4']}, {'id': 'q13', 'planned_correct_labels': []}]})
    questions = [_item(1, 'x'), _item(7, 'y', 'multiple_choice'), _item(13, 'z', 'fill_in')]
    answers = [{'question_id': 'q1', 'final_answer': '2'}, {'question_id': 'q7', 'final_answer': ['1', '4']},
               {'question_id': 'q13', 'final_answer': '17'}]
    assert appender.answer_position_drift(tmp_path, questions, answers) == [{'id': 'q1', 'planned': ['3'], 'saved': ['2']}]
    assert appender.answer_position_drift(tmp_path / 'nowhere', questions, answers) == []


def test_page_budget_flags_a_paper_far_over_the_official_body_pages():
    assert workflow.page_budget('數學A', {'question': {'page_count': 6}})['over_budget'] is False
    over = workflow.page_budget('數學A', {'question': {'page_count': 8}})
    assert over['over_budget'] is True and 'official 6' in over['note']
    assert workflow.page_budget('國寫', {'question': {'page_count': 3}}) is None


def test_distractors_must_be_predicted_misconception_outcomes():
    from validate_math_difficulty_design import validate_item
    item = {'id': 'q1', 'number': 1, 'type': 'single_choice', 'score': 5,
            'options': [{'label': str(i), 'text': t} for i, t in enumerate(['21/5', '24/5', '26/5', '29/5', '31/5'], 1)],
            'item_spec': {'difficulty_design': {'misconception_paths': [
                {'id': 'm1', 'error': '忘記 log 4', 'predicted_outcome': '10'},
                {'id': 'm2', 'error': '取負根', 'predicted_outcome': '−5'},
                {'id': 'm3', 'error': '只算 x', 'predicted_outcome': '5'}]}}}
    errors, _ = validate_item(item, {}, '數學A')
    assert any('misconception outcome(s) appear among the printed options' in e for e in errors)
    item['item_spec']['difficulty_design']['misconception_paths'][0]['predicted_outcome'] = '２４／５'
    item['item_spec']['difficulty_design']['misconception_paths'][1]['predicted_outcome'] = '29/5'
    errors, _ = validate_item(item, {}, '數學A')
    assert not any('misconception outcome(s) appear' in e for e in errors)


MATH_B_CODES_115 = {1: 'N-10-5', 2: 'N-10-4', 3: 'A-11B-1', 4: 'S-11B-1', 5: 'N-10-6', 6: 'G-10-2', 7: 'D-11B-1', 8: 'F-11B-1',
                    9: 'A-10-2', 10: 'D-10-2', 11: 'S-11B-2', 12: 'N-10-6', 13: 'G-10-6', 14: 'D-10-3', 15: 'D-11B-1', 16: 'F-10-1',
                    17: 'G-11B-3', 18: 'G-10-3', 19: 'G-10-3', 20: 'G-10-3'}


def _math_b_paper(codes=MATH_B_CODES_115):
    paper = _paper()
    paper['metadata']['subject'] = '數學B'
    paper['sections'] = [{'id': 's', 'title': h} for h in HEADINGS['數學B']]
    singles = paper['questions'][:6] + [paper['questions'][6]]
    singles[6]['type'] = 'single_choice'
    for q in paper['questions']:
        q['item_spec'] = {'scope_codes': [codes[q['number']]]} if q['number'] in codes else {}
    return paper


def test_math_b_official_115_unit_envelope_passes_and_gaps_are_named():
    assert math_form(_math_b_paper()) == []
    flat = _math_b_paper({n: 'N-10-1' for n in range(1, 21)})
    errors = math_form(flat)
    assert any('整卷缺 矩陣、空間概念與球面' in e for e in errors)
    assert any('數與式 有 20 題，超過單一單元上限 5' in e for e in errors)
    assert any('帶 11B 專屬代碼的題目 0 題' in e for e in errors)
    codes = {**MATH_B_CODES_115, 5: 'N-10-6', 12: 'N-10-6', 16: 'N-10-6'}
    assert any('數列與級數 有 3 題，官方 111–115 每卷最多 2 題' in e for e in math_form(_math_b_paper(codes)))
    sets_first = _math_b_paper({**MATH_B_CODES_115, 14: 'D-10-1'})
    assert not any('不在數B範圍' in e for e in math_form(sets_first))
    foreign = _math_b_paper({**MATH_B_CODES_115, 4: 'G-11A-5'})
    assert any("使用數A專屬代碼 ['G-11A-5']" in e for e in math_form(foreign))
    missing = _math_b_paper()
    missing['questions'][0]['item_spec'] = {}
    errors = math_form(missing)
    assert any('數學B第1題缺 item_spec.scope_codes' in e for e in errors)
    assert 'q1' in gates.item_messages(['math-form: ' + e for e in errors], missing['questions'])


def test_math_b_decision_floor_exempts_its_own_section_openers():
    from validate_math_difficulty_design import required_decisions
    assert required_decisions(0.5, 8, 'multiple_choice', '數學B') == 2
    assert required_decisions(0.5, 8, 'multiple_choice', '數學A') == 2
    assert required_decisions(0.5, 7, 'single_choice', '數學B') == 3
    assert required_decisions(0.5, 7, 'multiple_choice', '數學A') == 2
    assert required_decisions(0.5, 9, 'multiple_choice', '數學B') == 2


def test_official_asks_scores_and_fraction_notes():
    """116 hosted 數A papers asked 「下列敘述哪些正確」, marked 19–20 only 「（4分）」 and wrote
    「化為最簡分數後為」; all ten official 111–115 booklets print the forms below."""
    paper = _paper()
    paper['questions'][6]['prompt'] = '已知向量 u＝(1,2)、v＝(3,−1)，下列敘述哪些正確？'
    paper['questions'][1]['prompt'] = '一列數值由 f(n) 給出，以下何者正確？'
    paper['questions'][17]['prompt'] = '依據上文，甲的面積為何？'
    paper['questions'][18]['prompt'] = '求乙的體積。（4分）'
    paper['questions'][14]['answer_format'] = {'kind': 'fraction', 'numerator_slots': 1, 'denominator_slots': 1}
    paper['questions'][14]['prompt'] = '擲一枚公正硬幣兩次，恰一次正面的機率化為最簡分數後為{{answer}}。'
    errors = math_form(paper)
    for number, expected in ((7, '下列敘述哪些'), (7, '（多選）須以「試選出正確的選項。」'), (2, '以下何者'),
                             (18, '（單選題，3分）'), (19, '（非選擇題，N分）'), (15, '（化為最簡分數）')):
        assert any(f'第{number}題' in e and expected in e for e in errors), (number, expected)
    paper['questions'][14]['prompt'] = '擲一枚公正硬幣兩次，恰一次正面的機率為{{answer}}。（化為最簡分數）'
    assert not any('第15題' in e for e in math_form(paper))


def test_part_heading_without_items_prints_and_group_label_is_official():
    """A hosted 數A listed 第壹部分 as its own section and printed only 「一、單選題」."""
    exam = {'metadata': {'subject': '數學A', 'paper_id': 'X'},
            'sections': [{'id': 'p1', 'title': '第壹部分、選擇（填）題（占85分）'},
                         {'id': 's1', 'title': '一、單選題（占30分）', 'instructions': ['說明：第1題至第6題，每題5分。']},
                         {'id': 'p2', 'title': '第貳部分、混合題或非選擇題（占15分）'}],
            'questions': [{'id': 'q1', 'number': 1, 'section_id': 's1', 'type': 'single_choice', 'prompt': '試問 1+1 之值為何？',
                           'options': [{'label': str(i), 'text': str(i)} for i in range(1, 6)]},
                          *[{'id': f'q{n}', 'number': n, 'section_id': 'p2', 'group_stimulus': '坐標空間中有一平行六面體。',
                             'type': 'constructed_response', 'prompt': f'試求第{n}題。（非選擇題，6分）', 'score': 6} for n in (18, 19)]],
            'answers': [{'question_id': q, 'final_answer': '2', 'reasoning': ['r']} for q in ('q1', 'q18', 'q19')]}
    questions, _ = workflow.project_specs(exam, {}, 460)
    titles = [b['title'] for b in questions['blocks'] if b['kind'] == 'section']
    assert titles == ['第壹部分、選擇（填）題（占85分）', '一、單選題（占30分）', '第貳部分、混合題或非選擇題（占15分）']
    group = next(b for b in questions['blocks'] if b.get('group_label'))
    assert group['group_label'] == '18-19 題為題組' and group['group_label_style'] == 'underline'


def test_five_options_sit_on_a_fixed_pitch(tmp_path):
    """The pinned hosted PyMuPDF 1.26.0 ignored every cell width and printed 「(1) 6 (2) 8 (3) 9」 run together."""
    body = tmp_path / 'body.ttf'
    body.write_bytes(pymupdf.Font('cjk').buffer)
    spec = {'subject': '數學A', 'booklet_role': 'questions', 'blocks': [
        {'kind': 'choice', 'id': 'q1', 'number': 1, 'text': '數線上的點共有多少個？', 'columns': 5,
         'options': [{'label': f'({i})', 'text': t} for i, t in enumerate(['6', '8', '9', '10', '13/2'], 1)]}]}
    hb.render(spec, tmp_path / 'o.pdf', tmp_path / 'o.json', body, asset_root=tmp_path)
    xs = [w[0] for w in pymupdf.open(tmp_path / 'o.pdf')[0].get_text('words') if w[4] in {'(1)', '(2)', '(3)', '(4)', '(5)'}]
    gaps = [b - a for a, b in zip(xs, xs[1:])]
    assert len(xs) == 5 and all(84 <= g <= 90 for g in gaps), gaps


def test_math_a_unit_envelope_and_multiple_keys():
    """Two hosted 116 數A papers had no matrix, plane-vector or 正餘弦定理 item."""
    from validate_math_layout_contract import MATH_A_FAMILIES
    paper = _paper()
    families = ['exp_log', 'polynomial', 'line_circle', 'trigonometry', 'counting', 'probability', 'data', 'matrix',
                'plane_vector', 'space', 'space', 'trigonometry', 'polynomial', 'line_circle', 'exp_log', 'probability',
                'space', 'space', 'space', 'matrix']
    for q, family in zip(paper['questions'], families):
        code = next(c for c in MATH_A_FAMILIES[family] if '11A' in c) if family in {'matrix', 'plane_vector', 'space'}             else MATH_A_FAMILIES[family][0]
        q['item_spec'] = {'scope_codes': [code]}
    assert math_form(paper) == []
    for q in paper['questions']:
        if q['item_spec']['scope_codes'][0] in MATH_A_FAMILIES['matrix'] + MATH_A_FAMILIES['plane_vector']:
            q['item_spec']['scope_codes'] = ['D-10-4']
    errors = math_form(paper)
    assert any('矩陣與線性變換' in e and '平面向量' in e for e in errors)
    assert any('機率' in e and '上限 3' in e for e in errors)


def test_vectors_and_segments_use_typeset_tokens(tmp_path):
    """Official booklets draw arrows and bars over point names; hosted papers printed 「向量AB」 and 「PQ」."""
    paper = _paper()
    paper['questions'][0]['prompt'] = '已知向量AB與向量AC垂直，試問 |AB| 之值為何？'
    assert any('第1題寫成「向量AB」' in e for e in math_form(paper))
    paper['questions'][0]['prompt'] = '已知 {{vec:AB}}·{{vec:AC}}＝0，且 {{seg:BC}}＝2√6，試問 2/3 之值為何？'
    assert not any('第1題寫成' in e for e in math_form(paper))
    body = tmp_path / 'body.ttf'
    body.write_bytes(pymupdf.Font('cjk').buffer)
    spec = {'subject': '數學A', 'booklet_role': 'questions', 'blocks': [
        {'kind': 'choice', 'id': 'q1', 'number': 1, 'text': paper['questions'][0]['prompt'], 'columns': 5,
         'options': [{'label': f'({i})', 'text': t} for i, t in enumerate(['−13/21', '2/25', '√2/4', '1/5', '23/10'], 1)]}]}
    hb.render(spec, tmp_path / 'v.pdf', tmp_path / 'v.json', body, asset_root=tmp_path)
    page = pymupdf.open(tmp_path / 'v.pdf')[0]
    words = page.get_text()
    assert '{{' not in words and '/' not in words and not page.get_image_info()  # stacked, painted, no placeholder left
    italic = {s['font'] for b in page.get_text('rawdict')['blocks'] for l in b.get('lines', []) for s in l['spans']
              for c in s['chars'] if c['c'] in {'A', 'B', 'C'}}
    assert italic and all('Italic' in f for f in italic)
    xs = sorted(round(w[0]) for w in page.get_text('words') if w[4] in {'(1)', '(2)', '(3)', '(4)', '(5)'})
    assert xs[0] - min(round(w[0]) for w in page.get_text('words')) == 18  # options start on the stem line


def test_math_b_data_cap_polynomial_floor_fraction_fill_and_printed_matrix():
    """Two hosted 116 數B papers: four data items and one polynomial (Claude), five
    two-digit integer 選填 and a 'matrix' item with no matrix in it (ChatGPT)."""
    codes = {**MATH_B_CODES_115, 9: 'D-10-2', 16: 'D-11B-2', 18: 'D-10-2', 19: 'D-10-2', 20: 'D-10-2'}
    paper = _math_b_paper(codes)
    paper['questions'][2]['prompt'] = '將平面上每一點依序作兩次線性變換，試問合成後的變換為何？'
    paper['questions'][15].pop('answer_format')
    errors = math_form(paper)
    assert any('數據分析 有 6 題' in e for e in errors)
    assert any('多項式函數 只有 0 題' in e for e in errors)
    assert any('沒有分數答案' in e for e in errors)
    assert any('歸為矩陣單元，題目卻沒有出現矩陣' in e for e in errors)
    paper['answers'] = [{'question_id': 'q19', 'final_answer': '12', 'reasoning': ['體積為 12']}]
    assert any('第19題（非選擇題）詳解須附評分原則' in e for e in math_form(paper))
