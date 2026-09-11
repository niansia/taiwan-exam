#!/usr/bin/env python3
"""Reject current-form 國寫 materials that contain ungrounded or invented cases."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
from pathlib import Path
from typing import Any


BANNED_MARKERS = (
    "命題所設",
    "案例為命題",
    "情境為命題",
    "虛構案例",
    "情境模擬",
)

AUTHORED_AFFECTIVE_VOICES = {
    "authored_literary_prose",
    "authored_poetry",
    "authored_essay",
    "literary_nonfiction",
    "cultural_criticism",
    "interview_or_field_notes",
}

MATERIAL_HEADING = re.compile(r"材料[一二三四甲乙丙丁][：:]")
SOURCE_NOTE = re.compile(r"[（(][^）)]*(?:改寫|節錄|摘錄|取材|引)自[^）)]*[）)]")


def validate_exam(exam: dict[str, Any], source_pool: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if exam.get("metadata", {}).get("paper_subject") != "國寫":
        return ["exam metadata.paper_subject 必須是國寫"]

    records = {
        record.get("source_id"): record
        for record in source_pool.get("sources", [])
        if record.get("source_id")
    }
    questions = exam.get("questions", [])
    if len(questions) != 2:
        errors.append("當代國寫完整卷必須有兩大題")

    if exam.get("metadata", {}).get("generation_mode") == "full-paper":
        policy = source_pool.get("selection_policy") or {}
        if policy.get("publisher_neutral") is not True:
            errors.append("完整國寫卷的 source pool 必須明記 publisher_neutral: true")
        for field in ("preferred_publishers", "allowed_publishers", "publisher_whitelist"):
            if policy.get(field):
                errors.append(f"完整國寫卷不得設定 {field}；來源資格必須與出版者無關")

        candidates = source_pool.get("sources", [])
        publishers = [str(row.get("publisher") or "").strip() for row in candidates]
        domains = [str(row.get("source_domain") or "").strip() for row in candidates]
        if len(candidates) < 8:
            errors.append("完整國寫卷的來源競賽至少需要8個候選")
        if any(not value for value in publishers):
            errors.append("完整國寫卷的每個來源候選都必須記錄 publisher")
        elif len(set(publishers)) < 4:
            errors.append("完整國寫卷的來源競賽至少需要4個不同出版者")
        if any(not value for value in domains):
            errors.append("完整國寫卷的每個來源候選都必須記錄 source_domain")
        elif len(set(domains)) < 4:
            errors.append("完整國寫卷的來源競賽至少需要4個不同領域")

        if publishers and all(publishers):
            publisher, count = Counter(publishers).most_common(1)[0]
            if count > len(publishers) / 2 and not policy.get("dominant_publisher_justification"):
                errors.append(
                    f"完整國寫卷的候選池由「{publisher}」占過半，且未記錄外部可得性理由"
                )

    for question in questions:
        qid = question.get("id") or f"question-{question.get('number', '?')}"
        prompt = str(question.get("prompt") or "")
        continuation_text = "\n\n".join(
            str(value) for _, value in sorted(
                (question.get("continuation_pages") or {}).items(),
                key=lambda item: int(item[0]),
            )
        )
        material_text = "\n\n".join(part for part in (prompt, continuation_text) if part)
        spec = question.get("item_spec") or {}
        source_ids = spec.get("source_ids") or []
        mappings = spec.get("material_source_map") or []

        if not source_ids:
            errors.append(f"{qid}: 缺少 source_ids")
        if not mappings:
            errors.append(f"{qid}: 缺少 paragraph-level material_source_map")

        for marker in BANNED_MARKERS:
            if marker in material_text:
                errors.append(f"{qid}: 題面含禁止的虛構材料標記「{marker}」")

        if MATERIAL_HEADING.search(material_text):
            errors.append(f"{qid}: 正式國寫題面不得用「材料一：／材料二：」作正文標題；多文請用甲、乙編記")

        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", material_text) if part.strip()]
        for paragraph in paragraphs:
            if SOURCE_NOTE.fullmatch(paragraph):
                errors.append(f"{qid}: 來源註記不得獨立成段，應緊接所屬正文末句")

        missing_records = [source_id for source_id in source_ids if source_id not in records]
        if missing_records:
            errors.append(f"{qid}: source pool 缺少 {', '.join(missing_records)}")

        for source_id in source_ids:
            record = records.get(source_id) or {}
            if record.get("invented_modelling_values"):
                errors.append(f"{qid}: 國寫來源 {source_id} 的 invented_modelling_values 必須為空")

        mapped_ids: set[str] = set()
        for index, mapping in enumerate(mappings, 1):
            label = mapping.get("material_id") or f"mapping-{index}"
            mapping_ids = mapping.get("source_ids") or []
            claims = mapping.get("supported_claims") or []
            if not mapping_ids:
                errors.append(f"{qid}/{label}: 缺少來源")
            if not claims:
                errors.append(f"{qid}/{label}: 缺少受來源支持的主張清單")
            for source_id in mapping_ids:
                mapped_ids.add(source_id)
                if source_id not in source_ids:
                    errors.append(f"{qid}/{label}: {source_id} 未列於題目 source_ids")
                if source_id not in records:
                    errors.append(f"{qid}/{label}: {source_id} 不存在於 source pool")

        unmapped = set(source_ids) - mapped_ids
        if unmapped:
            errors.append(f"{qid}: 題目來源未映射到材料段落：{', '.join(sorted(unmapped))}")

        if material_text.count("改寫自") < len(set(source_ids)):
            errors.append(f"{qid}: 題面來源註記少於實際使用的來源數")

        if spec.get("writing_task_role") == "affective_expression":
            voices = {records.get(source_id, {}).get("source_voice") for source_id in source_ids}
            if not (voices & AUTHORED_AFFECTIVE_VOICES):
                errors.append(f"{qid}: 第二大題缺少具有作者聲音的散文／文學性非虛構來源")
            chinese_ready = any(
                str(records.get(source_id, {}).get("source_language") or "").startswith("zh")
                or (
                    records.get(source_id, {}).get("authorized_chinese_translation") is True
                    and str(records.get(source_id, {}).get("printed_title_language") or "").startswith("zh")
                )
                for source_id in source_ids
            )
            if not chinese_ready:
                errors.append(f"{qid}: 第二大題應優先採中文創作；使用翻譯文學時須有可辨識的正式中譯來源與中文篇名")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exam_json", type=Path)
    parser.add_argument("source_pool_json", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam_json.read_text(encoding="utf-8"))
    source_pool = json.loads(args.source_pool_json.read_text(encoding="utf-8"))
    errors = validate_exam(exam, source_pool)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: 國寫來源池不預設出版者，材料均有逐段來源、正式來源註記版式，且第二大題具中文文學來源")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
