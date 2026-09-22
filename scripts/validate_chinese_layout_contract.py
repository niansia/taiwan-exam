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
# Official 字音 options: two DIFFERENT characters that share a component, each
# quoted inside a classical four-character phrase, the halves joined by ／
# (111 痺／髀, 112 笳／袈, 113 闥／撻, 114 舁／臾, 115 攲／旖). One character with two
# readings (「屬」／「屬」) is a different exercise and never the official item 1.
QUOTED_CHARACTER = re.compile(r"「([^「」]+)」")
# Official 詞語填空 (111 Q6 杜甫 two poems, 112 Q6 〈補江總白猿傳〉, 114 Q3 聶華苓): the
# passage is a printed excerpt of a real work with its attribution, □ slots of two
# to four characters, and the four options are built from exactly two candidate
# words per slot so that any two options differ in at least two slots. A self-
# written sentence with four unrelated words per slot is eliminated slot by slot.
BLANK_RUN = re.compile(r"□+")
SOURCE_ATTRIBUTION = re.compile(r"[（(][^（）()]*(?:〈[^〈〉]+〉|《[^《》]+》|改寫自)[^（）()]*[）)]")
# Measured on the 111-115 booklets: options up to 19 printed characters including
# the (A) label share a row two abreast (152 such lines); longer options and every
# five-option item print one per line.
TWO_COLUMN_MAX_CHARACTERS = 16
LANGUAGE_KNOWLEDGE = re.compile(r"「」內|畫底線|詞語|成語|用法|用來修飾|文學|寫作特色|音節|平仄|押韻|字音|字形|讀音|錯別字|排列順序|填入|稱謂|量詞")
IDIOM = re.compile(r"成語|畫底線(?:處)?的詞語")
GRAMMAR = re.compile(r"用法|用來修飾|「以」|「則」|量詞|條件|語意邏輯|平仄|音節|押韻")
JUDGEMENT = re.compile(r"①.*②")
# The official ①②研判題 is a single-choice item whose four options are drawn from
# 皆符合／皆不符合／①符合，②不符合／①不符合，②無法判斷 (111 Q16, 113 Q12, 114 Q24,
# 115 Q7 and Q12); a multiple-choice item whose options are pairs of statements is
# a different, easier exercise.
JUDGEMENT_OPTION = re.compile(r"皆(?:符合|不符合|適當|不適當)|①(?:符合|不符合|適當|不適當|無法判斷)")
# Distractors written with absolute words (完全、必然、唯一、所有、只會…) can be
# eliminated without reading. Measured on 111-115: 6-12% of all options, and at
# most 36% of items carry one; a generated paper had 22% and 70%.
ABSOLUTE_WORD = re.compile(r"完全|必然|必定|唯一|所有|任何|一律|全部|凡是|只要|只會|只能|從不|毫無|一切|絕不|皆|無關|不可能|永遠")
ABSOLUTE_OPTION_SHARE = 0.12
ABSOLUTE_ITEM_SHARE = 0.40
# 改寫自／〈篇名〉／《書名》 across the whole booklet: official 43-68; generated 16.
ATTRIBUTION_TOKEN = re.compile(r"改寫自|〈[^〈〉]{1,20}〉|《[^《》]{1,20}》")
ATTRIBUTION_FLOOR = 30
SELF_WRITTEN = re.compile(r"自擬|自撰|編者[^，。]{0,6}撰成?|本題情境|虛構|為本題設計")
CHARACTER_FORM_MIN_CHARACTERS = 16
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
    elif first(1):
        errors.extend(pronunciation_pair_errors(first(1)))
    for number in range(1, 25):
        if first(number) and "排列順序" in prompt(number) and "古文" not in prompt(number):
            errors.append(f"國綜第{number}題排序題須為文言（下列是一段古文，依據文意，甲、乙、丙、丁排列順序最適當的是），"
                          "113、115 官方皆如此；白話句子重排不是本形式")
    for text, numbers in groups.items():
        if numbers[0] >= 6 and not SOURCE_ATTRIBUTION.search(text):
            errors.append(f"國綜第{numbers[0]}至{numbers[-1]}題題組材料須摘錄真實作品並印出處（白話印「改寫自 作者〈篇名〉」，"
                          "文言印篇名或書名），官方每卷 17–42 處出處；自撰材料難度與語感都達不到官方卷")
    for number in range(1, 25):
        question = first(number)
        # The passage is the shared stimulus, or the prompt's text after the stem's colon;
        # the stem's own 「□□內」 shorthand is not a slot.
        passage = stimulus(number) or re.split(r"[：:]", prompt(number), maxsplit=1)[-1]
        if question and "填入" in prompt(number) and "□" in passage and question.get("options"):
            errors.extend(blank_fill_errors(number, question, passage))
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
        layout = question.get("option_layout")
        option_texts = [str(o.get("text") or "") for o in question.get("options") or [] if isinstance(o, dict)]
        if option_texts and layout not in (None, "stack", "grid-2"):
            errors.append(f"國綜第{number}題選項最多並排兩欄（官方短選項兩兩一行，長選項自成一行），不得用{layout}")
        elif option_texts and layout == "grid-2" and (
                len(option_texts) != 4 or max(len(t) for t in option_texts) > TWO_COLUMN_MAX_CHARACTERS):
            errors.append(f"國綜第{number}題選項過長或為五選項，須逐項直排；官方僅四選項且每項不超過"
                          f"{TWO_COLUMN_MAX_CHARACTERS}字時才兩兩並排")
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
        judgement_items = [q for q in questions if isinstance(q, dict) and q.get("type") == "single_choice"
                           and JUDGEMENT.search(str(q.get("prompt") or "") + str(q.get("group_stimulus") or ""))
                           and sum(1 for o in q.get("options") or [] if isinstance(o, dict)
                                   and JUDGEMENT_OPTION.search(str(o.get("text") or ""))) >= 3]
        if not judgement_items:
            errors.append("國綜每年至少一題①②研判題：單選，題幹「關於①、②是否符合上文…最適當的研判是」，選項為"
                          "①、②皆符合／皆不符合／①符合，②不符合／①不符合，②無法判斷（111 Q16、113 Q12、114 Q24、115 Q7）；"
                          "本卷沒有此形式（多選題把①②寫成成對敘述不算）")
        errors.extend(difficulty_signal_errors(questions))
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


