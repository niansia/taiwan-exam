"""Persistence-only fixtures: no generated exam or fabricated QA approval."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import append_items as appender
import run_hosted_workflow as workflow
from hosted_run_timing import transition


def item(number):
    return {'id': 'q'+str(number), 'number': number, 'section_id': 'test',
            'type': 'constructed_response', 'prompt': 'Synthetic persistence item '+str(number)}


def batch(numbers):
    return {'questions': [item(n) for n in numbers], 'answers': [
        {'question_id': 'q'+str(n), 'final_answer': n, 'reasoning': ['Synthetic stored reasoning'],
         'verification_status': 'unverified'} for n in numbers]}


@pytest.fixture
def run(tmp_path):
    workflow.save(tmp_path/'preflight.json', {'status': 'ready-for-authoring', 'paper_id': 'p',
        'subject': '英文', 'review_mode': 'single-context', 'require_independent_review': False,
        'calibration': {}, 'template_asset_dir': 'templates'})
    transition(tmp_path/'generation-timing.json', 'p', 'reference_preflight')
    plan = {'metadata': {'title': 'Synthetic persistence only', 'exam': '學測',
                        'calibration_level': 'exploratory-uncalibrated', 'custom_note': 'Preserve metadata'},
            'sections': [{'id': 'test', 'title': 'Synthetic section'}], 'instructions': ['Not an exam.']}
    workflow.save(tmp_path/'plan.json', plan)
    workflow.save(tmp_path/'batch.json', batch([1, 2]))
    return tmp_path


def append(run, **kwargs):
    return appender.append(run, run/'batch.json', plan=run/'plan.json', **kwargs)


def test_first_batch_materializes_content_and_preserves_previous_items(run):
    assert not (run/'exam.json').exists()
    first = append(run)
    assert first['question_count'] == 2 and first['reviews_approved_by_tool'] is False
    exam = workflow.read(run/'exam.json')
    assert exam['metadata']['paper_id'] == 'p' and exam['metadata']['subject'] == '英文'
    assert exam['metadata']['custom_note'] == 'Preserve metadata'
    assert all(a['verification_status'] == 'unverified' for a in exam['answers'])
    state = workflow.read(run/'run-state.json')
    assert state['checks'] == {} and state['pdfs'] == {} and state['content_status'] == 'pending-review'
    assert state['exam'] == workflow.record(run, run/'exam.json')
    old = copy.deepcopy(exam['questions'])
    workflow.save(run/'batch.json', batch([3, 4]))
    assert append(run)['question_count'] == 4
    assert workflow.read(run/'exam.json')['questions'][:2] == old
    assert workflow.read(run/'generation-timing.json')['active']['phase'] == 'authoring'


def test_scored_subparts_share_printed_number_without_losing_either(run):
    data=batch([1,2])
    for i,(q,a) in enumerate(zip(data['questions'],data['answers']),1):
        q.update(id=f'q1-{i}',number=1,subpart_id=str(i))
        a['question_id']=q['id']
    workflow.save(run/'batch.json',data)
    append(run)
    assert [q['id'] for q in workflow.read(run/'exam.json')['questions']]==['q1-1','q1-2']
    assert append(run)['idempotent_replay']
    bad=batch([1]);workflow.save(run/'batch.json',bad)
    with pytest.raises(ValueError,match='collides'):append(run)


def test_unnumbered_translation_tasks_preserve_labels_and_order(run):
    data=batch([1,2])
    for i,q in enumerate(data['questions'],1):q.update(number=None,answer_label=f'Translation {i}')
    workflow.save(run/'batch.json',data);append(run)
    exam=workflow.read(run/'exam.json')
    assert [q['answer_label'] for q in exam['questions']]==['Translation 1','Translation 2']
    assert append(run)['idempotent_replay']


def test_planning_only_rows_do_not_pollute_exam_schema(run):
    plan=workflow.read(run/'plan.json');plan.update(items=[{'id':'pending-plan'}],answer_distribution_plan=[])
    workflow.save(run/'plan.json',plan);append(run)
    assert set(workflow.read(run/'exam.json'))=={'metadata','instructions','sections','questions','answers'}


def test_identical_replay_preserves_exam_bytes_and_clock(run):
    append(run)
    exam = (run/'exam.json').read_bytes()
    clock = (run/'generation-timing.json').read_bytes()
    replay = append(run)
    assert replay['idempotent_replay'] and replay['changed_item_ids'] == []
    assert (run/'exam.json').read_bytes() == exam
    assert (run/'generation-timing.json').read_bytes() == clock


def test_crash_after_atomic_exam_save_can_replay_without_loss(run, monkeypatch):
    original = appender.checkpoint
    def interrupted(*args, **kwargs):
        raise RuntimeError('Simulated interruption before checkpoint')
    monkeypatch.setattr(appender, 'checkpoint', interrupted)
    with pytest.raises(RuntimeError, match='Simulated interruption'):
        append(run)
    persisted = (run/'exam.json').read_bytes()
    assert len(workflow.read(run/'exam.json')['questions']) == 2
    assert not (run/'run-state.json').exists()
    monkeypatch.setattr(appender, 'checkpoint', original)
    resumed = append(run)
    assert resumed['idempotent_replay'] and resumed['question_count'] == 2
    assert (run/'exam.json').read_bytes() == persisted
    assert workflow.read(run/'run-state.json')['exam'] == workflow.record(run, run/'exam.json')


def test_replace_requires_explicit_flag_and_keeps_old_reviews_stale(run):
    append(run)
    old_hash = workflow.digest(run/'exam.json')
    report = {'exam_sha256': old_hash, 'status': 'pass', 'observations': 'Synthetic fixture review only'}
    workflow.save(run/'answers.json', report)
    workflow.checkpoint(run)
    supplied = batch([1, 2]); supplied['questions'][0]['prompt'] = 'Corrected synthetic statement'
    workflow.save(run/'batch.json', supplied)
    with pytest.raises(ValueError, match='--replace'):
        append(run)
    assert workflow.digest(run/'exam.json') == old_hash
    result = append(run, replace=True)
    assert result['changed_item_ids'] == ['q1']
    saved = workflow.read(run/'run-state.json')
    assert saved['exam']['sha256'] != old_hash and saved['content_status'] == 'pending-review'
    assert workflow.read(run/'answers.json') == report
    assert workflow.read(run/'answers.json')['exam_sha256'] != saved['exam']['sha256']


@pytest.mark.parametrize('bad', ['duplicate-id', 'duplicate-number', 'number-collision', 'missing-answer',
                                 'missing-prompt', 'missing-reasoning', 'invalid-reasoning', 'unknown-section', 'too-many'])
def test_invalid_batch_cannot_change_saved_exam_or_checkpoint(run, bad):
    append(run)
    supplied = batch([3, 4])
    if bad == 'duplicate-id': supplied['questions'][1]['id'] = 'q3'
    elif bad == 'duplicate-number': supplied['questions'][1]['number'] = 3
    elif bad == 'number-collision': supplied['questions'][0]['number'] = 1
    elif bad == 'missing-answer': supplied['answers'].pop()
    elif bad == 'missing-prompt': supplied['questions'][0].pop('prompt')
    elif bad == 'missing-reasoning': supplied['answers'][0].pop('reasoning')
    elif bad == 'invalid-reasoning': supplied['answers'][0]['reasoning'] = True
    elif bad == 'unknown-section': supplied['questions'][0]['section_id'] = 'missing'
    else: supplied = batch([3, 4, 5, 6, 7, 8, 9])
    workflow.save(run/'batch.json', supplied)
    original = {name: (run/name).read_bytes() for name in ('exam.json', 'run-state.json', 'generation-timing.json')}
    with pytest.raises(ValueError): append(run, replace=True)
    assert {name: (run/name).read_bytes() for name in original} == original


def test_append_to_latest_candidate_keeps_review_progress_for_old_bytes(run):
    append(run)
    state = workflow.read(run/'run-state.json')
    state['next_action'] = 'Existing review progress'
    state['review_mode'] = 'single-context'
    state['custom_progress'] = {'inspected_item': 'q1'}
    workflow.save(run/'latest-run-state.json', state)
    original = (run/'run-state.json').read_bytes()
    workflow.save(run/'batch.json', batch([3]))
    append(run, state=run/'latest-run-state.json')
    updated = workflow.read(run/'latest-run-state.json')
    assert updated['custom_progress'] == {'inspected_item': 'q1'}
    assert updated['review_mode'] == 'single-context'
    assert updated['content_status'] == 'pending-review'
    assert (run/'run-state.json').read_bytes() == original


def test_first_batch_does_not_invent_a_paper_plan(run):
    with pytest.raises(ValueError, match='requires --plan'):
        appender.append(run, run/'batch.json')
    assert not (run/'exam.json').exists()


def test_saving_lists_the_final_check_design_fields_still_missing(run, tmp_path_factory):
    first = append(run)  # 英文: the paper-balance fields apply to every subject
    assert first['design_fields_pending']['missing four-band estimate'] == ['q1', 'q2']
    assert 'page reviews stay valid' in first['design_note']
    math = tmp_path_factory.mktemp('math')
    for name in ('preflight.json', 'plan.json', 'generation-timing.json'):
        (math/name).write_bytes((run/name).read_bytes())
    preflight = workflow.read(math/'preflight.json')
    workflow.save(math/'preflight.json', {**preflight, 'subject': '數學A'})
    workflow.save(math/'batch.json', batch([1]))
    append(math)
    workflow.save(math/'batch.json', batch([2]))
    gaps = append(math)['design_fields_pending']
    assert all(ids == ['q2'] for ids in gaps.values())  # only the batch just saved
    assert gaps['missing difficulty_design'] == ['q2']  # the Math A/B design gate
