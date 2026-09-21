"""The hosted preflight must make PyMuPDF importable from a wheel when the runtime lacks it."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import ensure_pymupdf as module  # noqa: E402

MISSING = {'importable': False, 'error': 'No module named pymupdf'}


def test_module_never_imports_pymupdf_itself():
    tree = ast.parse((ROOT / 'scripts' / 'ensure_pymupdf.py').read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split('.')[0] not in {'pymupdf', 'fitz'} for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or '').split('.')[0] not in {'pymupdf', 'fitz'}


def test_pinned_wheel_matches_the_vendored_file_when_present():
    vendored = ROOT / 'vendor' / 'wheels' / module.WHEEL_FILE
    if not vendored.is_file():
        pytest.skip('wheel not fetched locally')
    data = vendored.read_bytes()
    assert len(data) == module.WHEEL_BYTES and hashlib.sha256(data).hexdigest() == module.WHEEL_SHA256
    assert module.WHEEL_URL.endswith('/' + module.WHEEL_FILE) and module.WHEEL_URL.startswith('https://github.com/niansia/taiwan-exam/releases/download/')


def test_present_runtime_is_reported_without_installing(monkeypatch):
    monkeypatch.setattr(module, '_pip_install', lambda *a, **k: pytest.fail('must not install'))
    monkeypatch.setattr(module, 'download_wheel', lambda *a, **k: pytest.fail('must not download'))
    report = module.ensure()
    assert report['status'] == 'present' and report['method'] == 'runtime'


def test_missing_runtime_downloads_the_pinned_wheel_before_asking(monkeypatch, tmp_path):
    monkeypatch.setattr(module, 'HERE', tmp_path / 'skill' / 'scripts')
    monkeypatch.delenv('TAIWAN_EXAM_WHEEL_DIR', raising=False)
    probes = iter([MISSING, {'importable': True, 'version': '1.26.0'}])
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: next(probes))
    fetched = tmp_path / 'dl' / module.WHEEL_FILE
    fetched.parent.mkdir()
    fetched.write_bytes(b'x')
    monkeypatch.setattr(module, 'download_wheel', lambda *a, **k: {'ok': True, 'url': module.WHEEL_URL, 'path': fetched,
                                                                   'sha256': module.WHEEL_SHA256, 'bytes': 1})
    installed = []
    monkeypatch.setattr(module, '_pip_install', lambda path, extra, python: (installed.append(path), {'ok': True, 'command': [], 'output': ''})[1])
    report = module.ensure(tmp_path / 'empty')
    assert report['status'] == 'installed' and report['method'] == 'downloaded-wheel:site-packages'
    assert installed == [fetched] and report['download']['ok'] is True


def test_blocked_download_becomes_a_named_ask_for_upload(monkeypatch, tmp_path):
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: MISSING)
    monkeypatch.setattr(module, '_pip_install', lambda *a, **k: pytest.fail('nothing to install'))
    monkeypatch.setattr(module, 'download_wheel', lambda *a, **k: {'ok': False, 'url': module.WHEEL_URL, 'error': 'HTTP 403'})
    monkeypatch.delenv('TAIWAN_EXAM_WHEEL_DIR', raising=False)
    monkeypatch.setattr(module, 'HERE', tmp_path / 'skill' / 'scripts')
    report = module.ensure(tmp_path / 'empty')
    assert report['status'] == 'missing-wheel' and report['download']['error'] == 'HTTP 403'
    assert 'upload' in report['next_action'] and module.WHEEL_FILE in report['next_action']
    assert 'another PDF library' in report['next_action']
    assert str((tmp_path / 'empty').resolve()) in report['searched']


def test_no_download_flag_skips_the_network(monkeypatch, tmp_path):
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: MISSING)
    monkeypatch.setattr(module, 'download_wheel', lambda *a, **k: pytest.fail('must not download'))
    monkeypatch.setattr(module, 'HERE', tmp_path / 'skill' / 'scripts')
    monkeypatch.delenv('TAIWAN_EXAM_WHEEL_DIR', raising=False)
    report = module.ensure(tmp_path / 'empty', download=False)
    assert report['status'] == 'missing-wheel' and 'download' not in report


def test_download_rejects_bytes_that_do_not_match_the_pin(monkeypatch, tmp_path):
    class Response:
        def __init__(self, data):
            self.data = data

        def read(self, n=-1):
            return self.data

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False
    monkeypatch.setattr(module.urllib.request, 'urlopen', lambda request, timeout=0: Response(b'not the wheel'))
    result = module.download_wheel(tmp_path)
    assert result['ok'] is False and 'do not match the pinned wheel' in result['error']
    assert not (tmp_path / module.WHEEL_FILE).exists()


def test_download_reports_http_and_network_errors(monkeypatch, tmp_path):
    def forbidden(request, timeout=0):
        raise module.urllib.error.HTTPError(module.WHEEL_URL, 403, 'Forbidden', {}, None)
    monkeypatch.setattr(module.urllib.request, 'urlopen', forbidden)
    assert module.download_wheel(tmp_path) == {'ok': False, 'url': module.WHEEL_URL, 'error': 'HTTP 403'}

    def unreachable(request, timeout=0):
        raise module.urllib.error.URLError('egress denied')
    monkeypatch.setattr(module.urllib.request, 'urlopen', unreachable)
    assert module.download_wheel(tmp_path)['ok'] is False


def test_local_wheel_is_installed_with_pip_no_index(monkeypatch, tmp_path):
    wheels = tmp_path / 'resources' / 'wheels'
    wheels.mkdir(parents=True)
    wheel = wheels / 'pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.whl'
    wheel.write_bytes(b'not a real wheel')
    monkeypatch.setattr(module, 'HERE', tmp_path / 'scripts')
    monkeypatch.setattr(module, 'download_wheel', lambda *a, **k: pytest.fail('local wheel wins'))
    probes = iter([MISSING, {'importable': True, 'version': '1.26.0'}])
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: next(probes))
    commands = []

    def fake_install(path, extra, python):
        commands.append((path, extra))
        return {'ok': True, 'command': [], 'output': 'Successfully installed'}
    monkeypatch.setattr(module, '_pip_install', fake_install)
    report = module.ensure()
    assert report['status'] == 'installed' and report['method'] == 'wheel-file:site-packages'
    assert commands == [(wheel, [])]


def test_uploaded_wheel_file_is_used_directly(monkeypatch, tmp_path):
    upload = tmp_path / 'uploads' / 'pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.whl'
    upload.parent.mkdir()
    upload.write_bytes(b'x')
    monkeypatch.setattr(module, 'HERE', tmp_path / 'scripts')
    monkeypatch.setattr(module, 'download_wheel', lambda *a, **k: {'ok': False, 'url': module.WHEEL_URL, 'error': 'HTTP 403'})
    probes = iter([MISSING, {'importable': True, 'version': '1.26.0'}])
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: next(probes))
    seen = []
    monkeypatch.setattr(module, '_pip_install', lambda path, extra, python: (seen.append(path), {'ok': True, 'command': [], 'output': ''})[1])
    report = module.ensure(wheel=upload)
    assert report['status'] == 'installed' and seen == [upload.resolve()]
    other = tmp_path / 'uploads' / 'requests-2.0-py3-none-any.whl'
    other.write_bytes(b'x')
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: MISSING)
    assert module.ensure(wheel=other)['status'] == 'missing-wheel'


def test_failed_install_falls_back_to_user_site_then_stops(monkeypatch, tmp_path):
    wheels = tmp_path / 'resources' / 'wheels'
    wheels.mkdir(parents=True)
    (wheels / 'pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.whl').write_bytes(b'x')
    monkeypatch.setattr(module, 'HERE', tmp_path / 'scripts')
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: MISSING)
    monkeypatch.setattr(module, '_pip_install', lambda path, extra, python: {'ok': False, 'command': [], 'output': 'denied'})
    report = module.ensure()
    assert report['status'] == 'install-failed'
    assert [a['target'] for a in report['attempts']] == ['site-packages', 'user-site']
    assert 'do not compose pages with another PDF library' in report['next_action']


def test_real_pip_install_command_uses_no_index_and_the_wheel_folder(tmp_path):
    wheel = tmp_path / 'pymupdf-0.0-cp39-abi3-manylinux2014_x86_64.whl'
    wheel.write_bytes(b'bogus')
    result = module._pip_install(wheel, [], sys.executable)
    assert result['ok'] is False  # bogus bytes must not install
    assert '--no-index' in result['command'] and str(tmp_path) in result['command']
    assert 'pypi.org' not in ' '.join(result['command'])


def test_cli_reports_json_and_exit_status():
    completed = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'ensure_pymupdf.py'), '--no-download'],
                               capture_output=True, text=True, timeout=300)
    report = json.loads(completed.stdout)
    assert report['status'] in {'present', 'installed'} and completed.returncode == 0


def test_renamed_upload_is_restored_to_the_canonical_wheel_name(monkeypatch, tmp_path):
    upload = tmp_path / 'wheel.whl'
    with module.zipfile.ZipFile(upload, 'w') as archive:
        archive.writestr('pymupdf/__init__.py', '')
        archive.writestr('pymupdf-1.26.0.dist-info/METADATA', 'Name: PyMuPDF')
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: MISSING)
    seen = []
    monkeypatch.setattr(module, '_pip_install', lambda path, extra, python: (seen.append(path), {'ok': False, 'command': [], 'output': 'x'})[1])
    report = module.ensure(wheel=upload)
    assert report['renamed_upload']['from'] == str(upload.resolve())
    assert seen and seen[0].name == module.WHEEL_FILE and seen[0].read_bytes() == upload.read_bytes()
