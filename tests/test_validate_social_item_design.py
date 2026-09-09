import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_social_item_design.py"
SPEC = importlib.util.spec_from_file_location("social_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def _competence(qid, domain, family, freshness="evergreen"):
    return {
        "id": qid,
        "score": 2,
        "domain": domain,
        "curriculum_codes": ["code"],
        "item_spec": {
            "domain": domain,
            "curriculum_codes": ["code"],
            "orientation": "competence",
            "source_family": family,
            "source_ids": [qid + "-s"],
            "evidence_targets": ["row 1"],
            "reasoning_operations": ["infer"],
            "stimulus_required": True,
            "stimulus_removal_test": "fail_without_stimulus",
            "external_knowledge_required": False,
            "fact_check_status": "verified",
            "freshness_class": freshness,
        },
    }


def test_balanced_evidence_design_passes():
    questions = [
        _competence("h", "歷史", "historical_primary_source"),
        _competence("g", "地理", "map"),
        _competence("c", "公民與社會", "law_or_judgment"),
        _competence("x", "歷史", "statistical_chart"),
        {"id": "b1", "score": 2, "domain": "地理", "curriculum_codes": ["code"], "item_spec": {"orientation": "basic", "domain": "地理", "curriculum_codes": ["code"]}},
        {"id": "b2", "score": 2, "domain": "公民與社會", "curriculum_codes": ["code"], "item_spec": {"orientation": "basic", "domain": "公民與社會", "curriculum_codes": ["code"]}},
    ]
    report = MODULE.validate_exam({"questions": questions})
    assert report["status"] == "pass"


def test_news_without_primary_source_fails():
    q = _competence("n", "歷史", "news", "current_event")
    q["item_spec"].update({
        "published_at": "2026-01-01",
        "editorial_lock_date": "2026-06-01",
        "proper_noun_substitution_test": "mechanism_changes",
    })
    questions = [q, _competence("g", "地理", "map"), _competence("c", "公民與社會", "law_or_judgment"), _competence("x", "歷史", "statistical_chart")]
    report = MODULE.validate_exam({"questions": questions})
    assert any(error["code"] == "news_is_sole_factual_authority" for error in report["errors"])


def test_full_paper_requires_current_clusters_in_objective_part():
    questions = []
    for index in range(60):
        domain = ["歷史", "地理", "公民與社會"][index % 3]
        questions.append({
            "id": f"b{index}", "number": index + 1, "score": 2,
            "section_id": "objective" if index < 38 else "mixed",
            "item_spec": {"orientation": "basic", "domain": domain, "curriculum_codes": ["code"]},
        })
    report = MODULE.validate_exam({"questions": questions})
    codes = {error["code"] for error in report["errors"]}
    assert "current_context_score_too_low" in codes
    assert "current_source_clusters_too_few" in codes
    assert "current_context_not_distributed_to_objective" in codes
