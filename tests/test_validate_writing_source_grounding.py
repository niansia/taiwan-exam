from scripts.validate_writing_source_grounding import validate_exam


def source(source_id="s1", voice="authored_literary_prose", invented=None, language="zh-Hant"):
    return {
        "source_id": source_id,
        "source_voice": voice,
        "source_language": language,
        "invented_modelling_values": invented or [],
    }


def question(qid="q1", role="intellectual_integration", source_id="s1"):
    return {
        "id": qid,
        "prompt": "本文內容。（改寫自某篇文章）",
        "item_spec": {
            "writing_task_role": role,
            "source_ids": [source_id],
            "material_source_map": [{
                "material_id": "本文",
                "source_ids": [source_id],
                "supported_claims": ["一項可核對主張"],
            }],
        },
    }


def test_grounded_two_task_paper_passes():
    exam = {"metadata": {"paper_subject": "國寫"}, "questions": [
        question(),
        question("q2", "affective_expression"),
    ]}
    assert validate_exam(exam, {"sources": [source()]}) == []


def test_invented_case_marker_and_values_fail():
    q1 = question()
    q1["prompt"] += "；校園案例為命題所設"
    exam = {"metadata": {"paper_subject": "國寫"}, "questions": [
        q1,
        question("q2", "affective_expression"),
    ]}
    errors = validate_exam(exam, {"sources": [source(invented=["虛構數值"])]})
    assert any("命題所設" in error for error in errors)
    assert any("invented_modelling_values" in error for error in errors)


def test_second_task_requires_authored_source_voice():
    exam = {"metadata": {"paper_subject": "國寫"}, "questions": [
        question(),
        question("q2", "affective_expression"),
    ]}
    errors = validate_exam(exam, {"sources": [source(voice="institutional_explainer")]})
    assert any("第二大題缺少" in error for error in errors)


def test_source_note_must_follow_body_and_material_heading_is_forbidden():
    q1 = question()
    q1["prompt"] = "材料一：本文內容。\n\n（改寫自某篇文章）"
    exam = {"metadata": {"paper_subject": "國寫"}, "questions": [
        q1,
        question("q2", "affective_expression"),
    ]}
    errors = validate_exam(exam, {"sources": [source()]})
    assert any("材料一" in error for error in errors)
    assert any("不得獨立成段" in error for error in errors)


def test_second_task_requires_chinese_or_named_translation():
    exam = {"metadata": {"paper_subject": "國寫"}, "questions": [
        question(),
        question("q2", "affective_expression"),
    ]}
    errors = validate_exam(exam, {"sources": [source(language="en")]})
    assert any("中文創作" in error for error in errors)
