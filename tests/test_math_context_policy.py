"""Synthetic source records test policy enforcement, not real-world facts."""
from pathlib import Path
import sys
import json
import pymupdf
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_math_context import validate, source_note_samples
from inspect_hosted_pdf import audit
from hosted_blind_review import review_errors
from test_hosted_run_evidence import saved_run, evaluate


@pytest.fixture
def paper():
    sources=[{'source_id':str(i),'event_date':'2019-08-01','published_at':'2019-08-05',
              'accessed_at':'2020-01-01','source_family':f'family-{i}',
              'canonical_url':f'https://example.org/{i}','authority_class':'primary',
              'publisher':'Synthetic publisher','title':'Synthetic source','rights_status':'facts_only_research',
              'fact_check_status':'verified','verified_facts':['Synthetic fact, not real source evidence']}
             for i in range(2)]
    questions=[{'id':str(i),'prompt':'Synthetic modelling question','item_spec':{}} for i in range(20)]
    for i in range(2):
        questions[i]['item_spec']={'scope_codes':['TEST-SCOPE'],'current_event':{
            'source_id':str(i),'event_to_model':'Preserve constrained relationship',
            'nonroutine_decision':'Compare feasible models','outside_knowledge_required':False}}
    return {'metadata':{'subject':'數學A','current_event_plan':{
        'editorial_lock_at':'2020-01-01','sources':sources}},'questions':questions}


def test_internal_urls_survive_without_appearing_on_math_paper(paper):
    assert validate(paper)==[]
    assert paper['metadata']['current_event_plan']['sources'][0]['canonical_url'].startswith('https://')


@pytest.mark.parametrize('mutation,expected',[
    ('old_event','365 days'),('future_publication','365 days'),('old_republished_event','365 days'),
    ('no_events','2-4'),('same_family','unrelated'),('unverified','verified'),
    ('outside_knowledge','self-contained'),('source_note','printed source'),('missing_scope','curriculum')])
def test_recent_date_and_literacy_records_cannot_be_omitted(paper,mutation,expected):
    records=paper['metadata']['current_event_plan']['sources']
    if mutation=='old_event':records[0]['event_date']='2018-12-31'
    elif mutation=='future_publication':records[0]['published_at']='2020-01-02'
    elif mutation=='old_republished_event':
        records[0].update(event_date='2017-01-01',published_at='2019-12-31')
    elif mutation=='no_events':
        for q in paper['questions']:q['item_spec']={}
    elif mutation=='same_family':records[1]['source_family']=records[0]['source_family']
    elif mutation=='unverified':records[0]['fact_check_status']='pending'
    elif mutation=='outside_knowledge':paper['questions'][0]['item_spec']['current_event']['outside_knowledge_required']=True
    elif mutation=='source_note':paper['questions'][0]['prompt']+='\n資料來源：某機構'
    elif mutation=='missing_scope':paper['questions'][0]['item_spec'].pop('scope_codes')
    assert any(expected in e for e in validate(paper))


def test_writing_source_notes_are_not_suppressed(paper):
    paper['metadata']['subject']='國寫'
    paper['questions'][0]['prompt']='文章（改寫自作者作品）'
    assert validate(paper)==[]


def test_note_detection_tolerates_pdf_character_spacing_and_preserves_natural_stem():
    assert source_note_samples('資 料 來 源 ： 某機構')
    assert not source_note_samples('某市試辦新的交通方案，以下為簡化模型。')


def test_actual_pdf_note_blocks_even_when_no_metadata_note(tmp_path):
    pdf=tmp_path/'math.pdf'
    with pymupdf.open() as doc:
        p=doc.new_page(width=595.28,height=841.89)
        p.insert_text((75,120),'https://example.org/source',fontsize=10)
        doc.save(pdf)
    assert audit(pdf,tmp_path/'raster',math=True)['blocking_pages']==[1]
    assert audit(pdf,tmp_path/'other-raster',math=False)['blocking_pages']==[]


def test_current_events_do_not_bypass_independent_decision_review(paper):
    paper['questions']=paper['questions'][:1]
    row={'id':'0','shortest_route':'Only calculate ratios','decisive_steps':['Divide','Multiply'],
         'shortcut_search':'No model selection needed','anchor_comparison':'Synthetic comparison',
         'expected_minutes':1,'difficulty_band':'easy','unresolved':[]}
    assert any('topical arithmetic' in e for e in review_errors(paper,{
        'author_context':'author','reviewer_context':'blind','items':[row]}))


def test_hosted_gate_checks_printed_math_fields(saved_run):
    state,save=saved_run
    paper=json.loads(Path('exam.json').read_text())
    paper['metadata']['subject']='數學A'
    paper['questions'][0]['prompt']='資料來源：某機構'
    state['exam']=save('exam.json',paper)
    assert any('printed source notes' in e for e in evaluate(state,save)['errors'])
