"""Time savers measured on a real 自然 run: none of them removes a quality check."""
import copy
import json
from pathlib import Path
import sys
import time

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import append_items as appender
import emit_item_skeleton as skeleton
import normalize_figure_asset as figures
import run_hosted_workflow as workflow
from hosted_run_timing import transition
from prepare_hosted_run import prepare

ROOT = Path(__file__).resolve().parents[1]
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:dc="http://purl.org/dc/elements/1.1/" width="{w}" height="{h}">'
       '<metadata><dc:date>{date}</dc:date></metadata><defs><clipPath id="{a}"><rect width="{w}" height="{h}"/></clipPath>'
       '</defs><path id="{b}" d="M5 15 L95 15" stroke="black" clip-path="url(#{a})"/><use href="#{b}"/></svg>')


@pytest.fixture
def run(tmp_path):
    workflow.save(tmp_path/'preflight.json', {'status': 'ready-for-authoring', 'paper_id': 'p',
        'subject': '自然', 'review_mode': 'single-context', 'require_independent_review': False,
        'calibration': {}, 'template_asset_dir': 'templates'})
    transition(tmp_path/'generation-timing.json', 'p', 'reference_preflight')
    workflow.save(tmp_path/'plan.json', {'metadata': {'title': 'Synthetic', 'exam': '學測',
        'calibration_level': 'exploratory-uncalibrated'}, 'sections': [{'id': 's', 'title': 'Synthetic'}],
        'instructions': ['Not an exam.']})
    return tmp_path


def item(qid, number, **fields):
    return {'id': qid, 'number': number, 'section_id': 's', 'type': 'constructed_response',
            'prompt': 'Synthetic ' + qid, **fields}


def batch(questions):
    return {'questions': questions, 'answers': [{'question_id': q['id'], 'final_answer': 1,
             'reasoning': ['Synthetic'], 'verification_status': 'unverified'} for q in questions]}


def append(run, questions, **kwargs):
    workflow.save(run/'batch.json', batch(questions))
    return appender.append(run, run/'batch.json', plan=run/'plan.json', **kwargs)


def test_first_batch_is_proofed_and_later_text_only_items_wait_for_the_build(run):
    first = append(run, [item('q1', 1), item('q2', 2)])
    assert set(first['proof_recommended']) == {'q1', 'q2'} and first['proof_optional'] == []
    assert all('first batch' in r[0] for r in first['proof_recommended'].values())
    figure = run/'fig.svg'
    figure.write_text(SVG.format(w=100, h=30, date='x', a='c', b='p'), encoding='utf-8')
    second = append(run, [item('q3', 3), item('q4', 4, visual_asset={'path': 'fig.svg', 'sha256': workflow.digest(figure)}),
                          item('q5', 5, prompt='H<sub>2</sub>O 的莫耳數'), item('q6', 6, prompt='答：______')])
    assert second['proof_optional'] == ['q3']
    assert second['proof_recommended']['q4'] == ['question figure']
    assert any('superscript' in r for r in second['proof_recommended']['q5'])
    assert any('blank' in r for r in second['proof_recommended']['q6'])
    assert 'plan_hint' not in second


def test_plan_hint_appears_once_enough_items_are_saved_and_stops_after_the_lock(run):
    for start in range(1, appender.EARLY_PLAN_ITEMS + 1, 4):
        report = append(run, [item(f'q{n}', n) for n in range(start, start + 4)])
        assert ('plan_hint' in report) == (start + 3 >= appender.EARLY_PLAN_ITEMS)
    assert 'plan' in report['plan_hint']
    (run/'content-lock.json').write_text('{}', encoding='utf-8')
    workflow.save(run/'batch.json', batch([item('q99', 99)]))
    assert 'plan_hint' not in appender.append(run, run/'batch.json')


@pytest.mark.parametrize('ids,message', [
    (['plot', 'calculation'], 'printed ordinal'),
    (['1', 'b'], 'one ordering scheme'),
])
def test_subparts_that_could_print_out_of_order_are_refused(run, ids, message):
    with pytest.raises(ValueError, match=message):
        append(run, [item(f'q50-{s}', 50, subpart_id=s) for s in ids])


