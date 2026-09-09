import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import scan_skill_release as security


def archive(tmp_path, name='SKILL.md', tamper=False):
    path = tmp_path / 'test.zip'
    body = b'fixture'
    record = {'path': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    with ZipFile(path, 'w') as zipped:
        zipped.writestr('taiwan-exam-generator/' + name, b'changed' if tamper else body)
        zipped.writestr('taiwan-exam-generator/PACKAGE_MANIFEST.json', json.dumps({'files': [record]}))
    return path


def scan(path, callback=lambda _: {'returncode': 0, 'output': 'fixture scan'}):
    return security.scan_release(path, status_fn=lambda: {'fixture': True}, scan_fn=callback,
        attachment_fn=lambda path: {'status': 'pass', 'hresult': 0, 'archive_sha256': security.digest(path)})


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
    report = security.scan_release(archive(tmp_path), status_fn=lambda: {},
        scan_fn=lambda _: {'returncode': 0, 'output': 'clean'},
        attachment_fn=lambda _: {'status': 'fail', 'hresult': -2147024671})
    assert report['status'] == 'fail'


def test_attachment_hash_mismatch_blocks(tmp_path):
    report = security.scan_release(archive(tmp_path), status_fn=lambda: {},
        scan_fn=lambda _: {'returncode': 0, 'output': 'clean'},
        attachment_fn=lambda _: {'status': 'pass', 'hresult': 0, 'archive_sha256': '0' * 64})
    assert report['status'] == 'fail'
