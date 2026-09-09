import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('overlap', Path(__file__).resolve().parents[1]/'scripts/audit_corpus_overlap.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_mask_numbers_preserves_english_semantics():
    assert audit.normalize('The samples increased by 24.', True) != audit.normalize('The prices decreased by 24.', True)
    assert audit.normalize('平均數為１２', True) == audit.normalize('平均數為27', True)


def test_same_group_does_not_trigger_duplicate_stimulus():
    s = '資料包含三個不同時期的公共衛生制度與登記單位。'*5
    exam = {'questions':[{'number':n, 'prompt':f'問題{n}', 'group_stimulus':s} for n in (48,49,50)]}
    assert audit.internal_review(exam) == []
    r = audit.records(exam, 'exam.json')
    assert len(r) == 1 and r[0]['locator'] == [48,49,50]


def test_disjoint_groups_are_reported():
    s = '資料包含三個不同時期的公共衛生制度與登記單位。'*5
    exam = {'questions':[{'number':33,'group_stimulus':s}, {'number':36,'prompt':'另一題'}, {'number':48,'group_stimulus':s}]}
    assert audit.internal_review(exam)[0]['groups'] == [[33],[48]]


def test_every_numbered_item_including_late_social_items():
    exam = {'questions':[{'number':65,'prompt':'試比較兩種社會政策實施前後的誘因變化並說明資料可以支持的結論。'}]}
    assert audit.records(exam,'exam.json')[0]['locator'] == 65


def test_no_answers_or_pass_flags_in_comparison_text():
    q = {'prompt':'Compare the two notices.', 'options':[{'text':'A plausible answer'}],
         'answer':'DO NOT INDEX', 'item_spec':{'reviewer_decision':'pass'}}
    assert audit.item_body(q) == 'Compare the two notices.A plausible answer'
    assert 'DO NOT INDEX' not in audit.item_body(q)


def test_paraphrased_disjoint_stimulus_is_flagged_for_review():
    a = '1915年港口檢疫簿逐船登記到港日出發港旅客症狀隔離人數解除日期。1950年代疫苗宣傳畫沒有逐人接種名冊。2003年醫院接觸者追蹤表記錄接觸時間場所與後續觀察。'
    b = '港口於1915年使用檢疫簿登記到港日出發港旅客症狀隔離人數解除日期。1950年代疫苗宣傳画沒有逐人接種名冊。2003年的醫院接觸者追蹤表記錄接觸時間場所與後續觀察。'
    exam = {'questions':[{'number':33,'group_stimulus':a}, {'number':36}, {'number':48,'group_stimulus':b}]}
    assert any(r['kind']=='similar_stimuli_need_review' for r in audit.internal_review(exam))
