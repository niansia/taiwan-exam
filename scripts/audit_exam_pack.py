"""Audit profile evidence; optionally revoke unsupported verified labels only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pack_verification import paper_errors, layout_errors


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
    args = ap.parse_args(); report = audit(args.root.resolve(), args.revoke_unsupported)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False)); return int(report['status'] == 'fail')


if __name__ == '__main__':
    raise SystemExit(main())
