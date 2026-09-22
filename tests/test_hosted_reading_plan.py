import json
import hashlib
from pathlib import Path
import re
import sys
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from read_web_knowledge import (LAYOUT_SLUGS, reading_plan, sections, pointer_value,
                                reading_plan_from_directory, READING_CHUNK_LIMIT, READING_CONTENT_MARKER)
import build_web_knowledge


@pytest.fixture(scope='module')
def knowledge(tmp_path_factory):
    path = tmp_path_factory.mktemp('knowledge') / 'knowledge.md'
    # Build from current canonical sources rather than silently testing the
    # previous published bundle while these instructions are being edited.
    path.write_bytes(build_web_knowledge.build('reading-plan-test').encode('utf-8'))
    return path


@pytest.fixture(scope='module')
def native_skill(tmp_path_factory):
    from build_hosted_skill import build
    directory = tmp_path_factory.mktemp('native-skill')
    archive = directory / 'candidate.zip'
    build('reading-plan-test', archive)
    with ZipFile(archive) as zipped:
        zipped.extractall(directory / 'installed')
    return directory / 'installed/taiwan-exam-generator'


def read_chunks(folder,result):
    manifest=json.loads((folder/result['reading_manifest']).read_text(encoding='utf-8'))
    full={}
    for phase,record in manifest['phases'].items():
        index=(folder/record['index']).read_text(encoding='utf-8')
        assert len(index)<=READING_CHUNK_LIMIT
        pieces=[];position=0
        for ordinal,chunk in enumerate(record['chunks'],1):
            text=(folder/chunk['path']).read_text(encoding='utf-8')
            assert len(text)==chunk['characters']<=READING_CHUNK_LIMIT
            assert f'{ordinal}/{len(record["chunks"])}' in text
            assert Path(chunk['path']).name in index
            payload=text.split(READING_CONTENT_MARKER,1)[1]
            assert chunk['content_start']==position
            position+=len(payload)
            assert chunk['content_end']==position
            assert hashlib.sha256(payload.encode()).hexdigest()==chunk['content_sha256']
            pieces.append(payload)
        content=''.join(pieces)
        assert len(content)==record['content_characters']
        assert hashlib.sha256(content.encode()).hexdigest()==record['content_sha256']
        for source in record['embedded_sources']:
            match=re.search(r'<reading-source path="'+re.escape(source)+r'">\n(.*?)</reading-source>',content,re.S)
            assert match,source
            canonical=(folder/source).read_text(encoding='utf-8-sig').replace('\r\n','\n').replace('\r','\n').rstrip()+'\n'
            assert match.group(1)==canonical
            assert hashlib.sha256(canonical.encode()).hexdigest()==manifest['embedded_sources'][source]['embedded_sha256']
            assert source in index  # Explicitly says this source is already embedded in full.
        full[phase]=content
    return manifest,full


@pytest.mark.parametrize('subject', LAYOUT_SLUGS)
def test_reading_plan_is_scoped_lossless_and_references_json_only(subject,tmp_path,knowledge):
    result=reading_plan(knowledge,subject,tmp_path)
    entries=sections(knowledge.read_text(encoding='utf-8'))
    manifest,full=read_chunks(tmp_path,result)
    assert result['selected_record_bytes']==0
    assert 'SKILL.md' not in manifest['embedded_sources']
    assert 'references/hosted-execution.md' in manifest['embedded_sources']
    assert 'references/pack-and-release-verification.md' not in manifest['embedded_sources']
    assert all(not path.endswith('.json') for path in manifest['embedded_sources'])
    for reference in manifest['json_references']:
        record,raw=entries[reference['canonical_source']]
        assert reference['embedded_sha256']==record['embedded_sha256']
        for pointer in reference['json_pointers']:
            value=pointer_value(json.loads(raw),pointer)
            assert pointer or reference['canonical_source'].endswith('.json')
            if isinstance(value,(dict,list)) and len(json.dumps(value))>1000:
                assert json.dumps(value,ensure_ascii=False,separators=(',',':')) not in ''.join(full.values())
        assert (tmp_path/reference['canonical_source']).read_bytes()==raw
    authoring=''.join(full['authoring'])
    assert 'schemas/exam.schema.json' in authoring and 'schemas/answer.schema.json' in authoring
    assert 'schemas/question.schema.json' not in authoring
    assert 'references/difficulty-field-contract.md' in authoring
    assert '/curricula/99' not in authoring
    assert f'templates/hosted-{LAYOUT_SLUGS[subject]}-questions.json' in full['layout']
    assert (tmp_path/'scripts/check_hosted_run.py').read_bytes()==entries['scripts/check_hosted_run.py'][1]
    for ref in manifest['json_references']:
        if ref['canonical_source'].endswith('writer-blueprint.json'):
            raw=json.loads(entries[ref['canonical_source']][1])
            for pointer in ref['json_pointers']:
                if pointer.startswith('/aggregate_pattern_clusters/'):
                    value=pointer_value(raw,pointer)
                    assert value['pattern']['curriculum']=='108'
                    if subject in {'國綜','國寫'}:assert value['pattern']['section'].startswith(subject)
        if ref['canonical_source'].endswith('difficulty-profile.json'):
            assert subject!='國寫' and '/curricula/108' in ref['json_pointers']
    assert reading_plan(knowledge,subject,tmp_path)==result


