#!/usr/bin/env python3
"""Check offline calibration and fixed-PDF production BEFORE authoring a paper."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pymupdf
from compose_hosted_pdf import compose
from fetch_hosted_template_assets import DEFAULT_MAP, materialize
from hosted_calibration import SUBJECTS, snapshot
from hosted_run_timing import transition


def save(path, data):
    raw = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)
    return hashlib.sha256(raw).hexdigest()


def acquire(subject, output, resource_pdf=None, local_root=None, deadline=45):
    if not 0 < deadline <= 60:
        raise ValueError('Resource deadline must be positive and at most 60 seconds')
    if resource_pdf:
        return materialize(subject, output, map_path=DEFAULT_MAP, local_root=None,
                           timeout=10, attempts=1, resource_pdf=resource_pdf)
    # A socket timeout does not bound repeated reads. Isolate the existing
    # parallel fetcher in a killable child so slow streams cannot consume a turn.
    command = [sys.executable, str(Path(__file__).with_name('fetch_hosted_template_assets.py')),
               '--subject', subject, '--output-dir', str(output), '--map', str(DEFAULT_MAP),
               '--timeout', '10', '--attempts', '1']
    if local_root:
        command += ['--local-root', str(local_root)]
    try:
        result = subprocess.run(command, capture_output=True, encoding='utf-8',
                                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, timeout=deadline)
    except subprocess.TimeoutExpired:
        return {'status': 'partial', 'errors': [{'message': 'Overall template acquisition deadline reached; '
                'retain verified cached components and use the offline resource PDF.'}]}
    if result.returncode and not result.stdout.strip():
        raise ValueError('Template helper failed: ' + result.stderr[-500:])
    return json.loads(result.stdout)


def prepare(subject, run_dir, paper_id, font, *, resource_pdf=None, local_root=None, deadline=45):
    started = time.monotonic()
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    timing = run_dir / 'generation-timing.json'
    # Never replace authored content, reviews or run-state on resume.
    for name in ('preflight.json', 'run-state.json'):
        if (run_dir / name).exists():
            previous = json.loads((run_dir / name).read_text(encoding='utf-8-sig'))
            if previous.get('paper_id') != paper_id or previous.get('subject', subject) != subject:
                raise ValueError('Refusing to reuse another paper or subject run directory')
    transition(timing, paper_id, 'reference_preflight')
    report = {'paper_id': paper_id, 'subject': subject, 'status': 'pending', 'errors': [],
              'scope': 'Resource readiness and small layout proofs only; no exam or quality approval.'}
    try:
        calibration = snapshot(subject)
        digest = save(run_dir / 'calibration.json', calibration)
        report['calibration'] = {'path': 'calibration.json', 'sha256': digest}
        report['calibration_basis'] = calibration['basis']
        report['original_pdf_required'] = False
        assets = acquire(subject, run_dir / 'templates', resource_pdf, local_root, deadline)
        if assets['status'] != 'verified':
            raise ValueError('Required template components unavailable: ' + json.dumps(assets['errors'], ensure_ascii=False))
        asset_dir = Path(assets['assets'][0]['path']).parent
        report['template_asset_dir'] = asset_dir.relative_to(run_dir).as_posix()
        proof_dir = run_dir / 'preflight-proofs'
        proof_dir.mkdir(exist_ok=True)
        body = proof_dir / 'body.pdf'
        with pymupdf.open() as doc:
            page = doc.new_page(width=595.28, height=841.89)
            page.insert_text((80, 140), 'Layout preflight only: 1 + 1 = 2', fontsize=12)
            body.write_bytes(doc.tobytes())
        proofs = {}
        for kind in ('questions', 'answers'):
            output = proof_dir / f'{kind}.pdf'
            result = compose(subject, body, asset_dir, output, year='116', title='學科能力測驗模擬試題',
                             running_name='學測', font_path=font, kind=kind)
            proofs[kind] = {'path': output.relative_to(run_dir).as_posix(), 'sha256': result['pdf_sha256']}
            with pymupdf.open(output) as doc:
                for index, page in enumerate(doc, 1):
                    page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(proof_dir / f'{kind}-{index}.png')
        report.update(status='ready-for-authoring', proofs=proofs,
                      next_action='Open the small proof rasters and check field/font fit; read the selected subject '
                      'calibration and curriculum guidance. Draft, solve and independently review small batches. '
                      'Use aggregate anchors honestly; final QA needs no original-PDF download. '
                      'Test actual body math typography separately before full composition.')
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        report['errors'].append(str(exc))
        report['next_action'] = 'Resolve the named resource/rendering gap before drafting; retain existing work.'
    report['elapsed_seconds'] = round(time.monotonic() - started, 3)
    save(run_dir / 'preflight.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject', required=True, choices=SUBJECTS)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--paper-id', required=True)
    parser.add_argument('--font', required=True, type=Path)
    parser.add_argument('--resource-pdf', type=Path)
    parser.add_argument('--local-root', type=Path)
    parser.add_argument('--deadline', type=float, default=45)
    args = parser.parse_args()
    result = prepare(args.subject, args.run_dir, args.paper_id, args.font,
                     resource_pdf=args.resource_pdf, local_root=args.local_root, deadline=args.deadline)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'ready-for-authoring' else 2)
