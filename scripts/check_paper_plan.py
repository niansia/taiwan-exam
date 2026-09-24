#!/usr/bin/env python3
"""Check a pre-authoring plan, never certify authored questions or their answers."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE='exam_packs/學測/metadata/official-current-web-sources.json'
BANDS=('簡單','中','中偏難','難')
STRANDS={'number_and_algebra','functions_and_models','geometry_and_space',
         'data_and_statistics','counting_and_probability'}
# Planning floors mirror visual-generation.md. These are product minima, not
# claims about official frequencies or proof that a planned visual is useful.
VISUAL_FLOORS={'數學A':(4,3,2,0,0),'數學B':(4,3,2,0,0),'自然':(8,2,4,4,1),
               '社會':(10,2,4,3,2),'英文':(3,2,2,0,1)}

def number(value, minimum=0):
    return type(value) in (int,float) and math.isfinite(value) and value>minimum

def profile(subject, root=ROOT):
    raw=(root/SOURCE).read_bytes()
    row=next((s for s in json.loads(raw)['subjects'] if s['subject']==subject),None)
    if row is None:raise ValueError('Unknown GSAT subject')
    return max(row['years'],key=lambda y:y['roc_year'])['paper_profile'],hashlib.sha256(raw).hexdigest()

def skeleton(subject, paper_id, year, root=ROOT):
    """Copy structure only. All author choices remain unset, never ready/pass."""
    official,_=profile(subject,root)
    items=[]
    populations=[]
    for s in official['evidence']['structure_review']['slots']:
        item={k:s.get(k) for k in ('id','number','section_id','type','score')}
        if s.get('subpart_id') is not None:item['subpart_id']=s['subpart_id']
        item.update(slot_id=s['id'],band=None,expected_minutes=None,visual_plan=None)
        if s.get('option_count'):
            labels=[str(n) for n in range(1,s['option_count']+1)]
            item.update(option_labels=labels,planned_correct_labels=[])
            if labels not in populations:populations.append(labels)
        items.append(item)
    metadata={'paper_id':paper_id,'title':f'{year}學測{subject}模擬考','exam':'學測','subject':subject,
              'curriculum':'108','generation_mode':'full-paper','calibration_level':'official-structure-only',
              'duration_minutes':official['duration_minutes'],'total_score':official['total_score'],
              'paper_difficulty_plan':{'basis':'','required_bands':list(BANDS) if len(items)>=4 else [],
                                       'target_counts':{b:None for b in BANDS},'target_points':{b:None for b in BANDS},
                                       'shared_reading_minutes':0}}
    if subject=='數學B':metadata['content_distribution_plan']={'strand_bands':{
        s:{'minimum':2,'maximum':6,'question_ids':[]} for s in sorted(STRANDS)}}
    return {'metadata':metadata,'instructions':[],
            'sections':[{'id':s['id'],'title':s['title'],'instructions':[s['instructions_pattern']]} for s in official['sections']],
            'items':items,'answer_distribution_plan':[{'option_labels':labels,'single_counts':{},'multiple_inclusion_counts':{}} for labels in populations]}

def validate(plan, root=ROOT):
    errors=[]
    meta=plan.get('metadata') or {}; subject=meta.get('subject')
    official,source_hash=profile(subject,root)
    items=plan.get('items') or []
    if not items or not all(isinstance(q,dict) for q in items):
        return {'status':'fail','errors':['items must contain scored-slot planning rows']}
    ids=[q.get('id') for q in items]
    if any(not isinstance(i,str) or not i.strip() for i in ids) or len(set(ids))!=len(ids):
        errors.append('item IDs must be nonempty and unique')
    slots={s['id']:s for s in official['evidence']['structure_review']['slots']}
    assigned=[q.get('slot_id',f"q{q.get('number')}") for q in items]
    if Counter(assigned)!=Counter(slots.keys()):errors.append('plan must cover each official scored slot exactly once')
    for q,sid in zip(items,assigned):
        slot=slots.get(sid)
        if slot:
            for key in ('number','section_id','type','score'):
                if q.get(key)!=slot.get(key):errors.append(f"{q.get('id')}: {key} differs from slot {sid}")
            if slot.get('option_count') and len(q.get('option_labels') or [])!=slot['option_count']:
                errors.append(f"{q.get('id')}: option count differs from slot {sid}")
        if not number(q.get('score')):errors.append(f"{q.get('id')}: score must be positive and finite")
        if not number(q.get('expected_minutes')):errors.append(f"{q.get('id')}: expected_minutes must be positive and finite")
        if q.get('band') not in BANDS:errors.append(f"{q.get('id')}: unknown difficulty band")
    total=sum(q['score'] for q in items if number(q.get('score')))
    duration=meta.get('duration_minutes')
    if total!=official['total_score'] or meta.get('total_score')!=official['total_score']:
        errors.append('planned total score differs from the controlling official profile')
    if duration!=official['duration_minutes']:errors.append('duration differs from the controlling official profile')
    difficulty=meta.get('paper_difficulty_plan') or meta.get('difficulty_balance_plan') or {}
    counts=Counter(q.get('band') for q in items)
    points={b:sum(q['score'] for q in items if q.get('band')==b and number(q.get('score'))) for b in BANDS}
    for b in BANDS:
        if difficulty.get('target_counts',{}).get(b)!=counts[b]:errors.append(f'{b}: target_counts mismatch')
        if difficulty.get('target_points',{}).get(b)!=points[b]:errors.append(f'{b}: target_points mismatch')
    required=difficulty.get('required_bands',list(BANDS) if len(items)>=4 else [])
    if not difficulty.get('basis') or not required or any(b not in BANDS or not counts[b] for b in required):
        errors.append('difficulty basis/required bands missing or unsatisfied')
    shared=difficulty.get('shared_reading_minutes',0)
    if type(shared) not in (int,float) or not math.isfinite(shared) or shared<0:
        errors.append('invalid shared reading time');shared=0
    minutes=sum(q['expected_minutes'] for q in items if number(q.get('expected_minutes')))+shared
    if number(duration) and minutes>duration:errors.append('planned solving time exceeds duration')
    if subject in {'數學A','數學B'}:
        if points['簡單']>=10 or points['中偏難']+points['難']<70 or points['難']<30:
            errors.append('math challenge floor: easy <10, medium-hard + hard >=70, hard >=30 points')
        if not 80<=minutes<=92:errors.append('math hand-solving plan must total 80–92 minutes')
        if any(number(q.get('expected_minutes')) and q['expected_minutes']>10 for q in items):
            errors.append('math item expected_minutes may not exceed 10')
    distribution=meta.get('content_distribution_plan') or {}
    if subject=='數學B' or distribution:
        bands=distribution.get('strand_bands',{})
        if set(bands)!=STRANDS:errors.append('content distribution must contain exactly the five strands')
        assigned_ids=[]
        for strand,rec in bands.items():
            group=rec.get('question_ids') or [];assigned_ids.extend(group)
            if not 2<=len(group)<=6 or rec.get('minimum')!=2 or rec.get('maximum')!=6:
                errors.append(f'{strand}: require 2–6 items and explicit minimum/maximum')
        if Counter(assigned_ids)!=Counter(ids):errors.append('five strands must partition the planned IDs exactly once')
    populations={}
    for q in items:
        if q.get('type') not in {'single_choice','multiple_choice'}:continue
        labels=q.get('option_labels') or [];key=q.get('planned_correct_labels') or []
        if (not all(isinstance(v,str) and v for v in labels+key) or len(set(labels))!=len(labels)
                or not key or len(set(key))!=len(key) or not set(key)<=set(labels)):
            errors.append(f"{q.get('id')}: invalid option labels/planned key");continue
        if q['type']=='single_choice' and len(key)!=1:errors.append(f"{q['id']}: single-choice needs exactly one planned label")
        population=populations.setdefault(tuple(labels),{'single_choice':[],'multiple_choice':[]})
        population[q['type']].append(key)
    answer_counts=[]
    targets=plan.get('answer_distribution_plan') or []
    for labels,pop in populations.items():
        single=Counter(x for key in pop['single_choice'] for x in key)
        multi=Counter(x for key in pop['multiple_choice'] for x in key)
        single_counts={x:single[x] for x in labels};multi_counts={x:multi[x] for x in labels}
        answer_counts.append({'option_labels':list(labels),'single_counts':single_counts,'multiple_inclusion_counts':multi_counts})
        declared=[r for r in targets if r.get('option_labels')==list(labels)]
        if len(declared)!=1 or any(declared[0].get(k)!=v for k,v in (('single_counts',single_counts),('multiple_inclusion_counts',multi_counts))):
            errors.append(f'answer distribution targets must match computed counts for {labels}')
        sequence=[key[0] for key in pop['single_choice']]
        if len(sequence)>=len(labels) and max(single_counts.values())-min(single_counts.values())>1:
            errors.append(f'single-choice planned positions are not near-even for {labels}')
        if any(len(set(sequence[i:i+4]))==1 for i in range(len(sequence)-3)):
            errors.append('four repeated single-choice planned positions')
        if any(sequence[i:i+k]==sequence[i+k:i+2*k]==sequence[i+2*k:i+3*k]
               for k in (2,3) for i in range(len(sequence)-3*k+1)):
            errors.append('mechanical single-choice planned cycle')
        # The final key test, run on the plan (periods 2-4, rotated keys): see answer_key_patterns.
        from answer_key_patterns import sequence_errors
        errors.extend(e for e in sequence_errors(sequence,list(labels),stage='planned')
                      if 'near-even' not in e and 'four identical' not in e)
    visual=[(q,q['visual_plan']) for q in items if isinstance(q.get('visual_plan'),dict)
            and q['visual_plan'].get('role') in {'evidence','required_for_solution'}]
    # Shared material counts once, including when several scored subparts use it.
    visuals={v.get('asset_id',q['id']):(q,v) for q,v in visual}
    for q,v in visual:
        if not v.get('kind') or not v.get('removal_changes_reasoning'):
            errors.append(f"{q['id']}: describe how the planned visual changes reasoning")
    floor=VISUAL_FLOORS.get(subject,(0,0,0,0,0))
    actual=(len(visuals),len({q.get('section_id') for q,v in visual}),len({v.get('kind') for q,v in visual}),
            len({v['domain'] for q,v in visual if v.get('domain')}),
            sum(v.get('sourced_photo') is True for q,v in visuals.values()))
    for label,got,minimum in zip(('visuals','visual sections','visual kinds','visual domains','sourced photos'),actual,floor):
        if got<minimum:errors.append(f'planned {label}: {got}, require at least {minimum}')
    return {'status':'plan-consistent-only' if not errors else 'fail','errors':errors,'subject':subject,
            'source_sha256':source_hash,'planned_score':total,'planned_minutes':minutes,
            'difficulty_counts':{b:counts[b] for b in BANDS},'difficulty_points':points,
            'answer_distributions':answer_counts,'visual_counts':dict(zip(('count','sections','kinds','domains','sourced_photos'),actual)),
            'limitations':['Planned answers must be replaced if actual mathematical truth differs.',
                          'A consistent plan does not certify difficulty, originality, visuals or final PDF quality.']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path,nargs='?');p.add_argument('--report',type=Path)
    p.add_argument('--plan',dest='plan_option',type=Path,help='Same as the positional plan path')
    p.add_argument('--skeleton',action='store_true');p.add_argument('--subject');p.add_argument('--paper-id');p.add_argument('--year')
    a=p.parse_args()
    a.plan=a.plan or a.plan_option
    if a.skeleton:
        if a.plan or not all((a.subject,a.paper_id,a.year,a.report)):
            p.error('--skeleton requires --subject, --paper-id, --year and a new --report path, without a plan input')
        if a.report.exists():p.error('Preserve the existing plan; choose a new output path')
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_bytes((json.dumps(skeleton(a.subject,a.paper_id,a.year),ensure_ascii=False,indent=2)+'\n').encode())
        print(json.dumps({'status':'draft-plan','path':str(a.report),'note':'Complete choices before validation.'}));return 0
    if not a.plan:p.error('Supply a plan input or --skeleton')
    try:result=validate(json.loads(a.plan.read_text(encoding='utf-8-sig')))
    except (ValueError,KeyError,TypeError,AttributeError) as e:result={'status':'fail','errors':[str(e)]}
    if a.report:
        if a.report.resolve()==a.plan.resolve():raise ValueError('Report must not overwrite the plan')
        a.report.write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
    print(json.dumps(result,ensure_ascii=False));return bool(result['errors'])

if __name__=='__main__':raise SystemExit(main())
