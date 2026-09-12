"""Synthetic evidence fixtures test freshness/coverage, never exam quality."""
import json
from pathlib import Path
import sys

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_hosted_run as gate
import inspect_hosted_pdf as inspector
import validate_math_difficulty_design as math_gate
from hosted_item_layout import crop_items
from hosted_run_timing import PHASES
from hosted_blind_review import packet


@pytest.fixture
def saved_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def save(path, value):
        path = Path(path)
        path.write_text(json.dumps(value), encoding='utf-8')
        return {'path': str(path), 'sha256': gate.sha(path)}

    exam = {'metadata': {'paper_id': 'fixture', 'subject': '英文'},
            'questions': [{'id': str(i), 'section_id': str(i % 3)} for i in range(4)]}
    state = {'schema_version': 1, 'paper_id': 'fixture', 'exam': save('exam.json', exam),
             'checks': {}, 'pdfs': {}}
    state['timing'] = save('generation-timing.json', {'paper_id': 'fixture', 'active': None,
        'intervals': [{'phase': phase, 'start': 1000+i*10, 'end': 1010+i*10}
                      for i, phase in enumerate(sorted(PHASES))]})
    for name in gate.ITEM_GATES + gate.PAPER_GATES:
        review = {'exam_sha256': state['exam']['sha256'], 'status': 'pass',
                  'observations': 'Synthetic test review; no academic acceptance.'}
        if name in gate.ITEM_GATES:
            review['items'] = [{'id': str(i), 'status': 'pass', 'observations': 'Fixture observation',
                                'visual_id': str(i), 'visual_role': str(i % 2),
                                'required_for_answer': True} for i in range(4)]
        if name == 'originality':
            review['comparison_scope'] = 'no-history-available'
        if name == 'difficulty':
            review.update(author_context='fixture-author', reviewer_context='fixture-blind-review')
            for row in review['items']:
                row.update(shortest_route='fixture route', decisive_steps=['fixture decision'],
                           shortcut_search='fixture search', anchor_comparison='fixture comparison',
                           expected_minutes=1, difficulty_band='easy', unresolved=[])
        state['checks'][name] = save(name + '.json', review)
    for role in ('question', 'solution'):
        pdf = Path(role + '.pdf')
        with pymupdf.open() as doc:
            p = doc.new_page(width=595.28, height=841.89)
            for i in range(4):
                p.insert_text((75, 120+i*60), role + ': synthetic layout test '+str(i))
            doc.save(pdf)
        reference = Path(role+'-reference.pdf')
        with pymupdf.open(pdf) as doc:
            doc.set_metadata({'title':'Synthetic density reference'})
            doc.save(reference)
        layout = {'pdf_sha256': gate.sha(pdf), 'parts': [
            {'id':str(i),'page':1,'bbox':[70,100+i*60,350,140+i*60],
             'components':[{'role':'stem','bbox':[75,105+i*60,340,125+i*60]}]} for i in range(4)]}
        item_review = crop_items(pdf, layout, Path('crops')/role)
        for part in item_review['parts']:
            part.update(status='pass',observations='Synthetic item crop')
        scan = inspector.audit(pdf, Path('rasters') / role)
        visual = {'pdf_sha256': gate.sha(pdf), 'pages': [
            {'page': p['page'], 'raster_sha256': p['raster_sha256'], 'status': 'pass',
             'observations': 'Synthetic one-line fixture; intentionally sparse, not an exam.',
             'issue_dispositions': {issue: {'decision': 'justified', 'reason': 'Sparse test fixture',
                                    'reference_pdf': {'path':str(reference),'sha256':gate.sha(reference)},
                                    'reference_page':1,'page_role':'body'}
                                    for issue in p['issues']}} for p in scan['pages']]}
        state['pdfs'][role] = {'file': {'path': str(pdf), 'sha256': gate.sha(pdf)},
                              'exam_sha256': state['exam']['sha256'],
                              'inspection': save(role + '-inspection.json', scan),
                              'item_review': save(role + '-items.json', item_review),
                              'visual_review': save(role + '-review.json', visual)}
    save('run-state.json', state)
    sources = {'subjects': [{'subject':subject,'years':[{'documents':{
        role: {'sha256':gate.sha(Path(role+'-reference.pdf'))} for role in ('question','solution')}}]}
        for subject in ('英文','數學A')]}
    save('test-source-map.json', sources)
    monkeypatch.setattr(gate, 'SOURCE_MAP', Path('test-source-map.json'))
    return state, save


