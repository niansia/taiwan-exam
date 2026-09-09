#!/usr/bin/env python3
"""Build subject difficulty curves from official CEEC P/D statistics."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def quantile(values: Iterable[float], proportion: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("quantile requires values")
    position = (len(ordered) - 1) * proportion
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def statistics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    p_values = [float(row["p_value"]) for row in rows]
    d_values = [float(row["discrimination"]) for row in rows]
    return {
        "count": len(rows),
        "p_mean": round(mean(p_values), 4),
        "p_median": round(median(p_values), 4),
        "p_q25": round(quantile(p_values, 0.25), 4),
        "p_q75": round(quantile(p_values, 0.75), 4),
        "p_min": min(p_values),
        "p_max": max(p_values),
        "discrimination_median": round(median(d_values), 4),
        "band_counts": dict(sorted(Counter(row["difficulty_band"] for row in rows).items())),
        "metric_type_counts": dict(sorted(Counter(row["metric_type"] for row in rows).items())),
    }


def section_for(profile: dict[str, Any] | None, question_number: int) -> tuple[str, float | None]:
    if not profile:
        return "(unmapped)", None
    for section in profile.get("sections") or []:
        start = section.get("question_number_start")
        end = section.get("question_number_end")
        if isinstance(start, int) and isinstance(end, int) and start <= question_number <= end:
            normalized = 0.0 if start == end else (question_number - start) / (end - start)
            return section["title"], round(normalized, 4)
    return "(unmapped)", None


def select_profile(profiles: list[dict[str, Any]], record: dict[str, Any]) -> dict[str, Any] | None:
    candidates = [
        profile
        for profile in profiles
        if profile.get("source_kind") == "official_past_exam"
        and profile.get("year") == record["year"]
        and profile.get("subject") == record["subject"]
    ]
    if record["subject"] == "國文" and record["roc_year"] >= 111:
        candidates = [profile for profile in candidates if profile.get("section") == "國綜"]
    elif record["subject"] == "國文":
        candidates = [profile for profile in candidates if not profile.get("section")]
    verified = [profile for profile in candidates if profile.get("structure_status") == "verified"]
    return (verified or candidates or [None])[0]


def fingerprint(rows: list[dict[str, Any]]) -> str:
    relevant = [
        {
            "roc_year": row["roc_year"],
            "subject": row["subject"],
            "question_number": row["question_number"],
            "metric_type": row["metric_type"],
            "p_value": row["p_value"],
            "discrimination": row["discrimination"],
            "source_sha256": row["source"]["file_sha256"],
        }
        for row in rows
    ]
    payload = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for row in relevant)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_curriculum(rows: list[dict[str, Any]], profiles: list[dict[str, Any]]) -> dict[str, Any]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        section, normalized_position = section_for(select_profile(profiles, row), row["question_number"])
        enriched.append({**row, "major_section": section, "normalized_section_position": normalized_position})

    years = sorted({row["roc_year"] for row in enriched})
    by_section_rows: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    by_question_rows: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        by_section_rows[row["major_section"]].append(row)
        by_question_rows[row["question_number"]].append(row)

    by_section: dict[str, Any] = {}
    for section, section_rows in sorted(by_section_rows.items()):
        bins: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in section_rows:
            position = row.get("normalized_section_position")
            if position is None:
                continue
            bin_number = min(4, int(position * 5))
            bins[bin_number].append(row)
        by_section[section] = {
            **statistics(section_rows),
            "normalized_position_quintiles": {
                str(bin_number + 1): statistics(bin_rows) for bin_number, bin_rows in sorted(bins.items())
            },
        }

    by_question_number = {
        str(question_number): {
            **statistics(item_rows),
            "roc_years": sorted({row["roc_year"] for row in item_rows}),
            "recommended_target": {
                "p_center": statistics(item_rows)["p_median"],
                "p_range": [statistics(item_rows)["p_q25"], statistics(item_rows)["p_q75"]],
                "discrimination_floor": max(0.20, round(statistics(item_rows)["discrimination_median"] * 0.75, 2)),
            },
        }
        for question_number, item_rows in sorted(by_question_rows.items())
    }
    measured = len(enriched)
    ready = len(years) >= 3 and measured >= 60 and "(unmapped)" not in by_section
    limitations = [
        "P is answer rate for single-choice items and score rate for starred multiple-selection items.",
        "Constructed-response items absent from the official P/D table need rubric-score distributions instead.",
        "Target P is a post-administration property; generated items require pilot data before claiming achieved difficulty.",
    ]
    if "(unmapped)" in by_section:
        limitations.append("At least one official item could not be mapped to a verified paper section.")
    return {
        "status": "ready" if ready else "insufficient-data",
        "scope": "official_objective_items_with_p_or_score_rate",
        "full_paper_status": "insufficient-data",
        "year_count": len(years),
        "roc_years": years,
        "measured_item_count": measured,
        "overall": statistics(enriched),
        "by_section": by_section,
        "by_question_number": by_question_number,
        "limitations": limitations,
    }


def build(root: Path) -> int:
    subjects_root = root / "exam_packs" / "學測" / "subjects"
    built = 0
    for subject_path in sorted(path for path in subjects_root.iterdir() if path.is_dir()):
        statistics_path = subject_path / "metadata" / "official-item-statistics.jsonl"
        rows = read_jsonl(statistics_path)
        if not rows:
            continue
        profiles = read_jsonl(subject_path / "metadata" / "papers.jsonl")
        curricula = sorted({row["curriculum"] for row in rows})
        profile = {
            "schema_version": 1,
            "exam": "學測",
            "subject": subject_path.name,
            "built_at": datetime.now(timezone.utc).isoformat(),
            "official_item_statistics_count": len(rows),
            "source_fingerprint": fingerprint(rows),
            "band_definition": {
                "authority": "skill_local_descriptive_only",
                "very_easy": "P >= 0.80",
                "easy": "0.65 <= P < 0.80",
                "medium": "0.40 <= P < 0.65",
                "hard": "0.20 <= P < 0.40",
                "very_hard": "P < 0.20",
            },
            "curricula": {
                curriculum: build_curriculum([row for row in rows if row["curriculum"] == curriculum], profiles)
                for curriculum in curricula
            },
        }
        target = subject_path / "blueprints" / "difficulty-profile.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"已建立 學測/{subject_path.name} 官方難度曲線：{len(rows)} 筆。")
        built += 1
    print(f"共建立 {built} 份 difficulty profile。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    return build(args.root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
