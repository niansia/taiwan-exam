"""Every subject's difficulty gate passes within a range, and a user's requested difficulty
(metadata.user_difficulty_request) replaces the 學測 defaults (maintainer decision 2026-09-25)."""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests')]
from hosted_blind_review import review_errors
from test_hosted_review_modes import review, row


def choice_paper(subject, p, n=20, request=None):
    exam = {'metadata': {'subject': subject, **({'user_difficulty_request': request} if request else {})},
            'questions': [{'id': str(i), 'score': 2, 'options': [{'label': 'A', 'text': 'x'}]} for i in range(n)]}
    r = review([row(i) for i in range(n)])
    for item, value in zip(r['items'], p if isinstance(p, list) else [p] * n):
        item.update(estimated_p=value, difficulty_band='medium')
    return exam, r


def mean_errors(errors):
    return [e for e in errors if '答對率' in e or '難 (' in e or 'user_difficulty_request' in e]


@pytest.mark.parametrize('subject,passing,failing', [('國綜', 0.64, 0.66), ('社會', 0.67, 0.69), ('自然', 0.67, 0.69)])
def test_mean_p_ceilings_accept_a_range(subject, passing, failing):
    assert not mean_errors(review_errors(*choice_paper(subject, passing)))
    assert mean_errors(review_errors(*choice_paper(subject, failing)))


def test_a_requested_mean_and_hard_share_replace_the_ceiling():
    request = {'request': '國綜平均答對率 0.5，難題 20%', 'mean_p': 0.5, 'hard_percent': 20}
    hard_mix = [0.2] * 4 + [0.575] * 16                        # mean 0.50, 20% below 0.30
    assert not mean_errors(review_errors(*choice_paper('國綜', hard_mix, request=request)))
    assert any('0.5 the user asked for' in e for e in review_errors(*choice_paper('國綜', 0.6, request=request)))
    assert any('asked for 20%' in e for e in review_errors(*choice_paper('國綜', [0.5] * 20, request=request)))
    easier = {'request': '社會簡單一點，平均答對率 0.75', 'mean_p': 0.75}
    assert not mean_errors(review_errors(*choice_paper('社會', 0.74, request=easier)))


def test_a_request_must_quote_the_user():
    errors = review_errors(*choice_paper('自然', 0.6, request={'request': '', 'hard_percent': 30}))
    assert any("user's own words" in e for e in errors)
    errors = review_errors(*choice_paper('自然', 0.6, request={'request': '自然難題 130%', 'hard_percent': 130}))
    assert any('hard_percent must be a number' in e for e in errors)


def math_paper(very_hard, hard, request=None):
    exam = {'metadata': {'subject': '數學A', **({'user_difficulty_request': request} if request else {})},
            'questions': [{'id': str(i), 'score': 5} for i in range(20)]}
    r = review([row(i) for i in range(20)])
    medium = 20 - very_hard - hard
    bands = ['medium'] * medium + ['hard'] * hard + ['very_hard'] * very_hard
    p = {'medium': .6, 'hard': .4, 'very_hard': .2}
    for item, band in zip(r['items'], bands):
        item.update(difficulty_band=band, estimated_p=p[band])
    return exam, r


def floor_errors(errors):
    return [e for e in errors if 'score' in e and ('hard' in e or 'easy' in e)]


def test_math_requested_hard_share_replaces_the_30_point_floor():
    # 20 x 5 points: 8 very_hard = 40 points, 8 hard = 40 points.
    request = {'request': '數A 難題 40%', 'hard_percent': 40}
    assert not floor_errors(review_errors(*math_paper(8, 8, request)))
    assert any('40 points the user asked for' in e for e in review_errors(*math_paper(6, 10, request)))
    easier = {'request': '數A 簡單一點：難題 15%、中偏難加難 50%', 'hard_percent': 15, 'challenge_percent': 50}
    assert not floor_errors(review_errors(*math_paper(3, 7, easier)))
    assert floor_errors(review_errors(*math_paper(3, 7)))  # without a request the 學測 floors apply
