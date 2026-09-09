#!/usr/bin/env python3
"""Triage lexical similarity without exporting source-question wording.

This script is deliberately unable to approve originality on its own.  It
identifies nearest textual neighbors and carries through the mandatory LLM
structural-review state stored in each generated Item Spec.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path
from typing import Any

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
QUESTION_RE = re.compile(r"^\s*(\d{1,2})\.\s+")
EXCLUDE_RE = re.compile(r"答案|詳解|解析|非選擇題參考答案|評分原則")


def compact(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u3400-\u9fff]+", "", text).lower()


def abstract(text: str) -> str:
    value = compact(text)
    value = re.sub(r"\d+(?:\.\d+)?", "N", value)
    value = re.sub(r"[a-z]+", "V", value)
    return value


def shingles(text: str, size: int) -> set[str]:
    if len(text) < size:
        return {text} if text else set()
    return {text[index:index + size] for index in range(len(text) - size + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def split_pdf(path: Path) -> list[dict[str, Any]]:
    segments: dict[int, list[str]] = {}
    current: int | None = None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True) or ""
            for raw_line in text.splitlines():
                line = raw_line.strip()
                match = QUESTION_RE.match(line)
                if match:
                    number = int(match.group(1))
                    if 1 <= number <= 99:
                        current = number
                        segments.setdefault(number, [])
                if current is not None and line:
                    segments[current].append(line)
    return [
        {"question_number": number, "text": "".join(lines)}
        for number, lines in sorted(segments.items())
        if len(compact("".join(lines))) >= 24
    ]


def official_sources(subject: str) -> list[Path]:
    base = ROOT / "exam_packs" / "學測" / "subjects" / subject / "歷屆試題"
    paths: list[Path] = []
    for roc_year in range(111, 116):
        folder = base / str(roc_year)
        if not folder.is_dir():
            continue
        candidates = [
            path for path in folder.glob("*.pdf")
            if not EXCLUDE_RE.search(path.name) and ("試題" in path.name or "試卷" in path.name)
        ]
        if candidates:
            paths.append(sorted(candidates)[0])
    return paths


def mock_sources(subject: str) -> list[Path]:
    registry = ROOT / "exam_packs" / "學測" / "metadata" / "source-registry.jsonl"
    if not registry.is_file():
        return []
    accepted_subjects = {subject}
    if subject in {"數學A", "數學B"}:
        accepted_subjects.add("數學（共同範圍模考）")
    paths: set[Path] = set()
    for line in registry.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("extension") != ".pdf" or row.get("role") not in {"question", "question_and_solution"}:
            continue
        if row.get("subject") not in accepted_subjects:
            continue
        path = ROOT / row["destination_relative_path"]
        if path.is_file():
            paths.add(path)
    return sorted(paths)


def source_records(subject: str, include_mocks: bool) -> list[dict[str, Any]]:
    seen: set[Path] = set()
    records: list[dict[str, Any]] = []
    for kind, paths in (("official", official_sources(subject)), ("publisher_mock", mock_sources(subject) if include_mocks else [])):
        for path in paths:
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            for item in split_pdf(path):
                records.append(
                    {
                        "source_kind": kind,
                        "relative_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "question_number": item["question_number"],
                        "raw": compact(item["text"]),
                        "abstract": abstract(item["text"]),
                    }
                )
    return records


def generated_text(item: dict[str, Any]) -> str:
    options = "".join(str(option.get("text") or "") for option in item.get("options") or [])
    return "".join(
        str(value or "")
        for value in (item.get("group_stimulus"), item.get("prompt"), options)
    )


def audit_item(item: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    raw = compact(generated_text(item))
    abstracted = abstract(generated_text(item))
    raw_shingles = shingles(raw, 4)
    neighbors = []
    for source in sources:
        raw_jaccard = jaccard(raw_shingles, shingles(source["raw"], 4))
        abstract_ratio = difflib.SequenceMatcher(None, abstracted, source["abstract"], autojunk=False).ratio()
        risk_score = max(raw_jaccard, abstract_ratio * 0.72)
        neighbors.append(
            {
                "source_kind": source["source_kind"],
                "relative_path": source["relative_path"],
                "question_number": source["question_number"],
                "raw_fourgram_jaccard": round(raw_jaccard, 4),
                "abstract_sequence_ratio": round(abstract_ratio, 4),
                "risk_score": round(risk_score, 4),
            }
        )
    top = sorted(neighbors, key=lambda row: row["risk_score"], reverse=True)[:3]
    lexical_flag = bool(top and (top[0]["raw_fourgram_jaccard"] >= 0.32 or top[0]["abstract_sequence_ratio"] >= 0.62))
    record = (item.get("item_spec") or {}).get("originality_record")
    declared_status = record.get("skin_swap_test") if isinstance(record, dict) else None
    return {
        "question_number": item.get("number"),
        "lexical_screen": "review" if lexical_flag else "pass",
        "structural_screen": "pending-evidence-backed-review",
        "author_declared_structural_screen": declared_status,
        "nearest_neighbors": top,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exam_json", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--official-only", action="store_true")
    args = parser.parse_args()

    exam = json.loads(args.exam_json.read_text(encoding="utf-8"))
    subject = str(exam["metadata"]["subject"])
    sources = source_records(subject, include_mocks=not args.official_only)
    items = [audit_item(item, sources) for item in exam["questions"]]
    lexical_reviews = [item["question_number"] for item in items if item["lexical_screen"] != "pass"]
    structural_pending = [item["question_number"] for item in items if str(item["structural_screen"]).startswith("pending")]
    report = {
        "schema_version": 1,
        "exam": str(args.exam_json.resolve()),
        "subject": subject,
        "corpus_scope": "ROC 111-115 official plus supplied same-period mathematics mocks" if not args.official_only else "ROC 111-115 official",
        "source_pdf_count": len({(row["source_kind"], row["relative_path"]) for row in sources}),
        "source_item_count": len(sources),
        "source_wording_exported": False,
        "method_warning": "Lexical triage cannot approve originality. Every item also requires LLM comparison of ordered givens, solution graph, distractor paths, and visual topology.",
        "lexical_review_items": lexical_reviews,
        "structural_review_pending_items": structural_pending,
        "status": "blocked" if lexical_reviews else "structural-review-pending",
        "items": items,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "subject", "source_pdf_count", "source_item_count", "lexical_review_items", "structural_review_pending_items")}, ensure_ascii=False, indent=2))
    return 1 if lexical_reviews else 0


if __name__ == "__main__":
    raise SystemExit(main())
