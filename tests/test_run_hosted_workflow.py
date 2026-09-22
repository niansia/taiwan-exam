"""Mechanical integration fixtures, never generated exams or academic approval."""
import copy
import json
from pathlib import Path
import sys
import time

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_hosted_workflow as workflow
from prepare_hosted_run import prepare
from verify_fixed_template_pdf import verify_pdf
from test_hosted_run_evidence import saved_run, fixed_evidence_pdfs


@pytest.mark.parametrize('subject', ['國綜','英文','數學A','數學B','自然','社會','國寫'])
def test_both_fixed_booklets_and_resume_without_repeating_work(subject, tmp_path, monkeypatch):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    assert prepare(subject, tmp_path, 'synthetic', font, resource_pdf=ROOT/'web/taiwan-exam-template-resources.pdf')['status'] == 'ready-for-authoring'
    exam = {'metadata': {'paper_id': 'synthetic', 'subject': subject}, 'questions': [{'id': '1'}]}
    workflow.save(tmp_path/'exam.json', exam)
    workflow.checkpoint(tmp_path, 'authoring')
    workflow.content_lock(tmp_path/'run-state.json')
    for role, kind in [('question', 'stimulus'), ('solution', 'solution')]:
        workflow.save(tmp_path/(role+'.json'), {'subject': subject, 'blocks': [
            {'kind': kind, 'id': '1', 'number': 1, 'text': 'Synthetic layout fixture only.',
             'steps': ['Mechanical test, not an exam solution.']}]})
    started = time.perf_counter()
    result = workflow.build(tmp_path/'run-state.json', tmp_path/'question.json', tmp_path/'solution.json',
                            font, tmp_path/'build-v1', year=116)
    first_ms = (time.perf_counter() - started) * 1000
    assert result['status'] == 'review-pending' and not result['cache_hit']
    state_path = Path(result['state'])
    state = workflow.read(state_path)
    for role, bundle in state['pdfs'].items():
        pdf = tmp_path/bundle['file']['path']
        assert verify_pdf(pdf, subject, 'questions' if role == 'question' else 'answers')['status'] == 'pass-fixed-template'
        for key, rows in [('visual_review', 'pages'), ('item_review', 'parts')]:
            report = workflow.read(tmp_path/bundle[key]['path'])
            assert all(row['status'] == 'pending' and not row['observations'] for row in report[rows])
    clock = (tmp_path/'generation-timing.json').read_bytes()
    def unexpected(*a, **k): raise AssertionError('Resume must not render or prepare again')
    monkeypatch.setattr(workflow, 'render', unexpected)
    monkeypatch.setattr(workflow, 'compose', unexpected)
    monkeypatch.setattr(workflow, 'prepare', unexpected)
    started = time.perf_counter()
    cached = workflow.build(tmp_path/'run-state.json', tmp_path/'question.json', tmp_path/'solution.json',
                            font, tmp_path/'build-v1', year=116)
    resume_ms = (time.perf_counter() - started) * 1000
    measurement = {'subject': subject, 'first_build_ms': round(first_ms, 2),
                   'resume_ms': round(resume_ms, 2), 'scope': 'One-item synthetic mechanical layout only; not exam generation or visual acceptance.'}
    workflow.save(tmp_path/'build-measurement.json', measurement)
    print(json.dumps(measurement, ensure_ascii=False))
    assert cached['cache_hit']
    assert (tmp_path/'generation-timing.json').read_bytes() == clock
    # The checkpoint uses the latest reviewed state rather than dropping pdfs.
    workflow.checkpoint(tmp_path, 'authoring', state=state_path)
    assert workflow.read(state_path)['pdfs'] == state['pdfs']
    (tmp_path/'build-v1/question.pdf').write_bytes(b'changed')
    with pytest.raises(ValueError, match='Cached build artifact changed'):
        workflow.build(tmp_path/'run-state.json', tmp_path/'question.json', tmp_path/'solution.json',
                       font, tmp_path/'build-v1', year=116)


def test_finalize_keeps_actual_pending_and_stale_reviews_blocking(saved_run, tmp_path):
    state, save = saved_run
    save('run-state.json', state)
    assert workflow.finalize(tmp_path/'run-state.json', tmp_path/'final.json')['status'] == 'evidence-complete'
    path = tmp_path/state['checks']['answers']['path']
    review = workflow.read(path)
    review['status'] = 'pending'
    review['observations'] = ''
    workflow.save(path, review)
    result = workflow.finalize(tmp_path/'run-state.json', tmp_path/'final.json')
    assert result['status'] == 'pending'
    assert workflow.read(path) == review  # No invented review observations.
    review['exam_sha256'] = '0'*64
    workflow.save(path, review)
    assert workflow.finalize(tmp_path/'run-state.json', tmp_path/'final.json')['status'] == 'pending'


