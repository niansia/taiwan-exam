#!/usr/bin/env python3
"""Validate the non-trivial, in-scope reasoning floor for current GSAT English."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import Counter
from typing import Any


GLOBAL_SPANS = {"cross_sentence", "cross_paragraph", "text_visual"}
VALID_SPANS = {"local_sentence", "cross_clause", *GLOBAL_SPANS}
HIGHER_VOCABULARY_BANDS = {"中偏難", "難", "medium_hard", "hard"}
SIMPLE_VOCABULARY_BANDS = {"簡單", "easy"}
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


def _meaningful_innovation_text(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.casefold() not in PLACEHOLDER_INNOVATION_TEXT


def _evidenced_pass(value: Any) -> bool:
    text = str(value or "").strip()
    return text.startswith("pass:") and len(text.partition(":")[2].strip()) >= 8


def _innovation_errors(question: dict[str, Any]) -> list[str]:
    label = question.get("number") or question.get("id") or "?"
    prefix = f"Q{label}"
    spec = question.get("item_spec") if isinstance(question.get("item_spec"), dict) else {}
    audit = spec.get("subject_innovation_audit")
    if not isinstance(audit, dict):
        return [f"{prefix}: missing subject_innovation_audit"]
    errors: list[str] = []
    if audit.get("subject") != "英文":
        errors.append(f"{prefix}: innovation audit subject must be 英文")
    if audit.get("candidate_competition_linked") is not True:
        errors.append(f"{prefix}: innovation audit is not linked to candidate competition")
    if audit.get("routine_template_recoverable") is not False:
        errors.append(f"{prefix}: routine/template recoverability has not been rejected")
    if audit.get("surface_or_topic_novelty_only") is not False:
        errors.append(f"{prefix}: surface/topic-only novelty has not been rejected")
    for field in INNOVATION_TEXT_FIELDS:
        if not _meaningful_innovation_text(audit.get(field)):
            errors.append(f"{prefix}: innovation audit {field} is missing or placeholder text")
    if audit.get("reviewer_decision") != "pass-subject-novelty":
        errors.append(f"{prefix}: subject innovation reviewer decision has not passed")
    return errors


def _paper_innovation_errors(meta: dict[str, Any]) -> list[str]:
    review = meta.get("subject_innovation_review")
    if not isinstance(review, dict):
        return ["metadata: missing subject_innovation_review for English"]
    errors: list[str] = []
    if review.get("subject") != "英文":
        errors.append("metadata: subject innovation review must identify 英文")
    if review.get("all_scored_items_reviewed") is not True:
        errors.append("metadata: subject innovation review must cover every scored English task")
    for field in (
        "mechanism_saturation_review",
        "representation_saturation_review",
        "section_or_domain_diversity_review",
    ):
        if not _evidenced_pass(review.get(field)):
            errors.append(f"metadata: English {field} has not passed")
    if review.get("reviewer_decision") != "pass-subject-novelty":
        errors.append("metadata: English subject innovation reviewer decision has not passed")
    return errors


def validate_exam(exam: dict[str, Any]) -> dict[str, Any]:
    meta = exam.get("metadata") or {}
    subject = meta.get("paper_subject") or meta.get("subject")
    if subject != "英文":
        return {"status": "pass", "subject": subject, "errors": [], "note": "not an English paper"}

    by_number = {
        int(question["number"]): question
        for question in exam.get("questions") or []
        if isinstance(question.get("number"), int) and 1 <= int(question["number"]) <= 50
    }
    errors: list[str] = []
    if set(by_number) != set(range(1, 51)):
        errors.append("complete English paper must contain numbered items 1-50")

    nonlocal_cloze = 0
    reading_global = 0
    mixed_synthesis = 0
    vocabulary_cross_clause = 0
    vocabulary_competitive = 0
    vocabulary_simple = 0
    vocabulary_higher = 0
    reading_groups = ((35, 38), (39, 42), (43, 46))
    answers_by_id = {
        str(answer.get("question_id")): str(answer.get("final_answer") or "")
        for answer in exam.get("answers") or []
        if isinstance(answer, dict) and answer.get("question_id") is not None
    }
    vocabulary_answer_labels: list[str] = []

    for question in exam.get("questions") or []:
        if isinstance(question, dict):
            errors.extend(_innovation_errors(question))
    nearest_differences = [
        str((((question.get("item_spec") or {}).get("subject_innovation_audit") or {}).get("nearest_neighbor_difference") or "")).strip()
        for question in exam.get("questions") or [] if isinstance(question, dict)
    ]
    repeated_nearest = {
        value: count for value, count in Counter(nearest_differences).items()
        if value and count > 1
    }
    if repeated_nearest:
        errors.append("English subject innovation audits reuse identical nearest-neighbor differences")

    for number in range(1, 51):
        question = by_number.get(number) or {}
        spec = question.get("item_spec") or {}
        contract = spec.get("english_difficulty_contract") if isinstance(spec.get("english_difficulty_contract"), dict) else {}
        if contract.get("direct_lookup_or_copy_only") is not False:
            errors.append(f"Q{number}: direct lookup/copy has not been rejected")
        if contract.get("outside_vocabulary_required") is not False:
            errors.append(f"Q{number}: outside vocabulary cannot be required")
        operations = contract.get("reasoning_operations") or []
        minimum = 3 if number >= 31 else 2
        if len(operations) < minimum:
            errors.append(f"Q{number}: only {len(operations)} linked operations; require {minimum}")
        span = contract.get("evidence_span")
        if span not in VALID_SPANS:
            errors.append(f"Q{number}: invalid or missing evidence_span")
        competition = contract.get("distractor_competition") or []
        options = question.get("options") or []
        if options:
            required = max(3, len(options) - 1)
            if len(competition) < required:
                errors.append(f"Q{number}: distractor competition has {len(competition)} records; require {required}")
            for record in competition:
                if not isinstance(record, dict) or not record.get("option") or not record.get("initial_fit") or not record.get("defeating_evidence"):
                    errors.append(f"Q{number}: every distractor record needs option, initial_fit, and defeating_evidence")
                    break
        if 11 <= number <= 34 and span in GLOBAL_SPANS:
            nonlocal_cloze += 1
        if 35 <= number <= 46 and span in GLOBAL_SPANS:
            reading_global += 1
        if 47 <= number <= 50 and contract.get("synthesis_or_transformation") is True and span in GLOBAL_SPANS:
            mixed_synthesis += 1

        if 1 <= number <= 10:
            if span == "cross_clause":
                vocabulary_cross_clause += 1
            challenge = spec.get("vocabulary_challenge") if isinstance(spec.get("vocabulary_challenge"), dict) else {}
            if not challenge:
                errors.append(f"Q{number}: vocabulary_challenge contract missing")
            else:
                if challenge.get("one_cue_shortcut_rejected") is not True:
                    errors.append(f"Q{number}: one-cue vocabulary shortcut has not been rejected")
                if challenge.get("surface_only_elimination") is not False:
                    errors.append(f"Q{number}: surface-only elimination has not been rejected")
                if challenge.get("two_plausible_distractors_after_local_read") is not True:
                    errors.append(f"Q{number}: fewer than two plausible distractors remain after a local read")
                if not str(challenge.get("decisive_relation") or "").strip():
                    errors.append(f"Q{number}: decisive vocabulary relation missing")
                if challenge.get("reviewed_against_recent_ceec") is not True:
                    errors.append(f"Q{number}: vocabulary demand was not reviewed against recent CEEC items")
                if all(
                    challenge.get(key) is value
                    for key, value in (
                        ("one_cue_shortcut_rejected", True),
                        ("surface_only_elimination", False),
                        ("two_plausible_distractors_after_local_read", True),
                        ("reviewed_against_recent_ceec", True),
                    )
                ):
                    vocabulary_competitive += 1
                band = str(challenge.get("band") or "")
                if band in SIMPLE_VOCABULARY_BANDS:
                    vocabulary_simple += 1
                if band in HIGHER_VOCABULARY_BANDS:
                    vocabulary_higher += 1
            label = answers_by_id.get(str(question.get("id") or ""), "")
            if label:
                vocabulary_answer_labels.append(label)

    if nonlocal_cloze < 12:
        errors.append(f"cloze/completion/structure has only {nonlocal_cloze} cross-sentence-or-wider items; require 12")
    if reading_global < 8:
        errors.append(f"reading has only {reading_global} cross-sentence-or-wider items; require 8")
    for start, end in reading_groups:
        if not any(
            ((by_number.get(number) or {}).get("item_spec") or {})
            .get("english_difficulty_contract", {})
            .get("evidence_span") in {"cross_paragraph", "text_visual"}
            for number in range(start, end + 1)
        ):
            errors.append(f"reading group {start}-{end} lacks cross-paragraph or text-visual inference")
    if mixed_synthesis < 3:
        errors.append(f"mixed section has only {mixed_synthesis} synthesis/transformation items; require 3")
    if vocabulary_cross_clause < 6:
        errors.append(f"vocabulary section has only {vocabulary_cross_clause} cross-clause decisions; require 6")
    if vocabulary_competitive < 8:
        errors.append(f"vocabulary section has only {vocabulary_competitive} fully competitive items; require 8")
    if vocabulary_simple > 1:
        errors.append(f"vocabulary section has {vocabulary_simple} simple anchors; allow at most 1")
    if vocabulary_higher < 5:
        errors.append(f"vocabulary section has only {vocabulary_higher} medium-hard/hard items; require 5")
    answer_counts = Counter(vocabulary_answer_labels)
    if len(vocabulary_answer_labels) != 10:
        errors.append("vocabulary answer labels could not be resolved for all ten items")
    elif len(answer_counts) < 3 or max(answer_counts.values()) > 4:
        errors.append(f"vocabulary answer-position distribution is implausibly concentrated: {dict(answer_counts)}")
    if set(by_number) == set(range(1, 51)):
        errors.extend(_paper_innovation_errors(meta))

    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "subject": subject,
        "numbered_item_count": len(by_number),
        "cross_sentence_or_wider_11_34": nonlocal_cloze,
        "cross_sentence_or_wider_reading": reading_global,
        "mixed_synthesis_count": mixed_synthesis,
        "vocabulary_cross_clause_count": vocabulary_cross_clause,
        "vocabulary_competitive_item_count": vocabulary_competitive,
        "vocabulary_simple_anchor_count": vocabulary_simple,
        "vocabulary_medium_hard_or_hard_count": vocabulary_higher,
        "vocabulary_answer_position_counts": dict(answer_counts),
        "errors": errors,
        "note": "Structural design validation only; vocabulary scope and achieved difficulty are separate checks.",
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
