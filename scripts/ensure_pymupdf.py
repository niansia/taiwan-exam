#!/usr/bin/env python3
"""Make PyMuPDF importable from a wheel file when the runtime lacks it.

Every hosted PDF helper composes onto the original fixed template PDFs with
PyMuPDF. Some hosted runtimes ship without it and block package indexes. This
helper, in order: uses a wheel already on disk (an explicit ``--wheel`` file, a
bundled ``resources/wheels/`` folder, or the platform's upload folder); otherwise
downloads the pinned wheel from this project's GitHub Release and verifies its
SHA-256 before installing; otherwise asks the user, once, to download that wheel
from the README troubleshooting entry and upload it to the chat. Installation is
``pip install --no-index`` on the local file. It never touches proxy or policy
settings, never bypasses a network block, and never substitutes another PDF
library. This file must not import pymupdf at module level.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
WHEEL_PATTERN = 'pymupdf-*.whl'
# Pinned wheel: PyMuPDF 1.26.0, CPython 3.9+ stable ABI, x86_64 Linux, no dependencies (Artifex, AGPL-3.0).
WHEEL_FILE = 'pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl'
WHEEL_SHA256 = 'a3f6a45fcf8177763a2629a2ab2cad326e8950a0d120b174b56369365355a2a7'
WHEEL_BYTES = 24052460
WHEEL_URL = 'https://github.com/niansia/taiwan-exam/releases/download/wheels-pymupdf-1.26.0/' + WHEEL_FILE
DOWNLOAD_TIMEOUT = 60
README_ENTRY = 'https://github.com/niansia/taiwan-exam#readme （疑難排解：「AI 說執行環境缺少 PyMuPDF」）'
ASK_ACTION = (
    'PyMuPDF is missing, no wheel file is available offline, and this runtime could not download it from '
    f'{WHEEL_URL}. Keep saved work and ask the user, once, to download the PyMuPDF wheel ({WHEEL_FILE}, linked '
    f'from {README_ENTRY}) and upload it to this chat; then rerun `python scripts/ensure_pymupdf.py --wheel '
    'UPLOADED_FILE` and continue the paper. Do not compose pages with another PDF library or deliver a redrawn '
    'substitute.')
STOP_ACTION = (
    'Stop before drafting. The formal PDF route needs PyMuPDF and the supplied wheel could not be installed. '
    'Report this exact result to the user; do not compose pages with another PDF library or deliver a '
    'redrawn substitute.')
# Where hosted platforms place files a user uploads to the chat.
UPLOAD_DIRS = ('/mnt/user-data/uploads', '/mnt/data', '/home/user', '.')


def candidate_directories(wheel_dir: Path | None = None) -> list[Path]:
    """Wheel locations, nearest first: an explicit dir, the env override, the Skill tree, then upload folders."""
    candidates = []
    if wheel_dir:
        candidates.append(Path(wheel_dir))
    env = os.environ.get('TAIWAN_EXAM_WHEEL_DIR')
    if env:
        candidates.append(Path(env))
    for base in (HERE.parent, *HERE.parents[1:3]):
        candidates.append(base / 'resources' / 'wheels')
        candidates.append(base / 'vendor' / 'wheels')
    candidates.extend(Path(p) for p in UPLOAD_DIRS)
    unique = []
    for path in candidates:
        resolved = path.expanduser().resolve()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def is_pymupdf_wheel(path: Path) -> bool:
    """A PyMuPDF wheel by name, or by its dist-info when the upload was renamed."""
    if not path.is_file() or path.suffix.lower() != '.whl':
        return False
    if path.name.lower().startswith('pymupdf-'):
        return True
    try:
        with zipfile.ZipFile(path) as archive:
            return any(name.lower().startswith(('pymupdf-', 'pymupdf/')) for name in archive.namelist())
    except (OSError, zipfile.BadZipFile):
        return False


def find_wheels(wheel_dir: Path | None = None, wheel: Path | None = None) -> list[Path]:
    if wheel:
        path = Path(wheel).expanduser().resolve()
        return [path] if is_pymupdf_wheel(path) else []
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


def download_wheel(destination_dir: Path | None = None, url: str = WHEEL_URL,
                   timeout: int = DOWNLOAD_TIMEOUT) -> dict:
    """Fetch the pinned wheel over HTTPS and verify its size and SHA-256; never install unverified bytes."""
    if destination_dir is None:
        destination_dir = Path(tempfile.mkdtemp(prefix='taiwan-exam-wheel-'))
    destination_dir.mkdir(parents=True, exist_ok=True)
    target = destination_dir / WHEEL_FILE
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'taiwan-exam-generator ensure_pymupdf'})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(WHEEL_BYTES + 1)
    except urllib.error.HTTPError as error:
        return {'ok': False, 'url': url, 'error': f'HTTP {error.code}'}
    except (urllib.error.URLError, OSError, ValueError) as error:
        return {'ok': False, 'url': url, 'error': str(error)[:300]}
    digest = hashlib.sha256(data).hexdigest()
    if len(data) != WHEEL_BYTES or digest != WHEEL_SHA256:
        return {'ok': False, 'url': url, 'error': f'downloaded bytes do not match the pinned wheel '
                                                 f'({len(data)} bytes, sha256 {digest[:16]}…); discarded'}
    target.write_bytes(data)
    return {'ok': True, 'url': url, 'path': target, 'sha256': digest, 'bytes': len(data)}


def _pip_install(wheel: Path, extra: list[str], python: str) -> dict:
    command = [python, '-m', 'pip', 'install', '--no-index', '--no-deps', '--disable-pip-version-check',
               '--find-links', str(wheel.parent), *extra, str(wheel)]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'ok': False, 'command': command, 'error': str(error)}
    output = (completed.stdout + '\n' + completed.stderr).strip()
    return {'ok': completed.returncode == 0, 'command': command, 'output': output[-1500:]}


def ensure(wheel_dir: Path | None = None, python: str = sys.executable, wheel: Path | None = None,
           download: bool = True) -> dict:
    """Return a JSON-able report; status is present, installed, missing-wheel or install-failed."""
    before = probe(python)
    if before['importable']:
        return {'status': 'present', 'version': before.get('version'), 'method': 'runtime',
                'python': python}
    wheels = find_wheels(wheel_dir, wheel)
    machine = platform.machine().lower()
    report = {'status': 'missing-wheel', 'python': python, 'platform': f'{sys.platform}-{machine}',
              'searched': [str(p) for p in candidate_directories(wheel_dir)], 'import_error': before.get('error')}
    source = 'wheel-file'
    if not wheels:
        if wheel:
            report['requested_wheel'] = str(wheel)
        if download:
            fetched = download_wheel()
            report['download'] = {k: (str(v) if isinstance(v, Path) else v) for k, v in fetched.items()}
            if fetched['ok']:
                wheels = [fetched['path']]
                source = 'downloaded-wheel'
        if not wheels:
            report['next_action'] = ASK_ACTION
            return report
    wheel = wheels[-1]
    if not wheel.name.lower().startswith('pymupdf-'):
        # pip refuses a wheel whose filename is not a valid wheel name; restore the canonical one.
        renamed = Path(tempfile.mkdtemp(prefix='taiwan-exam-wheel-')) / WHEEL_FILE
        renamed.write_bytes(wheel.read_bytes())
        report['renamed_upload'] = {'from': str(wheel), 'to': str(renamed)}
        wheel = renamed
    report['wheel'] = str(wheel)
    attempts = []
    for label, extra in (('site-packages', []), ('user-site', ['--user'])):
        result = _pip_install(wheel, extra, python)
        attempts.append({'target': label, 'ok': result['ok'], 'output': result.get('output') or result.get('error')})
        if result['ok']:
            after = probe(python)
            if after['importable']:
                report.update(status='installed', method=f'{source}:{label}', version=after.get('version'),
                              attempts=attempts)
                return report
            attempts[-1]['ok'] = False
            attempts[-1]['output'] = 'pip reported success but a fresh interpreter cannot import pymupdf: ' \
                                     + str(after.get('error'))
    report.update(status='install-failed', attempts=attempts, next_action=STOP_ACTION)
    return report


def require() -> None:
    """For helpers: obtain and install a wheel if needed, then import; raise with the report otherwise."""
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
                                 'next_action': report.get('next_action', STOP_ACTION)}, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel-dir', type=Path, help='Directory holding a PyMuPDF wheel')
    parser.add_argument('--wheel', type=Path, help='A PyMuPDF wheel file the user uploaded to the chat')
    parser.add_argument('--no-download', action='store_true',
                        help='Do not try the GitHub Release download; use only local wheel files')
    args = parser.parse_args()
    report = ensure(args.wheel_dir, wheel=args.wheel, download=not args.no_download)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] in {'present', 'installed'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
