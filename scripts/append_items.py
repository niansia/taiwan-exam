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

from run_hosted_workflow import checkpoint, inside, read, record, save

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


def validate_batch(batch):
    if not isinstance(batch, dict) or set(batch) - {'questions', 'answers'}:
        raise ValueError('Batch must contain only questions and answers')
    questions, answers = batch.get('questions'), batch.get('answers')
    if not isinstance(questions, list) or not 1 <= len(questions) <= 4:
        raise ValueError('Save 2-4 authored items per batch; a first or final single item is allowed')
    if not isinstance(answers, list) or len(answers) != len(questions):
        raise ValueError('Save one authored answer for every question in the batch')
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
    current_questions, current_answers = exam.get('questions', []), exam.get('answers', [])
    if not isinstance(current_questions, list) or not isinstance(current_answers, list):
        raise ValueError('Existing exam requires question and answer lists')
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
    return {**result, 'status': 'items-saved', 'question_count': len(exam['questions']),
            'saved_item_ids': [q['id'] for q in questions], 'changed_item_ids': changed,
            'idempotent_replay': not changed, 'content_status': 'pending-review' if content_changed else saved.get('content_status', 'pending-review'),
            'reviews_approved_by_tool': False}


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
