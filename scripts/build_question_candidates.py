#!/usr/bin/env python3
"""Extract reviewable, copyright-safe item metadata candidates from solution PDFs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from exam_data import validate_record


ROOT = Path(__file__).resolve().parents[1]
ITEM_MARKER = re.compile(r"(?m)^\s*(\d{1,2})\s*[.．、]\s*(?:[（(]([^\n）)]{1,20})[）)])?")
DIFFICULTY_MAP = {"易": 1, "中偏易": 2, "中": 3, "中偏難": 4, "難": 5}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def extract_text_isolated(path: Path, timeout_seconds: int) -> str:
    helper = ROOT / "scripts" / "build_paper_profiles.py"
    completed = subprocess.run(
        [sys.executable, str(helper), "--extract-one", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    if completed.returncode:
        raise RuntimeError((completed.stderr or completed.stdout or "PDF extraction failed")[:300])
    return json.loads(completed.stdout)["text"]


def clean_label(value: str | None, limit: int = 100) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip(" ：:;；")
    return value[:limit] or None


def field_line(block: str, labels: tuple[str, ...], limit: int = 100) -> str | None:
    joined = "|".join(r"\s*".join(re.escape(char) for char in label) for label in labels)
    match = re.search(rf"(?:{joined})\s*[：:]\s*([^\n]{{1,{limit + 40}}})", block)
    return clean_label(match.group(1), limit) if match else None


def difficulty_from_block(block: str) -> tuple[int | None, str | None]:
    match = re.search(r"難\s*易\s*度\s*[：:]\s*(中偏易|中偏難|易|中|難)", block)
    if not match:
        return None, None
    label = match.group(1)
    return DIFFICULTY_MAP[label], label


def curriculum_code(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(
        r"(?:[A-Za-z]{1,4}|歷|地|公)\s*[A-Za-z]{0,4}-[IVXⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+-\d+(?:-\d+)?",
        value,
    )
    return re.sub(r"\s+", "", match.group(0)) if match else None


def domain_for(subject: str, text: str) -> str | None:
    stripped = text.strip()
    if subject == "社會":
        if re.match(r"^公\s*[A-Za-z]", stripped):
            return "公民與社會"
        if re.match(r"^歷\s*[A-Za-z]", stripped):
            return "歷史"
        if re.match(r"^地\s*[A-Za-z]", stripped):
            return "地理"
    mappings = {
        "自然": ("物理", "化學", "生物", "地球科學", "探究與實作"),
        "社會": ("歷史", "地理", "公民與社會", "公民"),
    }
    for domain in mappings.get(subject, ()):
        if domain in text:
            return "公民與社會" if domain == "公民" else domain
    return None


def section_for(profile: dict[str, Any], number: int) -> dict[str, Any] | None:
    for section in profile.get("sections") or []:
        start = section.get("question_number_start")
        end = section.get("question_number_end")
        if isinstance(start, int) and isinstance(end, int) and start <= number <= end:
            return section
    return None


def question_type_for(section: dict[str, Any] | None) -> str:
    if section:
        mix = section.get("question_type_mix") or {}
        if len(mix) == 1:
            return next(iter(mix))
        title = section.get("title", "")
        if "多選" in title:
            return "multiple_choice"
        if "選填" in title:
            return "fill_in"
        if "混合" in title:
            return "mixed_group"
        if "作文" in title or "中譯英" in title or "非選擇" in title:
            return "constructed_response"
    return "single_choice"


def item_blocks(text: str) -> dict[int, str]:
    matches = list(ITEM_MARKER.finditer(text))
    candidates: dict[int, list[str]] = defaultdict(list)
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else min(len(text), match.end() + 1800)
        block = text[match.start() : min(end, match.start() + 2200)]
        if re.search(r"(?:出\s*處|課\s*綱|目\s*標|內\s*容|解\s*析|難\s*易\s*度)\s*[：:]", block):
            candidates[int(match.group(1))].append(block)
    return {
        number: max(blocks, key=lambda value: len(re.findall(r"(?:出\s*處|課\s*綱|目\s*標|內\s*容|解\s*析|難\s*易\s*度)\s*[：:]", value)))
        for number, blocks in candidates.items()
    }


def safe_score(section: dict[str, Any] | None) -> float | None:
    if not section or "混合" in section.get("title", ""):
        return None
    subtotal = section.get("subtotal_score")
    count = section.get("numbered_question_count")
    if isinstance(subtotal, (int, float)) and isinstance(count, int) and count > 0:
        value = subtotal / count
        return value if value > 0 else None
    return None


def recover_promoted_records(blueprint_path: Path, registry: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Recover source-level records from the last internal blueprint snapshot.

    This is a safety net for incremental corpus ingestion: a new extraction pass
    must not erase previously promoted, schema-valid metadata merely because a
    source PDF now needs OCR or a parser became more conservative.
    """
    if not blueprint_path.is_file():
        return {}
    try:
        blueprint = json.loads(blueprint_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    hashes = [str(item.get("sha256")) for item in registry if item.get("sha256")]
    recovered: dict[str, dict[str, Any]] = {}
    for group in blueprint.get("joint_patterns") or []:
        pattern = group.get("pattern") or {}
        if pattern.get("requires_diagram") is True:
            continue
        for question_id in group.get("source_question_ids") or []:
            year_match = re.search(r"^gsat-(\d{4})-", str(question_id))
            hash_match = re.search(r"-([0-9a-f]{10})-q\d+$", str(question_id), re.IGNORECASE)
            if not year_match:
                continue
            prefix = hash_match.group(1).lower() if hash_match else ""
            full_hash = next((value for value in hashes if value.lower().startswith(prefix)), None) if prefix else None
            record = {
                "exam": "學測",
                "year": int(year_match.group(1)),
                "subject": blueprint.get("subject"),
                "curriculum": pattern.get("curriculum"),
                "regime": pattern.get("regime"),
                "question_id": question_id,
                "question_number": pattern.get("question_number"),
                "section": pattern.get("section"),
                "domain": pattern.get("domain"),
                "group_id": None,
                "question_type": pattern.get("question_type"),
                "score": pattern.get("score"),
                "unit": pattern.get("unit"),
                "subunit": pattern.get("subunit"),
                "concepts": pattern.get("concepts") or [],
                "skills": pattern.get("skills") or [],
                "curriculum_codes": [],
                "stimulus_type": pattern.get("stimulus_type"),
                "requires_diagram": pattern.get("requires_diagram"),
                "expected_minutes": pattern.get("expected_minutes"),
                "difficulty": pattern.get("difficulty"),
                "empirical": pattern.get("difficulty_evidence"),
                "common_misconceptions": pattern.get("common_misconceptions") or [],
                "source": {
                    "kind": pattern.get("source_kind") or "mock_exam",
                    "file_sha256": full_hash,
                    "text_public": False,
                    "notes": "Recovered from the prior validated internal blueprint during incremental ingestion.",
                },
            }
            subject = str(blueprint.get("subject") or "")
            if subject and not validate_record(record, "學測", subject):
                recovered[str(question_id)] = record
    return recovered


def build(root: Path, timeout_seconds: int, promote: bool) -> int:
    registry = read_jsonl(root / "exam_packs" / "學測" / "metadata" / "source-registry.jsonl")
    registry_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in registry:
        if item.get("subject") != "shared":
            registry_groups[(item["bundle"], item["subject"], item.get("section") or "")].append(item)

    profiles: dict[tuple[str, str, str], dict[str, Any]] = {}
    subject_root = root / "exam_packs" / "學測" / "subjects"
    for path in subject_root.glob("*/metadata/papers.jsonl"):
        for profile in read_jsonl(path):
            profiles[(profile.get("bundle") or "", profile["subject"], profile.get("section") or "")] = profile

    output_by_subject: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    review_by_subject: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    skipped = Counter()
    for key, profile in profiles.items():
        confidence = (profile.get("evidence") or {}).get("confidence", 0)
        if profile.get("structure_status") != "verified" and confidence < 0.9:
            skipped["paper_profile_not_ready"] += 1
            continue
        sources = [
            item for item in registry_groups.get(key, [])
            if item.get("role") in {"solution", "question_and_solution"}
            and item.get("extension", "").lower() == ".pdf"
            and item.get("text_layer_status") == "extractable"
        ]
        if not sources:
            skipped["no_extractable_solution"] += 1
            continue
        source = sorted(sources, key=lambda item: (item["role"] != "solution", item["destination_relative_path"]))[0]
        try:
            text = extract_text_isolated(root / source["destination_relative_path"], timeout_seconds)
        except (subprocess.TimeoutExpired, RuntimeError, OSError, json.JSONDecodeError):
            skipped["extraction_failed"] += 1
            continue
        blocks = item_blocks(text)
        for number, block in blocks.items():
            total = profile.get("numbered_question_count")
            if not isinstance(total, int) or not 1 <= number <= total:
                continue
            difficulty, difficulty_label = difficulty_from_block(block)
            source_unit = field_line(block, ("出處", "課綱"), 100)
            content = field_line(block, ("內容",), 100)
            objective = field_line(block, ("測驗目標", "目標"), 120)
            section = section_for(profile, number)
            if profile["subject"] == "國文":
                unit = objective or content
            elif profile["subject"] == "英文":
                unit = source_unit or content or (section.get("title") if section else None)
            else:
                unit = source_unit or content
            partial_id = f"gsat-{profile['year']}-{source['series'].lower()}-{source['sha256'][:10]}-q{number:02d}"
            if difficulty is None or not unit:
                review_by_subject[profile["subject"]][partial_id] = {
                    "candidate_id": partial_id,
                    "exam": "學測",
                    "year": profile["year"],
                    "subject": profile["subject"],
                    "curriculum": profile["curriculum"],
                    "paper_id": profile["paper_id"],
                    "question_number": number,
                    "section": section.get("title") if section else profile.get("section"),
                    "explicit_source_unit": source_unit,
                    "explicit_content": content,
                    "explicit_objective": objective,
                    "difficulty_overall": difficulty,
                    "difficulty_label": difficulty_label,
                    "requires_diagram": None,
                    "missing_fields": [
                        field for field, missing in (("unit", not unit), ("difficulty", difficulty is None)) if missing
                    ],
                    "source_file_sha256": source["sha256"],
                    "source_relative_path": source["destination_relative_path"],
                    "review_status": "pending",
                }
                skipped["missing_explicit_unit_or_difficulty"] += 1
                continue
            code = curriculum_code(source_unit)
            qid = f"gsat-{profile['year']}-{source['series'].lower()}-{source['sha256'][:10]}-q{number:02d}"
            record: dict[str, Any] = {
                "exam": "學測",
                "year": profile["year"],
                "subject": profile["subject"],
                "curriculum": profile["curriculum"],
                "regime": profile.get("regime"),
                "question_id": qid,
                "question_number": number,
                "section": section.get("title") if section else profile.get("section"),
                "domain": domain_for(profile["subject"], f"{source_unit or ''} {content or ''}"),
                "group_id": None,
                "question_type": question_type_for(section),
                "score": safe_score(section),
                "unit": unit,
                "subunit": content if content and content != unit else None,
                "concepts": [],
                "skills": [objective] if objective else [],
                "curriculum_codes": [code] if code else [],
                "stimulus_type": None,
                "requires_diagram": None,
                "expected_minutes": None,
                "difficulty": {
                    "overall": difficulty,
                    "basis": "expert_review",
                    "reviewer_confidence": 0.8,
                },
                "empirical": None,
                "common_misconceptions": [],
                "source": {
                    "kind": "mock_exam",
                    "file_sha256": source["sha256"],
                    "text_public": False,
                    "notes": f"Auto-extracted from explicit solution labels ({difficulty_label}); review before promotion.",
                },
            }
            if not validate_record(record, "學測", profile["subject"]):
                output_by_subject[profile["subject"]][qid] = record

    total_candidates = 0
    promoted = 0
    recovered_count = 0
    by_subject_counts: dict[str, int] = {}
    for subject, records in output_by_subject.items():
        target = subject_root / subject / "metadata" / "questions.auto.jsonl"
        final_path = subject_root / subject / "metadata" / "questions.jsonl"
        preserved = {item["question_id"]: item for item in read_jsonl(final_path)}
        snapshot = recover_promoted_records(
            subject_root / subject / "blueprints" / "learned-blueprint.json",
            registry,
        )
        before = len(preserved)
        preserved.update({key: value for key, value in snapshot.items() if key not in preserved})
        recovered_count += len(preserved) - before
        preserved.update(records)
        ordered = sorted(preserved.values(), key=lambda item: (item["year"], item["question_number"], item["question_id"]))
        target.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in ordered), encoding="utf-8")
        by_subject_counts[subject] = len(ordered)
        total_candidates += len(ordered)
        if promote:
            validation_errors = [
                (record["question_id"], validate_record(record, "學測", subject)) for record in ordered
            ]
            validation_errors = [item for item in validation_errors if item[1]]
            if validation_errors:
                raise ValueError(f"{subject} 有 {len(validation_errors)} 筆候選未通過驗證，不執行 promotion")
            final_path.write_text(
                "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in ordered), encoding="utf-8"
            )
            promoted += len(ordered)
    for subject_path in subject_root.iterdir():
        stale = subject_path / "metadata" / "questions.auto.jsonl"
        if subject_path.name not in output_by_subject and stale.exists():
            stale.unlink()
    review_count = 0
    review_counts: dict[str, int] = {}
    for subject, records in review_by_subject.items():
        target = subject_root / subject / "metadata" / "question-review-queue.jsonl"
        ordered = sorted(records.values(), key=lambda item: (item["year"], item["question_number"], item["candidate_id"]))
        target.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in ordered), encoding="utf-8")
        review_counts[subject] = len(ordered)
        review_count += len(ordered)
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": total_candidates,
        "promoted_count": promoted,
        "recovered_from_prior_blueprint_count": recovered_count,
        "review_queue_count": review_count,
        "review_queue_by_subject": dict(sorted(review_counts.items())),
        "by_subject": dict(sorted(by_subject_counts.items())),
        "skipped": dict(skipped),
        "status": (
            "promoted after schema validation; rebuild blueprints"
            if promote
            else "review_required_before copying to questions.jsonl and rebuilding blueprints"
        ),
    }
    report_path = root / "exam_packs" / "學測" / "metadata" / "question-candidate-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已建立 {total_candidates} 筆逐題 metadata 候選；詳見 {report_path.relative_to(root)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="從詳解明示欄位建立逐題 metadata 候選")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--timeout-seconds", type=int, default=10)
    parser.add_argument("--promote", action="store_true", help="將通過驗證的候選寫入正式 questions.jsonl")
    args = parser.parse_args(argv)
    return build(args.root.resolve(), args.timeout_seconds, args.promote)


if __name__ == "__main__":
    raise SystemExit(main())
