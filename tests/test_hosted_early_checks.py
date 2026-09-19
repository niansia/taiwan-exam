"""Defects that used to surface only in final page review are caught or avoided earlier."""
import hashlib
import json
from pathlib import Path
import sys

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import append_items as appender
import compose_hosted_pdf as composer
import hosted_body_templates as templates
import run_hosted_workflow as workflow
from hosted_run_timing import transition

FONT = pymupdf.Font('cjk').buffer


@pytest.mark.parametrize('text,expected', [
    (r'計算 \frac{1}{2}', r'LaTeX \frac'),
    (r'x \cdot y', r'LaTeX \cdot'),
    ('設 $x$ 為實數', '"$"'),
    ('面積為 3$', '"$"'),
    ('a<sup>2</sup>+b<sup>2', 'unbalanced'),
])
def test_text_that_would_print_literally_is_named(text, expected):
    assert any(expected in issue for issue in workflow.text_issues(text))


@pytest.mark.parametrize('text', ['人均所得 US$30,000', 'NT$ 500 元', r'A \ B 的差集', 'H<sub>2</sub>O', 'x² + y²'])
def test_legitimate_printed_text_passes(text):
    assert workflow.text_issues(text) == []


@pytest.fixture
def run(tmp_path):
    workflow.save(tmp_path / 'preflight.json', {
        'status': 'ready-for-authoring', 'paper_id': 'p', 'subject': '數學A', 'review_mode': 'single-context',
        'require_independent_review': False, 'calibration': {}, 'template_asset_dir': 'templates'})
    transition(tmp_path / 'generation-timing.json', 'p', 'reference_preflight')
    workflow.save(tmp_path / 'plan.json', {
        'metadata': {'title': 'Synthetic checks only', 'exam': '學測', 'calibration_level': 'exploratory-uncalibrated'},
        'sections': [{'id': 's', 'title': '一、單選題'}], 'instructions': ['Not an exam.']})
    return tmp_path


def save_item(run, question, answer):
    workflow.save(run / 'batch.json', {'questions': [question], 'answers': [answer]})
    return appender.append(run, run / 'batch.json', plan=run / 'plan.json')


def test_batch_with_print_defects_is_refused_listing_every_issue(run):
    (run / 'q1.png').write_bytes(b'not the registered bytes')
    question = {'id': 'q1', 'number': 1, 'section_id': 's', 'type': 'single_choice',
                'prompt': r'若 $f(x)=x^2$，則 f(2) \times 3 為何？{{asset:area}}',
                'options': [{'label': '1', 'text': '12'}, {'label': '2', 'text': 'x<sup>2'}],
                'inline_assets': {'q1': {'path': 'q1.png', 'sha256': '0' * 64, 'width_pt': 40}}}
    answer = {'question_id': 'q1', 'final_answer': '1', 'reasoning': [r'f(2)=4，4 \cdot 3=12。']}
    with pytest.raises(ValueError) as caught:
        save_item(run, question, answer)
    for expected in (r'prompt: LaTeX \times', 'prompt: "$"', 'option 2: unbalanced', r'reasoning 1: LaTeX \cdot',
                     '{{asset:area}} is not declared', 'inline asset q1: sha256'):
        assert expected in str(caught.value)
    assert not (run / 'exam.json').exists()