def test_finalize_closes_a_paused_conversation_clock(saved_run, tmp_path):
    state, save = saved_run
    save('run-state.json', state)
    workflow.clock(tmp_path/'run-state.json', 'pause')
    result = workflow.finalize(tmp_path/'run-state.json', tmp_path/'final.json')
    assert result['status'] == 'evidence-complete'
    assert not workflow.read(tmp_path/'generation-timing.json').get('paused')


def test_finalize_delivers_copies_rendering_the_checked_pages(saved_run, tmp_path):
    state, save = saved_run
    save('run-state.json', state)
    result = workflow.finalize(tmp_path/'run-state.json', tmp_path/'final.json')
    assert result['status'] == 'evidence-complete' and set(result['delivery']) == set(state['pdfs'])
    for copy_ in result['delivery'].values():
        with pymupdf.open(tmp_path/copy_['checked_pdf']['path']) as checked, pymupdf.open(copy_['path']) as delivered:
            assert [page.get_text() for page in checked] == [page.get_text() for page in delivered]
            assert ([page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).samples for page in checked] ==
                    [page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).samples for page in delivered])
    assert workflow.read(tmp_path/'final.json')['delivery'] == result['delivery']
    assert Path(result['delivery']['question']['path']).name == '學測_英文_fixture_題本.pdf'
    assert Path(result['delivery']['solution']['path']).name == '學測_英文_fixture_詳解.pdf'
    again = workflow.finalize(tmp_path/'run-state.json', tmp_path/'final.json')
    assert {k: v['path'] for k, v in again['delivery'].items()} == {
        k: v['path'] for k, v in result['delivery'].items()}


@pytest.mark.parametrize('exam,subject', [
    *[('學測', s) for s in ('國綜', '國寫', '英文', '數學A', '數學B', '社會', '自然')],
    *[('會考', s) for s in ('國文', '英語', '數學', '社會', '自然')],
])
def test_delivery_names_identify_exam_subject_and_pair(exam, subject):
    metadata = {'exam': exam, 'subject': subject}
    for role, label in [('question', '題本'), ('solution', '詳解')]:
        assert workflow.delivery_filename(metadata, '20260920-01', role) == (
            f'{exam}_{subject}_20260920-01_{label}.pdf')


def test_delivery_names_are_portable_distinct_and_bounded():
    metadata = {'exam': '學測', 'subject': '數A'}
    names = [workflow.delivery_filename(metadata, paper, 'question')
             for paper in ('../a:b', '..\\a?b', 'x'*300, 'x'*299+'y')]
    assert len(set(names)) == 4
    for name in names:
        assert name.startswith('學測_數學A_') and name.endswith('_題本.pdf')
        assert not any(c in name for c in '<>:"/\\|?*')
        assert len(name) < 150


@pytest.mark.parametrize('name', ['run-state.json','exam.json','generation-timing.json','answers.json','question.pdf'])
def test_final_report_cannot_overwrite_any_input(saved_run, tmp_path, name):
    state, save = saved_run
    save('run-state.json', state)
    original = (tmp_path/name).read_bytes()
    with pytest.raises(ValueError, match='must not overwrite'):
        workflow.finalize(tmp_path/'run-state.json', tmp_path/name)
    assert (tmp_path/name).read_bytes() == original


def test_checkpoint_bundle_requires_current_real_reports(tmp_path):
    workflow.save(tmp_path/'preflight.json', {'status': 'ready-for-authoring', 'paper_id': 'id',
        'subject': '英文', 'review_mode': 'single-context', 'require_independent_review': False,
        'calibration': {}, 'template_asset_dir': 'templates'})
    workflow.save(tmp_path/'exam.json', {'metadata': {'paper_id': 'id', 'subject': '英文'}})
    workflow.checkpoint(tmp_path, 'authoring')
    review = {'exam_sha256': workflow.digest(tmp_path/'exam.json'), 'status': 'pending', 'observations': ''}
    workflow.save(tmp_path/'bundle.json', {'answers': review})
    workflow.checkpoint(tmp_path, review_bundle=tmp_path/'bundle.json')
    assert workflow.read(tmp_path/'answers.json') == review
    bad = copy.deepcopy(review); bad['exam_sha256'] = '0'*64
    workflow.save(tmp_path/'bundle.json', {'answers': bad})
    with pytest.raises(ValueError, match='stale exam'):
        workflow.checkpoint(tmp_path, review_bundle=tmp_path/'bundle.json')


