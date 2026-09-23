"""Faster repair loops must keep every visual gate: reuse only actual reviews of unchanged items."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_hosted_workflow as workflow
from append_items import append
from compose_hosted_pdf import compose
from hosted_body_templates import render, BLOCK_GRID_PT
from hosted_item_layout import render_signature, equivalent_render
from prepare_hosted_review import bind_layout, density_evidence, item_hashes, projected
from prepare_hosted_run import prepare as preflight
from verify_fixed_template_pdf import DEFAULT_MAP

SECTIONS = [{'id': 's1', 'title': '一、單選題', 'instructions': ['說明：合成測試說明。']},
            {'id': 's2', 'title': '二、選填題', 'instructions': ['說明：合成選填說明。']},
            {'id': 's3', 'title': '三、混合題', 'instructions': ['說明：合成混合題說明。']}]


def synthetic_items(figure):
    """Mechanical layout fixtures only; not exam questions or educational content."""
    questions = [
        {'id': 'q1', 'number': 1, 'section_id': 's1', 'type': 'single_choice', 'score': 5,
         'prompt': '合成版面測試：T<sup>2</sup> = 4 的排版。', 'option_layout': 'grid-2',
         'options': [{'label': f'({i})', 'text': f'合成選項 {i}'} for i in range(1, 6)]},
        {'id': 'q2', 'number': 2, 'section_id': 's1', 'type': 'single_choice', 'score': 5,
         'prompt': '合成版面測試長題幹。' * 8, 'option_layout': 'stack',
         'options': [{'label': f'({i})', 'text': f'合成選項內容 {i}'} for i in range(1, 6)]},
        {'id': 'q3', 'number': 13, 'section_id': 's2', 'type': 'fill_in', 'score': 5,
         'prompt': '合成選填版面：所求為 {{answer}}。',
         'answer_format': {'kind': 'fraction', 'numerator_slots': 1, 'denominator_slots': 2}},
        {'id': 'q4', 'number': 18, 'section_id': 's3', 'type': 'constructed_response', 'score': 4,
         'prompt': '合成圖文版面測試。', 'visual_layout': 'side-right',
         'visual_asset': {'path': figure.name, 'alt': 'synthetic figure', 'width_percent': 30,
                          'sha256': hashlib.sha256(figure.read_bytes()).hexdigest()}},
    ]
    answers = [
        {'question_id': 'q1', 'final_answer': '(2)', 'reasoning': ['合成排版步驟 T<sup>2</sup>。']},
        {'question_id': 'q2', 'final_answer': '(3)', 'reasoning': ['合成排版步驟一。', '合成排版步驟二。']},
        {'question_id': 'q3', 'final_answer': '1/12', 'reasoning': ['合成排版步驟。']},
        {'question_id': 'q4', 'final_answer': '合成要點', 'explanation_blocks': [
            {'type': 'analysis', 'title': '評分要點', 'content': '合成評分排版。'}]},
    ]
    return questions, answers


@pytest.fixture
def run(tmp_path):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    assert preflight('數學A', tmp_path, 'reuse', font,
                     resource_pdf=ROOT / 'web/taiwan-exam-template-resources.pdf')['status'] == 'ready-for-authoring'
    figure = tmp_path / 'figure.svg'
    figure.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="160" height="110">'
                      '<path d="M10 100 L150 10" stroke="black"/><text x="12" y="20" font-size="12">A</text></svg>',
                      encoding='utf-8')
    questions, answers = synthetic_items(figure)
    workflow.save(tmp_path / 'plan.json', {
        'metadata': {'title': '合成版面', 'exam': '學測', 'subject': '數學A',
                     'calibration_level': 'official-structure-only', 'paper_id': 'reuse'},
        'instructions': ['合成版面'], 'sections': SECTIONS})
    workflow.save(tmp_path / 'batch.json', {'questions': questions, 'answers': answers})
    append(tmp_path, tmp_path / 'batch.json', plan=tmp_path / 'plan.json')
    specs = (tmp_path / 'questions-blocks.json', tmp_path / 'solutions-blocks.json')
    assert workflow.specs(tmp_path / 'run-state.json', *specs)['status'] == 'specs-written'
    return tmp_path, font, specs, questions, answers


def crop_keys(report):
    totals, seen = Counter(p['id'] for p in report['parts']), Counter()
    for part in report['parts']:
        seen[part['id']] += 1
        yield part['id'] if totals[part['id']] == 1 else f"{part['id']}#{seen[part['id']]}"


def review_all(root, state_path, status='pass'):
    notes = {}
    for role, bundle in workflow.read(state_path)['pdfs'].items():
        items = workflow.read(root / bundle['item_review']['path'])
        scan = workflow.read(root / bundle['inspection']['path'])
        rows = {r['page']: r for r in workflow.read(root / bundle['visual_review']['path'])['pages']}
        pages = {}
        for page in scan['pages']:
            note = {'status': status, 'observations': f'Synthetic reviewer opened page {page["page"]}'}
            evidence = rows[page['page']].get('density_evidence') or {}
            if 'large-bottom-void-review' in page['issues'] and evidence.get('embedded_references'):
                note['issue_dispositions'] = {'large-bottom-void-review': {
                    'decision': 'justified', 'reason': 'Synthetic same-role comparison', 'embedded_reference': 0}}
            pages[str(page['page'])] = note
        notes[role] = {'pages': pages, 'items': {key: {'status': status, 'observations': f'Synthetic crop {key}'}
                                                 for key in crop_keys(items)}}
    workflow.save(root / 'notes.json', notes)
    return workflow.record_review(root / 'notes.json', state=state_path)


def statuses(root, state_path):
    result = {}
    for role, bundle in workflow.read(state_path)['pdfs'].items():
        items = workflow.read(root / bundle['item_review']['path'])['parts']
        result[role] = {part['id']: part['status'] for part in items}
    return result


def test_specs_are_a_projection_of_saved_content(run):
    root, _, (question_spec, solution_spec), questions, answers = run
    blocks = workflow.read(question_spec)['blocks']
    assert [b['kind'] for b in blocks] == ['section', 'choice', 'choice', 'section', 'fill', 'section', 'constructed']
    assert blocks[1]['text'] == {'rich': questions[0]['prompt']} and blocks[1]['columns'] == 2
    assert blocks[4]['rows'] == [1, 2] and blocks[6]['figure_position'] == 'right'
    solutions = workflow.read(solution_spec)['blocks']
    assert [b['text'] for b in solutions if b['kind'] == 'solution'][0] == '答案：(2)'
    assert solutions[-1]['steps'] == ['評分要點：合成評分排版。']
    # Printed text only comes from exam.json: a layout projection adds no content.
    printed = json.dumps([workflow.read(question_spec), workflow.read(solution_spec)], ensure_ascii=False)
    for question in questions:
        assert json.dumps(question['prompt'], ensure_ascii=False)[1:-1] in printed


def test_projection_refuses_ambiguous_layout_and_hand_edits(run):
    root, font, (question_spec, solution_spec), questions, answers = run
    state = root / 'run-state.json'
    broken = copy.deepcopy(questions[2])
    broken.pop('answer_format')  # No declared rail geometry: never guessed.
    workflow.save(root / 'batch.json', {'questions': [broken], 'answers': [answers[2]]})
    append(root, root / 'batch.json', replace=True)
    with pytest.raises(ValueError, match='answer_format'):
        workflow.specs(state, question_spec, solution_spec)
    # A spec generated for an older exam cannot be rendered as current content.
    with pytest.raises(ValueError, match='predates'):
        workflow.proof(state, question_spec, solution_spec, 'q1', font, root / 'proof-stale')
    edited = workflow.read(question_spec)
    edited['blocks'][1]['columns'] = 5
    workflow.save(question_spec, edited)
    workflow.save(root / 'batch.json', {'questions': [questions[2]], 'answers': [answers[2]]})
    append(root, root / 'batch.json', replace=True)
    with pytest.raises(ValueError, match='hand-written layout'):
        workflow.specs(state, question_spec, solution_spec)
    workflow.save(root / 'hints.json', {'items': {'q1': {'columns': 5}}})
    question_spec.unlink()
    workflow.specs(state, question_spec, solution_spec, hints=root / 'hints.json')
    assert workflow.read(question_spec)['blocks'][1]['columns'] == 5


def test_proof_reviews_carry_into_final_booklets_but_pages_still_need_review(run):
    root, font, specs, questions, _ = run
    state = root / 'run-state.json'
    proof = workflow.proof(state, *specs, ','.join(q['id'] for q in questions), font, root / 'proof-01')
    assert proof['status'] == 'proof-review-pending' and proof['reviews_approved_by_tool'] is False
    # One viewing call per batch: up to six crops, an item's own crops together.
    for batch in proof['review_batches']:
        assert 0 < len(batch['images']) <= workflow.REVIEW_BATCH_IMAGES
        assert len(batch['record_as']) == len(batch['images'])
        assert all(Path(image).is_file() for image in batch['images'])
    assert sum(len(batch['images']) for batch in proof['review_batches']) == len(proof['review_queue'])
    assert len(proof['review_batches']) < len(questions)  # not one call per item
    notes = {}
    for role in ('question', 'solution'):
        report = workflow.read(root / 'proof-01' / f'{role}-items.json')
        notes[role] = {'items': {key: {'status': 'pass', 'observations': f'Synthetic proof crop {key}'}
                                 for key in crop_keys(report)}}
    notes['question']['items']['q2'] = {'status': 'fail', 'observations': 'Synthetic defect finding'}
    workflow.save(root / 'proof-notes.json', notes)
    workflow.record_review(root / 'proof-notes.json', proof=root / 'proof-01')
    # A later proof of the same unchanged items re-queues only the crop with a recorded
    # defect; every passed crop stays locked (hosted runs re-viewed them in each proof).
    again = workflow.proof(state, *specs, ','.join(q['id'] for q in questions), font, root / 'proof-02')
    assert len(again['review_queue']) == 1 and again['review_batches'][0]['items'] == ['q2']
    assert sum(c['pixel-identical'] + c['vector-equivalent'] for c in again['retained_reviews'].values()) > 0
    # Only a proof with no new or changed item counts against the budget.
    assert proof['iteration_budget']['repeat_proofs'] == []
    assert again['iteration_budget']['repeat_proofs'] == ['proof-02'] and not again['iteration_budget']['over_budget']
    third = workflow.proof(state, *specs, ','.join(q['id'] for q in questions), font, root / 'proof-03')
    assert third['iteration_budget']['over_budget'] and third['iteration_budget']['unchanged_item_appearances'] == 2 * len(questions)
    workflow.content_lock(state)
    built = workflow.build(state, *specs, font, root / 'build-v1', year=116)
    assert built['reviews_approved_by_tool'] is False
    found = statuses(root, Path(built['state']))
    # A recorded defect on an equivalent rendering is never replaced by a pass.
    assert found['question']['q2'] == 'pending'
    assert all(status == 'pass' for qid, status in found['question'].items() if qid != 'q2')
    assert set(found['solution'].values()) == {'pass'}
    queue = built['review_queue']
    assert len(queue['question']['items']) == 1 and queue['question']['pages'] and queue['solution']['pages']
    review = workflow.read(root / workflow.read(Path(built['state']))['pdfs']['question']['visual_review']['path'])
    assert all(row['status'] == 'pending' for row in review['pages'])


def test_reflow_after_repair_keeps_only_unchanged_item_reviews(run):
    root, font, specs, questions, answers = run
    workflow.content_lock(root / 'run-state.json')
    built = workflow.build(root / 'run-state.json', *specs, font, root / 'build-v1', year=116)
    first_state = Path(built['state'])
    review_all(root, first_state)
    longer = copy.deepcopy(questions[0])
    longer['prompt'] += '（修訂後加長的合成題幹，讓後續題塊下移。）' * 3
    workflow.save(root / 'batch.json', {'questions': [longer], 'answers': [answers[0]]})
    append(root, root / 'batch.json', replace=True, state=first_state)
    workflow.specs(first_state, *specs)
    workflow.content_lock(first_state, reason='test repair')
    repaired = workflow.build(first_state, *specs, font, root / 'build-v2', year=116)
    found = statuses(root, Path(repaired['state']))
    for role in ('question', 'solution'):
        assert found[role]['q1'] == 'pending'
        assert all(status == 'pass' for qid, status in found[role].items() if qid != 'q1')
    assert repaired['retained_actual_reviews']['parts'] == 6
    state = workflow.read(Path(repaired['state']))
    parts = workflow.read(root / state['pdfs']['question']['item_review']['path'])['parts']
    first_page = next(p['page'] for p in parts if p['id'] == 'q1')
    pages = workflow.read(root / state['pdfs']['question']['visual_review']['path'])['pages']
    assert next(r for r in pages if r['page'] == first_page)['status'] == 'pending'
    assert all('unchanged authored item' in p['review_basis'] for p in parts if p['status'] == 'pass')


def test_changed_item_record_is_not_retained_even_with_identical_pixels(run):
    root, font, specs, questions, answers = run
    workflow.content_lock(root / 'run-state.json')
    built = workflow.build(root / 'run-state.json', *specs, font, root / 'build-v1', year=116)
    first_state = Path(built['state'])
    review_all(root, first_state)
    # The printed spec is kept hand-written and unchanged while the saved item
    # changes: a crop that still matches cannot vouch for different content.
    for path in specs:
        spec = workflow.read(path)
        for key in ('generated_by', 'exam_sha256', 'hints', 'blocks_sha256'):
            spec.pop(key)
        workflow.save(path, spec)
    revised = copy.deepcopy(answers[3])
    revised['explanation_blocks'][0]['content'] = '修訂後的合成評分排版。'
    workflow.save(root / 'batch.json', {'questions': [questions[3]], 'answers': [revised]})
    append(root, root / 'batch.json', replace=True, state=first_state)
    workflow.content_lock(first_state, reason='test repair')
    repaired = workflow.build(first_state, *specs, font, root / 'build-v2', year=116)
    found = statuses(root, Path(repaired['state']))
    # Only the solution changed: the question booklet prints no answer, so its crop stays passed.
    assert found['solution']['q4'] == 'pending' and found['question']['q4'] == 'pass'
    assert found['question']['q1'] == 'pass'


def test_record_review_needs_actual_findings_and_refreshes_bindings(run):
    root, font, specs, _, _ = run
    workflow.content_lock(root / 'run-state.json')
    built = workflow.build(root / 'run-state.json', *specs, font, root / 'build-v1', year=116)
    state_path = Path(built['state'])
    for bad in ({'question': {'items': {'q1': {'status': 'pass', 'observations': ' '}}}},
                {'question': {'items': {'q1': {'observations': 'no status'}}}},
                {'question': {'items': {'unknown': {'status': 'pass', 'observations': 'x'}}}},
                {'question': {'pages': {'1': {'status': 'pass', 'observations': 'x',
                              'issue_dispositions': {'answer-rail-format': {'decision': 'justified', 'reason': 'x'}}}}}}):
        workflow.save(root / 'bad.json', bad)
        with pytest.raises(ValueError):
            workflow.record_review(root / 'bad.json', state=state_path)
    result = review_all(root, state_path)
    assert result['reviews_approved_by_tool'] is False
    state = workflow.read(state_path)
    for bundle in state['pdfs'].values():
        for key in ('item_review', 'visual_review', 'inspection'):
            assert workflow.digest(root / bundle[key]['path']) == bundle[key]['sha256']


def test_review_observations_may_be_a_list_of_lines():
    row = {'status': 'pending', 'observations': ''}
    workflow.apply_review(row, {'status': 'pass', 'observations': ['fractions align', ' labels readable ']}, 'q1')
    assert row['observations'] == 'fractions align; labels readable'
    for empty in ([], [' '], ['ok', 3]):
        with pytest.raises(ValueError, match='as text'):
            workflow.apply_review({'status': 'pending'}, {'status': 'pass', 'observations': empty}, 'q1')


def test_review_list_opens_from_anywhere_and_its_template_records_in_one_call(run, monkeypatch, tmp_path_factory):
    root, font, specs, _, _ = run
    workflow.content_lock(root / 'run-state.json')
    built = workflow.build(root / 'run-state.json', *specs, font, root / 'build-v1', year=116)
    monkeypatch.chdir(tmp_path_factory.mktemp('elsewhere'))  # the helper's cwd is not the run
    listed = set()
    for batch in built['review_batches']:
        assert len(batch['record_as']) == len(batch['images'])
        assert all(Path(image).is_absolute() and Path(image).is_file() for image in batch['images'])
        listed |= {(batch['role'], kind, key) for target in batch['record_as'] for kind, key in target.items()}
    template = workflow.read(Path(built['observations_template']))
    assert listed == {(role, kind, key) for role, sections in template.items()
                      for kind, keys in sections.items() for key in keys}
    assert {entry['status'] for sections in template.values() for keys in sections.values()
            for entry in keys.values()} == {'pending'}  # the tool never pre-fills a pass
    for sections in template.values():
        for keys in sections.values():
            for key, entry in keys.items():
                entry.update(status='pass', observations=f'Synthetic reviewer opened {key} at full size')
    workflow.save(root / 'filled.json', template)
    result = workflow.record_review(root / 'filled.json', state=built['state'])
    assert all(not rows['items_pending'] and not rows['pages_pending'] for rows in result['remaining'].values())


def test_density_evidence_lists_only_same_role_embedded_measurements():
    inside = density_evidence('數學A', 'question', 3, 8, 0.30)
    assert inside['status'] == 'within-fixed-limit' and inside['page_role'] == 'body' and inside['limit'] == 0.32
    assert all(r['page_role'] == 'body' and 0.30 <= r['limit'] for r in inside['embedded_references'])
    assert inside['decision'] == 'not-made-by-tool'
    outside = density_evidence('數學A', 'question', 3, 8, 0.5)
    assert outside['status'] == 'exceeds-fixed-limit' and not outside['embedded_references']
    assert density_evidence('數學A', 'solution', 2, 3, 0.5)['page_role'] == 'solutions'
    assert density_evidence('數學A', 'question', 8, 8, 0.5)['page_role'] == 'formula'


def test_blocks_start_and_crop_on_the_review_pixel_grid(tmp_path):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec = json.loads((ROOT / 'templates/hosted-math-a-questions.json').read_text(encoding='utf-8'))
    layout = render(spec, tmp_path / 'body.pdf', tmp_path / 'layout.json', font,
                    asset_root=ROOT / 'templates', proof=True)
    for part in layout['parts']:
        assert all(abs(v / BLOCK_GRID_PT - round(v / BLOCK_GRID_PT)) < 1e-6 for v in part['bbox'])


@pytest.fixture(scope='module')
def composed_gallery(tmp_path_factory):
    """Same placeholder blocks at two vertical positions on real fixed pages."""
    folder = tmp_path_factory.mktemp('signature')
    font = folder / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    record = next(s for s in json.loads(DEFAULT_MAP.read_text(encoding='utf-8'))['subjects'] if s['subject'] == '數學A')
    assets = ROOT / Path(record['assets'][0]['repository_path']).parent
    base = json.loads((ROOT / 'templates/hosted-math-a-questions.json').read_text(encoding='utf-8'))
    results = {}
    for name, filler in (('base', None), ('moved', '合成插入內容。' * 20)):
        spec = copy.deepcopy(base)
        if filler:
            first = next(i for i, b in enumerate(spec['blocks']) if b['kind'] != 'section')
            spec['blocks'].insert(first, {'kind': 'stimulus', 'id': 'layout-inserted', 'text': filler})
        body, layout_path, pdf = folder / f'{name}-body.pdf', folder / f'{name}.json', folder / f'{name}.pdf'
        layout = render(spec, body, layout_path, font, asset_root=ROOT / 'templates', proof=True)
        compose('數學A', body, assets, pdf, year='116', title='版型示範', running_name='學測', font_path=font)
        results[name] = (pdf, bind_layout(body, pdf, layout, 1))
    return results


def test_moved_unchanged_blocks_are_vector_equivalent_on_fixed_pages(composed_gallery):
    base_pdf, base = composed_gallery['base']
    moved_pdf, moved = composed_gallery['moved']
    with pymupdf.open(base_pdf) as first, pymupdf.open(moved_pdf) as second:
        last = {part['id']: part for part in moved['parts']}
        compared = 0
        for part in base['parts']:
            other = last[part['id']]
            if (part['page'], part['bbox']) == (other['page'], other['bbox']):
                continue
            compared += 1
            assert equivalent_render(render_signature(first[part['page'] - 1], part['bbox']),
                                     render_signature(second[other['page'] - 1], other['bbox']))
        assert compared >= 3


@pytest.mark.parametrize('change', ['period', 'superscript', 'minus', 'rail', 'figure', 'intrusion'])
def test_signature_detects_printed_changes(tmp_path, change):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    figure = tmp_path / 'figure.svg'
    figure.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="150" height="100">'
                      '<path d="M5 95 L145 5" stroke="black"/></svg>', encoding='utf-8')
    other = tmp_path / 'other.svg'
    other.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="150" height="100">'
                     '<path d="M5 95 L145 7" stroke="black"/></svg>', encoding='utf-8')

    def signature(block, name, intrude=False):
        spec = {'subject': '數學A', 'blocks': [block]}
        layout = render(spec, tmp_path / f'{name}.pdf', tmp_path / f'{name}.json', font, asset_root=tmp_path)
        with projected(tmp_path / f'{name}.pdf', (594.96, 841.92)) as doc:
            part = layout['parts'][0]
            if intrude:
                box = part['bbox']
                doc[0].draw_rect(pymupdf.Rect(box[0] + 30, box[3] - 3, box[0] + 60, box[3] - 1), fill=(0, 0, 0))
            return render_signature(doc[part['page'] - 1], part['bbox'])

    choice = {'kind': 'choice', 'id': 'q1', 'number': 1, 'text': {'rich': '合成 T<sup>2</sup>，x=1.5，a-b。'},
              'options': [{'label': '(1)', 'text': '甲'}, {'label': '(2)', 'text': '乙'}]}
    fill = {'kind': 'fill', 'id': 'q1', 'number': 13, 'rows': [1, 2], 'text': '合成 {{answer}}。'}
    stimulus = {'kind': 'stimulus', 'id': 'q1', 'text': '合成圖。', 'figure': 'f', 'figure_position': 'right',
                'assets': {'f': {'path': 'figure.svg', 'sha256': hashlib.sha256(figure.read_bytes()).hexdigest(),
                                 'width_pt': 150}}}
    original, changed, intrude = {'period': (choice, {'rich': '合成 T<sup>2</sup>，x=15，a-b。'}, False),
                                  'superscript': (choice, {'rich': '合成 T<sup>3</sup>，x=1.5，a-b。'}, False),
                                  'minus': (choice, {'rich': '合成 T<sup>2</sup>，x=1.5，a−b。'}, False),
                                  'rail': (fill, None, False), 'figure': (stimulus, None, False),
                                  'intrusion': (choice, None, True)}[change]
    revised = copy.deepcopy(original)
    if isinstance(changed, dict):
        revised['text'] = changed
    elif change == 'rail':
        revised['rows'] = [2, 1]
    elif change == 'figure':
        revised['assets']['f'].update(path='other.svg', sha256=hashlib.sha256(other.read_bytes()).hexdigest())
    first = signature(original, 'first')
    assert equivalent_render(first, signature(original, 'again'))
    assert not equivalent_render(first, signature(revised, 'revised', intrude))


def test_item_hash_ignores_review_metadata_but_binds_printed_group():
    exam = {'questions': [{'id': 'a', 'prompt': 'x', 'group_stimulus': 'shared', 'item_spec': {'band': '中'}},
                          {'id': 'b', 'prompt': 'y', 'group_stimulus': 'shared'}],
            'answers': [{'question_id': 'a', 'final_answer': '1', 'independent_review': {'reviewer': 'r'}}]}
    before = item_hashes(exam)
    exam['questions'][0]['item_spec']['band'] = '難'
    exam['answers'][0]['independent_review']['reviewer'] = 'other'
    assert item_hashes(exam) == before
    exam['questions'][1]['prompt'] = 'z'
    after = item_hashes(exam)
    assert after['a'] != before['a'] and after['b'] != before['b']


def test_question_crops_do_not_bind_the_answer():
    """Correcting a solution must not send a passed question crop back to review."""
    exam = {'questions': [{'id': 'a', 'prompt': 'x'}],
            'answers': [{'question_id': 'a', 'final_answer': '1', 'explanation': 'old'}]}
    question, solution = item_hashes(exam, 'question'), item_hashes(exam, 'solution')
    exam['answers'][0]['explanation'] = 'new'
    assert item_hashes(exam, 'question') == question
    assert item_hashes(exam, 'solution') != solution
    exam['questions'][0]['prompt'] = 'y'
    assert item_hashes(exam, 'question') != question


def test_signature_identifies_each_rail_image_among_identical_black_layers(tmp_path):
    """Rails are black-on-transparent: PyMuPDF's image digest ignores the mask
    and reports the wrong xref when several rails share a page."""
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)

    def signature(rows, name):
        blocks = [{'kind': 'fill', 'id': 'q13', 'number': 13, 'rows': rows, 'text': '合成選填 {{answer}}。'},
                  {'kind': 'fill', 'id': 'q15', 'number': 15, 'rows': [1, 2], 'text': '合成選填 {{answer}}。'},
                  {'kind': 'fill', 'id': 'q17', 'number': 17, 'rows': [1, 2], 'text': '合成選填 {{answer}}。'}]
        layout = render({'subject': '數學A', 'blocks': blocks}, tmp_path / f'{name}.pdf', tmp_path / f'{name}.json',
                        font, asset_root=tmp_path)
        part = layout['parts'][0]
        with projected(tmp_path / f'{name}.pdf', (594.96, 841.92)) as doc:
            return render_signature(doc[part['page'] - 1], part['bbox'])

    original = signature([1, 2], 'original')
    assert equivalent_render(original, signature([1, 2], 'again'))
    # Same outer size and the same all-black colour layer; only the mask differs.
    assert not equivalent_render(original, signature([2, 1], 'swapped'))
