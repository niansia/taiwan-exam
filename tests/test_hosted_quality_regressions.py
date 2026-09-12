"""Regressions for visible defects, measured flow and non-self-labelled reviews."""
import json
from pathlib import Path
import sys
import pymupdf
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from inspect_hosted_pdf import rail_collision_samples, audit
from hosted_item_layout import reserve_rail, draw_rail, geometry_errors
from hosted_run_timing import transition, timing_errors, summary, PHASES
from hosted_blind_review import packet, review_errors
from test_hosted_run_evidence import saved_run, evaluate


def test_actual_native_and_outlined_math_collisions_block(tmp_path):
    with pymupdf.open() as doc:
        p=doc.new_page(width=595.28,height=841.89)
        p.insert_text((106,120),'How many integers?',fontsize=11)
        p.insert_text((106,124),'(13-1)',fontsize=9)
        p.insert_text((106,190),'(14-1)',fontsize=9)
        # A filled outline stands for a math glyph, absent from extracted text.
        p.draw_rect((110,184,115,188),fill=(0,0,0),color=None)
        findings=rail_collision_samples(p)
        assert {r['label'] for r in findings} == {'(13-1)','(14-1)'}
        assert {r['kind'] for r in findings} == {'text','outlined-math'}
        path=tmp_path/'bad.pdf';doc.save(path)
    assert audit(path,tmp_path/'rasters')['blocking_pages']==[1]


def test_flow_reserves_below_tall_figure_and_refuses_overflow():
    boxes=[[80,100,300,150],[320,100,500,240]]
    rail=reserve_rail(boxes,x=90,slots=3,bottom_limit=775)
    assert rail['bbox'][1] >= 248 and rail['next_y'] > rail['bbox'][3]
    assert reserve_rail(boxes,x=90,slots=3,bottom_limit=260) is None
    with pymupdf.open() as doc:
        p=doc.new_page(width=595.28,height=841.89)
        p.insert_text((80,140),'Measured stem')
        draw_rail(p,rail,15,3)
        assert not rail_collision_samples(p)
        parts=[{'id':'15','page':1,'bbox':[70,95,510,rail['next_y']],
                'components':[{'role':'stem','bbox':boxes[0]}, {'role':'figure','bbox':boxes[1]},
                              {'role':'answer_rail','bbox':rail['bbox']}]}]
        assert not geometry_errors(doc,parts)
        parts.append({'id':'16','page':1,'bbox':[70,210,510,270],
                      'components':[{'role':'stem','bbox':[80,215,500,235]}]})
        assert any('overlaps' in e for e in geometry_errors(doc,parts))


def test_real_template_assets_do_not_trigger_rail_false_positives():
    root=Path(__file__).resolve().parents[1]
    manifest=json.loads((root/'exam_packs/學測/templates/115/hosted-web-template-assets.json').read_text(encoding='utf-8'))
    for subject in manifest['subjects']:
        for asset in subject['assets']:
            with pymupdf.open(root/asset['repository_path']) as doc:
                assert all(not rail_collision_samples(p) for p in doc)


def test_measured_timer_records_repairs_and_benchmark_is_not_deadline(tmp_path,monkeypatch):
    import hosted_run_timing as timer
    ticks=iter(range(1000,10000,300))
    monkeypatch.setattr(timer.time,'time',lambda:next(ticks))
    path=tmp_path/'timing.json'
    for phase in sorted(PHASES):
        transition(path,'p',phase)
    report=transition(path,'p')
    assert not timing_errors(report,'p')
    assert summary(report)['target_met'] is False
    transition(path,'p','render_repair')
    assert timing_errors(json.loads(path.read_text()),'p')
    assert not timing_errors(transition(path,'p'),'p')


@pytest.mark.parametrize('missing',['timing','item_review'])
def test_missing_real_quality_artifacts_block(saved_run,missing):
    state,save=saved_run
    if missing=='timing':state.pop('timing')
    else:state['pdfs']['question'].pop('item_review')
    assert evaluate(state,save)['status']=='pending'


def test_clean_claim_cannot_hide_colliding_pdf(saved_run):
    state,save=saved_run
    with pymupdf.open('question.pdf') as doc:
        doc[0].insert_text((106,400),'How many integers?',fontsize=11)
        doc[0].insert_text((106,404),'(13-1)',fontsize=9)
        doc.save('revised.pdf')
    import check_hosted_run as gate
    state['pdfs']['question']['file']={'path':'revised.pdf','sha256':gate.sha(Path('revised.pdf'))}
    assert any('actual PDF answer-rail' in e for e in evaluate(state,save)['errors'])


def test_prose_only_density_waiver_is_rejected(saved_run):
    state,save=saved_run
    review=json.loads(Path('question-review.json').read_text())
    review['pages'][0]['issue_dispositions']['large-bottom-void-review'].pop('reference_pdf')
    state['pdfs']['question']['visual_review']=save('question-review.json',review)
    assert any('density-reference' in e for e in evaluate(state,save)['errors'])


def test_self_created_density_reference_is_rejected(saved_run):
    state,save=saved_run
    import check_hosted_run as gate
    with pymupdf.open('question-reference.pdf') as doc:
        doc.set_metadata({'title':'Unverified substitute'})
        doc.save('unverified-reference.pdf')
    review=json.loads(Path('question-review.json').read_text())
    review['pages'][0]['issue_dispositions']['large-bottom-void-review']['reference_pdf']={
        'path':'unverified-reference.pdf','sha256':gate.sha(Path('unverified-reference.pdf'))}
    state['pdfs']['question']['visual_review']=save('question-review.json',review)
    assert any('verified same-subject official source' in e for e in evaluate(state,save)['errors'])


def test_blind_packet_removes_labels_and_detects_shortcut_time_collapse():
    exam={'metadata':{'subject':'數學A','difficulty':'hard'},'questions':[
        {'id':'14','prompt':'Solve for requested linear combination','expected_minutes':6,
         'item_spec':{'difficulty_design':{'expert_estimate':{'difficulty_band':'very_hard'}}}}],
         'answers':[{'question_id':'14','final_answer':8,'difficulty_label':'難','reasoning':['Eliminate']}]}
    assert 'difficulty' not in json.dumps(packet(exam))
    row={'id':'14','shortest_route':'Two equation combinations','decisive_steps':['Eliminate z','Combine'],
         'shortcut_search':'No need to solve x and y','anchor_comparison':'Compared independently',
         'expected_minutes':1.5,'difficulty_band':'easy','unresolved':[]}
    errors=review_errors(exam,{'author_context':'a','reviewer_context':'b','items':[row]})
    assert any('50%' in e for e in errors) and any('two bands' in e for e in errors)


def test_blind_estimates_drive_full_paper_target_instead_of_author_labels():
    exam={'metadata':{'subject':'數學A'},'questions':[{'id':str(i),'score':5} for i in range(20)]}
    rows=[{'id':str(i),'shortest_route':'Short','decisive_steps':['One','Two'],
           'shortcut_search':'Checked','anchor_comparison':'Compared',
           'expected_minutes':2,'difficulty_band':'easy','unresolved':[]} for i in range(20)]
    errors=review_errors(exam,{'author_context':'a','reviewer_context':'b','items':rows})
    assert any('40 minutes' in e for e in errors)
    assert any('50-point' in e for e in errors)
