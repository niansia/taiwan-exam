#!/usr/bin/env python3
"""Build a review queue for subject-specific official GSAT Layout Profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def build(root: Path) -> int:
    rows: list[dict[str, Any]] = []
    for paper_path in (root / "exam_packs" / "學測" / "subjects").glob("*/metadata/papers.jsonl"):
        profiles = [
            profile
            for profile in read_jsonl(paper_path)
            if profile.get("source_kind") == "official_past_exam"
            and profile.get("structure_status") == "verified"
            and profile.get("curriculum") == "108"
        ]
        if not profiles:
            continue
        latest = max(profile["year"] for profile in profiles)
        for profile in profiles:
            if profile["year"] != latest:
                continue
            source = next(
                (item for item in profile.get("source_files") or [] if item.get("role") == "question"),
                (profile.get("source_files") or [{}])[0],
            )
            label = profile.get("section") or profile["subject"]
            rows.append(
                {
                    "candidate_profile_id": f"gsat-{profile['year']}-{profile['subject']}-{label}-layout",
                    "exam": "學測",
                    "subject": profile["subject"],
                    "section": profile.get("section"),
                    "curriculum": profile["curriculum"],
                    "regime": profile.get("regime"),
                    "reference_year": profile["year"],
                    "paper_profile_id": profile["paper_id"],
                    "source_file_sha256": source.get("sha256"),
                    "source_relative_path": source.get("relative_path"),
                    "source_page_count": source.get("page_count"),
                    "review_status": "pending_layout_measurement",
                    "required_fields": [
                        "cover_hierarchy",
                        "exact_instruction_transcription",
                        "scoring_instruction_transcription",
                        "page_geometry",
                        "typography",
                        "section_and_question_styles",
                        "running_headers_and_footers",
                        "answer_space_rules",
                        "pagination_contract",
                        "rendered_page_visual_diff",
                    ],
                }
            )
    rows.sort(key=lambda row: (row["subject"], str(row.get("section") or "")))
    target = root / "exam_packs" / "學測" / "metadata" / "layout-review-queue.jsonl"
    target.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    report = {
        "schema_version": 1,
        "candidate_count": len(rows),
        "reference_years": sorted({row["reference_year"] for row in rows}),
        "subjects": sorted({row["subject"] for row in rows}),
        "status": "pending-review",
        "gate": "No candidate becomes verified until instructions are transcribed and every rendered page passes visual review.",
    }
    (target.parent / "layout-review-queue-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(build(ROOT))
