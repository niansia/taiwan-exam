"""Native installs use a small entry, exact separate sources and closed imports."""
import ast
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import pytest
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_hosted_skill import build, archive_path, validate_member_path
from build_web_knowledge import source_paths
from package_skill import should_include
from fetch_hosted_template_assets import production_records


@pytest.fixture(scope='module')
def native(tmp_path_factory):
    directory=tmp_path_factory.mktemp('hosted-package')
    archive=directory/'candidate.zip'
    result=build('package-test',archive)
    with ZipFile(archive) as zipped:
        zipped.extractall(directory/'installed')
    return directory,archive,result,directory/'installed/taiwan-exam-generator'


def test_short_entry_is_separate_from_exact_canonical_sources(native):
    _,archive,result,installed=native
    entry=(installed/'SKILL.md').read_bytes()
    assert entry.startswith(b'---\n') and len(entry)<5000
    metadata=yaml.safe_load(entry.decode('utf-8').split('---\n',2)[1])
    assert metadata['name']=='taiwan-exam-generator'
    assert 0<len(metadata['description'])<=200
    assert b'references/hosted-execution.md' in entry
    assert b'not an\ninitial reading requirement' in entry
    assert (installed/'references/full-skill.md').read_bytes()==(ROOT/'SKILL.md').read_bytes()
    for source in source_paths():
        relative=source.relative_to(ROOT)
        destination='references/full-skill.md' if relative.as_posix()=='SKILL.md' else relative
        assert (installed/archive_path(str(destination).replace('\\', '/'))).read_bytes()==source.read_bytes()
    with ZipFile(archive) as zipped:
        names=zipped.namelist()
        assert len(names)==len(set(names))
        # Regresses Claude's "Zip file contains path with invalid characters":
        # every member, including non-selected/legacy subjects, must be portable.
        assert all(re.fullmatch(r'[A-Za-z0-9_./-]+', name) for name in names)
        assert not any('/./' in name or '/../' in name or '//' in name for name in names)
        assert all(name.startswith('taiwan-exam-generator/') for name in names)
        assert not any(name.endswith('.zip') or '/web/' in name or '/docs/' in name for name in names)
        assert not any('build_hosted_skill.py' in name or 'build_web_knowledge.py' in name for name in names)
    assert result['entry_bytes']==len(entry)
    assert result['security_acceptance']=='not-performed-by-builder'
    manifest=json.loads((installed/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['file_count']==len(manifest['files'])
    assert manifest['contains_original_exam_files'] is False
    # The only binaries are the fixed templates, byte-identical to their map.
    mapping=json.loads((ROOT/manifest['bundled_templates']['map']).read_text(encoding='utf-8-sig'))
    expected={a['repository_path']:a['sha256'] for s in mapping['subjects'] for a in production_records(s)}
    pdfs={row['runtime_path']:row for row in manifest['files'] if row['path'].endswith('.pdf')}
    templates={path:row['sha256'] for path,row in pdfs.items() if not path.startswith('layout-previews/')}
    assert templates==expected and manifest['bundled_templates']['count']==len(expected)==23
    # Layout previews: each subject's pair, traceable to the published preview bytes.
    previews=[row for path,row in pdfs.items() if path.startswith('layout-previews/')]
    assert len(previews)==manifest['layout_previews']['count']==14
    for row in previews:
        assert hashlib.sha256((ROOT/row['source']).read_bytes()).hexdigest()==row['source_sha256']
    for row in manifest['files']:
        data=(installed/row['path']).read_bytes()
        assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']


@pytest.mark.parametrize('path', ['exam_packs/學測/manifest.json',
                                 'exam_packs/學測/subjects/數學（舊制）/subject.json',
                                 '../outside.py', '/absolute.py', 'a//b.py',
                                 'a/./b.py', 'a\\b.py', 'drive:c.py', 'a\x00b.py'])
def test_archive_writer_rejects_nonportable_members(path):
    with pytest.raises(ValueError, match='Non-portable'):
        validate_member_path(path)


def test_native_archive_is_deterministic_and_does_not_overwrite(native):
    directory,archive,_,_=native
    second=directory/'same-inputs.zip'
    build('package-test',second)
    assert archive.read_bytes()==second.read_bytes()
    original=archive.read_bytes()
    with pytest.raises(ValueError,match='never overwrite'):
        build('package-test',archive)
    assert archive.read_bytes()==original


def test_hosted_and_local_distribution_contain_runtime_import_closure(native):
    *_,installed=native
    sources={p.stem:p for p in source_paths() if p.parent==ROOT/'scripts'}
    assert 'run_hosted_workflow' in sources
    assert should_include(ROOT/'references/hosted-execution.md')
    for module,path in sources.items():
        assert should_include(path), module
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            names=([node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module
                   else [item.name.split('.')[0] for item in node.names] if isinstance(node,ast.Import) else [])
            for name in names:
                if (ROOT/'scripts'/(name+'.py')).is_file():
                    assert name in sources, f'{module} imports missing local helper {name}'
                    assert (installed/'scripts'/(name+'.py')).is_file()
    for name in ('build_hosted_skill.py','build_web_knowledge.py','build_hosted_layout_examples.py'):
        assert not should_include(ROOT/'scripts'/name)


@pytest.mark.parametrize('helper',['run_hosted_workflow.py','prepare_hosted_run.py',
                                    'check_hosted_run.py','hosted_body_templates.py'])
def test_native_helpers_start_outside_repository(native,tmp_path,helper):
    *_,installed=native
    result=subprocess.run([sys.executable,str(installed/'scripts'/helper),'--help'],
                          cwd=tmp_path,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize('name', [
    'references/math-difficulty-design.md#math-a-unpredictable-answer-counts-and-occasional-close-options',
    'references/notes?draft.md',
    'scripts/tmp|copy.py',
    'exam_packs/學測/scratch<1>.json',
])
def test_unportable_filenames_never_enter_a_distribution(name):
    """A scratch copy named with a URL fragment or wildcard is not a source.

    One such leftover sat beside references/math-difficulty-design.md; the
    hosted builder skipped it only because it packages from an allowlist.
    """
    assert not should_include(ROOT / name)


def test_the_exclusion_does_not_reach_real_sources():
    for name in ('LICENSE', 'NOTICE', 'SKILL.md',
                 'references/math-difficulty-design.md',
                 'exam_packs/學測/manifest.json'):
        assert should_include(ROOT / name), name
