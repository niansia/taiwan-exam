#!/usr/bin/env python3
"""Validate current GSAT 國綜/自然 structure and official-scope anchors."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
CONTENT_CODE = re.compile(r"\b[A-Z][A-Za-z]{2}-Vc-\d\b")
PERFORMANCE_CODE = re.compile(r"\b[a-z]{2}-Ⅴc-\d\b")
CHINESE_CODES = {f"A{i}" for i in range(1, 7)} | {f"B{i}" for i in range(1, 6)}
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


def pdf_text(path: Path) -> str:
    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8-sig")
    doc = pymupdf.open(path)
    return "\n".join(page.get_text("text") or "" for page in doc)


def normalized_print(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).replace("（", "(").replace("）", ")")


def selected_labels(value: object) -> list[str]:
    if isinstance(value, list):
        values = [str(item).strip().upper() for item in value]
    else:
        values = re.findall(r"[A-E]", str(value or "").upper())
    return [value for value in values if value in {"A", "B", "C", "D", "E"}]


def meaningful_innovation_text(value: object) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.casefold() not in PLACEHOLDER_INNOVATION_TEXT


def evidenced_pass(value: object) -> bool:
    text = str(value or "").strip()
    return text.startswith("pass:") and len(text.partition(":")[2].strip()) >= 8


def innovation_errors(question: dict, expected_subject: str) -> list[str]:
    label = question.get("number") or question.get("id") or "?"
    prefix = f"Q{label}"
    spec = question.get("item_spec") if isinstance(question.get("item_spec"), dict) else {}
    audit = spec.get("subject_innovation_audit")
    if not isinstance(audit, dict):
        return [f"{prefix}: missing subject_innovation_audit"]
    errors: list[str] = []
    if audit.get("subject") != expected_subject:
        errors.append(f"{prefix}: innovation audit subject must be {expected_subject}")
    if audit.get("candidate_competition_linked") is not True:
        errors.append(f"{prefix}: innovation audit is not linked to candidate competition")
    if audit.get("routine_template_recoverable") is not False:
        errors.append(f"{prefix}: routine/template recoverability has not been rejected")
    if audit.get("surface_or_topic_novelty_only") is not False:
        errors.append(f"{prefix}: surface/topic-only novelty has not been rejected")
    for field in INNOVATION_TEXT_FIELDS:
        if not meaningful_innovation_text(audit.get(field)):
            errors.append(f"{prefix}: innovation audit {field} is missing or placeholder text")
    if audit.get("reviewer_decision") != "pass-subject-novelty":
        errors.append(f"{prefix}: subject innovation reviewer decision has not passed")
    return errors


def paper_innovation_errors(metadata: dict, expected_subject: str) -> list[str]:
    review = metadata.get("subject_innovation_review")
    if not isinstance(review, dict):
        return [f"metadata: missing subject_innovation_review for {expected_subject}"]
    errors: list[str] = []
    if review.get("subject") != expected_subject:
        errors.append(f"metadata: subject innovation review must identify {expected_subject}")
    if review.get("all_scored_items_reviewed") is not True:
        errors.append(f"metadata: subject innovation review must cover every scored {expected_subject} item")
    for field in (
        "mechanism_saturation_review",
        "representation_saturation_review",
        "section_or_domain_diversity_review",
    ):
        if not evidenced_pass(review.get(field)):
            errors.append(f"metadata: {expected_subject} {field} has not passed")
    if review.get("reviewer_decision") != "pass-subject-novelty":
        errors.append(f"metadata: {expected_subject} subject innovation reviewer decision has not passed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exam", type=Path)
    parser.add_argument("--science-spec", type=Path, default=ROOT / "tmp" / "pdfs" / "gsat-science-spec.pdf")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam.read_text(encoding="utf-8-sig"))
    subject = (exam.get("metadata") or {}).get("paper_subject")
    questions = exam.get("questions") or []
    errors: list[str] = []
    warnings: list[str] = []

    if subject not in {'國綜', '自然'}:
        errors.append(f"unsupported paper_subject {subject!r}")
    else:
        # Scope and full-paper structure are separate. Never hardcode one
        # generated paper's section ids/counts as all ROC 111-115 structures.
        warnings.append('Exact section/type/score structure must pass validate_exam_release.py against the selected source-reviewed profile.')

    used_codes = Counter()
    domain_counts = Counter()
    domain_scores = Counter()
    if subject == "國綜":
        if any("國寫" in str(q) for q in questions):
            errors.append("國綜 paper contains 國寫 material")
        for q in questions:
            errors.extend(innovation_errors(q, "國綜"))
            codes = (q.get("item_spec") or {}).get("curriculum_codes") or []
            if not codes:
                errors.append(f"Q{q.get('number')}: no curriculum code")
            bad = [c for c in codes if c not in CHINESE_CODES]
            if bad:
                errors.append(f"Q{q.get('number')}: invalid 國綜 scope codes {bad}")
            used_codes.update(codes)
        if not any(code.startswith("A") for code in used_codes):
            errors.append("國綜 has no language-knowledge A objective")
        for code in ("B1", "B2", "B3", "B4", "B5"):
            if not used_codes[code]:
                errors.append(f"國綜 missing {code}")
        if len(questions) >= 30 or (exam.get("metadata") or {}).get("generation_mode") == "full-paper":
            errors.extend(paper_innovation_errors(exam.get("metadata") or {}, "國綜"))
            nearest_differences = [
                str((((q.get("item_spec") or {}).get("subject_innovation_audit") or {}).get("nearest_neighbor_difference") or "")).strip()
                for q in questions
            ]
            if any(value and count > 1 for value, count in Counter(nearest_differences).items()):
                errors.append("國綜 subject innovation audits reuse identical nearest-neighbor differences")
    elif subject == "自然":
        source = pdf_text(args.science_spec)
        valid_content = set(CONTENT_CODE.findall(source))
        valid_performance = set(PERFORMANCE_CODE.findall(source))
        normalized_domains: dict[int, str] = {}
        for q in questions:
            spec = q.get("item_spec") or {}
            errors.extend(innovation_errors(q, "自然"))
            codes = spec.get("curriculum_codes") or []
            if not codes:
                errors.append(f"Q{q.get('number')}: no curriculum code")
                continue
            for code in codes:
                if code not in valid_content and code not in valid_performance:
                    errors.append(f"Q{q.get('number')}: code not in official specification: {code}")
                used_codes[code] += 1
            domain = str(spec.get("domain") or "")
            domain = domain.replace("地球科學", "地科")
            head = next((name for name in ("物理", "化學", "生物", "地科") if name in domain), None)
            if head:
                domain_counts[head] += 1
                domain_scores[head] += float(q.get("score") or 0)
                if isinstance(q.get("number"), int):
                    normalized_domains[int(q["number"])] = head
            else:
                errors.append(f"Q{q.get('number')}: natural-science domain is not classifiable")
            if len(questions) >= 50:
                contract = spec.get("natural_reasoning_contract") if isinstance(spec.get("natural_reasoning_contract"), dict) else {}
                if contract.get("recall_only") is not False:
                    errors.append(f"Q{q.get('number')}: pure definition/recall has not been rejected")
                if contract.get("direct_formula_substitution_only") is not False:
                    errors.append(f"Q{q.get('number')}: direct formula substitution has not been rejected")
                if contract.get("curriculum_centrality") not in {"core", "high_frequency"}:
                    errors.append(f"Q{q.get('number')}: curriculum anchor is peripheral or missing")
                if not str(contract.get("core_curriculum_anchor") or "").strip():
                    errors.append(f"Q{q.get('number')}: core curriculum anchor missing")
                operations = contract.get("reasoning_operations") or []
                minimum_operations = 3 if ((spec.get("difficulty_design") or {}).get("band") in {"中", "中偏難", "難"}) else 2
                if len(operations) < minimum_operations:
                    errors.append(f"Q{q.get('number')}: only {len(operations)} reasoning operations; require {minimum_operations}")
                if not str(contract.get("material_or_model_dependency") or "").strip():
                    errors.append(f"Q{q.get('number')}: material/model dependency missing")
        for domain in ("物理", "化學", "生物", "地科"):
            if domain_counts[domain] < 8:
                errors.append(f"{domain} coverage below 8 items: {domain_counts[domain]}")
        count_values = [domain_counts[name] for name in ("物理", "化學", "生物", "地科")]
        if max(count_values) - min(count_values) > 3:
            errors.append(
                "natural discipline item counts are imbalanced: "
                + ", ".join(f"{name}={domain_counts[name]}" for name in ("物理", "化學", "生物", "地科"))
            )
        total_domain_score = sum(domain_scores.values())
        score_shares = {
            name: domain_scores[name] / total_domain_score
            for name in ("物理", "化學", "生物", "地科")
        } if total_domain_score else {}
        if score_shares and max(score_shares.values()) - min(score_shares.values()) > 0.08:
            errors.append(
                "natural discipline score shares differ by more than 8 percentage points: "
                + ", ".join(f"{name}={score_shares[name]:.3f}" for name in ("物理", "化學", "生物", "地科"))
            )
        inquiry = sum(any(PERFORMANCE_CODE.fullmatch(c) for c in ((q.get("item_spec") or {}).get("curriculum_codes") or [])) for q in questions)
        if inquiry < 14:
            errors.append(f"inquiry/practice coverage below 14 items: {inquiry}")
        if not any(q.get("type") == "constructed_response" for q in questions):
            errors.append("natural mixed part has no constructed response")
        if len(questions) >= 50:
            metadata = exam.get("metadata") or {}
            errors.extend(paper_innovation_errors(metadata, "自然"))
            nearest_differences = [
                str((((q.get("item_spec") or {}).get("subject_innovation_audit") or {}).get("nearest_neighbor_difference") or "")).strip()
                for q in questions
            ]
            if any(value and count > 1 for value, count in Counter(nearest_differences).items()):
                errors.append("自然 subject innovation audits reuse identical nearest-neighbor differences")
            if int(metadata.get("layout_contract_version") or 0) < 5:
                errors.append("full natural paper requires layout_contract_version 5 for the cover scoring contract")
            choice_form = metadata.get("natural_choice_form_contract")
            expected_choice_form = {
                "profile_roc_year": 115,
                "first_part_score": 72,
                "first_part_item_score": 2,
                "first_part_single_choice_count": 24,
                "first_part_multiple_choice_count": 12,
                "mixed_part_single_choice_count": 6,
                "mixed_part_multiple_choice_count": 6,
                "mixed_part_constructed_response_count": 8,
            }
            if not isinstance(choice_form, dict):
                errors.append("full natural paper requires natural_choice_form_contract")
            else:
                for field, expected_value in expected_choice_form.items():
                    if choice_form.get(field) != expected_value:
                        errors.append(f"natural choice form {field} must be {expected_value}")
                if choice_form.get("option_labels") != ["A", "B", "C", "D", "E"]:
                    errors.append("natural selected-response option labels must be A-E")
                if choice_form.get("multiple_selection_cue") != "（應選n項）":
                    errors.append("natural multiple-selection cue contract must be （應選n項）")
                cover_rules = set(choice_form.get("cover_scoring_rules") or [])
                if cover_rules != {"single_choice_all_or_zero", "multiple_choice_n_minus_2k_over_n"}:
                    errors.append("natural cover must declare both official choice scoring rules")

            numbered = {q.get("number"): q for q in questions if isinstance(q.get("number"), int)}
            first_questions = [numbered.get(number) for number in range(1, 37)]
            if any(q is None for q in first_questions):
                errors.append("natural first part must contain every question from 1 through 36")
            else:
                first_types = Counter(q.get("type") for q in first_questions)
                if first_types != Counter({"single_choice": 24, "multiple_choice": 12}):
                    errors.append(f"natural first-part 115 choice mix must be 24 single and 12 multiple, got {dict(first_types)}")
                first_score = sum(float(q.get("score") or 0) for q in first_questions)
                if first_score != 72 or any(float(q.get("score") or 0) != 2 for q in first_questions):
                    errors.append("natural Questions 1-36 must each be 2 points and total 72 points")
                section_ids = {q.get("section_id") for q in first_questions}
                if len(section_ids) != 1:
                    errors.append("natural Questions 1-36 must share one first-part section")
                else:
                    section_id = next(iter(section_ids))
                    section = next((s for s in (exam.get("sections") or []) if s.get("id") == section_id), None)
                    if not section:
                        errors.append("natural first-part section metadata missing")
                    else:
                        if normalized_print(section.get("title")) != normalized_print("第壹部分、選擇題（占72分）"):
                            errors.append("natural first-part heading must print 第壹部分、選擇題（占72分）")
                        printed_direction = "".join(str(value) for value in (section.get("instructions") or []))
                        if normalized_print(printed_direction) != normalized_print("說明：第1題至第36題，含單選題及多選題，每題2分。"):
                            errors.append("natural first-part direction must state range, both choice types, and 2 points each")

            mixed_questions = [numbered.get(number) for number in range(37, 57)]
            if len(questions) == 56 and not any(q is None for q in mixed_questions):
                mixed_types = Counter(q.get("type") for q in mixed_questions)
                expected_mixed = Counter({"single_choice": 6, "multiple_choice": 6, "constructed_response": 8})
                if mixed_types != expected_mixed:
                    errors.append(f"natural mixed-part 115 response mix mismatch: {dict(mixed_types)}")

            answer_by_id = {answer.get("question_id"): answer for answer in (exam.get("answers") or [])}
            for q in questions:
                if q.get("type") not in {"single_choice", "multiple_choice"}:
                    continue
                number = q.get("number")
                options = q.get("options") or []
                labels = [str(option.get("label") or "") for option in options]
                if len(options) != 5 or labels != ["A", "B", "C", "D", "E"]:
                    errors.append(f"Q{number}: natural selected response must have five A-E options")
                answer_labels = selected_labels((answer_by_id.get(q.get("id")) or {}).get("final_answer"))
                if q.get("type") == "single_choice":
                    if len(answer_labels) != 1:
                        errors.append(f"Q{number}: single-choice key must contain exactly one A-E label")
                else:
                    required_count = q.get("required_selection_count")
                    if not isinstance(required_count, int) or required_count < 2 or required_count > 4:
                        errors.append(f"Q{number}: multiple-choice item requires required_selection_count from 2 to 4")
                    if len(answer_labels) != required_count:
                        errors.append(f"Q{number}: （應選{required_count}項） cue disagrees with verified key {answer_labels}")
            block_order = (exam.get("metadata") or {}).get("natural_objective_block_order")
            if not isinstance(block_order, list) or len(block_order) != 4 or set(block_order) != {"物理", "化學", "生物", "地科"}:
                errors.append("natural_objective_block_order must list physics, chemistry, biology, and earth science exactly once")
            else:
                expected = {
                    number: block_order[(number - 1) // 9]
                    for number in range(1, 37)
                }
                missing = [number for number in range(1, 37) if number not in normalized_domains]
                wrong = [
                    number for number in range(1, 37)
                    if number in normalized_domains and normalized_domains[number] != expected[number]
                ]
                if missing:
                    errors.append(f"natural selected-response 1-36 missing numbered/domain items: {missing}")
                if wrong:
                    errors.append(f"natural selected-response disciplines are interleaved or not in nine-item blocks: {wrong}")
            mixed_designs = (exam.get("metadata") or {}).get("natural_mixed_group_designs")
            if mixed_designs is not None:
                if not isinstance(mixed_designs, list):
                    errors.append("natural_mixed_group_designs must be a list when declared")
                else:
                    for index, design in enumerate(mixed_designs, 1):
                        if not isinstance(design, dict):
                            errors.append(f"natural mixed group {index}: invalid design record")
                            continue
                        domains = [str(value).replace("地球科學", "地科") for value in (design.get("required_domains") or [])]
                        if len(set(domains)) < 2 or not set(domains).issubset({"物理", "化學", "生物", "地科"}):
                            errors.append(f"natural mixed group {index}: cross-disciplinary record requires at least two valid domains")
                        if not str(design.get("evidence_bridge") or "").strip():
                            errors.append(f"natural mixed group {index}: evidence bridge missing")
                        if not design.get("question_numbers"):
                            errors.append(f"natural mixed group {index}: question numbers missing")
            source_plan = (exam.get("metadata") or {}).get("natural_source_ecology_plan")
            if not isinstance(source_plan, dict):
                errors.append("full natural paper requires natural_source_ecology_plan")
            else:
                if source_plan.get("mode") != "current-affairs-emphasis":
                    errors.append("natural source ecology must use current-affairs-emphasis mode")
                if source_plan.get("recent_window_months") != 12:
                    errors.append("natural current-affairs window must be the preceding 12 months")
                parsed_dates = {}
                for field in ("as_of_date", "editorial_lock_date"):
                    try:
                        parsed_dates[field] = dt.date.fromisoformat(str(source_plan.get(field) or ""))
                    except ValueError:
                        errors.append(f"natural source ecology has invalid {field}")
                if len(parsed_dates) == 2 and parsed_dates["editorial_lock_date"] > parsed_dates["as_of_date"]:
                    errors.append("natural editorial lock date cannot be after as-of date")
                recent_numbers = source_plan.get("recent_item_numbers") or []
                if (
                    not isinstance(recent_numbers, list)
                    or len(recent_numbers) != len(set(recent_numbers))
                    or any(not isinstance(number, int) or number < 1 or number > len(questions) for number in recent_numbers)
                ):
                    errors.append("natural recent_item_numbers must be unique valid question numbers")
                else:
                    if len(recent_numbers) < 6:
                        errors.append("natural full paper needs at least 6 visibly current-affairs-linked items")
                    recent_domains = {normalized_domains.get(number) for number in recent_numbers}
                    recent_domains.discard(None)
                    if len(recent_domains) < 3:
                        errors.append("natural current-affairs items must span at least 3 science disciplines")
                    if not any(number <= 36 for number in recent_numbers) or not any(number >= 37 for number in recent_numbers):
                        errors.append("natural current-affairs items must appear in both selected and mixed-response parts")
                recent_groups = source_plan.get("recent_source_groups") or []
                if not isinstance(recent_groups, list) or len(recent_groups) < 4 or any(not str(group).strip() for group in recent_groups):
                    errors.append("natural source ecology requires at least 4 distinct recent source groups")
                if not str(source_plan.get("older_dated_source_policy") or "").strip():
                    errors.append("natural source ecology must state an older-dated random/balanced sampling policy")
                if not str(source_plan.get("balance_note") or "").strip():
                    errors.append("natural source ecology must state how recency preserves whole-paper balance")
    else:
        inquiry = 0

    report = {
        "status": "pass" if not errors else "fail", "subject": subject,
        "question_count": len(questions), "total_score": sum(float(q.get("score") or 0) for q in questions),
        "domain_counts": dict(domain_counts), "domain_scores": dict(domain_scores),
        "curriculum_code_counts": dict(sorted(used_codes.items())),
        "inquiry_item_count": inquiry if subject == "自然" else None,
        "errors": errors, "warnings": warnings,
        "scope_source": str(args.science_spec) if subject == "自然" else "CEEC 國文考科考試說明 A1-A6/B1-B5",
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
