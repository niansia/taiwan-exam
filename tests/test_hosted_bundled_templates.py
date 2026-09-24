"""Formal PDFs compose on bundled fixed templates; a template gap stops instead of redrawing."""
import io
import json
from pathlib import Path
import shutil
import socket
import sys

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_hosted_skill as builder
import prepare_hosted_run as preflight
from fetch_hosted_template_assets import DEFAULT_MAP, production_records
from read_web_knowledge import TEMPLATE_SLUGS, reading_plan_from_directory
from scan_skill_release import inspect_archive

ROOT = Path(__file__).resolve().parents[1]
MAPPING = json.loads(DEFAULT_MAP.read_text(encoding='utf-8-sig'))


def forbid_network(*args, **kwargs):
    raise AssertionError('Bundled templates must not need a network connection')


@pytest.fixture
def font(tmp_path):
    path = tmp_path / 'font.ttf'
    path.write_bytes(pymupdf.Font('cjk').buffer)
    return path


def test_reader_template_slugs_match_the_map():
    assert TEMPLATE_SLUGS == {row['subject']: row['slug'] for row in MAPPING['subjects']}


def test_prepare_uses_bundled_templates_without_network(tmp_path, font, monkeypatch):
    monkeypatch.setattr(socket.socket, 'connect', forbid_network)
    report = preflight.prepare('數學A', tmp_path / 'run', 'bundled', font)
    assert report['status'] == 'ready-for-authoring', report
    assert report['template_source'] == 'bundled-with-skill'


def test_damaged_bundled_template_stops_without_download_or_redraw(tmp_path, font, monkeypatch):
    monkeypatch.setattr(socket.socket, 'connect', forbid_network)
    records = production_records(next(row for row in MAPPING['subjects'] if row['subject'] == '數學A'))
    for record in records:
        copy = tmp_path / 'bundle' / record['repository_path']
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / record['repository_path'], copy)
    damaged = tmp_path / 'bundle' / records[0]['repository_path']
    data = damaged.read_bytes()
    damaged.write_bytes(data[:-1] + bytes([data[-1] ^ 0xFF]))
    monkeypatch.setattr(preflight, 'bundled_root', lambda subject: tmp_path / 'bundle')
    report = preflight.prepare('數學A', tmp_path / 'run', 'damaged', font)
    assert report['status'] == 'pending'
    assert 'SHA-256 mismatch' in report['errors'][0]
    assert report['next_action'] == preflight.TEMPLATE_GAP_ACTION
    assert 'never typeset or redraw' in report['next_action']
    assert 'taiwan-exam-template-resources.pdf' in report['next_action']


def test_subject_previews_ship_in_the_skill_and_render_like_the_published_ones(tmp_path):
    archive = builder.build('preview-test', tmp_path / 'skill.zip')['archive']
    inspect_archive(Path(archive), tmp_path / 'skill')
    plan = reading_plan_from_directory(tmp_path / 'skill', '英文', tmp_path / 'refs')
    assert [Path(path).name for path in plan['layout_previews']] == ['english-questions.pdf', 'english-solutions.pdf']
    # The entry already sent the model through hosted-execution.md; no second reading.
    assert 'skip these chunks' in plan['first_read_note']
    for path in plan['layout_previews']:
        published = ROOT / 'docs/layout-examples' / builder.PREVIEW_VERSION / Path(path).name
        with pymupdf.open(path) as bundled, pymupdf.open(published) as original:
            assert bundled.page_count == original.page_count
            for mine, theirs in zip(bundled, original):
                assert mine.get_text() == theirs.get_text()
                assert (mine.get_pixmap(matrix=pymupdf.Matrix(2, 2)).samples ==
                        theirs.get_pixmap(matrix=pymupdf.Matrix(2, 2)).samples)


def test_without_a_chinese_font_the_preflight_uses_the_builtin_one(tmp_path, monkeypatch):
    monkeypatch.setattr(socket.socket, 'connect', forbid_network)
    report = preflight.prepare('數學A', tmp_path / 'run', 'no-font', None)
    assert report['status'] == 'ready-for-authoring', report
    assert report['body_font']['source'] == preflight.BUILTIN_FONT
    assert (tmp_path / 'run' / report['body_font']['path']).read_bytes() == pymupdf.Font('cjk').buffer
    # A ChatGPT run ended its response right after preflight to "tell the user"
    # about the font; on hosted surfaces a message to the user ends the turn.
    assert report['next_action'].startswith('Continue in this same response')
    for text in (report['next_action'], report['body_font']['style']):
        assert 'tell the user' not in text and 'delivery message' in text


