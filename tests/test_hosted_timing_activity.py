"""Activity estimates must not convert conversation waits into solved work."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import hosted_run_timing as timer
import run_hosted_workflow as workflow


def clock(tmp_path, monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(timer.time, 'time', lambda: now[0])
    path = tmp_path / 'generation-timing.json'
    def move(seconds, phase=None, **kwargs):
        now[0] += seconds
        return timer.transition(path, 'paper', phase, **kwargs)
    return path, move


def test_explicit_overnight_pause_and_resume(tmp_path, monkeypatch):
    path, move = clock(tmp_path, monkeypatch)
    move(0, 'solving', question_ids=['q20'], revision_id='v1')
    move(120, action='pause')
    move(14 * 3600, action='resume')
    report = move(90)
    result = timer.summary(report)
    assert result['wall_seconds'] == 14 * 3600 + 210
    assert result['agent_active_seconds'] == result['phase_seconds']['solving'] == 210
    assert result['waiting_seconds'] == 14 * 3600
    assert result['unobserved_seconds'] == 0
    assert result['target_met'] is False
    original = path.read_bytes()
    move(10)
    assert path.read_bytes() == original


def test_lost_turn_capped_at_last_heartbeat_plus_idle_threshold(tmp_path, monkeypatch):
    _, move = clock(tmp_path, monkeypatch)
    move(0, 'visual_qa')
    move(300, action='touch')
    report = move(5 * 3600)
    result = timer.summary(report)
    assert result['agent_active_seconds'] == 900
    assert result['unobserved_seconds'] == 5 * 3600 - 600
    assert result['waiting_seconds'] == 0  # only an explicit pause is a wait
    assert result['wall_seconds'] == 5 * 3600 + 300


def test_recorded_tools_refresh_activity_without_polluting_state_hash(tmp_path, monkeypatch):
    _, move = clock(tmp_path, monkeypatch)
    move(0, 'visual_qa')
    events = [{'started_at': 1500, 'elapsed_seconds': 900},
              {'started_at': 6000, 'elapsed_seconds': 30}]
    (tmp_path / 'workflow-events.jsonl').write_text('\n'.join(json.dumps(e) for e in events), encoding='utf-8')
    report = move(5100)
    result = timer.summary(report, events)
    assert result['wall_seconds'] == 5100
    assert result['agent_active_seconds'] == 2100
    assert result['unobserved_seconds'] == 3000 and result['waiting_seconds'] == 0
    assert result['tool_seconds'] == 930
    assert not any(r['start'] < 2400 and r['end'] > 1500 and r.get('state') != 'active'
                   for r in report['intervals'])


def test_legacy_clock_is_not_reconstructed(tmp_path):
    report = {'paper_id': 'paper', 'active': None, 'intervals': [
        {'phase': 'solving', 'start': 1, 'end': 14 * 3600}]}
    result = timer.summary(report)
    assert result['agent_active_seconds'] is None
    assert result['unclassified_seconds'] == 14 * 3600 - 1
    assert result['waiting_seconds'] == 0


def test_tool_union_is_subset_of_wall_time(tmp_path, monkeypatch):
    _, move = clock(tmp_path, monkeypatch)
    move(0, 'render_repair')
    report = move(60)
    events = [{'started_at': 990, 'elapsed_seconds': 30},
              {'started_at': 1010, 'elapsed_seconds': 30},
              {'started_at': 1050, 'elapsed_seconds': 100}]
    result = timer.summary(report, events)
    assert result['tool_seconds'] == 50
    assert result['wall_seconds'] == 60


def test_backward_clock_after_finish_does_not_rewrite(tmp_path, monkeypatch):
    path, move = clock(tmp_path, monkeypatch)
    move(0, 'authoring')
    move(10)
    original = path.read_bytes()
    with pytest.raises(ValueError, match='backwards'):
        move(-20, 'solving')
    assert path.read_bytes() == original


def test_clock_updates_selected_review_state_hash(tmp_path, monkeypatch):
    path, move = clock(tmp_path, monkeypatch)
    move(0, 'visual_qa')
    state_path = tmp_path / 'v3-review-run-state.json'
    workflow.save(state_path, {'paper_id': 'paper', 'pdfs': {'unchanged': 'review'}, 'timing': {}})
    move(10, action='touch')
    workflow.clock(state_path, 'pause')
    state = workflow.read(state_path)
    assert state['timing']['sha256'] == workflow.digest(path)
    assert state['pdfs'] == {'unchanged': 'review'}


def test_content_lock_rejects_changed_answer_and_requires_explicit_revision(tmp_path):
    exam_path, state_path = tmp_path / 'exam.json', tmp_path / 'run-state.json'
    workflow.save(exam_path, {'answers': [{'question_id': 'q1', 'answer': 'A'}]})
    state = {'paper_id': 'paper', 'exam': workflow.record(tmp_path, exam_path)}
    workflow.save(state_path, state)
    workflow.content_lock(state_path)
    workflow.check_content_lock(tmp_path, state)
    workflow.save(exam_path, {'answers': [{'question_id': 'q1', 'answer': 'B'}]})
    state['exam'] = workflow.record(tmp_path, exam_path)
    workflow.save(state_path, state)
    with pytest.raises(ValueError, match='Locked content changed'):
        workflow.check_content_lock(tmp_path, state)
    with pytest.raises(ValueError, match='re-solve/review'):
        workflow.content_lock(state_path)
    workflow.content_lock(state_path, reason='Recomputed q1; prior answer review must be renewed')
    lock = workflow.read(tmp_path / 'content-lock.json')
    assert lock['previous']['identity']['exam_content_sha256'] != lock['identity']['exam_content_sha256']
    workflow.check_content_lock(tmp_path, state)
    # Author-only difficulty labels and review metadata never break the lock.
    workflow.save(exam_path, {'answers': [{'question_id': 'q1', 'answer': 'B', 'difficulty_label': '難'}],
                              'questions': [], 'metadata': {'paper_difficulty_plan': {'hard': 30}}})
    state['exam'] = workflow.record(tmp_path, exam_path)
    workflow.save(state_path, state)
    workflow.check_content_lock(tmp_path, state)


def test_content_lock_binds_diagram_bytes(tmp_path):
    figure = tmp_path / 'figure.svg'
    figure.write_text('<svg/>', encoding='utf-8')
    exam, state_path = tmp_path / 'exam.json', tmp_path / 'run-state.json'
    workflow.save(exam, {'questions': [{'id': 'q1', 'visual_asset': {
        'path': 'figure.svg', 'sha256': workflow.digest(figure)}}]})
    state = {'paper_id': 'paper', 'exam': workflow.record(tmp_path, exam)}
    workflow.save(state_path, state)
    workflow.content_lock(state_path)
    figure.write_text('<svg>changed</svg>', encoding='utf-8')
    with pytest.raises(ValueError, match='asset hash changed'):
        workflow.check_content_lock(tmp_path, state)


def test_old_estimated_waiting_rows_count_as_unobserved():
    report = {'paper_id': 'paper', 'active': None, 'started_at': 0, 'ended_at': 300, 'intervals': [
        {'phase': 'authoring', 'start': 0, 'end': 100, 'state': 'active'},
        {'phase': 'authoring', 'start': 100, 'end': 250, 'state': 'waiting', 'estimated': True},
        {'phase': 'authoring', 'start': 250, 'end': 300, 'state': 'waiting', 'estimated': False}]}
    result = timer.summary(report)
    assert result['unobserved_seconds'] == 150 and result['waiting_seconds'] == 50
    assert result['unobserved_by_phase'] == {'authoring': 150}
    assert result['phase_seconds']['authoring'] == 100
