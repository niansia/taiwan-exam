#!/usr/bin/env python3
"""Measure the ROC 111-115 reading load and shared-stimulus structure of every current-form subject.

`analyze_current_chinese_natural_form.py` measures page geometry for 國綜 and 自然.
This analyzer answers a different question: how much substantive material an
official paper actually prints, how much of it sits in shared 題組 stimulus
blocks, and — for 自然 — how often a mixed group spans more than one discipline.

Reviewer feedback on generated 國寫／國綜／社會／自然／英文 papers reported items
that were too short and too easy. The measured envelope produced here is the
evidence those release gates compare against; it is an anti-collapse floor, not
a writing target and not a licence to pad.

Official papers stay local (`.gitignore` keeps `歷屆試題/` out of Git), so this is
a maintainer tool. Its JSON output is the artifact that ships in the pack.

Usage:
    python scripts/analyze_current_form_literacy.py \
        --output exam_packs/學測/shared-data/current-form-literacy-envelope.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
from pathlib import Path
from typing import Any

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
SUBJECTS_ROOT = ROOT / "exam_packs" / "學測" / "subjects"
YEARS = (111, 112, 113, 114, 115)

WHITESPACE = re.compile(r"\s+")
CJK = re.compile(r"[一-鿿]")
ASCII_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
GROUP_HEADER = re.compile(r"(?:第\s*)?(\d+)\s*[-–~～至]\s*(\d+)\s*(?:題)?為題組")
PART_TWO = re.compile(r"第貳部分")
# A 說明 block runs from its marker to the next numbered item, part heading or
# 大題 marker. Directions and the cover are printed by the Layout Profile, not
# authored in the exam record, so a gate reading exam.json never sees them.
DIRECTION = re.compile(
    r"說明：.*?(?=\n\s*\d+\s*[.．]|\n\s*第[壹貳]部分|\n\s*[一二三四五六]、|\Z)", re.S
)

# Running headers, footers and the signature banner repeat on every page and are
# not material a candidate has to read.
FURNITURE = re.compile(
    r"(請記得在答題卷簽名欄位|^第\s*\d+\s*頁|^共\s*\d+\s*頁|^\d+\s*年學測|"
    r"^(?:自然|社會|英文|國語文綜合能力測驗|國語文寫作能力測驗)考?科?\s*$|^-\s*[　\s]*\d*[　\s]*-\s*$)"
)

# Each subject's question booklet, by the folder its intake pack uses and the
# filename patterns CEEC has published across 111-115.
PAPERS: dict[str, dict[str, Any]] = {
    "國綜": {"folder": "國文", "include": ("國綜",), "exclude": ("答案", "評分", "國寫")},
    "國寫": {"folder": "國文", "include": ("國寫",), "exclude": ("答案", "評分")},
    "英文": {"folder": "英文", "include": ("英文",), "exclude": ("答案", "評分")},
    "社會": {"folder": "社會", "include": ("社會",), "exclude": ("答案", "評分")},
    "自然": {"folder": "自然", "include": ("自然",), "exclude": ("答案", "評分")},
}

# The 英文 booklet's section order has been stable across 111-115. Word budgets
# per section are far more actionable than one paper-level total.
# 中譯英 and 英文作文 print Chinese directions rather than English prose, so an
# English word band for them would measure nothing; they are covered by the
# separate task contract in references/current-gsat-english-form.md.
# Each band counts every English word printed in the section, directions and
# options included, so it is a section budget rather than a passage length.
ENGLISH_SECTIONS = (
    ("詞彙題", re.compile(r"一、\s*詞彙題")),
    ("綜合測驗", re.compile(r"二、\s*綜合測驗")),
    ("文意選填", re.compile(r"三、\s*文意選填")),
    ("篇章結構", re.compile(r"四、\s*篇章結構")),
    ("閱讀測驗", re.compile(r"五、\s*閱讀測驗")),
    ("混合題", re.compile(r"混合題")),
)


def compact(text: str) -> int:
    return len(WHITESPACE.sub("", text))


def find_paper(subject: str, year: int) -> Path | None:
    spec = PAPERS[subject]
    folder = SUBJECTS_ROOT / spec["folder"] / "歷屆試題" / str(year)
    if not folder.is_dir():
        return None
    candidates = []
    for path in sorted(folder.glob("*.pdf")):
        name = path.name
        if any(token in name for token in spec["exclude"]):
            continue
        if not any(token in name for token in spec["include"]):
            continue
        candidates.append(path)
    if not candidates:
        return None
    # A year occasionally ships both a 試卷 and a 定稿; either is the same paper.
    # Prefer the longest booklet so an answer-only stub can never win.
    return max(candidates, key=lambda path: pymupdf.open(path).page_count)


def strip_furniture(raw: str) -> str:
    return "\n".join(line for line in raw.split("\n") if not FURNITURE.search(line.strip()))


def booklet_text(path: Path) -> tuple[int, str]:
    doc = pymupdf.open(path)
    raw = "\n".join(page.get_text("text") or "" for page in doc)
    return doc.page_count, strip_furniture(raw)


def item_content_text(path: Path) -> str:
    """What a gate reading the authored exam record can actually measure.

    Drops the cover page and the section 說明 blocks, which the Layout Profile
    prints rather than the item writer. A floor compared against the full
    booklet would demand prose the exam record never contains — for 國寫 that
    alone is the difference between 1,528 and 1,240 characters, enough to
    reject a paper shaped exactly like ROC 111.
    """
    doc = pymupdf.open(path)
    body = strip_furniture("\n".join(page.get_text("text") or "" for page in list(doc)[1:]))
    return DIRECTION.sub("", body)


def group_records(text: str) -> list[dict[str, Any]]:
    """Shared-stimulus blocks, with the prose a candidate must read before item one."""
    part_two = text.find("第貳部分")
    marks = [
        (m.start(), int(m.group(1)), int(m.group(2)), m.end())
        for m in GROUP_HEADER.finditer(text)
    ]
    rows = []
    for index, (start, first, last, header_end) in enumerate(marks):
        following = marks[index + 1][0] if index + 1 < len(marks) else len(text)
        segment = text[header_end:following]
        # The stimulus runs from the group header to the first numbered item.
        opener = re.search(r"(?m)^\s*" + str(first) + r"\s*[.．]", segment)
        stimulus = segment[: opener.start()] if opener else segment
        rows.append(
            {
                "group": f"{first}-{last}",
                "items": last - first + 1,
                "stimulus_compact_chars": compact(stimulus),
                "part": 2 if (part_two >= 0 and start > part_two) else 1,
            }
        )
    return rows


def english_sections(text: str) -> dict[str, int]:
    marks = []
    for name, pattern in ENGLISH_SECTIONS:
        match = pattern.search(text)
        if match:
            marks.append((match.start(), name))
    marks.sort()
    out = {}
    for index, (start, name) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(text)
        out[name] = len(ASCII_WORD.findall(text[start:end]))
    return out


def writing_tasks(text: str) -> dict[str, int]:
    """國寫 prints two 大題; each supplies its own reading packet."""
    first = text.find("一、")
    second = text.find("二、", first + 1 if first >= 0 else 0)
    if first < 0 or second < 0:
        return {}
    return {
        "task_1_compact_chars": compact(text[first:second]),
        "task_2_compact_chars": compact(text[second:]),
    }


def spread(values: list[int]) -> dict[str, Any]:
    if not values:
        return {}
    return {
        "count": len(values),
        "min": min(values),
        "median": int(statistics.median(values)),
        "max": max(values),
    }


def measure(subject: str) -> dict[str, Any]:
    papers = []
    part1_stimuli: list[int] = []
    part2_stimuli: list[int] = []
    for year in YEARS:
        path = find_paper(subject, year)
        if path is None:
            continue
        pages, text = booklet_text(path)
        record: dict[str, Any] = {
            "roc_year": year,
            "page_count": pages,
            "substantive_compact_chars": compact(text),
            "cjk_chars": len(CJK.findall(text)),
            "english_words": len(ASCII_WORD.findall(text)),
        }
        content = item_content_text(path)
        record["item_content_compact_chars"] = compact(content)
        record["item_content_english_words"] = len(ASCII_WORD.findall(content))
        groups = group_records(text)
        if groups:
            part1 = [g for g in groups if g["part"] == 1]
            part2 = [g for g in groups if g["part"] == 2]
            part1_stimuli.extend(g["stimulus_compact_chars"] for g in part1)
            part2_stimuli.extend(g["stimulus_compact_chars"] for g in part2)
            record["groups"] = {
                "total": len(groups),
                "part_1_groups": len(part1),
                "part_1_grouped_items": sum(g["items"] for g in part1),
                "part_2_groups": len(part2),
                "part_2_grouped_items": sum(g["items"] for g in part2),
            }
        if subject == "英文":
            record["section_total_english_words"] = english_sections(text)
        if subject == "國寫":
            record.update(writing_tasks(text))
        papers.append(record)
    out: dict[str, Any] = {"subject": subject, "papers": papers}
    totals = [p["substantive_compact_chars"] for p in papers]
    if totals:
        out["paper_substantive_chars"] = spread(totals)
        out["paper_item_content_chars"] = spread([p["item_content_compact_chars"] for p in papers])
        out["paper_item_content_words"] = spread([p["item_content_english_words"] for p in papers])
    if part1_stimuli:
        out["part_1_group_stimulus_chars"] = spread(part1_stimuli)
    if part2_stimuli:
        out["part_2_group_stimulus_chars"] = spread(part2_stimuli)
    if subject == "英文":
        names = [name for name, _ in ENGLISH_SECTIONS]
        out["section_total_english_word_bands"] = {
            name: spread([
                p["section_total_english_words"][name]
                for p in papers
                if name in p.get("section_total_english_words", {})
            ])
            for name in names
        }
        out["section_band_note"] = (
            "Total English words printed in the section, including directions, "
            "item stems and options. Not passage prose alone: the per-passage "
            "prose bands live in references/current-gsat-english-form.md."
        )
        out["paper_english_words"] = spread([p["english_words"] for p in papers])
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "exam_packs" / "學測" / "shared-data" / "current-form-literacy-envelope.json",
    )
    args = parser.parse_args()

    subjects = [measure(name) for name in PAPERS]
    missing = [s["subject"] for s in subjects if len(s["papers"]) < len(YEARS)]
    payload = {
        "schema_version": 1,
        "basis": (
            "Direct text measurement of the supplied CEEC 學測 ROC 111-115 question "
            "booklets, running headers/footers and the signature banner removed. "
            "Reading-load floors only; not a verified Layout Profile and not an "
            "official difficulty statistic."
        ),
        "field_note": (
            "substantive_compact_chars excludes repeated page furniture and is "
            "therefore lower than the whole-PDF compact_chars in "
            "current-chinese-natural-density.json. item_content_compact_chars "
            "additionally excludes the cover page and the section 說明 blocks, and "
            "is the basis a gate reading the authored exam record must use. The "
            "three are not interchangeable."
        ),
        "measured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "roc_years": list(YEARS),
        "incomplete_subjects": missing,
        "usage": (
            "An anti-collapse floor for release gates. Never pad prose, inflate "
            "answer space or duplicate material to reach these numbers."
        ),
        "subjects": subjects,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n" keeps the shipped asset byte-identical on Windows, where the
    # repo's .gitattributes disables newline conversion.
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"output": str(args.output), "incomplete_subjects": missing}, ensure_ascii=False))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
