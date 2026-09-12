#!/usr/bin/env python3
"""Check saved hosted-run evidence; never infer mathematical or visual quality.

Read-only, offline, and portable alongside the embedded PDF inspector. A result
of evidence-complete means recorded reviews are current, not independently true.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ITEM_GATES = ('answers', 'difficulty', 'originality', 'visuals')
PAPER_GATES = ('structure_scope', 'difficulty_balance', 'source_grounding',
               'template_composition', 'answer_separation')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(state_path: Path) -> dict:
    state = json.loads(state_path.read_text(encoding='utf-8-sig'))
    root = state_path.resolve().parent
    errors = []

    def need(ok, message):
        if not ok:
            errors.append(message)
        return ok

    def file(record, label):
        if not isinstance(record, dict):
            need(False, f'{label}: missing artifact')
            return None
        relative = record.get('path', '')
        path = (root / relative).resolve()
        if not need(bool(relative) and not Path(relative).is_absolute()
                    and path.is_relative_to(root) and path.is_file(),
                    f'{label}: missing or external artifact'):
            return None
        if not need(record.get('sha256') == sha(path), f'{label}: stale artifact hash'):
            return None
        return path

    need(state.get('schema_version') == 1, 'unsupported schema_version')
    need(bool(state.get('paper_id')), 'missing paper_id')
    need(not state.get('failed_checks'), 'run: unresolved failed checks remain')
    exam_path = file(state.get('exam'), 'exam')
    if exam_path is None:
        return {'status': 'pending', 'errors': errors, 'formal_acceptance': False}
    exam_hash = sha(exam_path)
    exam = json.loads(exam_path.read_text(encoding='utf-8-sig'))
    items = exam.get('questions', [])
    ids = [item.get('id') for item in items]
    need(bool(ids) and all(isinstance(i, str) and i.strip() for i in ids)
         and len(set(ids)) == len(ids), 'exam: missing or duplicate item IDs')
    expected = set(ids)
    need(exam.get('metadata', {}).get('paper_id') == state.get('paper_id'),
         'exam: paper_id mismatch')

    for name in ITEM_GATES + PAPER_GATES:
        path = file(state.get('checks', {}).get(name), name)
        if path is None:
            continue
        review = json.loads(path.read_text(encoding='utf-8-sig'))
        need(review.get('exam_sha256') == exam_hash, f'{name}: reviewed exam changed')
        need(review.get('status') == 'pass' and bool(review.get('observations')),
             f'{name}: missing passing review with observations')
        if name in ITEM_GATES:
            rows = review.get('items', [])
            need({r.get('id') for r in rows} == expected and len(rows) == len(expected),
                 f'{name}: item coverage incomplete or duplicate')
            for row in rows:
                allowed = {'pass', 'not_applicable'} if name == 'visuals' else {'pass'}
                need(row.get('status') in allowed and bool(row.get('observations')),
                     f'{name}/{row.get("id")}: review pending or unsupported')
        if name == 'originality':
            need(review.get('comparison_scope') in {'available-history', 'no-history-available'},
                 'originality: disclose accessible comparison scope')
            for previous in review.get('history', []):
                file(previous, 'originality/history')
            if review.get('comparison_scope') == 'available-history':
                need(bool(review.get('history')), 'originality: history evidence missing')
        if name == 'visuals' and exam.get('metadata', {}).get('subject') in {'數學A', '數學B'}:
            required = [r for r in review.get('items', [])
                        if r.get('status') == 'pass' and r.get('required_for_answer') is True]
            need(len({r.get('visual_id') for r in required if r.get('visual_id')}) >= 4,
                 'visuals: math requires four distinct answer-bearing visuals')
            sections = {q.get('section') for q in items
                        if q.get('id') in {r.get('id') for r in required} and q.get('section')}
            need(len(sections) >= 3, 'visuals: math requires coverage of three sections')
            need(len({r.get('visual_role') for r in required if r.get('visual_role')}) >= 2,
                 'visuals: math requires more than one visual role')

    pdf_hashes = []
    for role in ('question', 'solution'):
        bundle = state.get('pdfs', {}).get(role, {})
        pdf = file(bundle.get('file'), f'{role}/pdf')
        scan_path = file(bundle.get('inspection'), f'{role}/inspection')
        review_path = file(bundle.get('visual_review'), f'{role}/visual_review')
        if not all((pdf, scan_path, review_path)):
            continue
        pdf_hash = sha(pdf)
        pdf_hashes.append(pdf_hash)
        scan = json.loads(scan_path.read_text(encoding='utf-8-sig'))
        review = json.loads(review_path.read_text(encoding='utf-8-sig'))
        need(scan.get('status') == 'mechanical-review-only', f'{role}: invalid inspector report')
        need(bundle.get('exam_sha256') == exam_hash, f'{role}: PDF predates content revision')
        need(scan.get('pdf_sha256') == review.get('pdf_sha256') == pdf_hash,
             f'{role}: inspection is not bound to final PDF')
        count = scan.get('page_count', 0)
        pages = scan.get('pages', [])
        expected_pages = set(range(1, count + 1)) if type(count) is int and count > 0 else set()
        need(bool(expected_pages) and {p.get('page') for p in pages} == expected_pages
             and len(pages) == count, f'{role}: incomplete raster inspection')
        need(not scan.get('blocking_pages'), f'{role}: mechanical blocking pages remain')
        rows = review.get('pages', [])
        need({p.get('page') for p in rows} == expected_pages and len(rows) == count,
             f'{role}: not every page visually reviewed')
        by_page = {r.get('page'): r for r in rows}
        for page in pages:
            n = page.get('page')
            need(not {'non-A4-or-rotated', 'replacement-or-null-glyph', 'text-outside-page'}
                 .intersection(page.get('issues', [])), f'{role}/page-{n}: mechanical failure')
            raster = file({'path': page.get('raster_path'),
                           'sha256': page.get('raster_sha256')}, f'{role}/page-{n}/raster')
            row = by_page.get(n, {})
            need(raster is not None and row.get('raster_sha256') == page.get('raster_sha256'),
                 f'{role}/page-{n}: viewed raster changed or missing')
            need(row.get('status') == 'pass' and bool(row.get('observations')),
                 f'{role}/page-{n}: visual review incomplete')
            dispositions = row.get('issue_dispositions', {})
            for issue in page.get('issues', []):
                finding = dispositions.get(issue, {})
                # A repaired PDF needs a new inspector report, not "fixed" on old bytes.
                need(finding.get('decision') == 'justified' and bool(finding.get('reason')),
                     f'{role}/page-{n}/{issue}: unresolved review flag')
    need(len(pdf_hashes) == 2 and len(set(pdf_hashes)) == 2,
         'two distinct question and solution PDFs required')
    return {'status': 'evidence-complete' if not errors else 'pending',
            'paper_id': state.get('paper_id'), 'errors': errors,
            'formal_acceptance': False,
            'scope': 'Evidence completeness and freshness only; recorded judgments need real review.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state', type=Path)
    args = parser.parse_args()
    try:
        result = check(args.state)
    except (ValueError, TypeError, KeyError, OSError, AttributeError) as exc:
        result = {'status': 'pending', 'errors': [f'Malformed/missing evidence: {type(exc).__name__}'],
                  'formal_acceptance': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'evidence-complete' else 2)
