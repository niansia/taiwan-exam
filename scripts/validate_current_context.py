#!/usr/bin/env python3
"""Recent-context floors for 自然, 英文, 國綜 and 國寫 full papers.

Math A/B use validate_math_context.py and 社會 uses validate_social_item_design.py.
This gate checks the per-item source and date records that make a "recent"
claim traceable, and the subject floors in references/current-form-topicality.md,
which were set from the maintainer's reading of ROC 111-115 official papers
(exam_packs/學測/shared-data/current-form-topicality-envelope.json). Dates and
record completeness are mechanical; whether the source relation really changes
the reasoning still needs the editorial review named in that reference.

    python scripts/validate_current_context.py generated-exam.json [--report out.json]
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlparse

SUBJECTS = {'自然', '英文', '國綜', '國寫'}
RECENT_CLASSES = {'current_event', 'recent_context'}
TREND_CLASS = 'current_trend'
RECENT_DAYS = 365
TREND_DAYS = 730
FRESH_DAYS = 180
FULL_PAPER_ITEMS = {'自然': 50, '英文': 40, '國綜': 30, '國寫': 2}
HAZARD_TAGS = {'typhoon', 'earthquake', 'weather_hazard'}
KNOWN_TAGS = HAZARD_TAGS | {'climate_energy', 'epidemic', 'space', 'taiwan', 'technology', 'society_trend',
                            'health', 'conflict', 'population', 'environment'}
# Floors are editorial targets above the weakest official year; the reference
# states which official years would fail them.
FLOORS = {
    '自然': {'recent_sources': 5, 'recent_items': 8, 'fresh_sources': 2, 'both_parts': True,
           'tags': {'taiwan_hazard': 1, 'climate_energy': 4, 'taiwan': 3}},
    '英文': {'recent_sources': 2, 'recent_items': 6, 'composition_trend': True},
    '國綜': {'recent_sources': 2, 'recent_items': 4, 'tags': {'taiwan': 2}},
    '國寫': {'trend_tasks': 1},
}
SOURCE_FIELDS = ('publisher', 'title', 'rights_status', 'source_family')
# Source diversity (maintainer decision 2026-09-24): two hosted 116 自然 papers built three Nobel
# groups each (the guidance once said 「plan the autumn Nobel prizes」), and one used NASA for
# three of six recent sources with the same eclipse and the same Swift notice in two groups each.
# Any fresh, checkable source serves: a journal paper, a conference result, a Nature/Science news
# item, an agency data release, a monitoring series (ENSO, CO2), a space mission, a hazard report,
# local Taiwan data. Official papers used 0-2 Nobel prizes a year.
NOBEL = re.compile(r'nobel|諾貝爾', re.I)
NOBEL_MAX = 1
NATURAL_FAMILIES_MIN = 3
PUBLISHER_MAX = 2


def parse_date(value):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def is_full_paper(exam):
    metadata = exam.get('metadata') or {}
    subject = metadata.get('paper_subject') or metadata.get('subject')
    if metadata.get('generation_mode') == 'full-paper':
        return True
    return len(exam.get('questions') or []) >= FULL_PAPER_ITEMS.get(subject, 10 ** 6)


def is_composition(question, sections):
    title = sections.get(question.get('section_id'), '')
    labels = ' '.join(str(question.get(k) or '') for k in ('number_display', 'answer_label', 'id', 'type'))
    return '作文' in title or '作文' in labels or question.get('type') == 'guided_writing'


def item_tags(question):
    spec = question.get('item_spec') or {}
    tags = spec.get('context_tags') or []
    return {str(tag) for tag in tags} if isinstance(tags, list) else set()


def collect(exam):
    """Per-item records with their resolved source and freshness, plus errors."""
    metadata = exam.get('metadata') or {}
    plan = metadata.get('current_context_plan') or {}
    lock = parse_date(plan.get('editorial_lock_date'))
    errors, warnings = [], []
    records = plan.get('sources') or []
    sources = {}
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict) or not record.get('source_id'):
            errors.append('current_context: every source record needs a source_id')
            continue
        if record['source_id'] in sources:
            errors.append(f'current_context: duplicate source id {record["source_id"]}')
        sources[record['source_id']] = record
    rows = []
    for question in exam.get('questions') or []:
        spec = question.get('item_spec') or {}
        context = spec.get('current_context')
        for tag in item_tags(question) - KNOWN_TAGS:
            warnings.append(f'{question.get("id")}: unknown context tag {tag}')
        if not context:
            continue
        qid = question.get('id')
        if not isinstance(context, dict):
            errors.append(f'{qid}: current_context must be an object')
            continue
        freshness = context.get('freshness_class')
        if freshness not in RECENT_CLASSES | {TREND_CLASS}:
            errors.append(f'{qid}: freshness_class must be current_event, recent_context or current_trend')
        for field in ('relation', 'removal_counterfactual'):
            if not str(context.get(field) or '').strip():
                errors.append(f'{qid}: current_context.{field} is required (what the source supplies and what breaks without it)')
        if context.get('outside_knowledge_required') is not False:
            errors.append(f'{qid}: current_context.outside_knowledge_required must be false; print every needed fact')
        record = sources.get(context.get('source_id'))
        if record is None:
            errors.append(f'{qid}: current_context.source_id has no record in metadata.current_context_plan.sources')
            rows.append({'id': qid, 'question': question, 'record': None, 'freshness': freshness, 'qualifies': False})
            continue
        qualifies = lock is not None
        if lock is None:
            errors.append(f'{qid}: current_context_plan.editorial_lock_date is required for recent claims')
        event = parse_date(record.get('event_date'))
        published = parse_date(record.get('published_at'))
        accessed = parse_date(record.get('accessed_at'))
        prefix = f'{qid} source {record["source_id"]}'
        if not (event and published and accessed):
            errors.append(f'{prefix}: event_date, published_at and accessed_at are required (YYYY-MM-DD)')
            qualifies = False
        elif lock:
            window = TREND_DAYS if freshness == TREND_CLASS else RECENT_DAYS
            if not 0 <= (lock - event).days <= window or not 0 <= (lock - published).days <= window:
                errors.append(f'{prefix}: event AND publication must fall within {window} days before the editorial lock')
                qualifies = False
            if not published <= accessed <= lock:
                errors.append(f'{prefix}: access date must lie between publication and the lock')
                qualifies = False
        url = urlparse(str(record.get('canonical_url') or ''))
        if url.scheme != 'https' or not url.netloc:
            errors.append(f'{prefix}: canonical_url must be an https address (kept internal, never printed)')
            qualifies = False
        if record.get('fact_check_status') != 'verified' or not record.get('verified_facts'):
            errors.append(f'{prefix}: fact_check_status must be verified with a verified_facts snapshot')
            qualifies = False
        missing = [field for field in SOURCE_FIELDS if not record.get(field)]
        if missing:
            errors.append(f'{prefix}: missing ' + ', '.join(missing))
            qualifies = False
        rows.append({'id': qid, 'question': question, 'record': record, 'freshness': freshness,
                     'qualifies': qualifies, 'event': event})
    if lock and lock > (datetime.now(timezone.utc) + timedelta(hours=8)).date():
        errors.append('current_context: editorial lock date cannot be in the future')
    return {'lock': lock, 'sources': sources, 'rows': rows, 'errors': errors, 'warnings': warnings}


def progress(exam):
    """Counts against the subject floor, for the authoring loop; no pass/fail."""
    metadata = exam.get('metadata') or {}
    subject = metadata.get('paper_subject') or metadata.get('subject')
    if subject not in SUBJECTS:
        return None
    found = collect(exam)
    recent = [r for r in found['rows'] if r['qualifies'] and r['freshness'] in RECENT_CLASSES]
    trend = [r for r in found['rows'] if r['qualifies'] and r['freshness'] == TREND_CLASS]
    tags = [tag for q in exam.get('questions') or [] for tag in item_tags(q)]
    floor = FLOORS[subject]
    counts = {'recent_sources': len({r['record']['source_id'] for r in recent}), 'recent_items': len(recent),
              'trend_tasks': len(trend), 'lock_date': str(found['lock']) if found['lock'] else None}
    if found['lock']:
        counts['fresh_sources'] = len({r['record']['source_id'] for r in recent
                                       if (found['lock'] - r['event']).days <= FRESH_DAYS})
    if 'tags' in floor:
        counts['tags'] = {name: sum(1 for t in tags if t == name) for name in floor['tags'] if name != 'taiwan_hazard'}
        if 'taiwan_hazard' in floor['tags']:
            counts['tags']['taiwan_hazard'] = sum(1 for q in exam.get('questions') or []
                                                  if item_tags(q) & HAZARD_TAGS and 'taiwan' in item_tags(q))
    return {'subject': subject, 'floor': floor, 'counts': counts}


def diversity_errors(subject, recent):
    """Nobel cap, publisher cap, source-family spread and one material per recent event."""
    records = {r['record']['source_id']: r['record'] for r in recent}
    describe = lambda rec: ' '.join(str(rec.get(k) or '') for k in ('publisher', 'title', 'source_family'))
    errors = []
    nobel = sorted(sid for sid, rec in records.items() if NOBEL.search(describe(rec)))
    if len(nobel) > NOBEL_MAX:
        errors.append(f'current_context: {len(nobel)} recent sources are Nobel prizes ({", ".join(nobel)}); use at most '
                      f'{NOBEL_MAX} and draw the rest from papers, conferences, data releases, monitoring series, missions '
                      'or hazard reports')
    if subject != '自然':
        return errors
    publishers = defaultdict(set)
    for sid, rec in records.items():
        publishers[re.sub(r'\W+', '', str(rec.get('publisher') or '')).casefold()].add(sid)
    for name, sids in publishers.items():
        if name and len(sids) > PUBLISHER_MAX:
            errors.append(f'current_context: {len(sids)} recent sources come from one publisher ({", ".join(sorted(sids))}); '
                          f'at most {PUBLISHER_MAX}, so the paper does not read as one agency press page')
    families = {str(rec.get('source_family') or '').strip().casefold() for rec in records.values()} - {''}
    if len(records) >= NATURAL_FAMILIES_MIN and len(families) < NATURAL_FAMILIES_MIN:
        errors.append(f'current_context: recent sources span {len(families)} source families ({", ".join(sorted(families))}); '
                      f'自然 needs at least {NATURAL_FAMILIES_MIN} (e.g. journal paper, conference, agency data, monitoring '
                      'series, space mission, hazard report, Taiwan local data)')
    materials = defaultdict(set)
    events = defaultdict(set)
    for row in recent:
        question = row['question']
        material = str(question.get('group_stimulus') or '').strip()[:80] or f'Q{question.get("number")}'
        rec = row['record']
        materials[rec['source_id']].add(material)
        events[(re.sub(r'\W+', '', str(rec.get('publisher') or '')).casefold(), str(rec.get('event_date')))].add(material)
    for sid, used in materials.items():
        if len(used) > 1:
            errors.append(f'current_context: source {sid} is the recent material of {len(used)} different groups or items; '
                          'one event feeds one group, so the paper does not repeat the same news')
    for (publisher, day), used in events.items():
        if publisher and len(used) > 1 and not any(len(materials[s]) > 1 for s in materials):
            errors.append(f'current_context: the same {publisher} event of {day} is the material of {len(used)} different '
                          'groups or items; use it once')
    return errors


def validate(exam):
    """Errors only, in the flat message style the hosted checker and release gate print."""
    metadata = exam.get('metadata') or {}
    subject = metadata.get('paper_subject') or metadata.get('subject')
    if subject not in SUBJECTS:
        return []
    found = collect(exam)
    errors = list(found['errors'])
    if not is_full_paper(exam):
        return errors
    floor = FLOORS[subject]
    lock = found['lock']
    recent = [r for r in found['rows'] if r['qualifies'] and r['freshness'] in RECENT_CLASSES]
    recent_sources = {r['record']['source_id'] for r in recent}
    questions = exam.get('questions') or []
    sections = {s.get('id'): str(s.get('title') or '') for s in exam.get('sections') or [] if isinstance(s, dict)}
    if floor.get('recent_sources') and len(recent_sources) < floor['recent_sources']:
        errors.append(f'current_context: {subject} full paper needs at least {floor["recent_sources"]} verified '
                      f'recent source(s) (event within {RECENT_DAYS} days before the lock); found {len(recent_sources)}')
    if floor.get('recent_items') and len(recent) < floor['recent_items']:
        errors.append(f'current_context: {subject} full paper needs at least {floor["recent_items"]} scored items '
                      f'whose reasoning depends on a verified recent source; found {len(recent)}')
    if floor.get('fresh_sources') and lock:
        fresh = {r['record']['source_id'] for r in recent if (lock - r['event']).days <= FRESH_DAYS}
        if len(fresh) < floor['fresh_sources']:
            errors.append(f'current_context: {subject} needs at least {floor["fresh_sources"]} recent source from the '
                          f'last {FRESH_DAYS} days before the lock (any fresh checkable source: a paper, a conference, a '
                          'data release, a mission, a hazard report); found ' + str(len(fresh)))
    errors.extend(diversity_errors(subject, recent))
    if floor.get('both_parts') and recent:
        numbers = [r['question'].get('number') for r in recent if isinstance(r['question'].get('number'), int)]
        if not any(n <= 36 for n in numbers) or not any(n >= 37 for n in numbers):
            errors.append('current_context: 自然 recent items must appear in both 第壹部分 (1-36) and 第貳部分 (37+)')
    for name, minimum in (floor.get('tags') or {}).items():
        if name == 'taiwan_hazard':
            count = sum(1 for q in questions if item_tags(q) & HAZARD_TAGS and 'taiwan' in item_tags(q))
            what = 'item(s) whose context is a Taiwan hazard (颱風／地震／豪雨／寒害 tagged taiwan plus the hazard)'
        else:
            count = sum(1 for q in questions if name in item_tags(q))
            what = f'item(s) tagged {name}'
        if count < minimum:
            errors.append(f'current_context: {subject} full paper needs at least {minimum} {what}; found {count}')
    if floor.get('composition_trend'):
        compositions = [q for q in questions if is_composition(q, sections)]
        tied = [r for r in found['rows'] if r['qualifies'] and r['freshness'] == TREND_CLASS
                and is_composition(r['question'], sections)]
        if compositions and not tied:
            errors.append('current_context: the English composition prompt must declare a verified current_trend '
                          'source (a real social trend within 730 days before the lock), as four of five official years do')
    if floor.get('trend_tasks'):
        tied = [r for r in found['rows'] if r['qualifies'] and r['freshness'] == TREND_CLASS]
        if len(tied) < floor['trend_tasks']:
            errors.append(f'current_context: 國寫 needs at least {floor["trend_tasks"]} task tied to a verified '
                          'current_trend source; older literary material stays eligible for the other task')
    families = {r['record'].get('source_family') for r in found['rows'] if r['qualifies']}
    if len({r['record']['source_id'] for r in found['rows'] if r['qualifies']}) >= 2 and len(families) < 2:
        errors.append('current_context: use at least two unrelated source families across the recent sources')
    ecology = metadata.get('natural_source_ecology_plan')
    if subject == '自然' and isinstance(ecology, dict):
        verified_numbers = {r['question'].get('number') for r in recent}
        listed = ecology.get('recent_item_numbers') or []
        unverified = [n for n in listed if n not in verified_numbers]
        if unverified:
            errors.append('current_context: natural_source_ecology_plan.recent_item_numbers lists items without a '
                          'verified current_context record: ' + ', '.join(str(n) for n in unverified))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('exam', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam.read_text(encoding='utf-8-sig'))
    errors = validate(exam)
    report = {'status': 'fail' if errors else 'pass', 'errors': errors,
              'warnings': collect(exam)['warnings'], 'progress': progress(exam),
              'scope': 'Dates, records and floors only; source truth and reasoning dependence need editorial review'}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + '\n', encoding='utf-8')
    print(rendered)
    return 2 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
