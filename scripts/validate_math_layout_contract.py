#!/usr/bin/env python3
"""Printed-form and stem-rhetoric contract for 數學A／數學B, measured on ROC 111–115.

Two hosted 116 數A papers (2026-09-22) passed every existing gate and still read
unlike the official booklets: one printed method instructions inside stems
(「先利用對數律合併左式，再依 x 的正負限制選取可行值」), a student-facing
disclaimer (「下列數值與流程為本題的模擬資料」) and no part headings; the other
ran 9 pages against the official 8 because stems averaged twice the official
length and used the same 物價指數年增率 context in three items.

Official facts this module enforces (text extracted from the ten booklets):

* headings: 第壹部分、選擇（填）題（占85分）／一、單選題（占30分 in 數A, 35 in 數B）／
  二、多選題（占30分 in 數A, 25 in 數B）／三、選填題（占25分）／第貳部分、混合題或非選擇題（占15分）;
* five options labelled (1)–(5) on every choice item;
* selected-response stems (items 1–17): median 83–123 compact characters,
  never above 340 in 數A; no stem tells the solver which formula or step to use;
* no student-facing disclaimer or invented-source label;
* no real-world context repeated in three or more items (official four-character
  repeats are only generic phrases such as 坐標平面上 and 試選出正確的選項).

Structural passes are never editorial passes.
"""
from __future__ import annotations

from collections import Counter
import re
from typing import Any

HEADINGS = {
    '數學A': ['第壹部分、選擇（填）題（占85分）', '一、單選題（占30分）', '二、多選題（占30分）', '三、選填題（占25分）',
            '第貳部分、混合題或非選擇題（占15分）'],
    '數學B': ['第壹部分、選擇（填）題（占85分）', '一、單選題（占35分）', '二、多選題（占25分）', '三、選填題（占25分）',
            '第貳部分、混合題或非選擇題（占15分）'],
}
METHOD_HINT = re.compile(r'先利用|先以|再依|再利用|判斷時應|可先|請先|先求出?|先化|先將|先代入|利用.{0,6}(?:公式|定理|律|性質).{0,4}(?:求|得|判斷|合併)|'
                         r'依.{0,8}(?:性質|定理|條件).{0,3}[，,]')
DISCLAIMER = re.compile(r'模擬資料|本題情境|並非.{0,14}(?:實際|真實)|自擬|自撰|虛構|編者.{0,6}撰')
GENERIC_PHRASES = ('根據上述', '依據上述', '根據題意', '依據題意', '哪個選項', '哪一選項', '下列敘述哪些正確', '下列敘述何者正確', '下列敘述何者為真', '下列選項何者正確', '下列哪些選項正確', '哪些選項是正確的',
                   '哪一個選項是正確的', '試選出正確的選項', '選出正確的選項', '試問下列何者正確', '下列何者正確', '為下列何者',
                   '等於下列何者', '之值為何', '為何', '坐標平面上', '坐標空間中', '化為最簡分數', '最簡分數', '如圖所示', '在答題卷',
                   '非選擇題', '所有可能的', '正整數', '實數', '下列哪一', '試問', '下列', '哪些', '何者', '滿足', '已知', '則', '若',
                   '其中', '設', '令', '為', '的', '與', '且', '之', '是', '有', '一個', '兩個', '三個', '四個', '五個')
GENERIC_PATTERN = re.compile('|'.join(sorted(map(re.escape, GENERIC_PHRASES), key=len, reverse=True)))
STEM_MAX_CHARACTERS = 340
STEM_MEDIAN_MAX = 150
CONTEXT_REPEAT_ITEMS = 3
OPTION_LABELS = ('1', '2', '3', '4', '5')


def _compact(text: Any) -> str:
    return re.sub(r'\s+', '', str(text or ''))


def _label(option: dict) -> str:
    return str(option.get('label') or '').strip().strip('()（）')