def difficulty_signal_errors(questions: list[dict]) -> list[str]:
    """Measured surface signals that separate the official papers from an easy imitation."""
    errors = []
    option_texts = []
    absolute_items = 0
    for question in questions:
        if not isinstance(question, dict):
            continue
        texts = [str(o.get("text") or "") for o in question.get("options") or [] if isinstance(o, dict)]
        if not texts:
            continue
        option_texts.extend(texts)
        if any(ABSOLUTE_WORD.search(t) for t in texts):
            absolute_items += 1
    scored = [q for q in questions if isinstance(q, dict) and q.get("options")]
    if option_texts:
        share = sum(1 for t in option_texts if ABSOLUTE_WORD.search(t)) / len(option_texts)
        if share > ABSOLUTE_OPTION_SHARE:
            errors.append(f"國綜選項中含絕對化字眼（完全、必然、唯一、所有、只會…）的比例為 {share:.0%}，官方 111–115 為 6–12%："
                          "不讀文本就能排除的選項太多，錯誤選項須是對文本的另一種可成立的誤讀，只錯在一個推論")
        item_share = absolute_items / len(scored)
        if item_share > ABSOLUTE_ITEM_SHARE:
            errors.append(f"國綜 {absolute_items}/{len(scored)} 題有絕對化字眼的選項（{item_share:.0%}），官方最多 36%")
    second = next((q for q in questions if isinstance(q, dict) and q.get("number") == 2), None)
    if second and "錯別字" in str(second.get("prompt") or ""):
        short = [str(o.get("text") or "") for o in second.get("options") or [] if isinstance(o, dict)
                 and len(str(o.get("text") or "")) < CHARACTER_FORM_MIN_CHARACTERS]
        if short:
            errors.append(f"國綜第2題字形題每句須至少 {CHARACTER_FORM_MIN_CHARACTERS} 字（官方 18–23 字，錯字藏在成語或書面語中）；"
                          f"過短：{'；'.join(short)}")
    # A shared stimulus is printed once, so it is counted once.
    stimuli = {str(q.get("group_stimulus") or "") for q in questions if isinstance(q, dict)}
    everything = "\n".join(stimuli) + "\n" + "\n".join(
        str(q.get("prompt") or "") + "\n" + "\n".join(str(o.get("text") or "") for o in q.get("options") or [] if isinstance(o, dict))
        for q in questions if isinstance(q, dict))
    if len(scored) >= 30:
        found = len(ATTRIBUTION_TOKEN.findall(everything))
        if found < ATTRIBUTION_FLOOR:
            errors.append(f"國綜全卷出處與篇名標記（改寫自／〈篇名〉／《書名》）共 {found} 處，官方 111–115 為 43–68 處，"
                          f"下限 {ATTRIBUTION_FLOOR}：材料與選項須大量取自真實作品")
    for question in questions:
        if isinstance(question, dict):
            text = str(question.get("group_stimulus") or "") + str(question.get("prompt") or "")
            hit = SELF_WRITTEN.search(text)
            if hit:
                errors.append(f"國綜第{question.get('number')}題材料印出「{hit.group(0)}」：學生卷不得出現自擬、自撰、編者撰成、"
                              "本題情境等字樣，材料本身須是可印出處的真實作品")
                break
    return errors