def test_ordered_subparts_print_in_their_ordinal_order(run):
    append(run, [item('q50-calc', 50, subpart_id='2-calculation'), item('q50-plot', 50, subpart_id='1-plot'),
                 item('q51-b', 51, subpart_id='b'), item('q51-a', 51, subpart_id='a')])
    saved = [q['id'] for q in workflow.read(run/'exam.json')['questions']]
    assert saved == ['q50-plot', 'q50-calc', 'q51-a', 'q51-b']


def test_profile_subpart_names_receive_their_printed_ordinal():
    plot = skeleton.skeleton('自然', number=50, subpart='plot')
    calculation = skeleton.skeleton('自然', number=50, subpart='calculation')
    assert plot['question']['subpart_id'] == '1-plot' and calculation['question']['subpart_id'] == '2-calculation'
    assert skeleton.skeleton('自然', number=38, subpart='b')['question']['subpart_id'] == 'b'


def test_absolute_option_wording_is_listed_without_blocking_the_batch(run):
    report = append(run, [item('q1', 1, options=[{'label': 'A', 'text': '折射角與入射角無關'},
                                                 {'label': 'B', 'text': '折射角隨入射角增大'}])])
    assert report['status'] == 'items-saved'
    assert report['absolute_claim_options'] == [{'id': 'q1', 'label': 'A', 'word': '無關', 'text': '折射角與入射角無關'}]
    assert 'condition' in report['absolute_claim_note']


def test_tall_figure_is_flagged_when_saved_not_after_pagination(run):
    tall, wide = run/'tall.svg', run/'wide.svg'
    tall.write_text(SVG.format(w=100, h=120, date='x', a='c', b='p'), encoding='utf-8')
    wide.write_text(SVG.format(w=100, h=30, date='x', a='c', b='p'), encoding='utf-8')
    report = append(run, [item('q1', 1, visual_asset={'path': 'tall.svg', 'sha256': workflow.digest(tall)}),
                          item('q2', 2, visual_asset={'path': 'wide.svg', 'sha256': workflow.digest(wide)}),
                          item('q3', 3, visual_asset={'path': 'tall.svg', 'sha256': workflow.digest(tall)},
                               visual_layout='side-right')])
    assert len(report['layout_risks']) == 1 and report['layout_risks'][0].startswith('item q1 ')
    assert 'width_percent' in report['layout_risks'][0]


def test_same_drawing_exported_twice_keeps_one_hash(tmp_path):
    first, second = tmp_path/'a.svg', tmp_path/'b.svg'
    first.write_text(SVG.format(w=100, h=30, date='2026-09-21T10:00:00', a='m5f97', b='p1a2'), encoding='utf-8')
    second.write_text(SVG.format(w=100, h=30, date='2026-09-21T11:00:00', a='m7a01', b='p9z8'), encoding='utf-8')
    assert figures.normalize(first)['sha256'] == figures.normalize(second)['sha256']
    assert 'url(#n1)' in first.read_text(encoding='utf-8') and '<metadata>' not in first.read_text(encoding='utf-8')
    with pymupdf.open(first) as drawing:
        assert drawing[0].rect.width == 100
    pdfs = []
    for stamp in ("D:20260921100000+08'00'", "D:20260921110000+08'00'"):
        with pymupdf.open() as doc:
            page = doc.new_page(width=200, height=100)
            page.draw_line((10, 50), (190, 50))
            doc.set_metadata({'creationDate': stamp, 'modDate': stamp, 'producer': 'plotter'})
            path = tmp_path/f'{len(pdfs)}.pdf'
            doc.save(path)
        pdfs.append(figures.normalize(path))
    assert pdfs[0]['sha256'] == pdfs[1]['sha256']
    with pymupdf.open(tmp_path/'0.pdf') as doc:
        assert len(doc) == 1 and doc.metadata['producer'] == ''
    (tmp_path/'x.png').write_bytes(b'not a figure')
    with pytest.raises(ValueError, match='SVG or single-page PDF'):
        figures.normalize(tmp_path/'x.png')


