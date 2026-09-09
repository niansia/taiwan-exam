"""Evidence contracts for observed paper/layout profiles (not self-certification).

No PDF wording is passed to an item writer. Reviews retain page references and
aggregate observations; source hashes and profile hashes invalidate stale claims.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ITEM_TYPES = {'single_choice', 'multiple_choice', 'fill_in', 'constructed_response', 'guided_writing'}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def profile_digest(profile):
    return digest({k: v for k, v in profile.items() if k not in {'evidence', 'structure_status', 'fidelity_status'}})


def source_errors(profile, root=None):
    errors = []
    sources = profile.get('source_files') or []
    if not sources:
        errors.append('no reference source files')
    for source in sources:
        sha = source.get('sha256', '')
        if len(sha) != 64 or set(sha) <= {'0'}:
            errors.append('reference hash missing or withheld; local re-verification required')
        if root is not None:
            path = Path(root) / source.get('relative_path', '')
            if not path.is_file():
                errors.append(f'reference unavailable: {source.get("relative_path")}')
            elif hashlib.sha256(path.read_bytes()).hexdigest() != sha:
                errors.append(f'reference hash mismatch: {source.get("relative_path")}')
    return errors


def review_errors(profile, review_name, root=None):
    errors = source_errors(profile, root)
    review = (profile.get('evidence') or {}).get(review_name) or {}
    if review.get('profile_sha256') != profile_digest(profile):
        errors.append(f'{review_name}: absent or stale profile digest')
    if not review.get('reviewer') or not review.get('reviewed_at'):
        errors.append(f'{review_name}: reviewer and review date required')
    if review.get('method') != 'page-by-page':
        errors.append(f'{review_name}: actual page-by-page review required')
    sources = {s.get('sha256'): s for s in profile.get('source_files', [])}
    pages = review.get('pages') or []
    if not pages:
        errors.append(f'{review_name}: missing page observations')
    for p in pages:
        s = sources.get(p.get('source_sha256'))
        number = p.get('page')
        if not s or not isinstance(number, int) or not 1 <= number <= (s.get('page_count') or 0) or not p.get('observations'):
            errors.append(f'{review_name}: invalid page reference or empty observations')
    if review.get('unresolved') != []:
        errors.append(f'{review_name}: unresolved findings must be explicitly empty')
    return errors


def paper_errors(profile, root=None):
    errors = review_errors(profile, 'structure_review', root)
    if profile.get('structure_status') != 'verified':
        errors.append('structure is not verified')
    sections = profile.get('sections') or []
    slots = ((profile.get('evidence') or {}).get('structure_review') or {}).get('slots') or []
    if len(slots) != profile.get('scored_item_count'):
        errors.append('scored-slot inventory missing or count mismatch')
    ids = [s.get('id') for s in slots]
    if any(not x for x in ids) or len(set(ids)) != len(ids):
        errors.append('scored-slot ids missing or duplicated')
    section_ids = {s.get('id') for s in sections}
    refs = {(p.get('source_sha256'), p.get('page')) for p in
            ((profile.get('evidence') or {}).get('structure_review') or {}).get('pages', [])}
    for slot in slots:
        if slot.get('type') not in ITEM_TYPES or slot.get('section_id') not in section_ids:
            errors.append('slot needs an actual response type and known section; mixed_group is not a response type')
        if not isinstance(slot.get('score'), (int, float)) or slot['score'] <= 0:
            errors.append('slot score missing or invalid')
        if (slot.get('source_sha256'), slot.get('page')) not in refs:
            errors.append('slot lacks a reviewed source-page reference')
        if slot.get('type') in {'single_choice', 'multiple_choice'} and (not isinstance(slot.get('option_count'), int) or slot['option_count'] < 2):
            errors.append('choice slot option count missing')
    for section in sections:
        selected = [s for s in slots if s.get('section_id') == section.get('id')]
        if len(selected) != section.get('scored_item_count'):
            errors.append(f'{section.get("id")}: scored count mismatch')
        if dict(Counter(s.get('type') for s in selected)) != section.get('question_type_mix'):
            errors.append(f'{section.get("id")}: response-type inventory mismatch or unresolved mix')
        if not section.get('instructions_pattern') or not section.get('score_rule'):
            errors.append(f'{section.get("id")}: exact instructions/scoring rule not reviewed')
        if abs(sum(s.get('score', 0) or 0 for s in selected) - (section.get('subtotal_score') or 0)) > 1e-6:
            errors.append(f'{section.get("id")}: slot scores do not reconcile')
    if not sections or sum(s.get('subtotal_score', 0) or 0 for s in sections) != profile.get('total_score'):
        errors.append('section scores do not reconcile with paper')
    numbered = {s.get('number') for s in slots if s.get('number') is not None}
    if len(numbered) != profile.get('numbered_question_count'):
        errors.append('numbered count does not reconcile with scored-slot inventory')
    if not profile.get('duration_minutes'):
        errors.append('duration not verified')
    return errors


def layout_errors(profile, root=None, paper=None):
    errors = review_errors(profile, 'layout_review', root)
    if profile.get('fidelity_status') != 'verified' or (profile.get('instructions') or {}).get('transcription_status') != 'verified':
        errors.append('layout/instruction transcription not verified')
    for field in ('page_geometry', 'typography', 'cover', 'running_elements', 'pagination', 'question_styles'):
        if not profile.get(field):
            errors.append(f'layout missing {field}')
    if not (profile.get('instructions') or {}).get('blocks'):
        errors.append('layout lacks full instruction blocks')
    pages = ((profile.get('evidence') or {}).get('layout_review') or {}).get('pages', [])
    for source in profile.get('source_files', []):
        covered = {p.get('page') for p in pages if p.get('source_sha256') == source.get('sha256')}
        if not source.get('page_count') or covered != set(range(1, source['page_count'] + 1)):
            errors.append('layout review must cover every reference page, including cover/final page')
    if paper:
        for key in ('exam', 'subject', 'curriculum', 'section', 'regime'):
            if profile.get(key) != paper.get(key):
                errors.append(f'layout/paper {key} mismatch')
    return errors
