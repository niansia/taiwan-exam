import copy
import random
from collections import Counter
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_paper_plan import BANDS,STRANDS,profile,validate

def make_plan(subject):
    official,_=profile(subject);items=[]
    for i,s in enumerate(official['evidence']['structure_review']['slots']):
        q={k:s.get(k) for k in ('id','number','section_id','type','score')}
        q.update(slot_id=s['id'],band=BANDS[i%4],expected_minutes=official['duration_minutes']*.85/official['scored_item_count'])
        if subject in {'數學A','數學B'}:
            q.update(band='簡單' if s['number']==18 else '中' if i<3 else '中偏難' if i<11 else '難',expected_minutes=4.3)
        if q['type'] in ('single_choice','multiple_choice'):
            q['option_labels']=[str(n) for n in range(1,s['option_count']+1)]
        q['visual_plan']={'asset_id':q['id'],'kind':f'kind-{i%4}','role':'evidence',
                          'domain':f'domain-{i%4}','sourced_photo':i<2,
                          'removal_changes_reasoning':'Synthetic plan fixture; no generated student content.'}
        items.append(q)
    populations={}
    for q in items:
        if 'option_labels' not in q:continue
        labels=tuple(q['option_labels']);p=populations.setdefault(labels,{'single':[],'multi':[]})
        if q['type']=='single_choice':
            # Balanced but not rotated: each block of len(labels) keys is a seeded shuffle.
            n=len(p['single']);block=list(labels);random.Random(n//len(labels)).shuffle(block)
            q['planned_correct_labels']=[block[n%len(labels)]];p['single']+=q['planned_correct_labels']
        else:q['planned_correct_labels']=list(labels[:2]);p['multi']+=q['planned_correct_labels']
    counts=Counter(q['band'] for q in items)
    meta={'subject':subject,'duration_minutes':official['duration_minutes'],'total_score':official['total_score'],
          'paper_difficulty_plan':{'basis':'Synthetic test planning only','required_bands':list(counts),
          'target_counts':{b:counts[b] for b in BANDS},
          'target_points':{b:sum(q['score'] for q in items if q['band']==b) for b in BANDS}}}
    if subject=='數學B':
        meta['content_distribution_plan']={'strand_bands':{s:{'question_ids':[q['id'] for q in items[j*4:j*4+4]],'minimum':2,'maximum':6}
                                                        for j,s in enumerate(sorted(STRANDS))}}
    answer=[{'option_labels':list(labels),'single_counts':{v:p['single'].count(v) for v in labels},
             'multiple_inclusion_counts':{v:p['multi'].count(v) for v in labels}} for labels,p in populations.items()]
    return {'metadata':meta,'items':items,'answer_distribution_plan':answer}

@pytest.mark.parametrize('subject',['國綜','英文','數學A','數學B','自然','社會','國寫'])
def test_all_subject_plans_use_actual_scored_slots(subject):
    result=validate(make_plan(subject))
    assert not result['errors'],result['errors']
    assert result['status']=='plan-consistent-only'

@pytest.mark.parametrize('change,error',[
    (lambda p:p['items'].pop(),'scored slot'),
    (lambda p:p['items'][0].update(score=7),'score'),
    (lambda p:p['items'][0].update(expected_minutes=50),'minutes'),
    (lambda p:[q.update(band='簡單') for q in p['items'][:2]],'easy <10'),
    (lambda p:p['items'][0].update(planned_correct_labels=['6']),'planned key'),
    (lambda p:p['answer_distribution_plan'][0]['multiple_inclusion_counts'].update({'1':0}),'answer distribution'),
    (lambda p:p['metadata']['paper_difficulty_plan']['target_counts'].update({'難':0}),'target_counts'),
    (lambda p:[q.pop('visual_plan') for q in p['items']],'planned visuals'),
])
def test_catches_expensive_plan_mistakes_before_authoring(change,error):
    plan=make_plan('數學A');change(plan)
    assert any(error in e for e in validate(plan)['errors'])

def test_strands_are_an_exact_partition():
    plan=make_plan('數學B');bands=plan['metadata']['content_distribution_plan']['strand_bands']
    rows=list(bands.values());rows[0]['question_ids'][0]=rows[1]['question_ids'][0]
    assert any('partition' in e for e in validate(plan)['errors'])

def test_planned_visual_material_is_deduplicated():
    plan=make_plan('自然')
    for q in plan['items']:q['visual_plan']['asset_id']='same-figure'
    assert any('planned visuals' in e for e in validate(plan)['errors'])


def test_plan_rejects_a_four_item_rotation_like_the_final_key_check():
    # A hosted 社會 plan keyed 29-43 in a four-item cycle and passed its plan check.
    plan=make_plan('社會')
    single=[q for q in plan['items'] if q.get('type')=='single_choice']
    for i,q in enumerate(single):q['planned_correct_labels']=[q['option_labels'][i%4]]
    labels=tuple(single[0]['option_labels'])
    for row in plan['answer_distribution_plan']:
        if tuple(row['option_labels'])==labels:
            row['single_counts']={v:sum(q['planned_correct_labels']==[v] for q in single) for v in labels}
    assert any('period-4 cycle' in e for e in validate(plan)['errors'])
