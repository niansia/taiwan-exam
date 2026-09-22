#!/usr/bin/env python3
"""One fixed page-density rule shared by plan, inspector, review preparation and the final checker.

Until 2026.09.22.8 three thresholds disagreed: `plan` warned above 0.28 and
ignored the last page, the inspector flagged above 0.32 on every page, and the
final checker recomputed a calibration-derived limit (largest embedded official
void + 0.10, about 0.23 for 國綜) that this renderer could not reach. A run could
iterate `plan` to green, watch `build` flag both booklets, and fail `finalize` a
third way. A hosted 國綜 paper was abandoned on exactly that.

The limits below are fixed and measured on the ROC 111–115 question booklets
(bottom void = blank share of the printable body, measured on pixels):

* body pages between the first and the last: 國綜 ≤ 0.13, 社會 ≤ 0.26, 自然 ≤ 0.22,
  數學A ≤ 0.26, 英文 ≤ 0.40 (section breaks) → limit 0.32, 英文 0.42;
* the last body page: 0.0–0.69 across subjects (自然 112 0.688, 社會 112 0.567,
  國綜 111 0.50) → limit 0.60;
* the cover and the mathematics formula page are fixed template layers and are
  never measured.

The embedded official page metrics stay in the review evidence as reference
material; they no longer set the threshold, and no disposition can waive a page
over the limit. The renderer's balanced pagination keeps ordinary papers well
inside these numbers, so an over-limit page is a layout defect to fix, not a
value to argue about.
"""
from __future__ import annotations

MAX_BODY_VOID = {'default': 0.32, '英文': 0.42}
MAX_LAST_PAGE_VOID = 0.60
MATH_SUBJECTS = {'數學A', '數學B'}
COVER_MARKERS = ('作答注意事項', '請於考試開始鈴響起')
FORMULA_MARKERS = ('參考公式', '可能用到的數值')


def body_void_limit(subject) -> float:
    return MAX_BODY_VOID.get(subject, MAX_BODY_VOID['default'])


def page_role(page_text: str, number: int, count: int, subject=None, *, solutions=False) -> str:
    """cover / formula / body / solutions for one page of a composed booklet."""
    text = page_text or ''
    if number == 1 and any(marker in text for marker in COVER_MARKERS):
        return 'cover'
    if (subject in MATH_SUBJECTS or subject is None) and number == count and any(m in text for m in FORMULA_MARKERS):
        return 'formula'
    return 'solutions' if solutions else 'body'


def last_body_page(number: int, count: int, roles: dict) -> bool:
    """True when no later page of the booklet is a body/solutions page."""
    return all(roles.get(n) in {'cover', 'formula'} for n in range(number + 1, count + 1))


def page_void_limit(subject, role: str, is_last_body_page: bool):
    """The fixed limit for this page, or None when the page is a fixed template layer."""
    if role in {'cover', 'formula'}:
        return None
    if is_last_body_page:
        return MAX_LAST_PAGE_VOID
    return body_void_limit(subject)


def booklet_limits(pages, subject=None, *, solutions=False):
    """{page number: (role, limit)} for a sequence of (number, text) pairs."""
    count = len(pages)
    roles = {n: page_role(text, n, count, subject, solutions=solutions) for n, text in pages}
    return {n: (roles[n], page_void_limit(subject, roles[n], last_body_page(n, count, roles))) for n, _ in pages}


def verdict(void: float, limit) -> dict:
    return {'bottom_void_ratio': round(float(void), 3), 'bottom_void_limit': limit,
            'over_limit': limit is not None and float(void) > limit}
