from scripts.validate_writing_source_grounding import validate_exam


def source(
    source_id="s1",
    voice="authored_literary_prose",
    invented=None,
    language="zh-Hant",
    publisher="出版者甲",
    domain="文學",
):
    return {
        "source_id": source_id,
        "source_voice": voice,
        "source_language": language,
        "invented_modelling_values": invented or [],
        "publisher": publisher,
        "source_domain": domain,
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


def test_continuation_pages_are_part_of_source_grounding_review():
    q1 = question()
    q1["continuation_pages"] = {"3": "情境為命題所設\n\n（改寫自另一篇文章）"}
    exam = {"metadata": {"paper_subject": "國寫"}, "questions": [
        q1,
        question("q2", "affective_expression"),
    ]}
    errors = validate_exam(exam, {"sources": [source()]})
    assert any("情境為命題" in error for error in errors)
    assert any("不得獨立成段" in error for error in errors)


def test_full_paper_source_pool_is_publisher_neutral_and_diverse():
    exam = {"metadata": {"paper_subject": "國寫", "generation_mode": "full-paper"}, "questions": [
        question(),
        question("q2", "affective_expression", "s2"),
    ]}
    sources = [
        source(f"s{i}", publisher=f"出版者{(i - 1) % 4}", domain=f"領域{(i - 1) % 4}")
        for i in range(1, 9)
    ]
    pool = {"selection_policy": {"publisher_neutral": True}, "sources": sources}
    assert validate_exam(exam, pool) == []


def test_full_paper_rejects_publisher_preference_and_unexplained_majority():
    exam = {"metadata": {"paper_subject": "國寫", "generation_mode": "full-paper"}, "questions": [
        question(),
        question("q2", "affective_expression", "s2"),
    ]}
    sources = [
        source(f"s{i}", publisher="單一媒體" if i <= 5 else f"出版者{i}", domain=f"領域{i}")
        for i in range(1, 9)
    ]
    pool = {
        "selection_policy": {
            "publisher_neutral": True,
            "preferred_publishers": ["單一媒體"],
        },
        "sources": sources,
    }
    errors = validate_exam(exam, pool)
    assert any("preferred_publishers" in error for error in errors)
    assert any("占過半" in error for error in errors)
