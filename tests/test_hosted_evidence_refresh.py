"""Evidence freshness, refresh drafts and the figure self-check: mechanics only, never review content."""
import json
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_hosted_run as gate
import hosted_evidence_refresh as evidence
import run_hosted_workflow as workflow
from hosted_blind_review import packet
from test_hosted_run_evidence import saved_run, fixed_evidence_pdfs  # noqa: F401  (fixtures)


def _state():
    return json.loads(Path('run-state.json').read_text(encoding='utf-8'))


def _exam():
    return json.loads(Path('exam.json').read_text(encoding='utf-8'))


def _change_item(item_id, prompt):
    """Edit one item, save the exam, and re-register it as the checker would after a checkpoint."""
    exam = _exam()
    next(q for q in exam['questions'] if q['id'] == item_id)['prompt'] = prompt
    Path('exam.json').write_text(json.dumps(exam), encoding='utf-8')
    state = _state()
    state['exam'] = {'path': 'exam.json', 'sha256': gate.sha(Path('exam.json'))}
    Path('run-state.json').write_text(json.dumps(state), encoding='utf-8')
    return state, exam


def test_complete_fixture_evidence_is_current(saved_run):
    report = evidence.evidence_gaps(Path('.'), _state(), _exam())
    assert report['ready'] is True and report['attention'] == []
    assert set(report['gates']) == set(gate.ITEM_GATES + gate.PAPER_GATES)


def test_incomplete_rows_and_missing_reports_are_named_in_checker_terms(saved_run):
    answers = json.loads(Path('answers.json').read_text(encoding='utf-8'))
    answers['items'][1].update(status='pending', observations='')
    Path('answers.json').write_text(json.dumps(answers), encoding='utf-8')
    Path('source_grounding.json').unlink()
    report = evidence.evidence_gaps(Path('.'), _state(), _exam())
    assert report['ready'] is False
    assert report['gates']['answers']['status'] == 'incomplete'
    assert any('rows pending or without observations: 1' in p for p in report['gates']['answers']['problems'])
    assert report['gates']['source_grounding']['status'] == 'missing'
    assert report['attention'] == ['answers', 'source_grounding']


def test_refresh_drafts_retain_unchanged_rows_and_never_write_a_pass(saved_run):
    old_state = _state()
    evidence.record_history(Path('.'), old_state['exam']['sha256'], _exam())
    before = {name: gate.sha(Path(name + '.json')) for name in gate.ITEM_GATES + gate.PAPER_GATES}
    state, exam = _change_item('2', 'Rewritten synthetic prompt')
    report = evidence.evidence_gaps(Path('.'), state, exam)
    assert all(v['status'] == 'stale' for v in report['gates'].values())
    assert report['gates']['answers']['items'] == {'changed': ['2'], 'added': [], 'removed': []}

    result = evidence.refresh(Path('.'), state, exam)
    assert result['status'] == 'review-pending' and result['reviews_approved_by_tool'] is False
    assert set(result['drafts']) == set(gate.ITEM_GATES + gate.PAPER_GATES)
    # The registered reports are untouched: a draft is a separate file the checker never reads.
    assert {name: gate.sha(Path(name + '.json')) for name in before} == before
    draft = json.loads(Path('answers.draft.json').read_text(encoding='utf-8'))
    assert draft['status'] == 'pending' and draft['observations'] == ''
    assert draft['exam_sha256'] == state['exam']['sha256']
    rows = {row['id']: row for row in draft['items']}
    assert rows['2'] == {'id': '2', 'status': 'pending', 'observations': ''}
    assert rows['0']['status'] == 'pass' and rows['0']['observations'] == 'Fixture observation'
    assert draft['refresh']['retained_rows'] == ['0', '1', '3'] and draft['refresh']['pending_rows'] == ['2']
    difficulty = json.loads(Path('difficulty.draft.json').read_text(encoding='utf-8'))
    blind = Path(difficulty['blind_packet']['path'])
    assert json.loads(blind.read_text(encoding='utf-8')) == packet(exam)
    assert difficulty['blind_packet']['sha256'] == gate.sha(blind)
    # Copying a draft wholesale cannot pass: the checker still sees pending rows.
    Path('answers.json').write_text(json.dumps(draft), encoding='utf-8')
    state['checks']['answers'] = {'path': 'answers.json', 'sha256': gate.sha(Path('answers.json'))}
    Path('run-state.json').write_text(json.dumps(state), encoding='utf-8')
    errors = gate.check(Path('run-state.json'))['errors']
    assert any(e.startswith('answers/2: review pending') for e in errors)
    assert any(e.startswith('answers: missing passing review') for e in errors)


def test_refresh_without_history_leaves_every_row_pending(saved_run):
    state, exam = _change_item('1', 'Another rewritten prompt')
    result = evidence.refresh(Path('.'), state, exam)
    draft = json.loads(Path('visuals.draft.json').read_text(encoding='utf-8'))
    assert all(row['status'] == 'pending' for row in draft['items'])
    assert draft['refresh']['history_known'] is False
    assert result['drafts']['visuals'] == {'path': str(Path('visuals.draft.json')), 'retained_rows': 0,
                                           'pending_rows': 4, 'paper_level': 'pending'}


