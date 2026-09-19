"""Formal PDFs compose on bundled fixed templates; a template gap stops instead of redrawing."""
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
    for path in plan['layout_previews']:
        published = ROOT / 'docs/layout-examples' / builder.PREVIEW_VERSION / Path(path).name
        with pymupdf.open(path) as bundled, pymupdf.open(published) as original:
            assert bundled.page_count == original.page_count
            for mine, theirs in zip(bundled, original):
                assert mine.get_text() == theirs.get_text()
                assert (mine.get_pixmap(matrix=pymupdf.Matrix(2, 2)).samples ==
                        theirs.get_pixmap(matrix=pymupdf.Matrix(2, 2)).samples)


def test_entry_forbids_redrawn_templates_and_requires_the_final_check():
    entry = builder.ENTRY.format(version='test')
    for phrase in ('Never typeset, trace or redraw', 'check_hosted_run.py', 'bundled original fixed template'):
        assert phrase in entry
