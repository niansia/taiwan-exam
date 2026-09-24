"""社會 booklet form measured on ROC 111-115 (2026-09-24 audit of two hosted 116 papers).

Hosted papers printed 「第 26 至 27 題為題組」, every option on its own line, keys that were the
longest option in 40 and 42 of 54 items, 「（本題3分）」, blank 「作答區／答＿＿」 boxes and
「教學虛構情境」 notes; neither could fetch a real photograph.
"""
from pathlib import Path
import hashlib
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import photo_library
import run_hosted_workflow as workflow
import validate_social_layout_contract as layout

MATERIAL = ('在某大城市，紅線違規停車經常造成交通堵塞和延誤，影響行人和其他駕駛人的正常通行，並增加交通事故的風險。'
            '現行法規的罰鍰金額忽略紅線違停對交通系統的潛在影響，因此市政府考慮修法調整罰鍰金額。請問：')


def options(*texts):
    return [{'label': label, 'text': text} for label, text in zip('ABCD', texts)]


def exam(questions, keys=None):
    return {'metadata': {'subject': '社會'},
            'sections': [{'id': 'p1', 'title': '第壹部分、選擇題（占4分）'},
                         {'id': 'p2', 'title': '第貳部分、混合題或非選擇題（占3分）'}],
            'questions': questions,
            'answers': [{'question_id': q['id'], 'final_answer': (keys or {}).get(q['id'], 'A'), 'reasoning': ['依上文。']}
                        for q in questions]}


@pytest.fixture(scope='module')
def rendered(tmp_path_factory):
    folder = tmp_path_factory.mktemp('social')
    questions = [
        {'id': 'q1', 'number': 1, 'section_id': 'p1', 'type': 'single_choice', 'score': 2,
         'prompt': '依據小文的評論，下列何者最能反映小文對健康保險制度的立場？',
         'options': options('健保旨在維護人民健康，應確保全民皆低價取得服務', '健保應有合理差別對待，故應僅要求高所得群體交換',
                            '健保重視平衡公益與私利，故基因應僅供有益人民健康', '健保旨在落實社會安全體系，故應提供人民健康照護')},
        {'id': 'q26', 'number': 26, 'section_id': 'p1', 'type': 'single_choice', 'score': 2, 'group_stimulus': MATERIAL,
         'prompt': '第二個考量因素主要是基於哪項工業區位要素？', 'options': options('原料', '市場', '動力', '資金')},
        {'id': 'q27', 'number': 27, 'section_id': 'p1', 'type': 'single_choice', 'score': 2, 'group_stimulus': MATERIAL,
         'prompt': '下列推論何者最可能成立？', 'options': options('熔岩台地農園遭颱風侵襲', '海階農園受侵蝕而崩落',
                                                               '三角洲農園因抽水下陷', '沖積扇農園因暴雨淹沒')},
    ]
    font = folder / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec, _ = workflow.project_specs(exam(questions), {}, 459.7)
    hb.render(spec, folder / 'q.pdf', folder / 'q.json', font, asset_root=folder, kai_font=font, balance_last_page=False)
    with pymupdf.open(folder / 'q.pdf') as pdf:
        lines = [(round(line['spans'][0]['bbox'][0], 1), ''.join(s['text'] for s in line['spans']).replace(chr(160), ' '))
                 for page in pdf for block in page.get_text('dict')['blocks'] for line in block.get('lines', [])]
    return spec, lines


def test_group_label_and_material_follow_115(rendered):
    spec, lines = rendered
    label = next(b for b in spec['blocks'] if b.get('group_label'))
    assert label['group_label'] == '26-27 為題組' and label['group_label_style'] == 'underline'
    first = next(x for x, text in lines if text.startswith('在某大城市'))
    assert first == pytest.approx(62.6 + 24, abs=1.5)  # 115: 87.8 against the 63.8 margin


def test_option_rows_follow_measured_lengths(rendered):
    _, lines = rendered
    # ≤7 characters four abreast at 112.6 pt, ≤16 two abreast at 225 pt, longer one per line.
    assert [x for x, text in lines if text in {'(B) 市場', '(C) 動力', '(D) 資金'}] == pytest.approx([193.2, 305.8, 418.4], abs=1.5)
    assert any(abs(x - 305.6) < 1.5 and text.startswith('(B) 海階') for x, text in lines)
    assert all(abs(x - 80.6) < 1.5 for x, text in lines if text.startswith(('(B) 健保', '(D) 健保')))


def test_longest_key_and_uneven_options_are_rejected():
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 'p1', 'type': 'single_choice', 'score': 2,
                  'prompt': '下列何者正確？', 'options': options('甲乙', '甲乙丙丁戊己庚辛壬癸子丑寅', '丙丁', '戊己')}
                 for n in range(1, 11)]
    errors = layout.option_form_errors(exam(questions, {q['id']: 'B' for q in questions}))
    assert any('single longest option in 10 items' in e for e in errors)
    assert any('10 of 10 items have options differing' in e for e in errors)
    even = [{**q, 'options': options('甲乙丙丁', '戊己庚辛', '壬癸子丑', '寅卯辰巳')} for q in questions]
    assert layout.option_form_errors(exam(even, {q['id']: 'B' for q in even})) == []