def test_clean_batch_with_a_registered_formula_image_saves(run):
    image = run / 'q1.png'
    image.write_bytes(b'formula image bytes')
    question = {'id': 'q1', 'number': 1, 'section_id': 's', 'type': 'single_choice',
                'prompt': '已知 {{asset:f}} 且 x² = 4，求 x。',
                'options': [{'label': '1', 'text': '2'}, {'label': '2', 'text': '−2'}],
                'inline_assets': {'f': {'path': 'q1.png', 'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                                        'width_pt': 60}}}
    answer = {'question_id': 'q1', 'final_answer': '1', 'reasoning': ['由 x² = 4 得 x = ±2。']}
    assert save_item(run, question, answer)['status'] == 'items-saved'


def body_font(tmp_path):
    path = tmp_path / 'font.ttf'
    path.write_bytes(FONT)
    return path


def test_figure_wider_than_its_column_prints_at_column_width(tmp_path):
    figure = tmp_path / 'wide.svg'
    figure.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">'
                      '<rect x="1" y="1" width="398" height="98" fill="none" stroke="black"/></svg>', encoding='utf-8')
    block = {'kind': 'choice', 'id': 'q1', 'number': 1, 'text': '合成題幹', 'figure': 'fig', 'figure_position': 'below',
             'assets': {'fig': {'path': 'wide.svg', 'sha256': hashlib.sha256(figure.read_bytes()).hexdigest(), 'width_pt': 460}},
             'options': [{'label': '(1)', 'text': '甲'}, {'label': '(2)', 'text': '乙'}]}
    layout = templates.render({'subject': '數學A', 'blocks': [block]}, tmp_path / 'body.pdf', tmp_path / 'layout.json',
                              body_font(tmp_path), asset_root=tmp_path)
    [scaled] = layout['scaled_assets']
    assert scaled['asset'] == 'fig' and scaled['requested_pt'] == 460 and scaled['printed_pt'] < 460


def test_last_page_holding_one_block_is_pulled_back_by_closer_spacing(tmp_path, monkeypatch):
    font = body_font(tmp_path)
    text = '合成段落，用於測試最後一頁只剩一兩行時，較小的題間距能否把它收回前一頁。'

    def pages(count, tag):
        blocks = [{'kind': 'stimulus', 'id': f'q{n}', 'text': text} for n in range(count)]
        layout = templates.render({'subject': '數學A', 'blocks': blocks}, tmp_path / f'{tag}.pdf',
                                  tmp_path / f'{tag}.json', font, asset_root=tmp_path)
        return max(row['page'] for row in layout['blocks']), layout

    monkeypatch.setattr(templates, 'TIGHTER_GAPS', ())
    low, high = 1, 80
    while high - low > 1:  # the fewest blocks that spill onto a second page at normal spacing
        middle = (low + high) // 2
        low, high = (middle, high) if pages(middle, f'plain-{middle}')[0] == 1 else (low, middle)
    monkeypatch.undo()
    count, layout = pages(high, 'tightened')
    assert count == 1 and layout['gap_scale'] < 1


def two_copies_of_a_whole_font():
    """Pages from separate sources carry separate font copies, as body and header fields did."""
    out = pymupdf.open()
    for text in ('測試字型精簡', '重複嵌入的同一字型'):
        with pymupdf.open() as source:
            page = source.new_page()
            page.insert_font(fontname='F', fontbuffer=FONT)
            page.insert_text((72, 100), text, fontname='F', fontsize=14)
            out.insert_pdf(source)
    return out.tobytes(deflate=True)


def rasters(data):
    with pymupdf.open(stream=data, filetype='pdf') as doc:
        return [page.get_pixmap(matrix=pymupdf.Matrix(3, 3), alpha=False).samples for page in doc], \
               [page.get_text() for page in doc]


def test_duplicate_whole_fonts_shrink_without_any_pixel_or_text_change():
    pytest.importorskip('fontTools')
    data = two_copies_of_a_whole_font()
    compact, report = composer.compact_fonts(data)
    assert report['status'] == 'unused-glyphs-dropped' and len(compact) < len(data) / 4
    assert rasters(compact) == rasters(data)


def test_without_fonttools_duplicate_fonts_are_still_merged(monkeypatch):
    monkeypatch.setitem(sys.modules, 'fontTools', None)  # any fontTools import now fails
    data = two_copies_of_a_whole_font()
    merged, report = composer.compact_fonts(data)
    assert report['status'] == 'duplicates-merged' and 'fontTools unavailable' in report['note']
    assert len(merged) < len(data) * 0.7 and rasters(merged) == rasters(data)


def test_subset_that_would_change_rendering_keeps_the_whole_fonts(monkeypatch):
    subset = pytest.importorskip('fontTools.subset')
    populate = subset.Subsetter.populate
    monkeypatch.setattr(subset.Subsetter, 'populate', lambda self, **kwargs: populate(self, gids=[0]))
    data = two_copies_of_a_whole_font()
    kept, report = composer.compact_fonts(data)
    assert report['status'] == 'duplicates-merged' and 'full fonts kept' in report['note']
    assert rasters(kept) == rasters(data)
