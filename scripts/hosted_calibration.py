#!/usr/bin/env python3
"""Offline aggregate calibration; never represent an unseen original as viewed."""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

from inspect_hosted_pdf import bottom_void

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = 'exam_packs/學測/metadata/official-current-web-sources.json'
METRICS_PATH = 'exam_packs/學測/metadata/hosted-page-metrics.json'
SUBJECTS = ('國綜', '國寫', '英文', '數學A', '數學B', '自然', '社會')


def algorithm_hash():
    return hashlib.sha256(inspect.getsource(bottom_void).replace('\r\n', '\n').encode()).hexdigest()


def snapshot(subject, root=ROOT):
    """Reconstruct from canonical extracted files, not author-supplied evidence."""
    if subject not in SUBJECTS:
        raise ValueError('Unknown calibration subject')
    sources = {}

    def read(relative):
        text = (root / relative).read_text(encoding='utf-8-sig').rstrip() + '\n'
        sources[relative] = hashlib.sha256(text.encode()).hexdigest()
        return json.loads(text) if relative.endswith('.json') else text

    source_map = read(SOURCE_PATH)
    record = next(s for s in source_map['subjects'] if s['subject'] == subject)
    controlling = max(record['years'], key=lambda y: y['roc_year'])
    profile = controlling['paper_profile']
    if profile.get('structure_status') != 'verified':
        raise ValueError('Controlling paper structure is not verified')
    base = f"exam_packs/學測/subjects/{record['catalog_subject']}/blueprints/"
    writer = read(base + 'writer-blueprint.json')
    calibration = writer['calibration_by_curriculum']['108']
    if calibration.get('status') != 'ready':
        raise ValueError('Embedded subject calibration is not ready')
    clusters = [c for c in writer['aggregate_pattern_clusters']
                if c['pattern'].get('curriculum') == '108'
                and (subject not in {'國綜', '國寫'} or
                     c['pattern'].get('section', '').startswith(subject))]
    if not clusters:
        raise ValueError('No subject-specific aggregate patterns')
    objective = None
    writing_rubric = None
    if subject == '國寫':
        writing_rubric = read('references/gsat-writing-111-115-selection-calibration.md')
    else:
        objective = read(base + 'difficulty-profile.json')['curricula']['108']
        if objective.get('status') != 'ready':
            raise ValueError('Objective calibration is not ready')
    metrics = read(METRICS_PATH)
    if metrics.get('algorithm_sha256') != algorithm_hash():
        raise ValueError('Page measurements use a stale algorithm; rebuild at release time')
    pages = [p for p in metrics['pages'] if p['subject'] == subject]
    approved = {d['sha256']: d for y in record['years'] for d in y['documents'].values()}
    if not pages:
        raise ValueError('No offline page measurements for subject')
    for page in pages:
        doc = approved.get(page.get('source_sha256'))
        if (not doc or type(page.get('page')) is not int or
                not 1 <= page['page'] <= doc['pages'] or
                type(page.get('bottom_void')) not in (int, float) or
                not 0 <= page['bottom_void'] <= 1):
            raise ValueError('Page measurement is not bound to a valid official source')
    return {'schema_version': 1, 'subject': subject,
            'basis': 'aggregate-profile-plus-expert-review',
            'limitations': ['Original PDFs are not materialized or viewed by this snapshot.',
                           'Historical aggregate targets do not prove achieved difficulty of new items.',
                           'Constructed responses require expert rubric review, not objective P/D.'],
            'source_hashes': sources, 'paper_profile': profile,
            'calibration_status': calibration, 'objective_profile': objective,
            'aggregate_patterns': clusters, 'writing_rubric': writing_rubric,
            'page_metrics': pages}


def anchor_errors(question, anchor, calibration):
    if anchor.get('kind') != 'embedded-calibration':
        return ['unknown offline anchor kind']
    constructed = (calibration['subject'] == '國寫' or
                   question.get('type') in {'constructed_response', 'essay', 'short_answer'})
    if constructed:
        expected = 'constructed-response'
    elif calibration['subject'] in {'數學A', '數學B'}:
        expected = f"slot:{question.get('number')}"
        if str(question.get('number')) not in (calibration['objective_profile'] or {}).get('by_question_number', {}):
            return ['no objective position calibration; use a compatible original anchor']
    else:
        expected = 'objective'
    return [] if anchor.get('key') == expected else [f'offline anchor key must be {expected}']


def density_limit(calibration, finding, expected_role):
    """Return a source-derived limit only for the actual candidate page role."""
    matches = [p for p in calibration['page_metrics']
               if p['source_sha256'] == finding.get('source_sha256')
               and p['page'] == finding.get('reference_page')]
    if len(matches) != 1 or matches[0]['page_role'] != expected_role or finding.get('page_role') != expected_role:
        raise ValueError('Offline density reference must match subject and actual page role')
    return matches[0]['bottom_void'] + .10