def evaluate(state, save):
    save('run-state.json', state)
    return gate.check(Path('run-state.json'))


def test_complete_record_is_not_academic_self_approval(saved_run):
    result = evaluate(*saved_run)
    assert result['status'] == 'evidence-complete'
    assert result['formal_acceptance'] is False


def test_interrupted_run_resumes_without_rewriting_passed_artifacts(saved_run):
    state, save = saved_run
    missing = state['checks'].pop('difficulty')
    assert evaluate(state, save)['status'] == 'pending'
    state['checks']['difficulty'] = missing
    assert evaluate(state, save)['status'] == 'evidence-complete'


@pytest.mark.parametrize('change', ['exam', 'pdf', 'raster', 'missing_page', 'unresolved_void', 'missing_item'])
def test_stale_or_incomplete_evidence_blocks_delivery(saved_run, change):
    state, save = saved_run
    if change == 'exam':
        exam = json.loads(Path('exam.json').read_text())
        exam['questions'][0]['prompt'] = 'Revised condition'
        state['exam'] = save('exam.json', exam)
    elif change == 'pdf':
        Path('question.pdf').write_bytes(Path('question.pdf').read_bytes() + b'\n%changed')
    elif change == 'raster':
        next(Path('rasters').rglob('*.png')).write_bytes(b'changed')
    elif change in {'missing_page', 'unresolved_void'}:
        review = json.loads(Path('question-review.json').read_text())
        if change == 'missing_page':
            review['pages'] = []
        else:
            review['pages'][0]['issue_dispositions'] = {}
        state['pdfs']['question']['visual_review'] = save('question-review.json', review)
    else:
        review = json.loads(Path('difficulty.json').read_text())
        review['items'].pop()
        state['checks']['difficulty'] = save('difficulty.json', review)
    assert evaluate(state, save)['status'] == 'pending'


def test_external_evidence_is_rejected(saved_run, tmp_path):
    state, save = saved_run
    state['checks']['answers']['path'] = str(tmp_path / 'answers.json')
    assert any('external' in e for e in evaluate(state, save)['errors'])


def test_math_visual_floor_counts_required_distinct_visuals_across_sections(saved_run):
    state, save = saved_run
    exam = json.loads(Path('exam.json').read_text())
    exam['metadata']['subject'] = '數學A'
    state['exam'] = save('exam.json', exam)
    for name, record in state['checks'].items():
        review = json.loads(Path(record['path']).read_text())
        review['exam_sha256'] = state['exam']['sha256']
        if name == 'difficulty':
            review['blind_packet'] = save('blind-packet.json', packet(exam))
        state['checks'][name] = save(record['path'], review)
    for bundle in state['pdfs'].values():
        bundle['exam_sha256'] = state['exam']['sha256']
    assert evaluate(state, save)['status'] == 'evidence-complete'
    review = json.loads(Path('visuals.json').read_text())
    for row in review['items']:
        row['required_for_answer'] = False
    state['checks']['visuals'] = save('visuals.json', review)
    assert any('four distinct' in e for e in evaluate(state, save)['errors'])


@pytest.mark.parametrize('subject', ['數學A', '數學B'])
def test_routine_math_cannot_omit_innovation_audit(subject):
    item = {'id': 'routine', 'number': 10, 'type': 'multiple_choice', 'score': 5,
            'item_spec': {'difficulty_design': {'shortcut_audit': {'direct_formula_substitution_only': True}}}}
    errors, _ = math_gate.validate_item(item, {}, subject)
    assert any('direct-formula-only' in e for e in errors)
    assert any('innovation audit' in e for e in errors)
