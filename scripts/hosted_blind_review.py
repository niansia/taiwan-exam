#!/usr/bin/env python3
"""Build a label-free difficulty packet; never synthesize a review or identity."""
import argparse
import json
import math
from pathlib import Path

REVIEW_MODES = ('independent-context', 'single-context')
# Math A/B reviewers estimate each item's 答對率 and the band follows from it (maintainer
# decision 2026-09-24): 難 below 0.30 and 中偏難 below 0.50, the cutoffs at which the
# official 115 數學B scores exactly 70 and 30 points, the project's floors. Without them
# hosted reviewers placed the same item on either side of 0.50 in successive rounds.
CHINESE_MEAN_P_MAX = 0.62
# 社會 111-115 objective items average 0.60, 0.51, 0.55, 0.52, 0.57 (official statistics); two
# hosted 116 papers had keys that were the longest option in 40 and 42 of 54 items.
SOCIAL_MEAN_P_MAX = 0.65
MATH_P_BANDS = ((0.30, 'very_hard'), (0.50, 'hard'), (0.70, 'medium'), (0.85, 'easy'), (1.01, 'very_easy'))


def band_for_p(p):
    return next(band for edge, band in MATH_P_BANDS if p < edge)


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
        if is_math:
            p = row.get('estimated_p')
            if type(p) not in (int, float) or not 0 <= p <= 1:
                errors.append(f'{prefix}: record estimated_p, the reviewer estimate of the 答對率 (0-1); the band follows from it')
            elif row.get('difficulty_band') in bands and band_for_p(p) != row['difficulty_band']:
                errors.append(f'{prefix}: estimated_p {p:g} is band {band_for_p(p)} (難 <0.30, 中偏難 0.30-0.50, '
                              f'中 0.50-0.70, 簡單 >=0.70), not {row["difficulty_band"]}')
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
    if exam.get('metadata', {}).get('subject') == '國綜':
        # Official 國綜 papers average 0.48-0.58 (111-115); two hosted 116 papers were
        # estimated at 0.70 and 0.80, with keys that were usually the longest option.
        estimates = [rows.get(q['id'], {}).get('estimated_p') for q in exam['questions']]
        if not all(type(p) in (int, float) and 0 <= p <= 1 for p in estimates):
            errors.append('difficulty: record estimated_p (the predicted 答對率, 0-1) for every 國綜 item')
        elif estimates and sum(estimates) / len(estimates) > CHINESE_MEAN_P_MAX:
            errors.append(f'difficulty: reviewed mean 答對率 {sum(estimates) / len(estimates):.2f} is easier than any official '
                          f'國綜 paper (111-115: 0.48-0.58; ceiling {CHINESE_MEAN_P_MAX})')
    if exam.get('metadata', {}).get('subject') == '社會':
        chosen = [q for q in exam['questions'] if q.get('options')]
        estimates = [rows.get(q['id'], {}).get('estimated_p') for q in chosen]
        if not all(type(p) in (int, float) and 0 <= p <= 1 for p in estimates):
            errors.append('difficulty: record estimated_p (the predicted 答對率, 0-1) for every 社會 choice item')
        elif estimates and sum(estimates) / len(estimates) > SOCIAL_MEAN_P_MAX:
            errors.append(f'difficulty: reviewed mean 答對率 {sum(estimates) / len(estimates):.2f} of the choice items is easier '
                          f'than any official 社會 paper (111-115: 0.51-0.60; ceiling {SOCIAL_MEAN_P_MAX}): make distractors '
                          'as long and plausible as the key, each failing on one specific concept')
    duration = exam.get('metadata', {}).get('duration_minutes')
    independent_total = sum(r.get('expected_minutes', 0) for r in rows.values()
                            if type(r.get('expected_minutes')) in (int,float))
    shared = (exam.get('metadata', {}).get('difficulty_balance_plan') or exam.get('metadata', {}).get('paper_difficulty_plan') or {}).get('shared_reading_minutes', 0)
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
        # Official 111-115 close 選填 and the 題組 with their hardest items (115 16-17 and
        # 20, 114 16-17 and 20, 113 17 and 20); two hosted 116 數A papers ended 選填 on a
        # textbook maximum and the 題組 on completing a square.
        for number in (17, 20):
            closing = next((q for q in exam['questions'] if q.get('number') == number), None)
            if closing and rows.get(closing['id'], {}).get('difficulty_band') not in {'hard', 'very_hard'}:
                errors.append(f'difficulty/{closing["id"]}: item {number} closes its part and must review hard or very_hard, '
                              'as every official 111-115 paper does; redesign it before rendering')
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
    parser.add_argument('exam', type=Path, nargs='?')
    parser.add_argument('output', type=Path, nargs='?')
    parser.add_argument('--exam', dest='exam_option', type=Path, help='Same as the first positional argument')
    parser.add_argument('--output', dest='output_option', type=Path, help='Same as the second positional argument')
    parser.add_argument('--review-mode', choices=REVIEW_MODES, default='independent-context')
    args = parser.parse_args()
    args.exam = args.exam or args.exam_option
    args.output = args.output or args.output_option
    if not args.exam or not args.output:
        parser.error('Give the exam and the output path (positionally or with --exam/--output)')
    args.output.write_text(json.dumps(packet(json.loads(args.exam.read_text(encoding='utf-8')), args.review_mode),
                                     ensure_ascii=False, indent=2), encoding='utf-8')
