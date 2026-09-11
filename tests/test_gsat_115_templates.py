"""Layout-only template regressions; these do not certify exam content."""

import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gsat_115_templates import COVER_CSS, FORMULA_GROUPS, SUBJECT_ORDER, cover_markup, inner_markup
from render_gsat_template_assets import component_markup
from render_gsat_official import cover as official_cover
from package_skill import should_include


def test_manifest_and_runtime_cover_the_same_seven_subjects():
    manifest = json.loads((ROOT / "exam_packs/學測/templates/115/template-pack.json").read_text(encoding="utf-8"))
    assert tuple(manifest["subjects"]) == SUBJECT_ORDER
    assert manifest["template_kind"] == "layout-only"
    assert set(manifest["dynamic_fields"]) == {"academic_year", "exam_name", "current_page", "total_pages"}
    assert should_include(ROOT / "scripts/gsat_115_templates.py")
    assert should_include(ROOT / "scripts/render_gsat_template_assets.py")
    assert should_include(ROOT / "exam_packs/學測/templates/115/assets/math-b/formula-blank.pdf")


def test_blank_assets_really_leave_year_name_and_page_numbers_open():
    cover = BeautifulSoup(cover_markup("社會"), "html.parser")
    assert cover.select_one(".tpl-title").get_text() == ""
    inner = BeautifulSoup(inner_markup("社會", parity="odd"), "html.parser")
    assert inner.select_one(".blank-year").get_text() == ""
    assert all(node.get_text() == "" for node in inner.select(".blank-number"))
    assert "Taiwan Exam 模擬試題" in cover.get_text()


def test_fillable_fields_are_escaped_and_land_in_expected_roles():
    markup = component_markup("英文", "packet", year="116", exam_name="<測驗>", current_page="3", total_pages="11")
    soup = BeautifulSoup(markup, "html.parser")
    assert soup.select_one(".tpl-title").get_text() == "116學年度<測驗>"
    assert soup.select_one(".blank-year").get_text() == "116"
    assert soup.select_one(".blank-number").get_text() == "3"
    assert "116年<測驗>" in soup.select_one(".inner-header").get_text()
    standard = BeautifulSoup(component_markup("英文", "inner-odd", year="116", exam_name="學科能力測驗模擬試題"), "html.parser")
    assert "116年學測" in standard.select_one(".inner-header").get_text()
    assert soup.find("測驗") is None


def test_locked_cover_uses_subject_rules_not_authored_question_instructions():
    natural = BeautifulSoup(cover_markup("自然", year="116", exam_name="學科能力測驗模擬試題"), "html.parser")
    assert "考試時間：110分鐘" in natural.get_text()
    assert "多選題" in natural.get_text()
    social = BeautifulSoup(cover_markup("社會"), "html.parser")
    assert "多選題" not in social.get_text()
    writing = BeautifulSoup(cover_markup("國寫"), "html.parser")
    assert "非選擇題共二大題" in writing.get_text()
    assert "限用中文書寫" in writing.get_text()


def test_formal_renderer_calls_locked_cover_instead_of_llm_instructions():
    rendered = BeautifulSoup(official_cover({"subject": "英文", "academic_year": "117"}, ["不應印出的LLM封面文字"]), "html.parser")
    assert "117學年度學科能力測驗模擬試題" in rendered.get_text()
    assert "不應印出的LLM封面文字" not in rendered.get_text()


def test_math_a_and_b_formula_variants_are_intentionally_different():
    assert len(FORMULA_GROUPS["數學A"]) == 7
    assert len(FORMULA_GROUPS["數學B"]) == 6
    assert any("和角公式" in line for group in FORMULA_GROUPS["數學A"] for line in group)
    assert not any("和角公式" in line for group in FORMULA_GROUPS["數學B"] for line in group)


def test_math_cover_fractions_are_atomic_and_fixed_denominator_has_one_bar():
    soup = BeautifulSoup(cover_markup("數學B"), "html.parser")
    fixed = soup.select_one(".fixed-denominator")
    assert fixed is not None and fixed.get_text() == "50"
    assert "white-space:nowrap" in COVER_CSS
    fraction_rule = COVER_CSS.split(".gsat115-cover .frac", 1)[1].split("}", 1)[0]
    assert "vertical-align:middle" in fraction_rule
    rule = COVER_CSS.split(".fill-fraction .fixed-denominator", 1)[1].split("}", 1)[0]
    assert "border-bottom" not in rule
