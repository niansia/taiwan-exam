"""Defects a 3-hour hosted run met only at whole-paper gates now surface when a batch is saved."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import append_items as appender
import check_paper_plan as plan_checker
import emit_item_skeleton as skeleton
import hosted_subject_gates as gates
import prepare_hosted_run as preflight
import validate_paper_difficulty_balance as balance
from validate_source_grounding import item_errors as grounding_item_errors


def _chinese_item(number, prompt, stimulus, options=None):
    return {'id': f'q{number}', 'number': number, 'section_id': 's', 'type': 'single_choice', 'prompt': prompt,
            'group_stimulus': stimulus,
            'options': options or [{'label': l, 'text': f'選項{l}'} for l in 'ABCD'], 'item_spec': {}}


def test_quotes_attributed_to_the_material_must_appear_in_it():
    material = '崇禎五年十二月，余住西湖。大雪三日，湖中人鳥聲俱絕。舟子喃喃曰：「莫說相公癡，更有癡似相公者！」（張岱〈湖心亭看雪〉）'
    exam = {'metadata': {'subject': '國綜'}, 'questions': [
        _chinese_item(13, '甲文先寫「人鳥聲俱絕」，其作用最適當的是：', material),
        _chinese_item(32, '乙、丙二文的「久」字，各指什麼？', material),
        _chinese_item(14, '關於甲、乙兩文對「癡」的理解，最適當的是：', material),
    ]}
    errors = gates.material_quote_errors(exam)
    assert len(errors) == 1 and errors[0].startswith('Q32') and '「久」' in errors[0]
    assert any(e.startswith('quotes: Q32') for e in gates.subject_gate_errors(exam, authoring=True))


def test_grounding_rules_are_reported_per_item_while_authoring():
    question = _chinese_item(6, '依據本文，作者的核心主張是：', '古蹟修復並不是把建築變回新的一樣。' * 6)
    errors = grounding_item_errors(question, '國綜')
    assert any('no item_spec.literacy.source_ids' in e for e in errors)
    assert any('source_grounding.status must be verified' in e for e in errors)
    assert any('material_mode' in e for e in errors)
    question['item_spec'] = {'literacy': {'source_ids': ['icomos-1964']},
                             'source_grounding': {'status': 'verified', 'proposition_map': [{'claim': 'x'}],
                                                  'material_mode': 'attributed_adaptation'}}
    assert grounding_item_errors(question, '國綜') == []
    assert grounding_item_errors(question, '國綜', sources={'other': {}}) == ['Q6: unknown source_ids [\'icomos-1964\']']
    exam = {'metadata': {'subject': '國綜'}, 'questions': [question]}
    assert not any(e.startswith('grounding:') for e in gates.subject_gate_errors(exam, authoring=True))


def test_group_items_inherit_audit_records_from_their_leader():
    leader = _chinese_item(6, '第一題', '共用材料')
    leader['item_spec'] = {'originality_record': {'candidate_count': 3}, 'subject_innovation_audit': {'subject': '國綜'},
                           'literacy': {'source_ids': ['s1']}, 'source_grounding': {'status': 'verified'},
                           'difficulty_design': {'band': 'easy'}}
    follower = _chinese_item(7, '第二題', '共用材料')
    follower['item_spec'] = {'inherits_audit_from': 'q6', 'difficulty_design': {'band': 'hard'}}
    assert appender.inherit_audits([follower], {'q6': leader}) == ['q7']
    spec = follower['item_spec']
    assert spec['originality_record'] == {'candidate_count': 3} and spec['literacy'] == {'source_ids': ['s1']}
    assert spec['audit_inherited_from'] == 'q6' and spec['difficulty_design'] == {'band': 'hard'}
    spec['originality_record']['candidate_count'] = 4
    assert leader['item_spec']['originality_record']['candidate_count'] == 3  # a copy, not a shared object
    stranger = _chinese_item(8, '第三題', '別的材料')
    stranger['item_spec'] = {'inherits_audit_from': 'q6'}
    with pytest.raises(ValueError, match='same group_stimulus'):
        appender.inherit_audits([stranger], {'q6': leader})
    orphan = _chinese_item(9, '第四題', '共用材料')
    orphan['item_spec'] = {'inherits_audit_from': 'q99'}
    with pytest.raises(ValueError, match='unknown item'):
        appender.inherit_audits([orphan], {'q6': leader})


def test_difficulty_plan_is_read_under_either_key():
    plan = {'basis': 'x', 'target_counts': {}, 'target_points': {}}
    assert balance.difficulty_plan({'paper_difficulty_plan': plan}) == plan
    assert balance.difficulty_plan({'difficulty_balance_plan': plan}) == plan
    assert balance.difficulty_plan({}) == {}


def test_skeleton_prints_official_subpart_labels():
    assert skeleton.subpart_label('1') == '(1)' and skeleton.subpart_label('2-1') == '(2)①'
    assert skeleton.subpart_label('2-2') == '(2)②' and skeleton.subpart_label('check') is None
    q32 = skeleton.skeleton('國綜', slot_id='q32-2-1')['question']
    assert q32['subpart_id'] == '2-1' and q32['answer_label'] == '(2)①'


def test_preflight_lists_authoring_requirements_per_subject():
    common = preflight.authoring_requirements('')
    assert any('curriculum_codes' in r for r in common) and any('inherits_audit_from' in r for r in common)
    chinese = preflight.authoring_requirements('國綜')
    assert len(chinese) == len(common) + 1 and '改寫自' in chinese[-1] and '①②研判' in chinese[-1]
    for subject, marker in (('數學A', 'scope_codes'), ('數學B', 'matrix, sphere/space'), ('國寫', '文長限80字以內'), ('自然', '12-19 多選'), ('英文', '中譯英 18-28 字')):
        assert any(marker in r for r in preflight.authoring_requirements(subject)[len(common):]), subject


def test_plan_checker_accepts_the_plan_as_a_flag(tmp_path):
    report = tmp_path / 'plan.json'
    subprocess.run([sys.executable, str(ROOT / 'scripts/check_paper_plan.py'), '--skeleton', '--subject', '國綜',
                    '--paper-id', 'flag-test', '--year', '116', '--report', str(report)], check=True, capture_output=True)
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}  # the report names 國綜 bands; decode it the way it is written
    positional = subprocess.run([sys.executable, str(ROOT / 'scripts/check_paper_plan.py'), str(report)],
                                capture_output=True, text=True, encoding='utf-8', env=env)
    flagged = subprocess.run([sys.executable, str(ROOT / 'scripts/check_paper_plan.py'), '--plan', str(report)],
                             capture_output=True, text=True, encoding='utf-8', env=env)
    assert flagged.returncode == positional.returncode
    assert json.loads(flagged.stdout)['status'] == json.loads(positional.stdout)['status']