def pronunciation_pair_errors(question: dict) -> list[str]:
    """Item 1 must pair two different look-alike characters, each in its own phrase."""
    errors = []
    for option in question.get("options") or []:
        if not isinstance(option, dict):
            continue
        label = str(option.get("label") or "").strip("()（）")
        text = str(option.get("text") or "")
        halves = [h.strip() for h in re.split(r"[／/]", text) if h.strip()]
        quoted = QUOTED_CHARACTER.findall(text)
        if len(halves) != 2 or len(quoted) != 2 or any(len(q) != 1 for q in quoted):
            errors.append(f"國綜第1題選項({label})須為「甲字所在短語／乙字所在短語」，每邊各引一個字：{text}")
            continue
        if quoted[0] == quoted[1]:
            errors.append(f"國綜第1題選項({label})引號內兩字相同（「{quoted[0]}」／「{quoted[1]}」）：官方每年都是兩個不同的"
                          "形近字（如「痺」／「髀」、「舁」／「臾」）比讀音，不是一字多音")
        if any(not 3 <= len(h) <= 6 for h in halves):
            errors.append(f"國綜第1題選項({label})每邊須為三至六字的文言或成語短語（官方多為四字）：{text}")
    return errors


def blank_fill_errors(number: int, question: dict, passage: str) -> list[str]:
    """詞語填空 must quote a real attributed work and use two candidates per slot."""
    errors = []
    slots = BLANK_RUN.findall(passage)
    if not SOURCE_ATTRIBUTION.search(passage):
        errors.append(f"國綜第{number}題填詞題須摘錄真實作品並印出處（作者〈篇名〉、〈篇名〉或（改寫自…）），"
                      "官方 111 杜甫詩、112〈補江總白猿傳〉、114 聶華苓皆如此；不得自撰句子挖空")
    if not 2 <= len(slots) <= 4:
        errors.append(f"國綜第{number}題填詞題須有二至四個□格（官方皆為三格）；現有{len(slots)}格")
    options = [str(o.get("text") or "") for o in question.get("options") or [] if isinstance(o, dict)]
    parts = [[part.strip() for part in re.split(r"[／/]", text)] for text in options]
    if slots and any(len(p) != len(slots) for p in parts):
        errors.append(f"國綜第{number}題填詞題每個選項的詞數須等於□格數（{len(slots)}），以／分隔")
        return errors
    if len(options) == 4 and slots:
        for index in range(len(slots)):
            column = [p[index] for p in parts]
            distinct = sorted(set(column))
            if len(distinct) != 2 or any(column.count(word) != 2 for word in distinct):
                errors.append(f"國綜第{number}題填詞題第{index + 1}格須恰有兩個候選詞、各出現在兩個選項（官方每年如此，"
                              f"如 破海綿／舊報紙、皎潔／青蒼）；現有{'、'.join(distinct)}。四個選項各用不同的詞會被逐格排除，太容易")
                break
        else:
            for i in range(4):
                for j in range(i + 1, 4):
                    if sum(a != b for a, b in zip(parts[i], parts[j])) < 2:
                        errors.append(f"國綜第{number}題填詞題選項{'ABCD'[i]}與{'ABCD'[j]}只差一格；官方任兩選項至少兩格不同")
                        break
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
