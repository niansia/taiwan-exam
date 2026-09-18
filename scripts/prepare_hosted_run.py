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
from fetch_hosted_template_assets import DEFAULT_MAP, PRODUCTION_COMPONENTS, materialize, production_records, verify
from hosted_calibration import SUBJECTS, snapshot
from hosted_run_timing import transition
from hosted_blind_review import REVIEW_MODES
from verify_fixed_template_pdf import verify_pdf


PREFLIGHT_DEPENDENCIES = (
    'prepare_hosted_run.py', 'compose_hosted_pdf.py', 'fetch_hosted_template_assets.py',
    'verify_fixed_template_pdf.py', 'inspect_hosted_pdf.py', 'validate_math_context.py',
    'hosted_calibration.py', 'hosted_run_timing.py', 'hosted_blind_review.py',
)


TEMPLATE_GAP_ACTION = (
    'Stop before drafting. Formal PDFs require the original fixed template components; never typeset or '
    'redraw a cover, running header/footer, answer-marking example or formula page with LaTeX, HTML, Word '
    'or drawing tools, and never deliver such a substitute. Tell the user which component failed and ask '
    'them to attach taiwan-exam-template-resources.pdf from '
    'https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates, then rerun with --resource-pdf.')


class TemplateUnavailable(ValueError):
    """The fixed template components needed for formal PDFs could not be verified."""


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cache_inputs(font):
    """Local runtime identity, not an installation or educational approval."""
    scripts = Path(__file__).resolve().parent
    return {'version': 1, 'font': {'path': str(font.resolve()), 'sha256': digest(font)},
            'pymupdf': pymupdf.VersionBind, 'template_map_sha256': digest(DEFAULT_MAP),
            'helpers': {name: digest(scripts / name) for name in PREFLIGHT_DEPENDENCIES}}


def cached_ready(previous, report, run_dir, font, calibration):
    """Reuse only intact readiness proofs; never touch a resumed paper's clock."""
    if not previous or previous.get('status') != 'ready-for-authoring' or previous.get('errors'):
        return False
    for key in ('paper_id', 'subject', 'review_mode', 'require_independent_review', 'scope'):
        if previous.get(key) != report.get(key):
            return False
    try:
        if previous.get('cache_inputs') != cache_inputs(font):
            return False
        # Detect a changed preflight record before trusting its artifact table.
        bound = {k: v for k, v in previous.items() if k != 'record_sha256'}
        if previous.get('record_sha256') != hashlib.sha256(
                json.dumps(bound, ensure_ascii=False, sort_keys=True).encode()).hexdigest():
            return False
        def intact(record, expected):
            path = run_dir / expected
            return (record.get('path') == expected and path.resolve().is_relative_to(run_dir)
                    and path.is_file() and record.get('sha256') == digest(path))
        if not intact(previous.get('calibration', {}), 'calibration.json'):
            return False
        if json.loads((run_dir / 'calibration.json').read_text(encoding='utf-8-sig')) != calibration:
            return False
        manifest = json.loads(DEFAULT_MAP.read_text(encoding='utf-8-sig'))
        subject = next(r for r in manifest['subjects'] if r['subject'] == report['subject'])
        relative = 'templates/' + subject['slug']
        asset_dir = (run_dir / relative).resolve()
        if previous.get('template_asset_dir') != relative or not asset_dir.is_relative_to(run_dir):
            return False
        for asset in subject['assets']:
            if asset['component'] in PRODUCTION_COMPONENTS:
                path = asset_dir / (asset['component'] + '.pdf')
                if not path.resolve().is_relative_to(run_dir):
                    return False
                verify(asset, path.read_bytes())
        if set(previous.get('proofs', {})) != {'questions', 'answers'}:
            return False
        for kind, proof in previous['proofs'].items():
            expected = f'preflight-proofs/{kind}.pdf'
            if not intact(proof, expected):
                return False
            verified = verify_pdf(run_dir / expected, report['subject'], kind, asset_dir)
            if verified['status'] != 'pass-fixed-template':
                return False
            rasters = proof.get('rasters', [])
            if len(rasters) != len(verified['pages']):
                return False
            if not all(intact(row, f'preflight-proofs/{kind}-{index}.png')
                       for index, row in enumerate(rasters, 1)):
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        return False


def save(path, data):
    raw = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)
    return hashlib.sha256(raw).hexdigest()


def bundled_root(subject):
    """This Skill's own root when it carries every component the subject needs."""
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(DEFAULT_MAP.read_text(encoding='utf-8-sig'))
    row = next((r for r in manifest['subjects'] if r['subject'] == subject), None)
    if row is None or not all((root / r['repository_path']).is_file() for r in production_records(row)):
        return None
    return root


def acquire(subject, output, resource_pdf=None, local_root=None, deadline=45):
    if not 0 < deadline <= 60:
        raise ValueError('Resource deadline must be positive and at most 60 seconds')
    if resource_pdf:
        return dict(materialize(subject, output, map_path=DEFAULT_MAP, local_root=None,
                                timeout=10, attempts=1, resource_pdf=resource_pdf), source='uploaded-resource-pdf')
    bundled = None if local_root else bundled_root(subject)
    if bundled:
        # Bundled bytes are checked against the map; a damaged copy fails closed
        # instead of falling back to a download.
        return dict(materialize(subject, output, map_path=DEFAULT_MAP, local_root=bundled,
                                timeout=10, attempts=1), source='bundled-with-skill')
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
    return dict(json.loads(result.stdout), source='local-root' if local_root else 'download')


