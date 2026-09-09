#!/usr/bin/env python3
"""Summarize official GSAT structure and empirical difficulty by regime."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def regime(roc_year: int) -> str:
    if roc_year >= 111:
        return "111-present_108-curriculum"
    if roc_year >= 107:
        return "107-110_transition"
    return "100-106_old-structure"


def stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    p_values = [float(row["p_value"]) for row in rows]
    d_values = [float(row["discrimination"]) for row in rows]
    return {
        "item_count": len(rows),
        "roc_years": sorted({row["roc_year"] for row in rows}),
        "p_mean": round(mean(p_values), 4),
        "p_median": round(median(p_values), 4),
        "p_min": min(p_values),
        "p_max": max(p_values),
        "discrimination_mean": round(mean(d_values), 4),
        "band_counts": dict(sorted(Counter(row["difficulty_band"] for row in rows).items())),
    }


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    x_mean = mean(xs)
    y_mean = mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys))
    return round(numerator / denominator, 4) if denominator else None


def latest_structures(subject_path: Path, subject: str) -> list[dict[str, Any]]:
    profiles = [
        row
        for row in read_jsonl(subject_path / "metadata" / "papers.jsonl")
        if row.get("source_kind") == "official_past_exam"
        and row.get("structure_status") == "verified"
        and row.get("year", 0) >= 2022
    ]
    if not profiles:
        return []
    latest_year = max(row["year"] for row in profiles)
    result = []
    for profile in profiles:
        if profile["year"] != latest_year:
            continue
        result.append(
            {
                "paper_id": profile["paper_id"],
                "year": profile["year"],
                "section": profile.get("section"),
                "duration_minutes": profile.get("duration_minutes"),
                "total_score": profile.get("total_score"),
                "numbered_question_count": profile.get("numbered_question_count"),
                "scored_item_count": profile.get("scored_item_count"),
                "source_kind": profile.get("source_kind"),
                "sections": [
                    {
                        "title": section.get("title"),
                        "question_number_start": section.get("question_number_start"),
                        "question_number_end": section.get("question_number_end"),
                        "numbered_question_count": section.get("numbered_question_count"),
                        "scored_item_count": section.get("scored_item_count"),
                        "question_type_mix": section.get("question_type_mix"),
                        "subtotal_score": section.get("subtotal_score"),
                        "score_rule": section.get("score_rule"),
                    }
                    for section in profile.get("sections") or []
                ],
                "layout_evidence_status": "not-yet-verified",
            }
        )
    return result


def structure_series(subject_path: Path) -> dict[str, Any]:
    profiles = [
        row
        for row in read_jsonl(subject_path / "metadata" / "papers.jsonl")
        if row.get("source_kind") == "official_past_exam"
    ]
    return {
        "paper_count": len(profiles),
        "year_count": len({row.get("year") for row in profiles}),
        "status_counts": dict(sorted(Counter(row.get("structure_status") for row in profiles).items())),
        "papers": [
            {
                "paper_id": row.get("paper_id"),
                "year": row.get("year"),
                "roc_year": row.get("year", 1911) - 1911,
                "regime": regime(row.get("year", 1911) - 1911),
                "section": row.get("section"),
                "duration_minutes": row.get("duration_minutes"),
                "total_score": row.get("total_score"),
                "numbered_question_count": row.get("numbered_question_count"),
                "structure_status": row.get("structure_status"),
                "confidence": (row.get("evidence") or {}).get("confidence"),
            }
            for row in sorted(profiles, key=lambda item: (item.get("year", 0), str(item.get("section") or "")))
        ],
        "warning": "Only verified profiles may define a formal full paper; auto-parsed historical rows remain audit evidence.",
    }


def math_opening_curve(rows: list[dict[str, Any]], length: int) -> dict[str, Any]:
    by_year: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["roc_year"] >= 111 and 1 <= row["question_number"] <= length:
            by_year[row["roc_year"]].append(row)
    annual = []
    by_position: defaultdict[int, list[float]] = defaultdict(list)
    for year, year_rows in sorted(by_year.items()):
        ordered = sorted(year_rows, key=lambda row: row["question_number"])
        for row in ordered:
            by_position[row["question_number"]].append(row["p_value"])
        annual.append(
            {
                "roc_year": year,
                "p_values": [row["p_value"] for row in ordered],
                "position_p_correlation": pearson(
                    [float(row["question_number"]) for row in ordered],
                    [float(row["p_value"]) for row in ordered],
                ),
            }
        )
    medians = [round(median(by_position[position]), 4) for position in sorted(by_position)]
    return {
        "section": "opening single-choice",
        "positions": sorted(by_position),
        "position_p_medians": medians,
        "position_p_correlation": pearson([float(value) for value in sorted(by_position)], medians),
        "annual_curves": annual,
        "interpretation": (
            "Negative correlation means later positions tend to be harder, but annual exceptions are preserved. "
            "This is a target curve, not a rule that every adjacent item must be harder."
        ),
    }


def build(root: Path) -> int:
    subjects_root = root / "exam_packs" / "學測" / "subjects"
    subject_reports: dict[str, Any] = {}
    for subject_path in sorted(path for path in subjects_root.iterdir() if path.is_dir()):
        rows = read_jsonl(subject_path / "metadata" / "official-item-statistics.jsonl")
        if not rows:
            continue
        by_regime: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            by_regime[regime(row["roc_year"])].append(row)
        report: dict[str, Any] = {
            "official_item_statistics_count": len(rows),
            "by_regime": {name: stats(group) for name, group in sorted(by_regime.items())},
            "structure_series": structure_series(subject_path),
            "latest_verified_structures": latest_structures(subject_path, subject_path.name),
        }
        if subject_path.name == "數學A":
            report["current_opening_curve"] = math_opening_curve(rows, 6)
        elif subject_path.name == "數學B":
            report["current_opening_curve"] = math_opening_curve(rows, 7)
        subject_reports[subject_path.name] = report

    output = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "exam": "學測",
        "official_coverage": {
            "roc_year_start": 100,
            "roc_year_end": 115,
            "regime_rule": "Never pool 100-106, 107-110, and 111-present as one generation population.",
        },
        "difficulty_interpretation": {
            "primary_metrics": ["official P (answer/score rate)", "official D (discrimination)"],
            "bands": "Skill-local descriptive bins only; not CEEC official labels.",
            "generated_item_warning": "A target P is not an achieved P until representative pilot data exist.",
            "constructed_response_warning": "Objective-item P/D tables do not calibrate unlisted constructed-response slots.",
        },
        "subjects": subject_reports,
    }
    target = root / "exam_packs" / "學測" / "metadata" / "official-pattern-analysis.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target), "subjects": sorted(subject_reports)}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    return build(ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
