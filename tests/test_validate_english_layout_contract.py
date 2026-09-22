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


OFFICIAL_115_READING_STEMS = {
    35: "What is this passage mainly about?", 36: "Which of the following idioms is closest in meaning to “exacerbated the situation” in the third paragraph?",
    37: "According to the passage, which of the following is true about Shackleton and his Antarctic expedition?",
    38: "Which of the following shows the correct route of the Endurance after leaving South Georgia?",
    39: "Which question can the passage answer?", 40: "What does “them” in the third paragraph refer to?",
    41: "According to the passage, which is a correct time sequence of the materials used in making spiral staircases?",
    42: "Which of the following statements can be inferred about spiral staircases in the Medieval Ages?",
    43: "What is the passage mainly about?", 44: "What does “this” refer to in the second paragraph?",
    45: "Which of the following is closest in meaning to “a blip” in the last paragraph?", 46: "Which of the following statements is true?",
}


def test_reading_stem_mix_follows_the_official_booklets():
    assert MODULE.reading_stem_errors({n: {"prompt": s} for n, s in OFFICIAL_115_READING_STEMS.items()}) == []
    detail_only = {n: {"prompt": "Which of the following statements is true about the passage?"} for n in range(35, 47)}
    errors = MODULE.reading_stem_errors(detail_only)
    assert any("至少 2 題字詞／指涉題" in e for e in errors)
    assert any("至少 1 題全文題" in e for e in errors)
    assert any("12 題為「which is true／NOT」" in e for e in errors)


def test_mixed_section_is_fill_multiple_short_never_single():
    official = {47: {"type": "fill_in", "score": 2}, 48: {"type": "fill_in", "score": 2},
                49: {"type": "multiple_choice", "score": 4}, 50: {"type": "constructed_response", "score": 2}}
    assert MODULE.mixed_section_errors(official) == []
    singles = {n: {"type": "single_choice", "score": 2.5} for n in range(47, 51)}
    errors = MODULE.mixed_section_errors(singles)
    assert any("不得有單選題" in e for e in errors)
    assert any("恰有 1 題多選題" in e for e in errors)
    assert any("一題 2 分簡答題" in e for e in errors)


def test_vocabulary_stem_words_translation_length_and_composition_picture_are_measured():
    questions = [{"number": 1, "prompt": "Jane is the best ______.", "options": [{"label": "A"}, {"label": "B"}, {"label": "C"}, {"label": "D"}], "option_layout": "row-4"}]
    exam = {"metadata": {"subject": "英文"}, "sections": [{"id": "translation", "title": "一、中譯英（占8分）"}],
            "questions": questions + [_composition("依提示寫一篇英文作文，文長至少120個單詞（words）。提示：請描述圖片，第一段說明現象，第二段說明你的看法。" + "並且" * 100),
                                      {"number": None, "number_display": "1.", "section_id": "translation", "prompt": "戰爭很可怕。"}]}
    errors = MODULE.validate_exam(exam)
    assert any("第1題詞彙題幹 4 個單詞" in e for e in errors)
    assert any("中譯英第1句 5 字" in e for e in errors)
    assert any("英文作文須附圖片" in e for e in errors)
    assert any("英文作文提示 " in e and "官方 111–115 為 108–174 字" in e for e in errors)
