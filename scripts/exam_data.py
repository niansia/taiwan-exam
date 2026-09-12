#!/usr/bin/env python3
"""Dependency-free data tools for Taiwan Exam Skill."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORIES = (
    "歷屆試題",
    "模擬考",
    "metadata",
    "blueprints",
    "answer-profiles",
    "format-references",
)
SOURCE_DIRECTORIES = ("歷屆試題", "模擬考")
QUESTION_TYPES = {
    "single_choice",
    "multiple_choice",
    "fill_in",
    "constructed_response",
    "mixed_group",
    "guided_writing",
    "listening_choice",
}
DIFFICULTY_FIELDS = (
    "overall",
    "concept_depth",
    "calculation_depth",
    "reasoning_steps",
    "reading_load",
    "novelty",
    "distractor_strength",
)
VISUAL_KINDS = {
    "coordinate_graph", "geometry_diagram", "statistical_chart", "data_table", "map", "timeline",
    "circuit", "experimental_setup", "biological_illustration", "chemical_structure", "photo",
    "document_facsimile", "other",
}
VISUAL_MODES = {"deterministic_svg", "chart_renderer", "image_model", "licensed_source", "none"}
GUIDANCE = {
    "歷屆試題": (
        "放資料到這裡.md",
        "# 歷屆試題投遞區\n\n放入正式歷屆試題、答案、官方試題說明或答題卷。"
        "建議檔名：`西元年_考試_科目_內容類型_來源.ext`。此資料夾預設不會提交到 Git。\n",
    ),
    "模擬考": (
        "放資料到這裡.md",
        "# 模擬考投遞區\n\n放入模擬考並在檔名或 metadata 記錄來源。"
        "請勿把模擬考當成官方歷屆題合併統計。此資料夾預設不會提交到 Git。\n",
    ),
    "answer-profiles": (
        "放詳解格式到這裡.md",
        "# 詳解格式參考\n\n放入你有權使用的詳解格式範例。標註希望的 profile："
        "official-short、teacher-detailed、student-friendly 或 machine-check。\n",
    ),
    "format-references": (
        "放格式範例到這裡.md",
        "# 排版參考\n\n放入空白答題卷、封面、頁首頁尾或你有權使用的版型參考。"
        "Renderer 應學排版規則，不複製受保護內容。\n",
    ),
}


def json_dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def pack_manifests(root: Path) -> Iterable[tuple[Path, dict[str, Any]]]:
    for path in sorted((root / "exam_packs").glob("*/manifest.json")):
        yield path, load_json(path)


def subject_paths(root: Path) -> Iterable[tuple[str, str, Path]]:
    for manifest_path, manifest in pack_manifests(root):
        exam = manifest["folder"]
        subjects = list(manifest["subjects"]) + list(manifest.get("historical_subjects", []))
        for subject in subjects:
            yield exam, subject, manifest_path.parent / "subjects" / subject


def resolve_subject(root: Path, exam: str, subject: str) -> Path:
    if exam == "學測":
        subject = {"國綜": "國文", "國寫": "國文", "數A": "數學A", "數B": "數學B"}.get(subject, subject)
    for found_exam, found_subject, path in subject_paths(root):
        if found_exam == exam and found_subject == subject:
            return path
    available = ", ".join(f"{e}/{s}" for e, s, _ in subject_paths(root))
    raise ValueError(f"找不到考試／科目 {exam}/{subject}。可用項目：{available}")


def prepare(root: Path) -> int:
    created = 0
    for _, _, subject_path in subject_paths(root):
        for name in DATA_DIRECTORIES:
            directory = subject_path / name
            directory.mkdir(parents=True, exist_ok=True)
            if name in GUIDANCE:
                filename, content = GUIDANCE[name]
                guide = directory / filename
                if not guide.exists():
                    guide.write_text(content, encoding="utf-8")
                    created += 1
    print(f"資料夾已就緒；新增 {created} 個說明檔。")
    return 0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def index_sources(root: Path) -> int:
    prepare(root)
    total = 0
    for exam, subject, subject_path in subject_paths(root):
        records: list[dict[str, Any]] = []
        for source_dir in SOURCE_DIRECTORIES:
            base = subject_path / source_dir
            for path in sorted(p for p in base.rglob("*") if p.is_file()):
                if path.name in {item[0] for item in GUIDANCE.values()}:
                    continue
                stat = path.stat()
                records.append(
                    {
                        "exam": exam,
                        "subject": subject,
                        "source_kind": "official_past_exam" if source_dir == "歷屆試題" else "mock_exam",
                        "relative_path": path.relative_to(root).as_posix(),
                        "sha256": sha256_file(path),
                        "size_bytes": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    }
                )
        target = subject_path / "metadata" / "source-index.jsonl"
        if records:
            target.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
        elif target.exists():
            target.unlink()
        total += len(records)
    print(f"已索引 {total} 個來源檔；原始內容未複製到索引。")
    return 0


def split_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def parse_optional_float(value: str | None) -> float | None:
    return None if value is None or not value.strip() else float(value)


def parse_optional_int(value: str | None) -> int | None:
    return None if value is None or not value.strip() else int(value)


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y", "是"}:
        return True
    if normalized in {"false", "0", "no", "n", "否"}:
        return False
    raise ValueError(f"無法辨識布林值：{value}")


def csv_row_to_record(row: dict[str, str]) -> dict[str, Any]:
    difficulty: dict[str, Any] = {
        "overall": int(row["difficulty_overall"]),
        "basis": row.get("difficulty_basis", "estimated") or "estimated",
    }
    for field in DIFFICULTY_FIELDS[1:]:
        parsed = parse_optional_int(row.get(field))
        if parsed is not None:
            difficulty[field] = parsed
    confidence = parse_optional_float(row.get("reviewer_confidence"))
    if confidence is not None:
        difficulty["reviewer_confidence"] = confidence

    empirical_values = {
        "answer_rate": parse_optional_float(row.get("answer_rate")),
        "discrimination": parse_optional_float(row.get("discrimination")),
        "sample_size": parse_optional_int(row.get("sample_size")),
    }
    empirical = {key: value for key, value in empirical_values.items() if value is not None}

    source: dict[str, Any] = {
        "kind": row.get("source_kind", "official_past_exam") or "official_past_exam",
        "text_public": parse_bool(row.get("source_text_public"), False),
    }
    optional_source = {
        "file_sha256": row.get("source_file_sha256", "").strip() or None,
        "url": row.get("source_url", "").strip() or None,
        "notes": row.get("source_notes", "").strip() or None,
    }
    source.update({key: value for key, value in optional_source.items() if value is not None})

    record: dict[str, Any] = {
        "exam": row["exam"].strip(),
        "year": int(row["year"]),
        "subject": row["subject"].strip(),
        "curriculum": row["curriculum"].strip(),
        "question_id": row["question_id"].strip(),
        "question_number": int(row["question_number"]),
        "question_type": row["question_type"].strip(),
        "unit": row["unit"].strip(),
        "difficulty": difficulty,
        "source": source,
    }
    visual_json = (row.get("visual_json") or "").strip()
    if visual_json:
        visual = json.loads(visual_json)
        if not isinstance(visual, dict):
            raise ValueError("visual_json 必須是 JSON object")
        record["visual"] = visual
    optional_scalars: dict[str, Any] = {
        "regime": row.get("regime", "").strip() or None,
        "section": row.get("section", "").strip() or None,
        "domain": row.get("domain", "").strip() or None,
        "group_id": row.get("group_id", "").strip() or None,
        "score": parse_optional_float(row.get("score")),
        "subunit": row.get("subunit", "").strip() or None,
        "stimulus_type": row.get("stimulus_type", "").strip() or None,
        "requires_diagram": parse_bool(row.get("requires_diagram"), False),
        "expected_minutes": parse_optional_float(row.get("expected_minutes")),
    }
    record.update({key: value for key, value in optional_scalars.items() if value is not None})
    for key in ("concepts", "skills", "curriculum_codes", "common_misconceptions"):
        values = split_list(row.get(key))
        if values:
            record[key] = values
    if empirical:
        record["empirical"] = empirical
    return record


def validate_record(record: Any, expected_exam: str | None = None, expected_subject: str | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record 必須是 JSON object"]
    required = (
        "exam",
        "year",
        "subject",
        "curriculum",
        "question_id",
        "question_number",
        "question_type",
        "unit",
        "difficulty",
        "source",
    )
    for key in required:
        if key not in record:
            errors.append(f"缺少欄位 {key}")
    if errors:
        return errors
    if expected_exam and record["exam"] != expected_exam:
        errors.append(f"exam 應為 {expected_exam}，實際為 {record['exam']}")
    if expected_subject and record["subject"] != expected_subject:
        errors.append(f"subject 應為 {expected_subject}，實際為 {record['subject']}")
    if not isinstance(record["year"], int) or not 1900 <= record["year"] <= 2200:
        errors.append("year 必須是 1900-2200 的西元年整數")
    question_number = record["question_number"]
    if question_number is None:
        scored_slot_id = record.get("scored_slot_id")
        if not isinstance(scored_slot_id, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]+", scored_slot_id):
            errors.append("未編號計分單元必須提供 ASCII scored_slot_id")
    elif not isinstance(question_number, int) or question_number < 1:
        errors.append("question_number 必須是正整數或未編號計分單元的 null")
    if not isinstance(record["question_id"], str) or not re.fullmatch(r"[A-Za-z0-9_.:-]+", record["question_id"]):
        errors.append("question_id 僅可使用 ASCII 字母、數字、底線、句點、冒號與連字號")
    if record["question_type"] not in QUESTION_TYPES:
        errors.append(f"未知 question_type：{record['question_type']}")
    difficulty = record.get("difficulty")
    if not isinstance(difficulty, dict) or "overall" not in difficulty:
        errors.append("difficulty.overall 為必填")
    else:
        for key in DIFFICULTY_FIELDS:
            value = difficulty.get(key)
            if value is not None and (not isinstance(value, int) or not 1 <= value <= 5):
                errors.append(f"difficulty.{key} 必須是 1-5 的整數")
        if difficulty.get("basis") not in {None, "empirical", "expert_review", "estimated"}:
            errors.append("difficulty.basis 必須是 empirical、expert_review 或 estimated")
        confidence = difficulty.get("reviewer_confidence")
        if confidence is not None and (not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1):
            errors.append("reviewer_confidence 必須介於 0-1")
    source = record.get("source")
    if not isinstance(source, dict) or source.get("kind") not in {"official_past_exam", "mock_exam", "synthetic", "other"}:
        errors.append("source.kind 無效")
    elif not isinstance(source.get("text_public"), bool):
        errors.append("source.text_public 必須是布林值")
    empirical = record.get("empirical")
    if empirical:
        answer_rate = empirical.get("answer_rate")
        if answer_rate is not None and not 0 <= answer_rate <= 1:
            errors.append("empirical.answer_rate 必須介於 0-1")
        p_value = empirical.get("p_value")
        if p_value is not None and not 0 <= p_value <= 1:
            errors.append("empirical.p_value 必須介於 0-1")
        if empirical.get("p_metric") not in {None, "answer_rate", "score_rate"}:
            errors.append("empirical.p_metric 必須是 answer_rate 或 score_rate")
        percentile = empirical.get("relative_difficulty_percentile")
        if percentile is not None and not 0 <= percentile <= 1:
            errors.append("empirical.relative_difficulty_percentile 必須介於 0-1")
    requires_diagram = record.get("requires_diagram", False)
    visual = record.get("visual")
    if requires_diagram and not isinstance(visual, dict):
        errors.append("requires_diagram 為 true 時必須提供 visual spec")
    if visual is not None:
        if not isinstance(visual, dict):
            errors.append("visual 必須是 object")
        else:
            if visual.get("kind") not in VISUAL_KINDS:
                errors.append("visual.kind 無效")
            if visual.get("generation_mode") not in VISUAL_MODES:
                errors.append("visual.generation_mode 無效")
            for key in ("information_density",):
                value = visual.get(key)
                if not isinstance(value, int) or not 1 <= value <= 5:
                    errors.append(f"visual.{key} 必須是 1-5 的整數")
            steps = visual.get("visual_reasoning_steps")
            if not isinstance(steps, int) or not 0 <= steps <= 5:
                errors.append("visual.visual_reasoning_steps 必須是 0-5 的整數")
            if not isinstance(visual.get("alt_text"), str) or not visual.get("alt_text", "").strip():
                errors.append("visual.alt_text 不可為空")
            checks = visual.get("validation_checks")
            if not isinstance(checks, list) or not checks:
                errors.append("visual.validation_checks 至少需要一項")
    forbidden = {"question_text", "prompt", "passage", "full_answer"}.intersection(record)
    if forbidden:
        errors.append(f"metadata 不應含原題全文欄位：{', '.join(sorted(forbidden))}")
    return errors


def validate_paper_profile(record: Any, expected_exam: str | None = None, expected_subject: str | None = None) -> list[str]:
    if not isinstance(record, dict):
        return ["Paper Profile 必須是 JSON object"]
    errors: list[str] = []
    required = (
        "paper_id", "exam", "year", "subject", "curriculum", "source_kind", "source_files",
        "structure_status", "sections", "evidence",
    )
    for key in required:
        if key not in record:
            errors.append(f"Paper Profile 缺少欄位 {key}")
    if errors:
        return errors
    if expected_exam and record["exam"] != expected_exam:
        errors.append(f"Paper Profile exam 應為 {expected_exam}")
    if expected_subject and record["subject"] != expected_subject:
        errors.append(f"Paper Profile subject 應為 {expected_subject}")
    if not isinstance(record["paper_id"], str) or not re.fullmatch(r"[A-Za-z0-9_.:-]+", record["paper_id"]):
        errors.append("paper_id 格式無效")
    if record["structure_status"] not in {"verified", "auto_parsed", "needs_review", "pending_ocr"}:
        errors.append("structure_status 無效")
    if not isinstance(record["source_files"], list) or not record["source_files"]:
        errors.append("source_files 至少需要一筆")
    else:
        for source in record["source_files"]:
            if not isinstance(source, dict) or not re.fullmatch(r"[a-f0-9]{64}", str(source.get("sha256", ""))):
                errors.append("source_files.sha256 必須是 64 位小寫雜湊")
                break
    sections = record.get("sections")
    if not isinstance(sections, list):
        errors.append("sections 必須是 array")
        sections = []
    orders = [item.get("order") for item in sections if isinstance(item, dict)]
    if len(orders) != len(set(orders)):
        errors.append("sections.order 不可重複")
    total = record.get("numbered_question_count")
    confidence = (record.get("evidence") or {}).get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("evidence.confidence 必須介於 0-1")
    if total is not None and (not isinstance(total, int) or total < 1):
        errors.append("numbered_question_count 必須是正整數或 null")
    known_section_counts = [item.get("numbered_question_count") for item in sections if isinstance(item, dict)]
    enforce_reconciliation = record.get("structure_status") == "verified" or (
        isinstance(confidence, (int, float)) and confidence >= 0.9
    )
    if enforce_reconciliation and total and sections and all(isinstance(value, int) for value in known_section_counts):
        if sum(known_section_counts) != total:
            errors.append("各大題 numbered_question_count 加總不等於整卷題數")
    if record.get('structure_status') == 'verified':
        from pack_verification import paper_errors
        errors.extend(paper_errors(record))
    return errors


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.exists():
        return records, errors
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{number}: JSON 錯誤：{exc.msg}")
            continue
        records.append(value)
    return records, errors


def import_csv(root: Path, exam: str, subject: str, input_path: Path, replace: bool) -> int:
    subject_path = resolve_subject(root, exam, subject)
    prepare(root)
    target = subject_path / "metadata" / "questions.jsonl"
    existing, read_errors = read_jsonl(target)
    if read_errors:
        print("\n".join(read_errors), file=sys.stderr)
        return 2
    existing_by_id = {record.get("question_id"): record for record in existing}
    imported: list[dict[str, Any]] = []
    errors: list[str] = []
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, 2):
            try:
                record = csv_row_to_record(row)
                row_errors = validate_record(record, exam, subject)
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"CSV 第 {row_number} 列：{exc}")
                continue
            if row_errors:
                errors.extend(f"CSV 第 {row_number} 列：{message}" for message in row_errors)
                continue
            qid = record["question_id"]
            if qid in existing_by_id and not replace:
                errors.append(f"CSV 第 {row_number} 列：question_id {qid} 已存在；需要覆寫時加 --replace")
                continue
            imported.append(record)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2
    for record in imported:
        existing_by_id[record["question_id"]] = record
    ordered = sorted(existing_by_id.values(), key=record_order_key)
    target.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in ordered), encoding="utf-8")
    print(f"已匯入 {len(imported)} 筆；{target.relative_to(root).as_posix()} 現有 {len(ordered)} 筆。")
    return 0


def validate_repository(root: Path, quiet: bool = False) -> tuple[int, dict[tuple[str, str], int]]:
    errors: list[str] = []
    counts: dict[tuple[str, str], int] = {}
    ids: dict[str, Path] = {}
    for manifest_path, manifest in pack_manifests(root):
        for key in ("id", "name", "folder", "pack_version", "schema_version", "subjects"):
            if key not in manifest:
                errors.append(f"{manifest_path}: manifest 缺少 {key}")
        if manifest.get("folder") != manifest_path.parent.name:
            errors.append(f"{manifest_path}: folder 必須與資料夾名稱一致")
    for exam, subject, subject_path in subject_paths(root):
        if not (subject_path / "subject.json").exists():
            errors.append(f"{subject_path}: 缺少 subject.json")
        path = subject_path / "metadata" / "questions.jsonl"
        records, read_errors = read_jsonl(path)
        errors.extend(read_errors)
        valid_count = 0
        for index, record in enumerate(records, 1):
            item_errors = validate_record(record, exam, subject)
            if item_errors:
                errors.extend(f"{path}:{index}: {message}" for message in item_errors)
                continue
            qid = record["question_id"]
            if qid in ids:
                errors.append(f"{path}:{index}: question_id {qid} 與 {ids[qid]} 重複")
                continue
            ids[qid] = path
            valid_count += 1
        counts[(exam, subject)] = valid_count
        paper_path = subject_path / "metadata" / "papers.jsonl"
        papers, paper_read_errors = read_jsonl(paper_path)
        errors.extend(paper_read_errors)
        paper_ids: set[str] = set()
        for index, paper in enumerate(papers, 1):
            paper_errors = validate_paper_profile(paper, exam, subject)
            errors.extend(f"{paper_path}:{index}: {message}" for message in paper_errors)
            paper_id = paper.get("paper_id") if isinstance(paper, dict) else None
            if paper_id in paper_ids:
                errors.append(f"{paper_path}:{index}: paper_id {paper_id} 重複")
            if paper_id:
                paper_ids.add(paper_id)
    if not quiet:
        if errors:
            print("驗證失敗：", file=sys.stderr)
            print("\n".join(f"- {message}" for message in errors), file=sys.stderr)
        else:
            print(f"驗證通過；共 {sum(counts.values())} 筆逐題 metadata。")
    return (0 if not errors else 2), counts


def difficulty_band(overall: int) -> str:
    if overall <= 2:
        return "easy"
    if overall == 3:
        return "medium"
    if overall == 4:
        return "medium_hard"
    return "hard"


def distribution(values: Iterable[Any]) -> dict[str, dict[str, float | int]]:
    counter = Counter("(unknown)" if value is None or value == "" else str(value) for value in values)
    total = sum(counter.values())
    return {
        key: {"count": count, "proportion": round(count / total, 6)}
        for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    }


def canonical_records_fingerprint(records: list[dict[str, Any]]) -> str:
    canonical = "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for item in records)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def record_order_key(record: dict[str, Any]) -> tuple[Any, ...]:
    """Sort numbered items first, then stable unnumbered scoring slots."""
    number = record.get("question_number")
    return (
        record["year"],
        0 if isinstance(number, int) else 1,
        number if isinstance(number, int) else 0,
        str(record.get("scored_slot_id") or ""),
        record["question_id"],
    )


def pattern_for(record: dict[str, Any]) -> dict[str, Any]:
    pattern = {
        "curriculum": record["curriculum"],
        "regime": record.get("regime"),
        "question_number": record["question_number"],
        "section": record.get("section"),
        "domain": record.get("domain"),
        "question_type": record["question_type"],
        "score": record.get("score"),
        "unit": record["unit"],
        "subunit": record.get("subunit"),
        "concepts": record.get("concepts", []),
        "skills": record.get("skills", []),
        "stimulus_type": record.get("stimulus_type"),
        "requires_diagram": record.get("requires_diagram"),
        "expected_minutes": record.get("expected_minutes"),
        "difficulty": record["difficulty"],
        "difficulty_evidence": record.get("empirical"),
        "source_kind": (record.get("source") or {}).get("kind"),
        "common_misconceptions": record.get("common_misconceptions", []),
    }
    visual = record.get("visual")
    if isinstance(visual, dict):
        pattern["visual"] = {
            key: visual.get(key)
            for key in (
                "kind", "subtype", "layout", "role", "generation_mode", "information_density", "visual_reasoning_steps",
                "entity_count", "panel_count", "label_count", "data_series_count", "distractor_salience", "precision",
                "scale_required", "color_dependency", "difficulty_basis",
            )
        }
    return pattern


def writer_pattern_for(record: dict[str, Any]) -> dict[str, Any]:
    """Return a coarse multi-item pattern that cannot identify one source question."""
    difficulty = record.get("difficulty") or {}
    return {
        "curriculum": record.get("curriculum"),
        "regime": record.get("regime"),
        "section": record.get("section"),
        "domain": record.get("domain"),
        "question_type": record.get("question_type"),
        "score": record.get("score"),
        "unit": record.get("unit"),
        "subunit": record.get("subunit"),
        "stimulus_type": record.get("stimulus_type"),
        "requires_diagram": record.get("requires_diagram"),
        "difficulty_band": difficulty_band(int(difficulty.get("overall") or 3)),
    }


def build_blueprints(root: Path, exam_filter: str | None = None, subject_filter: str | None = None) -> int:
    code, _ = validate_repository(root, quiet=True)
    if code:
        validate_repository(root)
        return code
    built = 0
    for exam, subject, subject_path in subject_paths(root):
        if exam_filter and exam != exam_filter:
            continue
        if subject_filter and subject != subject_filter:
            continue
        records, _ = read_jsonl(subject_path / "metadata" / "questions.jsonl")
        if not records:
            continue
        records = sorted(records, key=record_order_key)
        years = Counter(record["year"] for record in records)
        curricula = sorted({record["curriculum"] for record in records})
        pattern_groups: dict[str, dict[str, Any]] = {}
        for record in records:
            pattern = pattern_for(record)
            key = json.dumps(pattern, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if key not in pattern_groups:
                pattern_groups[key] = {"pattern": pattern, "count": 0, "source_question_ids": []}
            pattern_groups[key]["count"] += 1
            pattern_groups[key]["source_question_ids"].append(record["question_id"])
        joint_patterns = []
        for group in pattern_groups.values():
            joint_patterns.append(
                {
                    **group,
                    "proportion": round(group["count"] / len(records), 6),
                }
            )
        joint_patterns.sort(key=lambda item: (-item["count"], json.dumps(item["pattern"], ensure_ascii=False, sort_keys=True)))
        writer_groups: dict[str, dict[str, Any]] = {}
        for record in records:
            pattern = writer_pattern_for(record)
            key = json.dumps(pattern, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if key not in writer_groups:
                writer_groups[key] = {"pattern": pattern, "count": 0, "years": set(), "difficulty_values": []}
            writer_groups[key]["count"] += 1
            writer_groups[key]["years"].add(int(record["year"]))
            writer_groups[key]["difficulty_values"].append(int((record.get("difficulty") or {}).get("overall") or 3))
        aggregate_pattern_clusters = []
        for key, group in writer_groups.items():
            pattern = dict(group["pattern"])
            difficulty_values = sorted(group["difficulty_values"])
            pattern["difficulty"] = {
                "overall": difficulty_values[len(difficulty_values) // 2],
                "basis": "multi-item-aggregate",
            }
            pattern.pop("difficulty_band", None)
            cluster_id = "aggregate-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
            aggregate_pattern_clusters.append(
                {
                    "cluster_id": cluster_id,
                    "pattern": pattern,
                    "count": group["count"],
                    "supporting_year_count": len(group["years"]),
                    "year_range": [min(group["years"]), max(group["years"])],
                    "proportion": round(group["count"] / len(records), 6),
                }
            )
        aggregate_pattern_clusters.sort(key=lambda item: (-item["count"], item["cluster_id"]))
        distinct_years = len(years)
        minimum_records = 8 if subject == "寫作測驗" else 30
        calibration_by_curriculum = {}
        difficulty_profile_path = subject_path / "blueprints" / "difficulty-profile.json"
        difficulty_profile = load_json(difficulty_profile_path) if difficulty_profile_path.exists() else {}
        layout_profile_paths = sorted((subject_path / "blueprints" / "layout-profiles").glob("*.json"))
        layout_profiles = [load_json(path) for path in layout_profile_paths]
        verified_layout_profiles = [
            profile
            for profile in layout_profiles
            if profile.get("fidelity_status") == "verified"
            and (profile.get("instructions") or {}).get("transcription_status") == "verified"
        ]
        paper_profiles, _ = read_jsonl(subject_path / "metadata" / "papers.jsonl")
        for curriculum in curricula:
            curriculum_records = [record for record in records if record["curriculum"] == curriculum]
            curriculum_year_count = len({record["year"] for record in curriculum_records})
            official_records = [
                record for record in curriculum_records if (record.get("source") or {}).get("kind") == "official_past_exam"
            ]
            mock_records = [
                record for record in curriculum_records if (record.get("source") or {}).get("kind") == "mock_exam"
            ]
            official_year_count = len({record["year"] for record in official_records})
            vector_fields = DIFFICULTY_FIELDS[1:]
            vector_complete = sum(
                all((record.get("difficulty") or {}).get(field) is not None for field in vector_fields)
                for record in curriculum_records
            )
            literacy_complete = sum(isinstance(record.get("literacy"), dict) for record in curriculum_records)
            competence_records = [
                record
                for record in curriculum_records
                if (record.get("literacy") or {}).get("classification") == "competence_oriented"
            ]
            provenance_complete = sum(
                isinstance(record.get("stimulus_provenance"), dict) for record in competence_records
            )
            official_current_profiles = [
                profile
                for profile in paper_profiles
                if profile.get("source_kind") == "official_past_exam"
                and profile.get("curriculum") == curriculum
            ]
            constructed_required = any(
                any(
                    question_type in {"constructed_response", "guided_writing", "mixed_group"}
                    for question_type in (section.get("question_type_mix") or {})
                )
                or "非選擇" in str(section.get("title") or "")
                for profile in official_current_profiles
                for section in (profile.get("sections") or [])
            )
            constructed_records = [
                record
                for record in official_records
                if record.get("question_type") in {"constructed_response", "guided_writing", "mixed_group"}
            ]
            constructed_complete = sum(
                isinstance(record.get("constructed_response_calibration"), dict)
                for record in constructed_records
            )
            official_difficulty = (difficulty_profile.get("curricula") or {}).get(curriculum, {})
            dimensions = {
                "semantic_sample": {
                    "status": "ready" if curriculum_year_count >= 5 and len(curriculum_records) >= minimum_records else "insufficient-data",
                    "record_count": len(curriculum_records),
                    "year_count": curriculum_year_count,
                },
                "official_semantic_anchor": {
                    "status": "ready" if exam != "學測" or official_year_count >= 3 else "insufficient-data",
                    "record_count": len(official_records),
                    "year_count": official_year_count,
                },
                "official_objective_difficulty": {
                    "status": official_difficulty.get("status", "insufficient-data") if exam == "學測" else "not-required",
                    "measured_item_count": official_difficulty.get("measured_item_count", 0),
                    "year_count": official_difficulty.get("year_count", 0),
                    "source_fingerprint": difficulty_profile.get("source_fingerprint"),
                },
                "difficulty_vector": {
                    "status": "ready" if vector_complete >= max(minimum_records, int(len(curriculum_records) * 0.8)) else "insufficient-data",
                    "complete_count": vector_complete,
                    "coverage": round(vector_complete / len(curriculum_records), 6) if curriculum_records else 0,
                },
                "literacy_annotation": {
                    "status": "ready" if literacy_complete >= int(len(curriculum_records) * 0.9) else "insufficient-data",
                    "complete_count": literacy_complete,
                    "coverage": round(literacy_complete / len(curriculum_records), 6) if curriculum_records else 0,
                },
                "stimulus_provenance": {
                    "status": (
                        "ready"
                        if (
                            competence_records
                            and provenance_complete >= max(1, int(len(competence_records) * 0.9))
                        )
                        or (literacy_complete == len(curriculum_records) and not competence_records)
                        else "insufficient-data"
                    ),
                    "competence_item_count": len(competence_records),
                    "complete_count": provenance_complete,
                    "coverage": round(provenance_complete / len(competence_records), 6) if competence_records else 0,
                },
                "constructed_response_calibration": {
                    "status": (
                        "not-required"
                        if exam != "學測" or not constructed_required
                        else (
                            "ready"
                            if len({record["year"] for record in constructed_records}) >= 3
                            and constructed_complete >= max(1, int(len(constructed_records) * 0.8))
                            else "insufficient-data"
                        )
                    ),
                    "required_by_official_structure": constructed_required,
                    "official_record_count": len(constructed_records),
                    "complete_count": constructed_complete,
                    "year_count": len({record["year"] for record in constructed_records}),
                },
                "formal_layout": {
                    "status": "ready" if exam != "學測" or verified_layout_profiles else "insufficient-data",
                    "verified_profile_count": len(verified_layout_profiles),
                    "profile_ids": [profile.get("profile_id") for profile in verified_layout_profiles],
                },
            }
            required_dimensions = [
                dimensions["semantic_sample"]["status"],
                dimensions["official_semantic_anchor"]["status"],
                dimensions["difficulty_vector"]["status"],
                dimensions["literacy_annotation"]["status"],
                dimensions["stimulus_provenance"]["status"],
            ]
            if exam == "學測":
                required_dimensions.extend(
                    [
                        dimensions["official_objective_difficulty"]["status"],
                        dimensions["constructed_response_calibration"]["status"],
                        dimensions["formal_layout"]["status"],
                    ]
                )
            curriculum_ready = all(status == "ready" for status in required_dimensions)
            calibration_by_curriculum[curriculum] = {
                "record_count": len(curriculum_records),
                "year_count": curriculum_year_count,
                "official_record_count": len(official_records),
                "official_year_count": official_year_count,
                "mock_record_count": len(mock_records),
                "dimensions": dimensions,
                "status": "ready" if curriculum_ready else "insufficient-data",
            }
        ready = len(curricula) == 1 and calibration_by_curriculum[curricula[0]]["status"] == "ready"
        notes = []
        if len(curricula) > 1:
            notes.append("資料含多個課綱版本；生成時必須指定 curriculum，禁止混合抽樣。")
        if any(item["year_count"] < 5 for item in calibration_by_curriculum.values()):
            notes.append("至少一個課綱版本少於 5 個年度，尚不足以聲稱長期歷史校準。")
        if any(item["record_count"] < minimum_records for item in calibration_by_curriculum.values()):
            notes.append(f"至少一個課綱版本少於 {minimum_records} 題，分布估計不穩定。")
        if exam == "學測" and any(item["official_year_count"] < 3 for item in calibration_by_curriculum.values()):
            notes.append("至少一個課綱版本少於 3 個年度的官方逐題語意標註；模考資料不可代替正式題型錨點。")
        if any(item["dimensions"]["difficulty_vector"]["status"] != "ready" for item in calibration_by_curriculum.values()):
            notes.append("逐題多維難度向量覆蓋不足；不可只用出版社的單一易中難標籤宣稱校準。")
        if any(item["dimensions"]["literacy_annotation"]["status"] != "ready" for item in calibration_by_curriculum.values()):
            notes.append("素養題分類與素材功能標註不足；完整模擬卷必須停在資料補標階段。")
        if exam == "學測" and any(
            item["dimensions"]["stimulus_provenance"]["status"] != "ready"
            for item in calibration_by_curriculum.values()
        ):
            notes.append("尚未形成可驗證的素養素材來源與發布日至考試日時間差分布；不得宣稱已學會時事取材節奏。")
        if exam == "學測" and any(
            item["dimensions"]["constructed_response_calibration"]["status"] != "ready"
            for item in calibration_by_curriculum.values()
        ):
            notes.append("非選擇題／國寫尚缺官方評分規準與作答分布的結構化校準。")
        if exam == "學測" and any(
            item["dimensions"]["formal_layout"]["status"] != "ready"
            for item in calibration_by_curriculum.values()
        ):
            notes.append("尚無逐字作答說明與視覺比對均通過的正式 Layout Profile；不得輸出仿正式整卷。")
        blueprint = {
            "schema_version": 1,
            "exam": exam,
            "subject": subject,
            "curricula": curricula,
            "record_count": len(records),
            "years": {
                "minimum": min(years),
                "maximum": max(years),
                "counts": {str(year): count for year, count in sorted(years.items())},
            },
            "metadata_fingerprint": canonical_records_fingerprint(records),
            "built_at": datetime.now(timezone.utc).isoformat(),
            "calibration_status": "ready" if ready else "insufficient-data",
            "calibration_by_curriculum": calibration_by_curriculum,
            "calibration_notes": notes,
            "distributions": {
                "unit": distribution(record["unit"] for record in records),
                "subunit": distribution(record.get("subunit") for record in records),
                "question_type": distribution(record["question_type"] for record in records),
                "section": distribution(record.get("section") for record in records),
                "domain": distribution(record.get("domain") for record in records),
                "score": distribution(record.get("score") for record in records),
                "difficulty_band": distribution(difficulty_band(record["difficulty"]["overall"]) for record in records),
                "difficulty_basis": distribution((record.get("difficulty") or {}).get("basis") for record in records),
                "source_kind": distribution((record.get("source") or {}).get("kind") for record in records),
            },
            "joint_patterns": joint_patterns,
        }
        target = subject_path / "blueprints" / "learned-blueprint.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json_dump(blueprint), encoding="utf-8")
        writer_blueprint = {
            "schema_version": 1,
            "exam": exam,
            "subject": subject,
            "curricula": curricula,
            "record_count": len(records),
            "years": blueprint["years"],
            "metadata_fingerprint": blueprint["metadata_fingerprint"],
            "built_at": blueprint["built_at"],
            "calibration_status": blueprint["calibration_status"],
            "calibration_by_curriculum": blueprint["calibration_by_curriculum"],
            "calibration_notes": blueprint["calibration_notes"],
            "source_visibility": "aggregate-only",
            "individual_source_question_ids_included": False,
            "individual_question_numbers_included": False,
            "distribution_policy": "multi-year probability envelope; never copy one historical paper's unit sequence",
            "distributions": blueprint["distributions"],
            "aggregate_pattern_clusters": aggregate_pattern_clusters,
        }
        writer_target = subject_path / "blueprints" / "writer-blueprint.json"
        writer_target.write_text(json_dump(writer_blueprint), encoding="utf-8")
        print(f"已建立 {exam}/{subject} Blueprint：{len(records)} 題、{distinct_years} 年。")
        built += 1
    print(f"共建立 {built} 個 learned blueprint。")
    return 0


def status(root: Path) -> int:
    code, counts = validate_repository(root, quiet=True)
    rows = []
    for exam, subject, subject_path in subject_paths(root):
        blueprint_path = subject_path / "blueprints" / "writer-blueprint.json"
        difficulty_path = subject_path / "blueprints" / "difficulty-profile.json"
        official_pd_count = 0
        if difficulty_path.exists():
            official_pd_count = int(load_json(difficulty_path).get("official_item_statistics_count", 0))
        status_value = "尚無資料"
        years = "-"
        if blueprint_path.exists():
            blueprint = load_json(blueprint_path)
            status_value = blueprint.get("calibration_status", "unknown")
            span = blueprint.get('years') or {}
            years = f"{span.get('minimum', '?')}-{span.get('maximum', '?')}"
        elif counts.get((exam, subject), 0):
            status_value = "待建 Blueprint"
        elif official_pd_count:
            status_value = "僅官方難度；缺語意標註"
        rows.append((exam, subject, counts.get((exam, subject), 0), official_pd_count, years, status_value))
    header = ["考試", "科目", "本機逐題資料", "官方P/D", "彙整年度", "Writer 校準狀態"]
    widths = [max(len(str(row[index])) for row in (header, *rows)) for index in range(len(header))]
    print("  ".join(str(value).ljust(widths[index]) for index, value in enumerate(header)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))
    print("彙整 Blueprint 可隨發行版提供；本機逐題資料為 0 不代表沒有校準。完整前置檢查：python scripts/audit_exam_pack.py --readiness")
    return code


def select_paper_profile(
    subject_path: Path,
    curriculum: str | None,
    paper_id: str | None,
    paper_year: int | None,
    section: str | None = None,
) -> dict[str, Any]:
    profiles, errors = read_jsonl(subject_path / "metadata" / "papers.jsonl")
    if errors:
        raise ValueError("Paper Profile 檔案格式錯誤：" + "；".join(errors))
    if paper_id:
        profiles = [profile for profile in profiles if profile.get("paper_id") == paper_id]
    if paper_year:
        profiles = [profile for profile in profiles if profile.get("year") == paper_year]
    if curriculum:
        profiles = [profile for profile in profiles if profile.get("curriculum") == curriculum]
    if section:
        profiles = [profile for profile in profiles if profile.get('section') == section]

    def ready(profile: dict[str, Any]) -> bool:
        from pack_verification import paper_errors
        if paper_errors(profile, subject_path.parents[3]):
            return False
        evidence = profile.get("evidence") or {}
        status_value = profile.get("structure_status")
        if profile.get("exam") == "學測":
            trusted = status_value == "verified" and profile.get("source_kind") == "official_past_exam"
        else:
            trusted = status_value == "verified" or (
                status_value == "auto_parsed" and evidence.get("confidence", 0) >= 0.9
            )
        sections = profile.get("sections") or []
        total = profile.get("numbered_question_count")
        counts = [section.get("numbered_question_count") for section in sections]
        numbered_sections_valid = all(
            isinstance(value, int)
            or (
                value is None
                and section.get("question_number_start") is None
                and section.get("question_number_end") is None
            )
            for section, value in zip(sections, counts)
        )
        reconciled = bool(
            total
            and counts
            and numbered_sections_valid
            and sum(value for value in counts if isinstance(value, int)) == total
        )
        scores = [section.get("subtotal_score") for section in sections]
        score_reconciled = bool(
            profile.get("total_score") is not None
            and scores
            and all(isinstance(value, (int, float)) for value in scores)
            and abs(sum(scores) - profile["total_score"]) < 1e-6
        )
        return trusted and reconciled and score_reconciled and profile.get("duration_minutes") is not None

    ready_profiles = [profile for profile in profiles if ready(profile)]
    if not ready_profiles:
        target = paper_id or (f"{paper_year} 年" if paper_year else "相容")
        raise ValueError(f"找不到可通過全卷結構門檻的 {target} Paper Profile；請先複核題數、大題配方、配分與時間。")
    if len({p.get('section') for p in ready_profiles if p.get('section') in {'國綜', '國寫'}}) > 1:
        raise ValueError("國文包含兩份不同試卷；請以 --subject 國綜 或 --subject 國寫 指定，或提供 --paper-id。")
    return sorted(
        ready_profiles,
        key=lambda profile: (
            profile.get("year", 0),
            1 if profile.get("source_kind") == "official_past_exam" else 0,
            (profile.get("evidence") or {}).get("confidence", 0),
        ),
        reverse=True,
    )[0]


def select_layout_profile(
    subject_path: Path,
    curriculum: str | None,
    paper_profile: dict[str, Any],
) -> dict[str, Any]:
    paths = sorted((subject_path / "blueprints" / "layout-profiles").glob("*.json"))
    profiles = [load_json(path) for path in paths]
    from pack_verification import layout_errors
    candidates = [
        profile
        for profile in profiles
        if profile.get("fidelity_status") == "verified"
        and not layout_errors(profile, subject_path.parents[3], paper_profile)
        and (profile.get("instructions") or {}).get("transcription_status") == "verified"
        and (not curriculum or not profile.get("curriculum") or profile.get("curriculum") == curriculum)
        and (
            not paper_profile.get("section")
            or not profile.get("section")
            or profile.get("section") == paper_profile.get("section")
        )
    ]
    if not candidates:
        raise ValueError("找不到作答說明與視覺比對均通過的 Layout Profile；不可用通用版型冒充正式學測。")
    return sorted(candidates, key=lambda profile: profile.get("reference_year", 0), reverse=True)[0]


def normalized_section_label(value: str | None) -> str:
    """Reduce cosmetic numbering/score differences before matching section names."""
    if not value:
        return ""
    label = value.strip().lower()
    label = re.sub(r"[（(][^）)]*(?:分|題)[^）)]*[）)]", "", label)
    label = re.sub(r"^第[一二三四五六七八九十百壹貳參肆伍陸柒捌玖拾0-9]+部分[、，,:：.．\s]*", "", label)
    label = re.sub(r"^[一二三四五六七八九十百壹貳參肆伍陸柒捌玖拾0-9]+[、，,:：.．\s]+", "", label)
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", label)


def section_labels_match(source: str | None, target: str | None) -> bool:
    source_key = normalized_section_label(source)
    target_key = normalized_section_label(target)
    if not source_key or not target_key:
        return False
    return source_key == target_key or source_key in target_key or target_key in source_key


def matching_slot_patterns(patterns, paper, slot):
    section_id = slot['section_id']
    title = next((s['title'] for s in paper['sections'] if s['id'] == section_id), None)
    if paper.get('section') in {'國綜', '國寫'}:
        section_id = paper['section'] + '-' + section_id
    def response_type(pattern):
        # Historical annotation used task labels for these two English
        # sections. Normalize only known equivalents, never across sections.
        if paper.get('subject') == '英文':
            if slot['section_id'] == 'section-3' and pattern.get('unit') == '文意選填' and pattern.get('question_type') == 'fill_in':
                return 'single_choice'
            if slot['section_id'] == 'section-8' and pattern.get('unit') == '英文作文' and pattern.get('question_type') == 'guided_writing':
                return 'constructed_response'
        return pattern.get('question_type')
    def section_match(source):
        if source and re.fullmatch(r'(?:國綜-|國寫-)?section-\d+', source):
            return source == section_id
        return section_labels_match(source, title)
    return [item for item in patterns if response_type(item['pattern']) == slot['type']
            and section_match(item['pattern'].get('section'))]


def overall_from_target_p(p_value: float) -> int:
    if p_value >= 0.80:
        return 1
    if p_value >= 0.65:
        return 2
    if p_value >= 0.40:
        return 3
    if p_value >= 0.20:
        return 4
    return 5


def official_difficulty_target(
    difficulty_profile: dict[str, Any] | None,
    curriculum: str | None,
    position: int,
    target_section: str | None,
) -> dict[str, Any] | None:
    if not difficulty_profile or not curriculum:
        return None
    calibration = (difficulty_profile.get("curricula") or {}).get(curriculum)
    if not calibration:
        return None
    slot = (calibration.get("by_question_number") or {}).get(str(position))
    if slot and slot.get("count", 0) >= 3:
        recommended = slot.get("recommended_target") or {}
        p_center = recommended.get("p_center")
        if isinstance(p_center, (int, float)):
            return {
                "overall": overall_from_target_p(float(p_center)),
                "basis": "official_empirical_target",
                "p_center": p_center,
                "p_range": recommended.get("p_range"),
                "discrimination_floor": recommended.get("discrimination_floor"),
                "observations": slot.get("count"),
                "roc_years": slot.get("roc_years"),
                "source_fingerprint": difficulty_profile.get("source_fingerprint"),
                "target_note": "Target P is predictive; achieved difficulty requires pilot-response data.",
            }
    if target_section:
        for section_name, section in (calibration.get("by_section") or {}).items():
            if not section_labels_match(section_name, target_section):
                continue
            p_center = section.get("p_median")
            if isinstance(p_center, (int, float)):
                return {
                    "overall": overall_from_target_p(float(p_center)),
                    "basis": "official_empirical_section_fallback",
                    "p_center": p_center,
                    "p_range": [section.get("p_q25"), section.get("p_q75")],
                    "discrimination_floor": max(0.20, round(float(section.get("discrimination_median", 0.3)) * 0.75, 2)),
                    "observations": section.get("count"),
                    "source_fingerprint": difficulty_profile.get("source_fingerprint"),
                    "target_note": "Exact slot lacked three observations; section distribution used as fallback.",
                }
    return None


def generate_plan(
    root: Path,
    exam: str,
    subject: str,
    count: int | None,
    seed: int,
    curriculum: str | None,
    difficulty: str | None,
    excluded_units: list[str],
    output: Path | None,
    allow_insufficient: bool,
    full_paper: bool = False,
    paper_id: str | None = None,
    paper_year: int | None = None,
) -> int:
    subject_path = resolve_subject(root, exam, subject)
    paper_profile = None
    subject = subject if subject in {'國綜', '國寫'} else subject_path.name
    layout_profile = None
    if full_paper:
        if difficulty:
            raise ValueError("完整模擬卷必須保留官方逐題難度曲線；--difficulty 僅適用於自訂練習。")
        paper_profile = select_paper_profile(subject_path, curriculum, paper_id, paper_year,
                                             subject if subject in {'國綜', '國寫'} else None)
        paper_count = paper_profile["numbered_question_count"]
        if count is not None and count != paper_count:
            raise ValueError(f"--count {count} 與 Paper Profile 的整卷題數 {paper_count} 不一致")
        count = paper_count
    if count is None or count < 1:
        raise ValueError("自訂練習需提供大於 0 的 --count；全卷請使用 --full-paper")
    blueprint_path = subject_path / "blueprints" / "writer-blueprint.json"
    if not blueprint_path.exists():
        raise ValueError(f"{exam}/{subject} 尚無 aggregate-only writer blueprint；請先匯入 metadata 並執行 build-blueprints。")
    from writer_calibration import load_writer
    blueprint = load_writer(subject_path, root if full_paper else None)
    curricula = blueprint.get("curricula", [])
    if not curriculum and len(curricula) > 1:
        raise ValueError(f"Blueprint 含多個課綱版本 {curricula}；請用 --curriculum 明確指定，禁止混合抽樣。")
    if blueprint.get("source_visibility") != "aggregate-only" or blueprint.get("individual_source_question_ids_included") is not False:
        raise ValueError("Writer blueprint 未通過來源隔離檢查。")
    patterns = blueprint["aggregate_pattern_clusters"]
    selected_curriculum = curriculum or (curricula[0] if curricula else None)
    if selected_curriculum and selected_curriculum not in curricula:
        raise ValueError(f"Blueprint 不含課綱 {curriculum}")
    curriculum_status = blueprint.get("calibration_by_curriculum", {}).get(
        selected_curriculum, {"status": blueprint.get("calibration_status")}
    )
    if curriculum_status.get("status") != "ready" and (full_paper or not allow_insufficient):
        dimensions = curriculum_status.get("dimensions") or {}
        missing = [name for name, value in dimensions.items() if value.get("status") == "insufficient-data"]
        detail = f"；缺少：{', '.join(missing)}" if missing else ""
        if full_paper:
            raise ValueError(f"所選課綱未通過完整模擬卷校準門檻{detail}。--allow-insufficient 不可繞過整卷門檻。")
        raise ValueError("所選課綱的資料量尚未達歷史校準門檻；可補資料，或明確使用 --allow-insufficient 產生探索性規格。")
    if full_paper and exam == "學測":
        layout_profile = select_layout_profile(subject_path, selected_curriculum, paper_profile)
    if selected_curriculum:
        patterns = [p for p in patterns if p["pattern"].get("curriculum") == selected_curriculum]
    if difficulty:
        patterns = [p for p in patterns if difficulty_band(p["pattern"]["difficulty"]["overall"]) == difficulty]
    if excluded_units:
        excluded = set(excluded_units)
        patterns = [p for p in patterns if p["pattern"]["unit"] not in excluded]
    if not patterns:
        raise ValueError("篩選條件下沒有可用的歷史題型 pattern。")
    rng = random.Random(seed)
    difficulty_profile_path = subject_path / "blueprints" / "difficulty-profile.json"
    difficulty_profile = load_json(difficulty_profile_path) if difficulty_profile_path.exists() else None
    items = []
    missing_pattern_slots: list[dict[str, Any]] = []
    target_slots = [None] * count
    if paper_profile:
        target_slots = paper_profile['evidence']['structure_review']['slots']
        count = len(target_slots)
    for index, slot in enumerate(target_slots, 1):
        target_section = slot.get('section_id') if slot else None
        target_type = slot.get('type') if slot else None
        target = ({'target_slot_id': slot['id'], 'target_number': slot.get('number'),
                   'target_score': slot['score'], 'target_option_count': slot.get('option_count'),
                   'target_required_selection_count': slot.get('required_selection_count'),
                   'target_response_format': slot.get('response_format'),
                   'target_scoring_dependency': slot.get('scoring_dependency')}
                  if slot else {})
        section_title = next((s['title'] for s in paper_profile['sections'] if s['id'] == target_section), None) if paper_profile else None
        candidates = patterns
        if paper_profile and target_section:
            candidates = matching_slot_patterns(patterns, paper_profile, slot)
            if not candidates:
                missing_pattern_slots.append(
                    {"position": index, "section": target_section, "question_type": target_type}
                )
                items.append(
                    {
                        "item_id": f"generated-{index:02d}",
                        **target,
                        "target_position": index,
                        "target_section": target_section,
                        "target_question_type": target_type,
                        "section": target_section,
                        "question_type": target_type,
                        "curriculum": selected_curriculum,
                        "pattern_status": "missing_matching_aggregate_cluster",
                        "originality_contract": {
                            "writer_source_visibility": "aggregate-only",
                            "minimum_distinct_mechanism_candidates": 3,
                            "all_content_generated_fresh": True,
                        },
                    }
                )
                continue
        elif target_type:
            typed = [item for item in candidates if item["pattern"].get("question_type") == target_type]
            if typed:
                candidates = typed
        group = rng.choices(candidates, weights=[p["count"] for p in candidates], k=1)[0]
        pattern = group["pattern"]
        writer_pattern = dict(pattern)
        aggregate_cluster_id = group["cluster_id"]
        target_difficulty = official_difficulty_target(
            difficulty_profile, selected_curriculum, slot.get('number'), section_title
        ) if paper_profile and exam == "學測" and target_type in {'single_choice', 'multiple_choice'} and isinstance(slot.get('number'), int) else None
        items.append(
            {
                "item_id": f"generated-{index:02d}",
                "target_position": index,
                "target_section": target_section,
                "target_question_type": target_type,
                "pattern_status": "matched_aggregate_cluster",
                **writer_pattern,
                "aggregate_response_type": pattern.get('question_type'),
                **target,
                **({'section': target_section, 'question_type': target_type, 'score': slot['score']} if slot else {}),
                "curriculum": selected_curriculum,
                "current_form_cluster_id": aggregate_cluster_id,
                "aggregate_support_count": int(group.get("count") or 0),
                "originality_contract": {
                    "writer_source_visibility": "aggregate-only",
                    "minimum_distinct_mechanism_candidates": 3,
                    "all_content_generated_fresh": True,
                    "forbid_legacy_generated_content": True,
                    "required_audits": ["lexical", "solution-graph", "distractor-path", "visual-topology-if-applicable"],
                },
                "target_difficulty": target_difficulty,
            }
        )
    result = {
        "exam": exam,
        "subject": subject,
        "count": count,
        "numbered_question_count": paper_profile['numbered_question_count'] if paper_profile else count,
        "seed": seed,
        "calibration_level": (
            "incomplete-pattern-coverage" if missing_pattern_slots else
            "historically-calibrated" if curriculum_status.get("status") == "ready" else "exploratory-uncalibrated"
        ),
        "blueprint_fingerprint": blueprint["metadata_fingerprint"],
        "constraints": {
            "curriculum": curriculum,
            "difficulty_band": difficulty,
            "excluded_units": excluded_units,
        },
        "generation_isolation": {
            "writer_source_visibility": "aggregate-only",
            "individual_source_question_ids_exposed": False,
            "inherits_previous_generated_paper": False,
            "minimum_distinct_mechanism_candidates_per_item": 3,
            "distribution_policy": "new coherent draw inside the multi-year aggregate envelope; never copy one year's unit sequence",
        },
        "paper_profile": (
            {
                "paper_id": paper_profile["paper_id"],
                "year": paper_profile["year"],
                "bundle": paper_profile.get("bundle"),
                "source_kind": paper_profile["source_kind"],
                "curriculum": paper_profile["curriculum"],
                "regime": paper_profile.get("regime"),
                "duration_minutes": paper_profile["duration_minutes"],
                "total_score": paper_profile["total_score"],
                "numbered_question_count": paper_profile["numbered_question_count"],
                "sections": paper_profile["sections"],
                "structure_status": paper_profile["structure_status"],
                "evidence": paper_profile["evidence"],
            }
            if paper_profile
            else None
        ),
        "layout_profile": (
            {
                "profile_id": layout_profile["profile_id"],
                "reference_year": layout_profile.get("reference_year"),
                "fidelity_status": layout_profile["fidelity_status"],
                "instruction_transcription_status": (layout_profile.get("instructions") or {}).get("transcription_status"),
            }
            if layout_profile
            else None
        ),
        "historical_pattern_coverage": {
            "matched_slots": count - len(missing_pattern_slots),
            "total_slots": count,
            "missing_slots": missing_pattern_slots,
        },
        "official_difficulty_coverage": (
            {
                "matched_slots": sum(item.get("target_difficulty") is not None for item in items),
                "total_slots": count,
                "source_fingerprint": difficulty_profile.get("source_fingerprint") if difficulty_profile else None,
                "note": "Official P/D tables do not cover every constructed-response slot; those require rubric-score calibration.",
            }
            if paper_profile and exam == "學測"
            else None
        ),
        "items": items,
    }
    rendered = json_dump(result)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"已輸出 Item Specs：{output}")
    else:
        print(rendered, end="")
    return 2 if missing_pattern_slots else 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Taiwan Exam Skill 資料工具")
    result.add_argument("--root", type=Path, default=ROOT, help="Skill repository 根目錄")
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare", help="建立每個科目的資料投遞目錄")
    sub.add_parser("index-sources", help="索引本機來源檔，不複製題目文字")
    sub.add_parser("validate", help="驗證 manifests 與逐題 metadata")
    sub.add_parser("status", help="顯示各科資料與校準狀態")
    builder = sub.add_parser("build-blueprints", help="由 metadata 建立 learned blueprints")
    builder.add_argument("--exam", help="只重建指定考試，不更動其他校準資料")
    builder.add_argument("--subject", help="只重建指定科目")

    importer = sub.add_parser("import-csv", help="匯入逐題 CSV metadata")
    importer.add_argument("--exam", required=True)
    importer.add_argument("--subject", required=True)
    importer.add_argument("--input", required=True, type=Path)
    importer.add_argument("--replace", action="store_true")

    planner = sub.add_parser("plan", help="由 learned blueprint 抽樣 Item Specs")
    planner.add_argument("--exam", required=True)
    planner.add_argument("--subject", required=True)
    planner.add_argument("--count", type=int)
    planner.add_argument("--full-paper", action="store_true", help="鎖定完整 Paper Profile 的題數與大題配方")
    planner.add_argument("--paper-id", help="指定 metadata/papers.jsonl 中的 paper_id")
    planner.add_argument("--paper-year", type=int, help="選擇指定西元年度的已驗證卷型")
    planner.add_argument("--seed", type=int, default=42)
    planner.add_argument("--curriculum")
    planner.add_argument("--difficulty", choices=("easy", "medium", "medium_hard", "hard"))
    planner.add_argument("--exclude-unit", action="append", default=[])
    planner.add_argument("--output", type=Path)
    planner.add_argument("--allow-insufficient", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "prepare":
            return prepare(root)
        if args.command == "index-sources":
            return index_sources(root)
        if args.command == "validate":
            return validate_repository(root)[0]
        if args.command == "status":
            return status(root)
        if args.command == "build-blueprints":
            return build_blueprints(root, args.exam, args.subject)
        if args.command == "import-csv":
            return import_csv(root, args.exam, args.subject, args.input.resolve(), args.replace)
        if args.command == "plan":
            if args.count is not None and args.count < 1:
                raise ValueError("--count 必須大於 0")
            return generate_plan(
                root,
                args.exam,
                args.subject,
                args.count,
                args.seed,
                args.curriculum,
                args.difficulty,
                args.exclude_unit,
                args.output.resolve() if args.output else None,
                args.allow_insufficient,
                args.full_paper,
                args.paper_id,
                args.paper_year,
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
