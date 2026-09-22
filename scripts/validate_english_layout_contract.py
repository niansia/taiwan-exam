#!/usr/bin/env python3
"""Validate release-blocking structure for the verified 115 GSAT English form."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


WORD = re.compile(r"[A-Za-z]+(?:[-'’][A-Za-z]+)*")
VOCABULARY_STEM_WORDS = (12, 26)          # official 111–115: 13–24
TRANSLATION_SENTENCE_CJK = (16, 32)       # official 111–115: 18–28
COMPOSITION_PROMPT_CJK_MAX = 220          # official 111–115: 108–174
READING_DETAIL_MAX = 4                    # official 111–115: 2–4 true/NOT detail checks
REFERENCE_STEM = re.compile(r"refer to|refers to|closest in meaning|mean by|is used .{0,30}to refer|idiom|which words? .{0,20}(?:used|refer)", re.I)
GLOBAL_STEM = re.compile(r"mainly about|main purpose|purpose of|what question|can we learn|be inferred|inferred|how does the author|conclude|develop the ideas|best title|field of study", re.I)
DETAIL_STEM = re.compile(r"\b(?:is|are) (?:true|NOT|not)\b|\bNOT\b", re.I)
OFFICIAL_HEADINGS = (
    "第壹部分、選擇題（占62分）", "一、詞彙題（占10分）", "二、綜合測驗（占10分）", "三、文意選填（占10分）",
    "四、篇章結構（占8分）", "五、閱讀測驗（占24分）", "第貳部分、混合題（占10分）",
    "第參部分、非選擇題（占28分）", "一、中譯英（占8分）", "二、英文作文（占20分）",
)


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

    # The printed part/section headings of every official 111-115 paper, in order.
    printed_titles = "".join(str(section.get("title") or "") for section in exam.get("sections") or [])
    printed_titles = re.sub(r"\s+", "", printed_titles).replace("(", "（").replace(")", "）")
    cursor = 0
    for heading in OFFICIAL_HEADINGS:
        index = printed_titles.find(heading, cursor)
        if index < 0:
            errors.append(f"英文題本須依官方順序印出標題「{heading}」（111–115 每年皆同）")
        else:
            cursor = index + len(heading)

    by_number = {int(q.get("number")): q for q in exam.get("questions") or [] if isinstance(q.get("number"), int)}
    word_re = WORD
    for number in range(1, 47):
        question = by_number.get(number) or {}
        labels = [str(o.get("label") or "").strip("()（）") for o in question.get("options") or [] if isinstance(o, dict)]
        if labels and labels != list("ABCD")[: len(labels)] and not (number in range(31, 35) and labels == list("ABCDE")):
            errors.append(f"英文第{number}題選項標記須為(A)(B)(C)(D)，不是{labels}")
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
    discourse = str((by_number.get(31) or {}).get("group_stimulus") or "")
    if discourse and ("(D)" not in discourse or "(F)" in discourse):
        errors.append("英文篇章結構須為四空配四或五個候選句(A)–(D)／(A)–(E)（111–114 四句、115 五句）")
    for number in range(1, 11):
        stem = str((by_number.get(number) or {}).get("prompt") or "")
        words = len(word_re.findall(stem))
        if stem and not VOCABULARY_STEM_WORDS[0] <= words <= VOCABULARY_STEM_WORDS[1]:
            errors.append(f"英文第{number}題詞彙題幹 {words} 個單詞，官方 111–115 為 13–24 個（允許 {VOCABULARY_STEM_WORDS[0]}–{VOCABULARY_STEM_WORDS[1]}）")
    errors.extend(reading_stem_errors(by_number))
    errors.extend(mixed_section_errors(by_number))
    if not all((by_number.get(number) or {}).get("page") == 3 for number in range(11, 21)):
        errors.append("115英文兩組綜合測驗須依量測版型同置第3頁")

    # Empirical guardrails from the 111–115 official papers.  Count prose only,
    # excluding the option bank appended to inline-layout stimuli.
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
        31: (220, 315, "篇章結構"),
        35: (285, 390, "第35至38題閱讀"),
        39: (285, 390, "第39至42題閱讀"),
        43: (285, 390, "第43至46題閱讀"),
        47: (340, 480, "混合題材料"),
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

    composition = next(
        (
            question for question in exam.get("questions") or []
            if question.get("section_id") == "composition" or question.get("type") == "guided_writing"
        ),
        None,
    )
    if not composition:
        errors.append("115英文完整卷缺英文作文")
    else:
        prompt = str(composition.get("prompt") or "")
        cjk_count = len(re.findall(r"[\u3400-\u9fff]", prompt))
        latin_word_count = len(re.findall(r"[A-Za-z]+(?:[-'’][A-Za-z]+)*", prompt))
        if cjk_count < 30:
            errors.append("英文作文的學生作答提示必須以中文完整書寫")
        if cjk_count and latin_word_count > max(20, cjk_count):
            errors.append("英文作文題幹的英文指令過多，作答說明應以中文為主")
        if "120" not in prompt or "單詞" not in prompt or "英文" not in prompt:
            errors.append("英文作文題幹須以中文明示英文作文與至少120個單詞")
        if "提示" not in prompt or "第一段" not in prompt or "第二段" not in prompt:
            errors.append("英文作文題幹須依官方格式以中文寫出「提示：…」並指明第一段與第二段的任務")
        if re.match(r"\s*[A-Za-z]", prompt):
            errors.append("英文作文題幹以英文句子開頭；官方提示全文為中文，只有主題詞可附英文")
        if cjk_count > COMPOSITION_PROMPT_CJK_MAX:
            errors.append(f"英文作文提示 {cjk_count} 字，官方 111–115 為 108–174 字；提示不是作文範本")
        if not composition.get("visual_asset"):
            errors.append("英文作文須附圖片（官方 111–115 每年皆為看圖寫作：兩張圖、表情符號、三張圖、對比圖、多張圖）")
        spec = composition.get("item_spec") if isinstance(composition.get("item_spec"), dict) else {}
        contract = spec.get("composition_contract") if isinstance(spec.get("composition_contract"), dict) else {}
        if contract.get("directions_language") != "zh-TW":
            errors.append("英文作文 composition_contract 必須標示 directions_language=zh-TW")
        if int(contract.get("minimum_words") or 0) != 120:
            errors.append("英文作文 composition_contract 必須記錄 minimum_words=120")
        if contract.get("student_accessible_context") is not True:
            errors.append("英文作文情境必須在高中生日常生活或學習範疇內")
        review = contract.get("prompt_coherence_review") if isinstance(contract.get("prompt_coherence_review"), dict) else {}
        if review.get("status") != "pass":
            errors.append("英文作文未通過題意連貫與自然性審查")
        if review.get("forced_moral_or_abstract_jump") is not False:
            errors.append("英文作文不得從圖片觀察硬跳到無關的抽象教訓")
        if review.get("multiple_valid_angles") is not True:
            errors.append("英文作文須容許多種合理取徑，不能暗藏單一標準故事")
        if not str(review.get("task_bridge") or "").strip():
            errors.append("英文作文兩段任務的語意橋接未說明")
        if composition.get("visual_asset") and review.get("visible_evidence_boundary") is not True:
            errors.append("看圖作文必須限定圖像可見證據，不得要求學生編造圖中不存在的細節")

    for question in exam.get("questions") or []:
        if not question.get("visual_asset"):
            continue
        visible = f'{question.get("group_stimulus") or ""}\n{question.get("prompt") or ""}'
        if "照片：" in visible or "Photo:" in visible:
            errors.append(f"英文第{question.get('number')}題把照片權利資訊印入學生卷")
    translations = [q for q in exam.get("questions") or []
                    if q.get("section_id") == "translation" or "中譯英" in str(sections.get(q.get("section_id"), {}).get("title") or "")]
    for index, question in enumerate(translations, 1):
        label = re.sub(r"\s+", "", str(question.get("number_display") or question.get("answer_label") or ""))
        if label not in {f"{index}.", str(index), f"{index}．"}:
            errors.append(f"中譯英第{index}句須印為「{index}.」，不是「{label or '（無）'}」；「中譯英1」不是官方題號")
        if re.search(r"[A-Za-z]{3,}", str(question.get("prompt") or "")):
            errors.append(f"中譯英第{index}句題幹須為中文句子")
        cjk = len(re.findall(r"[\u3400-\u9fff]", str(question.get("prompt") or "")))
        if not TRANSLATION_SENTENCE_CJK[0] <= cjk <= TRANSLATION_SENTENCE_CJK[1]:
            errors.append(f"中譯英第{index}句 {cjk} 字，官方 111–115 每句 18–28 字（允許 {TRANSLATION_SENTENCE_CJK[0]}–{TRANSLATION_SENTENCE_CJK[1]}）")
    return errors


def reading_stem_errors(by_number: dict[int, dict]) -> list[str]:
    """閱讀測驗 35–46 stem mix measured on 111–115: 2–4 word/reference-in-context items,
    at least one global item (main idea, purpose, inference, author's method) and never
    more than four 'which statement is true / NOT' detail checks per booklet."""
    stems = {n: str((by_number.get(n) or {}).get("prompt") or "") for n in range(35, 47)}
    if not all(stems.values()):
        return []
    reference = [n for n, s in stems.items() if REFERENCE_STEM.search(s)]
    global_items = [n for n, s in stems.items() if GLOBAL_STEM.search(s)]
    detail = [n for n, s in stems.items() if DETAIL_STEM.search(s)]
    errors = []
    if len(reference) < 2:
        errors.append(f"英文閱讀測驗須有至少 2 題字詞／指涉題（refer to、closest in meaning、mean by），目前 {len(reference)} 題；官方 111–115 每年 2–4 題")
    if not global_items:
        errors.append("英文閱讀測驗須有至少 1 題全文題（mainly about、purpose、what can we learn、inferred、how does the author）；官方 111–115 每年皆有")
    if len(detail) > READING_DETAIL_MAX:
        errors.append(f"英文閱讀測驗 {len(detail)} 題為「which is true／NOT」細節核對題（{detail}），官方 111–115 每年最多 4 題")
    return errors


def mixed_section_errors(by_number: dict[int, dict]) -> list[str]:
    """混合題 47–50, identical in 111–115: a 4-point word-fill or short-answer pair (47–48),
    one 4-point 多選 and one 2-point 簡答; never a 單選."""
    items = {n: by_number.get(n) for n in range(47, 51)}
    if any(q is None for q in items.values()):
        return []
    errors = []
    types = {n: str(q.get("type") or "") for n, q in items.items()}
    if any(t == "single_choice" for t in types.values()):
        errors.append("英文混合題 47–50 不得有單選題；官方 111–115 為填充／簡答（4分）、多選（4分）、簡答（2分）")
    multiples = [n for n, t in types.items() if t == "multiple_choice"]
    if len(multiples) != 1:
        errors.append(f"英文混合題須恰有 1 題多選題（4分），目前 {len(multiples)} 題")
    scores = {n: q.get("score") for n, q in items.items()}
    if all(isinstance(s, (int, float)) for s in scores.values()):
        if sum(scores.values()) != 10:
            errors.append(f"英文混合題配分須合計 10 分，目前 {scores}")
        if multiples and scores.get(multiples[0]) != 4:
            errors.append("英文混合題的多選題須為 4 分")
        if 2 not in scores.values():
            errors.append("英文混合題須有一題 2 分簡答題（官方 111–115 每年為第50題）")
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
