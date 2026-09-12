#!/usr/bin/env python3
"""Math current-event planning and student-facing source-note checks.

Dates and traceability are mechanically checked; real source verification and
the necessity of a modelling decision still require editorial review.
"""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlparse

SOURCE_NOTE = re.compile(r'資料來源[：:]|參考來源[：:]|資料出處[：:]|參考文獻[：:]|出處[：:]|改寫自|改編自|節錄自|摘自|https?://|www\.|doi[：:]', re.I)


def source_note_samples(text):
    return sorted(set(SOURCE_NOTE.findall(re.sub(r'\s+', '', text))))


def printable_text(exam):
    """Inspect visible fields only. Internal URLs/provenance remain intact."""
    values = list(exam.get('instructions', []))
    for section in exam.get('sections', []):
        values.extend(section.get('instructions', []))
    for q in exam.get('questions', []):
        values.extend(q.get(k) or '' for k in ('prompt','group_stimulus'))
        values.extend(o.get('text','') for o in q.get('options', []))
        values.append((q.get('visual_asset') or {}).get('caption') or '')
    for answer in exam.get('answers', []):
        values.extend(answer.get('reasoning') or [])
        values.extend(b.get('content','') for b in answer.get('explanation_blocks', []))
        values.append((answer.get('visual_asset') or {}).get('caption') or '')
    return '\n'.join(str(value) for value in values)


def validate(exam):
    metadata = exam.get('metadata') or {}
    if (metadata.get('paper_subject') or metadata.get('subject')) not in {'數學A','數學B'}:
        return []
    errors = []
    if source_note_samples(printable_text(exam)):
        errors.append('math: remove printed source notes/URLs; preserve internal provenance and rewrite with independently created material')
    questions = exam.get('questions', [])
    linked = [q for q in questions if (q.get('item_spec') or {}).get('current_event')]
    if len(questions) == 20 and not 2 <= len(linked) <= 4:
        errors.append('math: default full paper requires 2-4 current-event items, not a news-themed whole paper')
    if not linked:
        return errors
    plan = metadata.get('current_event_plan') or {}
    try:
        lock = date.fromisoformat(plan.get('editorial_lock_at',''))
    except (TypeError, ValueError):
        return errors + ['math: missing editorial lock date for current events']
    if lock > (datetime.now(timezone.utc) + timedelta(hours=8)).date():
        errors.append('math: editorial lock cannot be in the future')
    records = plan.get('sources', [])
    sources = {s.get('source_id'):s for s in records}
    if len(sources) != len(records):
        errors.append('math: duplicate current-event source IDs')
    families = set()
    for q in linked:
        spec = q['item_spec']; context = spec['current_event']; prefix = f'math/{q["id"]}'
        record = sources.get(context.get('source_id'))
        if record is None:
            errors.append(f'{prefix}: missing internal source record'); continue
        try:
            event = date.fromisoformat(record.get('event_date',''))
            published = date.fromisoformat(record.get('published_at',''))
            accessed = date.fromisoformat(record.get('accessed_at',''))
            if not 0 <= (lock-event).days <= 365 or not 0 <= (lock-published).days <= 365:
                errors.append(f'{prefix}: event AND publication must be within 365 days before lock')
            if not published <= accessed <= lock:
                errors.append(f'{prefix}: inconsistent source access dates')
        except (TypeError,ValueError):
            errors.append(f'{prefix}: event/publication/access dates are required')
        url = urlparse(str(record.get('canonical_url','')))
        if url.scheme != 'https' or not url.netloc or record.get('fact_check_status') != 'verified':
            errors.append(f'{prefix}: missing verified primary-source URL')
        if record.get('authority_class') != 'primary' or not record.get('verified_facts'):
            errors.append(f'{prefix}: primary evidence and factual snapshot required')
        if not all(record.get(field) for field in ('publisher','title','rights_status')):
            errors.append(f'{prefix}: source publisher/title/rights record required')
        if record.get('source_family'):families.add(record['source_family'])
        for field in ('event_to_model','nonroutine_decision'):
            if not context.get(field):errors.append(f'{prefix}: missing {field}')
        if not spec.get('scope_codes') or context.get('outside_knowledge_required') is not False:
            errors.append(f'{prefix}: curriculum mapping and self-contained model required')
    if len(linked) >= 2 and len(families) < 2:
        errors.append('math: use at least two unrelated source families')
    return errors


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exam',type=Path)
    args=parser.parse_args()
    errors=validate(json.loads(args.exam.read_text(encoding='utf-8-sig')))
    print(json.dumps({'status':'fail' if errors else 'pass','errors':errors},ensure_ascii=False))
    raise SystemExit(2 if errors else 0)
