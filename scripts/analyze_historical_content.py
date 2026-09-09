#!/usr/bin/env python3
"""Build a source-blind pre-111 content/archetype envelope for current GSAT writers."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_CURRICULUM = "historical-pre-111"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def normalized_label(value: Any) -> str | None:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"\s*難\s*易\s*度\s*[:：].*$", "", text).strip()
    return text if 2 <= len(text) <= 120 else None


def recurring_labels(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    observations: dict[str, list[int]] = defaultdict(list)
    for record in records:
        value = (
            record.get("unit")
            or record.get("explicit_source_unit")
            or record.get("explicit_content")
            or record.get("explicit_objective")
        )
        label = normalized_label(value)
        year = record.get("year")
        if label and isinstance(year, int):
            observations[label].append(year)
    output = [
        {"label": label, "observation_count": len(years), "year_count": len(set(years))}
        for label, years in observations.items()
        if len(years) >= 2 and len(set(years)) >= 2
    ]
    return sorted(output, key=lambda item: (-item["year_count"], -item["observation_count"], item["label"]))


def build(root: Path, output: Path) -> dict[str, Any]:
    pack = root / "exam_packs" / "學測"
    registry = [
        row for row in read_jsonl(pack / "metadata" / "source-registry.jsonl")
        if row.get("curriculum") == HISTORICAL_CURRICULUM
    ]
    profiles: list[dict[str, Any]] = []
    promoted: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    for subject_dir in (pack / "subjects").iterdir():
        profiles.extend(
            row for row in read_jsonl(subject_dir / "metadata" / "papers.jsonl")
            if row.get("curriculum") == HISTORICAL_CURRICULUM
        )
        promoted.extend(
            row for row in read_jsonl(subject_dir / "metadata" / "questions.jsonl")
            if row.get("curriculum") == HISTORICAL_CURRICULUM
        )
        review.extend(
            row for row in read_jsonl(subject_dir / "metadata" / "question-review-queue.jsonl")
            if row.get("curriculum") == HISTORICAL_CURRICULUM
        )

    subjects = sorted({str(row.get("subject")) for row in registry if row.get("subject") != "shared"})
    content: dict[str, Any] = {}
    for subject in subjects:
        valid = [row for row in promoted if row.get("subject") == subject]
        pending = [row for row in review if row.get("subject") == subject]
        subject_profiles = [row for row in profiles if row.get("subject") == subject]
        response_types = Counter()
        for profile in subject_profiles:
            for section in profile.get("sections") or []:
                response_types.update(section.get("question_type_mix") or {})
        content[subject] = {
            "promoted_metadata_count": len(valid),
            "pending_metadata_count": len(pending),
            "profile_count": len(subject_profiles),
            "profile_status_counts": dict(sorted(Counter(str(row.get("structure_status")) for row in subject_profiles).items())),
            "domain_counts": dict(sorted(Counter(str(row.get("domain")) for row in valid if row.get("domain")).items())),
            "question_type_counts": dict(sorted(Counter(str(row.get("question_type")) for row in valid).items())),
            "historical_response_type_evidence": dict(sorted(response_types.items())),
            "difficulty_label_counts": dict(sorted(Counter(str((row.get("difficulty") or {}).get("overall")) for row in valid).items())),
            "recurring_content_labels": recurring_labels(valid + pending),
        }

    years = sorted({int(row["year"]) for row in registry if isinstance(row.get("year"), int)})
    payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "content-and-archetype-only; OCR coverage incomplete",
        "policy": {
            "allowed_uses": [
                "expand in-syllabus content coverage",
                "increase abstract reasoning-archetype diversity",
                "identify historically recurring curriculum labels",
            ],
            "forbidden_uses_for_current_gsat": [
                "question count or section recipe",
                "current wording or passage length",
                "current literacy-item share",
                "current option geometry or page layout",
                "Math A or Math B position/difficulty curve",
                "English current cloze or mixed-section structure",
                "single-source item skeleton, numeric tuple, equation order, or figure topology",
            ],
            "current_form_authority": "ROC 111-115 official papers and compatible current mocks only",
        },
        "inventory": {
            "file_count": len(registry),
            "year_range": [min(years), max(years)] if years else None,
            "year_count": len(years),
            "by_subject": dict(sorted(Counter(str(row.get("subject")) for row in registry).items())),
            "by_role": dict(sorted(Counter(str(row.get("role")) for row in registry).items())),
            "by_text_layer": dict(sorted(Counter(str(row.get("text_layer_status")) for row in registry).items())),
        },
        "content_evidence": content,
        "manual_visual_review": {
            "scope": "one representative historical mathematics paper per ROC year 101-110",
            "allowed_aggregate_archetypes": [
                "coordinate or function graph used as mathematical evidence",
                "geometry or incidence diagram used for deduction",
                "table or recorded measurements used for modelling",
                "finite pattern or combinatorial figure used for counting",
                "self-contained life or data context reduced to syllabus operations",
            ],
            "use_rule": "Use only to diversify representation roles. Invent all objects, values, solution graphs, and visual topology anew.",
        },
        "limitations": [
            "Scan/image-only papers are indexed but do not contribute semantic labels until OCR or manual review.",
            "Publisher difficulty labels are expert review, not official CEEC P/D.",
            "Rare one-paper labels are suppressed to reduce source fingerprinting and template imitation.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "exam_packs" / "學測" / "shared-data" / "historical-content-envelope.json",
    )
    args = parser.parse_args()
    payload = build(args.root.resolve(), args.output.resolve())
    print(json.dumps({
        "output": str(args.output.resolve()),
        "status": payload["status"],
        "inventory": payload["inventory"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
