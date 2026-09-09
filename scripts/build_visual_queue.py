#!/usr/bin/env python3
"""Expand the PDF visual-signal index into a human/model annotation queue."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "sha256", "year", "subject", "publisher", "bundle", "source_role", "destination_relative_path",
    "page_number", "signal", "annotation_status", "question_numbers", "visual_kind", "visual_subtype",
    "item_role", "layout", "generation_mode", "information_density", "visual_reasoning_steps",
    "entity_count", "panel_count", "label_count", "data_series_count", "distractor_salience",
    "precision", "scale_required", "color_dependency", "source_rights", "notes",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def build(root: Path) -> int:
    metadata = root / "exam_packs" / "學測" / "metadata"
    source = metadata / "visual-source-index.jsonl"
    target = metadata / "visual-annotation-queue.csv"
    rows: list[dict[str, Any]] = []
    for item in read_jsonl(source):
        pages = sorted(set(item.get("pages_with_raster") or []) | set(item.get("pages_with_vector_signal") or []))
        if not pages and item.get("analysis_status") != "ok":
            pages = [""]
        for page in pages:
            rows.append({
                "sha256": item["sha256"],
                "year": item["year"],
                "subject": item["subject"],
                "publisher": item["publisher"],
                "bundle": item["bundle"],
                "source_role": item["role"],
                "destination_relative_path": item["destination_relative_path"],
                "page_number": page,
                "signal": item["visual_signal"],
                "annotation_status": "pending" if page != "" else "needs_manual_probe",
            })
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"已建立 {target.relative_to(root)}；共 {len(rows)} 個候選頁面。")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="建立視覺題人工／模型標註佇列")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    return build(args.root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
