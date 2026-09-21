#!/usr/bin/env python3
"""Which saved items need their own readable crop, from the authored record alone.

A figure, formula image, sub/superscript, answer blank, cloze gap, response
table, fill rail or a long shared stimulus can print wrongly in ways a page
image at 1.5 px/pt may hide, so those items get 2 px/pt crops at proof and
final review. A plain paragraph item prints through the same text path as
every earlier proof; its final review happens on the page image that the
reviewer opens anyway, and the checker verifies that the page passed. The
decision is recomputed from the exam wherever it is used, so a review report
cannot relabel an item.
"""
from __future__ import annotations

import re

RICH_TAG = re.compile(r'</?(?:sup|sub|i|em|b|strong)>|<br>')
SCRIPT_RUN = re.compile('[₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ]')
ASSET_TOKEN = re.compile(r'\{\{asset:[^{}]+\}\}')
GAP = re.compile(r'\[\[\d+\]\]')
LONG_STIMULUS_CHARACTERS = 260  # the renderer's paragraph-split threshold


def _text(value):
    raw = value['rich'] if isinstance(value, dict) and set(value) == {'rich'} else value
    return raw if isinstance(raw, str) else None


def printed_values(question, answer):
    """(where, text) for every field the body projection prints."""
    for key in ('prompt', 'number_display', 'answer_label', 'group_stimulus'):
        yield key, question.get(key)
    for option in question.get('options') or []:
        if isinstance(option, dict):
            yield f'option {option.get("label")}', option.get('text')
    for key in ('continuation_pages', 'group_stimulus_page_splits'):
        for page, value in sorted((question.get(key) or {}).items()):
            yield f'{key} {page}', value
    table = question.get('response_format_table')
    if isinstance(table, dict):
        yield 'response table', table.get('caption')
        for row in table.get('rows') or []:
            if isinstance(row, dict):
                yield 'response row', row.get('instruction')
    final = (answer or {}).get('final_answer')
    for value in final if isinstance(final, list) else [final]:
        yield 'final_answer', value
    for step in (answer or {}).get('reasoning') or []:
        yield 'reasoning', step
    for block in (answer or {}).get('explanation_blocks') or []:
        if isinstance(block, dict):
            yield 'explanation', block.get('content')


def crop_reasons(question, answer):
    """Why this item needs its own crop; an empty list means text-only."""
    answer = answer or {}
    reasons = []
    for owner, record in (('question', question), ('answer', answer)):
        if isinstance(record.get('visual_asset'), dict):
            reasons.append(owner + ' figure')
        if record.get('inline_assets'):
            reasons.append(owner + ' inline formula image')
    if question.get('response_format_table'):
        reasons.append('response table')
    if question.get('answer_format') or question.get('continuation_pages') or question.get('group_stimulus_page_splits'):
        reasons.append('fill rail or explicit page continuation')
    stimulus = _text(question.get('group_stimulus'))
    if stimulus and len(stimulus) >= LONG_STIMULUS_CHARACTERS:
        reasons.append('long shared stimulus that may split across pages')
    for where, value in printed_values(question, answer):
        rich = isinstance(value, dict) and set(value) == {'rich'}
        raw = _text(value)
        if raw is None:
            continue
        if rich or RICH_TAG.search(raw) or SCRIPT_RUN.search(raw) or ASSET_TOKEN.search(raw):
            reasons.append(f'{where}: sub/superscript, markup or formula image')
        if '{{answer}}' in raw or '______' in raw or GAP.search(raw):
            reasons.append(f'{where}: answer blank or gap')
    return list(dict.fromkeys(reasons))


def needs_crop(question, answer):
    return bool(crop_reasons(question, answer))


def crop_required_ids(exam):
    """{question id: reasons} for every item whose crops must be opened."""
    answers = {a.get('question_id'): a for a in exam.get('answers') or [] if isinstance(a, dict)}
    found = {}
    for question in exam.get('questions') or []:
        if isinstance(question, dict):
            reasons = crop_reasons(question, answers.get(question.get('id')))
            if reasons:
                found[question.get('id')] = reasons
    return found


def part_reviewed_on_page(part, required):
    """A crop is read on its page only when nothing it prints needs a crop."""
    members = [part.get('id'), *(part.get('covers') or [])]
    if any(member in required for member in members):
        return False
    return all(component.get('role') == 'flow-content' for component in part.get('components') or [])
