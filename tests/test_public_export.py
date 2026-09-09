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


def test_only_reviewed_exporter_and_no_legacy_builders_are_distributed():
    assert package_skill.should_include(ROOT / 'scripts/export_public_repo.py')
    assert not package_skill.should_include(ROOT / 'scripts/new_unreviewed_builder.py')
    assert not package_skill.should_include(ROOT / 'scripts/build_gsat_stress_suite_116.py')
