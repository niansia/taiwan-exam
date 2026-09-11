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


def _composition(prompt, *, forced_jump=False):
    return {
        "id": "composition", "section_id": "composition", "type": "guided_writing",
        "prompt": prompt,
        "item_spec": {"composition_contract": {
            "directions_language": "zh-TW", "minimum_words": 120,
            "student_accessible_context": True,
            "prompt_coherence_review": {
                "status": "pass", "forced_moral_or_abstract_jump": forced_jump,
                "multiple_valid_angles": True,
                "task_bridge": "第二段直接回應第一段所描述的校園經驗與選擇。",
            },
        }},
    }


def test_english_composition_directions_must_be_written_in_chinese():
    exam = {
        "metadata": {"subject": "英文"},
        "questions": [_composition("Write an English essay of at least 120 words about a school experience.")],
    }
    errors = MODULE.validate_exam(exam)
    assert "英文作文的學生作答提示必須以中文完整書寫" in errors
    assert "英文作文題幹須以中文明示英文作文與至少120個單詞" in errors


def test_forced_abstract_jump_is_a_release_failure():
    prompt = (
        "依提示寫一篇英文作文，文長至少120個單詞。第一段描述一次校園活動中遇到的選擇，"
        "第二段說明你當時如何決定，以及這個決定帶來的具體影響。"
    )
    exam = {"metadata": {"subject": "英文"}, "questions": [_composition(prompt, forced_jump=True)]}
    errors = MODULE.validate_exam(exam)
    assert "英文作文不得從圖片觀察硬跳到無關的抽象教訓" in errors
