import importlib.util
from collections import Counter
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_english_vocabulary_scope.py"
SPEC = importlib.util.spec_from_file_location("english_vocab_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_ten_vocabulary_answer_positions_allow_only_three_three_two_two():
    assert MODULE.answer_positions_balanced(Counter({"A": 3, "B": 3, "C": 2, "D": 2}))


def test_ten_vocabulary_answer_positions_reject_four_three_two_one():
    assert not MODULE.answer_positions_balanced(Counter({"A": 4, "B": 3, "C": 2, "D": 1}))


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
            "options": [
                {"label": label, "text": text}
                for label, text in zip("ABCD", ["hasty", "tight", "diligent", "routine"])
            ],
            "item_spec": {"lexical_scope": {
                "target_word": "tight", "target_surface_form": "tight", "target_pos": "adj.",
                "option_pos": ["adj.", "adj.", "adj.", "adj."],
                "disambiguating_evidence": ["tight schedule", "limited time"],
                "distractor_confusion_basis": [
                    {
                        "option": "A", "surface_form": "hasty", "competition_type": "semantic_prosody",
                        "slot_feasible": True, "initial_fit": "can describe rushed planning",
                        "defeating_evidence": "the sentence describes limited capacity, not careless speed",
                        "plausibility_after_local_read": "high",
                    },
                    {
                        "option": "C", "surface_form": "diligent", "competition_type": "near_synonym",
                        "slot_feasible": True, "initial_fit": "can describe a demanding work routine",
                        "defeating_evidence": "diligent describes a person or effort, not a schedule's capacity",
                        "plausibility_after_local_read": "medium",
                    },
                    {
                        "option": "D", "surface_form": "routine", "competition_type": "collocation",
                        "slot_feasible": True, "initial_fit": "can modify an activity done regularly",
                        "defeating_evidence": "regularity does not express the limited time indicated here",
                        "plausibility_after_local_read": "medium",
                    },
                ],
            }},
        }],
        "answers": [{
            "question_id": "q1", "final_answer": "B",
            "lexical_explanation": {
                "selected_option_label": "B", "selected_surface_form": "tight",
                "evidence_cues": ["daily schedule", "limited time"],
                "context_fit": "tight collocates with schedule and expresses limited available time",
            },
            "reasoning": ["The exact answer is tight because a tight schedule leaves little free time."],
        }],
    }
    report = MODULE.validate_exam(exam, index)
    assert report["status"] == "pass", report["errors"]


def test_explanation_cannot_replace_printed_surface_form_with_related_or_synonymous_word():
    index = {
        word: [{"entry": word, "pos": "adj.", "level": 4}]
        for word in ("determined", "patient", "careful", "hopeful")
    }
    exam = {
        "sections": [{"id": "vocabulary", "title": "詞彙題"}],
        "questions": [{
            "id": "q4", "section_id": "vocabulary", "prompt": "She remained determined after two rejections.",
            "options": [
                {"label": label, "text": text}
                for label, text in zip("ABCD", ["determined", "patient", "careful", "hopeful"])
            ],
            "item_spec": {"lexical_scope": {
                "target_word": "determined", "target_surface_form": "determined", "target_pos": "adj.",
                "option_pos": ["adj."] * 4,
                "disambiguating_evidence": ["remained", "after two rejections"],
                "distractor_confusion_basis": [
                    {"option": label, "surface_form": text, "competition_type": kind,
                     "slot_feasible": True, "initial_fit": "describes a positive response",
                     "defeating_evidence": "does not express persistence after rejection",
                     "plausibility_after_local_read": "medium"}
                    for label, text, kind in zip(
                        "BCD", ["patient", "careful", "hopeful"],
                        ["near_synonym", "semantic_prosody", "register"],
                    )
                ],
            }},
        }],
        "answers": [{
            "question_id": "q4", "final_answer": "A",
            "lexical_explanation": {
                "selected_option_label": "A", "selected_surface_form": "determination",
                "evidence_cues": ["remained", "after two rejections"],
                "context_fit": "Continuing after rejection shows determination.",
            },
            "reasoning": ["Continuing after rejection shows determination."],
        }],
    }
    report = MODULE.validate_exam(exam, index)
    codes = {error["code"] for error in report["errors"]}
    assert "vocabulary_explanation_surface_form_mismatch" in codes
    assert "vocabulary_rendered_explanation_omits_selected_surface_form" in codes


