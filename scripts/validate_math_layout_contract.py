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
* every 多選題 stem asks 「試選出正確的選項」 and no stem asks 「下列敘述哪些正確」 or
  「以下何者正確」 (0 of 200 official items);
* a fraction 選填 answer is announced after its rail as 「（化為最簡分數）」;
* the 第貳部分 題組 marks its 單選題 「（單選題，N分）」 and each written item
  「（非選擇題，N分）」 (every year in both subjects).

Structural passes are never editorial passes.
"""
from __future__ import annotations

from collections import Counter
import json
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
# 數學B unit families by 108 scope code (templates/current-gsat-math-scope.json), and the
# per-paper envelope hand-classified on the official 111–115 booklets (20 items each, the
# 第貳部分 題組 counted as three): matrix 1/1/1/1/1, sphere or space 1/1/3/2/1,
# perspective 1/3/0/1/1, conic 0/1/0/1/1, polynomial 2/2/2/2/2, line-circle 1/1/1/1/5,
# trigonometry 3/2/1/2/2, exp-log 2/2/2/2/1, sequence 0/2/1/1/2, counting 2/1/1/1/1,
# probability 2/1/2/2/2, data 1/1/2/1/1, vector 2/1/2/1/0, number 2/2/1/2/1. Items carrying
# an 11B-only code: 7/8/6/8/8.
MATH_B_FAMILIES = {
    'number': ('N-10-1', 'N-10-2', 'N-10-5', 'N-10-7'),
    'exp_log': ('N-10-3', 'N-10-4', 'F-11B-2'),
    'polynomial': ('A-10-1', 'A-10-2', 'F-10-1', 'F-10-2', 'F-10-3'),
    'line_circle': ('G-10-1', 'G-10-2', 'G-10-3', 'G-10-4'),
    'trigonometry': ('G-10-5', 'G-10-6', 'G-10-7', 'N-11B-1', 'F-11B-1'),
    'sequence': ('N-10-6',),
    'counting': ('D-10-1', 'D-10-3'),
    'probability': ('D-10-4', 'D-11B-1'),
    'data': ('D-10-2', 'D-11B-2'),
    'matrix': ('A-11B-1',),
    'vector': ('G-11B-1', 'G-11B-2'),
    'sphere_space': ('S-11B-1', 'G-11B-4'),
    'perspective': ('G-11B-3',),
    'conic': ('S-11B-2',),
}
MATH_B_FAMILY_LABELS = {'number': '數與式', 'exp_log': '指數與對數', 'polynomial': '多項式函數', 'line_circle': '直線與圓',
                        'trigonometry': '三角', 'sequence': '數列與級數', 'counting': '排列組合', 'probability': '機率',
                        'data': '數據分析', 'matrix': '矩陣', 'vector': '平面向量', 'sphere_space': '空間概念與球面',
                        'perspective': '單點透視', 'conic': '圓錐曲線'}
MATH_B_REQUIRED_FAMILIES = ('matrix', 'sphere_space', 'polynomial', 'line_circle', 'trigonometry', 'exp_log',
                            'counting', 'probability', 'data')          # ≥1 item in every official year
MATH_B_FAMILY_CAPS = {'sequence': 2, 'counting': 2, 'probability': 3, 'matrix': 2, 'sphere_space': 3, 'data': 2}
# Polynomial is 2 items in every official year; a hosted paper had 1 (and 4 data items,
# a data 題組 the booklets never set).
MATH_B_FAMILY_FLOORS = {'polynomial': 2}
MATRIX_PRINTED = re.compile(r'矩陣|方陣|\[\s*-?\d')
MATH_B_ANY_FAMILY_CAP = 5
MATH_B_11B_ITEMS = (3, 10)
MATH_A_ONLY_CODES = re.compile(r'^[A-Z]-11A-\d+$')
# 數學A unit families, hand-classified item by item on the official 111–115 booklets
# (page images where extraction lost the math; 題組 counted as three). Per year:
# number 1/0/0/0/1, exp_log 1/1/2/1/2, polynomial 2/1/2/2/2, line_circle 2/2/2/4/2,
# trigonometry 4/4/3/3/2, sequence 1/2/0/1/0, counting 1/1/1/1/1, probability 2/1/1/2/2,
# data 1/1/1/1/1, matrix 1/2/3/2/2, plane_vector 1/1/1/1/2, space 3/4/4/2/3. Items
# needing an 11A-only code: 8/10/13/9/10. Two hosted 116 數A papers had no matrix,
# plane-vector or 正餘弦定理 item.
MATH_A_FAMILIES = {
    'number': ('N-10-1', 'N-10-2', 'N-10-5', 'N-10-7'),
    'exp_log': ('N-10-3', 'N-10-4', 'A-11A-4', 'F-11A-4'),
    'polynomial': ('A-10-1', 'A-10-2', 'F-10-1', 'F-10-2', 'F-10-3'),
    'line_circle': ('G-10-1', 'G-10-2', 'G-10-3', 'G-10-4'),
    'trigonometry': ('G-10-5', 'G-10-6', 'G-10-7', 'N-11A-1', 'G-11A-5', 'F-11A-1', 'F-11A-2'),
    'sequence': ('N-10-6',),
    'counting': ('D-10-1', 'D-10-3'),
    'probability': ('D-10-4', 'D-11A-1', 'D-11A-2', 'D-11A-3'),
    'data': ('D-10-2',),
    'matrix': ('A-11A-1', 'A-11A-2', 'A-11A-3', 'F-11A-3'),
    'plane_vector': ('G-11A-1', 'G-11A-4', 'G-11A-6'),
    'space': ('S-11A-1', 'G-11A-2', 'G-11A-3', 'G-11A-7', 'G-11A-8', 'G-11A-9', 'G-11A-10'),
}
MATH_A_FAMILY_LABELS = {'number': '數與式', 'exp_log': '指數與對數', 'polynomial': '多項式函數', 'line_circle': '直線與圓',
                        'trigonometry': '三角（含正餘弦定理、和角、三角函數）', 'sequence': '數列與級數', 'counting': '排列組合',
                        'probability': '機率（含條件機率、期望值）', 'data': '數據分析', 'matrix': '矩陣與線性變換',
                        'plane_vector': '平面向量', 'space': '空間向量、平面與直線'}
MATH_A_REQUIRED_FAMILIES = ('exp_log', 'polynomial', 'line_circle', 'trigonometry', 'counting', 'probability', 'data',
                            'matrix', 'plane_vector', 'space')     # ≥1 item in every official year
MATH_A_FAMILY_CAPS = {'number': 2, 'sequence': 2, 'counting': 2, 'probability': 3, 'data': 2}
MATH_A_ANY_FAMILY_CAP = 5
MATH_A_11A_ITEMS = (6, 14)
UNOFFICIAL_ASK = re.compile(r'下列敘述.{0,4}(?:哪些|何者)|以下何者|下列哪些選項|哪些選項|敘述哪些正確')
MULTIPLE_ASK = '試選出正確的選項'
FRACTION_NOTE = re.compile(r'（化為最簡分數）\s*$')
# The booklets draw vector arrows and segment bars over the letters; the renderer does
# it from {{vec:AB}} / {{seg:AB}}. Plain 「向量AB」 or combining marks print wrongly.
PLAIN_VECTOR = re.compile(r'向量\s*[A-Z]{2}(?![A-Za-z])|[⃗⃑̅̄]')
PART_TWO_SCORE = {'single_choice': re.compile(r'（單選題，\s*\d+\s*分）\s*$'),
                  'written': re.compile(r'（非選擇題，\s*\d+\s*分）\s*$')}


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
    if subject == '數學B':
        errors.extend(math_b_scope_errors(questions, full))
    if subject == '數學A':
        errors.extend(math_a_scope_errors(questions, full))
    # CEEC publishes a 評分原則 for the written items every year (111–115): full marks and
    # the partial credit per step. A hosted 數B paper's solutions gave neither for 19–20.
    answers = {str(a.get('question_id')): a for a in exam.get('answers') or [] if isinstance(a, dict)}
    for q in questions:
        record = answers.get(str(q.get('id')))
        if (record and isinstance(q.get('number'), int) and q['number'] >= 18
                and q.get('type') not in {'single_choice', 'multiple_choice', 'fill_in'}
                and '評分' not in json.dumps(record, ensure_ascii=False)):
            errors.append(f'{subject}第{q["number"]}題（非選擇題）詳解須附評分原則：滿分條件與各步驟的部分給分'
                          '（官方 111–115 每年公布）')

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
        vector = PLAIN_VECTOR.search(stem + _compact(question.get('group_stimulus')) +
                                     ''.join(_compact(o.get('text')) for o in question.get('options') or [] if isinstance(o, dict)))
        if vector:
            errors.append(f'{subject}第{number}題寫成「{vector.group(0)}」：官方以字母上方的箭號表示向量、橫線表示線段長，'
                          '請寫 {{vec:AB}}（向量）或 {{seg:AB}}（線段），不要用「向量AB」或組合符號')
        ask = UNOFFICIAL_ASK.search(stem)
        if ask:
            errors.append(f'{subject}第{number}題問「{ask.group(0)}」：官方 111–115 多選題一律寫「試選出正確的選項。」，'
                          '單選題寫「試問…為何？」')
        if question.get('type') == 'multiple_choice' and MULTIPLE_ASK not in stem:
            errors.append(f'{subject}第{number}題（多選）須以「試選出正確的選項。」作答要求（官方 111–115 每題皆同）')
        answer_format = question.get('answer_format') if isinstance(question.get('answer_format'), dict) else {}
        raw = str(question.get('prompt') or '')
        if answer_format.get('kind') == 'fraction' and not FRACTION_NOTE.search(raw):
            errors.append(f'{subject}第{number}題是分數選填：官方在答案格之後印「。（化為最簡分數）」作結'
                          '（不寫「化為最簡分數後為」）')
        if isinstance(question.get('number'), int) and question['number'] >= 18:
            role = 'single_choice' if question.get('type') == 'single_choice' else (
                'written' if question.get('type') not in {'multiple_choice', 'fill_in'} else None)
            if role and not PART_TWO_SCORE[role].search(raw):
                label = '（單選題，3分）' if role == 'single_choice' else '（非選擇題，N分）'
                errors.append(f'{subject}第{number}題（第貳部分題組）須以「{label}」作結（官方 111–115 每年如此），'
                              '不是只寫「（4分）」或不標')

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
        fills = [q for q in questions if isinstance(q.get('number'), int) and 13 <= q['number'] <= 17]
        if len(fills) == 5 and not any((q.get('answer_format') or {}).get('kind') == 'fraction' for q in fills
                                       if isinstance(q.get('answer_format'), dict)):
            errors.append(f'{subject}選填題 13–17 沒有分數答案：官方 111–115 每年至少一題「（化為最簡分數）」'
                          '（數A 1–4 題、數B 1–3 題），五題都填兩位整數的格式與官方不符')
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


def math_b_family(codes: list) -> str | None:
    """Primary unit family of an item: the family of its first recognised scope code."""
    for code in codes:
        for family, members in MATH_B_FAMILIES.items():
            if str(code) in members:
                return family
    return None


def math_b_scope_errors(questions: list[dict], full: bool) -> list[str]:
    """Per-item scope codes and the measured 111–115 unit envelope of a 數學B paper."""
    errors: list[str] = []
    families: Counter = Counter()
    eleven_b = 0
    for q in questions:
        number = q.get('number')
        spec = q.get('item_spec') if isinstance(q.get('item_spec'), dict) else {}
        codes = [str(c) for c in (spec.get('scope_codes') or [])]
        if not codes:
            errors.append(f'數學B第{number}題缺 item_spec.scope_codes（108 課綱代碼，見 current-gsat-math-scope.md）')
            continue
        foreign = [c for c in codes if MATH_A_ONLY_CODES.match(c)]
        if foreign:
            errors.append(f'數學B第{number}題使用數A專屬代碼 {foreign}；數B不含空間向量、平面方程式、和角公式與一般對數律')
        family = math_b_family(codes)
        if family is None:
            errors.append(f'數學B第{number}題的代碼 {codes} 不在數B範圍（10年級共同核心＋11B）')
            continue
        families[family] += 1
        printed = str(q.get('prompt') or '') + str(q.get('group_stimulus') or '')
        if family == 'matrix' and not MATRIX_PRINTED.search(printed):
            errors.append(f'數學B第{number}題歸為矩陣單元，題目卻沒有出現矩陣；官方 111–115 每年的矩陣題都直接以矩陣命題'
                          '（一題只用線性變換文字描述、不見矩陣，矩陣單元形同缺席）')
        if any('11B' in c for c in codes):
            eleven_b += 1
    if not full or len(questions) < 20:
        return errors
    missing = [MATH_B_FAMILY_LABELS[f] for f in MATH_B_REQUIRED_FAMILIES if families[f] == 0]
    if missing:
        errors.append(f'數學B整卷缺 {"、".join(missing)}：官方 111–115 每卷都各有至少 1 題')
    for family, cap in MATH_B_FAMILY_CAPS.items():
        if families[family] > cap:
            errors.append(f'數學B {MATH_B_FAMILY_LABELS[family]} 有 {families[family]} 題，官方 111–115 每卷最多 {cap} 題')
    for family, floor in MATH_B_FAMILY_FLOORS.items():
        if families[family] < floor:
            errors.append(f'數學B {MATH_B_FAMILY_LABELS[family]} 只有 {families[family]} 題，官方 111–115 每卷都是 {floor} 題')
    for family, count in families.items():
        if count > MATH_B_ANY_FAMILY_CAP:
            errors.append(f'數學B {MATH_B_FAMILY_LABELS[family]} 有 {count} 題，超過單一單元上限 {MATH_B_ANY_FAMILY_CAP}（官方最高為 115 直線與圓 5 題）')
    low, high = MATH_B_11B_ITEMS
    if not low <= eleven_b <= high:
        errors.append(f'數學B 帶 11B 專屬代碼的題目 {eleven_b} 題，官方 111–115 為 6–8 題（允許 {low}–{high}）：'
                      '矩陣、球面／空間、透視、圓錐曲線、正弦模型、平面向量、條件機率須有合理比重')
    return errors


def _family(codes: list, table: dict) -> str | None:
    for code in codes:
        for family, members in table.items():
            if str(code) in members:
                return family
    return None


def math_a_scope_errors(questions: list[dict], full: bool) -> list[str]:
    """The measured 111–115 unit envelope of a full 數學A paper (codes themselves are checked elsewhere)."""
    coded = [q for q in questions if isinstance(q.get('item_spec'), dict) and q['item_spec'].get('scope_codes')]
    if not full or len(questions) < 20 or len(coded) < len(questions):
        return []  # validate_math_curriculum reports items without scope_codes
    families: Counter = Counter()
    eleven_a = 0
    for q in questions:
        spec = q.get('item_spec') if isinstance(q.get('item_spec'), dict) else {}
        codes = [str(c) for c in (spec.get('scope_codes') or [])]
        family = _family(codes, MATH_A_FAMILIES)
        if family:
            families[family] += 1
        if any(MATH_A_ONLY_CODES.match(c) for c in codes):
            eleven_a += 1
    errors = []
    missing = [MATH_A_FAMILY_LABELS[f] for f in MATH_A_REQUIRED_FAMILIES if families[f] == 0]
    if missing:
        errors.append(f'數學A整卷缺 {"、".join(missing)}：官方 111–115 每卷都各有至少 1 題（以各題 scope_codes 的第一個可辨識代碼歸類）')
    for family, cap in MATH_A_FAMILY_CAPS.items():
        if families[family] > cap:
            errors.append(f'數學A {MATH_A_FAMILY_LABELS[family]} 有 {families[family]} 題，官方 111–115 每卷最多 {cap - 1}–{cap} 題（上限 {cap}）')
    for family, count in families.items():
        if count > MATH_A_ANY_FAMILY_CAP:
            errors.append(f'數學A {MATH_A_FAMILY_LABELS[family]} 有 {count} 題，超過單一單元上限 {MATH_A_ANY_FAMILY_CAP}（官方最高 4 題）')
    low, high = MATH_A_11A_ITEMS
    if not low <= eleven_a <= high:
        errors.append(f'數學A 帶 11A 專屬代碼的題目 {eleven_a} 題，官方 111–115 為 8–13 題（允許 {low}–{high}）')
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
