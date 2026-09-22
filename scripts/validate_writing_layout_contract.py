#!/usr/bin/env python3
"""Printed-form contract of the current GSAT 國寫 paper, measured on ROC 111–115.

The five official booklets (text extracted from the question PDFs on disk) share
one form that no earlier gate checked at save time:

* two 大題 printed as 一、 and 二、 under 非選擇題（共二大題，占50分）;
* 第一大題 (知性): one 白話 material of 331–606 CJK characters (two texts labelled
  甲／乙 in 113), then 問題（一）… 文長限80字以內（至多4行）。（占4分） and
  問題（二）… 文長限400字以內（至多19行）。（占21分）; 問題（一） always points back
  at the material (上文／甲、乙二文);
* 第二大題 (情意): one literary material of 226–443 CJK characters (essay, poem
  excerpt, or 幾米 圖文), then 請以「題目」為題 … （占25分）, asking for lived
  experience, feeling or imagination (書寫／抒發／敘述／描述／體悟／想像);
* at least one material each year carries an inline attribution
  （改寫自／節錄自 作者《書名》or〈篇名〉）; no material is 文言; nothing is 自擬.

Structural passes are never editorial passes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_chinese_layout_contract import is_classical  # noqa: E402

TASK_ONE_MATERIAL_CJK = (280, 700)      # official 331–606
TASK_TWO_MATERIAL_CJK = (180, 520)      # official 226–443
TASK_ONE_SHORT = re.compile(r'文長限\s*80\s*字以內（至多\s*4\s*行）')
TASK_ONE_LONG = re.compile(r'文長限\s*400\s*字以內（至多\s*19\s*行）')
SCORE = re.compile(r'（占\s*(\d+)\s*分）')
TITLE = re.compile(r'請以「[^」]{2,30}」為題')
MATERIAL_REFERENCE = re.compile(r'上文|上述|甲、乙|甲乙二文|二文|本文|依據.{0,4}文|根據.{0,4}文')
AFFECTIVE_CUE = re.compile(r'書寫|抒發|敘述|描述|體悟|感思|感受|想像|經驗|見聞|省思|回應|看待')
ATTRIBUTION = re.compile(r'[（(](?:圖文)?(?:改寫自|節錄自|摘錄自|摘自|譯自|取材自)[^）)]*[《〈][^）)]*[）)]')
SELF_WRITTEN = re.compile(r'自擬|自撰|編者撰|命題所設|虛構案例|情境模擬|模型生成')
TASK_SPLIT = re.compile(r'請分項回答下列問題|請回答下列問題|問題（一）')


def _cjk(text: str) -> int:
    return len(re.findall(r'[一-鿿]', text))


def _material(prompt: str, stimulus: str) -> str:
    """The printed reading material: group_stimulus, else the prompt before the task line."""
    if stimulus.strip():
        return stimulus
    return TASK_SPLIT.split(prompt, maxsplit=1)[0]


def validate_exam(exam: dict[str, Any]) -> list[str]:
    metadata = exam.get('metadata') or {}
    if (metadata.get('paper_subject') or metadata.get('subject')) != '國寫':
        return []
    questions = [q for q in exam.get('questions') or [] if isinstance(q, dict)]
    errors: list[str] = []
    by_number: dict[int, list[dict]] = {}
    for q in questions:
        if isinstance(q.get('number'), int):
            by_number.setdefault(q['number'], []).append(q)
    if sorted(by_number) != [1, 2]:
        errors.append(f'國寫須恰有兩大題（一、二），目前題號 {sorted(by_number)}')
        return errors
    task_one = sorted(by_number[1], key=lambda q: str(q.get('subpart_id') or ''))
    task_two = by_number[2]
    text_one = '\n'.join(str(q.get('prompt') or '') for q in task_one)
    text_two = '\n'.join(str(q.get('prompt') or '') for q in task_two)
    material_one = _material(str(task_one[0].get('prompt') or ''), str(task_one[0].get('group_stimulus') or ''))
    material_two = _material(str(task_two[0].get('prompt') or ''), str(task_two[0].get('group_stimulus') or ''))

    # 第一大題: 80字/4分 + 400字/21分 in every official year.
    if len(task_one) != 2:
        errors.append(f'國寫第一大題須為問題（一）與問題（二）兩個子題（官方 111–115 每年如此），目前 {len(task_one)} 個')
    if not TASK_ONE_SHORT.search(text_one):
        errors.append('國寫問題（一）須印「文長限80字以內（至多4行）」（官方 111–115 逐字相同）')
    if not TASK_ONE_LONG.search(text_one):
        errors.append('國寫問題（二）須印「文長限400字以內（至多19行）」（官方 111–115 逐字相同）')
    scores_one = [int(s) for s in SCORE.findall(text_one)]
    if scores_one != [4, 21]:
        errors.append(f'國寫第一大題配分須依序印（占4分）、（占21分），目前 {scores_one}')
    declared = [q.get('score') for q in task_one]
    if len(task_one) == 2 and declared != [4, 21]:
        errors.append(f'國寫第一大題 score 須為 4 與 21，目前 {declared}')
    first_prompt = re.split(r'問題（二）', text_one)[0]
    first_task = first_prompt.split('問題（一）')[-1] if '問題（一）' in first_prompt else ''
    if not MATERIAL_REFERENCE.search(first_task):
        errors.append('國寫問題（一）須要求依據上文／甲、乙二文作答（閱讀統整，官方 111–115 每年如此）')
    cjk_one = _cjk(material_one)
    if not TASK_ONE_MATERIAL_CJK[0] <= cjk_one <= TASK_ONE_MATERIAL_CJK[1]:
        errors.append(f'國寫第一大題材料 {cjk_one} 字，官方 111–115 為 331–606 字（允許 {TASK_ONE_MATERIAL_CJK[0]}–{TASK_ONE_MATERIAL_CJK[1]}）')

    # 第二大題: 25分 titled 情意 essay.
    if len(task_two) != 1:
        errors.append(f'國寫第二大題須為單一題（占25分），目前 {len(task_two)} 個子題')
    if SCORE.findall(text_two) not in ([], ['25']):
        errors.append(f'國寫第二大題配分須為（占25分），目前 {SCORE.findall(text_two)}')
    if task_two[0].get('score') != 25:
        errors.append(f'國寫第二大題 score 須為 25，目前 {task_two[0].get("score")}')
    if not TITLE.search(text_two):
        errors.append('國寫第二大題須印「請以「題目」為題」（官方 111–115 每年皆有命題）')
    task_two_prompt = text_two.split('請回答下列問題')[-1]
    if not AFFECTIVE_CUE.search(task_two_prompt):
        errors.append('國寫第二大題須為情意寫作：要求書寫經驗、感受、體悟或想像，不是第二篇知性論述')
    cjk_two = _cjk(material_two)
    if not TASK_TWO_MATERIAL_CJK[0] <= cjk_two <= TASK_TWO_MATERIAL_CJK[1]:
        errors.append(f'國寫第二大題材料 {cjk_two} 字，官方 111–115 為 226–443 字（允許 {TASK_TWO_MATERIAL_CJK[0]}–{TASK_TWO_MATERIAL_CJK[1]}）')

    # Materials: attributed, 白話, never self-written.
    if not ATTRIBUTION.search(material_one) and not ATTRIBUTION.search(material_two):
        errors.append('國寫兩大題材料至少一篇須緊接正文印出（改寫自 作者《書名》／〈篇名〉）；官方 111–115 每年如此')
    for label, material in (('第一大題', material_one), ('第二大題', material_two)):
        if is_classical(material):
            errors.append(f'國寫{label}材料為文言；官方 111–115 國寫材料皆為白話（論述、報導、對話、散文、新詩、圖文）')
        if SELF_WRITTEN.search(material):
            errors.append(f'國寫{label}材料標示自擬／虛構；材料須改寫自可查證的已出版文本')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exam_json', type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam_json.read_text(encoding='utf-8-sig'))
    errors = validate_exam(exam)
    for error in errors:
        print(f'FAIL: {error}')
    if not errors:
        print('PASS: 國寫 printed-form contract (ROC 111–115)')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
