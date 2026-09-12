#!/usr/bin/env python3
"""Build a label-free difficulty packet; never synthesize a review or identity."""
import argparse
import json
from pathlib import Path


def packet(exam):
    questions = []
    for q in exam['questions']:
        row = {k: q[k] for k in ('id','number','section_id','type','prompt','group_stimulus') if k in q}
        if q.get('options'):
            row['options'] = [{k: option[k] for k in ('label','text')} for option in q['options']]
        if q.get('visual_asset'):
            row['visual_asset'] = {k: q['visual_asset'][k] for k in ('path','sha256','alt','caption')
                                   if k in q['visual_asset']}
        questions.append(row)
    # Author's difficulty labels/reviews and item_spec never enter the packet.
    answers = [{k: a[k] for k in ('question_id','final_answer','reasoning') if k in a}
               for a in exam.get('answers', [])]
    return {'subject': exam['metadata']['subject'], 'questions': questions, 'answers': answers}


def review_errors(exam, review):
    errors = []
    bands = ['very_easy','easy','medium','hard','very_hard']
    rows = {r.get('id'):r for r in review.get('items', [])}
    if not review.get('reviewer_context') or review.get('author_context') == review.get('reviewer_context'):
        errors.append('difficulty: a separate blind reviewer context is required')
    for question in exam['questions']:
        row = rows.get(question['id'], {})
        prefix = f'difficulty/{question["id"]}'
        for field in ('shortest_route','decisive_steps','shortcut_search','anchor_comparison'):
            if not row.get(field):
                errors.append(f'{prefix}: missing {field}')
        steps = row.get('decisive_steps')
        if not isinstance(steps, list) or not steps or not all(isinstance(s,str) and s.strip() for s in steps):
            errors.append(f'{prefix}: decisive_steps must list actual decisions')
        if (question.get('item_spec') or {}).get('current_event') and (not isinstance(steps,list) or len(steps) < 3):
            errors.append(f'{prefix}: topical arithmetic alone is not literacy; independently verify three linked decisions')
        minutes = row.get('expected_minutes')
        if type(minutes) not in (int,float) or not 0 < minutes <= 100:
            errors.append(f'{prefix}: invalid independent time estimate')
            continue
        if row.get('difficulty_band') not in bands or row.get('unresolved') != []:
            errors.append(f'{prefix}: unresolved or missing independent judgment')
        declared = question.get('expected_minutes')
        if type(declared) in (int,float) and declared > minutes * 1.5:
            errors.append(f'{prefix}: author time exceeds blind estimate by over 50%; revise and rebalance')
        design = (question.get('item_spec') or {}).get('difficulty_design') or {}
        estimated = design.get('expert_estimate', {}).get('difficulty_band')
        if estimated in bands and row.get('difficulty_band') in bands:
            if bands.index(estimated) - bands.index(row['difficulty_band']) >= 2:
                errors.append(f'{prefix}: author difficulty exceeds blind estimate by two bands')
    if len(exam['questions']) == 20:
        total = sum(r.get('expected_minutes', 0) for r in rows.values()
                    if type(r.get('expected_minutes')) in (int,float))
        if not 80 <= total <= 92:
            errors.append(f'difficulty: blind hand-solving total {total:g} minutes is outside existing 80-92 target')
        decision_score = sum(q.get('score', 0) or 0 for q in exam['questions']
                             if isinstance(rows.get(q['id'], {}).get('decisive_steps'), list)
                             and len(rows[q['id']]['decisive_steps']) >= 3)
        if decision_score < 50:
            errors.append('difficulty: blind three-decision coverage below existing 50-point floor')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exam', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(packet(json.loads(args.exam.read_text(encoding='utf-8'))),
                                     ensure_ascii=False, indent=2), encoding='utf-8')
