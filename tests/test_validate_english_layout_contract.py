import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_english_layout_contract.py"
SPEC = importlib.util.spec_from_file_location("english_layout_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_wrong_score_and_standalone_blanks_fail():
    questions = []
    for number in range(11, 35):
        questions.append({"number": number, "prompt": f"Blank ({number})", "group_stimulus": "passage"})
    exam = {
        "metadata": {"subject": "英文", "scoring_note": "第壹部分72分"},
        "sections": [{"id": "vocabulary", "title": "第壹部分、選擇題（占72分）"}],
        "questions": questions,
    }
    errors = MODULE.validate_exam(exam)
    assert any("62分" in error for error in errors)
    assert any("獨立空格列" in error for error in errors)
    assert any("文章內編號底線" in error for error in errors)
