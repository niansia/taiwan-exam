#!/usr/bin/env python3
"""Make PyMuPDF importable offline from the wheel bundled with the hosted Skill.

Every hosted PDF helper composes onto the original fixed template PDFs with
PyMuPDF. Some hosted runtimes ship without it and block package indexes, so the
Skill carries a manylinux x86_64 abi3 wheel under ``resources/wheels/`` and this
helper installs it with ``pip --no-index``; no network is needed. It never
downloads, never touches proxy or policy settings, and never substitutes another
PDF library. This file must not import pymupdf at module level.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
WHEEL_PATTERN = 'pymupdf-*.whl'
STOP_ACTION = (
    'Stop before drafting. The formal PDF route needs PyMuPDF and neither the runtime nor the bundled '
    'wheel could supply it. Report this exact result to the user; do not compose pages with another '
    'PDF library or deliver a redrawn substitute.')


def candidate_directories(wheel_dir: Path | None = None) -> list[Path]:
    """Bundled wheel locations, nearest first: an explicit dir, the env override, then the Skill tree."""
    candidates = []
    if wheel_dir:
        candidates.append(Path(wheel_dir))
    env = os.environ.get('TAIWAN_EXAM_WHEEL_DIR')
    if env:
        candidates.append(Path(env))
    for base in (HERE.parent, *HERE.parents[1:3]):
        candidates.append(base / 'resources' / 'wheels')
        candidates.append(base / 'vendor' / 'wheels')
    unique = []
    for path in candidates:
        resolved = path.expanduser().resolve()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def find_wheels(wheel_dir: Path | None = None) -> list[Path]:
    for directory in candidate_directories(wheel_dir):
        if directory.is_dir():
            wheels = sorted(directory.glob(WHEEL_PATTERN))
            if wheels:
                return wheels
    return []


def probe(python: str = sys.executable) -> dict:
    """Import in a fresh interpreter, which is what every later helper will do."""
    code = 'import pymupdf, json; print(json.dumps({"version": pymupdf.__version__, "file": pymupdf.__file__}))'
    try:
        completed = subprocess.run([python, '-c', code], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'importable': False, 'error': str(error)}
    if completed.returncode == 0:
        try:
            return dict(json.loads(completed.stdout.strip().splitlines()[-1]), importable=True)
        except (ValueError, IndexError):
            return {'importable': True, 'version': None}
    return {'importable': False, 'error': (completed.stderr or completed.stdout).strip()[-800:]}


def _pip_install(wheel: Path, extra: list[str], python: str) -> dict:
    command = [python, '-m', 'pip', 'install', '--no-index', '--no-deps', '--disable-pip-version-check',
               '--find-links', str(wheel.parent), *extra, str(wheel)]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'ok': False, 'command': command, 'error': str(error)}
    output = (completed.stdout + '\n' + completed.stderr).strip()
    return {'ok': completed.returncode == 0, 'command': command, 'output': output[-1500:]}


def ensure(wheel_dir: Path | None = None, python: str = sys.executable) -> dict:
    """Return a JSON-able report; status is present, installed, missing-wheel or install-failed."""
    before = probe(python)
    if before['importable']:
        return {'status': 'present', 'version': before.get('version'), 'method': 'runtime',
                'python': python}
    wheels = find_wheels(wheel_dir)
    machine = platform.machine().lower()
    report = {'status': 'missing-wheel', 'python': python, 'platform': f'{sys.platform}-{machine}',
              'searched': [str(p) for p in candidate_directories(wheel_dir)], 'import_error': before.get('error')}
    if not wheels:
        report['next_action'] = STOP_ACTION
        return report
    wheel = wheels[-1]
    report['wheel'] = str(wheel)
    attempts = []
    for label, extra in (('site-packages', []), ('user-site', ['--user'])):
        result = _pip_install(wheel, extra, python)
        attempts.append({'target': label, 'ok': result['ok'], 'output': result.get('output') or result.get('error')})
        if result['ok']:
            after = probe(python)
            if after['importable']:
                report.update(status='installed', method=f'bundled-wheel:{label}', version=after.get('version'),
                              attempts=attempts)
                return report
            attempts[-1]['ok'] = False
            attempts[-1]['output'] = 'pip reported success but a fresh interpreter cannot import pymupdf: ' \
                                     + str(after.get('error'))
    report.update(status='install-failed', attempts=attempts, next_action=STOP_ACTION)
    return report


def require() -> None:
    """For helpers: install the bundled wheel if needed, then import; raise with the report otherwise."""
    try:
        importlib.import_module('pymupdf')
        return
    except ImportError:
        pass
    report = ensure()
    if report['status'] in {'present', 'installed'}:
        importlib.invalidate_caches()
        importlib.import_module('pymupdf')
        return
    raise SystemExit(json.dumps({'status': 'blocked-missing-pymupdf', 'ensure_pymupdf': report,
                                 'next_action': STOP_ACTION}, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel-dir', type=Path, help='Directory holding the bundled PyMuPDF wheel')
    args = parser.parse_args()
    report = ensure(args.wheel_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] in {'present', 'installed'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
