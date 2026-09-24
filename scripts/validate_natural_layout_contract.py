#!/usr/bin/env python3
"""Printed-form checks for a 自然 paper, measured on the official ROC 111-115 booklets.

Two hosted 116 papers (2026-09-24 audit) were compared with the five official booklets on
disk. Official booklets label every figure and table 「圖1」「表2」 (16-28 圖 and 4-12 表 a
year) and cite the label in the stem; the hosted papers wrote 「如圖」「如表」 with no label.
Official keys are the single longest of five options in 1-3 single-choice items a year (7-14%)
and one item's options differ by a median 1-5 characters; the hosted papers had 22% and 52%
and a median of 11-12. One paper printed 「教學模型」「非NASA數據」 notes in almost every group
and keyed many items 「仍需另查資料」 (official: at most one such correct option a year).
Official written subparts are 「(a)」「(b)」 after the number printed once (112-115).
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

from validate_social_layout_contract import METHOD_KEY, _keys, _length, _number, _questions, _text

LONGEST_KEY_MAX = 4            # official single-choice keys that are the strictly longest option: 2, 1, 3, 2, 2
OPTION_SPREAD_MEDIAN_MAX = 6   # official median spread of one item's five options: 1, 5, 2, 2, 3.5 characters
METHOD_KEY_MAX = 3             # official correct options of the 「再查證／補充資料」 kind: 0, 0, 1, 0, 0
CAPTION = re.compile(r'^(圖|表|照片)\s*(\d+)(?:\s*[(（][a-z甲乙丙丁][)）])?$')
# 「如圖」「依表」 with no number, in an item whose text cites no 「圖N／表N／照片N」 at all. Official
# stems write 「如圖14。圖中…」 and 「下表」 for an answer table, so only the unnumbered pointer counts.
BARE_REFERENCE = re.compile(r'(?:如|依|由|附|見)(?:圖|表|照片)(?![\s\d]*\d)')
NUMBERED_LABEL = re.compile(r'(?:圖|表|照片)\s*\d')
AUTHORING_NOTE = re.compile(r'虛構|教學(?:模型|情境|假設|用途|示意|改寫|模擬)|課堂模型|僅供教學|未抄錄|'
                            r'非\s*(?:NASA|NOAA|ESA|官方|真實|現場)[^。；，]{0,8}(?:數據|資料|實測|測值|觀測)|'
                            r'不是\s*(?:NASA|NOAA|ESA)[^。；]{0,10}(?:數據|資料|測值)')
OVERUSED = Path(__file__).resolve().parents[1] / 'exam_packs' / '學測' / 'shared-data' / 'overused-generated-materials.json'
NUMBERED_SUBPART = re.compile(r'^\s*\d{1,2}\s*[(（][a-z1-9][)）]')
DIGIT_SUBPART = re.compile(r'^\s*[(（][1-9][)）]')


def figure_label_errors(exam, subject='自然'):
    """Every figure carries a caption label, cited in its text; labels run 1, 2, 3 in print order."""
    errors = []
    questions = sorted(_questions(exam), key=lambda q: (q.get('number') or 0))
    group_text = defaultdict(str)
    for q in questions:
        key = str(q.get('group_stimulus') or '').strip()
        if key:
            group_text[key] += _text(q.get('prompt'))
    seen = defaultdict(list)
    for q in questions:
        number = _number(q)
        texts = [_text(q.get('group_stimulus')), _text(q.get('prompt'))]
        texts += [_text(o.get('text')) for o in q.get('options') or [] if isinstance(o, dict)]
        for value in texts:
            bare = BARE_REFERENCE.search(value)
            if bare and not NUMBERED_LABEL.search(' '.join(texts)):
                errors.append(f'Q{number}: 「{bare.group(0)}」 names no figure; {subject} 111-115 label every figure and table '
                              '(「如圖3」「表2」) and print the label under it: give the visual_asset a caption 「圖3」 and cite it')
                break
        asset = q.get('visual_asset')
        if not isinstance(asset, dict):
            continue
        caption = str(asset.get('caption') or '').strip()
        match = CAPTION.match(caption)
        if not match:
            errors.append(f'Q{number}: visual_asset.caption must be the printed label 「圖1」「表2」「照片1」 (found {caption!r})')
            continue
        seen[match.group(1)].append((number, int(match.group(2))))
        cited = ' '.join(texts) + ' ' + group_text.get(str(q.get('group_stimulus') or '').strip(), '')
        label = match.group(1) + match.group(2)
        if not re.search(re.escape(match.group(1)) + r'\s*' + match.group(2) + r'(?!\d)', cited):
            errors.append(f'Q{number}: {label} is printed but its material and stems never cite 「{label}」')
    for kind, rows in seen.items():
        values = [n for _, n in rows]
        distinct = list(dict.fromkeys(values))
        if distinct != list(range(1, len(distinct) + 1)):
            errors.append(f'{kind} labels run {distinct} in print order; number them 1, 2, 3 … as the official booklets do')
    return errors


def option_errors(exam):
    errors, spreads, longest = [], [], []
    keys = _keys(exam)
    for q in _questions(exam):
        options = [o for o in q.get('options') or [] if isinstance(o, dict)]
        if len(options) != 5:
            continue
        lengths = {str(o.get('label') or '').strip('()（） '): _length(o.get('text')) for o in options}
        spreads.append(max(lengths.values()) - min(lengths.values()))
        key = keys.get(q.get('id'))
        if q.get('type') == 'single_choice' and key in lengths and lengths[key] == max(lengths.values()) \
                and list(lengths.values()).count(lengths[key]) == 1:
            longest.append(_number(q))
        for o in options:
            if re.search(r'[。；;]\s*$', _text(o.get('text'))):
                errors.append(f'Q{_number(q)}: option ({o.get("label")}) ends with 「。」; official 自然 options end without it')
                break
    if len(longest) > LONGEST_KEY_MAX:
        errors.append(f'the key is the single longest option in {len(longest)} single-choice items (Q{", Q".join(map(str, longest))}); '
                      f'official 自然 111-115: 2, 1, 3, 2, 2 a year, at most {LONGEST_KEY_MAX} here: write each distractor as '
                      'complete and specific as the key')
    if spreads and statistics.median(spreads) > OPTION_SPREAD_MEDIAN_MAX:
        errors.append(f'the five options of an item differ by a median {statistics.median(spreads):g} characters; official '
                      f'自然 111-115: 1-5, at most {OPTION_SPREAD_MEDIAN_MAX} here')
    return errors


def method_key_errors(exam):
    keys = _keys(exam)
    hits = []
    for q in _questions(exam):
        chosen = set(re.findall(r'[A-E]', str(keys.get(q.get('id')) or '')))
        for o in q.get('options') or []:
            if isinstance(o, dict) and str(o.get('label') or '').strip('()（） ') in chosen and METHOD_KEY.search(_text(o.get('text'))):
                hits.append(_number(q))
                break
    if len(hits) > METHOD_KEY_MAX:
        return [f'{len(hits)} items are keyed on 「再蒐集／核對／另查資料」 (Q{", Q".join(map(str, hits))}); official 自然 111-115 '
                f'have at most one such correct option a year, at most {METHOD_KEY_MAX} here: key the science the evidence shows']
    return []


def note_errors(exam):
    errors = []
    for q in _questions(exam):
        texts = [q.get('group_stimulus'), q.get('prompt'), *[o.get('text') for o in q.get('options') or [] if isinstance(o, dict)]]
        for value in texts:
            match = AUTHORING_NOTE.search(_text(value))
            if match:
                errors.append(f'Q{_number(q)}: prints the authoring note 「{match.group(0)}」; official 自然 booklets state '
                              'assumptions as 「(設)」 or 「假設…」 and never say data are invented or not an agency\'s')
                break
    return errors


def subpart_errors(exam):
    errors = []
    for q in _questions(exam):
        if q.get('type') != 'constructed_response':
            continue
        prompt = _text(q.get('prompt'))
        if NUMBERED_SUBPART.match(prompt):
            errors.append(f'Q{_number(q)}: the prompt starts with its number and subpart (「{prompt[:6]}」); print the number '
                          'once and start each subpart with (a), (b) as 112-115 do (save each as its own record)')
        elif DIGIT_SUBPART.match(prompt) or str(q.get('subpart_label') or '').strip('()（） ').isdigit():
            errors.append(f'Q{_number(q)}: 自然 112-115 label written subparts (a), (b), not (1), (2)')
    return errors


def overused_material_errors(exam, subject='自然'):
    """Specific objects earlier generated papers wore out (the Hubble deep field, …)."""
    if not OVERUSED.is_file():
        return []
    entries = [e for e in json.loads(OVERUSED.read_text(encoding='utf-8'))['entries'] if subject in e['subjects']]
    errors = []
    for q in _questions(exam):
        texts = ' '.join([_text(q.get('group_stimulus')), _text(q.get('prompt'))])
        for entry in entries:
            if re.search(entry['pattern'], texts, re.I):
                errors.append(f'Q{_number(q)}: builds on {entry["what"]}, which {entry["seen"]} already used; choose '
                              'another object or dataset')
                break
    return errors


def validate_exam(exam):
    return [*figure_label_errors(exam), *overused_material_errors(exam), *option_errors(exam), *method_key_errors(exam), *note_errors(exam),
            *subpart_errors(exam)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exam_json', type=Path)
    args = parser.parse_args()
    errors = validate_exam(json.loads(args.exam_json.read_text(encoding='utf-8-sig')))
    print(json.dumps({'status': 'fail' if errors else 'pass', 'errors': errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