def test_checkpoint_reports_evidence_attention_and_records_history(tmp_path):
    workflow.save(tmp_path / 'preflight.json', {'status': 'ready-for-authoring', 'paper_id': 'id',
        'subject': '英文', 'review_mode': 'single-context', 'require_independent_review': False,
        'calibration': {}, 'template_asset_dir': 'templates'})
    workflow.save(tmp_path / 'exam.json', {'metadata': {'paper_id': 'id', 'subject': '英文'},
                                          'questions': [{'id': 'q1', 'prompt': 'one'}]})
    result = workflow.checkpoint(tmp_path, 'authoring')
    assert result['evidence_ready'] is False
    assert set(result['evidence_attention']) == set(gate.ITEM_GATES + gate.PAPER_GATES)
    assert all(v['status'] == 'missing' for v in result['evidence_attention'].values())
    first = workflow.digest(tmp_path / 'exam.json')
    workflow.save(tmp_path / 'answers.json', {'exam_sha256': first, 'status': 'pass', 'observations': 'real note',
                                             'items': [{'id': 'q1', 'status': 'pass', 'observations': 'seen'}]})
    result = workflow.checkpoint(tmp_path)
    assert 'answers' not in result['evidence_attention']
    workflow.save(tmp_path / 'exam.json', {'metadata': {'paper_id': 'id', 'subject': '英文'},
                                          'questions': [{'id': 'q1', 'prompt': 'one'}, {'id': 'q2', 'prompt': 'two'}]})
    result = workflow.checkpoint(tmp_path)
    stale = result['evidence_attention']['answers']
    assert stale['status'] == 'stale' and stale['reviewed_exam_sha256'] == first
    assert stale['items'] == {'changed': [], 'added': ['q2'], 'removed': []}
    history = workflow.read(tmp_path / evidence.HISTORY)
    assert set(history['exams']) == {first, workflow.digest(tmp_path / 'exam.json')}
    refreshed = workflow.refresh_evidence(tmp_path / 'run-state.json')
    assert refreshed['status'] == 'review-pending' and refreshed['content_lock'] == 'absent'
    assert refreshed['drafts']['answers']['retained_rows'] == 1 and refreshed['drafts']['answers']['pending_rows'] == 1


def _svg(body, width=200, height=100):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{body}</svg>').encode('utf-8')


def test_figure_selfcheck_reports_machine_visible_defects(tmp_path):
    (tmp_path / 'clean.svg').write_bytes(_svg('<path d="M10 80 L190 80" stroke="black" stroke-width="1"/>'
                                              '<text x="20" y="30" font-size="12">A</text>'))
    (tmp_path / 'colour.svg').write_bytes(_svg('<rect x="0" y="0" width="200" height="100" fill="red"/>'))
    (tmp_path / 'collide.svg').write_bytes(_svg('<path d="M10 50 L190 50" stroke="black" stroke-width="1"/>'
                                                '<text x="80" y="54" font-size="12">label</text>'))
    (tmp_path / 'page.png').write_bytes(b'<!DOCTYPE html><html><body>blocked</body></html>')
    (tmp_path / 'empty.svg').write_bytes(b'')

    def asset(name):
        path = tmp_path / name
        return {'path': name, 'sha256': workflow.digest(path) if path.exists() else '0' * 64, 'width_percent': 60}

    exam = {'questions': [
        {'id': '1', 'visual_asset': asset('clean.svg')},
        {'id': '2', 'visual_asset': asset('colour.svg')},
        {'id': '3', 'visual_asset': asset('collide.svg')},
        {'id': '4', 'visual_asset': asset('page.png')},
        {'id': '5', 'visual_asset': asset('missing.svg')},
        {'id': '6', 'visual_asset': asset('empty.svg')},
        {'id': '7', 'visual_asset': {**asset('clean.svg'), 'sha256': 'f' * 64}},
    ]}
    report = evidence.figure_selfcheck(tmp_path, exam, asset_issues=workflow.asset_issues)
    by_id = {f['referenced_by']: f for f in report['figures']}
    assert report['status'] == 'pending' and report['figure_count'] == 7
    assert by_id['item 1.visual_asset']['errors'] == [] and by_id['item 1.visual_asset']['warnings'] == []
    assert any('carry colour' in w for w in by_id['item 2.visual_asset']['warnings'])
    assert any('labels sit on strokes: label' in w for w in by_id['item 3.visual_asset']['warnings'])
    assert any('HTML page saved under an image name' in e for e in by_id['item 4.visual_asset']['errors'])
    assert any('missing' in e for e in by_id['item 5.visual_asset']['errors'])
    assert any('0 bytes' in e for e in by_id['item 6.visual_asset']['errors'])
    assert any('redrawn after the item was saved' in e for e in by_id['item 7.visual_asset']['errors'])
    assert 'proof crop' in report['note']


def test_figure_selfcheck_passes_a_clean_exam_and_flags_risky_glyphs(tmp_path):
    (tmp_path / 'glyphs.svg').write_bytes(_svg('<text x="20" y="40" font-size="12">10⁻⁴ mol</text>'))
    exam = {'questions': [{'id': '1', 'visual_asset': {'path': 'glyphs.svg', 'sha256': workflow.digest(tmp_path / 'glyphs.svg'),
                                                         'width_percent': 50}}]}
    report = evidence.figure_selfcheck(tmp_path, exam, asset_issues=workflow.asset_issues)
    assert report['status'] == 'pass' and report['errors'] == 0
    assert any('U+207B' in w and 'U+2074' in w for w in report['figures'][0]['warnings'])