def test_official_form_notes_scores_and_answer_boxes():
    q = {'id': 'w', 'number': 40, 'section_id': 'p2', 'type': 'constructed_response', 'score': 3,
         'group_stimulus': '以下某市政策會議與兩個里名均屬教學虛構情境。' + MATERIAL,
         'prompt': '(1) 請寫出一項證據。（10字以內）（本題3分）',
         'response_format_table': {'heading': '作答區', 'rows': [{'label': '請依題意書寫'}, {'label': '答　＿＿＿＿'}]}}
    errors = layout.validate_exam(exam([q]))
    assert any('教學虛構' in e or '虛構' in e for e in errors)
    assert any('本題3分' in e for e in errors)
    assert any('（1）（2） subparts' in e for e in errors)
    assert any('作答區' in e for e in errors)
    fine = {**q, 'group_stimulus': MATERIAL, 'prompt': '依據題文，最可能呈現出什麼特點？請在答題卷作答區作答。（3 分，35 字內）'}
    fine.pop('response_format_table')
    assert layout.validate_exam(exam([fine])) == []


def test_section_titles_and_method_keys():
    bad = exam([])
    bad['sections'][0]['title'] = '選擇題'
    assert any('第壹部分、選擇題（占76分）' in e for e in layout.section_errors(bad))
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 'p1', 'type': 'single_choice', 'score': 2, 'prompt': '何者最妥？',
                  'options': options('先核對各地的底片紀錄再排序', '依照片新舊直接排出年代先後', '把相冊次序視為拍攝的次序', '以建物外觀推定照片同一年')}
                 for n in range(1, 5)]
    assert any('collect, check or track more data' in e for e in layout.method_key_errors(exam(questions)))


def test_repeated_figures_across_groups_are_rejected():
    a = {'id': 'a', 'number': 3, 'section_id': 'p1', 'type': 'single_choice', 'prompt': '戶數9,908,298戶、失業率3.41%，何者正確？'}
    b = {'id': 'b', 'number': 39, 'section_id': 'p2', 'type': 'single_choice', 'group_stimulus': '全國戶數9,908,298戶，失業率3.41%。',
         'prompt': '何者正確？'}
    assert any('9,908,298' in e for e in layout.repeated_data_errors(exam([a, b])))


def test_photo_library_manifest_is_traceable():
    manifest = photo_library.manifest()
    assert len(manifest['items']) == 59
    assert {i['domain'] for i in manifest['items']} == {'地理', '歷史', '公民與社會'}
    for item in manifest['items']:
        source = item['source']
        assert source['page'].startswith('https://commons.wikimedia.org/wiki/File:') and source['license'] and source['creator']
        assert item['observable_features'] and item['curriculum_links'] and len(item['sha256']) == 64
        assert source['source_rights'] in {'public_domain', 'licensed'}


def test_library_crop_records_pass_the_visual_contract(tmp_path, monkeypatch):
    import validate_visual_item_contract as visuals
    image = tmp_path / 'library.jpg'
    pix = pymupdf.Pixmap(pymupdf.csGRAY, pymupdf.IRect(0, 0, 1400, 900), False)
    pix.clear_with(180)
    image.write_bytes(pix.tobytes('jpg'))
    item = dict(photo_library.manifest()['items'][0], file='g01.jpg', sha256=hashlib.sha256(image.read_bytes()).hexdigest())
    (tmp_path / 'photo-library').mkdir()
    (tmp_path / 'photo-library' / 'g01.jpg').write_bytes(image.read_bytes())
    monkeypatch.setattr(photo_library, 'manifest', lambda: {'items': [item]})
    record = photo_library.use('g01', tmp_path, 'figures/q10.jpg', crop='0.1,0,0.9,1')
    assert record['visual_spec']['generation_mode'] == 'photo_library' and record['visual_spec']['min_raster_dpi'] >= 200
    spec = {**record['visual_spec'], 'role': 'required_for_solution', 'information_density': 3, 'visual_reasoning_steps': 2,
            'precision': 'relational', 'alt_text': 'x', 'difficulty_basis': 'expert_review', 'answer_bearing_features': ['x'],
            'color_dependency': False, 'answer_evidence_survives_grayscale': True,
            'grayscale_review': {'status': 'pass', 'evidence_notes': 'x'}, 'validation_checks': sorted(visuals.REQUIRED_CHECKS)}
    question = {'number': 10, 'section_id': 'p1', 'visual_asset': {**record['visual_asset'], 'visual_spec': spec},
                'item_spec': {'requires_diagram': True, 'stimulus_required': True, 'stimulus_removal_test': 'fail_without_stimulus'}}
    report = visuals.validate_exam({'metadata': {'subject': '社會'}, 'questions': [question]}, tmp_path)
    assert report['errors'] == [] and report['sourced_photo_count'] == 1
