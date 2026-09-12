import hashlib
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

import sys
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import bootstrap_exam_sources as bootstrap


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_member_policy_accepts_only_exam_source_roots():
    assert bootstrap.allowed_member(bootstrap.PurePosixPath("exam_packs/學測/subjects/社會/歷屆試題/115/paper.pdf"))
    assert bootstrap.allowed_member(bootstrap.PurePosixPath("exam_packs/學測/shared-data/模擬考/bundle/chart.png"))
    assert not bootstrap.allowed_member(bootstrap.PurePosixPath("../paper.pdf"))
    assert not bootstrap.allowed_member(bootstrap.PurePosixPath("scripts/payload.py"))


def test_local_pack_is_extracted_and_verified_without_overwriting(tmp_path, monkeypatch):
    relative = "exam_packs/學測/subjects/社會/歷屆試題/115/paper.pdf"
    content = b"%PDF-1.4\nsource fixture\n%%EOF\n"
    archive = tmp_path / "source.zip"
    with ZipFile(archive, "w", compression=ZIP_STORED) as zipped:
        zipped.writestr(relative, content)
    pack = {
        "id": "fixture",
        "asset": archive.name,
        "download_url": archive.as_uri(),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": bootstrap.sha256_file(archive),
        "files": [{"path": relative, "bytes": len(content), "sha256": digest(content)}],
    }
    install_root = tmp_path / "installed"
    monkeypatch.setattr(bootstrap, "ROOT", install_root)
    assert bootstrap.install_pack(pack, tmp_path / "cache", verify_only=False) == (1, 0)
    assert bootstrap.install_pack(pack, tmp_path / "cache", verify_only=True) == (1, 0)
    assert (install_root / Path(*bootstrap.PurePosixPath(relative).parts)).read_bytes() == content


@pytest.fixture
def source_pack(tmp_path, monkeypatch):
    relative = 'exam_packs/學測/subjects/自然/歷屆試題/115/paper.pdf'
    content = b'source-data'
    archive = tmp_path / 'fixture.zip'
    with ZipFile(archive, 'w') as z:
        z.writestr(relative, content)
    pack = {'id': 'fixture', 'asset': archive.name, 'download_url': archive.as_uri(),
            'archive_bytes': archive.stat().st_size, 'archive_sha256': digest(archive.read_bytes()),
            'files': [{'path': relative, 'bytes': len(content), 'sha256': digest(content)}]}
    root = tmp_path / 'installed'
    monkeypatch.setattr(bootstrap, 'ROOT', root)
    return pack, root / relative, archive, tmp_path / 'cache'


def test_conflicting_user_source_is_preserved_before_download(source_pack, monkeypatch):
    pack, target, _, cache = source_pack
    target.parent.mkdir(parents=True)
    target.write_bytes(b'private user original')
    monkeypatch.setattr(bootstrap, 'download', lambda *a: pytest.fail('must detect conflicts before downloading'))
    assert bootstrap.install_pack(pack, cache, verify_only=True) == (0, 1)
    with pytest.raises(ValueError, match='preserved'):
        bootstrap.install_pack(pack, cache, verify_only=False)
    assert target.read_bytes() == b'private user original'


@pytest.mark.parametrize('name', ['../outside.pdf', '/absolute.pdf', 'scripts/payload.py',
                                  'exam_packs/學測/subjects/自然/歷屆試題/a.pdf:payload',
                                  'exam_packs/學測/subjects/自然/歷屆試題/../paper.pdf'])
def test_verify_only_rejects_unsafe_manifest_paths(source_pack, name):
    pack, _, _, cache = source_pack
    pack['files'][0]['path'] = name
    with pytest.raises(ValueError, match='Unsafe'):
        bootstrap.install_pack(pack, cache, verify_only=True)


def test_duplicate_archive_members_are_rejected(source_pack):
    pack, target, archive, cache = source_pack
    with pytest.warns(UserWarning, match='Duplicate'):
        with ZipFile(archive, 'a') as z:
            z.writestr(pack['files'][0]['path'], b'source-data')
    pack.update(archive_bytes=archive.stat().st_size, archive_sha256=digest(archive.read_bytes()))
    with pytest.raises(ValueError, match='Duplicate archive'):
        bootstrap.install_pack(pack, cache, verify_only=False)
    assert not target.exists()


def test_bad_member_hash_leaves_no_staging_file(source_pack):
    pack, target, _, cache = source_pack
    pack['files'][0]['sha256'] = 'a' * 64
    with pytest.raises(ValueError, match='verification failed'):
        bootstrap.install_pack(pack, cache, verify_only=False)
    assert not target.exists()
    assert not list(target.parent.glob('.source-*.part'))


def test_concurrent_source_creation_is_not_overwritten(source_pack, monkeypatch):
    pack, target, _, cache = source_pack
    link = bootstrap.os.link
    def concurrent_create(source, destination):
        target.write_bytes(b'concurrent user file')
        link(source, destination)
    monkeypatch.setattr(bootstrap.os, 'link', concurrent_create)
    with pytest.raises(ValueError, match='preserved'):
        bootstrap.install_pack(pack, cache, verify_only=False)
    assert target.read_bytes() == b'concurrent user file'
    assert not list(target.parent.glob('.source-*.part'))


def test_invalid_manifest_is_actionable_and_does_not_raise(tmp_path, capsys):
    manifest = tmp_path / 'manifest.json'
    manifest.write_text('{broken', encoding='utf-8')
    assert bootstrap.main(['--all', '--manifest', str(manifest)]) == 2
    assert 'invalid-manifest' in capsys.readouterr().err


def test_case_collisions_fail_before_any_write(source_pack):
    pack, target, _, cache = source_pack
    other = dict(pack['files'][0])
    other['path'] = other['path'].replace('paper.pdf', 'PAPER.pdf')
    pack['files'].append(other)
    with pytest.raises(ValueError, match='case-insensitive'):
        bootstrap.install_pack(pack, cache, verify_only=True)
    assert not target.exists()
