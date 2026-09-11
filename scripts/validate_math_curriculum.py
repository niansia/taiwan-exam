#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = ROOT / "templates" / "current-gsat-math-scope.json"
MATH_B_STRANDS = {
    "number_and_algebra",
    "functions_and_models",
    "geometry_and_space",
    "data_and_statistics",
    "counting_and_probability",
}
MATH_B_DISTINCTIVE_TOPICS = {
    "sphere-coordinate",
    "one-point-perspective",
    "periodic-sine-model",
    "plane-vector-projection",
    "conic-section",
}


def compact_text(question: dict) -> str:
    pieces = [str(question.get("prompt", "")), str(question.get("group_stimulus", ""))]
    pieces.extend(str(option.get("text", "")) for option in question.get("options", []))
    spec = question.get("item_spec", {})
    record = spec.get("originality_record", {})
    pieces.extend(str(x) for x in record.get("curriculum_reduction", {}).get("mapped_operations", []))
    return " ".join(pieces)


def forbidden_pattern_present(pattern: str, text: str) -> bool:
    """Lexical triage, not a semantic curriculum certificate.

    In a stated match-scoring context, 積分制度/積分總和 mean league
    points. Remove only those exact noun phrases, never every occurrence
    of 積分 or any actual calculus expression in the same question.
    """
    candidate = text
    if pattern == "積分" and re.search(r"和局|勝方|敗方|小組賽", text):
        candidate = re.sub(r"積分(?:制度|總和)", "賽事點數", text)
    return bool(re.search(re.escape(pattern), candidate, flags=re.IGNORECASE))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a generated GSAT Math A/B paper against the current curriculum gate.")
    parser.add_argument("paper", type=Path)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    args = parser.parse_args()

    paper = json.loads(args.paper.read_text(encoding="utf-8"))
    scope = json.loads(args.scope.read_text(encoding="utf-8"))
    subject = str(paper.get("metadata", {}).get("subject", ""))
    if subject not in {"數學A", "數學B"}:
        print(f"ERROR unsupported subject: {subject}")
        return 2

    suffix = "math_a_codes" if subject == "數學A" else "math_b_codes"
    allowed = set(scope["common_codes"]) | set(scope[suffix])
    errors: list[str] = []
    bridges: list[str] = []
    context_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    for question in paper.get("questions", []):
        qid = str(question.get("id", "?"))
        spec = question.get("item_spec", {})
        codes = spec.get("scope_codes", [])
        status = spec.get("scope_status")
        if not codes:
            errors.append(f"{qid}: missing scope_codes")
        unknown = sorted(set(codes) - allowed)
        if unknown:
            errors.append(f"{qid}: out-of-subject codes {unknown}")
        if status not in {"direct", "defined-bridge"}:
            errors.append(f"{qid}: scope_status must be direct or defined-bridge")
        elif status == "defined-bridge":
            bridges.append(qid)

        context_class = spec.get("context_class")
        topic_family = spec.get("topic_family")
        if context_class not in {"pure-math", "neutral-application", "dated-source"}:
            errors.append(f"{qid}: invalid or missing context_class")
        else:
            context_counts[context_class] += 1
        if not topic_family:
            errors.append(f"{qid}: missing topic_family")
        else:
            topic_counts[str(topic_family)] += 1

        text = compact_text(question)
        for pattern in scope["always_forbidden_patterns"]:
            if forbidden_pattern_present(pattern, text):
                errors.append(f"{qid}: forbidden GSAT concept/term {pattern!r}")
        if subject == "數學B":
            lowered = text.lower()
            for operation in scope["math_b_forbidden_operations"]:
                if operation.lower() in lowered:
                    errors.append(f"{qid}: Math B operation outside the A/B boundary {operation!r}")
            if topic_family == "sphere-coordinate" or set(codes) & {"S-11B-1", "G-11B-4"}:
                application = spec.get("math_b_sphere_application") if isinstance(spec.get("math_b_sphere_application"), dict) else {}
                if application.get("application_family") not in {
                    "spherical_distance", "route_comparison", "navigation_constraint"
                }:
                    errors.append(f"{qid}: Math B sphere item must assess distance, route comparison, or navigation constraints")
                if application.get("direct_coordinate_conversion_only") is not False:
                    errors.append(f"{qid}: coordinate conversion cannot be the whole Math B sphere task")
                if application.get("requires_comparison_or_constraint") is not True:
                    errors.append(f"{qid}: Math B sphere item needs an answer-bearing comparison or constraint")
                if len(application.get("reasoning_operations") or []) < 3:
                    errors.append(f"{qid}: Math B sphere item needs at least three recorded reasoning operations")

    item_count = len(paper.get("questions", []))
    if item_count == 20:
        if not 5 <= context_counts["dated-source"] <= 8:
            errors.append(f"paper: dated-source count {context_counts['dated-source']} is outside the internal 5-8 ecology band")
        if context_counts["pure-math"] < 4:
            errors.append(f"paper: only {context_counts['pure-math']} pure-math items; require at least 4")
        if context_counts["neutral-application"] < 4:
            errors.append(f"paper: only {context_counts['neutral-application']} neutral-application items; require at least 4")
        dominant = [(name, count) for name, count in topic_counts.items() if count > 4]
        if dominant:
            errors.append(f"paper: a topical family exceeds 20% of scored items: {dominant}")
        if topic_counts["combinatorics"] < 1:
            errors.append("paper: no explicit combinatorics item")
        if subject == "數學B":
            questions = paper.get("questions", [])
            question_ids = {str(question.get("id", "")) for question in questions}
            distribution = paper.get("metadata", {}).get("content_distribution_plan", {})
            bands = distribution.get("strand_bands", {}) if isinstance(distribution, dict) else {}
            if set(bands) != MATH_B_STRANDS:
                errors.append(
                    "paper: Math B content_distribution_plan must declare exactly the five required strands"
                )
            else:
                assigned: list[str] = []
                for strand in sorted(MATH_B_STRANDS):
                    record = bands.get(strand, {})
                    ids = [str(value) for value in record.get("question_ids", [])]
                    if not 2 <= len(ids) <= 6:
                        errors.append(
                            f"paper: Math B strand {strand} has {len(ids)} items; require 2-6"
                        )
                    if record.get("minimum") != 2 or record.get("maximum") != 6:
                        errors.append(
                            f"paper: Math B strand {strand} must record minimum=2 and maximum=6"
                        )
                    assigned.extend(ids)
                duplicate_ids = sorted(qid for qid, count in Counter(assigned).items() if count != 1)
                if duplicate_ids:
                    errors.append(f"paper: Math B strand plan has duplicate ids {duplicate_ids}")
                if set(assigned) != question_ids:
                    missing = sorted(question_ids - set(assigned))
                    unknown = sorted(set(assigned) - question_ids)
                    errors.append(
                        f"paper: Math B strand plan must partition all questions; missing={missing}, unknown={unknown}"
                    )

            sequence_ids = [
                str(question.get("id", ""))
                for question in questions
                if "N-10-6" in question.get("item_spec", {}).get("scope_codes", [])
                or any(
                    token in str(question.get("item_spec", {}).get("topic_family", "")).lower()
                    for token in ("sequence", "series", "recurrence")
                )
            ]
            counting_ids = [
                str(question.get("id", ""))
                for question in questions
                if "D-10-3" in question.get("item_spec", {}).get("scope_codes", [])
            ]
            if len(sequence_ids) > 2:
                errors.append(f"paper: sequence-and-series concentration exceeds 2 items: {sequence_ids}")
            if len(counting_ids) > 2:
                errors.append(f"paper: counting-and-combinatorics concentration exceeds 2 items: {counting_ids}")

            rotation = paper.get("metadata", {}).get("math_b_distinctive_rotation", {})
            mechanisms = rotation.get("this_form_mechanisms", {}) if isinstance(rotation, dict) else {}
            present_topics = set(topic_counts) & MATH_B_DISTINCTIVE_TOPICS
            if not present_topics:
                errors.append("paper: Math B lacks a distinctive grade-11 B mechanism")
            if not mechanisms or rotation.get("suite_window_size") != 3:
                errors.append("paper: Math B missing the three-form distinctive-topic rotation ledger")
            if rotation.get("audit_status") != "pass":
                errors.append("paper: Math B distinctive-topic rotation is not marked pass")
        if subject == "數學A":
            cubic_items = [
                question
                for question in paper.get("questions", [])
                if "F-10-2" in (question.get("item_spec", {}).get("scope_codes", []))
            ]
            if not 1 <= len(cubic_items) <= 2:
                errors.append(
                    f"paper: Math A requires 1-2 cubic-function items carrying F-10-2; found {len(cubic_items)}"
                )
            if len(cubic_items) == 2:
                mechanisms = [
                    str(
                        question.get("item_spec", {})
                        .get("originality_record", {})
                        .get("selected_mechanism", "")
                    )
                    for question in cubic_items
                ]
                if not all(mechanisms) or len(set(mechanisms)) != 2:
                    errors.append("paper: two F-10-2 items must use distinct recorded mechanism families")

    if errors:
        print("CURRICULUM CHECK: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "CURRICULUM CHECK: PASS "
        f"({item_count} items; ecology={dict(context_counts)}; "
        f"defined-bridge human review: {', '.join(bridges) or 'none'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
