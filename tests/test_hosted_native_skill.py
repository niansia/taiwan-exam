"""Native packaging must be progressive, complete, deterministic and unapproved."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import pymupdf
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_hosted_skill as builder
from scan_skill_release import inspect_archive
from validate_attribution import validate
from read_web_knowledge import LAYOUT_SLUGS, TEMPLATE_SLUGS, reading_plan_from_directory


def test_native_candidate_is_small_entry_with_real_separate_dependencies(tmp_path):
    report = builder.build('test-native', tmp_path / 'native.zip')
    assert report['entry_bytes'] < 5000
    assert report['distribution_status'] == 'internal-review-not-published'
    assert report['security_acceptance'] == 'not-performed-by-builder'
    extracted = tmp_path / 'skill'
    inspect_archive(Path(report['archive']), extracted)  # Existing security manifest/path validator.
    assert validate(extracted)['status'] == 'pass'
    entry = (extracted / 'SKILL.md').read_text(encoding='utf-8')
    metadata = yaml.safe_load(entry.split('---', 2)[1])
    assert metadata['name'] == 'taiwan-exam-generator' and metadata['description']
    assert len(entry.splitlines()) < 100 and '<canonical-source' not in entry
    assert (extracted / 'references/full-skill.md').read_bytes() == (builder.ROOT / 'SKILL.md').read_bytes()
    assert (extracted / 'references/hosted-execution.md').is_file()
    assert len(list(extracted.rglob('*.pdf'))) == 23 + 14  # Fixed templates and layout previews only.
    assert not list(extracted.rglob('taiwan-exam-web-knowledge.md'))
    scripts = {p.stem for p in (extracted / 'scripts').glob('*.py')}
    for path in (extracted / 'scripts').glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node, ast.ImportFrom) and node.module:
                stem = node.module.split('.')[0]
                if (builder.ROOT / 'scripts' / (stem + '.py')).is_file():
                    assert stem in scripts, (path.name, stem)
    for name in ('LICENSE', 'NOTICE', 'ORIGIN.json'):
        assert (extracted / name).read_bytes() == (builder.ROOT / name).read_bytes()


def test_native_candidate_build_is_deterministic_and_cannot_overwrite(tmp_path):
    one = builder.build('test-stable', tmp_path / 'one.zip')
    two = builder.build('test-stable', tmp_path / 'two.zip')
    assert one['sha256'] == two['sha256']
    with pytest.raises(ValueError, match='never overwrite'):
        builder.build('test-stable', tmp_path / 'one.zip')
    with pytest.raises(ValueError, match='version identifier'):
        builder.build('../bad\nname: altered', tmp_path / 'bad.zip')
    with ZipFile(one['archive']) as zipped:
        manifest = json.loads(zipped.read('taiwan-exam-generator/PACKAGE_MANIFEST.json'))
        assert manifest['contains_original_exam_files'] is False
        assert manifest['browser_acceptance'] == 'not-performed-by-builder'


@pytest.mark.parametrize('subject', ['國綜', '英文', '數學A', '數學B', '自然', '社會', '國寫'])
def test_native_helpers_execute_without_aggregate_bootstrap(tmp_path, subject):
    archive = tmp_path / 'runtime.zip'
    builder.build('test-runtime', archive)
    skill = tmp_path / 'skill'
    inspect_archive(archive, skill)
    runtime = tmp_path / 'references'
    reading_plan_from_directory(skill, subject, runtime)
    font = tmp_path / 'body.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    # Only the chosen subject's templates and previews are copied; templates need no network.
    slug = TEMPLATE_SLUGS[subject]
    previews = {f'layout-previews/{LAYOUT_SLUGS[subject]}-{role}.pdf' for role in ('questions', 'solutions')}
    copied = {p.relative_to(runtime).as_posix() for p in runtime.rglob('*.pdf')}
    assert previews < copied and all(p in previews or p.startswith(f'exam_packs/學測/templates/115/assets/{slug}/')
                                     for p in copied)
    command = [sys.executable, str(runtime / 'scripts/prepare_hosted_run.py'),
               '--subject', subject, '--run-dir', str(tmp_path / 'run'), '--paper-id', 'native',
               '--font', str(font)]
    unreachable = 'http://127.0.0.1:9'
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, timeout=45,
                            env=dict(os.environ, PYTHONIOENCODING='utf-8', HTTP_PROXY=unreachable,
                                     HTTPS_PROXY=unreachable, http_proxy=unreachable,
                                     https_proxy=unreachable, NO_PROXY='', no_proxy=''))
    assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
    prepared = json.loads(result.stdout)
    assert prepared['status'] == 'ready-for-authoring'
    assert prepared['template_source'] == 'bundled-with-skill'
    assert prepared['original_pdf_required'] is False
