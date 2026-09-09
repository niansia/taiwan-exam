"""Handoff integration regressions; these tests do not certify exam quality."""
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import validate_exam_pack_contract as gate
import validate_exam_release as release
import render_exam
import render_gsat_official
import render_gsat_internal_review
from pack_verification import digest
from validate_paper_difficulty_balance import content_hash


def sample():
    q = dict(id='q1', number=1, section_id='s', type='single_choice',
             prompt='Fixture only', score=1, options=[dict(label='A',text='1'),dict(label='B',text='2')])
    a = dict(question_id='q1',final_answer='A',reasoning=['Fixture reasoning'])
    a['independent_review'] = dict(question_sha256=content_hash(q),answer_sha256=digest(a),
          reviewer='unit-test',reviewed_at='2026-09-09',answer_visible_during_solve=False,
          solution='Fixture solution',shortest_route='Fixture route',difficulty_rationale='Fixture only',
          option_verdicts={'A':'True for fixture','B':'False for fixture'},derived_answer='A',unresolved=[])
    return dict(metadata=dict(exam='學測',subject='英文',generation_mode='full-paper'),
                questions=[q],answers=[a],sections=[dict(id='s',title='fixture')],instructions=[])


def test_bound_answer_review_and_staleness():
    d=sample()
    assert release.independent_answer_errors(d)==[]
    d['questions'][0]['prompt']='changed'
    assert release.independent_answer_errors(d)
    d=sample();d['answers'][0]['final_answer']='B'
    assert release.independent_answer_errors(d)


def test_missing_option_review_and_source_id():
    d=sample();d['answers'][0]['independent_review']['option_verdicts']={'A':'yes'}
    assert release.independent_answer_errors(d)
    d['questions'][0]['item_spec']={'literacy':{'source_ids':['missing']}}
    assert release.source_link_errors(d,[]) != []
    assert release.source_link_errors(d,[{'id':'missing'}]) == []


def test_generic_fullpaper_cannot_bypass_with_verified_label():
    d={'metadata':{'generation_mode':'full-paper','layout_fidelity_status':'verified'}}
    with pytest.raises(ValueError,match='generic renderer'):
        render_exam.render_exam(d)
    d['metadata']['generation_mode']='custom-practice'
    d['metadata']['paper_profile_id']='pretend-preview'
    with pytest.raises(ValueError,match='generic renderer'):
        render_exam.render_exam(d)


def test_subject_renderers_require_contract(tmp_path):
    d=sample()
    with pytest.raises(ValueError,match='handoff blocked'):
        render_gsat_official.render(d)
    with pytest.raises(ValueError,match='handoff blocked'):
        render_gsat_internal_review.render(d,base=tmp_path)


def test_adapter_invokes_same_gate_and_propagates_failures(tmp_path,monkeypatch):
    d=sample(); d['metadata']['run_contract']='contract.json'
    (tmp_path/'contract.json').write_text('{}')
    calls=[]
    def failed(exam_path,contract_path,stage):
        assert exam_path.parent == tmp_path  # relative asset lookup must survive
        calls.append((json.loads(exam_path.read_text(encoding='utf-8')),contract_path,stage))
        return dict(status='fail',errors=['actual subject check failed'])
    monkeypatch.setattr(release,'validate',failed)
    with pytest.raises(ValueError,match='actual subject check failed'):
        gate.require_handoff(d,tmp_path)
    assert calls[0][1]==tmp_path/'contract.json'
    assert calls[0][2]=='content'
    assert calls[0][0]['questions']==d['questions']
    assert not list(tmp_path.glob('.exam-content-handoff-*.json'))
    monkeypatch.setattr(release,'validate',lambda *a,**kw:dict(status='pass-content-evidence',errors=[]))
    gate.require_handoff(d,tmp_path)  # Adapter only, not educational acceptance.


def test_real_failed_suite_cannot_reach_subject_rendering():
    files=list((ROOT/'output/pdf/116學測模擬考壓力測試/json').glob('*.json'))
    if not files:pytest.skip('private stress data is not distributed')
    for path in files:
        d=json.loads(path.read_text(encoding='utf-8-sig'))
        with pytest.raises(ValueError,match='handoff blocked'):
            gate.require_handoff(d,path.parent)


def test_contract_override_preserves_exam_and_rejects_conflict(tmp_path,monkeypatch):
    d=sample(); original=json.dumps(d,sort_keys=True)
    contract=tmp_path/'request.json';contract.write_text('{}',encoding='utf-8')
    monkeypatch.setattr(release,'validate',lambda *a,**kw:dict(status='pass-content-evidence',errors=[]))
    gate.require_handoff(d,tmp_path,contract)
    assert json.dumps(d,sort_keys=True)==original
    d['metadata']['run_contract']='another.json'
    with pytest.raises(ValueError,match='disagree'):
        gate.require_handoff(d,tmp_path,contract)


def test_answer_schema_supports_current_review_and_four_band_label():
    jsonschema=pytest.importorskip('jsonschema')
    a=sample()['answers'][0]
    a.update(verification_status='independently_verified',difficulty_label='簡單')
    schema=json.loads((ROOT/'schemas/answer.schema.json').read_text(encoding='utf-8'))
    jsonschema.validate(a,schema)
