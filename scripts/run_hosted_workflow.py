#!/usr/bin/env python3
"""Batch mechanical hosted work. Never author questions or approve reviews.

checkpoint registers saved work; build renders/composes/prepares BOTH booklets;
finalize registers actual review files, closes the clock and runs the final gate.
All paths in state remain relative to the run, not the shell working directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

from hosted_run_timing import PHASES, transition
from hosted_body_templates import render
from compose_hosted_pdf import compose
from prepare_hosted_review import prepare
from check_hosted_run import check, ITEM_GATES, PAPER_GATES
from fetch_hosted_template_assets import DEFAULT_MAP


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    temporary.replace(path)


def inside(root, path):
    path = Path(path).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Artifact must stay inside this run: ' + str(path))
    return path


def record(root, path):
    path = inside(root, path)
    return {'path': path.relative_to(root.resolve()).as_posix(), 'sha256': digest(path)}


def event(root, action, started, **details):
    with (root / 'workflow-events.jsonl').open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps({'action': action, 'started_at': started,
                                'elapsed_seconds': round(time.time() - started, 4), **details}) + '\n')


def register_reviews(root, state):
    """Register real supplied reports; never fill status/observations or rebind exam hashes."""
    checks = state.setdefault('checks', {})
    for gate in ITEM_GATES + PAPER_GATES:
        path = root / checks.get(gate, {}).get('path', gate + '.json')
        inside(root, path)
        if path.is_file():
            review = read(path)
            if review.get('exam_sha256') != state['exam']['sha256']:
                continue  # Retain stale/missing evidence; the checker must reject it.
            checks[gate] = record(root, path)
    for bundle in state.get('pdfs', {}).values():
        for key in ('inspection', 'visual_review', 'item_review'):
            saved = bundle.get(key)
            if not saved:
                continue
            path = inside(root, root / saved['path'])
            if read(path).get('pdf_sha256') != bundle['file']['sha256']:
                raise ValueError('Review belongs to another PDF: ' + key)
            bundle[key] = record(root, path)


def checkpoint(run_dir, phase=None, review_bundle=None, state=None):
    started = time.time()
    root = Path(run_dir).resolve()
    preflight = read(root / 'preflight.json')
    if preflight.get('status') != 'ready-for-authoring':
        raise ValueError('Resolve preflight before creating a run checkpoint')
    state_path = inside(root, state) if state else root / 'run-state.json'
    if state_path.parent != root:
        raise ValueError('State must be directly inside the run')
    state = read(state_path) if state_path.exists() else {
        'schema_version': 1, 'paper_id': preflight['paper_id'],
        'subject': preflight['subject'], 'checks': {}, 'pdfs': {},
        'review_mode': preflight['review_mode'],
        'require_independent_review': preflight['require_independent_review'],
        'calibration': preflight['calibration'],
        'template_asset_dir': preflight['template_asset_dir'],
    }
    if state['paper_id'] != preflight['paper_id'] or state.get('subject') != preflight['subject']:
        raise ValueError('Checkpoint belongs to another paper or subject')
    if preflight['require_independent_review']:
        state['require_independent_review'] = True
    exam = root / 'exam.json'
    if exam.exists():
        metadata = read(exam).get('metadata', {})
        if metadata.get('paper_id') != state['paper_id'] or metadata.get('subject') != state['subject']:
            raise ValueError('Saved exam belongs to another paper or subject')
        state['exam'] = record(root, exam)
    if phase:
        if phase not in PHASES:
            raise ValueError('Unknown phase')
        transition(root / 'generation-timing.json', state['paper_id'], phase)
        state['current_phase'] = phase
    state['timing'] = record(root, root / 'generation-timing.json')
    if review_bundle:
        # One actual review session may write a bundle of complete gate records.
        # This is a lossless fan-out, not auto-generated review text or a pass.
        supplied = read(review_bundle)
        if not supplied or set(supplied) - set(ITEM_GATES + PAPER_GATES):
            raise ValueError('Review bundle must map existing gate names to their real reports')
        for gate, report in supplied.items():
            if report.get('exam_sha256') != state.get('exam', {}).get('sha256'):
                raise ValueError('Review bundle has a stale exam hash: ' + gate)
        for gate, report in supplied.items():
            destination = root / (gate + '.json')
            if destination.exists() and read(destination) != report:
                raise ValueError('Preserve earlier review; update its recorded file explicitly: ' + gate)
        for gate, report in supplied.items():
            save(root / (gate + '.json'), report)
    if state.get('exam'):
        register_reviews(root, state)
    save(state_path, state)
    event(root, 'checkpoint', started, phase=phase)
    return {'status': 'checkpoint-saved', 'state': str(state_path),
            'exam_saved': bool(state.get('exam')), 'registered_reviews': sorted(state['checks']),
            'reviews_approved_by_tool': False}


def build(state_path, question_spec, solution_spec, font, output, *, year,
          title='學科能力測驗模擬試題', running_name='學測', reading_font=None):
    started = time.time()
    state_path = Path(state_path).resolve()
    root = state_path.parent
    state = read(state_path)
    exam_path = inside(root, root / state['exam']['path'])
    if record(root, exam_path) != state['exam']:
        raise ValueError('Save a checkpoint for the current exam before building')
    exam = read(exam_path)
    subject = exam['metadata']['subject']
    if exam['metadata']['paper_id'] != state['paper_id']:
        raise ValueError('Wrong paper')
    output = inside(root, output)
    if output.parent != root:
        raise ValueError('Build output must be a direct child directory of the run')
    review_output = root / (output.name + '-review')
    candidate = root / (review_output.name + '-run-state.json')
    assets = inside(root, root / state['template_asset_dir'])
    specs = {'question': Path(question_spec).resolve(), 'solution': Path(solution_spec).resolve()}
    asset_inputs = {}
    for path in specs.values():
        inside(root, path)
        spec = read(path)
        if spec.get('subject') != subject:
            raise ValueError('Body spec must match the actual exam subject')
        for block in spec.get('blocks', []):
            for asset in block.get('assets', {}).values():
                asset_path = inside(root, path.parent / asset['path'])
                if digest(asset_path) != asset['sha256']:
                    raise ValueError('Body asset hash changed: ' + asset['path'])
                asset_inputs[asset_path.relative_to(root).as_posix()] = asset['sha256']
    # Same-byte cache includes every portable helper: renderer fixes invalidate it.
    scripts = Path(__file__).resolve().parent
    identity = {'exam': state['exam'], 'paper_id': state['paper_id'], 'subject': subject,
                'review_mode': state.get('review_mode'),
                'require_independent_review': state.get('require_independent_review', False),
                'specs': {role: record(root, path) for role, path in specs.items()},
                'font': digest(font), 'reading_font': digest(reading_font) if reading_font else None,
                'year': str(year), 'title': title, 'running_name': running_name,
                'assets': {p.name: digest(p) for p in sorted(assets.glob('*.pdf'))},
                'body_assets': asset_inputs, 'template_map': digest(DEFAULT_MAP),
                'helpers': {p.name: digest(p) for p in sorted(scripts.glob('*.py'))}}
    manifest_path = output / 'workflow-build.json'
    if output.exists():
        if not manifest_path.exists():
            raise ValueError('Partial build exists; preserve it and use a new output name')
        manifest = read(manifest_path)
        if manifest['inputs'] != identity:
            raise ValueError('Build inputs changed; use a new output name for the repair')
        for artifact in manifest['artifacts']:
            if record(root, root / artifact['path']) != artifact:
                raise ValueError('Cached build artifact changed: ' + artifact['path'])
        if not candidate.is_file():
            raise ValueError('Cached review state missing; recover it before continuing')
        cached_state = read(candidate)
        for name in ('exam', 'paper_id', 'review_mode'):
            if cached_state.get(name) != state.get(name):
                raise ValueError('Cached review state changed: ' + name)
        if cached_state.get('require_independent_review', False) != state.get('require_independent_review', False):
            raise ValueError('Cached review state changed: require_independent_review')
        if set(cached_state.get('pdfs', {})) != {'question', 'solution'}:
            raise ValueError('Cached review state is missing a booklet')
        for role, bundle in cached_state['pdfs'].items():
            if (bundle.get('exam_sha256') != state['exam']['sha256'] or
                    bundle.get('file') != record(root, output / (role + '.pdf'))):
                raise ValueError('Cached review state belongs to different PDF bytes')
            for name in ('inspection', 'visual_review', 'item_review'):
                path = inside(root, root / bundle[name]['path'])
                if read(path).get('pdf_sha256') != bundle['file']['sha256']:
                    raise ValueError('Cached review belongs to a different PDF: ' + name)
        event(root, 'build', started, cache_hit=True)
        return {**manifest['result'], 'cache_hit': True}
    if review_output.exists() or candidate.exists():
        raise ValueError('Review output already exists; choose a new build name')
    transition(root / 'generation-timing.json', state['paper_id'], 'render_repair')
    output.mkdir()
    pairs = {}
    for role, spec_path in specs.items():
        body = output / (role + '-body.pdf')
        layout = output / (role + '-layout.json')
        pdf = output / (role + '.pdf')
        render(read(spec_path), body, layout, Path(font), asset_root=spec_path.parent,
               reading_font=Path(reading_font) if reading_font else None)
        compose(subject, body, assets, pdf, year=str(year), title=title,
                running_name=running_name, font_path=Path(font),
                kind='questions' if role == 'question' else 'answers')
        pairs[role] = (pdf, body, layout)
    result = prepare(state_path, pairs, review_output)
    transition(root / 'generation-timing.json', state['paper_id'], 'visual_qa')
    reviewed = read(candidate)
    reviewed['timing'] = record(root, root / 'generation-timing.json')
    reviewed['current_phase'] = 'visual_qa'
    save(candidate, reviewed)
    # Human observations may change; immutable PDFs, layouts and images may not.
    immutable = [p for p in output.iterdir() if p.is_file()]
    immutable += list(review_output.rglob('*.png'))
    result.update(cache_hit=False, reviews_approved_by_tool=False,
                  next='Review actual page/item images and record observations, then finalize this state.')
    save(manifest_path, {'inputs': identity, 'artifacts': [record(root, p) for p in immutable], 'result': result})
    event(root, 'build', started, cache_hit=False)
    return result


def finalize(state_path, output):
    started = time.time()
    state_path = Path(state_path).resolve()
    root = state_path.parent
    state = read(state_path)
    output = inside(root, output)
    protected = {state_path, root / 'exam.json', root / 'generation-timing.json', root / 'preflight.json'}
    # Gate files may exist before their first registration. Never replace their
    # real observations with the final result, even when absent from old state.
    protected.update(root / (gate + '.json') for gate in ITEM_GATES + PAPER_GATES)
    def collect(value):
        if isinstance(value, dict):
            if isinstance(value.get('path'), str):
                protected.add((root / value['path']).resolve())
            for nested in value.values(): collect(nested)
        elif isinstance(value, list):
            for nested in value: collect(nested)
    collect(state)
    if output in protected or output.suffix.lower() != '.json':
        raise ValueError('Final report must not overwrite input or evidence artifacts')
    if output.exists():
        previous = read(output)
        if (not isinstance(previous, dict) or
                previous.get('scope') != 'Evidence completeness and freshness only; recorded judgments need real review.' or
                previous.get('status') not in {'pending', 'evidence-complete'} or
                previous.get('formal_acceptance') is not False or not isinstance(previous.get('errors'), list)):
            raise ValueError('Final report must not overwrite unrelated existing work')
    exam_path = inside(root, root / state['exam']['path'])
    if record(root, exam_path) != state['exam']:
        raise ValueError('Exam changed; recheck affected content and rebuild before finalizing')
    register_reviews(root, state)
    timing = root / 'generation-timing.json'
    if read(timing).get('active') is not None:
        transition(timing, state['paper_id'])
    state['timing'] = record(root, timing)
    save(state_path, state)
    result = check(state_path)
    save(output, result)
    event(root, 'finalize', started, status=result['status'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    start = commands.add_parser('checkpoint')
    start.add_argument('--run-dir', type=Path, required=True)
    start.add_argument('--phase', choices=sorted(PHASES))
    start.add_argument('--review-bundle', type=Path)
    start.add_argument('--state', type=Path, help='On repair, continue the latest review state')
    build_parser = commands.add_parser('build')
    for name in ('state', 'question-spec', 'solution-spec', 'font', 'output'):
        build_parser.add_argument('--' + name, type=Path, required=True)
    build_parser.add_argument('--year', required=True)
    build_parser.add_argument('--title', default='學科能力測驗模擬試題')
    build_parser.add_argument('--running-name', default='學測')
    build_parser.add_argument('--reading-font', type=Path)
    finish = commands.add_parser('finalize')
    finish.add_argument('--state', type=Path, required=True)
    finish.add_argument('--output', type=Path, required=True)
    args = vars(parser.parse_args())
    action = args.pop('action')
    try:
        if action == 'checkpoint':
            result = checkpoint(**args)
        else:
            args['state_path'] = args.pop('state')
            result = (build if action == 'build' else finalize)(**args)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(json.dumps({'status': 'pending', 'errors': [str(exc)]}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result.get('status') == 'pending' else 0


if __name__ == '__main__':
    raise SystemExit(main())