def test_explanation_cannot_swap_disrupted_for_interrupted():
    index = {
        word: [{"entry": word, "pos": "v.", "level": 4}]
        for word in ("disrupted", "delayed", "revised", "followed")
    }
    exam = {
        "sections": [{"id": "vocabulary", "title": "詞彙題"}],
        "questions": [{
            "id": "q5", "section_id": "vocabulary", "prompt": "The storm disrupted the original plan.",
            "options": [
                {"label": label, "text": text}
                for label, text in zip("ABCD", ["disrupted", "delayed", "revised", "followed"])
            ],
            "item_spec": {"lexical_scope": {
                "target_word": "disrupted", "target_surface_form": "disrupted", "target_pos": "v.",
                "option_pos": ["v."] * 4,
                "disambiguating_evidence": ["storm", "original plan"],
                "distractor_confusion_basis": [
                    {"option": label, "surface_form": text, "competition_type": kind,
                     "slot_feasible": True, "initial_fit": "can relate to a plan",
                     "defeating_evidence": "does not capture the storm breaking the planned sequence",
                     "plausibility_after_local_read": "medium"}
                    for label, text, kind in zip(
                        "BCD", ["delayed", "revised", "followed"],
                        ["near_synonym", "collocation", "semantic_prosody"],
                    )
                ],
            }},
        }],
        "answers": [{
            "question_id": "q5", "final_answer": "A",
            "lexical_explanation": {
                "selected_option_label": "A", "selected_surface_form": "interrupted",
                "evidence_cues": ["storm", "original plan"],
                "context_fit": "The delay interrupted the original plan.",
            },
            "reasoning": ["The delay interrupted the original plan."],
        }],
    }
    report = MODULE.validate_exam(exam, index)
    codes = {error["code"] for error in report["errors"]}
    assert "vocabulary_explanation_surface_form_mismatch" in codes
    assert "vocabulary_rendered_explanation_omits_selected_surface_form" in codes


OFFICIAL_115_TARGETS = ["tight", "amateur", "vacancy", "initially", "consumption", "dreads", "passion", "assaulted", "elbow", "grave"]


def _paper_with_targets(index, targets):
    questions, answers = [], []
    for n, word in enumerate(targets, 1):
        questions.append({"id": f"q{n}", "section_id": "v", "prompt": f"The {word} example sentence number {n} for the test.",
                          "options": [{"label": l, "text": t} for l, t in zip("ABCD", [word, "table", "window", "garden"])],
                          "item_spec": {"lexical_scope": {"target_word": word, "target_surface_form": word, "target_pos": "n.",
                                                          "option_pos": ["n."] * 4, "disambiguating_evidence": ["a", "b"],
                                                          "distractor_confusion_basis": [
                                                              {"option": l, "surface_form": t, "competition_type": k, "slot_feasible": True,
                                                               "initial_fit": "fits", "defeating_evidence": "fails", "plausibility_after_local_read": "medium"}
                                                              for l, t, k in zip("BCD", ["table", "window", "garden"], ["near_synonym", "collocation", "word_family_or_form"])]}}})
        answers.append({"question_id": f"q{n}", "final_answer": "A",
                        "lexical_explanation": {"selected_option_label": "A", "selected_surface_form": word, "evidence_cues": ["a", "b"], "context_fit": "fits"},
                        "reasoning": [f"The answer is {word}."]})
    for i, a in enumerate(answers):  # spread the printed key over A-D as the official papers do
        label = "ABCD"[i % 4]
        q = questions[i]
        q["options"][0]["label"], q["options"][i % 4]["label"] = label, "A"
        a["final_answer"] = label
        a["lexical_explanation"]["selected_option_label"] = label
    return {"sections": [{"id": "v", "title": "一、詞彙題（占10分）"}], "questions": questions, "answers": answers}


