"""Distribution boundaries, not legal or educational certification."""
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import package_skill
import export_public_repo


def test_nested_download_archive_is_not_repackaged():
    assert not package_skill.should_include(ROOT / 'downloads/taiwan-exam-generator.zip')
    assert not package_skill.should_include(ROOT / 'docs/gsat-writing-source-ecology-audit-2026-09-05.md')
    assert not package_skill.should_include(ROOT / 'PACKAGE_MANIFEST.json')
    assert not package_skill.should_include(ROOT / '.env.local')
    assert not package_skill.should_include(ROOT / 'exam_packs/學測/subjects/自然/metadata/source-index.jsonl')


def test_export_never_overwrites_existing_work(tmp_path):
    target = tmp_path / 'work'
    target.mkdir()
    sentinel = target / 'user.txt'
    sentinel.write_text('keep', encoding='utf-8')
    with pytest.raises(ValueError, match='new, nonexistent'):
        export_public_repo.export(target, 'test', internal_review=True)
    assert sentinel.read_text(encoding='utf-8') == 'keep'


def test_maintainer_tools_and_legacy_builders_are_not_distributed():
    for relative in export_public_repo.MAINTAINER_FILES:
        assert not package_skill.should_include(ROOT / relative)
    assert not package_skill.should_include(ROOT / 'scripts/new_unreviewed_builder.py')
    assert not package_skill.should_include(ROOT / 'scripts/build_gsat_stress_suite_116.py')
    assert not package_skill.should_include(ROOT / 'scripts/paginate_chinese_natural.js')
    assert not package_skill.should_include(ROOT / 'scripts/render_chinese_natural_proof.py')


def test_security_hold_blocks_publication(tmp_path):
    import json
    (tmp_path / 'SOFTWARE_RELEASE_STATUS.json').write_text(json.dumps({'status': 'suspended'}))
    with pytest.raises(ValueError, match='suspended'):
        package_skill.require_publication_open(tmp_path)


def test_ready_label_without_resolution_does_not_reopen(tmp_path):
    import json
    (tmp_path / 'SOFTWARE_RELEASE_STATUS.json').write_text(json.dumps({'status': 'ready'}))
    with pytest.raises(ValueError, match='suspended'):
        package_skill.require_publication_open(tmp_path)


def test_missing_security_state_blocks_publication(tmp_path):
    with pytest.raises(FileNotFoundError):
        package_skill.require_publication_open(tmp_path)


def test_source_export_preserves_maintainer_tools_only(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    destination = tmp_path / 'candidate'
    for relative in export_public_repo.MAINTAINER_FILES:
        file = source / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('# benign fixture: ' + relative, encoding='utf-8')
    extra = source / 'scripts/unreviewed.py'
    extra.write_text('# must not export', encoding='utf-8')
    monkeypatch.setattr(export_public_repo, 'ROOT', source)
    export_public_repo.copy_maintainer_files(destination)
    assert {p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()} == set(export_public_repo.MAINTAINER_FILES)
    for relative in export_public_repo.MAINTAINER_FILES:
        assert (destination / relative).read_bytes() == (source / relative).read_bytes()


def test_missing_maintainer_tool_fails_before_copy(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.mkdir()
    destination = tmp_path / 'candidate'
    monkeypatch.setattr(export_public_repo, 'ROOT', source)
    with pytest.raises(ValueError, match='Required maintainer tool'):
        export_public_repo.copy_maintainer_files(destination)
    assert not destination.exists()


def test_maintainer_export_does_not_overwrite_existing_file(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    destination = tmp_path / 'candidate'
    for relative in export_public_repo.MAINTAINER_FILES:
        file = source / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('# benign fixture', encoding='utf-8')
    sentinel = destination / export_public_repo.MAINTAINER_FILES[0]
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text('preserve', encoding='utf-8')
    monkeypatch.setattr(export_public_repo, 'ROOT', source)
    with pytest.raises(ValueError, match='must not overwrite'):
        export_public_repo.copy_maintainer_files(destination)
    assert sentinel.read_text(encoding='utf-8') == 'preserve'
