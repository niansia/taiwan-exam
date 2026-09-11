from scripts.validate_source_grounding import printed_material


def test_long_chinese_passage_inside_prompt_is_source_bearing():
    prompt = "閱讀下文：" + "這是一段需要查明出處與命題依據的文章內容。" * 8
    text, location = printed_material({"prompt": prompt}, "國綜")
    assert text == prompt
    assert location == "prompt"


def test_split_page_material_is_not_ignored():
    question = {
        "prompt": "依據本文作答。",
        "continuation_pages": {"4": "本文在下一頁繼續，仍屬學生可見材料。"},
    }
    text, location = printed_material(question, "國綜")
    assert "下一頁繼續" in text
    assert "continuation_pages" in location


def test_natural_empirical_prompt_is_source_bearing():
    prompt = "研究者量得三組相對活性，要求學生判讀資料。"
    text, location = printed_material({"prompt": prompt}, "自然")
    assert text == prompt
    assert location == "prompt"


def test_short_concept_question_does_not_require_external_source():
    assert printed_material({"prompt": "水的化學式為何？"}, "自然") == ("", "")
