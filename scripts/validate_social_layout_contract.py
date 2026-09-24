#!/usr/bin/env python3
"""Printed-form checks for a 社會 paper, measured on the official ROC 111-115 booklets.

Two hosted 116 papers (2026-09-24 audit, made with 2026.09.22.16) were compared with the five
official booklets on disk. Official options of one item are the same length in 80% of items
(spread of at most two characters in 89-96%) and the key is the single longest option in 0-3
items a year; the hosted papers had 1 and 0 equal-length items and keys that were the longest
option in 42 and 40 of 54 items, so choosing the longest option scored about 75%. One paper
also printed 「教學虛構情境」 notes, blank 「作答區／答＿＿」 boxes, 「（本題3分）」 scores,
the same household figures in two groups, and 17 keys of the form 「再蒐集／核對資料」 (none
in any official year). Every rule below cites what the official booklets print.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

SPREAD_TOLERANCE = 2            # characters between the longest and shortest option of one item
EQUAL_LENGTH_SHARE_MIN = 0.80   # official 111-115: 0.96, 0.91, 0.93, 1.00, 0.93 of items
LONGEST_KEY_MAX = 4             # official keys that are the strictly longest option: 3, 1, 3, 0, 1
METHOD_KEY_MAX = 3              # official keys telling the student to go and collect more data: 0 a year
FIRST_TITLE = re.compile(r'^第壹部分、選擇題（占\s*(\d+)\s*分）$')
SECOND_TITLE = re.compile(r'^第貳部分、混合題或非選擇題（占\s*(\d+)\s*分）$')
SCORE_MARK = re.compile(r'（\s*(\d+)\s*分(?:[，,][^（）]*)?）')
BAD_SCORE = re.compile(r'本(?:小)?題\s*\d+\s*分|（\s*\d+\s*字以?內\s*）|（\s*限?\s*\d+\s*字\s*）')
# Official booklets never tell the student that a scenario is invented or adapted for teaching.
AUTHORING_NOTE = re.compile(r'虛構(?!文學|小說)|教學(?:情境|改寫|模擬|假設|用途|示例)|未抄錄|原創的|'
                            r'(?:與|和)(?:實際|真實)[^。；，]{0,12}無關|不代表[^。；]{0,12}實際|僅供教學')
PLACEHOLDER_ROW = re.compile(r'^\s*(?:請依題意書寫|答\s*[＿_ˍ—－\-]*|[＿_ˍ\s]+)\s*$')
# 「再蒐集／核對／追蹤資料」 keys: calibrated on the official 111-115 keys (0 hits) and two hosted
# 116 papers (0 and 17 hits).
METHOD_KEY = re.compile(r'蒐集|查證|核對|追蹤|補充|實測|量測|比對|再調查|補證|另找|須查|應查|先查|分別查|'
                        r'逐.{0,3}(?:記錄|核對|確認)|仍須.{0,8}資料|需.{0,6}資料|資料.{0,4}(?:才能|再)')
SUBPART = re.compile(r'^\s*[（(]\s*[1-9一二三]\s*[）)]|[（(]\s*2\s*[）)]\s*承')
NUMBER_TOKEN = re.compile(r'\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d{2,}%?|\d{5,}')


def _text(value):
    if isinstance(value, dict):
        value = value.get('rich') or value.get('text') or ''
    return re.sub(r'<[^>]+>', '', str(value or ''))


def _length(value):
    return len(re.sub(r'\s', '', _text(value)))


def _questions(exam):
    return [q for q in exam.get('questions') or [] if isinstance(q, dict)]


def _number(q):
    return q.get('number') if q.get('number') is not None else q.get('id')


def _keys(exam):
    keys = {}
    for answer in exam.get('answers') or []:
        if isinstance(answer, dict):
            keys[answer.get('question_id')] = str(answer.get('final_answer') or '').strip('()（） ')
    return keys


def option_form_errors(exam):
    errors, spreads, longest = [], [], []
    keys = _keys(exam)
    for q in _questions(exam):
        options = [o for o in q.get('options') or [] if isinstance(o, dict)]
        if len(options) != 4:
            continue
        lengths = {str(o.get('label') or '').strip('()（） '): _length(o.get('text')) for o in options}
        spread = max(lengths.values()) - min(lengths.values())
        spreads.append((_number(q), spread))
        key = keys.get(q.get('id'))
        if key in lengths and lengths[key] == max(lengths.values()) and list(lengths.values()).count(lengths[key]) == 1:
            longest.append(_number(q))
        for o in options:
            if re.search(r'[。；;]\s*$', _text(o.get('text'))):
                errors.append(f'Q{_number(q)}: option ({o.get("label")}) ends with 「。」 or 「；」; official 社會 options end without punctuation')
    if spreads:
        uneven = [n for n, s in spreads if s > SPREAD_TOLERANCE]
        share = 1 - len(uneven) / len(spreads)
        if share < EQUAL_LENGTH_SHARE_MIN:
            errors.append(f'{len(uneven)} of {len(spreads)} items have options differing by more than {SPREAD_TOLERANCE} characters '
                          f'(Q{", Q".join(map(str, uneven[:20]))}); official 社會 111-115 write the four options of an item to one '
                          f'length in 80% of items and within two characters in 89-96%, at least {EQUAL_LENGTH_SHARE_MIN:.0%} here')
    if len(longest) > LONGEST_KEY_MAX:
        errors.append(f'the key is the single longest option in {len(longest)} items (Q{", Q".join(map(str, longest[:20]))}); '
                      f'official 社會 111-115: 3, 1, 3, 0, 1 a year, at most {LONGEST_KEY_MAX} here: '
                      'write distractors as long and as specific as the key')
    return errors


def method_key_errors(exam):
    keys = _keys(exam)
    hits = []
    for q in _questions(exam):
        chosen = next((o for o in q.get('options') or [] if isinstance(o, dict)
                       and str(o.get('label') or '').strip('()（） ') == keys.get(q.get('id'))), None)
        if chosen and METHOD_KEY.search(_text(chosen.get('text'))):
            hits.append(_number(q))
    if len(hits) > METHOD_KEY_MAX:
        return [f'{len(hits)} keys tell the student to collect, check or track more data (Q{", Q".join(map(str, hits))}); '
                f'no official 社會 key in 111-115 does, at most {METHOD_KEY_MAX} here: test a curriculum concept '
                'applied to the printed evidence instead']
    return []


def printed_note_errors(exam):
    errors = []
    seen = set()
    for q in _questions(exam):
        texts = [q.get('group_stimulus'), q.get('prompt'), *[o.get('text') for o in q.get('options') or [] if isinstance(o, dict)]]
        table = q.get('response_format_table') if isinstance(q.get('response_format_table'), dict) else {}
        texts += [table.get('caption')]
        for value in texts:
            plain = _text(value)
            match = AUTHORING_NOTE.search(plain)
            if match and (plain, match.group(0)) not in seen:
                seen.add((plain, match.group(0)))
                errors.append(f'Q{_number(q)}: prints the authoring note 「{match.group(0)}」; official 社會 booklets never say a '
                              'scenario is invented or adapted for teaching: state the situation (「某市」「某生」) or cite the real source')
    return errors


def score_errors(exam):
    errors = []
    totals = defaultdict(float)
    for q in _questions(exam):
        totals[_number(q)] += float(q.get('score') or 0)  # 115 Q46: a checkbox and a reason share 「（4 分）」
    for q in _questions(exam):
        prompt = _text(q.get('prompt'))
        if q.get('type') != 'constructed_response' or not prompt.strip() or q.get('suppress_question_display'):
            continue
        number = _number(q)
        bad = BAD_SCORE.findall(prompt)
        if bad:
            errors.append(f'Q{number}: 「{"」「".join(bad)}」 is not the official form; write the score and word limit in one '
                          'parenthesis at the end, 「（3 分）」 or 「（3 分，35 字內）」 (115 Q49)')
        marks = [int(m.group(1)) for m in SCORE_MARK.finditer(prompt)]
        if not marks:
            errors.append(f'Q{number}: a constructed response ends with its score, 「（3 分）」 or 「（3 分，35 字內）」')
        elif marks[-1] not in {q.get('score'), totals.get(number)}:
            errors.append(f'Q{number}: prints （{marks[-1]} 分） but scores {q.get("score")}')
        if SUBPART.search(prompt):
            errors.append(f'Q{number}: official 社會 111-115 print no （1）（2） subparts; ask both tasks in one stem and put '
                          'the two answers in a response_format_table (115 Q44, Q46, Q52: a checkbox cell and a reason cell)')
    return errors


def section_errors(exam):
    sections = [s for s in exam.get('sections') or [] if isinstance(s, dict)]
    if len(sections) < 2:
        return []
    errors = []
    by_section = defaultdict(float)
    for q in _questions(exam):
        by_section[q.get('section_id')] += float(q.get('score') or 0)
    for section, pattern, example in ((sections[0], FIRST_TITLE, '第壹部分、選擇題（占76分）'),
                                      (sections[1], SECOND_TITLE, '第貳部分、混合題或非選擇題（占68分）')):
        title = _text(section.get('title')).strip()
        match = pattern.match(title)
        if not match:
            errors.append(f'section {section.get("id")}: title 「{title}」 must read as 111-115 print it, 「{example}」')
        elif by_section.get(section.get('id')) and int(match.group(1)) != round(by_section[section.get('id')]):
            errors.append(f'section {section.get("id")}: title says 占{match.group(1)}分 but its items score '
                          f'{by_section[section.get("id")]:g}')
    return errors


def answer_area_errors(exam):
    errors = []
    for q in _questions(exam):
        table = q.get('response_format_table')
        if not isinstance(table, dict):
            continue
        rows = [r for r in table.get('rows') or [] if isinstance(r, dict)]
        heading = _text(table.get('heading'))
        blank = [r for r in rows if PLACEHOLDER_ROW.match(_text(r.get('label')) + _text(r.get('instruction')))]
        if heading.strip() in {'作答區', '作答欄'} or (rows and len(blank) == len(rows)):
            errors.append(f'Q{_number(q)}: a blank 「作答區／答＿＿」 box is not an official device; answers go on the answer '
                          'sheet, and a response table prints only labelled cells (勾選項目、判斷理由（2 分，30 字內）)')
    return errors


def repeated_data_errors(exam):
    """The same figures printed in two different materials (a hosted paper used one
    household count in Q3 and Q39 and one employment count in Q4 and Q55)."""
    places = defaultdict(set)
    for q in _questions(exam):
        material = _text(q.get('group_stimulus')) or _text(q.get('prompt'))
        for token in set(NUMBER_TOKEN.findall(material)):
            places[token].add(material)
    owners = {}
    for q in _questions(exam):
        material = _text(q.get('group_stimulus')) or _text(q.get('prompt'))
        owners.setdefault(material, _number(q))
    repeated = sorted({token for token, where in places.items() if len(where) > 1})
    if len(repeated) >= 2:
        pairs = sorted({tuple(sorted(owners[m] for m in places[t])) for t in repeated}, key=str)
        return [f'the figures {", ".join(repeated[:6])} are printed in more than one material '
                f'({"; ".join("Q" + " and Q".join(map(str, p)) for p in pairs[:4])}); each group needs its own evidence']
    return []


def validate_exam(exam):
    return [*section_errors(exam), *option_form_errors(exam), *method_key_errors(exam), *printed_note_errors(exam),
            *score_errors(exam), *answer_area_errors(exam), *repeated_data_errors(exam)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exam_json', type=Path)
    args = parser.parse_args()
    errors = validate_exam(json.loads(args.exam_json.read_text(encoding='utf-8-sig')))
    print(json.dumps({'status': 'fail' if errors else 'pass', 'errors': errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
