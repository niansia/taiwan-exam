#!/usr/bin/env python3
"""Parse CEEC GSAT item P/D tables into traceable JSONL calibration data."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

try:
    import xlrd
except ImportError as exc:  # pragma: no cover - dependency error is user-facing
    raise SystemExit("缺少 xlrd。請先執行：python -m pip install -r requirements.txt") from exc


ROOT = Path(__file__).resolve().parents[1]
OLD_SUBJECTS = ("國文", "英文", "數學（舊制）", "社會", "自然")
NEW_SUBJECTS = ("國文", "英文", "數學A", "數學B", "社會", "自然")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isnan(float(value)):
            return None
        return float(value)
    cleaned = str(value).strip().replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def question_number(value: Any) -> tuple[int, bool] | None:
    raw = str(value).strip()
    match = re.fullmatch(r"(\*)?(\d+)(?:\.0)?", raw)
    if not match:
        return None
    return int(match.group(2)), bool(match.group(1))


def difficulty_band_from_p(p_value: float) -> str:
    """Skill-local descriptive bands; CEEC publishes P, not these labels."""
    if p_value >= 0.80:
        return "very_easy"
    if p_value >= 0.65:
        return "easy"
    if p_value >= 0.40:
        return "medium"
    if p_value >= 0.20:
        return "hard"
    return "very_hard"


def overall_from_p(p_value: float) -> int:
    return {"very_easy": 1, "easy": 2, "medium": 3, "hard": 4, "very_hard": 5}[
        difficulty_band_from_p(p_value)
    ]


def sample_size(sheet: Any, header_row: int) -> int | None:
    candidates: list[int] = []
    for row_index in range(header_row):
        for col_index in range(sheet.ncols):
            text = str(sheet.cell_value(row_index, col_index))
            candidates.extend(int(value.replace(",", "")) for value in re.findall(r"\d[\d,]{3,}", text))
    plausible = [value for value in candidates if value >= 1000]
    return max(plausible) if plausible else None


def parse_sheet(
    sheet: Any,
    roc_year: int,
    subject: str,
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    header_row = next(
        (
            row_index
            for row_index in range(sheet.nrows)
            if sheet.ncols > 10
            and str(sheet.cell_value(row_index, 1)).strip() == "P"
            and str(sheet.cell_value(row_index, 10)).strip() == "D"
        ),
        None,
    )
    if header_row is None:
        raise ValueError(f"{roc_year} {subject} 找不到 P/D 欄位")
    cohort = sample_size(sheet, header_row)
    records: list[dict[str, Any]] = []
    for row_index in range(header_row + 1, sheet.nrows):
        parsed_q = question_number(sheet.cell_value(row_index, 0))
        if not parsed_q:
            continue
        item_number, starred = parsed_q
        raw_values = [number(sheet.cell_value(row_index, column)) if column < sheet.ncols else None for column in range(15)]
        p_percent = raw_values[1]
        d_percent = raw_values[10]
        if p_percent is None or d_percent is None or not 0 <= p_percent <= 100:
            continue
        p_value = p_percent / 100
        record: dict[str, Any] = {
            "exam": "學測",
            "roc_year": roc_year,
            "year": roc_year + 1911,
            "subject": subject,
            "curriculum": "108" if roc_year >= 111 else "99",
            "regime": "111學年度起" if roc_year >= 111 else "100-110學年度舊制",
            "question_number": item_number,
            "metric_type": "score_rate" if starred else "answer_rate",
            "p_value": round(p_value, 4),
            "discrimination": round(d_percent / 100, 4),
            "high_group_rate": round(raw_values[2] / 100, 4) if raw_values[2] is not None else None,
            "low_group_rate": round(raw_values[3] / 100, 4) if raw_values[3] is not None else None,
            "ability_quintile_rates": {
                key: round(raw_values[index] / 100, 4) if raw_values[index] is not None else None
                for key, index in (("A", 4), ("B", 5), ("C", 6), ("D", 7), ("E", 8))
            },
            "multiple_selection_marker": starred,
            "sample_size": cohort,
            "difficulty_band": difficulty_band_from_p(p_value),
            "difficulty_overall": overall_from_p(p_value),
            "band_definition": "skill-local-p-value-v1",
            "source": {
                "kind": "official_statistics",
                "publisher": "大學入學考試中心",
                "file_sha256": source["sha256"],
                "relative_path": source["destination_relative_path"],
                "url": source["url"],
                "table_label": source["label"],
                "sheet_index": source["sheet_index"],
                "source_row": row_index + 1,
            },
        }
        # Remove only unavailable optional values; keep nested quintile keys to
        # preserve the official table shape across years.
        records.append({key: value for key, value in record.items() if value is not None})
    return records


def percentile_ranks(records: list[dict[str, Any]]) -> None:
    by_paper: defaultdict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_paper[(record["roc_year"], record["subject"])].append(record)
    for paper_records in by_paper.values():
        ordered = sorted(paper_records, key=lambda item: (-item["p_value"], item["question_number"]))
        denominator = max(1, len(ordered) - 1)
        for rank, record in enumerate(ordered):
            record["relative_difficulty_percentile"] = round(rank / denominator, 4)


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_subject: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    by_paper: defaultdict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_subject[record["subject"]].append(record)
        by_paper[(record["roc_year"], record["subject"])].append(record)

    subject_summary: dict[str, Any] = {}
    for subject, rows in sorted(by_subject.items()):
        p_values = [row["p_value"] for row in rows]
        d_values = [row["discrimination"] for row in rows]
        subject_summary[subject] = {
            "record_count": len(rows),
            "roc_years": sorted({row["roc_year"] for row in rows}),
            "p_mean": round(mean(p_values), 4),
            "p_median": round(median(p_values), 4),
            "p_min": min(p_values),
            "p_max": max(p_values),
            "discrimination_mean": round(mean(d_values), 4),
            "difficulty_band_counts": dict(sorted(Counter(row["difficulty_band"] for row in rows).items())),
        }

    paper_summary: list[dict[str, Any]] = []
    for (roc_year, subject), rows in sorted(by_paper.items()):
        ordered = sorted(rows, key=lambda item: item["question_number"])
        p_values = [row["p_value"] for row in ordered]
        paper_summary.append(
            {
                "roc_year": roc_year,
                "subject": subject,
                "measured_item_count": len(rows),
                "p_mean": round(mean(p_values), 4),
                "p_median": round(median(p_values), 4),
                "difficulty_band_counts": dict(sorted(Counter(row["difficulty_band"] for row in rows).items())),
                "item_curve": [
                    {
                        "question_number": row["question_number"],
                        "p_value": row["p_value"],
                        "discrimination": row["discrimination"],
                        "metric_type": row["metric_type"],
                    }
                    for row in ordered
                ],
            }
        )
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "CEEC annual GSAT item answer/score-rate and discrimination tables",
        "band_definition": {
            "authority": "skill_local_descriptive_only",
            "very_easy": "P >= 0.80",
            "easy": "0.65 <= P < 0.80",
            "medium": "0.40 <= P < 0.65",
            "hard": "0.20 <= P < 0.40",
            "very_hard": "P < 0.20",
            "warning": "CEEC publishes continuous P/D values; these five bins are not official CEEC labels.",
        },
        "record_count": len(records),
        "by_subject": subject_summary,
        "by_paper": paper_summary,
    }


def build(root: Path) -> int:
    metadata_root = root / "exam_packs" / "學測" / "metadata"
    registry = [
        row
        for row in read_jsonl(metadata_root / "official-statistics-registry.jsonl")
        if row.get("table_kind") == "item_metrics_table"
    ]
    if not registry:
        raise SystemExit("找不到 official-statistics-registry.jsonl 的 item_metrics_table；請先下載官方統計。")

    all_records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for source in sorted(registry, key=lambda row: row["roc_year"]):
        path = root / source["destination_relative_path"]
        try:
            workbook = xlrd.open_workbook(path, on_demand=True)
            expected_subjects = NEW_SUBJECTS if source["roc_year"] >= 111 else OLD_SUBJECTS
            if workbook.nsheets != len(expected_subjects):
                raise ValueError(f"預期 {len(expected_subjects)} 張工作表，實際 {workbook.nsheets}")
            for sheet_index, subject in enumerate(expected_subjects):
                sheet_source = {**source, "sheet_index": sheet_index}
                all_records.extend(parse_sheet(workbook.sheet_by_index(sheet_index), source["roc_year"], subject, sheet_source))
            workbook.release_resources()
        except Exception as exc:
            failures.append({"roc_year": source["roc_year"], "path": str(path), "error": f"{type(exc).__name__}: {exc}"})

    percentile_ranks(all_records)
    all_records.sort(key=lambda row: (row["subject"], row["roc_year"], row["question_number"]))
    by_subject: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in all_records:
        by_subject[record["subject"]].append(record)
    for subject, rows in by_subject.items():
        write_jsonl(root / "exam_packs" / "學測" / "subjects" / subject / "metadata" / "official-item-statistics.jsonl", rows)

    report = summarize(all_records)
    report["failures"] = failures
    (metadata_root / "official-difficulty-analysis.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "record_count": len(all_records),
                "subjects": {subject: len(rows) for subject, rows in sorted(by_subject.items())},
                "failures": failures,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    return build(args.root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
