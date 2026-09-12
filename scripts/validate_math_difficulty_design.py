#!/usr/bin/env python3
"""Validate pre-pilot difficulty and discrimination design for current GSAT math."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def required_decisions(p_center: float | None, number: int, question_type: str) -> int:
    if p_center is None:
        return 4 if number == 20 else 3
    if p_center < 0.20:
        return 4
    if p_center < 0.40:
        return 3
    if p_center < 0.65:
        if question_type in {"single_choice", "multiple_choice"} and number not in {1, 2, 7, 8, 18}:
            return 3
        return 2
    return 2


def profile_for(subject: str) -> Path:
    return ROOT / "exam_packs" / "學測" / "subjects" / subject / "blueprints" / "difficulty-profile.json"


def profile_targets(path: Path) -> dict[int, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    current = data.get("curricula", {}).get("108", {})
    rows = current.get("by_question_number", {})
    return {int(number): row.get("recommended_target", {}) for number, row in rows.items()}


def validate_item(
    item: dict[str, Any], official: dict[int, dict[str, Any]], subject: str
) -> tuple[list[str], dict[str, Any]]:
    number = int(item.get("number", 0))
    qid = str(item.get("id", f"q{number}"))
    score = float(item.get("score") or 0)
    question_type = str(item.get("type", ""))
    spec = item.get("item_spec") if isinstance(item.get("item_spec"), dict) else {}
    design = spec.get("difficulty_design") if isinstance(spec.get("difficulty_design"), dict) else None
    errors: list[str] = []
    summary = {"id": qid, "number": number, "score": score, "level": "missing", "linked_decisions": 0}
    if design is None:
        return [f"{qid}: missing difficulty_design"], summary

    target = official.get(number, {})
    p_center = design.get("target_p_center")
    official_p = target.get("p_center")
    if official_p is not None:
        if not isinstance(p_center, (int, float)):
            errors.append(f"{qid}: target_p_center must be numeric for an objective slot")
        elif abs(float(p_center) - float(official_p)) > 0.02:
            errors.append(f"{qid}: target_p_center {p_center} does not match official profile {official_p}")
        expected_range = target.get("p_range")
        if design.get("target_p_range") != expected_range:
            errors.append(f"{qid}: target_p_range does not match official profile {expected_range}")
        official_d = target.get("discrimination_floor")
        if official_d is not None and design.get("target_d_floor") != official_d:
            errors.append(f"{qid}: target_d_floor does not match official profile {official_d}")
    elif design.get("target_basis") not in {"constructed-response-expert", "official-rubric-expert"}:
        errors.append(f"{qid}: constructed-response slot needs an explicit expert/rubric target basis")

    if design.get("metric_type") not in {"answer_rate", "score_rate", "constructed_response"}:
        errors.append(f"{qid}: invalid metric_type")

    decisions = as_list(design.get("linked_decisions"))
    minimum = required_decisions(float(p_center) if isinstance(p_center, (int, float)) else None, number, question_type)
    if subject == "數學B" and design.get("band") in {"簡單", "中"}:
        minimum = max(minimum, 3)
    declared_minimum = design.get("minimum_linked_decisions")
    if not isinstance(declared_minimum, int) or declared_minimum < minimum:
        errors.append(f"{qid}: minimum_linked_decisions must be at least {minimum}")
    if len(decisions) < minimum:
        errors.append(f"{qid}: only {len(decisions)} linked decisions; require at least {minimum}")
    decision_ids = [str(row.get("id", "")) for row in decisions if isinstance(row, dict)]
    descriptions = [str(row.get("description", "")).strip().lower() for row in decisions if isinstance(row, dict)]
    if len(set(decision_ids)) != len(decisions) or "" in decision_ids:
        errors.append(f"{qid}: linked decision ids must be present and unique")
    if len(set(descriptions)) != len(decisions) or "" in descriptions:
        errors.append(f"{qid}: linked decision descriptions must be present and distinct")
    for row in decisions:
        if not isinstance(row, dict) or not row.get("kind") or not row.get("trigger_evidence"):
            errors.append(f"{qid}: every linked decision needs kind and trigger_evidence")
            break

    representation_changes = design.get("representation_changes")
    constraint_checks = design.get("constraint_checks")
    if not isinstance(representation_changes, int) or representation_changes < 0:
        errors.append(f"{qid}: representation_changes must be a non-negative integer")
        representation_changes = 0
    if not isinstance(constraint_checks, int) or constraint_checks < 0:
        errors.append(f"{qid}: constraint_checks must be a non-negative integer")
        constraint_checks = 0
    if isinstance(p_center, (int, float)) and float(p_center) < 0.40 and representation_changes + constraint_checks < 1:
        errors.append(f"{qid}: hard target requires a representation change or constraint check")

    paths = as_list(design.get("misconception_paths"))
    min_paths = 3 if question_type in {"single_choice", "multiple_choice"} else 2
    if len(paths) < min_paths:
        errors.append(f"{qid}: only {len(paths)} misconception paths; require at least {min_paths}")
    path_ids = [str(row.get("id", "")) for row in paths if isinstance(row, dict)]
    path_errors = [str(row.get("error", "")).strip().lower() for row in paths if isinstance(row, dict)]
    if len(set(path_ids)) != len(paths) or "" in path_ids:
        errors.append(f"{qid}: misconception path ids must be present and unique")
    if len(set(path_errors)) != len(paths) or "" in path_errors:
        errors.append(f"{qid}: misconception errors must be present and distinct")
    for row in paths:
        if not isinstance(row, dict) or not row.get("predicted_outcome"):
            errors.append(f"{qid}: every misconception path needs a predicted_outcome")
            break

    discrimination = design.get("discrimination_design") if isinstance(design.get("discrimination_design"), dict) else {}
    level = discrimination.get("level")
    if level not in {"low", "medium", "high"}:
        errors.append(f"{qid}: invalid discrimination level")
        level = "missing"
    if not discrimination.get("lower_group_move") or not discrimination.get("proficient_move"):
        errors.append(f"{qid}: discrimination design needs lower_group_move and proficient_move")

    shortcut = design.get("shortcut_audit") if isinstance(design.get("shortcut_audit"), dict) else {}
    if len(as_list(shortcut.get("attempted_shortcuts"))) < 2:
        errors.append(f"{qid}: shortcut audit must attempt at least two shortcuts")
    if shortcut.get("collapse_found") is not False or shortcut.get("reviewer_decision") != "pass-no-collapse":
        errors.append(f"{qid}: shortcut-collapse audit has not passed")
    if shortcut.get("direct_formula_substitution_only") is not False:
        errors.append(f"{qid}: mathematics must explicitly reject a direct-formula-only solution")

    if subject in {"數學A", "數學B"}:
        innovation = design.get("innovation_audit") if isinstance(design.get("innovation_audit"), dict) else {}
        if innovation.get("formula_or_definition_recall_only") is not False:
            errors.append(f"{qid}: mathematics innovation audit must reject formula/definition recall")
        if innovation.get("skin_swap_changes_solution_graph") is not True:
            errors.append(f"{qid}: mathematics skin-swap audit must change the solution graph")
        if not str(innovation.get("nearest_neighbor_difference") or "").strip():
            errors.append(f"{qid}: mathematics innovation audit needs a structural nearest-neighbor difference")
        if innovation.get("reviewer_decision") != "pass-nonroutine":
            errors.append(f"{qid}: mathematics non-routine innovation audit has not passed")

    burden = design.get("burden_audit") if isinstance(design.get("burden_audit"), dict) else {}
    for field in ("arithmetic_volume_primary", "prose_length_primary", "outside_knowledge_primary"):
        if burden.get(field) is not False:
            errors.append(f"{qid}: burden_audit.{field} must be false")

    time_audit = design.get("time_audit") if isinstance(design.get("time_audit"), dict) else {}
    expected_minutes = time_audit.get("expected_minutes")
    if not isinstance(expected_minutes, (int, float)) or not 0 < float(expected_minutes) <= 10:
        errors.append(f"{qid}: time_audit.expected_minutes must be in (0, 10]")
        expected_minutes = 0
    item_minutes = item.get("expected_minutes")
    if not isinstance(item_minutes, (int, float)) or abs(float(item_minutes) - float(expected_minutes)) > 0.01:
        errors.append(f"{qid}: item expected_minutes must match time_audit.expected_minutes")
    if not time_audit.get("intended_short_route"):
        errors.append(f"{qid}: time audit needs an intended_short_route")
    for field in ("calculator_required", "exhaustive_enumeration_required"):
        if time_audit.get(field) is not False:
            errors.append(f"{qid}: time_audit.{field} must be false")
    if time_audit.get("hand_calculation_feasible") is not True:
        errors.append(f"{qid}: hand calculation feasibility has not passed")

    estimate = design.get("expert_estimate") if isinstance(design.get("expert_estimate"), dict) else {}
    if estimate.get("difficulty_band") not in {"very_easy", "easy", "medium", "hard", "very_hard"}:
        errors.append(f"{qid}: invalid expert difficulty band")
    if estimate.get("discrimination_level") != level:
        errors.append(f"{qid}: expert discrimination level must match discrimination_design")
    confidence = estimate.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
        errors.append(f"{qid}: expert confidence must be between 0 and 1")
    if estimate.get("status") != "provisional-until-representative-pilot":
        errors.append(f"{qid}: expert estimate must remain provisional until pilot")

    summary.update({"level": level, "linked_decisions": len(decisions), "required": minimum, "expected_minutes": expected_minutes})
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exam_json", type=Path)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    exam = json.loads(args.exam_json.read_text(encoding="utf-8"))
    subject = str(exam.get("metadata", {}).get("subject", ""))
    if subject not in {"數學A", "數學B"}:
        print(f"ERROR unsupported subject: {subject}")
        return 2
    profile = args.profile or profile_for(subject)
    report = validate(exam, profile)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not report['errors'] else 1


def validate(exam: dict, profile: Path | None = None) -> dict:
    subject = exam.get('metadata', {}).get('subject')
    if subject not in {'數學A', '數學B'}:
        return {'status': 'fail', 'errors': ['unsupported math subject']}
    official = profile_targets(profile or profile_for(subject))
    errors: list[str] = []
    summaries: list[dict[str, Any]] = []
    for item in exam.get("questions", []):
        item_errors, summary = validate_item(item, official, subject)
        errors.extend(item_errors)
        summaries.append(summary)

    questions = exam.get("questions", [])
    total_score = sum(float(item.get("score") or 0) for item in questions)
    medium_high_score = sum(row["score"] for row in summaries if row["level"] in {"medium", "high"})
    three_decision_score = sum(row["score"] for row in summaries if row["linked_decisions"] >= 3)
    expected_minutes = sum(float(row.get("expected_minutes") or 0) for row in summaries)
    if len(questions) == 20:
        if total_score != 100:
            errors.append(f"paper: expected 100 points, found {total_score:g}")
        if medium_high_score < 75:
            errors.append(f"paper: medium/high discrimination covers only {medium_high_score:g} points; require 75")
        if three_decision_score < 50:
            errors.append(f"paper: three-decision demand covers only {three_decision_score:g} points; require 50")
        if not 80 <= expected_minutes <= 92:
            errors.append(f"paper: expected hand-solving time is {expected_minutes:g} minutes; require 80-92")
        for start in range(len(summaries) - 2):
            if all(row["level"] == "low" for row in summaries[start : start + 3]):
                numbers = [row["number"] for row in summaries[start : start + 3]]
                errors.append(f"paper: three consecutive low-discrimination items {numbers}")
        section_ids = []
        for item in questions:
            sid = str(item.get("section_id", ""))
            if sid not in section_ids:
                section_ids.append(sid)
        for sid in section_ids:
            section_rows = [row for row, item in zip(summaries, questions) if str(item.get("section_id", "")) == sid]
            if section_rows and not any(row["level"] == "high" for row in section_rows):
                errors.append(f"paper: section {sid!r} has no high-discrimination item")

        if subject == "數學A":
            counting_pairs = []
            for item, row in zip(questions, summaries):
                spec = item.get("item_spec") if isinstance(item.get("item_spec"), dict) else {}
                scope_codes = set(str(code) for code in as_list(spec.get("scope_codes")))
                if "D-10-3" in scope_codes:
                    counting_pairs.append((item, row))
            if not counting_pairs:
                errors.append("paper: Math A needs at least one D-10-3 counting/combinatorics item")
            elif not any(
                row["level"] in {"medium", "high"}
                and row["linked_decisions"] >= 3
                and (
                    int((item.get("item_spec") or {}).get("difficulty_design", {}).get("representation_changes") or 0)
                    + int((item.get("item_spec") or {}).get("difficulty_design", {}).get("constraint_checks") or 0)
                ) >= 1
                for item, row in counting_pairs
            ):
                errors.append(
                    "paper: at least one D-10-3 item must have medium/high discrimination, "
                    "three linked decisions, and a representation change or constraint check"
                )
        elif subject == "數學B":
            floor = exam.get("metadata", {}).get("math_b_difficulty_floor", {})
            if floor.get("easy_medium_minimum_linked_decisions") != 3:
                errors.append("paper: Math B difficulty floor must require three decisions for easy/medium items")
            if floor.get("first_three_fill_ins_nonroutine") is not True:
                errors.append("paper: Math B difficulty floor must protect the first three fill-in items")
            if floor.get("audit_status") != "pass":
                errors.append("paper: Math B difficulty-floor audit is not pass")

            fill_ins = sorted(
                [item for item in questions if item.get("type") == "fill_in"],
                key=lambda item: int(item.get("number", 0)),
            )[:3]
            if len(fill_ins) < 3:
                errors.append("paper: Math B needs at least three fill-in items for the opening-fill-in audit")
            for item in fill_ins:
                qid = str(item.get("id", item.get("number")))
                design = (item.get("item_spec") or {}).get("difficulty_design") or {}
                decisions = as_list(design.get("linked_decisions"))
                combined = int(design.get("representation_changes") or 0) + int(design.get("constraint_checks") or 0)
                shortcut = design.get("shortcut_audit") or {}
                if len(decisions) < 3:
                    errors.append(f"{qid}: opening Math B fill-in needs at least three linked decisions")
                if combined < 2:
                    errors.append(f"{qid}: opening Math B fill-in needs two representation/constraint operations")
                if shortcut.get("direct_formula_substitution_only") is not False:
                    errors.append(f"{qid}: opening Math B fill-in collapses to direct substitution")

    report = {
        "status": "pass" if not errors else "fail",
        "subject": subject,
        "question_count": len(questions),
        "total_score": total_score,
        "medium_high_discrimination_score": medium_high_score,
        "three_or_more_linked_decisions_score": three_decision_score,
        "expected_hand_solving_minutes": expected_minutes,
        "items": summaries,
        "errors": errors,
        "note": "Design validation only; achieved P/D require representative pilot data.",
    }
    return report


if __name__ == "__main__":
    raise SystemExit(main())
