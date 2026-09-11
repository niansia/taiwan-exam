"""A league's points must not disable actual calculus detection."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_math_curriculum import forbidden_pattern_present


def test_explicit_league_scoring_nouns_are_not_calculus():
    assert not forbidden_pattern_present("積分", "勝方3分、和局各1分，此積分制度的四隊積分總和為16。")


@pytest.mark.parametrize("text", [
    "求函數的定積分。", "以不定積分求面積。", "積分總和為多少？",
    "小組賽積分制度如下，再對速度積分求距離。",
    "和局各1分，接著計算定積分。",
])
def test_calculus_and_ambiguous_uses_still_require_rejection(text):
    assert forbidden_pattern_present("積分", text)


def test_other_forbidden_concepts_are_never_exempted_by_sport_words():
    assert forbidden_pattern_present("特徵值", "和局模型的矩陣特徵值。")
