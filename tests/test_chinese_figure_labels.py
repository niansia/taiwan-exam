"""Figure and table labels print in Chinese outside 英文 (a hosted 自然 paper printed a table headed
「sample／sulfate／carbonate」 and figures labelled 「electrolyte」「reaction progress」)."""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_visual_item_contract import english_label_errors


def svg(tmp_path, *labels):
    path = tmp_path / 'fig.svg'
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">'
                    + ''.join(f'<text x="10" y="{20 * n + 20}">{t}</text>' for n, t in enumerate(labels))
                    + '<line x1="0" y1="0" x2="10" y2="10" stroke="black"/></svg>', encoding='utf-8')
    return path


@pytest.mark.parametrize('subject', ['自然', '社會', '數學A', '數學B'])
def test_english_words_in_svg_and_table_data_are_rejected(tmp_path, subject):
    spec = {'kind': 'data_table', 'semantic_data': {'headers': ['sample', 'sulfate', 'carbonate'], 'style': 'dashed'}}
    errors = english_label_errors(14, spec, svg(tmp_path, 'electrolyte', 'reaction progress'), subject)
    assert len(errors) == 1
    for word in ('sample', 'sulfate', 'electrolyte', 'reaction'):
        assert word in errors[0]
    assert 'dashed' not in errors[0]  # a style setting is not a printed label


def test_symbols_units_formulas_and_acronyms_stay_allowed(tmp_path):
    spec = {'kind': 'line_chart', 'semantic_data': {'x_label': '時間 t (s)', 'y_label': '濃度 (mmol/L)',
                                                     'series': [{'label': 'NaHCO3'}, {'label': 'DNA'}]}}
    path = svg(tmp_path, 'x', 'y', 'O', 'kWh', 'NOAA', 'pH 7', 'Ca(OH)2', 'sin θ', 'λ (nm)', 'LED')
    assert english_label_errors(3, spec, path, '自然') == []


def test_english_papers_and_photographs_are_exempt(tmp_path):
    path = svg(tmp_path, 'Library opening hours')
    assert english_label_errors(1, {'kind': 'bar_chart'}, path, '英文') == []
    assert english_label_errors(1, {'kind': 'photo', 'semantic_data': {'caption': 'Main Street'}}, path, '社會') == []


def test_check_figures_reports_english_labels_before_a_build(tmp_path):
    import hashlib
    from hosted_evidence_refresh import figure_selfcheck
    path = svg(tmp_path, 'electrolyte', '電流')
    asset = {'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
             'visual_spec': {'kind': 'schematic', 'semantic_data': {}}}
    exam = {'metadata': {'subject': '自然'}, 'questions': [{'id': 'q11', 'number': 11, 'visual_asset': asset}], 'answers': []}
    result = figure_selfcheck(tmp_path, exam)
    assert any('electrolyte' in e for f in result['figures'] for e in f['errors'])
