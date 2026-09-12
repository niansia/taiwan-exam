"""Additions remain reproducible, fail closed and never expose item records."""
import copy
import json
from pathlib import Path
import shutil
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import writer_calibration as wc
from audit_exam_pack import readiness


@pytest.fixture
def pack(tmp_path):
    source = ROOT / 'exam_packs/學測/subjects/英文'
    for name in ('blueprints/writer-blueprint.json', wc.LEDGER, wc.EXTENSION):
        target = tmp_path / name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source / name, target)
    return tmp_path


def test_all_seven_have_metadata_coverage():
    report = readiness(ROOT, check_sources=False)
    assert report['status'] == 'prerequisites-ready'
    assert all(not p['missing_pattern_slots'] for p in report['papers'])


def test_loader_returns_only_aggregates_and_preserves_base(pack):
    base_bytes = (pack / 'blueprints/writer-blueprint.json').read_bytes()
    base = json.loads(base_bytes)
    result = wc.load_writer(pack)
    assert result['metadata_fingerprint'] != base['metadata_fingerprint']
    assert result['calibration_by_curriculum'] == base['calibration_by_curriculum']
    assert 'question_source' not in json.dumps(result)
    assert 'observations' not in json.dumps(result)
    assert (pack / 'blueprints/writer-blueprint.json').read_bytes() == base_bytes
    assert result == wc.load_writer(pack)


@pytest.mark.parametrize('name', ['blueprints/writer-blueprint.json', wc.LEDGER, wc.EXTENSION])
def test_tampered_components_fail(pack, name):
    path = pack / name
    doc = wc.read(path)
    doc['tampered'] = True
    path.write_text(json.dumps(doc), encoding='utf-8')
    with pytest.raises(ValueError, match='stale or altered'):
        wc.load_writer(pack)


def test_missing_sources_are_not_silently_ready(pack, tmp_path):
    with pytest.raises(ValueError, match='reference unavailable'):
        wc.load_writer(pack, tmp_path)


def test_missing_extension_does_not_fall_back(pack):
    (pack / wc.EXTENSION).unlink()
    with pytest.raises(ValueError, match='additions missing'):
        wc.load_writer(pack)


def test_duplicate_item_cannot_inflate_support(pack):
    ledger = wc.read(pack / wc.LEDGER)
    ledger['records'].append(copy.deepcopy(ledger['records'][0]))
    with pytest.raises(ValueError, match='duplicate'):
        wc.aggregate(ledger)


def test_one_year_cannot_fill_a_family(pack):
    ledger = wc.read(pack / wc.LEDGER)
    ledger['records'] = [r for r in ledger['records'] if r['year'] == 2026]
    with pytest.raises(ValueError, match='three reviewed'):
        wc.aggregate(ledger)


def test_changed_pdf_fails_hash_check(pack, tmp_path):
    extension = wc.read(pack / wc.EXTENSION)
    for source in extension['source_files']:
        target = tmp_path / source['relative_path']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'not the inspected original')
    with pytest.raises(ValueError, match='hash mismatch'):
        wc.load_writer(pack, tmp_path)
