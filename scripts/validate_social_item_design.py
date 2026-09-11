#!/usr/bin/env python3
"""Validate evidence design and paper balance for current GSAT social studies."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


VALID_DOMAINS = {"歷史", "地理", "公民與社會"}
VALID_SOURCE_FAMILIES = {
    "historical_primary_source", "historical_secondary_source", "archive", "map",
    "aerial_or_satellite_image", "statistical_chart", "open_data", "law_or_judgment",
    "policy_document", "research", "news", "photograph", "life_document",
    "literature_or_artifact", "synthetic_closed_scenario", "official_disaster_report",
}
VALID_COGNITIVE_DEMANDS = {
    "evidence_application", "relation_analysis", "causal_constraint",
    "comparison_judgment", "source_evaluation", "procedural_application",
    "spatial_scale_reasoning", "quantitative_evidence_reasoning",
}
INNOVATION_TEXT_FIELDS = (
    "mechanism_family",
    "new_subject_mechanism",
    "evidence_or_reasoning_architecture",
    "nearest_neighbor_difference",
)
PLACEHOLDER_INNOVATION_TEXT = {
    "n/a", "na", "none", "pending", "pass", "passed", "todo", "tbd",
    "new topic", "different context", "new mechanism", "新主題", "不同情境", "新機制", "通過",
}

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "references" / "social-required-content-codes.json"
_REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
CONTENT_CODES_BY_DOMAIN = {
    domain: {str(code) for code in codes}
    for domain, codes in (_REGISTRY.get("domains") or {}).items()
}
ALL_CONTENT_CODES = set().union(*CONTENT_CODES_BY_DOMAIN.values())
ASSESSMENT_TARGETS_BY_DOMAIN = {
    domain: {str(target) for target in targets}
    for domain, targets in (_REGISTRY.get("ceec_assessment_targets") or {}).items()
}
ALL_ASSESSMENT_TARGETS = set().union(*ASSESSMENT_TARGETS_BY_DOMAIN.values())
PERFORMANCE_CODE_RE = re.compile(r"^[歷地公]\d[a-z]-[ⅤV]-\d+$")


def canonical_content_code(value: Any) -> str:
    """Normalize harmless spacing/roman-numeral variants without changing the code."""
    return re.sub(r"\s+", "", str(value or "")).replace("-V-", "-Ⅴ-")


def _meaningful_innovation_text(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.casefold() not in PLACEHOLDER_INNOVATION_TEXT


def _evidenced_pass(value: Any) -> bool:
    text = str(value or "").strip()
    return text.startswith("pass:") and len(text.partition(":")[2].strip()) >= 8


def _subject_innovation_errors(spec: dict[str, Any], qid: str) -> list[dict[str, Any]]:
    audit = spec.get("subject_innovation_audit")
    if not isinstance(audit, dict):
        return [{"code": "subject_innovation_audit_missing", "question_id": qid}]
    errors: list[dict[str, Any]] = []
    checks = (
        (audit.get("subject") == "社會", "subject_innovation_subject_mismatch"),
        (audit.get("candidate_competition_linked") is True, "innovation_candidate_competition_not_linked"),
        (audit.get("routine_template_recoverable") is False, "routine_template_recoverability_not_rejected"),
        (audit.get("surface_or_topic_novelty_only") is False, "surface_or_topic_only_novelty_not_rejected"),
        (audit.get("reviewer_decision") == "pass-subject-novelty", "subject_innovation_review_not_passed"),
    )
    for passed, code in checks:
        if not passed:
            errors.append({"code": code, "question_id": qid})
    for field in INNOVATION_TEXT_FIELDS:
        if not _meaningful_innovation_text(audit.get(field)):
            errors.append({
                "code": "subject_innovation_evidence_missing_or_placeholder",
                "question_id": qid,
                "field": field,
            })
    return errors


def _paper_innovation_errors(exam: dict[str, Any]) -> list[dict[str, Any]]:
    review = (exam.get("metadata") or {}).get("subject_innovation_review")
    if not isinstance(review, dict):
        return [{"code": "subject_innovation_review_missing"}]
    errors: list[dict[str, Any]] = []
    if review.get("subject") != "社會":
        errors.append({"code": "subject_innovation_review_subject_mismatch"})
    if review.get("all_scored_items_reviewed") is not True:
        errors.append({"code": "subject_innovation_review_incomplete"})
    for field in (
        "mechanism_saturation_review",
        "representation_saturation_review",
        "section_or_domain_diversity_review",
    ):
        if not _evidenced_pass(review.get(field)):
            errors.append({"code": "subject_innovation_paper_review_not_passed", "field": field})
    if review.get("reviewer_decision") != "pass-subject-novelty":
        errors.append({"code": "subject_innovation_paper_decision_not_passed"})
    return errors


def _scope_contract_errors(exam: dict[str, Any]) -> list[dict[str, Any]]:
    contract = (exam.get("metadata") or {}).get("social_scope_contract")
    if not isinstance(contract, dict):
        return [{"code": "social_scope_contract_missing"}]
    errors: list[dict[str, Any]] = []
    for field in (
        "ceec_specification_url", "ceec_specification_retrieved_at",
        "ceec_specification_sha256", "naer_curriculum_url",
        "naer_curriculum_retrieved_at", "naer_curriculum_sha256",
    ):
        if not str(contract.get(field) or "").strip():
            errors.append({"code": "social_scope_source_evidence_missing", "field": field})
    sections = {str(value) for value in (contract.get("examined_spec_sections") or [])}
    required_sections = {"測驗目標", "測驗內容", "題型配分", "試題舉例"}
    if not required_sections <= sections:
        errors.append({
            "code": "social_specification_sections_not_reviewed",
            "missing": sorted(required_sections - sections),
        })
    return errors


def objective_order_errors(exam: dict[str, Any]) -> list[dict[str, Any]]:
    """Check standalone blocks only; a mixed-section choice is not a standalone.

    Exact annual counts/order still require the selected reference review. Shared
    material is identified in the same way as the renderer, not by domain tags.
    """
    errors: list[dict[str, Any]] = []
    questions = [q for q in exam.get("questions", []) if isinstance(q, dict)]
    sections = exam.get("sections") or []
    if sections and isinstance(sections[0], dict):
        objective_id = sections[0].get("id")
    else:
        # Older metadata-only records use these explicit first-part ids.
        section_ids = {q.get("section_id") for q in questions}
        objective_id = next((s for s in ("objective", "section-1") if s in section_ids), None)
    if not objective_id:
        return [{"code": "social_objective_section_unresolved"}]
    ordered = sorted(enumerate(questions), key=lambda pair: pair[1].get("number", pair[0] + 1))
    objective = [q for _, q in ordered if q.get("section_id") == objective_id]
    if not objective:
        return [{"code": "social_objective_section_empty", "section_id": objective_id}]
    stimuli = Counter(q.get("group_stimulus") for q in objective if q.get("group_stimulus"))
    closed_domains: set[str] = set()
    seen_groups: set[str] = set()
    last_domain = None
    last_group = None
    groups_started = False
    for q in objective:
        qid = str(q.get("id") or q.get("number") or "unknown")
        stimulus = q.get("group_stimulus")
        if stimulus and stimuli[stimulus] > 1:
            groups_started = True
            if stimulus != last_group and stimulus in seen_groups:
                errors.append({"code": "social_objective_group_split", "question_id": qid})
            seen_groups.add(stimulus)
            last_group = stimulus
            continue
        last_group = None
        if groups_started:
            errors.append({"code": "social_standalone_after_objective_groups", "question_id": qid})
        spec = q.get("item_spec") if isinstance(q.get("item_spec"), dict) else {}
        domain = spec.get("domain") or q.get("domain")
        if domain not in VALID_DOMAINS:
            continue  # The item-level domain check supplies the error.
        if domain != last_domain:
            if domain in closed_domains:
                errors.append({"code": "social_standalone_domain_interleaved", "question_id": qid, "domain": domain})
            if last_domain is not None:
                closed_domains.add(last_domain)
            last_domain = domain
    return errors


def validate_exam(exam: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    domains: Counter[str] = Counter()
    domain_item_counts: Counter[str] = Counter()
    source_families: Counter[str] = Counter()
    current_items = 0
    within_year_items = 0
    editorial_lock_dates: set[date] = set()
    current_score = 0.0
    current_clusters: set[tuple[str, ...]] = set()
    objective_current_clusters: set[tuple[str, ...]] = set()
    competence_items = 0
    basic_items = 0
    full_current_paper = len(exam.get("questions") or []) >= 60
    questions = [q for q in (exam.get("questions") or []) if isinstance(q, dict)]
    unique_stimuli = {
        str(q.get("group_stimulus") or "").strip()
        for q in questions
        if str(q.get("group_stimulus") or "").strip()
    }
    stimulus_lengths = [len(re.sub(r"\s+", "", text)) for text in unique_stimuli]
    prompt_chars = sum(len(re.sub(r"\s+", "", str(q.get("prompt") or ""))) for q in questions)
    evidence_text_chars = sum(stimulus_lengths) + prompt_chars
    option_chars = sum(
        len(re.sub(r"\s+", "", str(option.get("text") or "")))
        for q in questions for option in (q.get("options") or []) if isinstance(option, dict)
    )
    printable_surface_chars = evidence_text_chars + option_chars
    median_stimulus_chars = statistics.median(stimulus_lengths) if stimulus_lengths else 0
    short_stimulus_ratio = (
        sum(length < 110 for length in stimulus_lengths) / len(stimulus_lengths)
        if stimulus_lengths else 1.0
    )

    if full_current_paper:
        errors.extend(_scope_contract_errors(exam))
        if evidence_text_chars < 7500:
            errors.append({
                "code": "social_evidence_text_volume_too_low",
                "found": evidence_text_chars,
                "minimum": 7500,
                "detail": "計數含每份共用材料一次及所有題幹，不含選項、解析與隱藏 metadata。",
            })
        if printable_surface_chars < 11000:
            errors.append({
                "code": "social_printable_surface_volume_too_low",
                "found": printable_surface_chars,
                "minimum": 11000,
            })
        if median_stimulus_chars < 120:
            errors.append({
                "code": "social_unique_stimulus_median_too_short",
                "found": median_stimulus_chars,
                "minimum": 120,
            })
        if short_stimulus_ratio > 0.40:
            errors.append({
                "code": "social_short_materials_dominate",
                "found_ratio": round(short_stimulus_ratio, 3),
                "maximum": 0.40,
            })

    for question in exam.get("questions", []):
        if not isinstance(question, dict):
            continue
        qid = str(question.get("id") or question.get("number") or "unknown")
        if question.get("options") and question.get("option_layout") != "stack":
            errors.append({"code": "social_options_not_stacked", "question_id": qid})
        spec = question.get("item_spec") if isinstance(question.get("item_spec"), dict) else {}
        if question.get("visual_asset"):
            visible_text = f'{question.get("group_stimulus") or ""}\n{question.get("prompt") or ""}'
            if "照片：" in visible_text or "Photo:" in visible_text:
                errors.append({"code": "photo_credit_printed_in_student_booklet", "question_id": qid})
        domain = str(spec.get("domain") or question.get("domain") or "")
        if domain not in VALID_DOMAINS:
            errors.append({"code": "social_domain_missing", "question_id": qid})
        else:
            domains[domain] += float(question.get("score") or 1)
            domain_item_counts[domain] += 1
        curriculum_codes = spec.get("curriculum_codes") or question.get("curriculum_codes") or []
        if not curriculum_codes:
            errors.append({"code": "curriculum_code_missing", "question_id": qid})
        canonical_codes = [canonical_content_code(code) for code in curriculum_codes]
        for raw_code, code in zip(curriculum_codes, canonical_codes):
            if PERFORMANCE_CODE_RE.fullmatch(code):
                errors.append({
                    "code": "learning_performance_code_in_curriculum_codes",
                    "question_id": qid,
                    "value": str(raw_code),
                    "detail": "curriculum_codes 只能放高一、高二必修學習內容碼；學習表現須另列。",
                })
            elif code not in ALL_CONTENT_CODES:
                errors.append({
                    "code": "curriculum_content_code_invalid",
                    "question_id": qid,
                    "value": str(raw_code),
                })
        if domain in VALID_DOMAINS and not (set(canonical_codes) & CONTENT_CODES_BY_DOMAIN[domain]):
            errors.append({
                "code": "primary_domain_content_code_missing",
                "question_id": qid,
                "domain": domain,
            })

        assessment_targets = [str(target) for target in (spec.get("ceec_assessment_targets") or [])]
        if full_current_paper and not assessment_targets:
            errors.append({"code": "ceec_assessment_target_missing", "question_id": qid})
        for target in assessment_targets:
            if target not in ALL_ASSESSMENT_TARGETS:
                errors.append({
                    "code": "ceec_assessment_target_invalid",
                    "question_id": qid,
                    "value": target,
                })
        allowed_targets = ASSESSMENT_TARGETS_BY_DOMAIN.get(domain, set()) | ASSESSMENT_TARGETS_BY_DOMAIN.get("跨科", set())
        if assessment_targets and not (set(assessment_targets) & allowed_targets):
            errors.append({
                "code": "ceec_assessment_target_domain_mismatch",
                "question_id": qid,
                "domain": domain,
            })

        if full_current_paper:
            alignment = spec.get("curriculum_alignment")
            if not isinstance(alignment, list):
                alignment = []
            aligned_codes: set[str] = set()
            for record in alignment:
                if not isinstance(record, dict):
                    continue
                aligned_codes.add(canonical_content_code(record.get("content_code")))
                if not all(str(record.get(field) or "").strip() for field in
                           ("assessed_relation", "stimulus_evidence", "centrality_reason")):
                    errors.append({
                        "code": "curriculum_alignment_evidence_incomplete",
                        "question_id": qid,
                        "content_code": record.get("content_code"),
                    })
            for code in canonical_codes:
                if code in ALL_CONTENT_CODES and code not in aligned_codes:
                    errors.append({
                        "code": "curriculum_alignment_record_missing",
                        "question_id": qid,
                        "content_code": code,
                    })

        if full_current_paper:
            contract = spec.get("social_reasoning_contract")
            if not isinstance(contract, dict):
                errors.append({"code": "social_reasoning_contract_missing", "question_id": qid})
                contract = {}
            if contract.get("recall_only") is not False:
                errors.append({"code": "bare_definition_or_recall_not_rejected", "question_id": qid})
            if not str(contract.get("core_curriculum_anchor") or "").strip():
                errors.append({"code": "core_curriculum_anchor_missing", "question_id": qid})
            if contract.get("curriculum_centrality") not in {"core", "high-frequency"}:
                errors.append({"code": "curriculum_target_not_central", "question_id": qid})
            if contract.get("cognitive_demand") not in VALID_COGNITIVE_DEMANDS:
                errors.append({"code": "nonrecall_cognitive_demand_missing", "question_id": qid})
            operations = contract.get("reasoning_operations") or spec.get("reasoning_operations") or []
            if not isinstance(operations, list) or len(operations) < 2:
                errors.append({"code": "linked_reasoning_operations_too_few", "question_id": qid, "minimum": 2})
            dependency = contract.get("material_or_scenario_dependency")
            if not str(dependency or "").strip():
                errors.append({"code": "material_or_scenario_dependency_missing", "question_id": qid})
            errors.extend(_subject_innovation_errors(spec, qid))

        orientation = spec.get("orientation") or "basic"
        if orientation == "basic":
            basic_items += 1
            continue
        competence_items += 1
        source_family = str(spec.get("source_family") or "")
        if source_family not in VALID_SOURCE_FAMILIES:
            errors.append({"code": "source_family_missing_or_invalid", "question_id": qid})
        else:
            source_families[source_family] += 1
        for field in ("source_ids", "evidence_targets", "reasoning_operations"):
            if not spec.get(field):
                errors.append({"code": f"{field}_missing", "question_id": qid})
        if spec.get("stimulus_required") is not True or spec.get("stimulus_removal_test") != "fail_without_stimulus":
            errors.append({"code": "stimulus_necessity_not_proven", "question_id": qid})
        if spec.get("external_knowledge_required") is not False:
            errors.append({"code": "external_news_knowledge_may_be_required", "question_id": qid})
        if spec.get("fact_check_status") != "verified":
            errors.append({"code": "source_fact_check_incomplete", "question_id": qid})
        if spec.get("freshness_class") in {"current_event", "recent_context"}:
            current_items += 1
            current_score += float(question.get("score") or 1)
            cluster = tuple(sorted(str(value) for value in (spec.get("source_ids") or [])))
            if cluster:
                current_clusters.add(cluster)
                if question.get("section_id") == "objective":
                    objective_current_clusters.add(cluster)
            if not spec.get("published_at") or not spec.get("editorial_lock_date"):
                errors.append({"code": "current_source_dates_missing", "question_id": qid})
            try:
                published = date.fromisoformat(str(spec.get("published_at") or ""))
                lock = date.fromisoformat(str(spec.get("editorial_lock_date") or ""))
                editorial_lock_dates.add(lock)
                if published > lock:
                    errors.append({"code": "current_source_published_after_lock", "question_id": qid})
                relevant_date = spec.get("substantive_update_date") or spec.get("event_date")
                if relevant_date:
                    happened = date.fromisoformat(str(relevant_date))
                    try:
                        year_start = lock.replace(year=lock.year - 1)
                    except ValueError:  # February 29 has no counterpart in the previous year.
                        year_start = date(lock.year - 1, 2, 28)
                    if happened > lock:
                        errors.append({"code": "current_event_after_lock", "question_id": qid})
                    elif published <= lock and year_start <= happened and spec.get("fact_check_status") == "verified":
                        within_year_items += 1
                else:
                    warnings.append({"code": "current_event_date_missing_not_counted_within_year", "question_id": qid})
            except (ValueError, TypeError):
                errors.append({"code": "current_source_date_invalid", "question_id": qid})
            relation_review = spec.get("source_relation_review") or {}
            relation_supported = all(relation_review.get(key) for key in
                                     ("evidence_location", "curriculum_bridge", "removal_counterfactual"))
            if not relation_supported and spec.get("proper_noun_substitution_test") != "mechanism_changes":
                errors.append({"code": "topical_name_is_decorative", "question_id": qid})
            if not relation_supported:
                warnings.append({"code": "source_relation_review_not_evidenced", "question_id": qid})
        if spec.get("source_family") == "news" and not spec.get("primary_fact_source_ids"):
            errors.append({"code": "news_is_sole_factual_authority", "question_id": qid})

    if set(domains) != VALID_DOMAINS:
        errors.append({"code": "paper_missing_social_discipline", "found": sorted(domains)})
    total_score = sum(domains.values())
    if total_score:
        for domain, score in domains.items():
            share = score / total_score
            if share < 0.25 or share > 0.42:
                warnings.append({"code": "discipline_score_share_review", "domain": domain, "share": round(share, 4)})
    if competence_items and len(source_families) < 4:
        errors.append({"code": "source_ecology_too_narrow", "source_families": dict(source_families)})
    if current_items and basic_items == 0:
        errors.append({"code": "paper_is_all_topical_no_basic_anchor"})
    if full_current_paper:
        errors.extend(_paper_innovation_errors(exam))
        nearest_differences = [
            str((((q.get("item_spec") or {}).get("subject_innovation_audit") or {}).get("nearest_neighbor_difference") or "")).strip()
            for q in questions
        ]
        repeated_nearest = {
            value: count for value, count in Counter(nearest_differences).items()
            if value and count > 1
        }
        if repeated_nearest:
            errors.append({
                "code": "subject_innovation_nearest_neighbor_text_reused",
                "duplicate_count": sum(repeated_nearest.values()),
            })
        errors.extend(objective_order_errors(exam))
        item_values = [domain_item_counts[name] for name in sorted(VALID_DOMAINS)]
        if max(item_values) - min(item_values) > 3:
            errors.append({
                "code": "social_discipline_item_count_imbalanced",
                "counts": dict(domain_item_counts),
                "maximum_allowed_gap": 3,
            })
        score_shares = {name: domains[name] / total_score for name in VALID_DOMAINS} if total_score else {}
        if score_shares and max(score_shares.values()) - min(score_shares.values()) > 0.08:
            errors.append({
                "code": "social_discipline_score_share_imbalanced",
                "shares": {name: round(score_shares[name], 4) for name in sorted(score_shares)},
                "maximum_allowed_gap": 0.08,
            })
        if within_year_items < 3:
            errors.append({"code": "within_year_current_context_items_too_few", "found": within_year_items, "minimum": 3})
        if len(editorial_lock_dates) > 1:
            errors.append({"code": "inconsistent_editorial_lock_dates"})

    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "release_status": "editorial-evidence-review-required",
        "domain_score_counts": dict(domains),
        "domain_item_counts": dict(domain_item_counts),
        "source_family_counts": dict(source_families),
        "competence_item_count": competence_items,
        "basic_item_count": basic_items,
        "current_context_item_count": current_items,
        "within_year_current_context_item_count": within_year_items,
        "current_context_score": current_score,
        "current_source_cluster_count": len(current_clusters),
        "objective_current_source_cluster_count": len(objective_current_clusters),
        "unique_stimulus_count": len(unique_stimuli),
        "unique_stimulus_chars": sum(stimulus_lengths),
        "median_unique_stimulus_chars": median_stimulus_chars,
        "short_stimulus_ratio": round(short_stimulus_ratio, 3),
        "evidence_text_chars": evidence_text_chars,
        "printable_surface_chars": printable_surface_chars,
        "errors": errors,
        "warnings": warnings,
        "notes": [
            "本工具只檢查設計欄位；不認證來源真實性、素養程度或原創性。計數是作者宣告值，不是逐題複核後的已驗證值。",
            "curriculum_codes 必須是國教院社會領綱高一、高二部定必修的學習內容碼；歷1b-Ⅴ-2 這類學習表現碼不得混充。",
            "完整卷還必須以 H/G/C/S 測驗目標碼另列能力層，並為每個學習內容碼說明實際得分關係、材料證據與核心性。",
            "25%–42% 為跨年度組卷警示帶，不取代所選正式年度的科別配分。",
            "完整卷的歷史、地理、公民題數差不得超過 3，配分占比差不得超過 8 個百分點。",
            "第一部分獨立單題按科連續；共用材料題組及整個第二部分不受此限制，可真正跨科。精確年度區塊題數與順序仍須核對正式參考卷。",
            "完整卷每題均須通過反純定義與課綱核心性契約；僅有課綱代碼不構成通過。",
            "完整卷每題另須通過社會科創新命題稽核；新地名、年份、政策名稱、圖片或來源不能替代新的證據與推理結構。",
            "社會完整卷另以內部反短材料門檻檢查可見證據量與獨立材料中位長度；這些值是退件下限，不是要求逐題灌字或冒充大考中心統計。",
            "時事只提供證據情境；題目不得要求考生事先知道新聞。",
            "完整卷預設只要求至少 3 題依賴截稿日前一年內的事件或實質更新；其餘選材不設新鮮度、時事配分或分區配額。日期計數仍須來源及內容複核。",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exam_json", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam_json.read_text(encoding="utf-8-sig"))
    report = validate_exam(exam)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
