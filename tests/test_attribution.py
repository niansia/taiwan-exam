import json
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import package_skill
from validate_attribution import validate


@pytest.fixture
def project(tmp_path):
    for relative in ["ORIGIN.json", "NOTICE", "AGENTS.md", "SKILL.md", "references/attribution-and-forks.md"]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    # Keep negative fixtures pending regardless of the real project's license.
    path = tmp_path / 'ORIGIN.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['licensing'].update(status='pending-owner-confirmation', spdx_id=None,
                             copyright_holders=[])
    path.write_text(json.dumps(data), encoding='utf-8')
    return tmp_path


def test_owner_confirmed_mit_declarations_pass(project):
    path = project / 'ORIGIN.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['upstream']['repository_url'] = 'https://github.com/example/example'
    data['licensing'].update(status='owner-confirmed', spdx_id='MIT',
                             copyright_holders=['Example test holder'])
    path.write_text(json.dumps(data), encoding='utf-8')
    (project / 'LICENSE').write_text('Fixture license declaration', encoding='utf-8')
    assert validate(project, public_release=True)['status'] == 'pass'


def change_origin(project, change):
    path = project / "ORIGIN.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_internal_package_allows_pending_license_without_claiming_approval(project):
    report = validate(project)
    assert report["status"] == "pass"
    assert report["warnings"]
    assert report["legal_or_exam_approval"] is False
    assert validate(project, public_release=True)["status"] == "fail"


def test_honestly_attributed_rename_passes(project):
    change_origin(project, lambda data: data["distribution"].update(
        name="Example Learning", is_derivative=True, changes=["Renamed interface labels; preserved upstream attribution."]))
    assert validate(project)["status"] == "pass"


def test_unacknowledged_rename_fails(project):
    change_origin(project, lambda data: data["distribution"].update(name="Example Learning"))
    assert validate(project)["status"] == "fail"


def test_origin_replacement_fails(project):
    change_origin(project, lambda data: data["upstream"].update(name="Example Learning", project_id="example-learning"))
    assert validate(project)["status"] == "fail"


def test_notice_global_replacement_fails(project):
    notice = project / "NOTICE"
    notice.write_text(notice.read_text().replace("Taiwan Exam", "Example Learning"))
    assert validate(project)["status"] == "fail"


def test_malformed_origin_fails_cleanly(project):
    (project / "ORIGIN.json").write_text("null")
    assert validate(project)["status"] == "fail"


def test_missing_notice_stops_packaging_before_touching_output(project, monkeypatch):
    (project / "NOTICE").unlink()
    archive = project / "keep.zip"
    archive.write_bytes(b"existing-user-file")
    monkeypatch.setattr(package_skill, "ROOT", project)
    monkeypatch.setattr(sys, "argv", ["package_skill.py", "--output", str(archive)])
    assert package_skill.main() == 2
    assert archive.read_bytes() == b"existing-user-file"


def test_packager_keeps_notices_and_reports_limited_scope(project, monkeypatch):
    archive = project / "dist" / "preview.zip"
    monkeypatch.setattr(package_skill, "ROOT", project)
    monkeypatch.setattr(sys, "argv", ["package_skill.py", "--output", str(archive)])
    assert package_skill.main() == 0
    with ZipFile(archive) as zipped:
        prefix = "taiwan-exam-generator/"
        assert zipped.read(prefix + "NOTICE") == (project / "NOTICE").read_bytes()
        assert zipped.read(prefix + "ORIGIN.json") == (project / "ORIGIN.json").read_bytes()
        manifest = json.loads(zipped.read(prefix + "PACKAGE_MANIFEST.json"))
        assert manifest["distribution_status"] == "internal-review"
        assert manifest["origin"]["upstream"]["name"] == "Taiwan Exam"
        assert manifest["exam_acceptance"] == "not-established-by-packager"


def test_public_release_is_not_silently_enabled(project, monkeypatch):
    archive = project / "dist" / "release.zip"
    monkeypatch.setattr(package_skill, "ROOT", project)
    monkeypatch.setattr(sys, "argv", ["package_skill.py", "--public-release", "--output", str(archive)])
    assert package_skill.main() == 2
    assert not archive.exists()