@pytest.fixture
def paper(tmp_path):
    """A small real 自然 run: preflight, saved items and projected specs."""
    font = tmp_path/'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    assert prepare('自然', tmp_path, 'plan-test', font,
                   resource_pdf=ROOT/'web/taiwan-exam-template-resources.pdf')['status'] == 'ready-for-authoring'
    workflow.save(tmp_path/'plan.json', {'metadata': {'title': 'Synthetic', 'exam': '學測',
        'calibration_level': 'exploratory-uncalibrated'}, 'sections': [{'id': 's', 'title': '第壹部分'}],
        'instructions': ['Not an exam.']})
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 's', 'type': 'single_choice',
                  'prompt': f'合成題幹 {n}：' + '此為版面量測用的合成文字。' * 6,
                  'options': [{'label': l, 'text': f'選項 {l}'} for l in 'ABCDE']} for n in range(1, 13)]
    for start in range(0, len(questions), 4):
        chunk = questions[start:start + 4]
        workflow.save(tmp_path/'batch.json', {'questions': chunk, 'answers': [
            {'question_id': q['id'], 'final_answer': 'A', 'reasoning': ['合成詳解。' * 8],
             'verification_status': 'unverified'} for q in chunk]})
        appender.append(tmp_path, tmp_path/'batch.json', plan=tmp_path/'plan.json' if start == 0 else None)
    workflow.specs(tmp_path/'run-state.json', tmp_path/'q.json', tmp_path/'s.json')
    return tmp_path, font


def test_plan_paginates_both_bodies_without_pdfs_rasters_or_review_state(paper):
    root, font = paper
    started = time.perf_counter()
    result = workflow.plan(root/'run-state.json', root/'q.json', root/'s.json', font, root/'plan-01')
    plan_seconds = time.perf_counter() - started
    assert result['status'] == 'page-plan-only' and result['deliverable'] is False
    assert result['content_lock'] == 'none' and result['reviews_approved_by_tool'] is False
    assert set(result['page_counts']) == {'question', 'solution'} and result['page_counts']['question'] >= 1
    saved = workflow.read(Path(result['page_plan']))
    assert saved['exam'] == workflow.read(root/'run-state.json')['exam']
    for role in ('question', 'solution'):
        assert saved['booklets'][role]['pages'][0]['bottom_void_ratio'] <= 1
        assert not (root/'plan-01'/(role + '.pdf')).exists()
    assert not (root/'plan-01-review').exists() and not (root/'plan-01-run-state.json').exists()
    assert not list((root/'plan-01').rglob('*.png'))
    assert 'pause' in result['clock_reminder']
    with pytest.raises(ValueError, match='exists'):
        workflow.plan(root/'run-state.json', root/'q.json', root/'s.json', font, root/'plan-01')
    workflow.content_lock(root/'run-state.json')
    second = workflow.plan(root/'run-state.json', root/'q.json', root/'s.json', font, root/'plan-02', compare=root/'plan-01')
    assert second['content_lock'] == 'matches'
    assert second['compared_with_previous']['question']['bottom_void_delta']
    assert second['iteration_budget'] == {'kind': 'plan', 'count': 2, 'budget': 3, 'over_budget': False, 'note': 'within budget'}
    started = time.perf_counter()
    build = workflow.build(root/'run-state.json', root/'q.json', root/'s.json', font, root/'build-v1', year=116)
    build_seconds = time.perf_counter() - started
    assert build['status'] == 'review-pending' and 'pause' in build['clock_reminder']
    assert build['iteration_budget']['count'] == 1
    assert workflow.read(Path(build['page_plan']))['booklets']['question']['plan']['page_count'] == result['page_counts']['question']
    print(json.dumps({'plan_seconds': round(plan_seconds, 2), 'build_seconds': round(build_seconds, 2)}))
    assert plan_seconds < build_seconds