def cjk_face(label):
    """One CJK font whose own names claim a regional form."""
    ttLib = pytest.importorskip('fontTools.ttLib')
    font = ttLib.TTFont(io.BytesIO(pymupdf.Font('cjk').buffer))
    for record in font['name'].names:
        if record.nameID in (1, 4, 6):
            record.string = label.encode('utf-16-be') if record.platformID == 3 else label.encode('latin-1')
    return font


def test_a_font_collection_uses_its_traditional_chinese_face(tmp_path):
    collection = pytest.importorskip('fontTools.ttLib').TTCollection()
    # Hosted images ship Noto CJK this way, with the Japanese face first.
    collection.fonts = [cjk_face('Test Serif CJK JP'), cjk_face('Test Serif CJK TC')]
    path = tmp_path / 'test-cjk.ttc'
    collection.save(str(path))
    report = preflight.prepare('數學A', tmp_path / 'run', 'collection', path)
    assert report['status'] == 'ready-for-authoring', report
    font = report['body_font']
    assert font['source'] == 'supplied-collection-face' and font['face'].startswith('Test Serif CJK TC')
    assert 'regional_form_note' not in font
    assert preflight.sfnt_names(Path(font['path']).read_bytes())[0] == 'Test Serif CJK TC'
    assert pymupdf.Font(fontfile=font['path']).has_glyph(ord('學'))


def test_a_japanese_face_still_runs_but_its_glyph_forms_are_disclosed(tmp_path):
    path = tmp_path / 'jp.ttf'
    cjk_face('Test Serif CJK JP').save(str(path))
    report = preflight.prepare('國綜', tmp_path / 'run', 'jp-face', path)
    assert report['status'] == 'ready-for-authoring', report
    assert report['body_font']['source'] == 'supplied'
    assert 'JP glyph forms' in report['body_font']['regional_form_note']


def test_a_font_missing_field_glyphs_is_replaced_and_the_reason_recorded(tmp_path):
    latin = tmp_path / 'latin.ttf'
    latin.write_bytes(pymupdf.Font('tiro').buffer)  # no CJK glyphs, like a default system font
    report = preflight.prepare('國綜', tmp_path / 'run', 'latin', latin)
    assert report['status'] == 'ready-for-authoring', report
    assert report['body_font']['source'] == preflight.BUILTIN_FONT
    assert 'latin.ttf lacks' in report['body_font']['replaced']


def test_later_commands_default_to_the_recorded_body_font(tmp_path, font):
    import run_hosted_workflow as workflow
    run = tmp_path / 'run'
    assert preflight.prepare('英文', run, 'recorded', None)['status'] == 'ready-for-authoring'
    assert workflow.recorded_font(run / 'run-state.json') == (run / 'fonts' / 'builtin-cjk.ttf').resolve()
    supplied = tmp_path / 'other-run'
    assert preflight.prepare('英文', supplied, 'supplied', font)['body_font']['source'] == 'supplied'
    assert workflow.recorded_font(supplied / 'run-state.json') == font.resolve()


def test_entry_forbids_redrawn_templates_and_requires_the_final_check():
    entry = builder.ENTRY.format(version='test')
    for phrase in ('Never typeset, trace or redraw', 'check_hosted_run.py', 'bundled original fixed template'):
        assert phrase in entry


def test_entry_and_route_keep_working_until_delivery():
    entry = ' '.join(builder.ENTRY.format(version='test').split())
    route = ' '.join((builder.ROOT / 'references/hosted-execution.md').read_text(encoding='utf-8').split())
    for text in (entry, route):
        assert 'one continuous job' in text and 'replies 繼續' in text
    assert 'Do not end the response to report the preflight' in entry
    assert 'make up an example prompt' in entry
    for stale in ('name what remains', 'turn limit', 'short progress update', 'tell the user the body'):
        assert stale not in entry and stale not in route


def test_one_subjects_reference_directory_carries_every_subjects_templates(tmp_path):
    """A hosted model materialized 數B, reused that directory for other subjects, found
    no templates for them and fell back to a GitHub download the runtime blocked."""
    archive = builder.build('templates-test', tmp_path / 'skill.zip')['archive']
    inspect_archive(Path(archive), tmp_path / 'skill')
    reading_plan_from_directory(tmp_path / 'skill', '數學B', tmp_path / 'refs')
    for row in MAPPING['subjects']:
        for record in production_records(row):
            assert (tmp_path / 'refs' / record['repository_path']).is_file(), record['repository_path']