@pytest.fixture
def asset_build(tmp_path):
    """One synthetic diagram tests artifact invalidation, not exam pedagogy."""
    font = tmp_path/'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    assert prepare('英文', tmp_path, 'asset-test', font,
                   resource_pdf=ROOT/'web/taiwan-exam-template-resources.pdf')['status'] == 'ready-for-authoring'
    workflow.save(tmp_path/'exam.json', {'metadata': {'paper_id': 'asset-test', 'subject': '英文'},
                                       'questions': [{'id': '1'}]})
    workflow.checkpoint(tmp_path, 'authoring')
    workflow.content_lock(tmp_path/'run-state.json')
    asset = tmp_path/'diagram.svg'
    asset.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="30"><path d="M5 15 L95 15" stroke="black"/></svg>')
    for role, kind in [('question', 'stimulus'), ('solution', 'solution')]:
        workflow.save(tmp_path/(role+'.json'), {'subject': '英文', 'blocks': [
            {'kind': kind, 'id': '1', 'number': 1, 'text': 'Synthetic diagram fixture only.',
             'steps': ['Mechanical fixture, not an examined solution.'],
             'figure': 'diagram', 'assets': {'diagram': {'path': 'diagram.svg',
                'sha256': workflow.digest(asset), 'width_pt': 100, 'height_pt': 30}}}]})
    args = (tmp_path/'run-state.json', tmp_path/'question.json', tmp_path/'solution.json', font, tmp_path/'build-v1')
    result = workflow.build(*args, year=116)
    return tmp_path, args, result


@pytest.mark.parametrize('changed', ['asset', 'updated-asset', 'exam', 'body', 'pdf', 'raster',
                                   'candidate-review-plan', 'new-review-requirement', 'candidate-exam', 'review-binding'])
def test_changed_inputs_or_cached_evidence_cannot_be_reused(asset_build, changed):
    root, args, result = asset_build
    candidate = Path(result['state'])
    state = workflow.read(candidate)
    if changed in {'asset', 'updated-asset'}:
        asset = root/'diagram.svg'
        asset.write_bytes(asset.read_bytes().replace(b'L95', b'L90'))
        if changed == 'updated-asset':
            spec = workflow.read(root/'question.json')
            spec['blocks'][0]['assets']['diagram']['sha256'] = workflow.digest(asset)
            workflow.save(root/'question.json', spec)
    elif changed in {'exam', 'body', 'pdf', 'raster'}:
        paths = {'exam': root/'exam.json', 'body': root/'build-v1/question-body.pdf',
                 'pdf': root/'build-v1/question.pdf',
                 'raster': next((root/'build-v1-review').rglob('*.png'))}
        path = paths[changed]
        path.write_bytes(path.read_bytes() + b'\nchanged')
    elif changed == 'new-review-requirement':
        original = workflow.read(args[0])
        original['require_independent_review'] = True
        workflow.save(args[0], original)
    elif changed == 'review-binding':
        path = root/state['pdfs']['question']['visual_review']['path']
        report = workflow.read(path)
        report['pdf_sha256'] = '0'*64
        workflow.save(path, report)
    else:
        if changed == 'candidate-review-plan':
            state['review_mode'] = 'independent-context'
        else:
            state['exam']['sha256'] = '0'*64
        workflow.save(candidate, state)
    with pytest.raises(ValueError):
        workflow.build(*args, year=116)


def test_cache_retains_actual_review_edits_without_claiming_approval(asset_build):
    root, args, result = asset_build
    candidate = Path(result['state'])
    state = workflow.read(candidate)
    path = root/state['pdfs']['question']['visual_review']['path']
    report = workflow.read(path)
    report['pages'][0]['observations'] = 'Synthetic reviewer observed a possible margin defect; still pending.'
    workflow.save(path, report)
    cached = workflow.build(*args, year=116)
    assert cached['cache_hit'] and cached['status'] == 'review-pending'
    assert cached['reviews_approved_by_tool'] is False
    assert workflow.read(path) == report


@pytest.mark.parametrize('output', ['unregistered-review', 'body-spec'])
def test_finalize_cannot_overwrite_unregistered_or_unrelated_work(saved_run, tmp_path, output):
    state, save = saved_run
    if output == 'unregistered-review':
        path = tmp_path/state['checks'].pop('answers')['path']
    else:
        path = tmp_path/'question-blocks.json'
        workflow.save(path, {'subject': '英文', 'blocks': [{'text': 'Saved editable work'}]})
    save('run-state.json', state)
    before = path.read_bytes()
    with pytest.raises(ValueError, match='must not overwrite'):
        workflow.finalize(tmp_path/'run-state.json', path)
    assert path.read_bytes() == before


def test_finalize_cannot_invent_missing_page_or_item_qa(saved_run, tmp_path):
    state, save = saved_run
    for role, bundle in state['pdfs'].items():
        path = tmp_path/bundle['visual_review']['path']
        report = workflow.read(path)
        report['pages'][0].update(status='pending', observations='')
        workflow.save(path, report)
        path = tmp_path/bundle['item_review']['path']
        report = workflow.read(path)
        report['parts'][0].update(status='pending', observations='')
        workflow.save(path, report)
    save('run-state.json', state)
    result = workflow.finalize(tmp_path/'run-state.json', tmp_path/'final.json')
    assert result['status'] == 'pending' and result['formal_acceptance'] is False
    assert any('review' in error for error in result['errors'])
