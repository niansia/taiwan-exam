#!/usr/bin/env python3
"""Run every subject's structural validator on the saved exam, on any surface.

The local release gate (validate_exam_release.py) always ran the subject
validators; the hosted final checker ran only the mathematics and balance
checks, so a hosted 英文 or 自然 paper could be delivered with wrong headings,
option labels, passage lengths, missing reasoning contracts and boilerplate
explanations. This module gives both surfaces one call. Messages are plain
strings; per-item ones start with the item's number so the authoring loop can
show them while the item is fresh.

Structural passes are never editorial passes.
"""
from __future__ import annotations

from collections import Counter
import re

from validate_literacy_load import SUBJECT_FLOORS, validate as literacy_report

LITERACY_SUBJECTS = set(SUBJECT_FLOORS)
BOILERPLATE_MIN_ITEMS = 3


def _subject(exam):
    metadata = exam.get('metadata') or {}
    return metadata.get('paper_subject') or metadata.get('subject')


def _is_full_paper(exam, subject):
    metadata = exam.get('metadata') or {}
    if metadata.get('generation_mode') == 'full-paper':
        return True
    minimum = {'自然': 50, '社會': 55, '英文': 40, '國綜': 30, '國寫': 2, '數學A': 20, '數學B': 20}.get(subject, 10 ** 6)
    return len(exam.get('questions') or []) >= minimum


def _option_text(option):
    text = option.get('text') if isinstance(option, dict) else None
    return text['rich'] if isinstance(text, dict) and set(text) == {'rich'} else text


def answer_explanation_errors(exam):
    """Explanations that could not have been written for this item."""
    questions = [q for q in exam.get('questions') or [] if isinstance(q, dict)]
    answers = {a.get('question_id'): a for a in exam.get('answers') or [] if isinstance(a, dict)}
    errors = []
    reasoning_texts = Counter()
    for question in questions:
        answer = answers.get(question.get('id')) or {}
        reasoning = answer.get('reasoning') or []
        joined = ' '.join(str(step) for step in reasoning if isinstance(step, (str, dict))).strip()
        if joined:
            reasoning_texts[re.sub(r'\s+', ' ', joined.lower())] += 1
        options = question.get('options') or []
        labels = {str(o.get('label')) for o in options if isinstance(o, dict)}
        key = answer.get('final_answer')
        number = question.get('number') or question.get('id')
        if options and joined:
            # A reordered option list leaves stale numbers in prose: 「選項（3）」 must exist.
            cited = set(re.findall(r'選項\s*[（(]\s*([A-Za-z0-9]{1,2})\s*[）)]', joined))
            stale = sorted(c for c in cited if c not in labels)
            if stale:
                errors.append(f'Q{number}: the explanation cites option(s) {", ".join(stale)} that are not printed labels '
                              f'({", ".join(sorted(labels))}); options were reordered after the explanation was written')
        if options and question.get('type') == 'single_choice':
            if str(key) not in labels:
                errors.append(f'Q{number}: single-choice key {key!r} is not a printed option label')
            elif joined:
                chosen = next((_option_text(o) for o in options if str(o.get('label')) == str(key)), None)
                if isinstance(chosen, str) and chosen.strip():
                    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'’-]+", chosen) if len(w) > 3]
                    cjk = re.findall(r'[㐀-鿿]{2,}', chosen)
                    if (words or cjk) and not any(w.lower() in joined.lower() for w in words) \
                            and not any(c in joined for c in cjk):
                        errors.append(f'Q{number}: the explanation never names the selected option ({chosen[:40]})')
    for text, count in reasoning_texts.items():
        if count >= BOILERPLATE_MIN_ITEMS:
            errors.append(f'{count} items share one identical explanation ("{text[:60]}…"): write each item\'s actual reasoning')
    return errors


QUOTED_FROM_MATERIAL = re.compile(r'(?:[甲乙丙丁戊己]文?|上文|本文|下文|原文|文中|詩中|詞中|文末|文首)[^「」]{0,10}「([^「」]{1,16})」')


def material_quote_errors(exam):
    """A stem that quotes 「…」 from 甲/乙/丙/上文 must quote text the material prints.

    A hosted 國綜 item asked about the word 「久」 in 乙、丙 while 丙 contained no
    such character; the defect was found by the second reviewer after the whole
    paper was written. Checked on save instead.
    """
    errors = []
    for question in exam.get('questions') or []:
        if not isinstance(question, dict):
            continue
        material = re.sub(r'\s+', '', str(question.get('group_stimulus') or ''))
        if not material:
            continue
        prompt = str(question.get('prompt') or '')
        texts = [prompt] + [str(o.get('text') or '') for o in question.get('options') or [] if isinstance(o, dict)]
        number = question.get('number') or question.get('id')
        missing = sorted({quote for text in texts for quote in QUOTED_FROM_MATERIAL.findall(text)
                          if re.sub(r'\s+', '', quote) not in material and not re.fullmatch(r'[甲乙丙丁戊己]', quote)})
        if missing:
            errors.append(f'Q{number}: quotes 「{"」「".join(missing)}」 as words of the material, but the printed material '
                          'does not contain them; quote the text as printed or rewrite the stem')
    return errors


