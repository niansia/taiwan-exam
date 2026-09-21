#!/usr/bin/env python3
"""Persist a small authored question/answer batch; never generate or approve items.

The exam is replaced atomically before its checkpoint. If the process stops in
between, retrying identical bytes reconciles the checkpoint without duplication.
Existing different items need --replace. Review artifacts remain intact and
their old exam hashes no longer validate changed content.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

from hosted_item_triage import crop_reasons, needs_crop
from run_hosted_workflow import (authoring_issues, checkpoint, figure_pagination_risks, inside, read, record, save,
                                 text_issues)
from validate_current_context import progress as context_progress, validate as current_context_errors
from validate_math_difficulty_design import validate as math_design
from validate_paper_difficulty_balance import validate as difficulty_balance

# Subparts print in subpart_id order. An id that starts with its printed
# ordinal (1, 2-a, b …) cannot be sorted out of order; a bare name can.
ORDERED_SUBPART = re.compile(r'^(?:\d+|[a-z])(?:$|[-_.])')
EARLY_PLAN_ITEMS = 20
TEXT_ONLY_BATCH_ITEMS = 6
# Words that make an option absolute. Such a distractor is wrong only if no
# condition makes it true; the writer confirms that once, when the item is saved.
ABSOLUTE_CLAIM = re.compile(r'必定|一定|必然|必|只有|只能|只|僅|無關|皆|所有|全部|不可能|永遠|從不|唯一|任何|一律|'
                            r'\b(?:always|never|only|all|none|impossible|every|entirely|solely)\b', re.I)


def absolute_claim_options(questions):
    """Options whose wording is absolute; a reminder, never a rejection."""
    rows = []
    for question in questions:
        for option in question.get('options') or []:
            text = option.get('text') if isinstance(option, dict) else None
            raw = text['rich'] if isinstance(text, dict) and set(text) == {'rich'} else text
            if isinstance(raw, str):
                match = ABSOLUTE_CLAIM.search(raw)
                if match:
                    rows.append({'id': question.get('id'), 'label': option.get('label'), 'word': match.group(),
                                 'text': raw[:60]})
    return rows


def proof_triage(questions, answers, *, first_batch):
    """Which saved items need an early crop proof, and why.

    Text-only items print through the same paragraph path as every earlier
    proof; their final-build crops and page review still inspect them. Figures,
    formulas, rails, tables, gaps and split stimuli are where early proofs have
    found defects, so those are proofed now.
    """
    by_answer = {a.get('question_id'): a for a in answers}
    recommended, optional = {}, []
    for question in questions:
        qid = question.get('id')
        reasons = (['first batch: verify the renderer, font and section layout once'] if first_batch else [])
        reasons += crop_reasons(question, by_answer.get(qid, {}))
        if reasons:
            recommended[qid] = reasons
        else:
            optional.append(qid)
    return {'proof_recommended': recommended, 'proof_optional': optional,
            'proof_note': ('Proof the recommended items now (their crops carry forward to the final build). '
                           'Text-only items need no proof: the final build reads them on their reviewed page images.')}


def design_gaps(exam, root, questions):
    """{final-check message: [item ids]} for the saved items, while they are fresh.

    The final check reads the same validators. Their fields (item_spec,
    expected_minutes) are not printed, so completing them after a review or a
    build keeps the page and crop reviews; waiting until finalize costs a repair.
    """
    messages = list(difficulty_balance(exam, root)['errors'])
    if exam.get('metadata', {}).get('subject') in {'數學A', '數學B'}:
        messages += math_design(exam)['errors']
    # Per-item record defects only; the whole-paper floors are reported as progress.
    messages += [m for m in current_context_errors(exam) if not m.startswith('current_context:')]
    gaps = {}
    for question in questions:
        prefixes = (question['id'] + ':', f"Q{question.get('number')}:")
        for message in messages:
            if message.startswith(prefixes):
                gaps.setdefault(message.split(':', 1)[1].strip(), []).append(question['id'])
    return gaps

def check_numbering(questions):
    """Numbered subparts share a printed number; unnumbered tasks use IDs."""
    groups={}
    for q in questions:
        n=q.get('number')
        if n is not None and (type(n) is not int or n<=0):
            raise ValueError('Question number must be a positive integer or null')
        if n is None:
            if not (q.get('number_display') or q.get('answer_label')):
                raise ValueError('Unnumbered task requires its actual number_display or answer_label')
            continue
        sub=q.get('subpart_id')
        if sub is not None and (not isinstance(sub,str) or not sub.strip()):
            raise ValueError('subpart_id must be a nonempty string when supplied')
        group=groups.setdefault(n,[])
        if group and (sub is None or None in group or sub in group):
            raise ValueError('Question number collides; same-number scored subparts require unique subpart_id')
        group.append(sub)
    for n,subs in groups.items():
        if len(subs)<2:
            continue
        unordered=[s for s in subs if not ORDERED_SUBPART.match(s)]
        if unordered:
            raise ValueError(f'Question {n}: subparts print in subpart_id order, so ids sharing one number must '
                             f'start with their printed ordinal (1, 2, 1-plot, 2-calculation or a, b); rename '
                             + ', '.join(sorted(unordered)))
        if len({s[0].isdigit() for s in subs})>1:
            raise ValueError(f'Question {n}: use one ordering scheme for its subparts, either 1, 2, … or a, b, …')


def validate_batch(batch):
    if not isinstance(batch, dict) or set(batch) - {'questions', 'answers'}:
        raise ValueError('Batch must contain only questions and answers')
    questions, answers = batch.get('questions'), batch.get('answers')
    if not isinstance(questions, list) or not 1 <= len(questions) <= TEXT_ONLY_BATCH_ITEMS:
        raise ValueError(f'Save 2-4 authored items per batch (up to {TEXT_ONLY_BATCH_ITEMS} when every item is '
                         'text-only); a first or final single item is allowed')
    if not isinstance(answers, list) or len(answers) != len(questions):
        raise ValueError('Save one authored answer for every question in the batch')
    if len(questions) > 4:
        by_id = {a.get('question_id'): a for a in answers if isinstance(a, dict)}
        needing = [q.get('id') for q in questions if isinstance(q, dict) and needs_crop(q, by_id.get(q.get('id')))]
        if needing:
            raise ValueError('Batches of 5-6 items are for text-only items; these need their own proof, so save '
                             'them in a batch of at most 4: ' + ', '.join(map(str, needing)))
    ids = set()
    for q in questions:
        if not isinstance(q, dict):
            raise ValueError('Each question must be an object')
        for name in ('id', 'section_id', 'type', 'prompt'):
            if not isinstance(q.get(name), str) or not q[name].strip():
                raise ValueError('Each question requires a nonempty ' + name)
        if 'number' not in q:raise ValueError('Each question requires number (null for an unnumbered task)')
        if q['id'] in ids:raise ValueError('Duplicate question ID within the batch')
        ids.add(q['id'])
        if 'options' in q:
            options = q['options']
            if (not isinstance(options, list) or any(not isinstance(o, dict) or
                    not isinstance(o.get('label'), str) or not o['label'].strip() or
                    not isinstance(o.get('text'), str) or not o['text'].strip() for o in options)):
                raise ValueError('Options require authored label and text')
            if len({o['label'] for o in options}) != len(options):
                raise ValueError('Duplicate option label')
    check_numbering(questions)
    answer_ids = set()
    for a in answers:
        if (not isinstance(a, dict) or a.get('question_id') not in ids or
                a['question_id'] in answer_ids or 'final_answer' not in a):
            raise ValueError('Answer IDs must match the batch exactly and include final_answer')
        reasoning, explanations = a.get('reasoning'), a.get('explanation_blocks')
        has_reasoning = (isinstance(reasoning, list) and bool(reasoning) and
                         all(isinstance(step, str) and step.strip() for step in reasoning))
        has_explanations = (isinstance(explanations, list) and bool(explanations) and
                            all(isinstance(block, dict) and isinstance(block.get('content'), str) and
                                block['content'].strip() for block in explanations))
        if not (has_reasoning or has_explanations):
            raise ValueError('Save actual solution reasoning with each answer')
        answer_ids.add(a['question_id'])
    return questions, answers


def append(run_dir, batch, *, state=None, plan=None, replace=False):
    root = Path(run_dir).resolve()
    preflight = read(root / 'preflight.json')
    if preflight.get('status') != 'ready-for-authoring':
        raise ValueError('Finish preflight before saving authored items')
    state_path = inside(root, state) if state else root / 'run-state.json'
    if state_path.parent != root or state_path.name in {'exam.json', 'preflight.json', 'generation-timing.json'}:
        raise ValueError('Use the actual run-state file directly inside the run')
    if state_path.exists():
        existing_state = read(state_path)
        if (existing_state.get('paper_id') != preflight.get('paper_id') or
                existing_state.get('subject') != preflight.get('subject')):
            raise ValueError('Run state belongs to another paper or subject')
    else:
        existing_state = {}
    supplied = read(batch)
    questions, answers = validate_batch(supplied)
    exam_path = root / 'exam.json'
    if exam_path.exists():
        exam = read(exam_path)
    else:
        if not plan:
            raise ValueError('The first batch requires --plan with the actual paper metadata, instructions and sections')
        exam = copy.deepcopy(read(plan))
        if (not isinstance(exam, dict) or not isinstance(exam.get('metadata'), dict) or
                not isinstance(exam.get('instructions'), list) or not isinstance(exam.get('sections'), list) or
                exam.get('questions') or exam.get('answers')):
            raise ValueError('Initial plan requires metadata, instructions and sections, without prewritten question batches')
        for name in ('title', 'exam', 'calibration_level'):
            if not isinstance(exam['metadata'].get(name), str) or not exam['metadata'][name].strip():
                raise ValueError('Initial plan must supply actual metadata.' + name)
        for name in ('paper_id', 'subject'):
            exam['metadata'].setdefault(name, preflight[name])
        # The separate plan may contain planning-only rows and answer quotas.
        # They are not generated-exam schema fields or a source of questions.
        exam={key:exam[key] for key in ('metadata','instructions','sections')}
        exam['questions'], exam['answers'] = [], []
    for name in ('paper_id', 'subject'):
        if exam.get('metadata', {}).get(name) != preflight.get(name):
            raise ValueError('Exam metadata belongs to another paper or subject')
    section_ids = {s.get('id') for s in exam.get('sections', []) if isinstance(s, dict)}
    if not section_ids or any(q['section_id'] not in section_ids for q in questions):
        raise ValueError('Question section_id must name a section in the saved paper plan')
    # Literal LaTeX, dollar signs, broken markup and unregistered formula images
    # otherwise surface only after rendering and page review; fix them now.
    issues = [f'section {s.get("id")} {key}: {issue}' for s in exam['sections'] if isinstance(s, dict)
              for key, value in [('title', s.get('title')), *[('instructions', v) for v in s.get('instructions') or []]]
              for issue in text_issues(value)]
    issues += authoring_issues(questions, answers, root=root)
    if issues:
        raise ValueError(f'Fix {len(issues)} print issue(s), then save the batch again: ' + ' | '.join(issues))
    current_questions, current_answers = exam.get('questions', []), exam.get('answers', [])
    if not isinstance(current_questions, list) or not isinstance(current_answers, list):
        raise ValueError('Existing exam requires question and answer lists')
    first_batch = not current_questions
    by_id = {q['id']: q for q in current_questions}
    by_answer = {a['question_id']: a for a in current_answers}
    if len(by_id) != len(current_questions) or len(by_answer) != len(current_answers):
        raise ValueError('Existing exam has duplicate IDs; resolve before appending')
    changed = []
    for question in questions:
        qid = question['id']
        answer = next(a for a in answers if a['question_id'] == qid)
        old, old_answer = by_id.get(qid), by_answer.get(qid)
        if old is not None or old_answer is not None:
            if old == question and old_answer == answer:
                continue  # Safe replay after a crash or repeated Continue message.
            if not replace:
                raise ValueError('Different existing item requires --replace: ' + qid)
        changed.append(qid)
        by_id[qid], by_answer[qid] = question, answer
    check_numbering(list(by_id.values()))
    if set(by_answer) != set(by_id):
        raise ValueError('The saved question and answer IDs do not match')
    sections={s['id']:i for i,s in enumerate(exam['sections'])}
    def order(q):
        sub=re.sub(r'\d+',lambda m:m.group().zfill(8),q.get('subpart_id',''))
        return (sections[q['section_id']],q['number'] is None,q['number'] or 0,sub)
    exam['questions'] = sorted(by_id.values(), key=order)
    exam['answers'] = [by_answer[q['id']] for q in exam['questions']]
    # Never overwrite review reports or mutate their exam hashes to make them pass.
    # Atomic exam first: a crash before checkpoint leaves recoverable, real content.
    if changed or not exam_path.exists():
        save(exam_path, exam)
    before = existing_state.get('exam')
    content_changed = before != record(root, exam_path)
    result = checkpoint(root, 'authoring' if content_changed else None, state=state_path)
    saved = read(state_path)
    if content_changed:
        saved['current_phase'] = 'authoring'
        saved['next_action'] = 'Continue this paper from saved items; review new or changed content before final delivery.'
        saved['content_status'] = 'pending-review'
        save(state_path, saved)
    report = {**result, 'status': 'items-saved', 'question_count': len(exam['questions']),
              'saved_item_ids': [q['id'] for q in questions], 'changed_item_ids': changed,
              'idempotent_replay': not changed, 'content_status': 'pending-review' if content_changed else saved.get('content_status', 'pending-review'),
              'reviews_approved_by_tool': False}
    gaps = design_gaps(exam, root, questions)
    if gaps:
        report['design_fields_pending'] = gaps
        report['design_note'] = ('The final check requires these difficulty-design fields. They are not printed: '
                                 'complete them with --replace as the batch is solved and reviewed; page reviews stay valid.')
    report.update(proof_triage(questions, answers, first_batch=first_batch))
    context = context_progress(exam)
    if context:
        report['current_context_progress'] = context
        report['current_context_note'] = ('Verified recent sources and tagged Taiwan/hazard/climate contexts so far against '
                                          'the subject floor (references/current-form-topicality.md); plan the remaining '
                                          'recent items now, not after the paper is paginated.')
    absolute = absolute_claim_options(questions)
    if absolute:
        report['absolute_claim_options'] = absolute
        report['absolute_claim_note'] = ('For each absolute wording ask once: is there any condition under which this '
                                         'option is true? If so, reword it before proof; a correct key is unaffected.')
    risks = figure_pagination_risks(questions, answers, root=root, subject=exam['metadata'].get('subject'))
    if risks:
        report['layout_risks'] = risks
    # About a third of a 自然/社會/英文 paper, or most of a 國綜/數學 paper.
    if len(exam['questions']) >= EARLY_PLAN_ITEMS and not (root / 'content-lock.json').exists():
        report['plan_hint'] = ('Enough items are saved to learn the pagination rhythm: run specs, then '
                               '`run_hosted_workflow.py plan` (seconds, no PDFs) and fix tall figures or '
                               'over-long groups now instead of after the whole paper is paginated.')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--batch', required=True, type=Path)
    parser.add_argument('--state', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--replace', action='store_true')
    args = vars(parser.parse_args())
    try:
        result = append(**args)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({'status': 'pending', 'errors': [str(exc)]}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
