"""Component regressions only; no fixture certifies an authored full exam."""
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_gsat_internal_review as renderer
from safe_rendering import prepare_html


def test_math_keeps_fraction_root_matrix_and_escapes_prose():
    value = r'<b>文字</b> \(x=\frac{1}{\sqrt{2}}\)，\(M=\begin{pmatrix}1&2\\3&4\end{pmatrix}\)'
    html = renderer._math_text_block(value)
    soup = BeautifulSoup(html, "html.parser")
    assert soup.find("b") is None
    assert len(soup.find_all("math")) == 2
    assert soup.mfrac is not None and soup.msqrt is not None
    assert len(soup.mtable.find_all("mtr")) == 2
    assert len(soup.mtable.find_all("mtd")) == 4
    assert all(node.get("displaystyle") == "true" for node in soup.find_all("math"))
    prepare_html(html)


@pytest.mark.parametrize("value", [
    r"\(x", r"\(x\) and \(", r"\(\href{https://example.com}{x}\)",
    r"\(\includegraphics{file}\)", r"\(\input{file}\)",
])
def test_bad_math_does_not_become_active_or_unrendered_content(value):
    with pytest.raises(ValueError):
        renderer._math_text_block(value)


def test_cover_marks_sign_and_digits_in_separate_actual_boxes():
    soup = BeautifulSoup(renderer._measured_math_cover({"subject":"數學A","duration_minutes":100}), "html.parser")
    rows = soup.select(".mark-row")
    assert len(rows) == 4
    selected = [row.select_one(".marked").get_text(strip=True) for row in rows]
    assert selected == ["3", "8", "−", "7"]
    assert all(len(row.select(".mark-cell b")) == 12 for row in rows)
    assert len(soup.select(".fill-slot")) == 4
    assert soup.select_one(".fixed-denominator").get_text() == "50"
    assert soup.select_one(".prototype") is None


def test_fill_fraction_rows_continue_from_numerator_to_denominator():
    soup = BeautifulSoup(renderer._fill_format({
        "number":16, "answer_format":{"kind":"fraction","numerator_slots":2,"denominator_slots":1}
    }), "html.parser")
    assert [node.get_text() for node in soup.select(".fill-slot")] == ["16-1","16-2","16-3"]
    assert soup.find("div") is None


def test_reference_formula_components_are_semantic_not_images():
    soup = BeautifulSoup(renderer._measured_math_formulas(), "html.parser")
    assert len(soup.select(".formula-block")) == 7
    assert soup.find("img") is None and soup.find("script") is None
    assert len(soup.find_all("mfrac")) >= 10
    assert len(soup.find_all("msqrt")) >= 6
    prepare_html(str(soup))


def test_math_b_reference_sheet_omits_math_a_angle_addition_block():
    soup = BeautifulSoup(renderer._measured_math_formulas("數學B"), "html.parser")
    assert len(soup.select(".formula-block")) == 6
    assert "和角公式" not in soup.get_text()
    assert "正弦定理" in soup.get_text()


def answer_fixture():
    return {
        "metadata": {"subject":"數學A", "layout_contract_version":4,
                     "answer_page_groups":[["q1"],["q2"]], "answer_expected_page_count":3},
        "questions":[{"id":"q1","number":1},{"id":"q2","number":2}],
        "answers":[{"question_id":qid,"final_answer":"1","reasoning":[r"計算 \(\frac{1}{2}\)。"]}
                   for qid in ("q1","q2")],
    }


def test_every_measured_answer_page_is_a_bounded_sheet():
    soup = BeautifulSoup(renderer._answers(answer_fixture()), "html.parser")
    assert len(soup.select(".sheet")) == 3
    assert len(soup.select(".sheet .content")) == 3
    assert len(soup.select(".sheet .solution")) == 2
    assert not soup.select(".answer-cover,.answer-page")


@pytest.mark.parametrize('correct_count', [1, 2, 3, 4, 5])
def test_math_a_multiple_selection_prints_every_allowed_correct_count(correct_count):
    # Serialization regression, not mathematical validation of a new question.
    exam = answer_fixture()
    question = exam['questions'][0]
    question['type'] = 'multiple_choice'
    question['options'] = [{'label': str(i), 'text': f'陳述{i}'} for i in range(1, 6)]
    key = [str(i) for i in range(1, correct_count + 1)]
    exam['answers'][0]['final_answer'] = key
    soup = BeautifulSoup(renderer._answers(exam), 'html.parser')
    printed_key = soup.select_one('.answer-grid tbody tr').select('td')[1].get_text()
    assert printed_key == '、'.join(key)
    assert '答案：' + '、'.join(key) in soup.select_one('.solution h2').get_text()


@pytest.mark.parametrize("groups", [None,[],[["q1"]],[["q1","q1"]],[["q2","q1"]]])
def test_answer_page_plan_cannot_lose_duplicate_or_reorder_answers(groups):
    exam = answer_fixture()
    exam["metadata"]["answer_page_groups"] = groups
    with pytest.raises(ValueError):
        renderer._answers(exam)


