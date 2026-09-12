"""Synthetic evidence fixtures test freshness/coverage, never exam quality."""
import json
from pathlib import Path
import sys

import pymupdf
import pytest
import shutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_hosted_run as gate
import inspect_hosted_pdf as inspector
import validate_math_difficulty_design as math_gate
from hosted_item_layout import crop_items
from hosted_run_timing import PHASES
from hosted_blind_review import packet
from validate_paper_difficulty_balance import content_hash, BANDS
from compose_hosted_pdf import compose
from fetch_hosted_template_assets import ROOT, DEFAULT_MAP


@pytest.fixture(scope='session')
def fixed_evidence_pdfs(tmp_path_factory):
    folder = tmp_path_factory.mktemp('fixed-evidence')
    body = folder/'body.pdf'
    with pymupdf.open() as doc:
        p = doc.new_page(width=595.28, height=841.89)
        for i in range(4):
            p.insert_text((75, 120+i*60), 'Synthetic layout test '+str(i))
        doc.save(body)
    font = folder/'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    record = next(s for s in json.loads(DEFAULT_MAP.read_text(encoding='utf-8'))['subjects'] if s['subject']=='英文')
    assets = ROOT/Path(record['assets'][0]['repository_path']).parent
    for role, kind in (('question','questions'),('solution','answers')):
        compose('英文', body, assets, folder/(role+'.pdf'), year='116', title='模擬試題',
                running_name='學測', font_path=font, kind=kind)
    return folder, assets


@pytest.fixture
def saved_run(tmp_path, monkeypatch, fixed_evidence_pdfs):
    monkeypatch.chdir(tmp_path)

    def save(path, value):
        path = Path(path)
        path.write_text(json.dumps(value), encoding='utf-8')
        return {'path': str(path), 'sha256': gate.sha(path)}

    exam = {'metadata': {'paper_id': 'fixture', 'subject': '英文'},
            'questions': [{'id': str(i), 'section_id': str(i % 3)} for i in range(4)]}
    exam['metadata']['difficulty_balance_plan'] = {'basis':'Synthetic fixture',
        'target_counts':dict.fromkeys(BANDS,1), 'target_points':dict.fromkeys(BANDS,5)}
    exam['answers'] = []
    for i,q in enumerate(exam['questions']):
        q.update(score=5, number=i+1)
        design = {'band':BANDS[i], 'content_sha256':content_hash(q), 'expected_minutes':1,
                  'basis':'Fixture', 'confidence':'Fixture', 'short_route':f'Fixture {i}',
                  'misconception':'Fixture', 'linked_decisions':['One','Two','Three'],
                  'bottleneck':['One','Two'], 'shortcut_status':'reviewed-no-direct-collapse'}
        q['item_spec'] = {'difficulty_design':design, 'difficulty':{'label':BANDS[i]}}
        exam['answers'].append({'question_id':q['id'],'difficulty_label':BANDS[i]})
    state = {'schema_version': 1, 'paper_id': 'fixture', 'exam': save('exam.json', exam),
             'checks': {}, 'pdfs': {}}
    folder, assets = fixed_evidence_pdfs
    shutil.copytree(assets, 'templates')
    state['template_asset_dir'] = 'templates'
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
            review['blind_packet'] = save('blind-packet.json', packet(exam))
            for row in review['items']:
                row.update(shortest_route='fixture route', decisive_steps=['fixture decision'],
                           shortcut_search='fixture search', anchor_comparison='fixture comparison',
                           expected_minutes=1,
                           difficulty_band=['easy','medium','hard','very_hard'][int(row['id'])], unresolved=[])
        state['checks'][name] = save(name + '.json', review)
    for role in ('question', 'solution'):
        pdf = Path(role + '.pdf')
        shutil.copyfile(folder/pdf, pdf)
        reference = Path(role+'-reference.pdf')
        with pymupdf.open(pdf) as doc:
            doc.set_metadata({'title':'Synthetic density reference'})
            doc.save(reference)
        layout = {'pdf_sha256': gate.sha(pdf), 'parts': [
            {'id':str(i),'page':2 if role=='question' else 1,'bbox':[70,100+i*60,350,140+i*60],
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
                                    'reference_page':p['page'],'page_role':'body'}
                                    for issue in p['issues']}} for p in scan['pages']]}
        state['pdfs'][role] = {'file': {'path': str(pdf), 'sha256': gate.sha(pdf)},
                              'exam_sha256': state['exam']['sha256'],
                              'inspection': save(role + '-inspection.json', scan),
                              'item_review': save(role + '-items.json', item_review),
                              'visual_review': save(role + '-review.json', visual)}
    review = json.loads(Path('difficulty.json').read_text())
    for row in review['items']:
        row['anchor'] = {'reference_pdf':{'path':'question-reference.pdf',
                        'sha256':gate.sha(Path('question-reference.pdf'))}, 'page':2, 'item':row['id']}
    state['checks']['difficulty'] = save('difficulty.json', review)
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
            review['pages'][1]['issue_dispositions'] = {}
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
    # This isolated four-item population tests the visual floor, not a complete
    # twenty-item math paper or its subject-specific templates.
    assert not any('four distinct' in e for e in evaluate(state, save)['errors'])
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
