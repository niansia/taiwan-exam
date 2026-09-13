#!/usr/bin/env python3
"""Build a label-free difficulty packet; never synthesize a review or identity."""
import argparse
import json
import math
from pathlib import Path

REVIEW_MODES = ('independent-context', 'single-context')


def packet(exam, review_mode='independent-context'):
    if review_mode not in REVIEW_MODES:
        raise ValueError('Unknown difficulty review mode')
    questions = []
    for q in exam['questions']:
        row = {k: q[k] for k in ('id','number','section_id','type','prompt','group_stimulus',
               'continuation_pages','group_stimulus_page_splits','response_format_table') if k in q}
        if q.get('options'):
            row['options'] = [{k: option[k] for k in ('label','text')} for option in q['options']]
        if q.get('visual_asset'):
            row['visual_asset'] = {k: q['visual_asset'][k] for k in ('path','sha256','alt','caption')
                                   if k in q['visual_asset']}
        questions.append(row)
    # Author's difficulty labels/reviews and item_spec never enter the packet.
    answers = [{k: a[k] for k in ('question_id','final_answer','reasoning','explanation_blocks') if k in a}
               for a in exam.get('answers', [])]
    result = {'subject': exam['metadata']['subject'], 'questions': questions}
    # Removing answers from the artifact reduces direct answer copying. It does
    # NOT erase the same model's history or make its second pass independent.
    if review_mode == 'independent-context':
        result['answers'] = answers
    return result


