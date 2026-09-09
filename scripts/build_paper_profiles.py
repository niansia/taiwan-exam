#!/usr/bin/env python3
"""Create paper-level structure profiles from the ingested GSAT source registry."""

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

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover
    raise SystemExit("需要 pypdf；請使用工作區內含 pypdf 的 Python 執行環境。") from exc


ROOT = Path(__file__).resolve().parents[1]
QUESTION_MARKER = re.compile(r"(?m)^\s*(\d{1,2})\s*[.．、]\s*")
SECTION_PATTERNS = [
    re.compile(r"(?m)^\s*第[壹貳參肆伍陸柒捌玖拾一二三四五六七八九十]+(?:部分|大題)[^\n]{0,60}$"),
    re.compile(
        r"(?m)^\s*[一二三四五六七八九十]+[、．.]\s*"
        r"(?:單選題|多選題|選填題|混合題|非選擇題|選擇題|詞彙題|綜合測驗|文意選填|篇章結構|閱讀測驗|中譯英|英文作文)[^\n]{0,40}$"
    ),
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def extract_text(path: Path) -> str:
    reader = PdfReader(path, strict=False)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_isolated(path: Path, timeout_seconds: int) -> str:
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--extract-one", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    if completed.returncode:
        raise RuntimeError((completed.stderr or completed.stdout or "PDF text extraction failed")[:300])
    return json.loads(completed.stdout)["text"]


def clean_heading(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()[:100]


def normalize_extracted_text(text: str) -> str:
    """Repair common spacing artifacts introduced by PDF text extraction."""
    text = text.replace("\u3000", " ")
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[第占共每（(、：:])\s+", "", text)
    text = re.sub(r"\s+(?=[題分）)])", "", text)
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"(?<=\d)\s+(?=\d\s*分)", "", text)
    return text


def section_type_mix(title: str, count: int | None) -> dict[str, int]:
    if count is None:
        return {}
    if "多選" in title:
        return {"multiple_choice": count}
    if "選填" in title:
        return {"fill_in": count}
    if "混合" in title:
        return {"mixed_group": count}
    if "非選擇" in title or "中譯英" in title or "作文" in title:
        return {"constructed_response": count}
    if "單選" in title or "詞彙" in title or "閱讀" in title or "綜合" in title or "篇章" in title:
        return {"single_choice": count}
    return {}


def find_headings(text: str) -> list[tuple[int, str]]:
    found: dict[tuple[int, str], None] = {}
    for pattern in SECTION_PATTERNS:
        for match in pattern.finditer(text):
            heading = clean_heading(match.group(0))
            if 2 <= len(heading) <= 100:
                found[(match.start(), heading)] = None
    return sorted(found)


def major_part_sections(
    text: str, markers: list[tuple[int, int]], plausible_max: int | None
) -> list[dict[str, Any]]:
    if plausible_max is None:
        return []
    headings = [
        (match.start(), clean_heading(match.group(0)))
        for match in re.finditer(
            r"(?m)^\s*第[壹貳參肆伍陸柒捌玖拾一二三四五六七八九十]+部分[^\n]{0,80}$",
            text,
        )
    ]
    if len(headings) < 2:
        return []
    sections: list[dict[str, Any]] = []
    last_number = 0
    for index, (start, title) in enumerate(headings):
        end = headings[index + 1][0] if index + 1 < len(headings) else len(text)
        numbers = sorted({number for position, number in markers if start <= position < end and last_number < number <= plausible_max})
        if not numbers:
            return []
        first = min(numbers)
        final = max(numbers)
        count = final - first + 1
        if first != last_number + 1:
            return []
        score_match = re.search(r"(?:占|共)\s*(\d+(?:\.\d+)?)\s*分", title)
        if not score_match:
            return []
        nearby = text[start : min(end, start + 600)]
        if "混合題" in title or "非選擇題" in title:
            type_mix = {"mixed_group": count}
        elif re.search(r"為\s*單選題", nearby):
            type_mix = {"single_choice": count}
        else:
            # Natural-science choice sections can mix single- and multiple-choice
            # items without declaring their individual counts in the instructions.
            type_mix = {}
        score = float(score_match.group(1))
        sections.append({
            "id": f"section-{index + 1}", "title": title, "order": index + 1,
            "question_number_start": first, "question_number_end": final,
            "numbered_question_count": count, "scored_item_count": count,
            "group_count": None, "question_type_mix": type_mix,
            "subtotal_score": score, "score_rule": clean_heading(score_match.group(0)),
            "instructions_pattern": None,
        })
        last_number = final
    return sections if last_number == plausible_max else []


def parse_structure(text: str, fallback_title: str, official: bool = False) -> tuple[int | None, list[dict[str, Any]], float, str]:
    if official:
        text = normalize_extracted_text(text)
    if fallback_title == "國寫":
        prompt_count = len(set(re.findall(r"問題\s*[（(][一二三四五六七八九十]+[）)]", text)))
        if prompt_count:
            sections = [{
                "id": "section-1", "title": "國寫非選擇題", "order": 1,
                "question_number_start": 1, "question_number_end": prompt_count,
                "numbered_question_count": prompt_count, "scored_item_count": prompt_count,
                "group_count": None, "question_type_mix": {"guided_writing": prompt_count},
                "subtotal_score": 50.0 if prompt_count == 2 else None,
                "score_rule": "兩大題合計 50 分" if prompt_count == 2 else None,
                "instructions_pattern": None,
            }]
            return prompt_count, sections, 0.95, f"Detected {prompt_count} Chinese-numbered writing prompts."

    markers = [
        (match.start(), int(match.group(1)))
        for match in QUESTION_MARKER.finditer(text)
        if 1 <= int(match.group(1)) <= 80
    ]
    numbers = sorted({number for _, number in markers})
    range_matches = list(re.finditer(r"第\s*(\d{1,2})\s*題?\s*(?:至|到|[-~～])\s*第?\s*(\d{1,2})\s*題", text))
    range_ends = [int(match.group(2)) for match in range_matches]
    plausible_max = max(numbers + range_ends) if numbers or range_ends else None
    if plausible_max and plausible_max > 80:
        plausible_max = None
    contiguous = 0.0
    if plausible_max:
        contiguous = len({number for number in numbers if 1 <= number <= plausible_max}) / plausible_max
        if contiguous < 0.45:
            plausible_max = None

    headings = find_headings(text)
    sections: list[dict[str, Any]] = []
    if headings:
        for index, (start, title) in enumerate(headings):
            end = headings[index + 1][0] if index + 1 < len(headings) else len(text)
            section_numbers = sorted({number for position, number in markers if start <= position < end})
            nearby = text[start : min(end, start + 500)]
            range_match = re.search(r"第\s*(\d{1,2})\s*題?\s*(?:至|到|[-~～])\s*第?\s*(\d{1,2})\s*題", nearby)
            explicit_start = int(range_match.group(1)) if range_match else None
            explicit_end = int(range_match.group(2)) if range_match else None
            count_match = re.search(r"共\s*(\d{1,2})\s*題", nearby)
            explicit_count = (explicit_end - explicit_start + 1) if range_match and explicit_end >= explicit_start else (int(count_match.group(1)) if count_match else None)
            count = explicit_count or len(section_numbers) or None
            score_match = re.search(r"(?:占|共)\s*(\d+(?:\.\d+)?)\s*分", nearby)
            subtotal = float(score_match.group(1)) if score_match else None
            english_constructed = fallback_title == "英文" and any(label in title for label in ("中譯英", "作文"))
            if count is None and fallback_title == "英文" and subtotal is not None:
                if any(label in title for label in ("詞彙", "綜合測驗", "文意選填")):
                    count = int(subtotal)
                elif any(label in title for label in ("篇章結構", "閱讀測驗")):
                    count = int(subtotal / 2)
            if count is None and "作文" in title and not english_constructed:
                count = 1
            scored_count = 1 if english_constructed else count
            candidate = {
                "id": f"section-{index + 1}",
                "title": title,
                "order": index + 1,
                "question_number_start": explicit_start if explicit_start is not None else (min(section_numbers) if section_numbers else None),
                "question_number_end": explicit_end if explicit_end is not None else (max(section_numbers) if section_numbers else None),
                "numbered_question_count": count,
                "scored_item_count": scored_count,
                "group_count": None,
                "question_type_mix": section_type_mix(title, count),
                "subtotal_score": subtotal,
                "score_rule": clean_heading(score_match.group(0)) if score_match else None,
                "instructions_pattern": None,
                "_raw_numbers": section_numbers,
                "_explicit_range": range_match is not None,
            }
            # Drop parent headings that only announce a subtotal before leaf subsections.
            if count is not None or scored_count is not None:
                sections.append(candidate)
    elif plausible_max:
        sections.append({
            "id": "section-1",
            "title": fallback_title,
            "order": 1,
            "question_number_start": 1,
            "question_number_end": plausible_max,
            "numbered_question_count": plausible_max,
            "scored_item_count": plausible_max,
            "group_count": None,
            "question_type_mix": {},
            "subtotal_score": None,
            "score_rule": None,
            "instructions_pattern": None,
        })

    if plausible_max and headings and sections:
        last_end = 0
        for item in sections:
            raw = item.pop("_raw_numbers", [])
            explicit_range = item.pop("_explicit_range", False)
            filtered = sorted({number for number in raw if last_end < number <= plausible_max})
            if explicit_range:
                last_end = max(last_end, item["question_number_end"] or last_end)
            elif filtered:
                item["question_number_start"] = min(filtered)
                item["question_number_end"] = max(filtered)
                item["numbered_question_count"] = len(filtered)
                item["scored_item_count"] = len(filtered)
                item["question_type_mix"] = section_type_mix(item["title"], len(filtered))
                last_end = max(filtered)
            elif "作文" in item["title"] and last_end < plausible_max:
                last_end += 1
                item["question_number_start"] = last_end
                item["question_number_end"] = last_end
                item["numbered_question_count"] = 1
                item["scored_item_count"] = 1
                item["question_type_mix"] = {"constructed_response": 1}
        sections = [item for item in sections if item["numbered_question_count"] or item["scored_item_count"]]
        for order, item in enumerate(sections, 1):
            item["order"] = order
            item["id"] = f"section-{order}"

        if fallback_title == "英文":
            flexible: list[dict[str, Any]] = []
            for item in sections:
                title = item["title"]
                score = item["subtotal_score"]
                normalized: int | None = None
                if score is not None and any(label in title for label in ("詞彙", "綜合測驗", "文意選填")):
                    normalized = int(score)
                elif score is not None and any(label in title for label in ("篇章結構", "閱讀測驗")):
                    normalized = int(score / 2)
                elif "中譯英" in title or "作文" in title:
                    item["numbered_question_count"] = None
                    item["scored_item_count"] = 1
                    item["question_number_start"] = None
                    item["question_number_end"] = None
                    item["question_type_mix"] = {"constructed_response": 1}
                    continue
                elif "混合題" in title:
                    flexible.append(item)
                if normalized:
                    item["numbered_question_count"] = normalized
                    item["scored_item_count"] = normalized
                    item["question_type_mix"] = section_type_mix(title, normalized)
            fixed = sum(item["numbered_question_count"] or 0 for item in sections if item not in flexible)
            if len(flexible) == 1 and 0 < plausible_max - fixed <= 10:
                flexible[0]["numbered_question_count"] = plausible_max - fixed
                flexible[0]["scored_item_count"] = plausible_max - fixed
                flexible[0]["question_type_mix"] = {"mixed_group": plausible_max - fixed}
            next_number = 1
            for item in sections:
                count = item["numbered_question_count"] or 0
                if count:
                    item["question_number_start"] = next_number
                    item["question_number_end"] = next_number + count - 1
                    next_number += count
                else:
                    item["question_number_start"] = None
                    item["question_number_end"] = None

    if fallback_title in {"社會", "自然"}:
        major = major_part_sections(text, markers, plausible_max)
        if major:
            sections = major

    for item in sections:
        item.pop("_raw_numbers", None)
        item.pop("_explicit_range", None)

    confidence = 0.0
    if plausible_max:
        confidence = 0.55 + min(contiguous, 1.0) * 0.2
    if sections and any(item["numbered_question_count"] for item in sections):
        confidence += 0.08
    reconciled = plausible_max is not None and sum(item["numbered_question_count"] or 0 for item in sections) == plausible_max
    if reconciled and len(sections) >= 2:
        confidence += 0.08
    section_scores = [item.get("subtotal_score") for item in sections]
    if (
        fallback_title == "英文"
        and reconciled
        and section_scores
        and all(isinstance(value, (int, float)) for value in section_scores)
        and abs(sum(section_scores) - 100) < 1e-6
    ):
        # English fill-in and mixed blanks are not always extractable as line-start
        # item markers. Explicit section ranges plus a reconciled 100-point section
        # table are stronger evidence than raw marker coverage in that case.
        confidence = max(confidence + 0.04, 0.92)
    confidence = round(min(confidence, 0.95), 2)
    note = (
        f"Detected {len(numbers)} distinct Arabic item markers and {len(headings)} section headings; "
        f"section counts {'reconcile' if reconciled else 'do not reconcile'} with the paper total."
    )
    return plausible_max, sections, confidence, note


def parse_duration(text: str) -> int | None:
    matches = re.findall(r"(?:作答|測驗|考試)時間[^\d]{0,8}(\d{2,3})\s*分(?:鐘)?", text)
    values = [int(value) for value in matches if 30 <= int(value) <= 180]
    return Counter(values).most_common(1)[0][0] if values else None


def parse_total_score(text: str) -> float | None:
    matches = re.findall(r"(?:滿分|全卷共|總分)[^\d]{0,8}(\d{2,3}(?:\.\d+)?)\s*分", text)
    values = [float(value) for value in matches if 10 <= float(value) <= 200]
    return Counter(values).most_common(1)[0][0] if values else None


def official_current_structure(
    roc_year: int, subject: str, section: str | None
) -> tuple[int, int, list[dict[str, Any]], float] | None:
    """Legacy reference recipes, NEVER proof of observed or verified structure."""
    if not 111 <= roc_year <= 115:
        return None
    recipes: list[tuple[str, int, int, float, str]] | None = None
    if subject == "國文" and section == "國寫":
        recipes = [("國寫非選擇題", 2, 2, 50, "guided_writing")]
    elif subject == "國文" and section == "國綜":
        if roc_year <= 112:
            recipes = [("單選題", 25, 25, 50, "single_choice"), ("多選題", 7, 7, 28, "multiple_choice"), ("混合題或非選擇題", 5, 5, 22, "mixed_group")]
        else:
            recipes = [("單選題", 24, 24, 48, "single_choice"), ("多選題", 7, 7, 28, "multiple_choice"), ("混合題或非選擇題", 5, 5, 24, "mixed_group")]
    elif subject == "數學A":
        recipes = [("單選題", 6, 6, 30, "single_choice"), ("多選題", 6, 6, 30, "multiple_choice"), ("選填題", 5, 5, 25, "fill_in"), ("混合題或非選擇題", 3, 3, 15, "mixed_group")]
    elif subject == "數學B":
        recipes = [("單選題", 7, 7, 35, "single_choice"), ("多選題", 5, 5, 25, "multiple_choice"), ("選填題", 5, 5, 25, "fill_in"), ("混合題或非選擇題", 3, 3, 15, "mixed_group")]
    elif subject == "英文":
        recipes = [
            ("詞彙題", 10, 10, 10, "single_choice"), ("綜合測驗", 10, 10, 10, "single_choice"),
            ("文意選填", 10, 10, 10, "fill_in"), ("篇章結構", 4, 4, 8, "single_choice"),
            ("閱讀測驗", 12, 12, 24, "single_choice"), ("混合題", 4, 4, 10, "mixed_group"),
            ("中譯英", 0, 1, 8, "constructed_response"), ("英文作文", 0, 1, 20, "constructed_response"),
        ]
    elif subject == "社會":
        totals = {111: 67, 112: 66, 113: 64, 114: 64, 115: 65}
        first_counts = {111: 46, 112: 45, 113: 35, 114: 42, 115: 38}
        first_scores = {111: 92, 112: 90, 113: 70, 114: 84, 115: 76}
        first = first_counts[roc_year]
        recipes = [("選擇題", first, first, first_scores[roc_year], "single_choice"), ("混合題或非選擇題", totals[roc_year] - first, totals[roc_year] - first, 144 - first_scores[roc_year], "mixed_group")]
    elif subject == "自然":
        totals = {111: 60, 112: 61, 113: 56, 114: 57, 115: 56}
        recipes = [("選擇題", 36, 36, 72, "unresolved_choice_mix"), ("混合題或非選擇題", totals[roc_year] - 36, totals[roc_year] - 36, 56, "mixed_group")]
    if recipes is None:
        return None
    sections: list[dict[str, Any]] = []
    start = 1
    for order, (title, numbered_count, scored_count, score, question_type) in enumerate(recipes, 1):
        end = start + numbered_count - 1 if numbered_count else None
        sections.append({
            "id": f"section-{order}", "title": title, "order": order,
            "question_number_start": start if numbered_count else None, "question_number_end": end,
            "numbered_question_count": numbered_count or None, "scored_item_count": scored_count,
            "group_count": None, "question_type_mix": {} if question_type == "unresolved_choice_mix" else {question_type: scored_count},
            "subtotal_score": float(score), "score_rule": f"占 {score} 分", "instructions_pattern": None,
        })
        if numbered_count:
            start = int(end) + 1
    return start - 1, sum(item[2] for item in recipes), sections, float(sum(item[3] for item in recipes))


def build(root: Path, timeout_seconds: int, bundle_filter: str | None = None) -> int:
    metadata_root = root / "exam_packs" / "學測" / "metadata"
    registry: list[dict[str, Any]] = []
    for name in ("source-registry.jsonl", "official-source-registry.jsonl"):
        path = metadata_root / name
        if path.is_file():
            registry.extend(read_jsonl(path))
    if not registry:
        raise SystemExit(f"找不到來源索引：{metadata_root}")
    if bundle_filter:
        registry = [row for row in registry if row.get("bundle") == bundle_filter]
        if not registry:
            raise SystemExit(f"來源索引中找不到套卷：{bundle_filter}")
    paper_roles = {"question", "question_and_solution"}
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in registry:
        if record.get("subject") == "shared":
            continue
        groups[(record["bundle"], record["subject"], record.get("section") or "")].append(record)
    paper_groups = {key: value for key, value in groups.items() if any(item["role"] in paper_roles for item in value)}
    by_subject: dict[str, list[dict[str, Any]]] = defaultdict(list)
    statuses: Counter[str] = Counter()

    for index, ((bundle, subject, section), records) in enumerate(sorted(paper_groups.items()), 1):
        sources = sorted(
            records,
            key=lambda item: (
                0 if item["role"] == "question" else 1 if item["role"] == "question_and_solution" else 2,
                item["destination_relative_path"],
            ),
        )
        question_extractable = [
            item for item in sources
            if item.get("extension", "").lower() == ".pdf"
            and item.get("text_layer_status") == "extractable"
            and item.get("role") == "question"
        ]
        combined_extractable = [
            item for item in sources
            if item.get("extension", "").lower() == ".pdf"
            and item.get("text_layer_status") == "extractable"
            and item.get("role") == "question_and_solution"
        ]
        solution_extractable = [
            item for item in sources
            if item.get("extension", "").lower() == ".pdf"
            and item.get("text_layer_status") == "extractable"
            and item.get("role") == "solution"
        ]
        extractable = question_extractable or combined_extractable[:1] or solution_extractable[:1]
        text_parts: list[str] = []
        errors: list[str] = []
        for item in extractable:
            try:
                text_parts.append(extract_text_isolated(root / item["destination_relative_path"], timeout_seconds))
            except (subprocess.TimeoutExpired, RuntimeError, OSError, json.JSONDecodeError) as exc:
                errors.append(f"{item['sha256'][:10]}:{type(exc).__name__}")
        text = "\n".join(text_parts)
        question_sources = [item for item in sources if item["role"] in paper_roles]
        identifier_source = question_sources[0]
        is_official = identifier_source.get("source_kind") == "official_past_exam"
        total, sections, confidence, note = parse_structure(text, section or subject, official=is_official) if text else (None, [], 0.0, "No extractable text.")
        verified_structure = official_current_structure(identifier_source["roc_year"], subject, section or None) if is_official else None
        if verified_structure:
            total, verified_scored_total, sections, verified_score = verified_structure
            confidence = min(confidence, 0.8)
            note = "Legacy reference recipe only; requires page-by-page source reconciliation and scored-slot inventory. " + note
        if verified_structure:
            status = "needs_review"
            method = "official_document"
        elif total:
            status = "auto_parsed"
            method = "text_layer_parse"
        elif text:
            status = "needs_review"
            method = "text_layer_parse"
        else:
            status = "pending_ocr"
            method = "unparsed"
        statuses[status] += 1
        inferred_total_score = parse_total_score(normalize_extracted_text(text) if is_official else text) if text else None
        if verified_structure:
            inferred_total_score = verified_score
        if sections and total and sum(item.get("numbered_question_count") or 0 for item in sections) == total and all(item["subtotal_score"] is not None for item in sections):
            summed = sum(item["subtotal_score"] for item in sections)
            if 20 <= summed <= 200:
                inferred_total_score = summed
        parsed_scored_total = (
            sum(item.get("scored_item_count") or 0 for item in sections)
            if sections and all(item.get("scored_item_count") is not None for item in sections)
            else total
        )
        profile = {
            "paper_id": f"gsat-{identifier_source['year']}-{identifier_source['series'].lower()}-{identifier_source['sha256'][:12]}",
            "exam": "學測",
            "year": identifier_source["year"],
            "subject": subject,
            "section": section or None,
            "curriculum": identifier_source.get("curriculum") or "108",
            "regime": identifier_source.get("regime") or "111學年度起",
            "publisher": identifier_source.get("publisher"),
            "bundle": bundle,
            "source_kind": identifier_source.get("source_kind") or "mock_exam",
            "source_files": [
                {
                    "sha256": item["sha256"],
                    "relative_path": item["destination_relative_path"],
                    "role": item["role"],
                    "page_count": item.get("pdf_pages"),
                }
                for item in sources
            ],
            "duration_minutes": parse_duration(text) if text else None,
            "total_score": inferred_total_score,
            "numbered_question_count": total,
            "scored_item_count": verified_scored_total if verified_structure else parsed_scored_total,
            "structure_status": status,
            "sections": sections,
            "layout": {
                "paper_size": "A4",
                "columns": 1,
                "answer_sheet_mode": "另附答題卷" if identifier_source.get("source_kind") == "official_past_exam" else "卷卡合一",
            },
            "evidence": {
                "method": method,
                "confidence": confidence,
                "notes": note + (f" Extraction issues: {', '.join(errors)}." if errors else ""),
                "reviewed_at": None,
            },
        }
        by_subject[subject].append(profile)
        if index % 15 == 0 or index == len(paper_groups):
            print(f"已建立 {index}/{len(paper_groups)} 份 Paper Profile", flush=True)

    for subject, profiles in by_subject.items():
        target = root / "exam_packs" / "學測" / "subjects" / subject / "metadata" / "papers.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        output_profiles = profiles
        if target.is_file():
            from pack_verification import paper_errors
            reviewed = {p['paper_id']: p for p in read_jsonl(target)
                        if p.get('structure_status') == 'verified' and not paper_errors(p, root)}
            output_profiles = [reviewed.get(p['paper_id'], p) for p in profiles]
        if bundle_filter and target.is_file():
            preserved = [item for item in read_jsonl(target) if item.get("bundle") != bundle_filter]
            output_profiles = preserved + output_profiles
            output_profiles.sort(key=lambda item: (item.get("year") or 0, item.get("paper_id") or ""))
        target.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in output_profiles), encoding="utf-8")
    if bundle_filter:
        all_profiles = []
        for target in (root / "exam_packs" / "學測" / "subjects").glob("*/metadata/papers.jsonl"):
            all_profiles.extend(read_jsonl(target))
        statuses = Counter(profile["structure_status"] for profile in all_profiles)
        report_by_subject = dict(Counter(profile["subject"] for profile in all_profiles))
    else:
        all_profiles = [profile for profiles in by_subject.values() for profile in profiles]
        report_by_subject = {subject: len(items) for subject, items in sorted(by_subject.items())}
    full_paper_ready = [
        profile for profile in all_profiles
        if (
            profile["structure_status"] == "verified"
        )
        and profile["duration_minutes"] is not None
        and profile["total_score"] is not None
        and profile["numbered_question_count"] is not None
        and profile["sections"]
        and sum(section.get("numbered_question_count") or 0 for section in profile["sections"])
        == profile["numbered_question_count"]
        and sum(section.get("scored_item_count") or 0 for section in profile["sections"])
        == profile["scored_item_count"]
        and all(section.get("subtotal_score") is not None for section in profile["sections"])
        and abs(sum(section["subtotal_score"] for section in profile["sections"]) - profile["total_score"]) < 1e-6
    ]
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paper_profile_count": len(all_profiles),
        "by_status": dict(statuses),
        "by_subject": dict(sorted(report_by_subject.items())),
        "full_paper_ready_count": len(full_paper_ready),
        "full_paper_ready_by_subject": dict(Counter(profile["subject"] for profile in full_paper_ready)),
        "gate": "Only hash-bound page/slot-reviewed profiles may claim full-paper readiness; parser confidence and reference recipes never establish verification.",
    }
    report_path = root / "exam_packs" / "學測" / "metadata" / "paper-profile-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已輸出 {report_path.relative_to(root)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="從學測來源索引建立逐卷結構資料")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--timeout-seconds", type=int, default=12)
    parser.add_argument("--bundle", help="只重建指定套卷並保留其他 Paper Profile")
    parser.add_argument("--extract-one", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.extract_one:
        try:
            print(json.dumps({"text": extract_text(args.extract_one.resolve())}, ensure_ascii=False))
            return 0
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
    return build(args.root.resolve(), args.timeout_seconds, args.bundle)


if __name__ == "__main__":
    raise SystemExit(main())
