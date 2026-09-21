#!/usr/bin/env python3
"""Reject under-written or structurally collapsed 國綜／國寫／英文／社會／自然 papers.

Mathematics already has a pre-writing construction gate
(`validate_math_difficulty_design.py`). The other five current-form subjects did
not, and reviewed papers collapsed in three ways: standalone one-sentence items
instead of shared-stimulus 題組, roughly half an official booklet's reading
material, and 自然 mixed groups that never leave one discipline.

This validator runs on the authored exam JSON **before** layout, so a thin paper
is caught before a booklet is composed. It does not replace
`validate_current_form_density.py`, which compares a rendered PDF, nor any
subject scope audit.

Floors come from `exam_packs/學測/shared-data/current-form-literacy-envelope.json`
and sit below the weakest official ROC 111-115 year, so no official paper would
be rejected by them. See `references/current-form-literacy-load.md`.

Usage:
    python scripts/validate_literacy_load.py generated-exam.json --subject 自然 \
        --report output/literacy-load.json
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "exam_packs" / "學測" / "shared-data"
# The floors below are transcribed from these measured files. A test asserts each
# one still sits under the weakest official year, so a stale floor cannot silently
# start rejecting real papers.
ENVELOPE = SHARED / "current-form-literacy-envelope.json"
CROSS_DISCIPLINE = SHARED / "natural-mixed-group-cross-discipline.json"

WHITESPACE = re.compile(r"\s+")
ASCII_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
DISCIPLINES = ("物理", "化學", "生物", "地科")

# Section ids and titles the packs use for 第貳部分 (混合題或非選擇題).
PART_TWO_IDS = {"section-2", "mixed", "mixed-response", "non-selected", "constructed"}
PART_TWO_TITLE = re.compile(r"第貳部分|混合題|非選擇題")

PLACEHOLDER = {
    "", "n/a", "na", "none", "pending", "pass", "passed", "todo", "tbd",
    "跨科", "跨科整合", "待補", "通過", "無",
}

# Floors are 0.85 of the weakest measured official year, except where a count is
# already an integer minimum.
#
# The volume floors compare against `paper_item_content_chars` / `_words`, not
# the whole booklet: this gate reads the authored exam record, which contains
# unique group stimuli, item prompts and option text but not the cover page or
# the section 說明 blocks the Layout Profile prints. Comparing against the full
# booklet would demand prose the record never holds — for 國寫 that difference
# alone (1,528 vs 1,109 characters) would have rejected a ROC 111-shaped paper.
SUBJECT_FLOORS: dict[str, dict[str, Any]] = {
    "國綜": {
        "unit": "chars",
        "min_paper_chars": 9117,
        "official_weakest": 10727,
        "min_total_groups": 8,
        "group_stimulus_median": 300,
    },
    "國寫": {
        "unit": "chars",
        "min_paper_chars": 942,
        "official_weakest": 1109,
        "min_task_1_chars": 560,
        "min_task_2_chars": 290,
    },
    "英文": {
        "unit": "words",
        "min_paper_words": 2553,
        "official_weakest": 3004,
        "min_total_groups": 6,
    },
    "社會": {
        "unit": "chars",
        "min_paper_chars": 10802,
        "official_weakest": 12709,
        "min_part_1_groups": 5,
        "min_part_2_groups": 7,
        "group_stimulus_median": 170,
        "short_stimulus_chars": 110,
        "max_short_stimulus_ratio": 0.30,
    },
    "自然": {
        "unit": "chars",
        "min_paper_chars": 10687,
        "official_weakest": 12573,
        "min_part_1_groups": 3,
        "min_part_1_grouped_items": 6,
        "exact_part_2_groups": 6,
        "part_2_stimulus_median": 175,
        "short_stimulus_chars": 120,
        "max_short_part_2_groups": 2,
        "part_1_stimulus_median": 90,
        "min_cross_discipline_groups": 2,
    },
}


def compact(text: str) -> int:
    return len(WHITESPACE.sub("", str(text or "")))


def substantive(value: object) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.casefold() not in PLACEHOLDER and len(text) >= 12


def question_text(question: dict[str, Any]) -> str:
    parts = [str(question.get("prompt") or "")]
    for option in question.get("options") or []:
        parts.append(str((option or {}).get("text") or ""))
    return "\n".join(parts)


def part_two_sections(exam: dict[str, Any]) -> set[str]:
    ids = set()
    for section in exam.get("sections") or []:
        identifier = str(section.get("id") or "")
        title = str(section.get("title") or "")
        if identifier in PART_TWO_IDS or PART_TWO_TITLE.search(title):
            ids.add(identifier)
    return ids


def build_groups(questions: list[dict[str, Any]], part_two: set[str]) -> list[dict[str, Any]]:
    """A 題組 is two or more scored items sharing one printed stimulus."""
    shared = Counter(
        str(q.get("group_stimulus") or "").strip()
        for q in questions
        if str(q.get("group_stimulus") or "").strip()
    )
    groups: dict[str, dict[str, Any]] = {}
    for question in questions:
        stimulus = str(question.get("group_stimulus") or "").strip()
        if not stimulus or shared[stimulus] < 2:
            continue
        record = groups.setdefault(
            stimulus,
            {
                "stimulus_compact_chars": compact(stimulus),
                "numbers": [],
                "domains": set(),
                "secondary_domains": set(),
                "part": 1,
            },
        )
        record["numbers"].append(question.get("number"))
        spec = question.get("item_spec") or {}
        domain = normalize_domain(spec.get("domain"))
        if domain:
            record["domains"].add(domain)
        for extra in spec.get("secondary_domains") or []:
            extra = normalize_domain(extra)
            if extra:
                record["secondary_domains"].add(extra)
        if str(question.get("section_id") or "") in part_two:
            record["part"] = 2
    ordered = []
    for record in groups.values():
        numbers = [n for n in record["numbers"] if isinstance(n, int)]
        record["group"] = f"{min(numbers)}-{max(numbers)}" if numbers else ""
        record["items"] = len(record["numbers"])
        record["domains"] = sorted(record["domains"])
        record["secondary_domains"] = sorted(record["secondary_domains"])
        ordered.append(record)
    ordered.sort(key=lambda row: min([n for n in row["numbers"] if isinstance(n, int)] or [0]))
    return ordered


def normalize_domain(value: object) -> str | None:
    text = str(value or "").replace("地球科學", "地科")
    return next((name for name in DISCIPLINES if name in text), None)


def cross_discipline_errors(
    exam: dict[str, Any], groups: list[dict[str, Any]], floor: int
) -> tuple[list[str], int]:
    """Count mixed groups that genuinely require a second discipline.

    Uses the record shape `validate_chinese_natural_scope.py` already defines for
    `metadata.natural_mixed_group_designs` — `question_numbers`,
    `required_domains`, `evidence_bridge` — so a paper declares each group once.
    Only cross-disciplinary groups are listed, which is that field's existing
    convention. `second_discipline_removable: false` is the added assertion that
    the crossing is load-bearing.
    """
    errors: list[str] = []
    declared = (exam.get("metadata") or {}).get("natural_mixed_group_designs")
    if not isinstance(declared, list) or not declared:
        return ["metadata.natural_mixed_group_designs is missing or empty"], 0

    by_number: dict[int, dict[str, Any]] = {}
    for row in groups:
        if row["part"] != 2:
            continue
        for number in row["numbers"]:
            if isinstance(number, int):
                by_number[number] = row

    qualifying = 0
    counted: set[int] = set()
    for index, record in enumerate(declared, 1):
        if not isinstance(record, dict):
            errors.append(f"natural mixed group {index}: invalid design record")
            continue
        numbers = [n for n in (record.get("question_numbers") or []) if isinstance(n, int)]
        if not numbers:
            errors.append(f"natural mixed group {index}: question numbers missing")
            continue
        actual = next((by_number[n] for n in numbers if n in by_number), None)
        if actual is None:
            errors.append(f"natural mixed group {index}: matches no 第貳部分 題組")
            continue
        domains = {normalize_domain(value) for value in (record.get("required_domains") or [])}
        domains.discard(None)
        if len(domains) < 2:
            errors.append(f"natural mixed group {index}: fewer than two valid domains")
            continue
        if not substantive(record.get("evidence_bridge")):
            errors.append(f"natural mixed group {index}: evidence bridge is missing or a placeholder")
            continue
        if record.get("second_discipline_removable") is not False:
            errors.append(
                f"natural mixed group {index}: a removable second discipline has not been rejected"
            )
            continue
        # Structural corroboration: the paper must mark the crossing on its own
        # items, not only in the declaration.
        marked = set(actual["domains"]) | set(actual["secondary_domains"])
        if len(marked) < 2:
            errors.append(
                f"natural mixed group {index}: declares two disciplines but every subpart records "
                "one domain and none declares item_spec.secondary_domains"
            )
            continue
        key = min(numbers)
        if key in counted:
            errors.append(f"natural mixed group {index}: duplicates an already counted 題組")
            continue
        counted.add(key)
        qualifying += 1
    if qualifying < floor:
        errors.append(
            f"only {qualifying} cross-disciplinary 第貳部分 題組; require {floor} "
            "(CEEC declares exactly 2 合科 題組 in every official ROC 111-115 paper; the maintainer's wider reading finds 3-5)"
        )
    return errors, qualifying


def validate(exam: dict[str, Any], subject: str, exam_path: str = "") -> dict[str, Any]:
    """Reading-load and shared-stimulus floors for one authored exam record."""
    if subject not in SUBJECT_FLOORS:
        raise ValueError("no literacy floor for subject " + str(subject))
    floors = SUBJECT_FLOORS[subject]
    questions = [q for q in exam.get("questions") or [] if isinstance(q, dict)]
    errors: list[str] = []

    part_two = part_two_sections(exam)
    groups = build_groups(questions, part_two)

    # Printed student-facing volume. Each shared stimulus is counted once, the
    # way a candidate reads it.
    seen: set[str] = set()
    printed: list[str] = []
    for question in questions:
        stimulus = str(question.get("group_stimulus") or "").strip()
        if stimulus and stimulus not in seen:
            seen.add(stimulus)
            printed.append(stimulus)
        printed.append(question_text(question))
    body = "\n".join(printed)
    paper_chars = compact(body)
    paper_words = len(ASCII_WORD.findall(body))

    metrics: dict[str, Any] = {
        "paper_substantive_chars": paper_chars,
        "paper_english_words": paper_words,
        "question_count": len(questions),
        "group_count": len(groups),
        "part_1_groups": sum(1 for g in groups if g["part"] == 1),
        "part_2_groups": sum(1 for g in groups if g["part"] == 2),
        "part_1_grouped_items": sum(g["items"] for g in groups if g["part"] == 1),
    }

    if floors["unit"] == "words":
        if paper_words < floors["min_paper_words"]:
            errors.append(
                f"paper prints {paper_words} English words; floor is {floors['min_paper_words']} "
                f"(weakest official year {floors['official_weakest']})"
            )
    elif paper_chars < floors["min_paper_chars"]:
        errors.append(
            f"paper prints {paper_chars} substantive characters; floor is "
            f"{floors['min_paper_chars']} (weakest official year {floors['official_weakest']})"
        )

    if "min_total_groups" in floors and len(groups) < floors["min_total_groups"]:
        errors.append(f"{len(groups)} shared-stimulus 題組; require {floors['min_total_groups']}")
    if "min_part_1_groups" in floors and metrics["part_1_groups"] < floors["min_part_1_groups"]:
        errors.append(
            f"第壹部分 has {metrics['part_1_groups']} 題組; require {floors['min_part_1_groups']}. "
            "Standalone one-sentence items are not the current form."
        )
    if "min_part_1_grouped_items" in floors and metrics["part_1_grouped_items"] < floors["min_part_1_grouped_items"]:
        errors.append(
            f"第壹部分 題組 carry {metrics['part_1_grouped_items']} items; "
            f"require {floors['min_part_1_grouped_items']}"
        )
    if "min_part_2_groups" in floors and metrics["part_2_groups"] < floors["min_part_2_groups"]:
        errors.append(f"第貳部分 has {metrics['part_2_groups']} 題組; require {floors['min_part_2_groups']}")
    if "exact_part_2_groups" in floors and metrics["part_2_groups"] != floors["exact_part_2_groups"]:
        errors.append(
            f"第貳部分 has {metrics['part_2_groups']} 題組; the current form prints "
            f"exactly {floors['exact_part_2_groups']}"
        )

    def stimulus_check(rows: list[dict[str, Any]], label: str, median_floor: int) -> None:
        lengths = [row["stimulus_compact_chars"] for row in rows]
        if not lengths:
            return
        median = int(statistics.median(lengths))
        metrics[f"{label}_stimulus_median"] = median
        metrics[f"{label}_stimulus_min"] = min(lengths)
        if median < median_floor:
            errors.append(
                f"{label} 題組 stimulus median is {median} characters; floor is {median_floor}"
            )

    if "part_2_stimulus_median" in floors:
        part2 = [g for g in groups if g["part"] == 2]
        stimulus_check(part2, "part_2", floors["part_2_stimulus_median"])
        short = [g for g in part2 if g["stimulus_compact_chars"] < floors["short_stimulus_chars"]]
        metrics["part_2_short_groups"] = len(short)
        if len(short) > floors["max_short_part_2_groups"]:
            errors.append(
                f"{len(short)} 第貳部分 題組 print under {floors['short_stimulus_chars']} characters; "
                f"at most {floors['max_short_part_2_groups']} may"
            )
    if "part_1_stimulus_median" in floors:
        stimulus_check([g for g in groups if g["part"] == 1], "part_1", floors["part_1_stimulus_median"])
    if "group_stimulus_median" in floors:
        stimulus_check(groups, "all", floors["group_stimulus_median"])
        if "short_stimulus_chars" in floors:
            lengths = [g["stimulus_compact_chars"] for g in groups]
            if lengths:
                ratio = sum(x < floors["short_stimulus_chars"] for x in lengths) / len(lengths)
                metrics["short_stimulus_ratio"] = round(ratio, 3)
                if ratio > floors["max_short_stimulus_ratio"]:
                    errors.append(
                        f"{ratio:.0%} of 題組 print under {floors['short_stimulus_chars']} characters; "
                        f"at most {floors['max_short_stimulus_ratio']:.0%} may"
                    )

    if subject == "國寫":
        # Each 大題 supplies one reading packet that its subparts share, so count
        # distinct packets. Taking the two largest questions instead would let one
        # task's packet satisfy both floors.
        packets: dict[str, int] = {}
        for question in questions:
            text = str(question.get("group_stimulus") or "").strip()
            if not text:
                text = str(question.get("prompt") or "").strip()
            if text:
                packets[text] = compact(text)
        sizes = sorted(packets.values(), reverse=True)
        metrics["writing_packet_chars"] = sizes
        if len(sizes) < 2:
            errors.append(
                f"國寫 prints two 大題, each with its own reading packet; {len(sizes)} distinct packet(s) found"
            )
        else:
            longer, shorter = sizes[0], sizes[1]
            if longer < floors["min_task_1_chars"]:
                errors.append(
                    f"the longer 國寫 packet is {longer} characters; floor is "
                    f"{floors['min_task_1_chars']}"
                )
            if shorter < floors["min_task_2_chars"]:
                errors.append(
                    f"the shorter 國寫 packet is {shorter} characters; floor is "
                    f"{floors['min_task_2_chars']}"
                )

    if subject == "自然":
        cross_errors, qualifying = cross_discipline_errors(
            exam, groups, floors["min_cross_discipline_groups"]
        )
        metrics["cross_discipline_groups"] = qualifying
        errors.extend(cross_errors)

    report = {
        "status": "pass" if not errors else "fail",
        "subject": subject,
        "exam": exam_path,
        "reference": {
            "basis": "official 學測 ROC 111-115",
            "envelope": ENVELOPE.name,
            "cross_discipline_record": CROSS_DISCIPLINE.name,
        },
        "floors": floors,
        "metrics": metrics,
        "errors": errors,
        "note": (
            "A structural pass is not an editorial pass. A reviewer must still "
            "confirm that the declared linked operations, evidence bridges and "
            "cross-discipline dependencies exist in the printed material. Never "
            "pad prose or answer space to clear a floor."
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exam", type=Path)
    parser.add_argument("--subject", required=True, choices=tuple(SUBJECT_FLOORS))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam.read_text(encoding="utf-8-sig"))
    report = validate(exam, args.subject, str(args.exam))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
