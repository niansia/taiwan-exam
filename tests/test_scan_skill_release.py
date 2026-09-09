import hashlib
import json
from pathlib import Path
import sys
import pytest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import scan_skill_release as security

SOURCE_URL = 'https://example.org/releases/skill-v1.zip'


def archive(tmp_path, name='SKILL.md', tamper=False):
    path = tmp_path / 'test.zip'
    body = b'fixture'
    record = {'path': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    with ZipFile(path, 'w') as zipped:
        zipped.writestr('taiwan-exam-generator/' + name, b'changed' if tamper else body)
        zipped.writestr('taiwan-exam-generator/PACKAGE_MANIFEST.json', json.dumps({'files': [record]}))
    return path


def scan(path, callback=lambda _: {'returncode': 0, 'output': 'fixture scan'}):
    return security.scan_release(path, source_url=SOURCE_URL, status_fn=lambda: {'fixture': True}, scan_fn=callback,
        attachment_fn=lambda path, url: {'status': 'pass', 'hresult': 0, 'archive_sha256': security.digest(path), 'source_url': url})


def test_scans_archive_and_extracted_members(tmp_path):
    report = scan(archive(tmp_path))
    assert report['status'] == 'pass'
    assert [row['target'] for row in report['scans']] == ['archive', 'extracted-members']


def test_detection_blocks_before_extraction(tmp_path):
    report = scan(archive(tmp_path), lambda _: {'returncode': 2, 'output': 'detection'})
    assert report['status'] == 'fail'
    assert len(report['scans']) == 1


def test_changed_manifest_blocks(tmp_path):
    assert scan(archive(tmp_path, tamper=True))['status'] == 'fail'


def test_retired_helpers_block(tmp_path):
    assert scan(archive(tmp_path, 'scripts/paginate_chinese_natural.js'))['status'] == 'fail'


def test_path_traversal_blocks(tmp_path):
    assert scan(archive(tmp_path, '../escape.txt'))['status'] == 'fail'
    assert not (tmp_path / 'escape.txt').exists()


def test_scanner_error_blocks(tmp_path):
    def unavailable(_):
        raise OSError('not installed')
    assert scan(archive(tmp_path), unavailable)['status'] == 'fail'


def test_changed_zip_during_scan_blocks(tmp_path):
    path = archive(tmp_path)
    def change(target):
        if target.is_dir():
            with path.open('ab') as stream:
                stream.write(b'changed')
        return {'returncode': 0, 'output': 'fixture scan'}
    assert scan(path, change)['status'] == 'fail'


def test_disappearing_member_during_scan_blocks(tmp_path):
    def quarantine(target):
        if target.is_dir():
            (target / 'SKILL.md').unlink()
        return {'returncode': 0, 'output': 'fixture scan'}
    assert scan(archive(tmp_path), quarantine)['status'] == 'fail'


def test_attachment_rejection_overrides_clean_file_scans(tmp_path):
    report = security.scan_release(archive(tmp_path), source_url=SOURCE_URL, status_fn=lambda: {},
        scan_fn=lambda _: {'returncode': 0, 'output': 'clean'},
        attachment_fn=lambda *args: {'status': 'fail', 'hresult': -2147024671})
    assert report['status'] == 'fail'


def test_attachment_hash_mismatch_blocks(tmp_path):
    report = security.scan_release(archive(tmp_path), source_url=SOURCE_URL, status_fn=lambda: {},
        scan_fn=lambda _: {'returncode': 0, 'output': 'clean'},
        attachment_fn=lambda *args: {'status': 'pass', 'hresult': 0, 'archive_sha256': '0' * 64, 'source_url': SOURCE_URL})
    assert report['status'] == 'fail'


def test_attachment_failure_keeps_diagnostic_codes(tmp_path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(security.subprocess, 'run', lambda *a, **k: SimpleNamespace(
        returncode=2, stdout=json.dumps({'status':'fail', 'hresult':-2147024671, 'hresult_hex':'0x800700E1', 'private_path':'do-not-export'})))
    report = security.attachment_scan(tmp_path / 'fixture.zip', SOURCE_URL)
    assert report['status'] == 'fail' and report['hresult_hex'] == '0x800700E1'
    assert 'private_path' not in report


def test_powershell_child_does_not_inherit_ps7_module_paths(monkeypatch):
    monkeypatch.setenv('PSModulePath', 'fixture-ps7-modules')
    monkeypatch.setenv('TAIWAN_EXAM_TEST_VALUE', 'keep')
    child = security.windows_powershell_env()
    assert not any(key.upper() == 'PSMODULEPATH' for key in child)
    assert child['TAIWAN_EXAM_TEST_VALUE'] == 'keep'
    assert any(key.upper() == 'PSMODULEPATH' for key in security.os.environ)


@pytest.mark.parametrize('url', [None, '', 'http://example.org/file.zip',
    'https://user:password@example.org/file.zip', 'https://example.org/file.zip?token=secret',
    'https://example.org/file.zip#fragment', 'https:///file.zip',
    'https://example.org/file\n.zip', 'https://example.org\\file.zip'])
def test_invalid_source_fails_before_scanner(tmp_path, url):
    calls = []
    report = security.scan_release(archive(tmp_path), source_url=url,
        status_fn=lambda: calls.append('must not run'))
    assert report['status'] == 'fail' and not calls
    assert 'source_url' not in report


def test_attachment_receives_and_reports_actual_source_url(tmp_path, monkeypatch):
    from types import SimpleNamespace
    observed = []
    def run(command, **kwargs):
        observed.append(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            'status': 'pass', 'hresult': 0, 'source_url': SOURCE_URL}))
    monkeypatch.setattr(security.subprocess, 'run', run)
    result = security.attachment_scan(tmp_path / 'fixture.zip', SOURCE_URL)
    assert observed[0][-2:] == ['-SourceUrl', SOURCE_URL]
    assert result['status'] == 'pass' and result['source_url'] == SOURCE_URL


def test_attachment_helper_wrong_source_blocks(tmp_path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(security.subprocess, 'run', lambda *a, **k: SimpleNamespace(
        returncode=0, stdout=json.dumps({'status':'pass', 'hresult':0,
            'source_url':'https://example.org/wrong.zip'})))
    assert security.attachment_scan(tmp_path / 'fixture.zip', SOURCE_URL)['status'] == 'fail'


def test_attachment_report_wrong_source_blocks_release(tmp_path):
    report = security.scan_release(archive(tmp_path), source_url=SOURCE_URL,
        status_fn=lambda: {}, scan_fn=lambda _: {'returncode': 0},
        attachment_fn=lambda path, url: {'status': 'pass', 'hresult': 0,
            'archive_sha256': security.digest(path), 'source_url': url + '.different'})
    assert report['status'] == 'fail'


def test_source_url_is_bound_to_scan_report(tmp_path):
    report = scan(archive(tmp_path))
    assert report['status'] == 'pass' and report['schema_version'] == 3
    assert report['source_url'] == report['attachment_check']['source_url'] == SOURCE_URL