def test_plan_refuses_a_stale_spec_and_a_foreign_subject(paper):
    root, font = paper
    spec = workflow.read(root/'q.json')
    workflow.save(root/'edited.json', {**spec, 'subject': '英文'})
    with pytest.raises(ValueError, match='subject'):
        workflow.plan(root/'run-state.json', root/'edited.json', root/'s.json', font, root/'plan-x')
    stale = copy.deepcopy(spec)
    stale['exam_sha256'] = '0' * 64
    workflow.save(root/'stale.json', stale)
    with pytest.raises(ValueError, match='predates'):
        workflow.plan(root/'run-state.json', root/'stale.json', root/'s.json', font, root/'plan-y')


def test_text_only_crops_are_read_on_their_page_and_settle_with_it(paper):
    """Every item is still read: text-only crops pass through their page review."""
    root, font = paper
    figure = root/'fig.svg'
    figure.write_text(SVG.format(w=100, h=30, date='x', a='c', b='p'), encoding='utf-8')
    workflow.save(root/'batch.json', batch([item('q13', 13, type='single_choice',
                                                 visual_asset={'path': 'fig.svg', 'sha256': workflow.digest(figure)},
                                                 options=[{'label': l, 'text': f'選項 {l}'} for l in 'ABCDE'])]))
    appender.append(root, root/'batch.json')
    workflow.specs(root/'run-state.json', root/'q2.json', root/'s2.json')
    workflow.content_lock(root/'run-state.json')
    built = workflow.build(root/'run-state.json', root/'q2.json', root/'s2.json', font, root/'build-v2', year=116)
    state = workflow.read(Path(built['state']))
    items = workflow.read(root/state['pdfs']['question']['item_review']['path'])['parts']
    by_id = {p['id']: p for p in items}
    assert by_id['q13'].get('review_via') is None and by_id['q1']['review_via'] == 'page'
    assert built['items_read_on_pages']['question'] == 12
    queued = {Path(p).name for p in built['review_queue']['question']['items']}
    assert queued == {Path(by_id['q13']['raster_path']).name}
    template = workflow.read(Path(built['observations_template']))
    assert set(template['question']['items']) == {'q13'}
    for role in ('question', 'solution'):
        for key in template[role].get('items', {}):
            template[role]['items'][key] = {'status': 'pass', 'observations': 'figure and labels readable'}
        for key in template[role]['pages']:
            template[role]['pages'][key] = {'status': 'pass', 'observations': f'page {key} read at full size'}
    workflow.save(root/'notes.json', template)
    result = workflow.record_review(root/'notes.json', state=built['state'])
    assert all(not r['items_pending'] and not r['items_settled_by_page_review_pending'] for r in result['remaining'].values())
    settled = workflow.read(root/state['pdfs']['question']['item_review']['path'])['parts']
    assert all(p['status'] == 'pass' and 'read on page' in p['observations'] for p in settled if p['id'] != 'q13')
    check = workflow.finalize(built['state'], root/'final.json')
    assert not any('readable item review missing' in e or 'is not a passed review' in e for e in check['errors'])
    # A report cannot relabel a figure item as page-reviewed: the checker recomputes the triage.
    report_path = root/state['pdfs']['question']['item_review']['path']
    report = workflow.read(report_path)
    for part in report['parts']:
        if part['id'] == 'q13':
            part.update(review_via='page', status='pass', observations='text-only item read on page 4: faked')
    workflow.save(report_path, report)
    from prepare_hosted_review import refresh_review_hashes
    refresh_review_hashes(Path(built['state']))
    check = workflow.finalize(built['state'], root/'final-2.json')
    assert any('needs its own crop review' in e for e in check['errors'])


def test_batches_of_six_are_for_text_only_items(run):
    six = [item(f'q{n}', n) for n in range(1, 7)]
    assert append(run, six)['question_count'] == 6
    figure = run/'fig.svg'
    figure.write_text(SVG.format(w=100, h=30, date='x', a='c', b='p'), encoding='utf-8')
    with pytest.raises(ValueError, match='at most 4'):
        append(run, [item(f'q{n}', n) for n in range(7, 12)] +
               [item('q12', 12, visual_asset={'path': 'fig.svg', 'sha256': workflow.digest(figure)})])
    with pytest.raises(ValueError, match='2-4'):
        append(run, [item(f'q{n}', n) for n in range(13, 20)])
