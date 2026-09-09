import builtins
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def importer_without_xlrd(monkeypatch):
    original = builtins.__import__
    def without_xlrd(name, *args, **kwargs):
        if name == 'xlrd':
            raise ModuleNotFoundError('Simulated unavailable optional dependency')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', without_xlrd)
    spec = importlib.util.spec_from_file_location('statistics_without_xlrd', ROOT / 'scripts/import_ceec_gsat_difficulty.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_helpers_work_without_excel_dependency(importer_without_xlrd):
    assert importer_without_xlrd.number('1,234') == 1234
    assert importer_without_xlrd.difficulty_band_from_p(.85) == 'very_easy'


def test_missing_data_is_not_misreported_as_install_failure(importer_without_xlrd, tmp_path):
    with pytest.raises(SystemExit, match='official-statistics-registry'):
        importer_without_xlrd.build(tmp_path)


def test_actual_excel_ingestion_requires_optional_dependency_before_writes(importer_without_xlrd, tmp_path):
    metadata = tmp_path / 'exam_packs/學測/metadata'
    metadata.mkdir(parents=True)
    (metadata / 'official-statistics-registry.jsonl').write_text(json.dumps({'table_kind':'item_metrics_table'}) + '\n', encoding='utf-8')
    with pytest.raises(SystemExit, match='requirements-statistics.txt'):
        importer_without_xlrd.build(tmp_path)
    assert not (metadata / 'official-difficulty-analysis.json').exists()
