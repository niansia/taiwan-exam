import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_social_item_design.py"
SPEC = importlib.util.spec_from_file_location("social_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


DOMAIN_CODE = {
    "歷史": "歷Db-Ⅴ-3",
    "地理": "地Ab-Ⅴ-2",
    "公民與社會": "公Ac-Ⅴ-3",
}
# Rotating content codes so a 60-item fixture spreads over the 主題 bands the
# validator now requires (臺灣史／中國與東亞／世界史, 地理技能／系統／視野, 公民 A-D).
DOMAIN_CODES = {
    "歷史": ["歷Db-Ⅴ-3", "歷Ga-Ⅴ-1", "歷K-Ⅴ-1", "歷A-Ⅴ-1"],
    "地理": ["地Ab-Ⅴ-2", "地Ba-Ⅴ-1", "地Ca-Ⅴ-1", "地Bb-Ⅴ-1"],
    "公民與社會": ["公Ac-Ⅴ-3", "公Bb-Ⅴ-1", "公Ca-Ⅴ-1", "公Da-Ⅴ-1", "公Bc-Ⅴ-1"],
}
assert all(code in MODULE.ALL_CONTENT_CODES for codes in DOMAIN_CODES.values() for code in codes)


def _rotating_code(domain, qid):
    digits = "".join(ch for ch in str(qid) if ch.isdigit())
    return DOMAIN_CODES[domain][int(digits or 0) % len(DOMAIN_CODES[domain])]
DOMAIN_TARGET = {"歷史": "H3", "地理": "G3", "公民與社會": "C3"}


def _scope_contract():
    return {
        "ceec_specification_url": "https://www.ceec.edu.tw/social-spec.pdf",
        "ceec_specification_retrieved_at": "2026-09-10",
        "ceec_specification_sha256": "fixture-social-spec-sha256",
        "naer_curriculum_url": "https://stv.naer.edu.tw/social-curriculum.pdf",
        "naer_curriculum_retrieved_at": "2026-09-10",
        "naer_curriculum_sha256": "fixture-curriculum-sha256",
        "examined_spec_sections": ["測驗目標", "測驗內容", "題型配分", "試題舉例"],
    }


def _scope_fields(domain, code=None):
    code = code or DOMAIN_CODE[domain]
    return {
        "curriculum_codes": [code],
        "ceec_assessment_targets": [DOMAIN_TARGET[domain]],
        "curriculum_alignment": [{
            "content_code": code,
            "assessed_relation": "apply the required-course concept to the printed relation",
            "stimulus_evidence": "the relevant comparison is stated in the material",
            "centrality_reason": "the assessed relation is central to the cited required content",
        }],
    }


def _innovation(domain, index=0):
    return {
        "subject": "社會",
        "mechanism_family": f"{domain}-evidence-relation-{index % 5}",
        "candidate_competition_linked": True,
        "routine_template_recoverable": False,
        "surface_or_topic_novelty_only": False,
        "new_subject_mechanism": "the comparison denominator and institutional condition jointly change the warranted conclusion",
        "evidence_or_reasoning_architecture": "identify the source scope, compare the denominator, apply the institutional constraint, then judge",
        "nearest_neighbor_difference": f"item {index}'s nearest neighbor has one source and no interaction between comparison scope and institutional procedure",
        "reviewer_decision": "pass-subject-novelty",
    }


def _paper_innovation_review():
    return {
        "subject": "社會",
        "all_scored_items_reviewed": True,
        "mechanism_saturation_review": "pass: repeated policy and comparison mechanisms were screened",
        "representation_saturation_review": "pass: source, map, chart, and legal-document roles were screened",
        "section_or_domain_diversity_review": "pass: history, geography, civics, and mixed groups were reviewed",
        "reviewer_decision": "pass-subject-novelty",
    }


def _basic(qid, domain, number=None, section_id=None):
    code = _rotating_code(domain, qid)
    question = {
        "id": qid, "score": 2, "domain": domain,
        "curriculum_codes": [code],
        "item_spec": {
            "orientation": "basic", "domain": domain,
            **_scope_fields(domain, code),
        },
    }
    if number is not None:
        question["number"] = number
    if section_id is not None:
        question["section_id"] = section_id
    return question


def _competence(qid, domain, family, freshness="evergreen"):
    code = _rotating_code(domain, qid)
    return {
        "id": qid,
        "score": 2,
        "domain": domain,
        "curriculum_codes": [code],
        "item_spec": {
            "domain": domain,
            **_scope_fields(domain, code),
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
        _basic("b1", "地理"),
        _basic("b2", "公民與社會"),
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


def test_full_paper_requires_a_few_within_year_items_not_large_topical_quotas():
    questions = []
    for index in range(60):
        domain = ["歷史", "地理", "公民與社會"][index % 3]
        questions.append(_basic(
            f"b{index}", domain, index + 1,
            "objective" if index < 38 else "mixed",
        ))
    report = MODULE.validate_exam({"metadata": {"social_scope_contract": _scope_contract()}, "questions": questions})
    codes = {error["code"] for error in report["errors"]}
    assert "within_year_current_context_items_too_few" in codes
    assert not codes & {
        "current_context_score_too_low", "current_source_clusters_too_few",
        "current_context_not_distributed_to_objective",
    }


def _full_paper_with_recent_items(count=6):
    """Metadata fixture only; no generated exam content or educational acceptance."""
    questions = []
    for index in range(60):
        domain = ["歷史", "地理", "公民與社會"][index % 3]
        families = ["historical_primary_source", "map", "law_or_judgment", "statistical_chart"]
        question = _competence(f"q{index}", domain, families[index % 4])
        question["group_stimulus"] = (
            f"測試材料{index}：某地方政府同時公布基準期與政策後資料，分別列出不同地區、群體與時間點的變化。"
            "研究者提醒，總量、比例與平均值的分母不同，不能只靠單一數字判斷因果；訪談紀錄又指出執行程序、可及性與替代方案會改變政策效果。"
            "作答時須把資料的時間順序、比較口徑、適用範圍及材料未能證明的部分一併納入，並以另一項證據交叉檢查。"
            "附表另列出同期鄰近行政區的對照數值、抽樣方式與回收率，並註明兩份問卷的題目用語曾在期中修訂，"
            "因此跨期比較時須說明哪些欄位可以直接對照、哪些只能作為趨勢參考。"
        )
        question["prompt"] = "依據材料中的時間、比較口徑與證據界線，哪一項推論最能同時符合所有限制？"
        question["option_layout"] = "stack"
        question["options"] = [
            {"label": "A", "text": "只憑單一總量即可確認所有群體都受益"},
            {"label": "B", "text": "比較前後資料時仍須控制口徑並檢查替代解釋"},
            {"label": "C", "text": "只要訪談存在，量化資料便失去任何用途"},
            {"label": "D", "text": "資料涵蓋兩期即可直接證明唯一因果關係"},
        ]
        spec = question["item_spec"]
        if index >= max(count, 4):
            spec["orientation"] = "basic"
        question["section_id"] = "mixed" if index < count else "objective"
        spec["social_reasoning_contract"] = {
            "recall_only": False,
            "core_curriculum_anchor": "required-course anchor",
            "curriculum_centrality": "core",
            "cognitive_demand": "evidence_application",
            "reasoning_operations": ["read evidence", "apply concept"],
            "material_or_scenario_dependency": "the printed relation changes the answer",
        }
        spec["subject_innovation_audit"] = _innovation(domain, index)
        if index < count:
            # Two of the recent items fall inside the 180-day freshness window.
            spec.update({
                "freshness_class": "current_event", "event_date": "2026-08-01" if index < 2 else "2026-01-01",
                "published_at": "2026-01-02", "editorial_lock_date": "2026-09-10",
                "source_relation_review": {
                    "evidence_location": "row 1", "curriculum_bridge": "compare evidence",
                    "removal_counterfactual": "the comparison becomes undecidable",
                },
            })
        questions.append(question)
    # Preserve list positions used by the date tests, but number the printed
    # first-part standalones in discipline blocks, followed by mixed items.
    objective = [q for q in questions if q["section_id"] == "objective"]
    objective.sort(key=lambda q: ["歷史", "地理", "公民與社會"].index(q["item_spec"]["domain"]))
    mixed = [q for q in questions if q["section_id"] == "mixed"]
    for number, question in enumerate(objective + mixed, 1):
        question["number"] = number
    return {"metadata": {
        "social_scope_contract": _scope_contract(),
        "subject_innovation_review": _paper_innovation_review(),
    }, "questions": questions}


def _ordering_fixture(standalone_domains):
    questions = [
        {"id": f"q{i}", "number": i, "section_id": "first", "type": "single_choice",
         "item_spec": {"domain": domain}}
        for i, domain in enumerate(standalone_domains, 1)
    ]
    return {"sections": [{"id": "first", "title": "第壹部分"},
                         {"id": "second", "title": "第貳部分"}], "questions": questions}


def _append_group(exam, domains, stimulus, section="first"):
    for domain in domains:
        number = len(exam["questions"]) + 1
        exam["questions"].append({
            "id": f"q{number}", "number": number, "section_id": section,
            "type": "single_choice", "group_stimulus": stimulus,
            "item_spec": {"domain": domain},
        })


@pytest.mark.parametrize("domains", [
    ["公民與社會"] * 6 + ["歷史"] * 9 + ["地理"] * 10,
    ["歷史"] * 4 + ["地理"] * 5 + ["公民與社會"] * 3,
])
def test_standalone_blocks_allow_different_reference_orders_and_counts(domains):
    assert MODULE.objective_order_errors(_ordering_fixture(domains)) == []


def test_interleaved_standalones_fail_even_with_unique_passages():
    exam = _ordering_fixture(["歷史", "地理", "歷史", "公民與社會"])
    for question in exam["questions"]:
        question["group_stimulus"] = "unique material " + question["id"]
    assert {e["code"] for e in MODULE.objective_order_errors(exam)} == {"social_standalone_domain_interleaved"}


def test_objective_and_mixed_groups_allow_three_domains_and_single_choice_subparts():
    exam = _ordering_fixture(["公民與社會", "歷史", "地理"])
    _append_group(exam, ["歷史", "地理", "公民與社會", "歷史"], "shared objective")
    _append_group(exam, ["公民與社會", "地理", "歷史", "地理"], "shared mixed", "second")
    exam["questions"][-1]["type"] = "constructed_response"
    assert MODULE.objective_order_errors(exam) == []


def test_mixed_section_order_is_not_restricted_even_without_shared_stimulus():
    exam = _ordering_fixture(["公民與社會", "歷史", "地理"])
    _append_group(exam, ["公民與社會", "地理", "公民與社會", "歷史"], None, "second")
    assert MODULE.objective_order_errors(exam) == []


def test_objective_group_cannot_be_split_to_regroup_domains():
    exam = _ordering_fixture(["公民與社會", "歷史", "地理"])
    _append_group(exam, ["歷史", "地理"], "shared A")
    _append_group(exam, ["公民與社會", "歷史"], "shared B")
    exam["questions"][-1]["group_stimulus"] = "shared A"
    errors = MODULE.objective_order_errors(exam)
    assert "social_objective_group_split" in {e["code"] for e in errors}


def test_standalone_cannot_follow_the_objective_groups():
    exam = _ordering_fixture(["公民與社會", "歷史", "地理"])
    _append_group(exam, ["歷史", "地理"], "shared")
    _append_group(exam, ["地理"], None)
    assert "social_standalone_after_objective_groups" in {e["code"] for e in MODULE.objective_order_errors(exam)}


def test_full_paper_integration_checks_the_printed_numbers_not_array_order():
    exam = _full_paper_with_recent_items()
    assert MODULE.validate_exam(exam)["status"] == "pass"
    objective = sorted((q for q in exam["questions"] if q["section_id"] == "objective"), key=lambda q: q["number"])
    first = objective[1]
    later = next(q for q in objective if q["item_spec"]["domain"] == "地理")
    first["number"], later["number"] = later["number"], first["number"]
    assert "social_standalone_domain_interleaved" in {e["code"] for e in MODULE.validate_exam(exam)["errors"]}


@pytest.mark.parametrize("count", [6, 8, 10])
def test_small_year_old_allocation_passes_without_score_cluster_or_section_quota(count):
    report = MODULE.validate_exam(_full_paper_with_recent_items(count))
    assert report["status"] == "pass", report["errors"]
    assert report["within_year_current_context_item_count"] == count
    assert report["objective_current_source_cluster_count"] == 0


def test_two_recent_items_do_not_meet_default_few_item_floor():
    report = MODULE.validate_exam(_full_paper_with_recent_items(2))
    assert {"code": "within_year_current_context_items_too_few", "found": 2, "minimum": 6} in report["errors"]
    aged = _full_paper_with_recent_items(6)
    for question in aged["questions"][:6]:
        question["item_spec"]["event_date"] = "2026-01-01"
    assert {"code": "fresh_current_context_items_too_few", "found": 0, "minimum": 2, "window_days": 180} in MODULE.validate_exam(aged)["errors"]


@pytest.mark.parametrize("event_date,accepted", [
    ("2025-09-10", True), ("2025-09-09", False),
    ("2026-09-10", True), ("2026-09-11", False),
    ("not-a-date", False), (None, False),
])
def test_recent_event_dates_use_calendar_year_inclusive_bounds(event_date, accepted):
    exam = _full_paper_with_recent_items()
    for question in exam["questions"][2:6]:
        question["item_spec"].update({"event_date": event_date, "published_at": "2026-09-10"})
    report = MODULE.validate_exam(exam)
    assert (report["status"] == "pass") is accepted, report["errors"]
    assert report["within_year_current_context_item_count"] == (6 if accepted else 2)


def test_verified_substantive_update_can_renew_an_older_event():
    exam = _full_paper_with_recent_items()
    for question in exam["questions"][2:6]:
        question["item_spec"].update({
            "event_date": "2020-01-01", "substantive_update_date": "2026-01-01",
        })
    report = MODULE.validate_exam(exam)
    assert report["status"] == "pass", report["errors"]


@pytest.mark.parametrize("mutation,error_code", [
    ({"published_at": "2026-09-11"}, "current_source_published_after_lock"),
    ({"editorial_lock_date": "2026-09-09"}, "inconsistent_editorial_lock_dates"),
    ({"fact_check_status": "pending"}, "source_fact_check_incomplete"),
])
def test_future_source_mixed_cutoffs_and_unverified_facts_fail(mutation, error_code):
    exam = _full_paper_with_recent_items()
    exam["questions"][0]["item_spec"].update(mutation)
    report = MODULE.validate_exam(exam)
    assert error_code in {error["code"] for error in report["errors"]}


def test_leap_day_cutoff_uses_previous_february_28():
    exam = _full_paper_with_recent_items()
    for index, question in enumerate(exam["questions"][:6]):
        question["item_spec"].update({
            "event_date": "2024-02-20" if index < 2 else "2023-02-28", "published_at": "2024-02-21" if index < 2 else "2023-03-01",
            "editorial_lock_date": "2024-02-29",
        })
    report = MODULE.validate_exam(exam)
    assert report["status"] == "pass", report["errors"]


def test_full_paper_rejects_discipline_imbalance():
    questions = []
    domains = ["歷史"] * 28 + ["地理"] * 17 + ["公民與社會"] * 15
    for index, domain in enumerate(domains):
        questions.append(_basic(
            f"u{index}", domain, index + 1,
            "objective" if index < 38 else "mixed",
        ))
    report = MODULE.validate_exam({"metadata": {"social_scope_contract": _scope_contract()}, "questions": questions})
    codes = {error["code"] for error in report["errors"]}
    assert "social_discipline_item_count_imbalanced" in codes
    assert "social_discipline_score_share_imbalanced" in codes


def test_full_paper_rejects_bare_definition_and_peripheral_contracts():
    questions = []
    for index in range(60):
        domain = ["歷史", "地理", "公民與社會"][index % 3]
        question = _basic(
            f"r{index}", domain, index + 1,
            "objective" if index < 38 else "mixed",
        )
        question["item_spec"]["social_reasoning_contract"] = {
            "recall_only": False,
            "core_curriculum_anchor": "required-course anchor",
            "curriculum_centrality": "core",
            "cognitive_demand": "evidence_application",
            "reasoning_operations": ["read evidence", "apply concept"],
            "material_or_scenario_dependency": "the printed relation changes the answer",
        }
        questions.append(question)
    questions[0]["item_spec"]["social_reasoning_contract"] = {
        "recall_only": True,
        "core_curriculum_anchor": "",
        "curriculum_centrality": "peripheral",
        "cognitive_demand": "definition_recall",
        "reasoning_operations": ["remember term"],
        "material_or_scenario_dependency": "",
    }
    report = MODULE.validate_exam({"metadata": {"social_scope_contract": _scope_contract()}, "questions": questions})
    codes = {error["code"] for error in report["errors"] if error.get("question_id") == "r0"}
    assert {
        "bare_definition_or_recall_not_rejected",
        "core_curriculum_anchor_missing",
        "curriculum_target_not_central",
        "nonrecall_cognitive_demand_missing",
        "linked_reasoning_operations_too_few",
        "material_or_scenario_dependency_missing",
    } <= codes


def test_learning_performance_code_cannot_masquerade_as_learning_content_code():
    question = _competence("h", "歷史", "historical_primary_source")
    question["curriculum_codes"] = ["歷1b-Ⅴ-2"]
    question["item_spec"]["curriculum_codes"] = ["歷1b-Ⅴ-2"]
    report = MODULE.validate_exam({"questions": [
        question,
        _competence("g", "地理", "map"),
        _competence("c", "公民與社會", "law_or_judgment"),
        _competence("x", "歷史", "statistical_chart"),
    ]})
    codes = {error["code"] for error in report["errors"] if error.get("question_id") == "h"}
    assert "learning_performance_code_in_curriculum_codes" in codes
    assert "primary_domain_content_code_missing" in codes


def test_full_social_paper_rejects_surface_only_novelty_record():
    exam = _full_paper_with_recent_items()
    question = exam["questions"][10]
    question["item_spec"]["subject_innovation_audit"]["surface_or_topic_novelty_only"] = True
    report = MODULE.validate_exam(exam)
    qid = question["id"]
    assert {"code": "surface_or_topic_only_novelty_not_rejected", "question_id": qid} in report["errors"]


def test_full_social_paper_requires_paper_innovation_review():
    exam = _full_paper_with_recent_items()
    del exam["metadata"]["subject_innovation_review"]
    report = MODULE.validate_exam(exam)
    assert {"code": "subject_innovation_review_missing"} in report["errors"]


def test_stimulus_median_floor_matches_the_measured_official_envelope():
    """A 155-character median passed the old 120 floor; official years run 203-271."""
    exam = _full_paper_with_recent_items()
    for index, question in enumerate(exam["questions"]):
        question["group_stimulus"] = (
            f"測試材料{index}：某地方政府公布基準期與政策後資料，並列出不同地區與時間點的變化。"
            "研究者提醒分母不同不能只靠單一數字判斷因果，訪談紀錄也指出執行程序會改變效果。"
            "作答時須把時間順序與比較口徑一併納入。"
        )
    codes = {e["code"] for e in MODULE.validate_exam(exam)["errors"]}
    assert "social_unique_stimulus_median_too_short" in codes


def test_declared_medium_band_needs_a_third_reasoning_operation():
    """A 中/中偏難/難 label has to be earned, not just written."""
    exam = _full_paper_with_recent_items()
    target = exam["questions"][0]
    target["item_spec"]["difficulty_design"] = {"band": "中偏難"}
    errors = [e for e in MODULE.validate_exam(exam)["errors"]
              if e["code"] == "linked_reasoning_operations_too_few"]
    assert errors and errors[0]["minimum"] == 3

    target["item_spec"]["social_reasoning_contract"]["reasoning_operations"].append(
        "reconcile the two sources' comparison scope"
    )
    codes = {e["code"] for e in MODULE.validate_exam(exam)["errors"]}
    assert "linked_reasoning_operations_too_few" not in codes


def _printed_full_paper():
    """The 115 printed shape: 38 單選 in 第壹部分, 27 items in 11 題組 of 第貳部分."""
    exam = _full_paper_with_recent_items(6)
    questions = exam["questions"]
    for q in questions:
        q["type"] = "single_choice"
    extra = []
    for index in range(60, 65):
        q = _basic(f"q{index}", ["歷史", "地理", "公民與社會"][index % 3], index + 1, "mixed")
        q["type"] = "single_choice"
        extra.append(q)
    questions.extend(extra)
    objective = [q for q in questions if q["section_id"] == "objective"][:38]
    for q in questions:
        if q["section_id"] == "objective" and q not in objective:
            q["section_id"] = "mixed"
    mixed = [q for q in questions if q["section_id"] == "mixed"]
    for number, q in enumerate(objective, 1):
        q["number"] = number
    for offset, q in enumerate(mixed):
        q["number"] = 39 + offset
        q["group_stimulus"] = f"第貳部分共用材料 {offset % 11}：" + "某地方政府公布基準期與政策後資料，研究者提醒分母不同不能只看單一數字。" * 6
        if offset % 3 == 2 and q["type"] == "single_choice":
            q["type"] = "constructed_response"
            q["score"] = 3
            q.pop("options", None)
    exam["sections"] = [{"id": "objective", "title": "第壹部分、選擇題（占76分）"},
                        {"id": "mixed", "title": "第貳部分、混合題或非選擇題（占68分）"}]
    return exam


def test_printed_form_bands_measured_on_111_115_pass_and_deviations_are_named():
    exam = _printed_full_paper()
    # 115 stores 44, 46 and 52 as a checkbox record plus a reason record sharing the
    # number; the bands count printed numbers, so the extra records must not push
    # the second part or its constructed count out of band.
    for number in (44, 46, 52):
        base = next(q for q in exam["questions"] if q["number"] == number)
        base["type"] = "constructed_response"
        base.pop("options", None)
        twin = dict(base, id=f"{base['id']}-reason", subpart_id="reason", score=2)
        exam["questions"].append(twin)
    report = MODULE.validate_exam(exam)
    codes = {e["code"] for e in report["errors"]}
    assert not any(c.startswith("social_first_part") or c.startswith("social_second_part") or c.startswith("social_total") for c in codes), report["errors"]
    assert "social_curriculum_band_underrepresented" not in codes and "social_civics_themes_too_narrow" not in codes
    exam["questions"][0]["type"] = "multiple_choice"
    exam["questions"][1]["options"] = [{"label": str(i), "text": "x"} for i in range(1, 5)]
    for q in exam["questions"]:
        if q["section_id"] == "mixed" and q["type"] == "constructed_response":
            q["type"] = "single_choice"
    report = MODULE.validate_exam(exam)
    codes = {e["code"] for e in report["errors"]}
    assert {"social_multiple_choice_not_in_official_form", "social_option_labels_not_a_to_d",
            "social_second_part_constructed_outside_band", "social_second_part_single_choice_outside_band"} <= codes


def test_curriculum_breadth_requires_every_history_period_and_geography_theme():
    exam = _printed_full_paper()
    for q in exam["questions"]:
        if q["item_spec"]["domain"] == "歷史":
            q["item_spec"]["curriculum_codes"] = ["歷Db-Ⅴ-3"]
            q["curriculum_codes"] = ["歷Db-Ⅴ-3"]
        if q["item_spec"]["domain"] == "地理":
            q["item_spec"]["curriculum_codes"] = ["地Ab-Ⅴ-2"]
            q["curriculum_codes"] = ["地Ab-Ⅴ-2"]
    errors = [e for e in MODULE.validate_exam(exam)["errors"] if e["code"] == "social_curriculum_band_underrepresented"]
    assert {(e["domain"], e["band"]) for e in errors} == {("歷史", "中國與東亞"), ("歷史", "世界史"), ("地理", "地理系統"), ("地理", "地理視野")}
    # A 跨科 history item listing a geography code first still counts under its own discipline only.
    exam = _printed_full_paper()
    for q in exam["questions"]:
        if q["item_spec"]["domain"] == "歷史":
            q["item_spec"]["curriculum_codes"] = ["地Ab-Ⅴ-2"] + q["item_spec"]["curriculum_codes"]
            q["curriculum_codes"] = q["item_spec"]["curriculum_codes"]
    assert not [e for e in MODULE.validate_exam(exam)["errors"] if e["code"] == "social_curriculum_band_underrepresented"]
