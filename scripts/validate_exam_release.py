"""Fail-closed content/delivery gate. Reports are local evidence, not certificates.

The external contract preserves the user's requested product even when exam
metadata is changed to custom-practice. No rendering or publication is done here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from pack_verification import paper_errors, layout_errors, digest, positive_score
from validate_paper_difficulty_balance import content_hash

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_check(name, args):
    try:
        result = subprocess.run([sys.executable, str(ROOT / 'scripts' / name), *map(str, args)],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
        return {'check': name, 'exit_code': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'check': name, 'exit_code': -1, 'error': str(exc)}


def independent_answer_errors(exam):
    errors = []; answers = exam.get('answers') or []
    by_id = {a.get('question_id'): a for a in answers}
    ids = {q.get('id') for q in exam.get('questions', [])}
    if None in ids or '' in ids or len(ids) != len(exam.get('questions', [])):
        errors.append('question ids missing or duplicated')
    if len(by_id) != len(answers) or set(by_id) != ids:
        errors.append('answer ids missing, duplicated or extraneous')
    subject = (exam.get('metadata') or {}).get('paper_subject') or (exam.get('metadata') or {}).get('subject')
    section_titles = {s.get('id'): s.get('title', '') for s in exam.get('sections', [])}
    for q in exam.get('questions', []):
        a = by_id.get(q.get('id'), {}); r = a.get('independent_review') or {}
        if r.get('question_sha256') != content_hash(q) or r.get('answer_sha256') != digest({k:v for k,v in a.items() if k != 'independent_review'}):
            errors.append(f'Q{q.get("number")}: missing/stale question-and-answer review')
        if not all(r.get(k) for k in ('reviewer', 'solution', 'difficulty_rationale', 'shortest_route', 'reviewed_at')) or r.get('answer_visible_during_solve') is not False or r.get('unresolved') != []:
            errors.append(f'Q{q.get("number")}: independent solving evidence incomplete')
        if a.get('final_answer') in (None, '') or not a.get('reasoning'):
            errors.append(f'Q{q.get("number")}: answer/explanation absent')
        if r.get('derived_answer') != a.get('final_answer'):
            errors.append(f'Q{q.get("number")}: independently derived answer and published key disagree or are missing')
        labels = {o.get('label') for o in q.get('options') or []}
        options = q.get('options') or []
        texts = [re.sub(r'\s+', '', str(o.get('text', ''))) for o in options]
        if len(labels) != len(options) or len(set(texts)) != len(texts) or (options and (None in labels or '' in labels or '' in texts)):
            errors.append(f'Q{q.get("number")}: duplicate or empty option label/text')
        if q.get('type') == 'single_choice' and a.get('final_answer') not in labels:
            errors.append(f'Q{q.get("number")}: single-choice key is not a printed option')
        if labels and set((r.get('option_verdicts') or {}).keys()) != labels:
            errors.append(f'Q{q.get("number")}: every option requires a truth/evidence review')
        if labels and not all(isinstance(v, str) and v.strip() for v in (r.get('option_verdicts') or {}).values()):
            errors.append(f'Q{q.get("number")}: empty option-verdict evidence')
        title = section_titles.get(q.get('section_id'), '')
        if subject == '英文' and (q.get('type') == 'fill_in' or q.get('suppress_question_display') or any(t in title for t in ('綜合測驗', '文意選填', '篇章結構'))):
            if not r.get('completed_text') or '[[' in r['completed_text']:
                errors.append(f'Q{q.get("number")}: completed English passage/sentence reinsertion review missing')
        if q.get('type') in {'constructed_response', 'guided_writing'} and not r.get('rubric_review'):
            errors.append(f'Q{q.get("number")}: constructed response needs rubric/equivalence review')
    return errors


def answer_distribution_errors(exam):
    """Reject conspicuous answer-key artifacts in a complete paper.

    This operates on the final printed label order.  It intentionally checks
    homogeneous single-choice populations only; multiple-selection inclusion
    frequencies need a separate subject-aware review.
    """
    meta = exam.get('metadata') or {}
    if meta.get('generation_mode') != 'full-paper':
        return []
    answer_by_id = {a.get('question_id'): a for a in exam.get('answers') or []}
    populations = {}
    for question in exam.get('questions') or []:
        if question.get('type') != 'single_choice':
            continue
        labels = tuple(str(option.get('label')) for option in question.get('options') or [])
        answer = str((answer_by_id.get(question.get('id')) or {}).get('final_answer') or '')
        if len(labels) < 2 or len(set(labels)) != len(labels) or answer not in labels:
            continue
        populations.setdefault(labels, []).append((question.get('number'), answer))
    errors = []
    for labels, numbered_answers in populations.items():
        if len(numbered_answers) < 2 * len(labels):
            continue
        sequence = [answer for _, answer in numbered_answers]
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
        for period in range(2, min(5, len(sequence) // 3 + 1)):
            span = period * 3
            if any(sequence[start:start + period] * 3 == sequence[start:start + span]
                   for start in range(0, len(sequence) - span + 1)):
                errors.append(f'final single-choice answer key contains a mechanical period-{period} cycle repeated three times')
                break
    return errors


def source_link_errors(exam, registry):
    if isinstance(registry, dict):
        registry = registry.get('sources') or []
    ids = {r.get('id', r.get('source_id')) for r in registry}
    errors = []
    for q in exam.get('questions', []):
        spec = q.get('item_spec') or {}
        refs = set(spec.get('source_ids') or []) | set(q.get('source_ids') or []) | set((spec.get('literacy') or {}).get('source_ids') or [])
        for ref in refs:
            if ref not in ids:
                errors.append(f'Q{q.get("number")}: unresolved source id {ref}')
    return errors


def generated_scored_units(questions):
    """Expand authored major questions into the source-reviewed scored units.

    Current 國寫 has two printed major questions but three independently scored
    units: the first major question contains 4-point and 21-point responses.
    Other subjects may also have multiple scored subparts. Printed parent
    numbers and independently scored units are deliberately different counts.
    """
    units = []
    for question in questions:
        declared = (question.get('item_spec') or {}).get('scored_units')
        if not declared:
            units.append({
                'number': question.get('number'),
                'section_id': question.get('section_id'),
                'type': question.get('type'),
                'score': question.get('score'),
                'option_count': len(question.get('options') or []) if question.get('options') is not None else None,
                **({'slot_id': question['item_spec']['slot_id']} if (question.get('item_spec') or {}).get('slot_id') else {}),
            })
            continue
        for unit in declared if isinstance(declared, list) else []:
            if not isinstance(unit, dict):
                continue
            units.append({
                'number': unit.get('number', question.get('number')),
                'section_id': unit.get('section_id', question.get('section_id')),
                'type': unit.get('type', question.get('type')),
                'score': unit.get('score'),
                'option_count': unit.get('option_count'),
                **({'slot_id': unit['slot_id']} if unit.get('slot_id') else {}),
            })
    return units


def scored_unit_errors(questions, slots, section_map=None):
    errors = []
    section_map = section_map or {}
    units = generated_scored_units(questions)
    if len(units) != len(slots):
        errors.append('generated scored units differ from verified slot inventory')
    for question in questions:
        declared = (question.get('item_spec') or {}).get('scored_units')
        if declared is not None:
            valid = isinstance(declared, list) and bool(declared) and all(
                isinstance(u, dict) and isinstance(u.get('score'), (int, float))
                and not isinstance(u['score'], bool) and math.isfinite(u['score']) and u['score'] > 0
                for u in declared)
            if not valid or sum(u['score'] for u in declared) != question.get('score'):
                errors.append(f'Q{question.get("number")}: parent score differs from declared scored units')
    for unit, slot in zip(units, slots):
        if not positive_score(unit.get('score')) or isinstance(unit.get('number'), bool):
            errors.append(f'Q{unit.get("number")}: invalid scored unit number/score')
        if (unit.get('number') != slot.get('number')
                or section_map.get(unit.get('section_id'), unit.get('section_id')) != slot.get('section_id')
                or unit.get('type') != slot.get('type') or unit.get('score') != slot.get('score')):
            errors.append(f'Q{unit.get("number")}: number/section/type/score differs from source-reviewed slot')
        if slot.get('option_count') is not None and unit.get('option_count') != slot['option_count']:
            errors.append(f'Q{unit.get("number")}: option count differs from source-reviewed slot')
        # A slot id is necessary for indistinguishable subparts under one number.
        if sum(s.get('number') == slot.get('number') for s in slots) > 1 and unit.get('slot_id') != slot.get('id'):
            errors.append(f'Q{unit.get("number")}: scored subpart must bind its reviewed slot_id')
    return errors


def artifact_review_errors(artifact, base, exam_sha, role):
    errors = []
    path = base / artifact.get('path', '')
    if not path.is_file() or artifact.get('sha256') != file_hash(path):
        return [f'{role}: missing or changed PDF']
    from pypdf import PdfReader
    count = len(PdfReader(path).pages)
    if artifact.get('expected_page_count') != count:
        errors.append(f'{role}: measured page count differs from approved page contract')
    review_path = base / artifact.get('review_path', '')
    if not review_path.is_file():
        return errors + [f'{role}: no final raster page review']
    r = load(review_path)
    if r.get('pdf_sha256') != file_hash(path) or r.get('exam_sha256') != exam_sha:
        errors.append(f'{role}: stale page review')
    pages = r.get('pages') or []
    if len(pages) != count or {p.get('page') for p in pages} != set(range(1, count + 1)):
        errors.append(f'{role}: review must cover every PDF page, not a contact sheet')
    if not r.get('reviewer') or not r.get('reviewed_at') or r.get('unresolved') != []:
        errors.append(f'{role}: missing reviewer or unresolved visual defects')
    checks = {'font_glyphs', 'font_roles_sizes', 'formula_geometry', 'overflow', 'whitespace',
              'source_notes', 'figure_grayscale', 'headers_numbering', 'content_legibility'}
    for page in pages:
        observed = page.get('checks') or {}
        if not checks <= observed.keys() or any(observed.get(k) not in {'pass', 'not-applicable'} for k in checks):
            errors.append(f'{role} page {page.get("page")}: visual checks incomplete/failed')
        if not page.get('observations') or not page.get('reference_page'):
            errors.append(f'{role} page {page.get("page")}: missing specific reference comparison')
        raster = base / page.get('raster_path', '')
        if not raster.is_file() or page.get('raster_sha256') != file_hash(raster):
            errors.append(f'{role} page {page.get("page")}: missing/changed review raster')
    return errors


def validate(exam_path, contract_path, stage='content', root=ROOT, execute=True):
    exam = load(exam_path); contract = load(contract_path); base = contract_path.parent
    meta = exam.get('metadata') or {}; errors = []; checks = []
    if stage not in {'content', 'delivery'}:
        errors.append('unknown validation stage')
    subject = meta.get('paper_subject') or meta.get('subject')
    if contract.get('requested_mode') != 'full-paper':
        errors.append('formal gate requires an explicit full-paper request contract; software smoke/custom practice cannot claim acceptance')
    for key, value in [('subject', subject), ('exam', meta.get('exam')), ('curriculum', meta.get('curriculum'))]:
        if contract.get(key) != value:
            errors.append(f'requested {key} differs from generated product')
    if not contract.get('user_request'):
        errors.append('original user request missing from contract')
    if meta.get('generation_mode') != 'full-paper':
        errors.append('request downgraded to custom/generic preview')
    if meta.get('layout_fidelity_status') != 'verified':
        errors.append('generic/reference-only layout is not a formal paper')
    folder_subject = '國文' if subject in {'國綜', '國寫'} else subject
    pack = root / 'exam_packs' / str(meta.get('exam')) / 'subjects' / str(folder_subject)
    manifest_path = pack.parents[1] / 'manifest.json'
    subject_path = pack / 'subject.json'
    if not manifest_path.is_file() or folder_subject not in load(manifest_path).get('subjects', []):
        errors.append('manifest missing or requested subject not registered')
    if not subject_path.is_file() or load(subject_path).get('name') != folder_subject:
        errors.append('subject.json missing or wrong subject')
    profiles_path = pack / 'metadata' / 'papers.jsonl'
    profiles = [json.loads(l) for l in profiles_path.read_text(encoding='utf-8-sig').splitlines() if l.strip()] if profiles_path.is_file() else []
    profile = next((p for p in profiles if p.get('paper_id') == meta.get('paper_profile_id')), None)
    if not profile:
        errors.append('selected paper profile not found in exam_packs (composite ids are not profiles)')
    else:
        errors.extend('pack: ' + e for e in paper_errors(profile, root))
        if profile.get('subject') != folder_subject or profile.get('curriculum') != meta.get('curriculum'):
            errors.append('paper profile subject/curriculum mismatch')
        if subject in {'國綜', '國寫'} and profile.get('section') != subject:
            errors.append('國綜/國寫 profile mismatch')
        slots = ((profile.get('evidence') or {}).get('structure_review') or {}).get('slots') or []
        questions = exam.get('questions') or []
        section_map = contract.get('section_map') or {}
        errors.extend(scored_unit_errors(questions, slots, section_map))
        if meta.get('total_score') != profile.get('total_score') or meta.get('duration_minutes') != profile.get('duration_minutes'):
            errors.append('score/duration differs from verified profile')
    layouts = [load(p) for p in (pack / 'blueprints' / 'layout-profiles').glob('*.json')]
    layout = next((p for p in layouts if p.get('profile_id') == meta.get('layout_profile')), None)
    if not layout:
        errors.append('layout profile not found in exam_packs')
    else:
        errors.extend('layout: ' + e for e in layout_errors(layout, root, profile))
    writer = pack / 'blueprints' / 'writer-blueprint.json'
    if not writer.is_file():
        errors.append('writer-blueprint missing; do not hardcode a fingerprint')
    else:
        from writer_calibration import load_writer
        try:
            w = load_writer(pack, root)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            errors.append('writer calibration: ' + str(exc))
            w = {}
        expected = w.get('metadata_fingerprint') or w.get('source_fingerprint') or w.get('blueprint_fingerprint')
        if not expected or meta.get('blueprint_fingerprint') != expected:
            errors.append('writer-blueprint fingerprint missing/mismatched')
        if (w.get('calibration_by_curriculum', {}).get(meta.get('curriculum'), {}).get('status') or w.get('calibration_status')) != 'ready':
            errors.append('pack calibration incomplete; no formal-calibration claim')
    errors.extend(independent_answer_errors(exam))
    from validate_math_context import validate as math_context_errors
    errors.extend(math_context_errors(exam))
    errors.extend(answer_distribution_errors(exam))
    source_path = base / contract.get('source_registry', '')
    registry = load(source_path) if source_path.is_file() else []
    errors.extend(source_link_errors(exam, registry))
    commands = [('validate_paper_difficulty_balance.py', [exam_path]),
                ('validate_llm_originality_contract.py', [exam_path]),
                ('validate_visual_item_contract.py', [exam_path])]
    if subject in {'數學A', '數學B'}:
        commands += [('validate_math_curriculum.py', [exam_path]), ('validate_math_difficulty_design.py', [exam_path])]
    elif subject in {'國綜', '自然'}:
        commands += [('validate_chinese_natural_scope.py', [exam_path]),
                     ('validate_source_grounding.py', [exam_path, source_path, '--novelty-report', base / contract.get('source_novelty_report', '')])]
    elif subject == '社會':
        commands += [('validate_social_item_design.py', [exam_path])]
    elif subject == '英文':
        commands += [('validate_english_layout_contract.py', [exam_path]),
                     ('validate_english_vocabulary_scope.py', [exam_path, base / contract.get('vocabulary_reference', '')]),
                     ('validate_english_difficulty_design.py', [exam_path])]
    elif subject == '國寫':
        commands += [('validate_writing_source_grounding.py', [exam_path, source_path])]
    else:
        errors.append('no formal gate routing for this subject/combined booklet; do not silently skip it')
    if execute:
        for script, args in commands:
            result = run_check(script, args); checks.append(result)
            if result['exit_code'] != 0:
                errors.append(f'{script}: failed or unavailable')
    else:
        errors.append('machine checks not executed (test-only diagnostic)')
    if stage == 'delivery':
        from verify_fixed_template_pdf import verify_pdf
        for role in ('student_pdf', 'answer_pdf'):
            errors.extend(artifact_review_errors(contract.get(role) or {}, base, file_hash(exam_path), role))
            pdf_path = base / (contract.get(role) or {}).get('path', '')
            if pdf_path.is_file():
                result = verify_pdf(pdf_path, subject, 'questions' if role == 'student_pdf' else 'answers')
                errors.extend(f'{role}/fixed-template: {e}' for e in result['errors'])
        if execute:
            for role in ('student_html', 'answer_html'):
                entry = contract.get(role) or {}; path = base / entry.get('path', '')
                if not path.is_file() or entry.get('sha256') != file_hash(path):
                    errors.append(f'{role}: missing/changed fixed-page HTML')
                else:
                    r = run_check('validate_fixed_page_html.py', [path]); checks.append(r)
                    if r['exit_code']:errors.append(f'{role}: final DOM overflow/containment failed')
            student_path = base / (contract.get('student_pdf') or {}).get('path', '')
            if subject in {'數學A','數學B'}:
                import pymupdf
                from validate_math_context import source_note_samples
                for pdf_role in ('student_pdf','answer_pdf'):
                    pdf_path = base / (contract.get(pdf_role) or {}).get('path', '')
                    if pdf_path.is_file():
                        with pymupdf.open(pdf_path) as doc:
                            if any(source_note_samples(page.get_text()) for page in doc):
                                errors.append(f'{pdf_role}: printed math source note')
            reference = next((root / s['relative_path'] for s in (profile or {}).get('source_files', []) if s.get('role') == 'question'), None)
            if subject in {'國綜', '自然'} and student_path.is_file():
                r = run_check('validate_current_form_density.py', [student_path, '--subject', subject, '--reference-year', str((profile or {}).get('year', 1911) - 1911)])
                checks.append(r)
                if r['exit_code']:errors.append('final student page count/density failed')
            elif subject in {'國寫', '數學A', '數學B', '英文', '社會'} and student_path.is_file() and reference:
                r = run_check('validate_reference_page_density.py', [student_path, reference, '--subject', subject]); checks.append(r)
                if r['exit_code']:errors.append('final student reference density/content-volume failed')
        # Hash-bind qualitative reviews too. A filled-in pass field alone cannot
        # establish that an independent reading, corpus check or comparison ran.
        required = ['curriculum_semantics', 'source_grounding', 'corpus_originality', 'literacy', 'layout_comparison']
        if contract.get('suite_size', 1) > 1:
            required.append('cross_form_originality')
            suite = contract.get('suite_exams') or []
            if len(suite) != contract['suite_size']:
                errors.append('suite file inventory missing or wrong size')
            for entry in suite:
                path = base / entry.get('path', '')
                if not path.is_file() or entry.get('sha256') != file_hash(path):
                    errors.append('suite file missing or changed')
        for kind in required:
            entry = (contract.get('editorial_reviews') or {}).get(kind) or {}
            path = base / entry.get('path', '')
            if not path.is_file() or entry.get('sha256') != file_hash(path):
                errors.append(f'{kind}: review missing/changed'); continue
            r = load(path)
            if r.get('exam_sha256') != file_hash(exam_path) or r.get('status') != 'pass' or r.get('unresolved') != [] or not r.get('observations') or not r.get('reviewer'):
                errors.append(f'{kind}: stale/incomplete editorial evidence')
            if kind == 'cross_form_originality' and (r.get('suite_sha256') != digest(contract.get('suite_exams') or []) or not r.get('pairwise_findings')):
                errors.append('cross-form review does not bind the current suite and pairwise findings')
    return {'status': 'fail' if errors else f'pass-{stage}-evidence', 'exam_sha256': file_hash(exam_path),
            'contract_sha256': file_hash(contract_path), 'errors': errors, 'checks': checks,
            'limitations': 'Evidence consistency only. Does not prove reviewer independence, absence of semantic errors, or achieved pilot P/D. No publication performed.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('exam', type=Path); ap.add_argument('--contract', type=Path, required=True)
    ap.add_argument('--stage', choices=['content', 'delivery'], default='content')
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    try:
        report = validate(a.exam.resolve(), a.contract.resolve(), a.stage)
    except Exception as exc:
        report = {'status': 'fail', 'errors': [f'{type(exc).__name__}: {exc}']}
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False)); return int(report['status'] == 'fail')


if __name__ == '__main__':
    raise SystemExit(main())