def test_shipped_ceec_list_loads_and_official_115_targets_pass_the_level_rules():
    index = MODULE.load_reference()
    assert 6000 < len(index) < 9000
    assert MODULE.resolve_token("abandon", index)[1][0]["level"] == 4
    assert MODULE.resolve_token("brought", index)[0] == "bring"
    report = MODULE.validate_exam(_paper_with_targets(index, OFFICIAL_115_TARGETS), index)
    codes = {e["code"] for e in report["errors"]}
    assert not any(c.startswith("vocabulary_target") or c.endswith("rate_too_high") or c == "unjustified_level_6_nonreading" for c in codes), report["errors"]
    assert report["vocabulary_target_level_counts"] == {3: 3, 4: 4, 5: 2, 6: 1}
    two_level_six = MODULE.validate_exam(_paper_with_targets(index, OFFICIAL_115_TARGETS[:-1] + ["randomly"]), index)
    assert "vocabulary_target_level_6_more_than_one" in {e["code"] for e in two_level_six["errors"]}
    all_easy = MODULE.validate_exam(_paper_with_targets(index, ["table", "window", "garden", "apple", "water", "house", "school", "mother", "father", "book"]), index)
    assert "vocabulary_target_level_mix_too_low" in {e["code"] for e in all_easy["errors"]}


def test_off_list_tokens_are_a_rate_not_a_per_word_veto():
    index = MODULE.load_reference()
    words = ["the", "students", "read", "carefully", "before", "answering"] * 10 + ["Picasso", "don't", "well-known", "zebrafish"]
    exam = {"sections": [{"id": "c", "title": "二、綜合測驗（占10分）"}],
            "questions": [{"id": "q11", "section_id": "c", "group_stimulus": " ".join(words), "options": []}]}
    report = MODULE.validate_exam(exam, index)
    assert not any(e["code"] == "nonreading_off_list_rate_too_high" for e in report["errors"]), report["errors"]
    assert any(w["code"] == "off_list_token" and w["token"] == "zebrafish" for w in report["warnings"])
    flooded = {"sections": exam["sections"], "questions": [{"id": "q11", "section_id": "c", "group_stimulus": " ".join(["students", "read"] * 20 + ["zebrafish", "judoka", "savannah", "neurotransmitter"] * 2), "options": []}]}
    assert any(e["code"] == "nonreading_off_list_rate_too_high" for e in MODULE.validate_exam(flooded, index)["errors"])


def test_completion_bank_words_come_from_the_list_with_some_level_four_plus():
    index = MODULE.load_reference()
    official_115 = "(A) retain (B) depend on (C) atmosphere (D) delay (E) unproductive (F) risk (G) function (H) minimal (I) dramatic (J) point to"
    exam = {"sections": [{"id": "t", "title": "三、文意選填（占10分）"}],
            "questions": [{"id": "q21", "section_id": "t", "group_stimulus": "A passage with [[21]] gaps.\n\n" + official_115, "options": []}]}
    assert not any(e["code"].startswith("completion_bank") for e in MODULE.validate_exam(exam, index)["errors"])
    easy = exam["questions"][0]["group_stimulus"].replace(official_115, "(A) table (B) window (C) garden (D) apple (E) water (F) house (G) school (H) mother (I) father (J) book")
    exam["questions"][0]["group_stimulus"] = easy
    assert any(e["code"] == "completion_bank_too_easy" for e in MODULE.validate_exam(exam, index)["errors"])
    exam["questions"][0]["group_stimulus"] = easy.replace("(A) table (B) window", "(A) zzzzq (B) qqzzx")
    assert any(e["code"] == "completion_bank_off_list" for e in MODULE.validate_exam(exam, index)["errors"])


def test_nonreading_level_six_fails():
    index = {"arcane": [{"entry": "arcane", "pos": "adj.", "level": 6}]}
    exam = {
        "sections": [{"id": "c", "title": "綜合測驗"}],
        "questions": [{"id": "q", "section_id": "c", "prompt": "arcane", "options": []}],
    }
    report = MODULE.validate_exam(exam, index)
    assert any(error["code"] == "unjustified_level_6_nonreading" for error in report["errors"])