def test_answer_page_count_is_approved_before_printing():
    exam = answer_fixture()
    exam["metadata"]["answer_expected_page_count"] = 2
    with pytest.raises(ValueError):
        renderer._answers(exam)


@pytest.mark.parametrize("value", [r"\(\binom63=20\)", r"\(\frac12\)", r"\(\frac{1}2\)", "u=2^x", "M_min=3"])
def test_ambiguous_or_plain_math_cannot_silently_change_printed_meaning(value):
    with pytest.raises(ValueError):
        renderer._math_text_block(value)


def test_braced_binomial_has_six_above_three_not_sixtythree_above_equals():
    soup = BeautifulSoup(renderer._math_text_block(r"\(\binom{6}{3}=20\)"), "html.parser")
    fraction = soup.mfrac
    assert fraction is not None
    assert [x.get_text() for x in fraction.find_all(recursive=False)] == ["6", "3"]


@pytest.mark.parametrize("value", [r"\(\sin^2\theta+\cos^2\theta\)", r"\(\log_2 a+\log_2 b\)", r"\(\log_2^2 x\)"])
def test_function_spacing_preserves_script_arity_and_stays_in_expression_rows(value):
    soup = BeautifulSoup(renderer._math_text_block(value), "html.parser")
    assert soup.find("mspace") is not None
    for node in soup.find_all(["msub", "msup", "msubsup"]):
        assert len(node.find_all(recursive=False)) == (3 if node.name == "msubsup" else 2)
        assert node.find("mspace", recursive=False) is None
    for node in soup.find_all("mspace"):
        assert node.parent.name == "mrow"


def test_teacher_even_page_footer_is_on_the_outer_right():
    soup = BeautifulSoup(renderer._answers(answer_fixture()), "html.parser")
    footers = soup.select(".footer .center")
    assert ["outer-right" in node.get("class", []) for node in footers] == [False, True, False]


def test_only_immediate_closing_punctuation_is_bound_to_inline_math():
    value = r'前文\(x^2\)，\(y_1\)。」後文<b>不是標記</b>'
    soup = BeautifulSoup(renderer._math_text_block(value, keep_closing_punctuation=True), 'html.parser')
    spans = soup.select('.math-with-punctuation')
    assert len(spans) == 2
    assert [span.contents[-1] for span in spans] == ['，', '。」']
    assert all(len(span.find_all('math')) == 1 for span in spans)
    assert '後文' not in spans[-1].get_text()
    assert soup.find('b') is None
    prepare_html(str(soup))


@pytest.mark.parametrize('value', [r'\[x^2\]。', '\\(x^2\\)\n。', r'\(x^2\) 下一句。'])
def test_punctuation_binding_does_not_capture_display_math_or_whitespace(value):
    soup = BeautifulSoup(renderer._math_text_block(value, keep_closing_punctuation=True), 'html.parser')
    assert not soup.select('.math-with-punctuation')
    assert len(soup.find_all('math')) == 1


def test_punctuation_fix_is_enabled_for_measured_answers_not_legacy_papers():
    exam = answer_fixture()
    assert BeautifulSoup(renderer._answers(exam), 'html.parser').select('.math-with-punctuation')
    exam['metadata']['layout_contract_version'] = 3
    assert not BeautifulSoup(renderer._answers(exam), 'html.parser').select('.math-with-punctuation')
    assert 'math-with-punctuation' not in renderer._paper_text(r'\(x\)。', '數學A')


@pytest.mark.parametrize('subject', ['數學A', '數學B'])
@pytest.mark.parametrize('overlong', [False, True])
def test_real_browser_math_fragments_have_glyph_clearance(tmp_path, subject, overlong):
    from render_pdf import find_browser
    from validate_fixed_page_html import validate_html
    try:
        browser = find_browser()
    except (ValueError, FileNotFoundError, RuntimeError):
        pytest.skip('A local Chromium browser is needed for actual geometry')
    # New component fixture, not a reused exam or an educational-quality claim.
    formulas = [r'\frac{1}{\sqrt{2}}', r'\log_2^2 x', r'\sqrt{\frac{a^2+b^2}{3}}',
                r'\begin{pmatrix}1&2\\3&4\end{pmatrix}']
    if overlong:
        formulas.append('+'.join(['x'] * 120))
    body = ''.join('<div class="question"><span class="qno">1.</span><div class="prompt">'
                   + renderer._math_text_block('檢查\\(' + formula + '\\)的字形邊界。') + '</div></div>'
                   for formula in formulas)
    source = tmp_path / 'math-geometry.html'
    source.write_text('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>'
                      + renderer.STYLE + '</style></head><body class="paper-' + subject
                      + ' measured-math"><section class="sheet"><main class="content">'
                      + body + '</main></section></body></html>', encoding='utf-8')
    report = validate_html(source, browser)
    assert report['status'] == ('fail' if overlong else 'pass'), report