def review_errors(exam, review):
    errors = []
    bands = ['very_easy','easy','medium','hard','very_hard']
    rows = {r.get('id'):r for r in review.get('items', [])}
    is_math = exam.get('metadata', {}).get('subject') in {'數學A', '數學B'}
    preceding = set()
    mode = review.get('review_mode', 'independent-context')  # Preserve legacy evidence semantics.
    if mode not in REVIEW_MODES:
        errors.append('difficulty: unknown review mode')
    elif mode == 'independent-context':
        if not review.get('reviewer_context') or review.get('author_context') == review.get('reviewer_context'):
            errors.append('difficulty: a separate blind reviewer context is required for independent-context mode')
        if review.get('independent_review') is False:
            errors.append('difficulty: contradictory independent review claim')
    else:
        if (not review.get('author_context') or
                review.get('reviewer_context') != review.get('author_context')):
            errors.append('difficulty: single-context review must retain the actual author context')
        if review.get('independent_review') is not False or not review.get('review_reason'):
            errors.append('difficulty: single-context review must disclose non-independence and capability reason')
    for question in exam['questions']:
        row = rows.get(question['id'], {})
        prefix = f'difficulty/{question["id"]}'
        if mode == 'single-context' and not (isinstance(row.get('answer_recheck'), str) and row['answer_recheck'].strip()):
            errors.append(f'{prefix}: record the fresh solving route and comparison with the saved answer')
        for field in ('shortest_route','decisive_steps','shortcut_search','anchor_comparison'):
            if not row.get(field):
                errors.append(f'{prefix}: missing {field}')
        steps = row.get('decisive_steps')
        if not isinstance(steps, list) or not steps or not all(isinstance(s,str) and s.strip() for s in steps):
            errors.append(f'{prefix}: decisive_steps must list actual decisions')
        elif len(set(s.strip().casefold() for s in steps)) != len(steps):
            errors.append(f'{prefix}: repeated arithmetic lines are not distinct decisions')
        if is_math:
            prior = row.get('uses_prior_results')
            if not isinstance(prior, list) or not all(isinstance(i,str) and i in preceding for i in prior):
                errors.append(f'{prefix}: identify only earlier items that scaffold this solution')
            if not row.get('scaffolding_audit') or type(row.get('routine_only')) is not bool:
                errors.append(f'{prefix}: classify the shortest route after option/prior-item hints')
            if row.get('routine_only') is True and row.get('difficulty_band') in {'hard','very_hard'}:
                errors.append(f'{prefix}: routine substitution cannot receive a hard label')
        preceding.add(question['id'])
        if (question.get('item_spec') or {}).get('current_event') and (not isinstance(steps,list) or len(steps) < 3):
            errors.append(f'{prefix}: topical arithmetic alone is not literacy; verify three linked decisions')
        minutes = row.get('expected_minutes')
        if type(minutes) not in (int,float) or not math.isfinite(minutes) or not 0 < minutes <= 100:
            errors.append(f'{prefix}: invalid reviewed time estimate')
            continue
        if row.get('difficulty_band') not in bands or row.get('unresolved') != []:
            errors.append(f'{prefix}: unresolved or missing reviewed judgment')
        declared = question.get('expected_minutes')
        if type(declared) in (int,float) and declared > minutes * 1.5:
            errors.append(f'{prefix}: author time exceeds reviewed estimate by over 50%; revise and rebalance')
        design = (question.get('item_spec') or {}).get('difficulty_design') or {}
        independent_band = {'very_easy':'簡單', 'easy':'簡單', 'medium':'中',
                            'hard':'中偏難', 'very_hard':'難'}.get(row.get('difficulty_band'))
        if design.get('band') and independent_band and design['band'] != independent_band:
            errors.append(f'{prefix}: adopt the reviewed band and rebalance the paper before rendering')
        estimated = design.get('expert_estimate', {}).get('difficulty_band')
        if estimated in bands and row.get('difficulty_band') in bands:
            if bands.index(estimated) - bands.index(row['difficulty_band']) >= 2:
                errors.append(f'{prefix}: author difficulty exceeds reviewed estimate by two bands')
    duration = exam.get('metadata', {}).get('duration_minutes')
    independent_total = sum(r.get('expected_minutes', 0) for r in rows.values()
                            if type(r.get('expected_minutes')) in (int,float))
    shared = (exam.get('metadata', {}).get('difficulty_balance_plan') or {}).get('shared_reading_minutes', 0)
    if type(duration) in (int,float) and type(shared) in (int,float) and independent_total + shared > duration:
        errors.append('difficulty: reviewed solving plus shared reading exceeds paper duration')
    if is_math and len(exam['questions']) == 20:
        reviewed_points = {b: sum(q.get('score', 0) or 0 for q in exam['questions']
                                  if rows.get(q['id'], {}).get('difficulty_band') == b) for b in bands}
        if reviewed_points['easy'] + reviewed_points['very_easy'] >= 10:
            errors.append('difficulty: reviewed easy score must be below 10 points')
        if reviewed_points['hard'] + reviewed_points['very_hard'] < 70:
            errors.append('difficulty: reviewed medium-hard/hard score must reach 70 points')
        if reviewed_points['very_hard'] < 30:
            errors.append('difficulty: reviewed hard score must reach 30 points')
        total = sum(r.get('expected_minutes', 0) for r in rows.values()
                    if type(r.get('expected_minutes')) in (int,float))
        if not 80 <= total <= 92:
            errors.append(f'difficulty: reviewed hand-solving total {total:g} minutes is outside existing 80-92 target')
        decision_score = sum(q.get('score', 0) or 0 for q in exam['questions']
                             if isinstance(rows.get(q['id'], {}).get('decisive_steps'), list)
                             and len(rows[q['id']]['decisive_steps']) >= 3
                             and rows[q['id']].get('routine_only') is False)
        if decision_score < 50:
            errors.append('difficulty: reviewed three-decision coverage below existing 50-point floor')
        routine_points = sum(q.get('score', 0) or 0 for q in exam['questions']
                             if rows.get(q['id'], {}).get('routine_only') is True)
        if routine_points > 25:
            errors.append(f'difficulty: routine-only routes cover {routine_points:g} points; maximum 25 under project policy')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exam', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--review-mode', choices=REVIEW_MODES, default='independent-context')
    args = parser.parse_args()
    args.output.write_text(json.dumps(packet(json.loads(args.exam.read_text(encoding='utf-8')), args.review_mode),
                                     ensure_ascii=False, indent=2), encoding='utf-8')
