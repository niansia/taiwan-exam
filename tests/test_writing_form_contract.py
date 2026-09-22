"""國寫 printed form measured on ROC 111–115: 80/4 + 400/21, titled 25-point 情意 task, attributed 白話 materials."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import hosted_subject_gates as gates
from validate_writing_layout_contract import validate_exam as writing_form

SENTENCE = '人們習慣使用標籤將複雜的事物簡化、分類，再附上標記，然而有時我們也將標籤使用在人的身上，形成刻板印象。'
LITERARY = '夏天暑熱的午後，廟埕後有一棵巨大的龍眼樹，我從小學翻牆出來，背著書包爬上樹，躲在密密的枝葉裡，聽見蟬聲淹沒了母親的呼喚。'


def paper():
    material_one = SENTENCE * 7 + '（改寫自黃宗慧、黃宗潔《就算牠沒有臉》）'
    material_two = LITERARY * 4 + '（改寫自蔣勳《給青年藝術家的信》）'
    questions = [
        {'id': 'q1-1', 'number': 1, 'subpart_id': '1', 'type': 'guided_writing', 'score': 4, 'number_display': '一、',
         'prompt': material_one + '\n\n請分項回答下列問題：\n問題（一）：依據上文，請說明「標籤」用於人身上的正面與負面作用。文長限80字以內（至多4行）。（占4分）'},
        {'id': 'q1-2', 'number': 1, 'subpart_id': '2', 'type': 'guided_writing', 'score': 21, 'number_display': '',
         'prompt': '問題（二）：日常生活中不乏貼標籤的實例，請寫一篇短文，舉例說明你對標籤現象的看法。文長限400字以內（至多19行）。（占21分）'},
        {'id': 'q2', 'number': 2, 'type': 'guided_writing', 'score': 25, 'number_display': '二、',
         'prompt': material_two + '\n\n請回答下列問題：\n氣味透過嗅覺喚起記憶和感受。請以「花草樹木的氣味記憶」為題，寫一篇文章，書寫你熟悉的花草樹木的氣味，及其所召喚的記憶和感受。（占25分）'},
    ]
    return {'metadata': {'subject': '國寫', 'paper_subject': '國寫', 'generation_mode': 'full-paper'}, 'questions': questions,
            'answers': [{'question_id': q['id'], 'final_answer': '評分說明', 'reasoning': [f'{q["id"]} 評分要點']} for q in questions]}


def test_official_shape_passes():
    assert writing_form(paper()) == []


def test_missing_length_lines_scores_title_and_reference_are_named():
    p = paper()
    p['questions'][0]['prompt'] = p['questions'][0]['prompt'].replace('文長限80字以內（至多4行）。（占4分）', '簡答即可。（占5分）').replace('依據上文，', '')
    p['questions'][1]['prompt'] = '問題（二）：請寫一篇短文。（占20分）'
    p['questions'][2]['prompt'] = LITERARY * 4 + '（改寫自蔣勳《給青年藝術家的信》）\n\n請回答下列問題：\n請分析上文的論證結構並評論其合理性。（占25分）'
    errors = writing_form(p)
    for expected in ('文長限80字以內（至多4行）', '文長限400字以內（至多19行）', '配分須依序印（占4分）、（占21分）', '依據上文／甲、乙二文', '請以「題目」為題', '情意寫作'):
        assert any(expected in e for e in errors), expected


def test_material_length_attribution_and_classical_material_are_measured():
    p = paper()
    p['questions'][0]['prompt'] = SENTENCE * 2 + '\n\n請分項回答下列問題：\n問題（一）：依據上文，請說明作用。文長限80字以內（至多4行）。（占4分）'
    p['questions'][2]['prompt'] = ('蝜蝂者，善負小蟲也。行遇物，輒持取，卬其首負之。背愈重，雖困劇不止也。其背甚澀，物積因不散，卒躓仆不能起。'
                                   '人或憐之，為去其負。苟能行，又持取如故。又好上高，極其力不已，至墜地死。' * 3
                                   + '\n\n請回答下列問題：\n請以「負重」為題，書寫你的經驗與感受。（占25分）')
    errors = writing_form(p)
    assert any('第一大題材料' in e and '331–606' in e for e in errors)
    assert any('至少一篇須緊接正文印出（改寫自' in e for e in errors)
    assert any('第二大題材料為文言' in e for e in errors)
    p = paper()
    p['questions'][2]['prompt'] = p['questions'][2]['prompt'].replace('（改寫自蔣勳《給青年藝術家的信》）', '（本文為命題所設情境）')
    assert any('自擬／虛構' in e for e in writing_form(p))


def test_hosted_gate_accepts_the_three_record_shape_with_both_writing_validators():
    """W116M1 stalled because the form contract wants 問題（一）/（二） records while the
    grounding validator counted records instead of 大題; both now agree on the shape."""
    p = paper()
    p['metadata']['writing_source_pool'] = {
        'selection_policy': {'publisher_neutral': True},
        'sources': [{'source_id': f's{i}', 'source_voice': 'authored_literary_prose', 'source_language': 'zh-Hant',
                     'publisher': f'出版者{i}', 'source_domain': f'領域{i}', 'invented_modelling_values': []} for i in range(1, 9)],
    }
    p['questions'][0]['item_spec'] = {'writing_task_role': 'intellectual_integration', 'source_ids': ['s1'],
                                      'material_source_map': [{'material_id': '本文', 'source_ids': ['s1'], 'supported_claims': ['一項主張']}]}
    p['questions'][2]['item_spec'] = {'writing_task_role': 'affective_expression', 'source_ids': ['s2'],
                                      'material_source_map': [{'material_id': '本文', 'source_ids': ['s2'], 'supported_claims': ['一項主張']}]}
    errors = gates.subject_gate_errors(p)
    assert not any(e.startswith('writing-form: ') or e.startswith('writing: ') for e in errors), errors


def test_hosted_gate_routes_the_writing_form_contract():
    p = paper()
    p['questions'][1]['prompt'] = '問題（二）：請寫一篇短文。（占21分）'
    errors = gates.subject_gate_errors(p)
    assert any(e.startswith('writing-form: ') and '文長限400字以內' in e for e in errors)
    assert json.dumps(errors, ensure_ascii=False)
