"""自然 booklet form measured on ROC 111-115 (2026-09-24 audit of two hosted 116 papers).

The hosted papers wrote 「如圖」「如表」 with no label, keyed the longest option in 22% and 52% of
single-choice items (official 7-14%), printed 「教學模型」「非NASA數據」 notes, numbered subparts
「38(a)」 and 「(1)」, and put 8-52-character options two abreast.
"""
from pathlib import Path
import hashlib
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import run_hosted_workflow as workflow
import validate_natural_layout_contract as natural

LABELS = 'ABCDE'


def options(*texts):
    return [{'label': label, 'text': text} for label, text in zip(LABELS, texts)]


def exam(questions, keys=None):
    return {'metadata': {'subject': '自然'},
            'sections': [{'id': 'p1', 'title': '第壹部分、選擇題（占72分）'}, {'id': 'p2', 'title': '第貳部分、混合題或非選擇題（占56分）'}],
            'questions': questions,
            'answers': [{'question_id': q['id'], 'final_answer': (keys or {}).get(q['id'], 'A'), 'reasoning': ['依圖1。']}
                        for q in questions]}


@pytest.fixture(scope='module')
def rendered(tmp_path_factory):
    folder = tmp_path_factory.mktemp('natural')
    svg = folder / 'fig.svg'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="160"><rect width="300" height="160" '
                   'fill="none" stroke="black"/></svg>', encoding='utf-8')
    questions = [
        {'id': 'q7', 'number': 7, 'section_id': 'p1', 'type': 'single_choice', 'score': 2,
         'group_stimulus': '某生以頻閃攝影記錄小球的位置，結果如圖1。',
         'visual_asset': {'path': 'fig.svg', 'sha256': hashlib.sha256(svg.read_bytes()).hexdigest(), 'caption': '圖1'},
         'prompt': '依圖1，下列何者正確？', 'options': options('甲', '乙', '丙', '丁', '戊')},
        {'id': 'q8', 'number': 8, 'section_id': 'p1', 'type': 'single_choice', 'score': 2,
         'group_stimulus': '某生以頻閃攝影記錄小球的位置，結果如圖1。', 'prompt': '承上題，下列何者正確？',
         'options': options('小球的水平速度保持固定', '小球的鉛直速度保持固定', '小球的加速度方向為水平',
                            '小球所受合力隨時間增加', '小球的動能在過程中不變')},
        {'id': 'w1', 'number': 42, 'section_id': 'p2', 'type': 'constructed_response', 'score': 2, 'prompt': '(a)寫出分子式。(2 分)'},
        {'id': 'w2', 'number': 42, 'section_id': 'p2', 'type': 'constructed_response', 'score': 2, 'prompt': '(b)畫出孤對電子。(2 分)'},
    ]
    font = folder / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    question_spec, solution_spec = workflow.project_specs(exam(questions), {}, 459.7)
    hb.render(question_spec, folder / 'q.pdf', folder / 'q.json', font, asset_root=folder, kai_font=font, balance_last_page=False)
    with pymupdf.open(folder / 'q.pdf') as pdf:
        lines = [(round(line['spans'][0]['bbox'][0], 1), ''.join(s['text'] for s in line['spans']).replace(chr(160), ' '))
                 for page in pdf for block in page.get_text('dict')['blocks'] for line in block.get('lines', [])]
    return question_spec, solution_spec, lines


def test_figure_caption_prints_centred_under_the_figure(rendered):
    _, _, lines = rendered
    x = next(x for x, text in lines if text == '圖1')
    assert 250 < x < 320  # centred on the 459.7 pt body


def test_options_follow_measured_rows(rendered):
    _, _, lines = rendered
    assert sum(1 for _, text in lines if text.startswith('(A) 甲')) == 1
    assert any(text.startswith('(B) 乙') and x > 150 for x, text in lines)       # five abreast
    assert any(text.startswith('(B) 小球') and x < 90 for x, text in lines)      # one per line


def test_subparts_print_a_b_under_one_number(rendered):
    _, solutions, lines = rendered
    assert sum(1 for _, text in lines if text.startswith('42.')) == 1
    assert any(text.startswith('(b)') for _, text in lines)
    assert [b['label'] for b in solutions['blocks'] if b.get('id') in {'w1', 'w2'}] == ['第42題(a)', '第42題(b)']


def test_unnumbered_figures_and_bad_captions_are_rejected():
    bare = {'id': 'q1', 'number': 1, 'type': 'single_choice', 'prompt': '結果如圖，下列何者正確？', 'options': options(*'甲乙丙丁戊')}
    assert any('names no figure' in e for e in natural.figure_label_errors(exam([bare])))
    labelled = dict(bare, prompt='結果如圖2，下列何者正確？', visual_asset={'path': 'x.svg', 'caption': '圖2'})
    assert any('run [2]' in e for e in natural.figure_label_errors(exam([labelled])))
    uncited = dict(bare, prompt='下列何者正確？', visual_asset={'path': 'x.svg', 'caption': '圖1'})
    assert any('never cite' in e for e in natural.figure_label_errors(exam([uncited])))
    good = dict(bare, prompt='結果如圖1，下列何者正確？', visual_asset={'path': 'x.svg', 'caption': '圖1'})
    assert natural.figure_label_errors(exam([good])) == []


def test_longest_key_notes_method_keys_and_subparts():
    items = [{'id': f'q{n}', 'number': n, 'type': 'single_choice', 'prompt': '何者正確？',
              'options': options('甲', '乙乙乙乙乙乙乙乙乙乙乙乙乙乙乙', '丙', '丁', '戊')} for n in range(1, 7)]
    errors = natural.option_errors(exam(items, {q['id']: 'B' for q in items}))
    assert any('single longest option in 6' in e for e in errors) and any('median 14' in e for e in errors)
    noted = [{'id': 'g', 'number': 21, 'type': 'single_choice', 'group_stimulus': '以下百分比全部為可重算的教學模型，並非NOAA野外逐日觀測資料。',
              'prompt': '何者正確？', 'options': options(*'甲乙丙丁戊')}]
    assert natural.note_errors(exam(noted))
    method = [{'id': f'm{n}', 'number': n, 'type': 'single_choice', 'prompt': '何者合理？',
               'options': options('仍需另查地面觀測資料', '乙', '丙', '丁', '戊')} for n in range(1, 5)]
    assert natural.method_key_errors(exam(method))
    written = [{'id': 'w', 'number': 38, 'type': 'constructed_response', 'prompt': '38(a) 讀圖寫出數值。(2分)'},
               {'id': 'v', 'number': 41, 'type': 'constructed_response', 'prompt': '(1)說明原因。(2 分)'}]
    assert len(natural.subpart_errors(exam(written))) == 2


def test_worn_out_materials_are_rejected():
    item = {'id': 'q33', 'number': 33, 'type': 'single_choice', 'group_stimulus': '哈伯太空望遠鏡的「極深空場」(XDF)影像……',
            'prompt': '何者正確？', 'options': options(*'甲乙丙丁戊')}
    assert natural.overused_material_errors(exam([item]))
