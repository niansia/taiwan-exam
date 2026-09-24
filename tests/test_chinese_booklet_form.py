"""國綜 booklet form measured on ROC 115 (2026-09-24 audit of two hosted 116 papers).

Hosted papers printed 「32.（1）」「（2）①」「（2）②」 as separate items with labels at three
different x positions, the 題組 label as 「第 6 至 8 題為題組」, reading material in the 明體
body face at the margin, and a single item's material above its number.
"""
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import run_hosted_workflow as workflow

PARAGRAPH = '從十一世紀末到十六世紀初，西方史家大致都承認這期間是騎士的鼎盛時代，由騎士構成西方武力的主體。' * 2
PAIR = '甲、孔子學鼓琴於師襄子而不進。師襄子曰：「夫子可以進矣！」孔子曰：「丘已得其曲矣，未得其數也。」\n\n乙、孔子鼓瑟，曾子、子貢側門而聽。曲終，曾子曰：「嗟乎！夫子瑟聲殆有貪狼之志。」（《韓詩外傳》）'


def options(*texts):
    return [{'label': label, 'text': text} for label, text in zip('ABCDE', texts)]


@pytest.fixture(scope='module')
def booklet(tmp_path_factory):
    folder = tmp_path_factory.mktemp('chinese')
    group = PARAGRAPH + '\n\n' + PARAGRAPH + '（改寫自余英時〈俠與中國文化〉）'
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 's', 'type': 'single_choice', 'group_stimulus': group,
                  'score': 2, 'prompt': '依據上文，敘述最適當的是：', 'options': options('甲說', '乙說', '丙說', '丁說')}
                 for n in (11, 12)]
    questions.append({'id': 'q27', 'number': 27, 'section_id': 's', 'type': 'single_choice', 'group_stimulus': PAIR,
                      'score': 2, 'prompt': '關於樂曲的彈奏與聆聽，符合下文敘述的是：',
                      'options': options('聆聽者常將個人意念投射於樂曲，如子貢善經商，遂覺曲中有趨利之心', '乙', '丙', '丁')})
    questions += [
        {'id': 'w1', 'number': 32, 'section_id': 'm', 'type': 'constructed_response', 'score': 2,
         'number_stem': '歸有光的抒情散文中，有意識地留存了家族女性的聲音，請回答下列問題：',
         'prompt': '（1）依據甲文所引三段文字，文中的「大母」、「孺人」、「夫人」對自己角色所擔負的期待是什麼？（占2分，作答字數：15字以內。）'},
        {'id': 'w2', 'number': 32, 'section_id': 'm', 'type': 'constructed_response', 'score': 4,
         'prompt': '（2）丙文的受訪者知道六女兒對「作新娘」的想法後，①有何反應？②此反應背後的特定標準是什麼？（占4分，作答字數：①、②各15字以內。）'}]
    exam = {'metadata': {'subject': '國綜'},
            'sections': [{'id': 's', 'title': '一、單選題（占48分）'}, {'id': 'm', 'title': '第貳部分、混合題或非選擇題（占24分）'}],
            'questions': questions,
            'answers': [{'question_id': q['id'], 'final_answer': 'A', 'reasoning': ['依上文。']} for q in questions]}
    font = folder / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    question_spec, solution_spec = workflow.project_specs(exam, {}, 459.7)
    lines = {}
    for role, spec in (('question', question_spec), ('solution', solution_spec)):
        hb.render(spec, folder / f'{role}.pdf', folder / f'{role}.json', font, asset_root=folder, kai_font=font,
                  balance_last_page=False)
        with pymupdf.open(folder / f'{role}.pdf') as pdf:
            lines[role] = [(round(line['spans'][0]['bbox'][0], 1), ''.join(span['text'] for span in line['spans']))
                           for page in pdf for block in page.get_text('dict')['blocks'] for line in block.get('lines', [])]
    return question_spec, lines


def test_group_label_and_material_follow_115(booklet):
    spec, lines = booklet
    label = next(b for b in spec['blocks'] if b.get('group_label'))
    assert label['group_label'] == '11-12為題組。閱讀下文，回答11-12題。' and label['group_label_style'] == 'plain'
    assert label.get('material') is True
    first = [x for x, text in lines['question'] if text.startswith('從十一世紀')]
    assert first and all(abs(x - 106.1) < 1.5 for x in first)                 # first line 24 pt in
    rest = [x for x, text in lines['question'] if text.startswith('成西方') or text.startswith('士構成')]
    assert not rest or all(abs(x - 82.1) < 1.5 for x in rest)                  # material column at 82.1


def test_single_item_material_follows_its_stem_and_hangs(booklet):
    spec, lines = booklet
    assert not any(b['kind'] == 'stimulus' and b.get('id') == 'q27' for b in spec['blocks'])
    texts = [text for _, text in lines['question']]
    assert texts.index(next(t for t in texts if t.startswith('27.'))) < texts.index(next(t for t in texts if t.startswith('甲、')))
    assert next(x for x, text in lines['question'] if text.startswith('甲、')) == pytest.approx(82.1, abs=1.5)


def test_written_item_prints_its_number_once_with_hanging_subparts(booklet):
    spec, lines = booklet
    blocks = [b for b in spec['blocks'] if b.get('id') in {'w1', 'w2'}]
    assert 'label' not in blocks[0] and blocks[1]['label'] == ''  # 「32.」 comes from the number, once
    assert [b['subpart'] for b in blocks] == ['（1）', '（2）']
    assert sum(1 for _, text in lines['question'] if text.startswith('32.')) == 1
    for label in ('（1）', '（2）'):
        assert next(x for x, text in lines['question'] if text.startswith(label)) == pytest.approx(82.1, abs=1.5)
    solutions = [text for _, text in lines['solution']]
    assert '第32題（1）' in solutions and '第32題（2）' in solutions


def test_two_column_options_tab_at_303(booklet):
    _, lines = booklet
    assert any(abs(x - 303.2) < 1.5 and text.startswith('(B)') for x, text in lines['question'])
