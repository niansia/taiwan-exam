#!/usr/bin/env python3
"""Validate release-blocking structure for the verified 115 GSAT English form."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def validate_exam(exam: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    meta = exam.get("metadata") or {}
    if (meta.get("paper_subject") or meta.get("subject")) != "英文":
        return errors
    sections = {section.get("id"): section for section in exam.get("sections") or []}
    vocabulary_title = str((sections.get("vocabulary") or {}).get("title") or "")
    if "占62分" not in vocabulary_title.replace(" ", ""):
        errors.append("115英文第壹部分必須標示占62分")
    if "62分" not in str(meta.get("scoring_note") or ""):
        errors.append("英文封面計分方式須標示第壹部分62分")
    if (meta.get("section_header_previews") or {}).get("2") != "cloze":
        errors.append("115英文第2頁末須預置綜合測驗標題與說明")

    by_number = {int(q.get("number")): q for q in exam.get("questions") or [] if isinstance(q.get("number"), int)}
    for number in range(1, 21):
        if (by_number.get(number) or {}).get("option_layout") != "row-4":
            errors.append(f"英文第{number}題四個短選項須使用同列row-4版型")
    for number in range(35, 49):
        question = by_number.get(number) or {}
        if question.get("options") and question.get("option_layout") != "stack":
            errors.append(f"英文第{number}題閱讀或混合題選項須逐項直排")
    for number in range(11, 35):
        question = by_number.get(number) or {}
        if question.get("suppress_question_display") is not True:
            errors.append(f"英文第{number}題不得另印工作紙式獨立空格列")
        stimulus = str(question.get("group_stimulus") or "")
        if f"[[{number}]]" not in stimulus:
            errors.append(f"英文第{number}題缺少文章內編號底線空格")
        if "Blank (" in str(question.get("prompt") or "") or "Choose the best answer for blank" in str(question.get("prompt") or ""):
            errors.append(f"英文第{number}題仍含重複空格提示")

    completion = str((by_number.get(21) or {}).get("group_stimulus") or "")
    if "(J)" not in completion or "(K)" in completion or "(L)" in completion:
        errors.append("115英文文意選填須為十空、十個A至J選項")
    if not all((by_number.get(number) or {}).get("page") == 3 for number in range(11, 21)):
        errors.append("115英文兩組綜合測驗須依量測版型同置第3頁")

    # Empirical guardrails from the 111–115 official papers.  Count prose only,
    # excluding the option bank appended to inline-layout stimuli.
    word_re = re.compile(r"[A-Za-z]+(?:[-'’][A-Za-z]+)*")

    def prose_word_count(number: int) -> int:
        question = by_number.get(number) or {}
        stimulus = str(question.get("group_stimulus") or "")
        if number in {11, 16}:
            stimulus = re.split(rf"\n\s*\n\s*{number}\.", stimulus, maxsplit=1)[0]
        elif number in {21, 31}:
            stimulus = re.split(r"\n\s*\n\s*\(A\)", stimulus, maxsplit=1)[0]
        return len(word_re.findall(stimulus))

    length_contracts = {
        11: (175, 235, "第11至15題綜合測驗"),
        16: (175, 235, "第16至20題綜合測驗"),
        21: (265, 325, "文意選填"),
        31: (250, 315, "篇章結構"),
        35: (320, 390, "第35至38題閱讀"),
        39: (320, 390, "第39至42題閱讀"),
        43: (320, 390, "第43至46題閱讀"),
        47: (340, 460, "混合題材料"),
    }
    for number, (minimum, maximum, label) in length_contracts.items():
        count = prose_word_count(number)
        if count < minimum or count > maximum:
            errors.append(f"{label}正文{count}字，不在111–115實卷基準{minimum}–{maximum}字內")

    mixed = by_number.get(47) or {}
    page_splits = mixed.get("group_stimulus_page_splits") or {}
    if set(page_splits) != {"10", "11"} or "".join(page_splits.values()).strip() == "":
        errors.append("英文混合題長材料須跨第9至10題本頁分段配置，避免單頁擁塞或次頁大片留白")
    if not mixed.get("visual_asset"):
        errors.append("115英文混合題首段須配置可讀的非連續文本或視覺證據，避免材料頁大面積留白")

    for question in exam.get("questions") or []:
        if not question.get("visual_asset"):
            continue
        visible = f'{question.get("group_stimulus") or ""}\n{question.get("prompt") or ""}'
        if "照片：" in visible or "Photo:" in visible:
            errors.append(f"英文第{question.get('number')}題把照片權利資訊印入學生卷")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exam_json", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam_json.read_text(encoding="utf-8-sig"))
    errors = validate_exam(exam)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: verified 115 English layout contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
