import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_english_vocabulary_scope.py"
SPEC = importlib.util.spec_from_file_location("english_vocab_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_expand_ceec_notation():
    assert MODULE._expand_word_expression("a/an") == {"a", "an"}
    assert MODULE._expand_word_expression("accomplish(ment)") == {"accomplish", "accomplishment"}
    assert MODULE._expand_word_expression("argue(argument)") == {"argue", "argument"}
    assert MODULE._expand_word_expression("they (them, their, theirs, themselves)") == {
        "they", "them", "their", "theirs", "themselves"
    }


def test_morphology_resolves_regular_forms():
    index = {"study": [{"entry": "study", "pos": "v.", "level": 1}]}
    resolved, _ = MODULE.resolve_token("studies", index)
    assert resolved == "study"


def test_vocabulary_item_requires_same_pos_and_evidence():
    index = {
        word: [{"entry": word, "pos": pos, "level": level}]
        for word, pos, level in [
            ("a", "art.", 1), ("tight", "adj.", 3), ("daily", "adj.", 2),
            ("schedule", "n./v.", 3), ("hasty", "adj.", 4),
            ("diligent", "adj.", 4), ("routine", "adj./n.", 3),
        ]
    }
    exam = {
        "sections": [{"id": "v", "title": "詞彙題"}],
        "questions": [{
            "id": "q1", "section_id": "v", "prompt": "A tight daily schedule.",
            "options": [{"text": x} for x in ["hasty", "tight", "diligent", "routine"]],
            "item_spec": {"lexical_scope": {
                "target_word": "tight", "target_pos": "adj.",
                "option_pos": ["adj.", "adj.", "adj.", "adj."],
                "disambiguating_evidence": ["tight schedule", "limited time"],
                "distractor_confusion_basis": ["speed", "effort", "regularity"],
            }},
        }],
    }
    report = MODULE.validate_exam(exam, index)
    assert report["status"] == "pass"


def test_nonreading_level_six_fails():
    index = {"arcane": [{"entry": "arcane", "pos": "adj.", "level": 6}]}
    exam = {
        "sections": [{"id": "c", "title": "綜合測驗"}],
        "questions": [{"id": "q", "section_id": "c", "prompt": "arcane", "options": []}],
    }
    report = MODULE.validate_exam(exam, index)
    assert any(error["code"] == "unjustified_level_6_nonreading" for error in report["errors"])
