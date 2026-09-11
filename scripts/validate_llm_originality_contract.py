#!/usr/bin/env python3
"""Fail a generated exam unless every item records fresh LLM construction."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def validate_item(item: dict[str, Any]) -> list[str]:
    number = item.get("number", "?")
    prefix = f"Q{number}"
    errors: list[str] = []
    spec = item.get("item_spec")
    if not isinstance(spec, dict):
        return [f"{prefix}: missing item_spec"]
    record = spec.get("originality_record")
    if not isinstance(record, dict):
        return [f"{prefix}: missing originality_record"]
    if record.get("generated_by") != "llm-original-construction":
        errors.append(f"{prefix}: generated_by must be llm-original-construction")
    if record.get("source_visibility") != "aggregate-only":
        errors.append(f"{prefix}: source_visibility must be aggregate-only")
    candidate_count = record.get("candidate_count")
    if not isinstance(candidate_count, int) or candidate_count < 3:
        errors.append(f"{prefix}: candidate_count must be at least 3")
    candidate_families = as_list(record.get("candidate_mechanism_families"))
    if len(set(map(str, candidate_families))) < 3:
        errors.append(f"{prefix}: at least 3 distinct candidate mechanism families required")
    if not record.get("selected_mechanism") or not record.get("domain_family"):
        errors.append(f"{prefix}: selected_mechanism and domain_family are required")
    if len(as_list(record.get("novelty_dimensions"))) < 3:
        errors.append(f"{prefix}: at least 3 novelty_dimensions required")
    if not str(record.get("skin_swap_test") or "").startswith("pass"):
        errors.append(f"{prefix}: skin_swap_test has not passed")
    if not str(record.get("lexical_screen") or "").startswith("pass"):
        errors.append(f"{prefix}: lexical_screen has not passed")
    if item.get("visual_asset") and not str(record.get("visual_topology_screen") or "").startswith("pass"):
        errors.append(f"{prefix}: visual item lacks a passing visual_topology_screen")
    curriculum = record.get("curriculum_reduction")
    if not isinstance(curriculum, dict):
        errors.append(f"{prefix}: missing curriculum_reduction")
    else:
        if curriculum.get("outside_knowledge_required") is not False:
            errors.append(f"{prefix}: outside_knowledge_required must be false")
        if not as_list(curriculum.get("mapped_operations")):
            errors.append(f"{prefix}: curriculum mapped_operations are required")
    if not str(record.get("reviewer_decision") or "").startswith("pass"):
        errors.append(f"{prefix}: reviewer_decision has not passed")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exam_json", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam_json.read_text(encoding="utf-8"))
    metadata = exam.get("metadata") or {}
    errors: list[str] = []
    contract = metadata.get("llm_original_generation_contract")
    if not isinstance(contract, dict):
        errors.append("metadata: missing llm_original_generation_contract")
    else:
        if contract.get("all_items_generated_fresh") is not True:
            errors.append("metadata: all_items_generated_fresh must be true")
        if contract.get("inherits_legacy_question_content") is not False:
            errors.append("metadata: inherits_legacy_question_content must be false")
        if contract.get("source_access_mode") != "aggregate-only":
            errors.append("metadata: source_access_mode must be aggregate-only")

    questions = exam.get("questions") or []
    for item in questions:
        errors.extend(validate_item(item))

    stimulus_counts = Counter(str(item.get("group_stimulus")) for item in questions if item.get("group_stimulus"))
    # A one-item source passage is already covered by that item's originality
    # record.  The extra group record is required only when one material is
    # reused across two or more scored items.
    shared = {stimulus for stimulus, count in stimulus_counts.items() if count > 1}
    group_records = metadata.get("mixed_group_originality_records")
    if shared:
        if not isinstance(group_records, list) or len(group_records) < len(shared):
            errors.append("metadata: every mixed/shared stimulus needs a group-level originality record")
        else:
            for index, record in enumerate(group_records, 1):
                if not isinstance(record, dict):
                    errors.append(f"mixed group {index}: invalid record")
                    continue
                for field in ("stimulus_originality", "subpart_dependency", "answer_leakage", "integration"):
                    if not str(record.get(field) or "").startswith("pass"):
                        errors.append(f"mixed group {index}: {field} has not passed")

    records = [
        (item.get("item_spec") or {}).get("originality_record") or {}
        for item in questions
    ]
    mechanisms = Counter(str(record.get("selected_mechanism") or "missing") for record in records)
    domains = Counter(str(record.get("domain_family") or "missing") for record in records)
    diversity = metadata.get("paper_originality_matrix")
    if not isinstance(diversity, dict) or not str(diversity.get("reviewer_decision") or "").startswith("pass"):
        errors.append("metadata: paper_originality_matrix reviewer decision has not passed")

    report = {
        "status": "pass" if not errors else "fail",
        "question_count": len(questions),
        "mechanism_family_counts": dict(mechanisms),
        "domain_family_counts": dict(domains),
        "errors": errors,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
