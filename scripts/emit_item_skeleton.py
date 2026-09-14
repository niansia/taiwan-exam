#!/usr/bin/env python3
"""Emit one pending item structure and exact profile fields, never a question or review."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from validate_math_difficulty_design import profile_for, profile_targets, required_decisions
from validate_paper_difficulty_balance import BANDS

ROOT=Path(__file__).resolve().parents[1]
SUBJECTS=('國綜','英文','數學A','數學B','自然','社會','國寫')
SOURCE_MAP=ROOT/'exam_packs/學測/metadata/official-current-web-sources.json'


def skeleton(subject,number=None,subpart=None,slot_id=None):
    if subject not in SUBJECTS or (slot_id is None and (type(number) is not int or number<1)):
        raise ValueError('Choose a supported subject and a positive numbered slot')
    if slot_id is not None and (number is not None or subpart is not None):
        raise ValueError('Select by slot_id or by number/subpart, not both')
    raw=SOURCE_MAP.read_bytes()
    source=next(row for row in json.loads(raw)['subjects'] if row['subject']==subject)
    year=max(source['years'],key=lambda row:row['roc_year'])
    profile=year['paper_profile']
    slots=profile['evidence']['structure_review']['slots']
    matches=[slot for slot in slots if (slot['id']==slot_id if slot_id is not None else slot['number']==number)]
    if subpart is not None:matches=[slot for slot in matches if slot.get('subpart_id')==str(subpart)]
    if len(matches)!=1:
        raise ValueError('No unique current numbered slot; use --subpart for a grouped writing item or inspect the subject profile')
    slot=matches[0]
    number=slot['number']
    question={key:slot[key] for key in ('id','number','section_id','type','score')}
    if slot.get('subpart_id'):question['subpart_id']=slot['subpart_id']
    if number is None:
        section=next(s for s in profile['sections'] if s['id']==slot['section_id'])
        question['number_display']=slot.get('printed_label') or section['title']
    question.update(prompt=None,group_stimulus=None,visual_asset=None,expected_minutes=None,
                    options=[{'label':str(i),'text':None} for i in range(1,slot.get('option_count',0)+1)])
    design={'band':None,'content_sha256':None,'basis':None,'confidence':None,
            'short_route':None,'misconception':None,'linked_decisions':[],
            'bottleneck':[],'expected_minutes':None,'shortcut_status':'pending'}
    requirements={'field_contract':'references/difficulty-field-contract.md',
                  'schema':'schemas/difficulty-design.schema.json','four_bands':list(BANDS),
                  'paper_profile':{'path':SOURCE_MAP.relative_to(ROOT).as_posix(),
                                   'sha256':hashlib.sha256(raw).hexdigest(),'reference_year':year['roc_year'],
                                   'slot':number},
                  'response_format':slot.get('response_format'),
                  'scope':'Pending structure only. Fill actual new content and review; this is not a passing exam.'}
    if subject in {'數學A','數學B'}:
        path=profile_for(subject)
        targets=profile_targets(path)
        target=targets.get(number,{})
        p=target.get('p_center')
        minimum=required_decisions(p,number,slot['type'])
        metric='constructed_response' if slot['type']=='constructed_response' else (
            'score_rate' if slot['type']=='multiple_choice' else 'answer_rate')
        design.update(target_p_center=p,target_p_range=target.get('p_range'),
                      target_d_floor=target.get('discrimination_floor'),
                      target_basis='official-profile' if p is not None else 'constructed-response-expert',
                      metric_type=metric,minimum_linked_decisions=minimum,
                      linked_decisions=[{'id':f'd{i+1}','description':None,'kind':None,
                                         'trigger_evidence':None} for i in range(minimum)],
                      representation_changes=None,constraint_checks=None,
                      misconception_paths=[{'id':f'm{i+1}','error':None,'predicted_outcome':None}
                                           for i in range(3 if slot['type'] in {'single_choice','multiple_choice'} else 2)],
                      discrimination_design={'level':None,'lower_group_move':None,'proficient_move':None},
                      shortcut_audit={'attempted_shortcuts':[],'collapse_found':None,
                                      'reviewer_decision':'pending','direct_formula_substitution_only':None},
                      innovation_audit={'formula_or_definition_recall_only':None,
                                        'skin_swap_changes_solution_graph':None,'nearest_neighbor_difference':None,
                                        'reviewer_decision':'pending'},
                      burden_audit={'arithmetic_volume_primary':None,'prose_length_primary':None,
                                    'outside_knowledge_primary':None},
                      time_audit={'expected_minutes':None,'intended_short_route':None,'calculator_required':None,
                                  'exhaustive_enumeration_required':None,'hand_calculation_feasible':None},
                      expert_estimate={'difficulty_band':None,'discrimination_level':None,'confidence':None,
                                       'status':'pending'})
        requirements['difficulty_profile']={'path':path.relative_to(ROOT).as_posix(),
                                           'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                           'target':target,'minimum_linked_decisions':minimum,
                                           'note':'Reference P/D targets are not achieved item difficulty.'}
        if subject=='數學B':
            requirements['math_b_conditions']={
                'easy_medium_minimum_linked_decisions':max(minimum,3),
                'opening_fill_in':slot['type']=='fill_in' and number in sorted(
                    s['number'] for s in slots if s['type']=='fill_in')[:3],
                'opening_fill_in_minimum_linked_decisions':3,
                'opening_fill_in_minimum_representation_plus_constraint_checks':2}
    else:
        requirements['difficulty_profile']={
            'target':None,'minimum_linked_decisions':None,
            'note':'Use this subject’s rules. No Math A/B P/D or decision minimum is inferred.'}
    question['item_spec']={'difficulty':{'label':None},'difficulty_design':design}
    return {'status':'pending-authoring','subject':subject,'question':question,
            'answer':{'question_id':slot['id'],'final_answer':None,'reasoning':[],
                      'difficulty_label':None},'requirements':requirements}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject',choices=SUBJECTS,required=True)
    selection=parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--number',type=int)
    selection.add_argument('--slot-id',help='Exact current structure slot ID, including unnumbered translation/composition')
    parser.add_argument('--subpart',help='Exact subpart ID when a printed number has several writing tasks')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=skeleton(args.subject,args.number,args.subpart,args.slot_id)
    raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    if args.output:
        if args.output.exists():raise ValueError('Preserve existing authored file; choose a new output')
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(raw)
    else:print(raw.decode('utf-8'),end='')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
