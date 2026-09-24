"""國寫 第一大題's questions print on one page (a hosted W116A booklet left 問題（一） at the foot of
page 2 and 問題（二） on page 3); its reading material may still continue on the next page, and the
第二大題 essay task may run on."""
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import run_hosted_workflow as workflow

SENTENCE = '近年來，許多國家開始限制學生在校使用手機，研究團隊比較了限制型與寬鬆型學校的學生在校使用時間、睡眠與成績。'
DIRECTION = '說明：本部分共有二大題，各題配分標於題末。請依各題指示作答，答案必須寫在「答題卷」上。'


def paper(paragraphs, extra=0):
    material = '\n\n'.join([SENTENCE * 4] * paragraphs) + SENTENCE * extra + '（改寫自某研究〈學校手機政策〉）'
    questions = [
        {'id': 'q1-1', 'number': 1, 'subpart_id': '1', 'type': 'guided_writing', 'score': 4, 'number_display': '一、',
         'prompt': material + '\n\n請分項回答下列問題：\n問題（一）：請根據上文，說明兩項研究評估結果出現差異的原因。文長限80字以內（至多4行）。（占4分）'},
        {'id': 'q1-2', 'number': 1, 'subpart_id': '2', 'type': 'guided_writing', 'score': 21, 'number_display': '',
         'prompt': '問題（二）：有人主張學校不必限制學生在校使用手機。你是否同意這個主張？請提出你的看法並說明理由。'
                   '文長限400字以內（至多19行）。（占21分）'},
        {'id': 'q2', 'number': 2, 'type': 'guided_writing', 'score': 25, 'number_display': '二、',
         'prompt': '\n\n'.join([SENTENCE * 3] * 3) + '\n\n請以「陌生人留下的痕跡」為題，寫一篇完整的文章。（占25分）'},
    ]
    return {'metadata': {'subject': '國寫'}, 'questions': questions,
            'sections': [{'id': 'w', 'title': '非選擇題（共二大題，占50分）', 'instructions': [DIRECTION]}],
            'answers': [{'question_id': q['id'], 'final_answer': '評分說明', 'reasoning': ['評分要點']} for q in questions]}


def page_of(pdf, prefix):
    return next(n for n, page in enumerate(pdf, 1) if any(
        ''.join(s['text'] for s in line['spans']).replace(' ', '').startswith(prefix)
        for block in page.get_text('dict')['blocks'] for line in block.get('lines', [])))


# Material lengths that left 問題（二） alone on page 2 before the fix, and two either side.
@pytest.mark.parametrize('paragraphs,extra', [(3, 6), (3, 7), (3, 8), (4, 3), (4, 5)])
def test_first_part_questions_share_a_page(tmp_path, paragraphs, extra):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec, _ = workflow.project_specs(paper(paragraphs, extra), {}, 459.7)
    hb.render(spec, tmp_path / 'q.pdf', tmp_path / 'q.json', font, asset_root=tmp_path, kai_font=font,
              balance_last_page=False)
    with pymupdf.open(tmp_path / 'q.pdf') as pdf:
        ask, first, second = page_of(pdf, '請分項回答'), page_of(pdf, '問題（一）'), page_of(pdf, '問題（二）')
        material = page_of(pdf, SENTENCE[:10])
    assert ask == first == second
    assert material <= first


def test_only_the_material_and_the_single_task_part_may_split():
    spec, _ = workflow.project_specs(paper(4), {}, 459.7)
    blocks = {b['id']: b for b in spec['blocks'] if b.get('id')}
    assert blocks['q1-1']['split'] == 'paragraphs' and blocks['q1-1']['split_keep_tail'] == 1  # 「請分項回答…問題（一）…」
    assert blocks['q1-1']['keep_with_next'] and not blocks['q1-2'].get('keep_with_next')
    assert blocks['q2']['split'] == 'paragraphs' and 'split_keep_tail' not in blocks['q2']
