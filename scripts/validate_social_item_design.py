#!/usr/bin/env python3
"""Validate evidence design and paper balance for current GSAT social studies."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


VALID_DOMAINS = {"歷史", "地理", "公民與社會"}
VALID_SOURCE_FAMILIES = {
    "historical_primary_source", "historical_secondary_source", "archive", "map",
    "aerial_or_satellite_image", "statistical_chart", "open_data", "law_or_judgment",
    "policy_document", "research", "news", "photograph", "life_document",
    "literature_or_artifact", "synthetic_closed_scenario", "official_disaster_report",
}


def validate_exam(exam: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    domains: Counter[str] = Counter()
    source_families: Counter[str] = Counter()
    current_items = 0
    current_score = 0.0
    current_clusters: set[tuple[str, ...]] = set()
    objective_current_clusters: set[tuple[str, ...]] = set()
    competence_items = 0
    basic_items = 0

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
        curriculum_codes = spec.get("curriculum_codes") or question.get("curriculum_codes") or []
        if not curriculum_codes:
            errors.append({"code": "curriculum_code_missing", "question_id": qid})

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
    full_current_paper = len(exam.get("questions") or []) >= 60
    if full_current_paper:
        if current_items < 24:
            errors.append({"code": "current_context_items_too_few", "found": current_items, "minimum": 24})
        if current_score < 24:
            errors.append({"code": "current_context_score_too_low", "found": current_score, "minimum": 24})
        if len(current_clusters) < 7:
            errors.append({"code": "current_source_clusters_too_few", "found": len(current_clusters), "minimum": 7})
        if len(objective_current_clusters) < 2:
            errors.append({"code": "current_context_not_distributed_to_objective", "found": len(objective_current_clusters), "minimum": 2})

    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "release_status": "editorial-evidence-review-required",
        "domain_score_counts": dict(domains),
        "source_family_counts": dict(source_families),
        "competence_item_count": competence_items,
        "basic_item_count": basic_items,
        "current_context_item_count": current_items,
        "current_context_score": current_score,
        "current_source_cluster_count": len(current_clusters),
        "objective_current_source_cluster_count": len(objective_current_clusters),
        "errors": errors,
        "warnings": warnings,
        "notes": [
            "本工具只檢查設計欄位；不認證來源真實性、素養程度或原創性。計數是作者宣告值，不是逐題複核後的已驗證值。",
            "25%–42% 為跨年度組卷警示帶，不取代所選正式年度的科別配分。",
            "時事只提供證據情境；題目不得要求考生事先知道新聞。",
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