def prepare(subject, run_dir, paper_id, font, *, resource_pdf=None, local_root=None, deadline=45,
            review_mode='single-context', require_independent_review=False):
    started = time.monotonic()
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    timing = run_dir / 'generation-timing.json'
    previous_preflight = None
    # Never replace authored content, reviews or run-state on resume.
    for name in ('preflight.json', 'run-state.json'):
        if (run_dir / name).exists():
            previous = json.loads((run_dir / name).read_text(encoding='utf-8-sig'))
            if previous.get('paper_id') != paper_id or previous.get('subject', subject) != subject:
                raise ValueError('Refusing to reuse another paper or subject run directory')
            if previous.get('require_independent_review') is True:
                require_independent_review = True  # Never drop an explicit requirement on resume.
            if name == 'preflight.json':
                previous_preflight = previous
    report = {'paper_id': paper_id, 'subject': subject, 'status': 'pending', 'errors': [],
              'review_mode': review_mode, 'require_independent_review': require_independent_review,
              'scope': 'Resource readiness and small layout proofs only; no exam or quality approval.'}
    try:
        if review_mode not in REVIEW_MODES:
            raise ValueError('Unknown difficulty review mode')
        if require_independent_review and review_mode != 'independent-context':
            raise ValueError('Explicit independent review requirement needs an actual separate reviewer; resolve before authoring')
        calibration = snapshot(subject)
        if timing.is_file() and cached_ready(previous_preflight, report, run_dir, font, calibration):
            clock = json.loads(timing.read_text(encoding='utf-8-sig'))
            if clock.get('paper_id') != paper_id:
                raise ValueError('Refusing to mix paper clocks')
            resumed = dict(previous_preflight)
            resumed.update(reused_preflight=True, elapsed_seconds=round(time.monotonic() - started, 3),
                           next_action='Resume the saved paper and its next_action; readiness artifacts were verified '
                           'without rebuilding proofs, repeating their visual review, or changing the active phase clock.')
            resumed['record_sha256'] = hashlib.sha256(json.dumps(
                {k: v for k, v in resumed.items() if k != 'record_sha256'},
                ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            return resumed
        transition(timing, paper_id, 'reference_preflight')
        calibration_digest = save(run_dir / 'calibration.json', calibration)
        report['calibration'] = {'path': 'calibration.json', 'sha256': calibration_digest}
        report['calibration_basis'] = calibration['basis']
        report['original_pdf_required'] = False
        try:
            assets = acquire(subject, run_dir / 'templates', resource_pdf, local_root, deadline)
        except (OSError, ValueError, RuntimeError) as exc:
            raise TemplateUnavailable(str(exc)) from exc
        if assets['status'] != 'verified':
            raise TemplateUnavailable('Required template components unavailable: '
                                      + json.dumps(assets['errors'], ensure_ascii=False))
        report['template_source'] = assets.get('source', 'unspecified')
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
            proofs[kind] = {'path': output.relative_to(run_dir).as_posix(), 'sha256': result['pdf_sha256'],
                            'rasters': []}
            with pymupdf.open(output) as doc:
                for index, page in enumerate(doc, 1):
                    raster = proof_dir / f'{kind}-{index}.png'
                    page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(raster)
                    proofs[kind]['rasters'].append({'path': raster.relative_to(run_dir).as_posix(),
                                                   'sha256': digest(raster)})
        report['cache_inputs'] = cache_inputs(font)
        report.update(status='ready-for-authoring', proofs=proofs,
                      next_action='Open the small proof rasters and check field/font fit; read the selected subject '
                      'calibration and curriculum guidance. Use the recorded review_mode for small batches: '
                      'single-context means a fresh answer-free solving pass followed by answer comparison, '
                      'not independent blind review. Never invent a reviewer context. '
                      'Use aggregate anchors honestly; final QA needs no original-PDF download. '
                      'Test actual body math typography separately before full composition.')
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        if not timing.exists():
            transition(timing, paper_id, 'reference_preflight')
        report['errors'].append(str(exc))
        report['next_action'] = (TEMPLATE_GAP_ACTION if isinstance(exc, TemplateUnavailable) else
                                 'Resolve the named resource/rendering gap before drafting; retain existing work.')
    report['elapsed_seconds'] = round(time.monotonic() - started, 3)
    report['record_sha256'] = hashlib.sha256(
        json.dumps(report, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
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
    parser.add_argument('--review-mode', choices=REVIEW_MODES, default='single-context',
                        help='Select independent-context only when a real separate reviewer is available')
    parser.add_argument('--require-independent-review', action='store_true',
                        help='Preserve an explicit user requirement; do not enable merely because it is preferred')
    args = parser.parse_args()
    result = prepare(args.subject, args.run_dir, args.paper_id, args.font,
                     resource_pdf=args.resource_pdf, local_root=args.local_root, deadline=args.deadline,
                     review_mode=args.review_mode, require_independent_review=args.require_independent_review)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'ready-for-authoring' else 2)