def english_vocabulary_errors(exam):
    """CEEC 參考詞彙表 scope from the shipped list; a missing list is itself an error."""
    from validate_english_vocabulary_scope import DEFAULT_REFERENCE, load_reference, validate_exam as vocabulary
    if not DEFAULT_REFERENCE.is_file():
        return [f'the CEEC vocabulary list is missing at {DEFAULT_REFERENCE.as_posix()}; 詞彙題 and 文意選填 scope cannot be checked']
    out = []
    for row in vocabulary(exam, load_reference(DEFAULT_REFERENCE))['errors']:
        where = f"Q{row.get('question_id')}: " if row.get('question_id') else ''
        extra = {k: v for k, v in row.items() if k not in {'code', 'question_id'}}
        out.append(where + str(row.get('code')) + (f' {extra}' if extra else ''))
    return out


def subject_gate_errors(exam, *, root=None, science_spec=None, authoring=False):
    """All subject validators that can run from the exam record alone.

    Whole-paper validators run for a full paper, and during authoring
    (`authoring=True`) so per-item messages reach the writer early; a partial
    paper checked for other reasons is not held to full-paper floors.
    """
    subject = _subject(exam)
    errors = []
    full = _is_full_paper(exam, subject) or authoring
    if subject in LITERACY_SUBJECTS and full:
        errors.extend('literacy: ' + e for e in literacy_report(exam, subject)['errors'])
    if subject == '英文' and full:
        from validate_english_layout_contract import validate_exam as english_layout
        from validate_english_difficulty_design import validate_exam as english_design
        errors.extend('english-layout: ' + e for e in english_layout(exam))
        errors.extend('english-design: ' + e for e in english_design(exam)['errors'])
        errors.extend('english-vocabulary: ' + e for e in english_vocabulary_errors(exam))
    elif subject in {'國綜', '自然'}:
        from validate_chinese_natural_scope import validate as scope
        errors.extend('scope: ' + e for e in scope(exam, science_spec)['errors'])
        if subject == '國綜' and full:
            from validate_chinese_layout_contract import validate_exam as chinese_layout
            errors.extend('chinese-layout: ' + e for e in chinese_layout(exam))
    elif subject == '社會':
        from validate_social_item_design import validate_exam as social
        for row in social(exam)['errors']:
            if isinstance(row, dict):
                where = f"Q{row.get('question_id')}: " if row.get('question_id') else ''
                extra = {k: v for k, v in row.items() if k not in {'code', 'question_id'}}
                errors.append('social: ' + where + str(row.get('code')) + (f' {extra}' if extra else ''))
            else:
                errors.append('social: ' + str(row))
        if full:
            from validate_social_layout_contract import validate_exam as social_layout
            errors.extend('social-layout: ' + e for e in social_layout(exam))
    elif subject == '國寫' and full:
        from validate_writing_layout_contract import validate_exam as writing_form
        errors.extend('writing-form: ' + e for e in writing_form(exam))
        from validate_writing_source_grounding import validate_exam as writing
        pool = (exam.get('metadata') or {}).get('writing_source_pool')
        if not isinstance(pool, dict):
            errors.append('writing: metadata.writing_source_pool (the publisher-neutral source pool) is required')
        else:
            errors.extend('writing: ' + e for e in writing(exam, pool))
    if full and root is not None:
        from pathlib import Path
        from validate_visual_item_contract import validate_exam as visuals
        errors.extend('visuals: ' + str(e) for e in visuals(exam, Path(root)).get('errors', []))
    if subject in {'數學A', '數學B'}:
        from validate_math_layout_contract import validate_exam as math_layout
        errors.extend('math-form: ' + e for e in math_layout(exam))
    if subject in {'國綜', '自然'}:
        from validate_source_grounding import item_errors as grounding_item_errors
        registry = (exam.get('metadata') or {}).get('source_registry') or {}
        sources = ({str(s.get('source_id')): s for s in registry.get('sources') or [] if isinstance(s, dict)}
                   if isinstance(registry, dict) and registry.get('sources') else None)
        for question in exam.get('questions') or []:
            if isinstance(question, dict):
                errors.extend('grounding: ' + e for e in grounding_item_errors(question, subject, sources))
    if subject == '國綜':
        errors.extend('quotes: ' + e for e in material_quote_errors(exam))
    if subject not in {'數學A', '數學B'}:
        errors.extend('answers: ' + e for e in answer_explanation_errors(exam))
    from answer_key_patterns import answer_pattern_errors
    errors.extend('answer-key: ' + e for e in answer_pattern_errors(exam, require_full=not (full or authoring)))
    return errors


def item_messages(errors, questions):
    """{item id: [messages]} for messages that name a saved item's number or id."""
    numbers = {}
    for question in questions:
        if isinstance(question, dict):
            if isinstance(question.get('number'), int):
                numbers.setdefault(str(question['number']), []).append(question.get('id'))
            numbers.setdefault(str(question.get('id')), []).append(question.get('id'))
    found = {}
    for message in errors:
        body = message.split(': ', 1)[1] if ': ' in message else message
        match = (re.match(r'(?:Q|英文第|國綜第|國寫第|數學[AB]第|第)(\d+)(?:題)?', body)
                 or re.match(r'([A-Za-z0-9_-]+):', body))
        if match:
            for qid in numbers.get(match.group(1), []):
                found.setdefault(qid, []).append(message)
    return found
