#!/usr/bin/env python3
"""Audit mock-exam coverage and calibration evidence without copying question text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def count(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter("(unknown)" if value is None else str(value) for value in values).items()))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def score_statistics_evidence(root: Path, registry: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row for row in registry if row.get("role") == "score_statistics"]
    extractable: list[dict[str, Any]] = []
    for row in rows:
        if row.get("text_layer_status") != "extractable" or row.get("extension") != ".pdf":
            continue
        path = root / row["destination_relative_path"]
        try:
            text = "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
        except Exception as exc:
            extractable.append(
                {
                    "bundle": row.get("bundle"),
                    "source": row.get("original_relative_path"),
                    "parse_error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        dates = sorted(set(re.findall(r"考試日期\s*[：:]\s*(\d{4}/\d{2}/\d{2})", text)))
        cohorts = sorted({int(value) for value in re.findall(r"到考人數\s*[：:]\s*(\d+)\s*人", text)})
        extractable.append(
            {
                "bundle": row.get("bundle"),
                "publisher": row.get("publisher"),
                "source": row.get("original_relative_path"),
                "exam_dates": dates,
                "cohort_sizes": cohorts,
                "contains_five_standards": all(label in text for label in ("頂標", "前標", "均標", "後標", "底標")),
                "contains_raw_score_conversion": "原始分數與級分對照" in text or "級距" in text,
            }
        )
    return {
        "file_count": len(rows),
        "bundle_count": len({row.get("bundle") for row in rows}),
        "text_layer_status": count([row.get("text_layer_status") for row in rows]),
        "publisher_counts": count([row.get("publisher") for row in rows]),
        "extractable_file_evidence": extractable,
        "interpretation": (
            "These files can calibrate whole-paper score severity for their documented cohorts. "
            "They cannot supply per-item P/D unless an item-analysis table is present."
        ),
    }


def build(root: Path, intake: Path) -> int:
    registry_path = root / "exam_packs" / "學測" / "metadata" / "source-registry.jsonl"
    registry = read_jsonl(registry_path)
    intake_files = [path for path in intake.rglob("*") if path.is_file()] if intake.is_dir() else []
    intake_hashes = {sha256_file(path) for path in intake_files}
    profiles: list[dict[str, Any]] = []
    questions: list[dict[str, Any]] = []
    for path in (root / "exam_packs" / "學測" / "subjects").glob("*/metadata/papers.jsonl"):
        profiles.extend(row for row in read_jsonl(path) if row.get("source_kind") == "mock_exam")
    for path in (root / "exam_packs" / "學測" / "subjects").glob("*/metadata/questions.jsonl"):
        questions.extend(row for row in read_jsonl(path) if (row.get("source") or {}).get("kind") == "mock_exam")

    ready_profiles = [
        row
        for row in profiles
        if row.get("structure_status") == "verified"
        or (
            row.get("structure_status") == "auto_parsed"
            and (row.get("evidence") or {}).get("confidence", 0) >= 0.9
        )
    ]
    vector_fields = (
        "concept_depth", "calculation_depth", "reasoning_steps", "reading_load", "novelty", "distractor_strength"
    )
    full_vectors = [
        row for row in questions if all((row.get("difficulty") or {}).get(field) is not None for field in vector_fields)
    ]
    empirical = [row for row in questions if row.get("empirical")]
    literacy = [row for row in questions if isinstance(row.get("literacy"), dict)]
    provenance = [row for row in questions if isinstance(row.get("stimulus_provenance"), dict)]

    by_subject_profile: dict[str, Any] = {}
    for subject in sorted({row["subject"] for row in profiles}):
        subject_rows = [row for row in profiles if row["subject"] == subject]
        subject_ready = [row for row in ready_profiles if row["subject"] == subject]
        by_subject_profile[subject] = {
            "paper_count": len(subject_rows),
            "ready_structure_count": len(subject_ready),
            "status_counts": count([row.get("structure_status") for row in subject_rows]),
            "publishers": count([row.get("publisher") for row in subject_rows]),
            "year_count": len({row.get("year") for row in subject_rows}),
        }

    by_subject_question: dict[str, Any] = {}
    for subject in sorted({row["subject"] for row in questions}):
        rows = [row for row in questions if row["subject"] == subject]
        by_subject_question[subject] = {
            "item_metadata_count": len(rows),
            "year_count": len({row["year"] for row in rows}),
            "difficulty_basis_counts": count([(row.get("difficulty") or {}).get("basis") for row in rows]),
            "difficulty_overall_counts": count([(row.get("difficulty") or {}).get("overall") for row in rows]),
            "empirical_count": sum(bool(row.get("empirical")) for row in rows),
            "full_difficulty_vector_count": sum(row in full_vectors for row in rows),
            "literacy_annotation_count": sum(row in literacy for row in rows),
            "stimulus_provenance_count": sum(row in provenance for row in rows),
        }

    registry_hashes = {row.get("sha256") for row in registry if row.get("sha256")}
    matched_registry_rows = [row for row in registry if row.get("sha256") in intake_hashes]
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "intake": {
            "path": intake.name,
            "file_count": len(intake_files),
            "unique_sha256_count": len(intake_hashes),
            "registry_match_count": len(intake_hashes & registry_hashes),
            "fully_indexed": bool(intake_files) and intake_hashes <= registry_hashes,
            "resolved_bundles": sorted({str(row.get("bundle")) for row in matched_registry_rows if row.get("bundle")}),
            "top_level_directory_count": len([path for path in intake.iterdir() if path.is_dir()]) if intake.is_dir() else 0,
        },
        "registry": {
            "record_count": len(registry),
            "unique_sha256_count": len(registry_hashes),
            "bundle_count": len({row.get("bundle") for row in registry}),
            "publishers": count([row.get("publisher") for row in registry]),
            "subjects": count([row.get("subject") for row in registry]),
            "roles": count([row.get("role") for row in registry]),
            "text_layer_status": count([row.get("text_layer_status") for row in registry]),
            "score_statistics_files": sum(row.get("role") == "score_statistics" for row in registry),
        },
        "score_statistics": score_statistics_evidence(root, registry),
        "paper_profiles": {
            "count": len(profiles),
            "ready_structure_count": len(ready_profiles),
            "by_subject": by_subject_profile,
        },
        "item_metadata": {
            "count": len(questions),
            "empirical_count": len(empirical),
            "full_difficulty_vector_count": len(full_vectors),
            "literacy_annotation_count": len(literacy),
            "stimulus_provenance_count": len(provenance),
            "by_subject": by_subject_question,
        },
        "findings": [
            "The intake is fully indexed only when every unique intake hash appears in the merged registry; registry size may exceed one intake.",
            "Publisher difficulty labels are expert labels, not CEEC-equivalent empirical P values.",
            "Score-standard files can calibrate whole-paper severity but cannot assign item difficulty.",
            "Image/outline PDFs require OCR or manual review before structural or semantic promotion.",
            "A full mock paper must remain blocked while official semantic anchors, multidimensional difficulty, or literacy-source annotations are incomplete.",
        ],
    }
    target = root / "exam_packs" / "學測" / "metadata" / "mock-dataset-audit.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--intake",
        type=Path,
        required=True,
        help="本次要稽核的原始資料夾；只讀取，不會移動或刪除。",
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    return build(args.root.resolve(), args.intake.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
