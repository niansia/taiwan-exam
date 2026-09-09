#!/usr/bin/env python3
"""Measure current Math A/B booklet form without retaining source wording.

ROC 111–115 official papers are the primary corpus.  Same-period publisher
mocks are supplementary form evidence.  The report stores only counts and
layout measurements, never source questions or answer text.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
QUESTION_RE = re.compile(r"^\s*(\d{1,2})\.\s+")
OPTION_RE = re.compile(r"\(\s*([1-5])\s*\)")
EXCLUDE_RE = re.compile(r"答案|詳解|解析|非選擇|評分|解答")


def percentile(values: list[int], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 1)


def layout_signature(option_rows: list[int]) -> str:
    rows = [value for value in option_rows if value]
    if not rows:
        return "none-detected"
    if rows == [5]:
        return "row-5"
    if rows == [4]:
        return "row-4"
    if rows == [3, 2]:
        return "grid-3-2"
    if rows == [2, 2, 1]:
        return "grid-2-2-1"
    if rows == [1, 1, 1, 1, 1]:
        return "stack-5"
    return "rows-" + "-".join(str(value) for value in rows)


def inspect_pdf(path: Path, *, source_kind: str, subject: str, roc_year: int) -> dict[str, Any]:
    segments: dict[int, dict[str, Any]] = {}
    current: int | None = None
    content_page_chars: list[int] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            text = page.extract_text(layout=True) or ""
            compact_page = re.sub(r"\s+", "", text)
            content_page_chars.append(len(compact_page))
            for raw_line in text.splitlines():
                line = raw_line.strip()
                match = QUESTION_RE.match(line)
                if match:
                    candidate = int(match.group(1))
                    if 1 <= candidate <= 25:
                        current = candidate
                        segments.setdefault(current, {"pages": set(), "lines": [], "option_rows": []})
                if current is None or not line:
                    continue
                item = segments[current]
                item["pages"].add(page_number)
                item["lines"].append(line)
                count = len(OPTION_RE.findall(line))
                if count:
                    item["option_rows"].append(count)

    items = []
    for number, data in sorted(segments.items()):
        compact = re.sub(r"\s+", "", "".join(data["lines"]))
        option_rows = data["option_rows"]
        items.append(
            {
                "question_number": number,
                "pages": sorted(data["pages"]),
                "compact_character_count": len(compact),
                "printed_line_count": len(data["lines"]),
                "option_row_counts": option_rows,
                "option_layout": layout_signature(option_rows),
            }
        )
    selected = [item for item in items if item["option_layout"] != "none-detected"]
    return {
        "source_kind": source_kind,
        "subject": subject,
        "roc_year": roc_year,
        "relative_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "page_count": len(content_page_chars),
        "question_count_detected": len(items),
        "selected_item_count_detected": len(selected),
        "selected_item_character_median": (
            round(statistics.median(item["compact_character_count"] for item in selected), 1) if selected else None
        ),
        "option_layout_counts": dict(sorted(Counter(item["option_layout"] for item in selected).items())),
        "items": items,
    }


def official_files() -> list[tuple[Path, str, int]]:
    rows: list[tuple[Path, str, int]] = []
    for subject in ("數學A", "數學B"):
        base = ROOT / "exam_packs" / "學測" / "subjects" / subject / "歷屆試題"
        for roc_year in range(111, 116):
            folder = base / str(roc_year)
            if not folder.is_dir():
                continue
            candidates = [
                path for path in folder.glob("*.pdf")
                if not EXCLUDE_RE.search(path.name) and ("試題" in path.name or "試卷" in path.name)
            ]
            if candidates:
                rows.append((sorted(candidates)[0], subject, roc_year))
    return rows


def mock_files(limit_per_subject_year: int) -> list[tuple[Path, str, int]]:
    buckets: dict[tuple[str, int], list[Path]] = {}
    registry = ROOT / "exam_packs" / "學測" / "metadata" / "source-registry.jsonl"
    if not registry.is_file():
        return []
    rows = [json.loads(line) for line in registry.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    for row in rows:
        if row.get("role") != "question" or row.get("extension") != ".pdf":
            continue
        subject = row.get("subject")
        if subject not in {"數學A", "數學B", "數學（共同範圍模考）"}:
            continue
        roc_year = int(row.get("roc_year") or 0)
        if not 111 <= roc_year <= 115:
            continue
        path = ROOT / row["destination_relative_path"]
        if not path.is_file():
            continue
        buckets.setdefault((subject, roc_year), []).append(path)
    rows: list[tuple[Path, str, int]] = []
    for (subject, roc_year), paths in sorted(buckets.items()):
        for path in sorted(paths)[:limit_per_subject_year]:
            rows.append((path, subject, roc_year))
    return rows


def aggregate(papers: list[dict[str, Any]]) -> dict[str, Any]:
    items = [item for paper in papers for item in paper["items"] if item["option_layout"] != "none-detected"]
    chars = [int(item["compact_character_count"]) for item in items]
    layouts = Counter(item["option_layout"] for item in items)
    horizontal = sum(any(value > 1 for value in item["option_row_counts"]) for item in items)
    return {
        "paper_count": len(papers),
        "subjects": dict(sorted(Counter(paper["subject"] for paper in papers).items())),
        "roc_years": sorted({paper["roc_year"] for paper in papers}),
        "selected_item_count_detected": len(items),
        "selected_item_character_p25": percentile(chars, 0.25),
        "selected_item_character_median": percentile(chars, 0.5),
        "selected_item_character_p75": percentile(chars, 0.75),
        "option_layout_counts": dict(sorted(layouts.items())),
        "horizontal_option_share": round(horizontal / len(items), 4) if items else None,
        "method_warning": "PDF text-layer heuristic; use rendered-page review for promotion.",
    }


def writer_aggregate(papers: list[dict[str, Any]]) -> dict[str, Any]:
    summary = aggregate(papers)
    canonical = {"row-5", "row-4", "grid-3-2", "grid-2-2-1", "stack-5"}
    layouts = summary.pop("option_layout_counts")
    summary["canonical_option_layout_counts"] = {
        key: value for key, value in layouts.items() if key in canonical
    }
    summary["unclassified_layout_signal_count"] = sum(
        value for key, value in layouts.items() if key not in canonical
    )
    return summary


def write_writer_profile(report: dict[str, Any]) -> Path:
    official = [paper for paper in report["papers"] if paper["source_kind"] == "official"]
    mocks = [paper for paper in report["papers"] if paper["source_kind"] == "publisher_mock"]
    writer_report = {
        "schema_version": 1,
        "created_at": report["created_at"],
        "source_visibility": "aggregate-only",
        "individual_question_numbers_included": False,
        "source_paths_included": False,
        "policy": report["policy"],
        "official": {
            subject: writer_aggregate([paper for paper in official if paper["subject"] == subject])
            for subject in ("數學A", "數學B")
        },
        "publisher_mocks": {
            subject: writer_aggregate([paper for paper in mocks if paper["subject"] == subject])
            for subject in ("數學A", "數學B", "數學（共同範圍模考）")
        },
        "release_note": "Layout counts are heuristic aggregates; the renderer still requires an explicit per-item option_layout and rendered-page verification.",
    }
    target = ROOT / "exam_packs" / "學測" / "shared-data" / "current-math-form-writer-profile.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(writer_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock-limit-per-subject-year", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "exam_packs" / "學測" / "metadata" / "recent-math-form-analysis.json",
    )
    parser.add_argument("--from-existing", action="store_true", help="由既有詳細報告重建 aggregate-only writer profile")
    args = parser.parse_args()
    if args.from_existing:
        report = json.loads(args.output.read_text(encoding="utf-8-sig"))
        target = write_writer_profile(report)
        print(json.dumps({"source": str(args.output), "writer_profile": str(target)}, ensure_ascii=False, indent=2))
        return 0
    official = [inspect_pdf(path, source_kind="official", subject=subject, roc_year=year) for path, subject, year in official_files()]
    mocks = [inspect_pdf(path, source_kind="publisher_mock", subject=subject, roc_year=year) for path, subject, year in mock_files(args.mock_limit_per_subject_year)]
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "primary_form_years": [111, 112, 113, 114, 115],
            "official_role": "authoritative structure, difficulty, and final layout shell",
            "publisher_mock_role": "supplementary current-form variation",
            "unlabeled_common_math_role": "shared-unit and print-form evidence only; never a Math A/B full-paper distribution",
            "roc_100_110_role": "content scope and abstract item archetypes only",
        },
        "official": aggregate(official),
        "publisher_mocks": aggregate(mocks),
        "papers": official + mocks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_writer_profile(report)
    print(json.dumps({"output": str(args.output), "official": report["official"], "publisher_mocks": report["publisher_mocks"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