def test_reading_plan_preserves_changed_views(tmp_path, knowledge):
    reading_plan(knowledge, '數學A', tmp_path)
    view = tmp_path / 'reading/preflight.md'
    view.write_text('user notes', encoding='utf-8')
    with pytest.raises(ValueError, match='Preserve existing reading view'):
        reading_plan(knowledge, '數學A', tmp_path)
    assert view.read_text(encoding='utf-8') == 'user notes'


@pytest.mark.parametrize('subject', LAYOUT_SLUGS)
def test_native_skill_reads_without_aggregate_and_preserves_runtime(subject, tmp_path, native_skill):
    result = reading_plan_from_directory(native_skill, subject, tmp_path)
    read_chunks(tmp_path,result)
    assert not (native_skill / 'taiwan-exam-web-knowledge.md').exists()
    manifest=json.loads((native_skill/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    from hosted_bundles import expand
    files={str(p.relative_to(native_skill)).replace('\\','/'):p.read_bytes()
           for p in native_skill.rglob('*') if p.is_file() and p.name!='PACKAGE_MANIFEST.json'}
    files=expand(files,manifest)
    for row in manifest['files']:
        path=row.get('runtime_path', row['path'])
        if (tmp_path/path).is_file():
            assert (tmp_path/path).read_bytes() == files[row['path']]
    assert (tmp_path/'exam_packs/學測/metadata/official-current-web-sources.json').is_file()
    assert not (native_skill/'exam_packs/學測').exists()
    assert reading_plan_from_directory(native_skill, subject, tmp_path) == result


@pytest.mark.parametrize('runtime_path', ['../outside.json', '/absolute.json',
                                        'C:/outside.json', 'a\\b.json', 'a//b.json'])
def test_native_reader_rejects_unsafe_runtime_alias_before_writing(tmp_path, runtime_path):
    source=tmp_path/'source'
    source.mkdir()
    (source/'PACKAGE_MANIFEST.json').write_text(json.dumps({'files': [
        {'path': 'resources/canonical/record.json', 'runtime_path': runtime_path}
    ]}), encoding='utf-8')
    output=tmp_path/'runtime'
    with pytest.raises(ValueError, match='Unsafe or duplicate package path'):
        reading_plan_from_directory(source, '數學A', output)
    assert not output.exists()


def test_native_reader_rejects_changed_mapped_data_before_writing(tmp_path, native_skill):
    manifest=json.loads((native_skill/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    row=next(row for row in manifest['files']
             if row.get('runtime_path')=='exam_packs/學測/metadata/official-current-web-sources.json')
    row={k:v for k,v in row.items() if k!='bundle'}  # a loose copy: the digest check is the same either way
    source=tmp_path/'tampered'
    file=source/row['path']
    file.parent.mkdir(parents=True)
    file.write_bytes(b'{"changed": true}')
    (source/'PACKAGE_MANIFEST.json').write_text(json.dumps({'files': [row]}), encoding='utf-8')
    with pytest.raises(ValueError, match='Package checksum mismatch'):
        reading_plan_from_directory(source, '數學A', tmp_path/'runtime')
    assert not (tmp_path/'runtime').exists()


def test_native_reader_rejects_colliding_aliases_even_for_unselected_subject(tmp_path):
    source=tmp_path/'source'
    source.mkdir()
    (source/'PACKAGE_MANIFEST.json').write_text(json.dumps({'files': [
        {'path': 'resources/a.json', 'runtime_path': 'exam_packs/會考/test.json'},
        {'path': 'resources/b.json', 'runtime_path': 'exam_packs/會考/TEST.json'}
    ]}), encoding='utf-8')
    with pytest.raises(ValueError, match='Unsafe or duplicate package path'):
        reading_plan_from_directory(source, '數學A', tmp_path/'runtime')
    assert not (tmp_path/'runtime').exists()


def test_native_reader_rejects_changed_manifest_bound_helper(tmp_path, native_skill):
    # A small package copy suffices to prove the mismatch is found before any
    # files are installed; the real package fixture covers complete positive runs.
    source = tmp_path / 'bad-package'
    source.mkdir()
    manifest = json.loads((native_skill / 'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
    row = next(row for row in manifest['files'] if row['path'] == 'scripts/check_hosted_run.py')
    (source / 'PACKAGE_MANIFEST.json').write_bytes(json.dumps({'files': [row]}).encode('utf-8'))
    script = source / row['path']
    script.parent.mkdir()
    script.write_bytes(b'print("changed")\n')
    output = tmp_path / 'runtime'
    with pytest.raises(ValueError, match='Package checksum mismatch'):
        reading_plan_from_directory(source, '數學A', output)
    assert not output.exists()
