"""Honest single-context fallback without relaxing content or identity checks."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from hosted_blind_review import packet, review_errors
from hosted_calibration import SUBJECTS
import prepare_hosted_run as preflight
from test_hosted_run_evidence import saved_run, fixed_evidence_pdfs, evaluate


def row(number=1):
    return {'id': str(number), 'shortest_route': 'Synthetic independent derivation route',
            'decisive_steps': ['Compare constraints', 'Exclude alternative', 'Derive requested result'],
            'shortcut_search': 'Synthetic shortcut audit', 'anchor_comparison': 'Synthetic calibration comparison',
            'expected_minutes': 4.25, 'difficulty_band': 'easy', 'unresolved': [],
            'routine_only': False, 'uses_prior_results': [], 'scaffolding_audit': 'No prior result in this fixture',
            'answer_recheck': 'Synthetic fresh calculation gives 8, matching saved answer'}


def review(rows):
    return {'review_mode': 'single-context', 'author_context': 'actual-session',
            'reviewer_context': 'actual-session', 'independent_review': False,
            'review_reason': 'Only one model context is available in this test fixture', 'items': rows}


@pytest.mark.parametrize('subject', SUBJECTS)
def test_single_context_supported_for_all_subjects_with_honest_packet(subject):
    exam = {'metadata': {'subject': subject}, 'questions': [{'id': '1', 'prompt': 'Synthetic task',
            'item_spec': {'difficulty': 'author label'}}],
            'answers': [{'question_id': '1', 'final_answer': 8, 'reasoning': ['Saved route']}]}
    assert review_errors(exam, review([row()])) == []
    stripped = packet(exam, 'single-context')
    assert 'answers' not in stripped and 'item_spec' not in stripped['questions'][0]
    assert packet(exam)['answers'][0]['final_answer'] == 8  # Legacy packet unchanged.


@pytest.mark.parametrize('change', ['false-independence', 'fake-context', 'missing-recheck', 'missing-reason', 'unknown-mode'])
def test_fallback_requires_actual_rechecks_and_honest_claims(change):
    exam = {'metadata': {'subject': '英文'}, 'questions': [{'id': '1'}]}
    r = review([row()])
    if change == 'false-independence': r['independent_review'] = True
    elif change == 'fake-context': r['reviewer_context'] = 'invented-second-agent'
    elif change == 'missing-recheck': r['items'][0].pop('answer_recheck')
    elif change == 'missing-reason': r.pop('review_reason')
    else: r['review_mode'] = 'skip'
    assert review_errors(exam, r)


@pytest.mark.parametrize('subject', ['數學A', '數學B'])
def test_fallback_cannot_pass_easy_routine_paper_by_relabeling(subject):
    exam = {'metadata': {'subject': subject}, 'questions': [{'id': str(i), 'score': 5} for i in range(1, 21)]}
    r = review([row(i) for i in range(1, 21)])
    for item, band in zip(r['items'], ['easy'] + ['medium']*4 + ['hard']*8 + ['very_hard']*7):
        item['difficulty_band'] = band
    assert not review_errors(exam, r)
    for item in r['items']:
        item.update(routine_only=True, difficulty_band='very_hard', expected_minutes=2)
    errors = review_errors(exam, r)
    assert any('routine substitution' in e for e in errors)
    assert any('40 minutes' in e for e in errors)
    assert any('50-point' in e for e in errors)
    assert any('routine-only routes' in e for e in errors)


def self_review_fixture(saved):
    state, save = saved
    exam = json.loads(Path('exam.json').read_text())
    r = json.loads(Path('difficulty.json').read_text())
    r.update(review_mode='single-context', reviewer_context=r['author_context'], independent_review=False,
             review_reason='No second reviewer tool available')
    for item in r['items']:
        item['answer_recheck'] = 'Synthetic fresh solving pass reconciled with saved fixture answer'
    r['blind_packet'] = save('review-packet.json', packet(exam, 'single-context'))
    state['checks']['difficulty'] = save('difficulty.json', r)
    state['review_mode'] = 'single-context'
    return state, save


def test_complete_fallback_is_disclosed_and_explicit_independence_still_required(saved_run):
    state, save = self_review_fixture(saved_run)
    result = evaluate(state, save)
    assert result['status'] == 'evidence-complete'
    assert result['difficulty_review_mode'] == 'single-context'
    assert 'not independent' in result['delivery_note'] and result['formal_acceptance'] is False
    state['require_independent_review'] = True
    result = evaluate(state, save)
    assert result['status'] == 'pending'
    assert any('explicitly required' in e for e in result['errors'])


def test_fallback_does_not_accept_answer_bearing_packet_or_missing_visuals(saved_run):
    state, save = self_review_fixture(saved_run)
    r = json.loads(Path('difficulty.json').read_text())
    r['blind_packet'] = save('review-packet.json', packet(json.loads(Path('exam.json').read_text())))
    state['checks']['difficulty'] = save('difficulty.json', r)
    state['pdfs']['question'].pop('item_review')
    result = evaluate(state, save)
    assert result['status'] == 'pending'
    assert any('packet changed' in e for e in result['errors'])
    assert any('item_review' in e for e in result['errors'])


@pytest.mark.parametrize('saved_requirement', [False, True])
def test_explicit_independence_fails_preflight_before_fetch_and_survives_resume(tmp_path, monkeypatch, saved_requirement):
    def unexpected_fetch(*args, **kwargs):
        pytest.fail('Should resolve explicit reviewer requirement before fetching assets')
    monkeypatch.setattr(preflight, 'acquire', unexpected_fetch)
    if saved_requirement:
        (tmp_path/'run-state.json').write_text(json.dumps({'paper_id':'p','require_independent_review':True}), encoding='utf-8')
    result = preflight.prepare('數學A', tmp_path, 'p', tmp_path/'unused-font.ttf',
                               require_independent_review=not saved_requirement)
    assert result['status'] == 'pending'
    assert result['require_independent_review'] is True
    assert 'actual separate reviewer' in result['errors'][0]
