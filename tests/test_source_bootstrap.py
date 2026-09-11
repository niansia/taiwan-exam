import hashlib
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

import sys


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
