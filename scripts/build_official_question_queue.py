#!/usr/bin/env python3
"""Create item-level annotation stubs for official GSAT papers without copying question text."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def section_for(profile: dict[str, Any], number: int) -> dict[str, Any] | None:
    for section in profile.get("sections") or []:
        start = section.get("question_number_start")
        end = section.get("question_number_end")
        if isinstance(start, int) and isinstance(end, int) and start <= number <= end:
            return section
    return None


def build(root: Path) -> int:
    subjects_root = root / "exam_packs" / "學測" / "subjects"
    totals: Counter[str] = Counter()
    years: defaultdict[str, set[int]] = defaultdict(set)
    for paper_path in subjects_root.glob("*/metadata/papers.jsonl"):
        subject = paper_path.parents[1].name
        statistics = {
            (row["year"], row["question_number"]): row
            for row in read_jsonl(paper_path.parent / "official-item-statistics.jsonl")
        }
        rows: list[dict[str, Any]] = []
        for profile in read_jsonl(paper_path):
            if profile.get("source_kind") != "official_past_exam":
                continue
            total = profile.get("numbered_question_count")
            if not isinstance(total, int):
                continue
            question_sources = [item for item in profile["source_files"] if item.get("role") == "question"]
            source = question_sources[0] if question_sources else profile["source_files"][0]
            for number in range(1, total + 1):
                section = section_for(profile, number)
                metric = statistics.get((profile["year"], number))
                missing_fields = [
                    "unit",
                    "skills",
                    "actual_question_type",
                    "difficulty_vector",
                    "literacy_classification",
                    "stimulus_provenance_if_competence",
                    "visual_review",
                ]
                if metric is None:
                    missing_fields.append("difficulty_evidence")
                type_hint = section.get("question_type_mix") if section else {}
                if any(
                    key in {"constructed_response", "guided_writing", "mixed_group"}
                    for key in type_hint
                ) or "非選擇" in str((section or {}).get("title") or ""):
                    missing_fields.append("constructed_response_calibration_if_applicable")
                rows.append({
                    "candidate_id": f"{profile['paper_id']}-q{number:02d}",
                    "exam": "學測",
                    "year": profile["year"],
                    "roc_year": profile["year"] - 1911,
                    "subject": profile["subject"],
                    "curriculum": profile["curriculum"],
                    "regime": profile.get("regime"),
                    "paper_id": profile["paper_id"],
                    "question_number": number,
                    "paper_section": profile.get("section"),
                    "major_section": section.get("title") if section else None,
                    "question_type_hint": type_hint,
                    "actual_question_type": None,
                    "unit": None,
                    "skills": [],
                    "difficulty_overall": metric.get("difficulty_overall") if metric else None,
                    "difficulty_basis": "empirical" if metric else None,
                    "difficulty_vector": {
                        "concept_depth": None,
                        "calculation_depth": None,
                        "reasoning_steps": None,
                        "reading_load": None,
                        "novelty": None,
                        "distractor_strength": None,
                    },
                    "empirical": (
                        {
                            "p_value": metric["p_value"],
                            "p_metric": metric["metric_type"],
                            "discrimination": metric["discrimination"],
                            "sample_size": metric.get("sample_size"),
                            "relative_difficulty_percentile": metric.get("relative_difficulty_percentile"),
                        }
                        if metric
                        else None
                    ),
                    "requires_diagram": None,
                    "literacy": None,
                    "stimulus_provenance": None,
                    "constructed_response_calibration": None,
                    "missing_fields": missing_fields,
                    "source_kind": "official_past_exam",
                    "source_file_sha256": source["sha256"],
                    "source_relative_path": source["relative_path"],
                    "review_status": "pending_semantic_annotation",
                })
        target = paper_path.parent / "official-question-review-queue.jsonl"
        target.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        if rows:
            totals[subject] += len(rows)
            years[subject].update(row["year"] for row in rows)

    report = {
        "schema_version": 1,
        "purpose": "Official item stubs for semantic unit/skill/visual annotation with CEEC P/D evidence when published; no question wording is copied.",
        "candidate_count": sum(totals.values()),
        "by_subject": dict(sorted(totals.items())),
        "year_coverage": {subject: sorted(values) for subject, values in sorted(years.items())},
        "promotion_gate": (
            "Do not promote until unit/skills, actual item type, full difficulty vector, literacy class, "
            "competence-item provenance/timing, visual review, constructed-response calibration where applicable, "
            "and either official P/D evidence or an explicit non-empirical basis are complete."
        ),
    }
    report_path = root / "exam_packs" / "學測" / "metadata" / "official-question-queue-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    return build(args.root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
