"""Reproducible, source-bound additions to a distributed aggregate blueprint.

The analysis ledger is never returned to a writer. This supports incremental
annotation when the private records behind an existing blueprint are unavailable;
it neither reconstructs those records nor changes their readiness claims.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path
from pack_verification import digest, positive_score, source_errors, ITEM_TYPES

LEDGER = 'metadata/calibration-additions.json'
EXTENSION = 'blueprints/writer-calibration-additions.json'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(ledger):
    """Validate reviewed observations and emit only coarse section/type families."""
    if ledger.get('schema_version') != 1 or not ledger.get('reviewer') or not ledger.get('reviewed_at'):
        raise ValueError('calibration additions: review identity/date missing')
    records = ledger.get('records') or []
    identities = set(); groups = defaultdict(list)
    for r in records:
        identity = (r['question_source']['sha256'], r['number'], r.get('part'))
        if identity in identities:
            raise ValueError('calibration additions: duplicate source item')
        identities.add(identity)
        if r['type'] not in ITEM_TYPES or not positive_score(r['score']):
            raise ValueError('calibration additions: invalid type/score')
        if (r['curriculum'] != '108' or r['year'] < 2022 or not r['section']
                or not r.get('observations') or not r.get('reasoning_operations')
                or r.get('difficulty_basis') != 'estimated'):
            raise ValueError('calibration additions: incomplete semantic annotation')
        vector = r.get('difficulty') or {}
        fields = ('overall', 'concept_depth', 'calculation_depth', 'reasoning_steps',
                  'reading_load', 'novelty', 'distractor_strength')
        if any(type(vector.get(k)) is not int or not 1 <= vector[k] <= 5 for k in fields):
            raise ValueError('calibration additions: incomplete difficulty vector')
        for key in ('question_source', 'answer_source'):
            s = r[key]
            if source_errors({'source_files': [s]}) or not s.get('pages_reviewed'):
                raise ValueError('calibration additions: missing source evidence')
            if any(type(p) is not int or not 1 <= p <= s['page_count'] for p in s['pages_reviewed']):
                raise ValueError('calibration additions: invalid reviewed page')
        if r['type'] in {'single_choice', 'multiple_choice'}:
            if type(r.get('option_count')) is not int or r['option_count'] < 2:
                raise ValueError('calibration additions: missing option count')
        elif not r.get('scoring_observations'):
            raise ValueError('calibration additions: short response needs rubric observations')
        groups[(r['curriculum'], r['section'], r['type'])].append(r)
    if not groups:
        raise ValueError('calibration additions: empty review ledger')
    clusters = []
    for (curriculum, section, kind), rows in sorted(groups.items()):
        years = sorted({r['year'] for r in rows})
        if len(years) < 3 or len({r['question_source']['sha256'] for r in rows}) < 3:
            raise ValueError('calibration additions: each family needs three reviewed official years')
        levels = sorted(r['difficulty']['overall'] for r in rows)
        clusters.append({
            'cluster_id': 'addition-' + digest([curriculum, section, kind])[:12],
            'count': len(rows), 'supporting_year_count': len(years),
            'year_range': [years[0], years[-1]],
            'proportion': round(len(rows) / len(records), 6),
            'pattern': {'curriculum': curriculum, 'regime': '111學年度起',
                        'section': section, 'domain': '跨單元', 'question_type': kind,
                        'score': None, 'unit': '篇章結構' if section == 'section-4' and ledger['subject'] == '英文' else '綜合應用',
                        'subunit': '題組資訊整合', 'stimulus_type': 'mixed',
                        'requires_diagram': any(r.get('requires_diagram') for r in rows),
                        'difficulty': {'overall': levels[len(levels)//2], 'basis': 'multi-item-aggregate'}},
            'limitations': 'Section/type coverage and estimated reasoning only; not empirical item statistics or every curriculum unit. Current verified paper slots control scores/options/subparts.'})
    return clusters


def build(subject_path):
    ledger = read(subject_path / LEDGER)
    clusters = aggregate(ledger)
    sources = {}
    for r in ledger['records']:
        for key in ('question_source', 'answer_source'):
            s = r[key]
            sources[s['relative_path']] = {k: s[k] for k in ('relative_path', 'sha256', 'page_count')}
    return {'schema_version': 1, 'source_visibility': 'aggregate-only',
            'individual_source_question_ids_included': False,
            'base_blueprint_sha256': file_sha(subject_path / 'blueprints/writer-blueprint.json'),
            'review_ledger_sha256': file_sha(subject_path / LEDGER),
            'record_count': len(ledger['records']), 'source_files': list(sources.values()),
            'aggregate_pattern_clusters': clusters}


def load_writer(subject_path, root=None):
    base = read(subject_path / 'blueprints/writer-blueprint.json')
    path = subject_path / EXTENSION
    if not path.exists():
        if (subject_path / LEDGER).exists():
            raise ValueError('calibration additions missing; rebuild reviewed additions')
        return base
    extension = read(path)
    if extension != build(subject_path):
        raise ValueError('calibration additions stale or altered; rebuild from reviewed evidence')
    errors = source_errors(extension, root)
    if errors:
        raise ValueError('calibration additions: ' + '; '.join(errors))
    merged = copy.deepcopy(base)
    merged['aggregate_pattern_clusters'].extend(extension['aggregate_pattern_clusters'])
    total = sum(c['count'] for c in merged['aggregate_pattern_clusters'])
    for c in merged['aggregate_pattern_clusters']:
        c['proportion'] = round(c['count'] / total, 6)
    merged['calibration_additions'] = {'record_count': extension['record_count'],
                                      'base_metadata_fingerprint': base.get('metadata_fingerprint'),
                                      'fingerprint_basis': 'distributed-base-and-reviewed-additions'}
    merged['metadata_fingerprint'] = digest({'base': base.get('metadata_fingerprint'), 'additions': extension})
    return merged


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    for path in (args.root / 'exam_packs').glob('*/subjects/*/' + LEDGER):
        subject_path = path.parent.parent
        extension = build(subject_path)
        errors = source_errors(extension, args.root)
        if errors:
            raise ValueError('; '.join(errors))
        (subject_path / EXTENSION).write_text(json.dumps(extension, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(f'{subject_path.name}: {extension["record_count"]} reviewed additions')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
