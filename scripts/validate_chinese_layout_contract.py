#!/usr/bin/env python3
"""Printed-form contract of the current GSAT 國綜 paper, measured on ROC 111-115.

The item-by-item reading in exam_packs/學測/shared-data/chinese-item-type-envelope.json
holds in every year: item 1 is 字音, item 2 is 字形, items 1-5 stand alone, the
shared-stimulus groups start at item 6 or later, the first multiple-choice item
is 文言字義, multiple-choice items 25-29 stand alone and 30-31 form one group,
no multiple-choice stem prints （應選n項）, every year has a 成語／詞語運用 item,
a 語法 item, a ①②研判題 and a 古典韻文 item, and 第貳部分 is one group 32-36
with two 2-point single-choice subparts and three constructed items whose
2-point subparts allow 10-20 characters and 4-point subparts 30-40. Options are
(A)-(E), one per line, under four headings with scores. A hosted paper reviewed
on 2026-09-22 broke each of these; this module names them.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

OFFICIAL_HEADINGS = (
    "第壹部分、選擇題（占76分）", "一、單選題（占48分）", "二、多選題（占28分）",
    "第貳部分、混合題或非選擇題（占24分）",
)
LANGUAGE_KNOWLEDGE = re.compile(r"「」內|畫底線|詞語|成語|用法|用來修飾|文學|寫作特色|音節|平仄|押韻|字音|字形|讀音|錯別字|排列順序|填入|稱謂|量詞")
IDIOM = re.compile(r"成語|畫底線(?:處)?的詞語")
GRAMMAR = re.compile(r"用法|用來修飾|「以」|「則」|量詞|條件|語意邏輯|平仄|音節|押韻")
JUDGEMENT = re.compile(r"①.*②")
CLASSICAL_VERSE = re.compile(r"詩|詞|曲|韻文|絕句|律詩|樂府")
CHAR_LIMIT = re.compile(r"(\d+)\s*字以內")


def validate_exam(exam: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    meta = exam.get("metadata") or {}
    if (meta.get("paper_subject") or meta.get("subject")) != "國綜":
        return errors
    questions = [q for q in exam.get("questions") or [] if isinstance(q, dict)]
    by_number: dict[int, list[dict]] = {}
    for question in questions:
        if isinstance(question.get("number"), int):
            by_number.setdefault(question["number"], []).append(question)

    printed_titles = "".join(str(section.get("title") or "") for section in exam.get("sections") or [])
    printed_titles = re.sub(r"\s+", "", printed_titles).replace("(", "（").replace(")", "）")
    cursor = 0
    for heading in OFFICIAL_HEADINGS:
        index = printed_titles.find(heading, cursor)
        if index < 0:
            errors.append(f"國綜題本須依官方順序印出標題「{heading}」（111–115 每年皆同）")
        else:
            cursor = index + len(heading)

    def first(number: int) -> dict:
        return (by_number.get(number) or [{}])[0]

    def prompt(number: int) -> str:
        return " ".join(str(q.get("prompt") or "") for q in by_number.get(number) or [])

    def stimulus(number: int) -> str:
        return str(first(number).get("group_stimulus") or "").strip()

    shared: dict[str, list[int]] = {}
    for question in questions:
        text = str(question.get("group_stimulus") or "").strip()
        if text and isinstance(question.get("number"), int):
            shared.setdefault(text, []).append(question["number"])
    groups = {text: sorted(set(numbers)) for text, numbers in shared.items() if len(set(numbers)) > 1}

    if first(1) and "讀音" not in prompt(1):
        errors.append("國綜第1題須為字音題（下列「」內的字，讀音前後相同的是），111–115 每年皆同")
    if first(2) and "錯別字" not in prompt(2):
        errors.append("國綜第2題須為字形題（下列文句，完全沒有錯別字的是），111–115 每年皆同")
    for number in range(1, 6):
        if first(number) and stimulus(number) and stimulus(number) in groups:
            errors.append(f"國綜第{number}題須為獨立語文知識或短文題，不得與其他題共用題組材料（題組自第6題起）")
    if first(3) and not any(LANGUAGE_KNOWLEDGE.search(prompt(n)) for n in (3, 4, 5)):
        errors.append("國綜第3至5題中至少一題須為詞語運用、填詞、稱謂或文言排序等語文知識題")
    single_groups = [numbers for numbers in groups.values() if numbers and numbers[-1] <= 24]
    for numbers in single_groups:
        if not 2 <= len(numbers) <= 5:
            errors.append(f"國綜單選題組第{numbers[0]}至{numbers[-1]}題有{len(numbers)}題；官方題組為2至3題（最多5題）")
    if any(n >= 20 for n in by_number) and len(single_groups) < 6:
        errors.append(f"國綜第6至24題須為6至8個共用材料題組（每組2至3題）；現有{len(single_groups)}組")

    for number in range(1, 32):
        question = first(number)
        labels = [str(o.get("label") or "").strip("()（）") for o in question.get("options") or [] if isinstance(o, dict)]
        if labels and labels != list("ABCDE")[: len(labels)]:
            errors.append(f"國綜第{number}題選項標記須為(A)(B)(C)(D)，不是{labels}")
        if question.get("options") and question.get("option_layout") not in (None, "stack"):
            errors.append(f"國綜第{number}題選項須逐項直排（官方每個選項自成一行），不得用多欄版型")
    multiple = [n for n in range(25, 32) if first(n)]
    if first(25) and not ("「」內的詞" in prompt(25) and "意義" in prompt(25)):
        errors.append("國綜第25題（多選第一題）須為文言字義題「下列各組「」內的詞，意義前後相同的是」，選項取自核心古文，111–115 每年皆同")
    for number in multiple:
        question = first(number)
        if question.get("type") != "multiple_choice":
            errors.append(f"國綜第{number}題須為多選題")
        if "應選" in prompt(number):
            errors.append(f"國綜第{number}題不得印「應選n項」；國綜多選題不預告正確選項數")
        if number <= 29 and stimulus(number) and stimulus(number) in groups:
            errors.append(f"國綜第{number}題須為獨立多選題（第25至29題各有自己的材料，只有第30至31題成組）")
    if first(30) and first(31) and (not stimulus(30) or stimulus(30) != stimulus(31)):
        errors.append("國綜第30至31題須為一個共用材料的兩題題組（含文言或韻文），111–115 每年皆同")
    knowledge = sum(1 for n in multiple if LANGUAGE_KNOWLEDGE.search(prompt(n)))
    if multiple and knowledge < 2:
        errors.append(f"國綜多選題須有至少2題語文知識題（文言字義、成語運用、語法、文學常識）；現有{knowledge}題")

    all_prompts = [prompt(n) for n in sorted(by_number)]
    all_text = "\n".join(all_prompts + [str(q.get("group_stimulus") or "") for q in questions])
    if len(by_number) >= 30:
        if not any(IDIOM.search(p) for p in all_prompts):
            errors.append("國綜每年有一題成語／畫底線詞語運用題（113–115 在多選第25至26題）；本卷沒有")
        if not any(GRAMMAR.search(p) for p in all_prompts):
            errors.append("國綜每年至少一題語法或虛詞題（「以」「則」用法、程度副詞、量詞、條件句）；本卷沒有")
        if not any(JUDGEMENT.search(p) for p in all_prompts):
            errors.append("國綜每年至少一題①②研判題（皆符合／皆不符合／①符合②不符合／無法判斷）；本卷沒有")
        if not any(CLASSICAL_VERSE.search(p) for p in all_prompts) and not CLASSICAL_VERSE.search(all_text):
            errors.append("國綜每年至少一題古典詩詞曲材料；本卷沒有")

    part_two = sorted(n for n in by_number if n >= 32)
    if part_two:
        if part_two[0] != 32 or part_two[-1] not in (36, 37):
            errors.append(f"國綜第貳部分為第32至36題一個題組；現有題號 {part_two}")
        singles = [q for n in part_two for q in by_number[n] if q.get("type") == "single_choice"]
        constructed = [q for n in part_two for q in by_number[n] if q.get("type") == "constructed_response"]
        if len(singles) != 2:
            errors.append(f"國綜第貳部分須有恰好2題單選子題（各2分）；現有{len(singles)}題")
        for q in singles:
            if q.get("score") not in (None, 2):
                errors.append(f"國綜第貳部分第{q.get('number')}題單選子題配分須為2分")
        if len({q.get("number") for q in constructed}) < 3:
            errors.append(f"國綜第貳部分須有3題非選（每題含(1)(2)兩小題）；現有{len({q.get('number') for q in constructed})}題")
        for q in constructed:
            score = q.get("score")
            limits = [int(v) for v in CHAR_LIMIT.findall(str(q.get("prompt") or ""))]
            if score == 2 and limits and max(limits) > 20:
                errors.append(f"國綜第{q.get('number')}題2分小題字數上限須為10至20字；印出{max(limits)}字以內")
            if score == 4 and limits and max(limits) > 40:
                errors.append(f"國綜第{q.get('number')}題4分小題字數上限須為30至40字；印出{max(limits)}字以內")
            if score not in (None, 2, 4) and score is not None and score > 4:
                errors.append(f"國綜第{q.get('number')}題非選小題配分須為2分或4分；現有{score}分")
        stimuli = {stimulus(n) for n in part_two}
        if len(stimuli) != 1 or "" in stimuli:
            errors.append("國綜第貳部分五題須共用同一組多文本材料（甲乙丙，含文言或韻文）")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exam_json", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam_json.read_text(encoding="utf-8-sig"))
    errors = validate_exam(exam)
    report = {"status": "fail" if errors else "pass", "errors": errors}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
