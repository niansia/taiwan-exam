#!/usr/bin/env python3
"""Create a copyright-safe aggregate analysis for one ingested mock bundle."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
ITEM_MARKER = re.compile(r"(?m)^\s*(\d{1,2})\s*[.．、]")
GROUP_CUE = re.compile(r"第\s*\d{1,2}\s*(?:[.．、]\s*)?(?:至|[-~～、])\s*\d{1,2}\s*[.．、]?\s*題為題組")
VISUAL_CUE = re.compile(r"(?:圖|表)\s*(?:\d+|[一二三四五六七八九十甲乙丙丁])|地圖|流程圖|示意圖|數據")
SOURCE_CUE = re.compile(r"新聞|報導|研究|調查|政府|官方|法案|判決|實驗|文獻|統計|資料顯示|根據|依據")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def counts(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter("(unknown)" if value is None else str(value) for value in values).items()))


def slug(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z]+", "-", value).strip("-").lower()
    return cleaned or "mock-bundle"


def text_form_metrics(path: Path, numbered_total: int | None) -> dict[str, Any]:
    reader = PdfReader(path, strict=False)
    body = "\n".join(page.extract_text() or "" for page in reader.pages[1:])
    compact_chars = len(re.sub(r"\s+", "", body))
    matches = [
        match for match in ITEM_MARKER.finditer(body)
        if 1 <= int(match.group(1)) and (numbered_total is None or int(match.group(1)) <= numbered_total)
    ]
    first_by_number: dict[int, Any] = {}
    for match in matches:
        first_by_number.setdefault(int(match.group(1)), match)
    ordered = sorted(first_by_number.values(), key=lambda item: item.start())
    block_lengths = [
        len(re.sub(r"\s+", "", body[item.start() : ordered[index + 1].start() if index + 1 < len(ordered) else len(body)]))
        for index, item in enumerate(ordered)
    ]
    years = [int(value) for value in re.findall(r"(?<!\d)(20\d{2})(?!\d)", body)]
    return {
        "page_count": len(reader.pages),
        "body_nonwhitespace_chars": compact_chars,
        "extracted_numbered_block_count": len(block_lengths),
        "block_chars": {
            "median": round(statistics.median(block_lengths), 1) if block_lengths else None,
            "mean": round(statistics.mean(block_lengths), 1) if block_lengths else None,
            "p75": round(statistics.quantiles(block_lengths, n=4)[2], 1) if len(block_lengths) >= 4 else None,
            "maximum": max(block_lengths) if block_lengths else None,
        },
        "option_marker_count": len(re.findall(r"[（(]\s*[）)]\s*[A-E1-5]", body)),
        "group_range_cue_count": len(GROUP_CUE.findall(body)),
        "visual_or_data_cue_count": len(VISUAL_CUE.findall(body)),
        "source_context_cue_count": len(SOURCE_CUE.findall(body)),
        "mentioned_calendar_years": counts(years),
    }


def build(root: Path, bundle: str, output: Path | None) -> Path:
    metadata_root = root / "exam_packs" / "學測" / "metadata"
    registry = [row for row in read_jsonl(metadata_root / "source-registry.jsonl") if row.get("bundle") == bundle]
    if not registry:
        raise ValueError(f"來源索引中找不到套卷：{bundle}")
    source_hashes = {row["sha256"] for row in registry}
    subject_root = root / "exam_packs" / "學測" / "subjects"
    profiles: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    for path in subject_root.glob("*/metadata/papers.jsonl"):
        profiles.extend(row for row in read_jsonl(path) if row.get("bundle") == bundle)
    for path in subject_root.glob("*/metadata/questions.auto.jsonl"):
        candidates.extend(
            row for row in read_jsonl(path) if (row.get("source") or {}).get("file_sha256") in source_hashes
        )
    for path in subject_root.glob("*/metadata/question-review-queue.jsonl"):
        review.extend(row for row in read_jsonl(path) if row.get("source_file_sha256") in source_hashes)
    visuals = [
        row for row in read_jsonl(metadata_root / "visual-source-index.jsonl")
        if row.get("sha256") in source_hashes
    ]
    profiles_by_key = {(row["subject"], row.get("section") or ""): row for row in profiles}
    by_subject: dict[str, Any] = {}
    for subject in sorted({row["subject"] for row in registry if row.get("subject") != "shared"}):
        sources = [row for row in registry if row["subject"] == subject]
        subject_profiles = [row for row in profiles if row["subject"] == subject]
        subject_candidates = [row for row in candidates if row["subject"] == subject]
        subject_review = [row for row in review if row["subject"] == subject]
        question_metrics = []
        for row in sources:
            if row.get("role") != "question" or row.get("extension") != ".pdf":
                continue
            profile = profiles_by_key.get((subject, row.get("section") or ""))
            path = root / row["destination_relative_path"]
            try:
                metrics = text_form_metrics(path, (profile or {}).get("numbered_question_count"))
                metrics["analysis_status"] = "ok"
            except Exception as exc:
                metrics = {"analysis_status": "failed", "error": f"{type(exc).__name__}: {exc}"[:240]}
            metrics["section"] = row.get("section")
            metrics["sha256_prefix"] = row["sha256"][:12]
            question_metrics.append(metrics)
        subject_visuals = [row for row in visuals if row.get("subject") == subject and row.get("role") == "question"]
        unit_values = [row.get("unit") for row in subject_candidates]
        unit_values.extend(row.get("explicit_source_unit") for row in subject_review if row.get("explicit_source_unit"))
        by_subject[subject] = {
            "source_files": {
                "count": len(sources),
                "roles": counts([row.get("role") for row in sources]),
                "pages": sum(row.get("pdf_pages") or 0 for row in sources),
                "text_layer": counts([row.get("text_layer_status") for row in sources]),
            },
            "paper_profiles": [
                {
                    "section": row.get("section"),
                    "duration_minutes": row.get("duration_minutes"),
                    "total_score": row.get("total_score"),
                    "numbered_question_count": row.get("numbered_question_count"),
                    "scored_item_count": row.get("scored_item_count"),
                    "structure_status": row.get("structure_status"),
                    "confidence": (row.get("evidence") or {}).get("confidence"),
                    "sections": row.get("sections"),
                }
                for row in subject_profiles
            ],
            "item_metadata": {
                "promotable_count": len(subject_candidates),
                "review_queue_count": len(subject_review),
                "difficulty_distribution": counts([(row.get("difficulty") or {}).get("overall") for row in subject_candidates]),
                "missing_fields": counts([field for row in subject_review for field in row.get("missing_fields") or []]),
                "domain_distribution": counts([row.get("domain") for row in subject_candidates]),
                "unit_label_count": len({str(value) for value in unit_values if value}),
                "top_unit_labels": counts([value for value in unit_values if value]),
            },
            "question_text_form": question_metrics,
            "visual_evidence": [
                {
                    "page_count": row.get("page_count"),
                    "visual_signal": row.get("visual_signal"),
                    "candidate_visual_page_count": len(set((row.get("pages_with_raster") or []) + (row.get("pages_with_vector_signal") or []))),
                    "raster_object_count": row.get("raster_object_count"),
                    "vector_operation_count": row.get("vector_operation_count"),
                    "analysis_status": row.get("analysis_status"),
                }
                for row in subject_visuals
            ],
        }
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "exam": "學測",
        "bundle": bundle,
        "year": next(iter({row.get("year") for row in registry}), None),
        "publisher": next(iter({row.get("publisher") for row in registry}), None),
        "scope": next(iter({row.get("scope") for row in registry}), None),
        "source_file_count": len(registry),
        "unique_source_hash_count": len(source_hashes),
        "subjects": by_subject,
        "integration_gate": {
            "promotable_item_count": len(candidates),
            "pending_review_item_count": len(review),
            "empirical_difficulty_count": sum(bool(row.get("empirical")) for row in candidates),
            "policy": "Only schema-valid, explicitly supported metadata may enter questions.jsonl and aggregate writer blueprints.",
        },
        "limits": [
            "Mentioned calendar years are topic-timing cues, not publication dates or editorial lead-time evidence.",
            "Source-context cue counts do not classify an item as competence-oriented and do not replace the stimulus-removal test.",
            "No difficulty is inferred when the publisher solution omits a difficulty label; such items stay in the review queue.",
            "The report contains aggregate signals only and is not an item-writing seed library.",
        ],
    }
    target = output or metadata_root / "bundle-analyses" / f"{slug(bundle)}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        target = build(args.root.resolve(), args.bundle, args.output.resolve() if args.output else None)
        print(target)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"錯誤：{exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