def validate_exam(exam: dict) -> list[str]:
    metadata = exam.get('metadata') or {}
    subject = metadata.get('paper_subject') or metadata.get('subject')
    if subject not in HEADINGS:
        return []
    questions = [q for q in exam.get('questions') or [] if isinstance(q, dict)]
    errors: list[str] = []
    full = metadata.get('generation_mode') == 'full-paper' or len(questions) >= 20

    for question in questions:
        number = question.get('number') or question.get('id')
        stem = _compact(question.get('prompt'))
        hint = METHOD_HINT.search(stem)
        if hint:
            errors.append(f'{subject}第{number}題題幹寫出解法指示「{hint.group(0)}」：官方 111–115 題幹從不告訴考生該用哪個公式或步驟，'
                          '刪掉指示，讓判斷路徑成為題目的一部分')
        printed = stem + _compact(question.get('group_stimulus'))
        disclaimer = DISCLAIMER.search(printed)
        if disclaimer:
            errors.append(f'{subject}第{number}題印出「{disclaimer.group(0)}」：學生卷不得出現模擬資料、本題情境、並非實際等聲明；'
                          '情境數值要麼取自可印出處的真實資料，要麼寫成不需聲明的假設情境')
        if isinstance(question.get('number'), int) and question['number'] <= 17 and len(stem) > STEM_MAX_CHARACTERS:
            errors.append(f'{subject}第{number}題題幹 {len(stem)} 字：官方選擇（填）題題幹不超過 {STEM_MAX_CHARACTERS} 字（中位數 83–123），'
                          '刪掉不改變解題路徑的敘述')
        if question.get('type') in {'single_choice', 'multiple_choice'}:
            labels = [_label(o) for o in question.get('options') or [] if isinstance(o, dict)]
            if tuple(labels) != OPTION_LABELS:
                errors.append(f'{subject}第{number}題須有五個選項並標為(1)(2)(3)(4)(5)；現有 {labels}')

    if full:
        titles = [_compact(s.get('title')) for s in exam.get('sections') or [] if isinstance(s, dict)]
        for heading in HEADINGS[subject]:
            if _compact(heading) not in titles:
                errors.append(f'{subject}缺少官方標題「{heading}」（111–115 每年皆同；sections[].title 須逐字相同）')
        stems = [len(_compact(q.get('prompt'))) for q in questions if isinstance(q.get('number'), int) and q['number'] <= 17]
        if stems:
            ordered = sorted(stems)
            median = ordered[len(ordered) // 2]
            if median > STEM_MEDIAN_MAX:
                errors.append(f'{subject}選擇（填）題題幹中位數 {median} 字，官方 111–115 為 83–123 字：'
                              '整卷敘述過長會多出一頁，且把判斷寫成說明降低難度')
        # A shared stimulus is one context however many items read it.
        contexts: dict[str, list] = {}
        for q in questions:
            key = _compact(q.get('group_stimulus')) or f"item:{q.get('id')}"
            entry = contexts.setdefault(key, [key if not key.startswith('item:') else '', []])
            entry[0] += _compact(q.get('prompt'))
            entry[1].append(str(q.get('number') or q.get('id')))
        stems = [text for text, _ in contexts.values()]
        labels = ['、'.join(items) if len(items) == 1 else f'{items[0]}–{items[-1]}' for _, items in contexts.values()]
        for items, gram in context_repeats(stems, labels)[:3]:
            errors.append(f'{subject}第{"、".join(items)}題共用同一情境「{gram}」：官方 111–115 從不在三題以上重複同一現實情境'
                          '（重複的只有坐標平面上、試選出正確的選項等套語），換成不同情境')
    return errors


def context_repeats(stems: list[str], labels: list[str] | None = None) -> list[tuple[tuple, str]]:
    """Four-character phrases (generic exam wording removed) shared by three or more stems."""
    labels = labels or [str(i + 1) for i in range(len(stems))]
    owners: dict[str, set] = {}
    for label, stem in zip(labels, stems):
        cleaned = GENERIC_PATTERN.sub(' ', _compact(stem))
        seen = set()
        for run in re.findall(r'[一-鿿]{4,}', cleaned):
            for i in range(len(run) - 3):
                gram = run[i:i + 4]
                if gram not in seen:
                    seen.add(gram)
                    owners.setdefault(gram, set()).add(label)
    repeated = {gram: tuple(sorted(items, key=lambda v: (len(v), v))) for gram, items in owners.items()
                if len(items) >= CONTEXT_REPEAT_ITEMS}
    by_items: dict[tuple, str] = {}
    for gram, items in sorted(repeated.items(), key=lambda kv: -len(kv[0])):
        by_items.setdefault(items, gram)
    return list(by_items.items())
