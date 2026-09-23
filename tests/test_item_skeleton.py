"""Exact profile skeletons save lookup work, without generating evidence."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import jsonschema
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from emit_item_skeleton import SUBJECTS,skeleton
from validate_math_difficulty_design import profile_for,profile_targets,required_decisions,validate_item
from validate_paper_difficulty_balance import content_hash

SCHEMA=json.loads((ROOT/'schemas/difficulty-design.schema.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('subject',['數學A','數學B'])
@pytest.mark.parametrize('number',range(1,21))
def test_math_slot_copies_exact_targets_and_has_no_passing_review(subject,number):
    result=skeleton(subject,number)
    q=result['question'];design=q['item_spec']['difficulty_design']
    official=profile_targets(profile_for(subject));target=official.get(number,{})
    assert result['status']=='pending-authoring'
    assert q['prompt'] is None and result['answer']['final_answer'] is None
    assert all(option['text'] is None for option in q['options'])
    assert design['target_p_center']==target.get('p_center')
    assert design['target_p_range']==target.get('p_range')
    assert design['target_d_floor']==target.get('discrimination_floor')
    assert design['minimum_linked_decisions']==required_decisions(target.get('p_center'),number,q['type'])
    assert all(row['description'] is None for row in design['linked_decisions'])
    assert design['content_sha256'] is None and design['band'] is None
    assert design['expert_estimate']['status']=='pending'
    assert design['shortcut_audit']['reviewer_decision']=='pending'
    assert design['innovation_audit']['reviewer_decision']=='pending'
    assert design['time_audit']['hand_calculation_feasible'] is None
    jsonschema.validate(design,SCHEMA)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(design,SCHEMA['$defs']['completedMathDesign'])
    assert validate_item(q,official,subject)[0]  # Pending draft cannot pass actual gate.


@pytest.mark.parametrize('subject',[s for s in SUBJECTS if s not in {'數學A','數學B'}])
def test_non_math_has_no_invented_math_difficulty_targets(subject):
    result=skeleton(subject,1,'1' if subject=='國寫' else None)
    assert result['requirements']['difficulty_profile']['target'] is None
    assert result['requirements']['difficulty_profile']['minimum_linked_decisions'] is None
    design=result['question']['item_spec']['difficulty_design']
    assert 'target_p_center' not in design and 'minimum_linked_decisions' not in design
    assert design['band'] is None
    jsonschema.validate(design,SCHEMA)


def test_math_b_conditional_floor_is_explicit_not_a_fabricated_review():
    r=skeleton('數學B',13)
    constraints=r['requirements']['math_b_conditions']
    assert constraints['opening_fill_in'] is True
    assert constraints['easy_medium_minimum_linked_decisions']>=3
    assert constraints['opening_fill_in_minimum_representation_plus_constraint_checks']==2
    assert r['question']['item_spec']['difficulty_design']['constraint_checks'] is None


def test_field_contract_names_exact_hash_inputs_and_enums():
    text=(ROOT/'references/difficulty-field-contract.md').read_text(encoding='utf-8')
    for field in ('content_sha256','prompt','group_stimulus','options','visual_asset',
                  'continuation_pages','group_stimulus_page_splits','response_format_table'):
        assert field in text
    q=skeleton('數學A',1)['question'];q['prompt']='Synthetic statement'
    baseline=content_hash(q)
    changed=copy.deepcopy(q);changed['options'][0]['text']='Changed condition'
    assert content_hash(changed)!=baseline
    changed=copy.deepcopy(q);changed['item_spec']['difficulty_design']['band']='中'
    assert content_hash(changed)==baseline


def test_cli_emits_pending_json_and_preserves_existing_work(tmp_path):
    output=tmp_path/'q14.json'
    command=[sys.executable,str(ROOT/'scripts/emit_item_skeleton.py'),'--subject','數學A',
             '--number','14','--output',str(output)]
    first=subprocess.run(command,cwd=tmp_path,capture_output=True,timeout=30)
    assert first.returncode==0,first.stderr
    data=output.read_bytes()
    assert json.loads(data)['status']=='pending-authoring'
    second=subprocess.run(command,cwd=tmp_path,capture_output=True,timeout=30)
    assert second.returncode!=0 and output.read_bytes()==data


def test_unknown_slot_is_not_guessed():
    with pytest.raises(ValueError,match='No unique current numbered slot'):
        skeleton('數學A',21)
    with pytest.raises(ValueError,match='--subpart'):
        skeleton('國寫',1)
    assert skeleton('國寫',1,'1')['question']['score']==4
    assert skeleton('國寫',1,'2')['question']['score']==21
    first,second,essay=(skeleton('國寫',1,'1')['question'],skeleton('國寫',1,'2')['question'],skeleton('國寫',2)['question'])
    assert (first['number_display'],second['number_display'],essay['number_display'])==('一、','','二、')
    assert (first['answer_label'],second['answer_label'],essay['answer_label'])==('一、問題（一）','一、問題（二）','二、')


@pytest.mark.parametrize('slot',['translation-1','translation-2','composition'])
def test_english_unnumbered_slots_keep_printed_labels(slot):
    q=skeleton('英文',slot_id=slot)['question']
    assert q['id']==slot and q['number'] is None and q['number_display']
