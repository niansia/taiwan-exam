#!/usr/bin/env python3
"""Reject answer keys that are visibly mechanical.

A hosted English paper keyed its vocabulary 1-4-3-2-1-4-3-2-1-4, its cloze
D-A-C-B-A-D-C-B-A-D, its completion bank A through J in order, its discourse
A-B-C-D and every reading group 3-2-1-4. Official keys carry no such order: a
candidate who notices the pattern answers without reading. These checks run on
the final printed label order, on every surface, for every subject.
"""
from __future__ import annotations

from collections import Counter

MIN_POPULATION_MULTIPLE = 2   # a population needs 2 x label-count answers before counts are judged
MONOTONE_RUN = 5              # A,B,C,D,E or 5,4,3,2,1 in a row (a shared option bank)
CYCLE_REPEATS = 3
NO_REPEAT_SUSPECT = 16        # P(no adjacent repeat in 16 random 4-option answers) is about 1.3%


def _single_choice_populations(exam):
    answers = {a.get('question_id'): a for a in exam.get('answers') or [] if isinstance(a, dict)}
    populations = {}
    for question in exam.get('questions') or []:
        if not isinstance(question, dict) or question.get('type') != 'single_choice':
            continue
        labels = tuple(str(o.get('label')) for o in question.get('options') or [] if isinstance(o, dict))
        answer = str((answers.get(question.get('id')) or {}).get('final_answer') or '')
        if len(labels) < 2 or len(set(labels)) != len(labels) or answer not in labels:
            continue
        populations.setdefault(labels, []).append((question.get('number'), answer, question))
    return populations


def _monotone_run(sequence, labels, length):
    """First window of `length` answers that steps +1 or -1 through the labels."""
    order = {label: i for i, label in enumerate(labels)}
    for start in range(0, len(sequence) - length + 1):
        window = [order[a] for a in sequence[start:start + length]]
        steps = {b - a for a, b in zip(window, window[1:])}
        if steps == {1} or steps == {-1}:
            return start
    return None


def _group_key(question):
    stimulus = question.get('group_stimulus')
    if isinstance(stimulus, str) and stimulus.strip():
        return ('stimulus', stimulus.strip()[:200])
    return None


def answer_pattern_errors(exam, *, require_full=True):
    metadata = exam.get('metadata') or {}
    if require_full and metadata.get('generation_mode') != 'full-paper':
        return []
    errors = []
    for labels, rows in _single_choice_populations(exam).items():
        sequence = [answer for _, answer, _ in rows]
        if len(rows) >= MIN_POPULATION_MULTIPLE * len(labels):
            counts = Counter(sequence)
            values = [counts[label] for label in labels]
            if min(values) == 0 or max(values) - min(values) > 1:
                errors.append(f'final single-choice answer positions are not near-even for {labels}: {dict(counts)}')
            run = 1
            for previous, current in zip(sequence, sequence[1:]):
                run = run + 1 if current == previous else 1
                if run >= 4:
                    errors.append('final single-choice answer key contains four identical positions in succession')
                    break
            for period in range(2, 5):
                # Two full repeats plus a partial third already give the pattern
                # away: the paper's vocabulary key 1-4-3-2-1-4-3-2-1-4 has ten items.
                needed = 2 * period + 2  # p=2 needs three repeats; p=4 needs two and a half
                longest, stretch = 0, period
                for i in range(period, len(sequence)):
                    stretch = stretch + 1 if sequence[i] == sequence[i - period] else period
                    longest = max(longest, stretch)
                if longest >= needed:
                    errors.append(f'final single-choice answer key contains a mechanical period-{period} cycle over {longest} items')
                    break
            if len(sequence) >= NO_REPEAT_SUSPECT and all(a != b for a, b in zip(sequence, sequence[1:])):
                errors.append(f'{len(sequence)} consecutive single-choice answers never repeat a position: a rotated '
                              'key, not a random one (official keys repeat neighbours regularly)')
        if len(sequence) >= MONOTONE_RUN:
            start = _monotone_run(sequence, labels, MONOTONE_RUN)
            if start is not None:
                first = rows[start][0]
                errors.append(f'answer key runs through the labels in order from Q{first} '
                              f'({", ".join(sequence[start:start + MONOTONE_RUN])}): a candidate can answer by the pattern')
        # A bank shared by many gaps (文意選填 A-J, 篇章結構 A-E): its answers must not
        # be the bank in order, and every option is used at most as often as the form allows.
        if len(labels) >= 5 and len(sequence) >= len(labels) - 1:
            order = {label: i for i, label in enumerate(labels)}
            indices = [order[a] for a in sequence]
            if indices == sorted(indices) or indices == sorted(indices, reverse=True):
                errors.append(f'the {len(labels)}-option bank is keyed in label order ({", ".join(sequence)}); shuffle the bank')
        # Groups sharing one stimulus must not repeat one another's answer sequence.
        groups = {}
        for number, answer, question in rows:
            key = _group_key(question)
            if key:
                groups.setdefault(key, []).append(answer)
        seen = {}
        for key, group_sequence in groups.items():
            if len(group_sequence) >= 3:
                signature = tuple(group_sequence)
                if signature in seen:
                    errors.append(f'two item groups share the same answer sequence {"-".join(signature)}; reorder options in one of them')
                    break
                seen[signature] = key
    return errors
