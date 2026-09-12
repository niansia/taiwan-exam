"""Audit profile evidence; optionally revoke unsupported verified labels only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pack_verification import paper_errors, layout_errors


def readiness(root, year=2026, check_sources=True):
    """Seven-booklet prerequisites, separate from finished-paper acceptance."""
    from exam_data import matching_slot_patterns
    rows = []
    for subject in ('國綜', '英文', '數學A', '數學B', '自然', '社會', '國寫'):
        folder = '國文' if subject in {'國綜', '國寫'} else subject
        pack = root / 'exam_packs/學測/subjects' / folder
        errors = []; paper = None; layout = None; missing = []
        try:
            records = [json.loads(x) for x in (pack / 'metadata/papers.jsonl').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
            matches = [p for p in records if p.get('year') == year and p.get('source_kind') == 'official_past_exam'
                       and (subject not in {'國綜', '國寫'} or p.get('section') == subject)]
            if len(matches) != 1:
                raise ValueError('expected one exact official paper for the requested year/booklet')
            paper = matches[0]
            errors.extend('paper: ' + e for e in paper_errors(paper, root if check_sources else None))
            layouts = [json.loads(p.read_text(encoding='utf-8-sig')) for p in (pack / 'blueprints/layout-profiles').glob('*.json')]
            layouts = [p for p in layouts if not layout_errors(p, root if check_sources else None, paper)]
            if not layouts:
                errors.append('layout: no compatible verified profile with complete evidence')
            else:
                layout = max(layouts, key=lambda p: p.get('reference_year', 0))
            from writer_calibration import load_writer
            writer = load_writer(pack, root if check_sources else None)
            if writer.get('source_visibility') != 'aggregate-only' or writer.get('individual_source_question_ids_included') is not False:
                errors.append('writer: source isolation invalid')
            curriculum = paper['curriculum']
            if writer.get('calibration_by_curriculum', {}).get(curriculum, {}).get('status', writer.get('calibration_status')) != 'ready':
                errors.append('writer: curriculum calibration incomplete')
            patterns = [p for p in writer['aggregate_pattern_clusters'] if p['pattern'].get('curriculum') == curriculum]
            slots = paper.get('evidence', {}).get('structure_review', {}).get('slots', [])
            missing = [{'slot_id': s['id'], 'section_id': s['section_id'], 'type': s['type']}
                       for s in slots if not matching_slot_patterns(patterns, paper, s)]
            if missing:
                errors.append(f'writer: {len(missing)} scored slots lack matching aggregate calibration; annotate source corpus and rebuild in the analysis phase')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(str(exc))
        rows.append({'subject': subject, 'status': 'blocked' if errors else 'prerequisites-ready',
                     'paper_id': paper.get('paper_id') if paper else None,
                     'layout_id': layout.get('profile_id') if layout else None,
                     'numbered_question_count': paper.get('numbered_question_count') if paper else None,
                     'scored_item_count': paper.get('scored_item_count') if paper else None,
                     'errors': errors, 'missing_pattern_slots': missing})
    return {'status': 'blocked' if any(r['errors'] for r in rows) else 'prerequisites-ready',
            'source_files_checked': check_sources, 'year': year, 'papers': rows,
            'note': 'Metadata-only checks do not establish local source availability. Prerequisites never replace original drafting, independent solving, content gates and review of both final PDFs.'}


def audit(root, repair=False):
    rows = []; changed = 0
    for path in sorted((root / 'exam_packs').glob('*/subjects/*/metadata/papers.jsonl')):
        records = [json.loads(x) for x in path.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
        dirty = False
        for r in records:
            if r.get('structure_status') != 'verified':
                continue
            errors = paper_errors(r, root)
            rows.append({'file': str(path.relative_to(root)), 'id': r.get('paper_id'), 'errors': errors})
            if errors and repair:
                # Preserve source files and all observed content. Never guess a
                # missing type mix or grant verification from a recipe.
                r['structure_status'] = 'needs_review'
                ev = r.setdefault('evidence', {})
                ev['confidence'] = min(ev.get('confidence', 0), 0.8)
                ev['notes'] = 'Verification revoked: no complete hash-bound page/slot review. Previous note: ' + (ev.get('notes') or '')
                if r.get('subject') == '自然' and 2022 <= r.get('year', 0) <= 2026:
                    for section in r.get('sections', []):
                        if section.get('question_number_start') == 1 and section.get('question_number_end') == 36 and section.get('question_type_mix') == {'single_choice': 36}:
                            section['question_type_mix'] = {}
                            ev['notes'] += ' Natural choice section mix is unresolved, not 36 single-choice items.'
                dirty = True; changed += 1
        if dirty:
            path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records), encoding='utf-8')
    for path in sorted((root / 'exam_packs').glob('*/subjects/*/blueprints/layout-profiles/*.json')):
        r = json.loads(path.read_text(encoding='utf-8-sig'))
        if r.get('fidelity_status') == 'verified':
            errors = layout_errors(r, root)
            rows.append({'file': str(path.relative_to(root)), 'id': r.get('profile_id'), 'errors': errors})
            if errors and repair:
                r['fidelity_status'] = 'reference-only'
                path.write_text(json.dumps(r, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                changed += 1
    return {'status': 'fail' if any(r['errors'] for r in rows) else 'pass-claims-only',
            'changed_profiles': changed, 'profiles': rows,
            'note': 'Checks existing verified claims only; absence of verified profiles is NOT generation readiness.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--revoke-unsupported', action='store_true')
    ap.add_argument('--output', type=Path)
    ap.add_argument('--readiness', action='store_true', help='Check all seven current GSAT booklets, including aggregate coverage')
    ap.add_argument('--metadata-only', action='store_true', help='Do not assert availability of source PDFs (e.g. source-only CI)')
    ap.add_argument('--year', type=int, default=2026, help='Gregorian reference year, default 2026 / ROC 115')
    args = ap.parse_args()
    if args.metadata_only and not args.readiness:
        ap.error('--metadata-only requires --readiness')
    if args.readiness and args.revoke_unsupported:
        ap.error('readiness is read-only; do not combine with --revoke-unsupported')
    report = readiness(args.root.resolve(), args.year, not args.metadata_only) if args.readiness else audit(args.root.resolve(), args.revoke_unsupported)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False)); return int(report['status'] in {'fail', 'blocked'})


if __name__ == '__main__':
    raise SystemExit(main())
