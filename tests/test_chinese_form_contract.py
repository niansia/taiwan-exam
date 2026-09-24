"""The 國綜 printed-form contract measured on ROC 111-115; fixtures are synthetic."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import hosted_subject_gates as gates
import run_hosted_workflow as workflow
from answer_key_patterns import answer_pattern_errors
from validate_chinese_layout_contract import OFFICIAL_HEADINGS, validate_exam as chinese_layout
from test_hosted_subject_gates import keyed
import pytest
import validate_chinese_layout_contract as contract


@pytest.fixture(autouse=True)
def no_official_fingerprints(monkeypatch, request):
    """The shape fixtures quote official 111–115 passages on purpose; only the overlap test checks them."""
    if 'official_passage' not in request.node.name:
        monkeypatch.setattr(contract, 'FINGERPRINTS', Path('missing-fingerprints.json'))
        monkeypatch.setattr(contract, '_fingerprints', {})


def test_reused_official_passage_is_rejected():
    # 114's 30–31 passage (〈晚遊六橋待月記〉), reprinted by a hosted 116 paper at the same position.
    text = ('然杭人遊湖，止午、未、申三時；其實湖光染翠之工，山嵐設色之妙，皆在朝日始出，夕舂未下，始極其濃媚。'
            '月景尤不可言，花態柳情，山容水意，別是一種趣味。此樂留與山僧、遊客受用，安可為俗士道哉！')
    assert contract.official_overlap(text) == ['114']
    assert contract.official_overlap('完全新寫的一段材料，' * 8) == []


def chinese_paper():
    questions, answers = [], []
    prompts = {1: '下列「」內的字，讀音前後相同的是：', 2: '下列文句，完全沒有錯別字的是：',
               3: '下列文句畫底線處的詞語，運用最適當的是：', 5: '下列是一段古文，依據文意，甲、乙、丙、丁排列順序最適當的是：',
               7: '關於①、②是否符合上文內容，最適當的研判是：',
               22: '關於這首詩的寫法，敘述最適當的是：',
               25: '下列各組「」內的詞，意義前後相同的是：', 26: '下列文句畫底線的詞語，運用適當的是：',
               29: '下列文句中的「以」，表示目的的是：'}
    groups = {6: '閱讀材料一', 7: '閱讀材料一', 8: '閱讀材料一', 9: '閱讀材料二', 10: '閱讀材料二',
              11: '閱讀材料三', 12: '閱讀材料三', 13: '閱讀材料四', 14: '閱讀材料四', 15: '閱讀材料五',
              16: '閱讀材料五', 17: '閱讀材料五', 18: '閱讀材料六', 19: '閱讀材料六', 20: '閱讀材料七',
              21: '閱讀材料七', 22: '杜甫〈觀打魚歌〉與注解', 23: '杜甫〈觀打魚歌〉與注解', 24: '杜甫〈觀打魚歌〉與注解',
              30: '甲、論表；乙、出師表', 31: '甲、論表；乙、出師表'}
    for n in range(1, 32):
        kind = 'multiple_choice' if 25 <= n <= 31 else 'single_choice'
        labels = 'ABCDE' if kind == 'multiple_choice' else 'ABCD'
        q = {'id': f'q{n}', 'number': n, 'section_id': 'single' if n <= 24 else 'multi', 'type': kind,
             'prompt': prompts.get(n, f'依據上文，敘述最適當的是（第{n}題）：'),
             'options': [{'label': l, 'text': f'選項{n}{l}'} for l in labels]}
        if n == 1:  # the official shape: two different look-alike characters, one per phrase
            q['options'] = [{'label': 'A', 'text': '既瘖且「痺」／彈箏搏「髀」'}, {'label': 'B', 'text': '不「忮」不求／「庋」藏字畫'},
                            {'label': 'C', 'text': '「攢」蹙累積／踰牆「鑽」穴'}, {'label': 'D', 'text': '「剜」肉補瘡／壯士斷「腕」'}]
        if n in groups:  # official group material always prints its source
            q['group_stimulus'] = groups[n] + '（改寫自某作者〈某篇〉；另見《某書》）'
        if n in (6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 22, 23, 24, 30, 31):  # 文言 groups keep the classical share at the floor
            q['group_stimulus'] = ('蝜蝂者，善負小蟲也。行遇物，輒持取，卬其首負之。背愈重，雖困劇不止也。其背甚澀，物積因不散，卒躓仆不能起。'
                                   '人或憐之，為去其負，苟能行，又持取如故。又好上高，極其力不已，至墜地死。今世之嗜取者，遇貨不避，以厚其室，不知為己累也。'
                                   + groups[n] + '（改寫自柳宗元〈蝜蝂傳〉；另見《某書》）')
        if n == 2:  # 18-23 character sentences, one hidden 錯別字 each
            q['options'] = [{'label': l, 'text': f'面對突如其來的質疑，他仍神色自若，逐一釐清原委{l}。'} for l in 'ABCD']
        if n == 7:  # the official ①②研判 option set
            q['options'] = [{'label': 'A', 'text': '①、②皆符合'}, {'label': 'B', 'text': '①符合，②不符合'},
                            {'label': 'C', 'text': '①不符合，②無法判斷'}, {'label': 'D', 'text': '①無法判斷，②符合'}]
        questions.append(q)
        answers.append({'question_id': q['id'], 'final_answer': 'B' if kind == 'single_choice' else 'A、C',
                        'reasoning': [f'選項{n}B 依據第二段證據成立。']})
    mixed = ('甲、回憶一直是文學重要的題材和主題。在書寫回憶的文學作品裡，一般關注的是追憶的內容、方式以及其中的自我。沒有記憶，我們就不知道自己是誰，'
             '過去曾是什麼，未來又將有什麼樣的發展。（改寫自某作者〈某篇〉）\n乙、琦君〈髻〉：母親年輕的時候，一把青絲梳一條又粗又長的辮子。\n'
             '丙、李煜〈浪淘沙〉：簾外雨潺潺，春意闌珊。羅衾不耐五更寒。夢裡不知身是客，一晌貪歡。獨自莫憑欄，無限江山，別時容易見時難。流水落花春去也，天上人間。')
    for n, kind, score, text in ((32, 'constructed_response', 2, '（1）依甲文，乙文屬於哪一種回憶方式？（占2分，作答字數：10字以內。）'),
                                 (32, 'constructed_response', 4, '（2）回憶時會意識到哪些情況？（占4分，作答字數：30字以內。）'),
                                 (33, 'constructed_response', 4, '（1）（占4分，作答字數：40字以內。）'),
                                 (33, 'constructed_response', 4, '（2）（占4分，作答字數：①、②各10字以內。）'),
                                 (34, 'single_choice', 2, '關於丙詞的夢與現實，敘述最適當的是：（占2分，單選題）'),
                                 (35, 'single_choice', 2, '關於①、②是否適當，最適當的研判是：（占2分，單選題）'),
                                 (36, 'constructed_response', 2, '（1）（占2分，作答字數：20字以內。）'),
                                 (36, 'constructed_response', 4, '（2）（占4分，作答字數：30字以內。）')):
        sub = text[1] if text.startswith('（') else None
        q = {'id': f'q{n}-{sub or "s"}', 'number': n, 'section_id': 'mixed', 'type': kind, 'score': score,
             'prompt': text, 'group_stimulus': mixed}
        if sub:
            q['subpart_id'] = '1' if sub == '1' else '2'
            if sub == '1':
                q['number_stem'] = '依據甲、乙文，請回答下列問題：'
        if kind == 'single_choice':
            q['options'] = [{'label': l, 'text': f'選項{n}{l}'} for l in 'ABCD']
        questions.append(q)
        answers.append({'question_id': q['id'], 'final_answer': 'B' if kind == 'single_choice' else '不由自主的回憶',
                        'reasoning': ['依甲文第三段定義判斷。']})
    return {'metadata': {'subject': '國綜', 'paper_subject': '國綜', 'generation_mode': 'full-paper'},
            'sections': [{'id': 'single', 'title': OFFICIAL_HEADINGS[0] + '\n' + OFFICIAL_HEADINGS[1]},
                         {'id': 'multi', 'title': OFFICIAL_HEADINGS[2]}, {'id': 'mixed', 'title': OFFICIAL_HEADINGS[3]}],
            'questions': questions, 'answers': answers}


def test_official_shape_passes_and_gpt_style_defects_are_named():
    assert chinese_layout(chinese_paper()) == []
    paper = chinese_paper()
    paper['sections'] = [{'id': 'single', 'title': '單選題'}, {'id': 'multi', 'title': '多選題'},
                         {'id': 'mixed', 'title': '混合題或非選擇題'}]
    paper['questions'][0].update(prompt='編輯改寫初稿，最主要遵守哪一項原則？', group_stimulus='文物館木箱')
    paper['questions'][1].update(prompt='若另增一句說明，何者最符合？', group_stimulus='文物館木箱')
    for q in paper['questions'][:10]:
        q['options'] = [{'label': str(i), 'text': f'w{i}'} for i in range(1, 5)]
        q['option_layout'] = 'row-4'
    for q in paper['questions'][24:31]:
        q['prompt'] = '關於甲、乙二文，下列敘述哪些適當？（應選3項）'
        q['group_stimulus'] = '甲乙二文'
    errors = chinese_layout(paper)
    for expected in ('第壹部分、選擇題（占76分）', '第1題須為字音題', '第2題須為字形題', '不得與其他題共用題組材料',
                     '選項標記須為(A)(B)(C)(D)', '最多並排兩欄', '不得印「應選n項」', '須為獨立多選題', '文言字義題',
                     '至少2題語文知識題'):
        assert any(expected in e for e in errors), expected
    assert any('chinese-layout' in e for e in gates.subject_gate_errors(paper))


def test_blank_fill_items_quote_a_real_source_and_interleave_two_candidates_per_slot():
    paper = chinese_paper()
    generated = paper['questions'][2]
    generated.update(prompt='下列文句□中，最適合依序填入的選項是：「面對積累多年的檔案，整理者最需要的並不是一次□□的清掃，'
                            '而是願意在細節上反覆□□的耐性；否則看似整齊的目錄，只會把真正重要的線索□□在相似的名稱之下。」',
                     options=[{'label': 'A', 'text': '輕率／斟酌／保留'}, {'label': 'B', 'text': '全面／揣度／標示'},
                              {'label': 'C', 'text': '草率／琢磨／凸顯'}, {'label': 'D', 'text': '徹底／推敲／掩蓋'}])
    errors = chinese_layout(paper)
    assert any('須摘錄真實作品並印出處' in e for e in errors)
    assert any('第1格須恰有兩個候選詞' in e for e in errors)
    official = chinese_paper()
    official['questions'][2].update(
        prompt='依據下文，□□內最適合填入的詞語依序是：',
        group_stimulus='月亮從大大小小的雲朵裡照下來，就像是從厚薄不勻的□□□中滲出來的，滴到柏油路上，濃一塊，淡一塊，'
                       '成了深深淺淺的□□。□□的城市。街上的人都那麼匆匆地趕路，各找各的營養。（聶華苓〈月光•枯井•三腳貓〉）',
        options=[{'label': 'A', 'text': '破海綿／皎潔／貪婪'}, {'label': 'B', 'text': '破海綿／青蒼／貧血'},
                 {'label': 'C', 'text': '舊報紙／青蒼／貪婪'}, {'label': 'D', 'text': '舊報紙／皎潔／貧血'}])
    assert chinese_layout(official) == []
    assert workflow.option_columns(official['questions'][2], '國綜') == 2
    near = json.loads(json.dumps(official))
    near['questions'][2]['options'][1]['text'] = '破海綿／皎潔／貧血'  # differs from A in one slot only
    assert any('只差一格' in e or '須恰有兩個候選詞' in e for e in chinese_layout(near))


def test_measured_difficulty_signals_reject_an_easy_imitation():
    paper = chinese_paper()
    assert chinese_layout(paper) == []
    easy = json.loads(json.dumps(paper))
    for q in easy['questions'][5:24]:  # nineteen reading items with absolutist distractors
        q['options'] = [{'label': 'A', 'text': '這完全與文本無關'}, {'label': 'B', 'text': '作者必然反對一切改變'},
                        {'label': 'C', 'text': '文本合理的一種讀法'}, {'label': 'D', 'text': '所有讀者都只能這樣理解'}]
    errors = chinese_layout(easy)
    assert any('絕對化字眼（完全、必然、唯一、所有、只會…）的比例' in e for e in errors)
    assert any('官方最多 36%' in e for e in errors)
    short = json.loads(json.dumps(paper))
    short['questions'][1]['options'] = [{'label': l, 'text': '河道整治只求立杆見影。'} for l in 'ABCD']
    assert any('字形題每句須至少 16 字' in e for e in chinese_layout(short))
    paired = json.loads(json.dumps(paper))
    paired['questions'][6]['options'] = [{'label': l, 'text': f'①敘述{l}；②敘述{l}'} for l in 'ABCD']
    assert any('多選題把①②寫成成對敘述不算' in e for e in chinese_layout(paired))
    unsourced = json.loads(json.dumps(paper))
    for q in unsourced['questions']:
        if q.get('group_stimulus'):
            q['group_stimulus'] = q['group_stimulus'].replace('（改寫自某作者〈某篇〉；另見《某書》）', '')
    assert any('全卷出處與篇名標記' in e for e in chinese_layout(unsourced))
    declared = json.loads(json.dumps(paper))
    declared['questions'][31]['group_stimulus'] += '（乙選自袁宏道〈滿井遊記〉；甲、丙、丁由編者依題組脈絡撰成。）'
    assert any('編者依題組脈絡撰成' in e for e in chinese_layout(declared))


def test_regulatory_material_is_capped_classical_share_has_a_floor_and_dingbats_are_rejected():
    from validate_chinese_layout_contract import is_classical
    assert is_classical('蝜蝂者，善負小蟲也。行遇物，輒持取，卬其首負之。背愈重，雖困劇不止也。其背甚澀，物積因不散，卒躓仆不能起。人或憐之，為去其負。')
    assert not is_classical('把主要靠口說流傳的語言寫成漢字，難處不在找不到字，而在同一個詞往往有幾種寫法可以主張。')
    paper = chinese_paper()
    assert not any('法條、辦法、手冊' in e for e in chinese_layout(paper))
    civics = json.loads(json.dumps(paper))
    labels = {'閱讀材料三': '著作權法第六十五條規定合理使用的四項基準', '閱讀材料六': '教育部《重訂標點符號手冊》修訂版規定引號',
              '閱讀材料七': '鄉鎮市區公所的調解是訴訟的前置程序'}
    for q in civics['questions']:
        for key, text in labels.items():
            if q.get('group_stimulus', '').startswith(key):
                q['group_stimulus'] = text + q['group_stimulus']
    errors = chinese_layout(civics)
    assert any('3 組材料取自法條、辦法、手冊、辭典條目' in e for e in errors)
    modern = json.loads(json.dumps(paper))
    for q in modern['questions']:
        if '蝜蝂' in q.get('group_stimulus', ''):
            q['group_stimulus'] = '把主要靠口說流傳的語言寫成漢字，難處不在找不到字，而在同一個詞往往有幾種寫法可以主張。' + q['group_stimulus'][-40:]
    assert any('以文言／古典材料命題者僅' in e for e in chinese_layout(modern))
    dingbat = json.loads(json.dumps(paper))
    dingbat['questions'][6]['prompt'] = '關於➀、➁是否符合上文內容，最適當的研判是：'
    assert any('dingbat 圈號' in e for e in chinese_layout(dingbat))


def test_part_two_materials_must_pair_modern_framing_with_classical_texts():
    from validate_chinese_layout_contract import part_two_material_errors
    assert chinese_layout(chinese_paper()) == []
    all_classical = ('甲、古之學者必有師。師者，所以傳道、受業、解惑也。人非生而知之者，孰能無惑？惑而不從師，其為惑也，終不解矣。（節錄自韓愈〈師說〉）\n'
                     '乙、學然後知不足，教然後知困。知不足，然後能自反也；知困，然後能自強也。故曰：教學相長也。（節錄自《禮記·學記》）\n'
                     '丙、人生小幼，精神專利，長成已後，思慮散逸，固須早教，勿失機也。吾七歲時，誦靈光殿賦，至於今日，十年一理，猶不遺忘。（節錄自《顏氏家訓·勉學》）')
    errors = part_two_material_errors(all_classical)
    assert len(errors) == 1 and '皆為文言，變成純文言閱讀' in errors[0]
    all_modern = ('甲、回憶一直是文學重要的題材和主題。在書寫回憶的文學作品裡，一般關注的是追憶的內容、方式以及其中的自我。沒有記憶，我們就不知道自己是誰。\n'
                  '乙、長期記憶分布在腦內各處，不像短期記憶一樣分布在某個專屬區域。因此，人不會突如其來地完全忘記某件事，而是在時光流逝中逐漸失去細節。')
    assert any('皆為白話' in e for e in part_two_material_errors(all_modern))
    assert any('分不出篇章' in e for e in part_two_material_errors('一段沒有標示的材料。'))
    paper = chinese_paper()
    for q in paper['questions']:
        if q['number'] >= 32:
            q['group_stimulus'] = all_classical
    assert any('純文言閱讀' in e for e in chinese_layout(paper))


def test_item_one_pairs_two_different_lookalike_characters_and_short_options_share_rows():
    paper = chinese_paper()
    # A generated paper tested one character's two readings; the official item never does.
    paper['questions'][0]['options'] = [{'label': 'A', 'text': '舉酒「屬」客／有良田美池桑竹之「屬」'},
                                        {'label': 'B', 'text': '陟罰臧「否」／「否」則前功盡棄'},
                                        {'label': 'C', 'text': '不「復」出焉／「復」興舊業'},
                                        {'label': 'D', 'text': '惑而不「從」師／舉止「從」容'}]
    errors = chinese_layout(paper)
    assert sum('引號內兩字相同' in e for e in errors) == 4
    assert any('三至六字' in e for e in errors)  # 有良田美池桑竹之「屬」 is a nine-character half
    paper['questions'][0]['options'][0]['text'] = '既瘖且痺／彈箏搏髀'
    assert any('每邊各引一個字' in e for e in chinese_layout(paper))
    # Column rule measured on 111-115: four options of at most 16 characters share rows two abreast.
    short = [{'label': l, 'text': '既瘖且「痺」／彈箏搏「髀」'} for l in 'ABCD']
    assert workflow.option_columns({'options': short}, '國綜') == 2
    assert workflow.option_columns({'options': [{'label': l, 'text': '這是一個超過十六個字的長選項，官方會讓它自成一行印出'} for l in 'ABCD']}, '國綜') == 1
    assert workflow.option_columns({'options': [{'label': l, 'text': '短選項'} for l in 'ABCDE']}, '國綜') == 1
    long_grid = chinese_paper()
    long_grid['questions'][2]['options'] = [{'label': l, 'text': '這是一個超過十六個字的長選項，官方會讓它自成一行印出'} for l in 'ABCD']
    long_grid['questions'][2]['option_layout'] = 'grid-2'
    assert any('選項過長或為五選項' in e for e in chinese_layout(long_grid))


def test_yearly_fixtures_and_part_two_shape_are_required():
    paper = chinese_paper()
    for q in paper['questions']:
        if q['number'] in (7, 35):
            q['prompt'] = '依據上文，敘述最適當的是：'
        if q['number'] in (26, 3):
            q['prompt'] = '依據上文，敘述最適當的是：'
    errors = chinese_layout(paper)
    assert any('研判題' in e for e in errors) and any('成語' in e for e in errors)
    paper = chinese_paper()
    paper['questions'] = [q for q in paper['questions'] if q['id'] != 'q34-s'] + [
        {'id': 'q34-x', 'number': 34, 'section_id': 'mixed', 'type': 'constructed_response', 'score': 6,
         'prompt': '（1）（占6分，作答字數：80字以內。）', 'group_stimulus': '甲、回憶文學論述；乙、琦君〈髻〉；丙、李煜〈浪淘沙〉'}]
    errors = chinese_layout(paper)
    assert any('恰好2題單選子題' in e for e in errors) and any('2分或4分' in e for e in errors)
    paper = chinese_paper()
    for q in paper['questions']:
        if q['id'] == 'q36-2':
            q['prompt'] = '（2）（占4分，作答字數：80字以內。）'
    assert any('30至40字' in e for e in chinese_layout(paper))


def test_rotated_keys_that_never_repeat_a_neighbour_are_suspect():
    q, a = keyed(list('132421431243241324312431'), labels='1234')
    rotated = {'metadata': {'subject': '國綜', 'generation_mode': 'full-paper'}, 'questions': q, 'answers': a}
    assert any('never repeat a position' in e for e in answer_pattern_errors(rotated))
    q, a = keyed(list('BBDACCABDDBADCAABCDDBCAB'))
    natural = {'metadata': {'subject': '國綜', 'generation_mode': 'full-paper'}, 'questions': q, 'answers': a}
    assert not any('never repeat' in e for e in answer_pattern_errors(natural))


def test_style_floors_measured_on_111_115():
    options = lambda n: [{'label': l, 'text': '短' if l != 'A' else '這是最長而且最周全的正確選項敘述'} for l in 'ABCD']
    questions = [{'id': f'q{n}', 'number': n, 'type': 'single_choice', 'prompt': '下列敘述最適當的是：', 'options': options(n)}
                 for n in range(1, 11)]
    questions[0]['prompt'] = '下列敘述何者最適當？'
    questions[1]['prompt'] = '依『導讀』所述，➀與➁皆正確的是：'
    questions[2]['group_stimulus'] = '甲、一段文字。（本段為命題者設計的假設情境）'
    questions.append({'id': 'w', 'number': 32, 'type': 'constructed_response', 'prompt': '（1）說明。（占2分，作答字數：15字以內。）'})
    answers = [{'question_id': f'q{n}', 'final_answer': 'A'} for n in range(1, 11)]
    answers.append({'question_id': 'w', 'final_answer': '略', 'explanation': '答出一點得1分'})
    errors = contract.printed_style_errors({'answers': answers}, questions)
    for expected in ('以「？」作結', '➀➁', '『』作為第一層引號', '命題說明', '唯一最長選項', '1 分級距'):
        assert any(expected in e for e in errors), expected
