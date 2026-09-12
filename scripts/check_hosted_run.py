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
import pymupdf
from inspect_hosted_pdf import HARD_FAILURES, rail_collision_samples, bottom_void
from hosted_item_layout import geometry_errors, crop_bytes
from hosted_run_timing import timing_errors, summary as timing_summary
from hosted_blind_review import packet, review_errors
from verify_fixed_template_pdf import verify_pdf
from validate_math_difficulty_design import validate as math_design
from validate_paper_difficulty_balance import validate as difficulty_balance
from validate_math_context import validate as math_context_errors, source_note_samples


ITEM_GATES = ('answers', 'difficulty', 'originality', 'visuals')
PAPER_GATES = ('structure_scope', 'difficulty_balance', 'source_grounding',
               'template_composition', 'answer_separation')
SOURCE_MAP = Path(__file__).resolve().parents[1] / 'exam_packs/學測/metadata/official-current-web-sources.json'


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
    timing_path = file(state.get('timing'), 'timing')
    timing = None
    if timing_path:
        timing = json.loads(timing_path.read_text(encoding='utf-8-sig'))
        errors.extend(timing_errors(timing, state.get('paper_id')))
    exam_path = file(state.get('exam'), 'exam')
    if exam_path is None:
        return {'status': 'pending', 'errors': errors, 'formal_acceptance': False}
    exam_hash = sha(exam_path)
    exam = json.loads(exam_path.read_text(encoding='utf-8-sig'))
    errors.extend(math_context_errors(exam))
    # Execute the embedded checks on actual authored content. A passing review
    # claiming that these ran is not an equivalent execution path.
    errors.extend('difficulty_balance: ' + e for e in difficulty_balance(exam, root)['errors'])
    if exam.get('metadata', {}).get('subject') in {'數學A', '數學B'}:
        errors.extend('math_design: ' + e for e in math_design(exam)['errors'])
        questions = exam.get('questions', [])
        need(len(questions) == 20 and {q.get('number') for q in questions} == set(range(1, 21)),
             'math structure: current full paper requires 20 numbered items')
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
        if name == 'difficulty':
            blind_path = file(review.get('blind_packet'), 'difficulty/blind_packet')
            if blind_path:
                need(json.loads(blind_path.read_text(encoding='utf-8-sig')) == packet(exam),
                     'difficulty: packet changed or includes author labels')
            for question in items:
                if question.get('visual_asset'):
                    file(question['visual_asset'], f'difficulty/{question["id"]}/visual')
            need(bool(review.get('author_context')), 'difficulty: missing real author context')
            errors.extend(review_errors(exam, review))
            source_map = json.loads(SOURCE_MAP.read_text(encoding='utf-8-sig'))
            approved = {d['sha256'] for s in source_map['subjects']
                        if s['subject'] == exam['metadata']['subject']
                        for year in s['years'] for d in year['documents'].values()}
            for row in review.get('items', []):
                anchor = row.get('anchor') or {}
                reference = file(anchor.get('reference_pdf'), f'difficulty/{row.get("id")}/anchor')
                if reference:
                    need(sha(reference) in approved,
                         f'difficulty/{row.get("id")}: anchor must be a verified same-subject official source')
                    with pymupdf.open(reference) as ref:
                        page = anchor.get('page')
                        need(type(page) is int and 1 <= page <= len(ref) and bool(anchor.get('item')),
                             f'difficulty/{row.get("id")}: locate the actual anchor page and item')
        if name == 'visuals' and exam.get('metadata', {}).get('subject') in {'數學A', '數學B'}:
            required = [r for r in review.get('items', [])
                        if r.get('status') == 'pass' and r.get('required_for_answer') is True]
            need(len({r.get('visual_id') for r in required if r.get('visual_id')}) >= 4,
                 'visuals: math requires four distinct answer-bearing visuals')
            sections = {q.get('section_id') for q in items
                        if q.get('id') in {r.get('id') for r in required} and q.get('section_id')}
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
        template_dir = state.get('template_asset_dir')
        asset_dir = (root / template_dir).resolve() if isinstance(template_dir, str) and template_dir else None
        if need(asset_dir is not None and not Path(template_dir).is_absolute()
                and asset_dir.is_relative_to(root) and asset_dir.is_dir(),
                'template_asset_dir: retain the verified subject assets inside the run directory'):
            fixed = verify_pdf(pdf, exam['metadata']['subject'],
                               'questions' if role == 'question' else 'answers', asset_dir)
            errors.extend(f'{role}/fixed-template: {e}' for e in fixed['errors'])
        # Read final bytes again, independently of a hand-edited zero-issues report.
        with pymupdf.open(pdf) as actual:
            actual_count = len(actual)
            actual_issues = {}
            for number, actual_page in enumerate(actual, 1):
                collisions = rail_collision_samples(actual_page)
                need(not collisions,
                     f'{role}/page-{number}: actual PDF answer-rail-content-collision')
                rect = actual_page.rect
                need(not actual_page.rotation and abs(rect.width-595.28) <= 1 and abs(rect.height-841.89) <= 1,
                     f'{role}/page-{number}: actual PDF non-A4-or-rotated')
                text = actual_page.get_text()
                if exam.get('metadata', {}).get('subject') in {'數學A','數學B'}:
                    need(not source_note_samples(text), f'{role}/page-{number}: printed math source note')
                need('\ufffd' not in text and '\x00' not in text,
                     f'{role}/page-{number}: actual PDF replacement-or-null-glyph')
                spans = [s for b in actual_page.get_text('dict')['blocks']
                         for line in b.get('lines', []) for s in line['spans']]
                need(all(rect.contains(pymupdf.Rect(s['bbox'])) for s in spans),
                     f'{role}/page-{number}: actual PDF text-outside-page')
                actual_issues[number] = set()
                if bottom_void(actual_page) > .32:
                    actual_issues[number].add('large-bottom-void-review')
            item_path = file(bundle.get('item_review'), f'{role}/item_review')
            if item_path:
                item_review = json.loads(item_path.read_text(encoding='utf-8-sig'))
                need(item_review.get('pdf_sha256') == pdf_hash, f'{role}: stale item crops')
                parts = item_review.get('parts', [])
                need({part.get('id') for part in parts} == expected, f'{role}: item crop coverage incomplete')
                layout_errors = geometry_errors(actual, parts)
                errors.extend(f'{role}: {error}' for error in layout_errors)
                if not layout_errors:
                    for part in parts:
                        crop = file({'path': part.get('raster_path'), 'sha256': part.get('raster_sha256')},
                                    f'{role}/{part.get("id")}/crop')
                        need(crop is not None and crop.read_bytes() == crop_bytes(actual[part['page']-1], part['bbox']),
                             f'{role}/{part.get("id")}: crop is not from final PDF')
                        need(part.get('status') == 'pass' and bool(part.get('observations')),
                             f'{role}/{part.get("id")}: readable item review missing')
        scan = json.loads(scan_path.read_text(encoding='utf-8-sig'))
        review = json.loads(review_path.read_text(encoding='utf-8-sig'))
        need(scan.get('status') == 'mechanical-review-only', f'{role}: invalid inspector report')
        need(bundle.get('exam_sha256') == exam_hash, f'{role}: PDF predates content revision')
        need(scan.get('pdf_sha256') == review.get('pdf_sha256') == pdf_hash,
             f'{role}: inspection is not bound to final PDF')
        count = scan.get('page_count', 0)
        need(count == actual_count, f'{role}: inspector omitted actual PDF pages')
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
            need(actual_issues.get(n, set()).issubset(set(page.get('issues', []))),
                 f'{role}/page-{n}: inspector omitted actual density findings')
            need(not HARD_FAILURES
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
                if issue == 'large-bottom-void-review':
                    reference = file(finding.get('reference_pdf'), f'{role}/page-{n}/density-reference')
                    if reference:
                        source_map = json.loads(SOURCE_MAP.read_text(encoding='utf-8-sig'))
                        approved = {document['sha256'] for subject in source_map['subjects']
                                    if subject['subject'] == exam['metadata']['subject']
                                    for year in subject['years'] for document in year['documents'].values()}
                        need(sha(reference) in approved and sha(reference) != pdf_hash,
                             f'{role}/page-{n}: density reference must be a verified same-subject official source')
                        with pymupdf.open(reference) as ref, pymupdf.open(pdf) as candidate:
                            rn = finding.get('reference_page', 0)
                            need(finding.get('page_role') in {'cover','formula','body','solutions'},
                                 f'{role}/page-{n}: density page role missing')
                            if (need(type(rn) is int and 1 <= rn <= len(ref), f'{role}/page-{n}: invalid reference page')
                                    and need(type(n) is int and 1 <= n <= len(candidate), f'{role}/page-{n}: stale candidate page')):
                                need(bottom_void(candidate[n-1]) <= bottom_void(ref[rn-1]) + .10,
                                     f'{role}/page-{n}: bottom void exceeds reference by over 10 percentage points')
    need(len(pdf_hashes) == 2 and len(set(pdf_hashes)) == 2,
         'two distinct question and solution PDFs required')
    return {'status': 'evidence-complete' if not errors else 'pending',
            'paper_id': state.get('paper_id'), 'errors': errors,
            'formal_acceptance': False,
            'timing': timing_summary(timing) if timing and not timing_errors(timing, state.get('paper_id')) else None,
            'scope': 'Evidence completeness and freshness only; recorded judgments need real review.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state', type=Path)
    args = parser.parse_args()
    try:
        result = check(args.state)
    except (ValueError, TypeError, KeyError, OSError, AttributeError, IndexError, RuntimeError, OverflowError) as exc:
        result = {'status': 'pending', 'errors': [f'Malformed/missing evidence: {type(exc).__name__}'],
                  'formal_acceptance': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'evidence-complete' else 2)
