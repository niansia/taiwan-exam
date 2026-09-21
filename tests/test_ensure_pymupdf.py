"""The hosted preflight must make PyMuPDF importable offline from the bundled wheel."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import ensure_pymupdf as module  # noqa: E402


def test_module_never_imports_pymupdf_itself():
    import ast
    tree = ast.parse((ROOT / 'scripts' / 'ensure_pymupdf.py').read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split('.')[0] not in {'pymupdf', 'fitz'} for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or '').split('.')[0] not in {'pymupdf', 'fitz'}


def test_present_runtime_is_reported_without_installing(monkeypatch):
    monkeypatch.setattr(module, '_pip_install', lambda *a, **k: pytest.fail('must not install'))
    report = module.ensure()
    assert report['status'] == 'present' and report['method'] == 'runtime'


def test_missing_runtime_without_wheel_is_a_named_blocker(monkeypatch, tmp_path):
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: {'importable': False, 'error': 'No module named pymupdf'})
    monkeypatch.setattr(module, '_pip_install', lambda *a, **k: pytest.fail('nothing to install'))
    monkeypatch.delenv('TAIWAN_EXAM_WHEEL_DIR', raising=False)
    monkeypatch.setattr(module, 'HERE', tmp_path / 'skill' / 'scripts')
    report = module.ensure(tmp_path / 'empty')
    assert report['status'] == 'missing-wheel'
    assert 'Stop before drafting' in report['next_action']
    assert str((tmp_path / 'empty').resolve()) in report['searched']


def test_bundled_wheel_is_installed_with_pip_no_index(monkeypatch, tmp_path):
    wheels = tmp_path / 'resources' / 'wheels'
    wheels.mkdir(parents=True)
    wheel = wheels / 'pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.whl'
    wheel.write_bytes(b'not a real wheel')
    monkeypatch.setattr(module, 'HERE', tmp_path / 'scripts')
    probes = iter([{'importable': False, 'error': 'No module named pymupdf'},
                   {'importable': True, 'version': '1.26.0'}])
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: next(probes))
    commands = []

    def fake_install(path, extra, python):
        commands.append((path, extra))
        return {'ok': True, 'command': [], 'output': 'Successfully installed'}
    monkeypatch.setattr(module, '_pip_install', fake_install)
    report = module.ensure()
    assert report['status'] == 'installed' and report['method'] == 'bundled-wheel:site-packages'
    assert commands == [(wheel, [])]


def test_failed_install_falls_back_to_user_site_then_stops(monkeypatch, tmp_path):
    wheels = tmp_path / 'resources' / 'wheels'
    wheels.mkdir(parents=True)
    (wheels / 'pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.whl').write_bytes(b'x')
    monkeypatch.setattr(module, 'HERE', tmp_path / 'scripts')
    monkeypatch.setattr(module, 'probe', lambda python=sys.executable: {'importable': False, 'error': 'missing'})
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
    completed = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'ensure_pymupdf.py')],
                               capture_output=True, text=True, timeout=300)
    report = json.loads(completed.stdout)
    assert report['status'] in {'present', 'installed'} and completed.returncode == 0
