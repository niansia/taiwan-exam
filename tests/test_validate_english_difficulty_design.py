import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_english_difficulty_design.py"
SPEC = importlib.util.spec_from_file_location("english_difficulty_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def _innovation(number):
    return {
        "subject": "英文",
        "mechanism_family": f"discourse-evidence-family-{number % 7}",
        "candidate_competition_linked": True,
        "routine_template_recoverable": False,
        "surface_or_topic_novelty_only": False,
        "new_subject_mechanism": "the local choice changes a later reference and rhetorical contrast",
        "evidence_or_reasoning_architecture": "read the local fit, trace the later reference, then reconcile the contrast",
        "nearest_neighbor_difference": f"Q{number}'s nearest item lacks this later reference dependency and uses a different distractor failure",
        "reviewer_decision": "pass-subject-novelty",
    }


def _paper_innovation_review():
    return {
        "subject": "英文",
        "all_scored_items_reviewed": True,
        "mechanism_saturation_review": "pass: section mechanisms were compared",
        "representation_saturation_review": "pass: prose and visual evidence were compared",
        "section_or_domain_diversity_review": "pass: each section uses distinct operations",
        "reviewer_decision": "pass-subject-novelty",
    }


def _exam():
    questions = []
    answers = []
    answer_labels = "ABCDABCDAB"
    for number in range(1, 51):
        if 1 <= number <= 6:
            span = "cross_clause"
        elif 11 <= number <= 22:
            span = "cross_sentence"
        elif 35 <= number <= 42:
            span = "cross_paragraph"
        elif number in {43, 47, 48, 49}:
            span = "text_visual"
        else:
            span = "local_sentence"
        operations = ["locate evidence", "resolve meaning"]
        if number >= 31:
            operations.append("integrate relation")
        item_spec = {"subject_innovation_audit": _innovation(number), "english_difficulty_contract": {
            "direct_lookup_or_copy_only": False,
            "outside_vocabulary_required": False,
            "reasoning_operations": operations,
            "evidence_span": span,
            "synthesis_or_transformation": 47 <= number <= 49,
            "distractor_competition": [
                {"option": label, "initial_fit": "fits locally", "defeating_evidence": "fails wider context"}
                for label in "BCD"
            ],
        }}
        if number <= 10:
            item_spec["vocabulary_challenge"] = {
                "one_cue_shortcut_rejected": True,
                "surface_only_elimination": False,
                "two_plausible_distractors_after_local_read": True,
                "decisive_relation": "the second clause fixes the intended sense and collocation",
                "reviewed_against_recent_ceec": True,
                "band": "簡單" if number == 1 else ("中偏難" if number >= 6 else "中等"),
            }
            answers.append({"question_id": f"q{number}", "final_answer": answer_labels[number - 1]})
        questions.append({
            "id": f"q{number}", "number": number,
            "options": [{"label": label, "text": label} for label in "ABCD"],
            "item_spec": item_spec,
        })
    return {"metadata": {"subject": "英文", "subject_innovation_review": _paper_innovation_review()}, "questions": questions, "answers": answers}


def test_complete_english_reasoning_floor_passes():
    report = MODULE.validate_exam(_exam())
    assert report["status"] == "pass", report["errors"]


def test_direct_copy_item_fails():
    exam = _exam()
    exam["questions"][34]["item_spec"]["english_difficulty_contract"]["direct_lookup_or_copy_only"] = True
    report = MODULE.validate_exam(exam)
    assert any("Q35: direct lookup/copy" in error for error in report["errors"])


def test_one_cue_easy_vocabulary_design_fails_even_when_labeled_hard():
    exam = _exam()
    challenge = exam["questions"][3]["item_spec"]["vocabulary_challenge"]
    challenge["one_cue_shortcut_rejected"] = False
    challenge["band"] = "難"
    report = MODULE.validate_exam(exam)
    assert any("Q4: one-cue vocabulary shortcut" in error for error in report["errors"])


def test_vocabulary_answer_positions_cannot_all_be_the_same():
    exam = _exam()
    for answer in exam["answers"]:
        answer["final_answer"] = "A"
    report = MODULE.validate_exam(exam)
    assert any("answer-position distribution" in error for error in report["errors"])


def test_surface_only_english_novelty_claim_fails():
    exam = _exam()
    exam["questions"][20]["item_spec"]["subject_innovation_audit"]["surface_or_topic_novelty_only"] = True
    report = MODULE.validate_exam(exam)
    assert any("Q21: surface/topic-only novelty" in error for error in report["errors"])


def test_complete_english_paper_requires_paper_innovation_review():
    exam = _exam()
    del exam["metadata"]["subject_innovation_review"]
    report = MODULE.validate_exam(exam)
    assert "metadata: missing subject_innovation_review for English" in report["errors"]


def test_bare_pass_is_not_an_evidenced_paper_innovation_review():
    exam = _exam()
    exam["metadata"]["subject_innovation_review"]["mechanism_saturation_review"] = "pass"
    report = MODULE.validate_exam(exam)
    assert "metadata: English mechanism_saturation_review has not passed" in report["errors"]
