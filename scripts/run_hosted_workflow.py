#!/usr/bin/env python3
"""Batch mechanical hosted work. Never author questions or approve reviews.

checkpoint registers saved work; specs projects saved items into body layout
specs; proof renders selected items for early crop review; build renders,
composes and prepares BOTH booklets; record-review writes the reviewer's actual
findings; finalize registers review files, closes the clock and runs the gate.
All paths in state remain relative to the run, not the shell working directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import re
import time

import pymupdf
from hosted_run_timing import PHASES, transition
from hosted_body_templates import render
from hosted_item_layout import crop_bytes, geometry_errors
from compose_hosted_pdf import compact_fonts, compose
from prepare_hosted_review import (prepare, item_hashes, annotate_parts, projected,
                                   refresh_review_hashes, canonical_sha, crop_keys, pending_note)
from check_hosted_run import check, ITEM_GATES, PAPER_GATES
from fetch_hosted_template_assets import DEFAULT_MAP

SPEC_GENERATOR = 'run_hosted_workflow.py specs'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    temporary.replace(path)


def inside(root, path):
    path = Path(path).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Artifact must stay inside this run: ' + str(path))
    return path


def record(root, path):
    path = inside(root, path)
    return {'path': path.relative_to(root.resolve()).as_posix(), 'sha256': digest(path)}


def event(root, action, started, **details):
    with (root / 'workflow-events.jsonl').open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps({'action': action, 'started_at': started,
                                'elapsed_seconds': round(time.time() - started, 4), **details}) + '\n')


def register_reviews(root, state):
    """Register real supplied reports; never fill status/observations or rebind exam hashes."""
    checks = state.setdefault('checks', {})
    for gate in ITEM_GATES + PAPER_GATES:
        path = root / checks.get(gate, {}).get('path', gate + '.json')
        inside(root, path)
        if path.is_file():
            review = read(path)
            if review.get('exam_sha256') != state['exam']['sha256']:
                continue  # Retain stale/missing evidence; the checker must reject it.
            checks[gate] = record(root, path)
    for bundle in state.get('pdfs', {}).values():
        for key in ('inspection', 'visual_review', 'item_review'):
            saved = bundle.get(key)
            if not saved:
                continue
            path = inside(root, root / saved['path'])
            if read(path).get('pdf_sha256') != bundle['file']['sha256']:
                raise ValueError('Review belongs to another PDF: ' + key)
            bundle[key] = record(root, path)


def checkpoint(run_dir, phase=None, review_bundle=None, state=None):
    started = time.time()
    root = Path(run_dir).resolve()
    preflight = read(root / 'preflight.json')
    if preflight.get('status') != 'ready-for-authoring':
        raise ValueError('Resolve preflight before creating a run checkpoint')
    state_path = inside(root, state) if state else root / 'run-state.json'
    if state_path.parent != root:
        raise ValueError('State must be directly inside the run')
    state = read(state_path) if state_path.exists() else {
        'schema_version': 1, 'paper_id': preflight['paper_id'],
        'subject': preflight['subject'], 'checks': {}, 'pdfs': {},
        'review_mode': preflight['review_mode'],
        'require_independent_review': preflight['require_independent_review'],
        'calibration': preflight['calibration'],
        'template_asset_dir': preflight['template_asset_dir'],
    }
    if state['paper_id'] != preflight['paper_id'] or state.get('subject') != preflight['subject']:
        raise ValueError('Checkpoint belongs to another paper or subject')
    if preflight['require_independent_review']:
        state['require_independent_review'] = True
    exam = root / 'exam.json'
    if exam.exists():
        metadata = read(exam).get('metadata', {})
        if metadata.get('paper_id') != state['paper_id'] or metadata.get('subject') != state['subject']:
            raise ValueError('Saved exam belongs to another paper or subject')
        state['exam'] = record(root, exam)
    if phase:
        if phase not in PHASES:
            raise ValueError('Unknown phase')
        transition(root / 'generation-timing.json', state['paper_id'], phase)
        state['current_phase'] = phase
    state['timing'] = record(root, root / 'generation-timing.json')
    if review_bundle:
        # One actual review session may write a bundle of complete gate records.
        # This is a lossless fan-out, not auto-generated review text or a pass.
        supplied = read(review_bundle)
        if not supplied or set(supplied) - set(ITEM_GATES + PAPER_GATES):
            raise ValueError('Review bundle must map existing gate names to their real reports')
        for gate, report in supplied.items():
            if report.get('exam_sha256') != state.get('exam', {}).get('sha256'):
                raise ValueError('Review bundle has a stale exam hash: ' + gate)
        for gate, report in supplied.items():
            destination = root / (gate + '.json')
            if destination.exists() and read(destination) != report:
                raise ValueError('Preserve earlier review; update its recorded file explicitly: ' + gate)
        for gate, report in supplied.items():
            save(root / (gate + '.json'), report)
    if state.get('exam'):
        register_reviews(root, state)
    save(state_path, state)
    event(root, 'checkpoint', started, phase=phase)
    return {'status': 'checkpoint-saved', 'state': str(state_path),
            'exam_saved': bool(state.get('exam')), 'registered_reviews': sorted(state['checks']),
            'reviews_approved_by_tool': False}


def build(state_path, question_spec, solution_spec, font, output, *, year,
          title='學科能力測驗模擬試題', running_name='學測', reading_font=None):
    started = time.time()
    state_path = Path(state_path).resolve()
    root = state_path.parent
    state = read(state_path)
    exam_path = inside(root, root / state['exam']['path'])
    if record(root, exam_path) != state['exam']:
        raise ValueError('Save a checkpoint for the current exam before building')
    exam = read(exam_path)
    subject = exam['metadata']['subject']
    if exam['metadata']['paper_id'] != state['paper_id']:
        raise ValueError('Wrong paper')
    output = inside(root, output)
    if output.parent != root:
        raise ValueError('Build output must be a direct child directory of the run')
    review_output = root / (output.name + '-review')
    candidate = root / (review_output.name + '-run-state.json')
    assets = inside(root, root / state['template_asset_dir'])
    specs = {'question': Path(question_spec).resolve(), 'solution': Path(solution_spec).resolve()}
    asset_inputs = {}
    for path in specs.values():
        inside(root, path)
        spec = read(path)
        if spec.get('subject') != subject:
            raise ValueError('Body spec must match the actual exam subject')
        current_generated_spec(spec, state)
        for block in spec.get('blocks', []):
            for asset in block.get('assets', {}).values():
                asset_path = inside(root, path.parent / asset['path'])
                if digest(asset_path) != asset['sha256']:
                    raise ValueError('Body asset hash changed: ' + asset['path'])
                asset_inputs[asset_path.relative_to(root).as_posix()] = asset['sha256']
    # Same-byte cache includes every portable helper: renderer fixes invalidate it.
    scripts = Path(__file__).resolve().parent
    identity = {'exam': state['exam'], 'paper_id': state['paper_id'], 'subject': subject,
                'review_mode': state.get('review_mode'),
                'require_independent_review': state.get('require_independent_review', False),
                'specs': {role: record(root, path) for role, path in specs.items()},
                'font': digest(font), 'reading_font': digest(reading_font) if reading_font else None,
                'year': str(year), 'title': title, 'running_name': running_name,
                'assets': {p.name: digest(p) for p in sorted(assets.glob('*.pdf'))},
                'body_assets': asset_inputs, 'template_map': digest(DEFAULT_MAP),
                'helpers': {p.name: digest(p) for p in sorted(scripts.glob('*.py'))}}
    manifest_path = output / 'workflow-build.json'
    if output.exists():
        if not manifest_path.exists():
            raise ValueError('Partial build exists; preserve it and use a new output name')
        manifest = read(manifest_path)
        if manifest['inputs'] != identity:
            raise ValueError('Build inputs changed; use a new output name for the repair')
        for artifact in manifest['artifacts']:
            if record(root, root / artifact['path']) != artifact:
                raise ValueError('Cached build artifact changed: ' + artifact['path'])
        if not candidate.is_file():
            raise ValueError('Cached review state missing; recover it before continuing')
        cached_state = read(candidate)
        for name in ('exam', 'paper_id', 'review_mode'):
            if cached_state.get(name) != state.get(name):
                raise ValueError('Cached review state changed: ' + name)
        if cached_state.get('require_independent_review', False) != state.get('require_independent_review', False):
            raise ValueError('Cached review state changed: require_independent_review')
        if set(cached_state.get('pdfs', {})) != {'question', 'solution'}:
            raise ValueError('Cached review state is missing a booklet')
        for role, bundle in cached_state['pdfs'].items():
            if (bundle.get('exam_sha256') != state['exam']['sha256'] or
                    bundle.get('file') != record(root, output / (role + '.pdf'))):
                raise ValueError('Cached review state belongs to different PDF bytes')
            for name in ('inspection', 'visual_review', 'item_review'):
                path = inside(root, root / bundle[name]['path'])
                if read(path).get('pdf_sha256') != bundle['file']['sha256']:
                    raise ValueError('Cached review belongs to a different PDF: ' + name)
        event(root, 'build', started, cache_hit=True)
        return {**manifest['result'], 'cache_hit': True}
    if review_output.exists() or candidate.exists():
        raise ValueError('Review output already exists; choose a new build name')
    transition(root / 'generation-timing.json', state['paper_id'], 'render_repair')
    output.mkdir()
    pairs = {}
    for role, spec_path in specs.items():
        body = output / (role + '-body.pdf')
        layout = output / (role + '-layout.json')
        pdf = output / (role + '.pdf')
        render(read(spec_path), body, layout, Path(font), asset_root=spec_path.parent,
               reading_font=Path(reading_font) if reading_font else None)
        compose(subject, body, assets, pdf, year=str(year), title=title,
                running_name=running_name, font_path=Path(font),
                kind='questions' if role == 'question' else 'answers')
        pairs[role] = (pdf, body, layout)
    result = prepare(state_path, pairs, review_output,
                     render_identity=render_identity(Path(font), Path(reading_font) if reading_font else None))
    transition(root / 'generation-timing.json', state['paper_id'], 'visual_qa')
    reviewed = read(candidate)
    reviewed['timing'] = record(root, root / 'generation-timing.json')
    reviewed['current_phase'] = 'visual_qa'
    save(candidate, reviewed)
    # Human observations may change; immutable PDFs, layouts and images may not.
    immutable = [p for p in output.iterdir() if p.is_file()]
    immutable += list(review_output.rglob('*.png'))
    result.update(cache_hit=False, reviews_approved_by_tool=False)
    save(manifest_path, {'inputs': identity, 'artifacts': [record(root, p) for p in immutable], 'result': result})
    event(root, 'build', started, cache_hit=False)
    return result


def render_identity(font, reading_font=None):
    """Fonts and painting code behind a crop; a changed identity never inherits a review."""
    scripts = Path(__file__).resolve().parent
    return {'font': digest(font), 'reading_font': digest(reading_font) if reading_font else None,
            'pymupdf': pymupdf.VersionBind,
            'helpers': {name: digest(scripts / name) for name in
                        ('hosted_body_templates.py', 'compose_hosted_pdf.py', 'hosted_item_layout.py')}}


def current_generated_spec(spec, state):
    """A projected spec must describe the saved exam; hand-written specs stay supported."""
    if spec.get('generated_by') != SPEC_GENERATOR:
        return
    if canonical_sha(spec.get('blocks')) != spec.get('blocks_sha256'):
        raise ValueError('Generated body spec was edited; put layout decisions in hints and regenerate specs')
    if spec.get('exam_sha256') != state['exam']['sha256']:
        raise ValueError('Body spec predates the saved exam; rerun specs before rendering')


OPTION_LAYOUT_COLUMNS = {'row-5': 5, 'row-4': 4, 'grid-3-2': 3, 'grid-2': 2, 'stack': 1}
RICH_TAG = re.compile(r'</?(?:sup|sub|i|em|b|strong)>|<br>')
SUBSCRIPT = '₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎'
SUPERSCRIPT = '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ'
SCRIPT_RUN = re.compile(f'([{SUBSCRIPT}]+)|([{SUPERSCRIPT}]+)')
SCRIPT_TEXT = (str.maketrans(SUBSCRIPT, '0123456789+−=()'), str.maketrans(SUPERSCRIPT, '0123456789+−=()ni'))
# Long text may continue on the next page at paragraph boundaries; short
# evidence packets stay whole, as in the maintained official-form renderers.
SPLIT_MIN_CHARACTERS = 260
LATEX_COMMAND = re.compile(r'\\(?:[A-Za-z]+|[()\[\]{}])')
# A currency amount is the only printed dollar sign: $ directly before a digit.
TEX_DOLLAR = re.compile(r'\$(?![  ]?\d)')
MARKUP_TAG = re.compile(r'<(/?)(sup|sub|i|em|b|strong)>')
ASSET_TOKEN = re.compile(r'\{\{asset:([^{}]+)\}\}')


def text_issues(value):
    """What the body renderer would print literally; checked when items are saved."""
    raw = value['rich'] if isinstance(value, dict) and set(value) == {'rich'} else value
    if not isinstance(raw, str):
        return []
    issues = []
    command = LATEX_COMMAND.search(raw)
    if command:
        issues.append(f'LaTeX {command.group()} prints literally: write the symbol, <sup>/<sub>, '
                      'or a declared {{asset:NAME}} formula image')
    if TEX_DOLLAR.search(raw):
        issues.append('"$" prints literally: TeX math delimiters are not rendered')
    depth = Counter()
    for closing, tag in MARKUP_TAG.findall(raw):
        depth[tag] += -1 if closing else 1
        if depth[tag] < 0:
            break
    if any(depth.values()):
        issues.append('unbalanced <sup>/<sub>/<i>/<b> markup')
    return issues


def printed_fields(question, answer):
    """(where, text) for every saved field the specs projection prints."""
    for key in ('prompt', 'number_display', 'answer_label', 'group_stimulus'):
        if isinstance(question.get(key), str):
            yield key, question[key]
    for option in question.get('options') or []:
        if isinstance(option, dict):
            yield f'option {option.get("label")}', option.get('text')
    for key in ('continuation_pages', 'group_stimulus_page_splits'):
        for page, value in sorted((question.get(key) or {}).items()):
            yield f'{key} {page}', value
    table = question.get('response_format_table')
    if isinstance(table, dict):
        for key in ('caption', 'heading'):
            if isinstance(table.get(key), str):
                yield 'response table ' + key, table[key]
        for index, row in enumerate(table.get('rows') or [], 1):
            if isinstance(row, dict):
                for key in ('label', 'instruction'):
                    if isinstance(row.get(key), str):
                        yield f'response row {index} {key}', row[key]
    final = answer.get('final_answer')
    for value in final if isinstance(final, list) else [final]:
        if isinstance(value, str):
            yield 'final_answer', value
    for index, step in enumerate(answer.get('reasoning') or [], 1):
        yield f'reasoning {index}', step
    for index, block in enumerate(answer.get('explanation_blocks') or [], 1):
        if isinstance(block, dict):
            for key in ('title', 'content'):
                if isinstance(block.get(key), str):
                    yield f'explanation {index} {key}', block[key]


def authoring_issues(questions, answers, *, root):
    """Print defects in saved items, found before any rendering or visual review."""
    by_answer = {a.get('question_id'): a for a in answers}
    found = []
    for question in questions:
        qid = question.get('id')
        answer = by_answer.get(qid, {})
        tokens = {'question': set(), 'answer': set()}
        for where, value in printed_fields(question, answer):
            owner = 'answer' if where.startswith(('final_answer', 'reasoning', 'explanation')) else 'question'
            raw = value['rich'] if isinstance(value, dict) and set(value) == {'rich'} else value
            if isinstance(raw, str):
                tokens[owner].update(ASSET_TOKEN.findall(raw))
            found += [f'item {qid} {where}: {issue}' for issue in text_issues(value)]
        for owner, record_ in (('question', question), ('answer', answer)):
            declared = record_.get('inline_assets') or {}
            for name in sorted(tokens[owner] - set(declared)):
                found.append(f'item {qid} {owner}: {{{{asset:{name}}}}} is not declared in its inline_assets')
            files = [(f'inline asset {name}', asset) for name, asset in declared.items()]
            if isinstance(record_.get('visual_asset'), dict):
                files.append(('visual_asset', record_['visual_asset']))
            for where, asset in files:
                path = (root / str((asset or {}).get('path') or '')).resolve() if isinstance(asset, dict) else root
                if not isinstance(asset, dict) or not asset.get('path') or not path.is_relative_to(root) or not path.is_file():
                    found.append(f'item {qid} {owner} {where}: file not found in this run')
                elif asset.get('sha256') != digest(path):
                    found.append(f'item {qid} {owner} {where}: sha256 missing or different from the file')
    return found


def printed(value, where, *, english=False, gaps=False):
    """Printed exam text with typography normalised for the body renderer.

    Unicode sub/superscript characters become <sub>/<sup>: common CJK fonts lack
    most of them and MuPDF otherwise mixes fallback serif glyphs into formulas.
    English keeps the maintained *italic* and [[n]] gap conventions.
    """
    rich = isinstance(value, dict) and set(value) == {'rich'}
    raw = value['rich'] if rich else value
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(where + ': printed text must be a nonempty string')
    issues = text_issues(raw)
    if issues:
        raise ValueError(where + ': ' + '; '.join(issues))
    converted = raw
    if not rich and not RICH_TAG.search(raw):
        converted = html.escape(raw, quote=False)
    converted = SCRIPT_RUN.sub(lambda m: (f'<sub>{m.group(1).translate(SCRIPT_TEXT[0])}</sub>' if m.group(1)
                                          else f'<sup>{m.group(2).translate(SCRIPT_TEXT[1])}</sup>'), converted)
    if english:
        converted = re.sub(r'\*([^*\n]+)\*', r'<i>\1</i>', converted)
    if gaps:
        converted = re.sub(r'\[\[(\d{1,2})\]\]', r'{{gap:\1}}', converted)
    if not rich and not RICH_TAG.search(converted):
        return raw if converted == html.escape(raw, quote=False) else html.unescape(converted)
    if not rich and not RICH_TAG.search(raw):
        converted = converted.replace('\n', '<br>')
    elif not rich:
        converted = re.sub(r'<(?!/?(?:sup|sub|i|em|b|strong)>|br>)', '&lt;', converted).replace('\n', '<br>')
    return {'rich': converted}


def plain_length(value):
    raw = value['rich'] if isinstance(value, dict) else str(value)
    return len(re.sub(r'<[^>]+>', '', raw))


def paragraphs_of(value):
    return [part for part in re.split(r'\n\s*\n', value) if part.strip()]


def latin_text(*values):
    """Mostly-Latin printed text (English stems/options), not Chinese directions."""
    raw = ' '.join(v['rich'] if isinstance(v, dict) else str(v) for v in values)
    latin = len(re.findall(r'[A-Za-z]', raw))
    return latin > 0 and len(re.findall(r'[㐀-鿿]', raw)) * 4 < latin


def option_label(label):
    label = str(label).strip()
    return label if re.fullmatch(r'[(（].*[)）]', label) else f'({label})'


def option_columns(question, subject):
    """Explicit option_layout first; otherwise the maintained renderer heuristic."""
    if question.get('option_layout') in OPTION_LAYOUT_COLUMNS:
        return OPTION_LAYOUT_COLUMNS[question['option_layout']]
    options = question.get('options') or []
    longest = max((len(str(o.get('text', ''))) for o in options), default=0)
    if longest > 52:
        return 1
    if longest > 23:
        return 2
    if subject in {'數學A', '數學B'} and len(options) == 5:
        return 5
    if subject == '英文' and len(options) == 4:
        return 4
    return 2


def answer_text(value):
    if isinstance(value, list):
        return '、'.join(answer_text(v) for v in value)
    if isinstance(value, dict):
        return '；'.join(f'{k}：{answer_text(v)}' for k, v in value.items())
    return str(value)


def fill_rows(answer_format):
    if not isinstance(answer_format, dict):
        return None
    if answer_format.get('kind') == 'fraction':
        if answer_format.get('fixed_denominator') is not None:
            return None  # Needs its own verified response asset.
        return [int(answer_format.get('numerator_slots') or 1), int(answer_format.get('denominator_slots') or 1)]
    return [int(answer_format.get('slots') or 1)]


def attach_assets(block, record_, where, body_width, hint, *, figure_key, position=None, shown=None):
    assets = dict(hint.get('assets') or {})
    assets.update(record_.get('inline_assets') or {})
    visual = record_.get('visual_asset')
    # A shared figure prints once, where its first item appears.
    if visual and (shown is None or visual.get('path') not in shown):
        if not visual.get('sha256'):
            raise ValueError(where + ': visual_asset needs its sha256 before layout')
        if shown is not None:
            shown.add(visual.get('path'))
        width = hint.get('figure_width_pt') or round(body_width * (visual.get('width_percent') or 62) / 100, 1)
        assets[figure_key] = {'path': visual['path'], 'sha256': visual['sha256'], 'width_pt': width}
        block['figure'] = figure_key
        block['figure_position'] = position or hint.get('figure_position') or (
            'right' if record_.get('visual_layout') == 'side-right' else 'below')
    if assets:
        block['assets'] = assets


def english_segment(owner, segment, members, where, layout):
    """A passage with gaps, its option bank, and cloze rows as aligned choices."""
    by_number = {m.get('number'): m for m in members}
    blocks, paragraphs, emitted = [], [], set()

    def flush():
        if paragraphs:
            blocks.append({'kind': 'passage', 'id': owner, 'language': 'en', 'paragraphs': list(paragraphs),
                           **({'indent': True} if layout == 'prose' else {})})
            paragraphs.clear()

    for index, text_ in enumerate(paragraphs_of(segment)):
        row = re.match(r'\s*(\d{1,2})\.\s*(\(A\).*)', text_, re.S)
        member = by_number.get(int(row.group(1))) if row else None
        options = (member or {}).get('options') or []
        expected = ' '.join(f'{option_label(o["label"])} {o["text"]}' for o in options)
        if row and options and re.sub(r'\s+', ' ', row.group(2)).strip() == re.sub(r'\s+', ' ', expected).strip():
            flush()
            blocks.append({'kind': 'choice', 'id': member['id'], 'number': member['number'], 'text': '', 'language': 'en',
                           'options': [{'label': option_label(o['label']),
                                        'text': printed(o['text'], where + ' option', english=True)} for o in options],
                           'columns': option_columns(member, '英文')})
            emitted.add(member['id'])
            continue
        entries = re.findall(r'\(([A-Z])\)\s*(.*?)(?=\s*\([A-Z]\)|\s*$)', text_, re.S)
        if (paragraphs and re.match(r'\s*\(A\)', text_) and len(entries) >= 3 and
                [label for label, _ in entries] == [chr(65 + n) for n in range(len(entries))]):
            # One lettered bank printed once after its passage, never per gap.
            flush()
            blocks[-1].update(bank=[{'label': f'({label})', 'text': printed(entry.strip(), where + ' option bank', english=True)}
                                    for label, entry in entries],
                              columns=5 if len(entries) >= 5 and all(len(entry.strip()) <= 20 for _, entry in entries) else 1)
            continue
        paragraphs.append(printed(text_, where + ' passage', english=True, gaps=True))
    flush()
    return blocks, emitted


def project_specs(exam, hints, body_width):
    """Deterministic layout projection of saved items. It adds no printed content.

    Printed text comes only from exam.json, following the conventions of the
    maintained official-form renderers for every subject. Hints hold layout
    choices and explicit blocks for structures the item fields cannot express.
    """
    subject = exam['metadata']['subject']
    english = subject == '英文'
    questions = exam.get('questions', [])
    sections = {s['id']: s for s in exam.get('sections', [])}
    answers = {}
    for answer in exam.get('answers', []):
        answers.setdefault(answer.get('question_id'), []).append(answer)
    item_hints = hints.get('items', {})
    unknown = set(item_hints) - {q.get('id') for q in questions}
    if unknown:
        raise ValueError('Layout hints name unsaved items: ' + ', '.join(sorted(unknown)))
    blocks, solutions = [], []
    if hints.get('solution_heading'):
        heading = hints['solution_heading']
        solutions.append({'kind': 'section', 'title': printed(heading.get('title'), 'solution_heading'),
                          **({'directions': printed(heading['directions'], 'solution_heading')}
                             if heading.get('directions') else {})})
    owner_blocks = {}
    number_owner = {}
    totals = {}
    for question in questions:
        if type(question.get('number')) is int and type(question.get('score')) in (int, float):
            totals[question['number']] = totals.get(question['number'], 0) + question['score']
    suppressed = []
    shown = set()
    current_section = None

    def add(block):
        blocks.append(block)
        if block['kind'] != 'section':
            owner_blocks.setdefault(block['id'], []).append(block)
        return block

    def cover(owner, covered):
        for block in owner_blocks.get(owner, []):
            block['covers'] = sorted(set(block.get('covers', [])) | set(covered))

    def emit_question(q):
        hint = item_hints.get(q['id'], {})
        where = 'item ' + q['id']
        if 'question_blocks' in hint:
            for block in hint['question_blocks']:
                add(block)
            number_owner[q.get('number')] = q['id']
            return
        kind = hint.get('kind') or {'single_choice': 'choice', 'multiple_choice': 'multiple',
                                    'fill_in': 'constructed' if english else 'fill',
                                    'constructed_response': 'constructed', 'guided_writing': 'constructed',
                                    'short_answer': 'constructed', 'essay': 'constructed'}.get(q.get('type'))
        if kind is None:
            raise ValueError(where + f': no standard layout for type {q.get("type")}; supply question_blocks hints')
        number = hint.get('number', q.get('number'))
        prompt = str(q.get('prompt') or '')
        continuations = [text_ for _, text_ in sorted((q.get('continuation_pages') or {}).items(), key=lambda item: int(item[0]))]
        if kind == 'constructed' and continuations:
            # Continued material stays in the item's text column; page turns
            # happen at paragraph boundaries instead of fixed page numbers.
            prompt = '\n\n'.join([prompt, *continuations])
            continuations = []
        if kind == 'multiple' and subject == '自然':
            count = q.get('required_selection_count')
            if '應選' in prompt:
                raise ValueError(where + ': 應選項數 comes from required_selection_count, not the prompt')
            if type(count) is not int or not 2 <= count < len(q.get('options') or []):
                raise ValueError(where + ': Natural Science multiple choice needs a valid required_selection_count')
            prompt += f'（應選{count}項）'
        if kind == 'fill' and '{{answer}}' not in prompt:
            prompt = prompt.replace('______', '{{answer}}', 1) if '______' in prompt else prompt + '{{answer}}'
        block = {'kind': kind, 'id': q['id'], 'text': printed(prompt, where + ' prompt', english=english)}
        if type(number) is int:
            block['number'] = number
        label = hint.get('label', q.get('number_display', None if type(number) is int else q.get('answer_label')))
        if label is not None:
            block['label'] = printed(label, where + ' label') if str(label).strip() else ''
        if kind in {'choice', 'multiple'}:
            block['options'] = [{'label': option_label(o['label']),
                                 'text': printed(o['text'], where + ' option ' + str(o['label']), english=english)}
                                for o in q.get('options') or []]
            block['columns'] = hint.get('columns', option_columns(q, subject))
        if kind == 'fill':
            rows = hint.get('rows') or fill_rows(q.get('answer_format'))
            if not rows:
                raise ValueError(where + ': declare answer_format slots or hints rows; fixed denominators need a verified response asset')
            block['rows'] = rows
        if kind == 'constructed':
            block['score'] = q.get('score')
            for printed_score in dict.fromkeys([q.get('score'), totals.get(q.get('number'))]):
                if type(printed_score) in (int, float) and re.search(rf'(?<![0-9.]){printed_score:g}\s*分', prompt):
                    block['score_in_text'] = True
                    if printed_score != q.get('score'):
                        block['printed_score'] = printed_score
                    break
        if english and latin_text(block['text'], *[o['text'] for o in block.get('options', [])]):
            block['language'] = 'en'
        attach_assets(block, q, where, body_width, hint, figure_key='figure',
                      position='below' if kind == 'fill' else None, shown=shown)
        split = hint.get('split')
        if split is None:
            split = (q.get('allow_page_split') or (kind == 'constructed' and len(paragraphs_of(prompt)) > 1 and
                                                   plain_length(block['text']) >= SPLIT_MIN_CHARACTERS))
        if split and kind in {'choice', 'multiple', 'constructed'}:
            block['split'] = 'paragraphs'
        table = q.get('response_format_table')
        if isinstance(table, dict) and table.get('rows'):
            block['keep_with_next'] = True
        elif hint.get('keep_with_next'):
            block['keep_with_next'] = True
        add(block)
        if isinstance(table, dict) and table.get('rows'):
            add({'kind': 'table', 'id': q['id'],
                 **({'text': printed(table['caption'], where + ' response table caption')} if table.get('caption') else {}),
                 'headers': [printed(table.get('heading') or '作答格式', where + ' response table heading')],
                 'rows': [[printed(f'{row.get("label", "")}　{row.get("instruction", "")}'.strip(), where + ' response row')]
                          for row in table['rows']]})
        for continuation in continuations:
            text_ = printed(continuation, where + ' continuation', english=english)
            add({'kind': 'stimulus', 'id': q['id'], 'text': text_,
                 **({'split': 'paragraphs'} if plain_length(text_) >= SPLIT_MIN_CHARACTERS else {})})
        number_owner[q.get('number')] = q['id']

    i = 0
    while i < len(questions):
        q = questions[i]
        if q.get('section_id') != current_section:
            section = sections.get(q.get('section_id'))
            if section is None:
                raise ValueError(f'item {q["id"]}: unknown section_id')
            notes = ' '.join(section.get('instructions') or [])
            add({'kind': 'section', 'title': printed(section['title'], 'section ' + section['id']),
                 **({'directions': printed(notes, 'section ' + section['id'] + ' instructions')} if notes.strip() else {})})
            current_section = q.get('section_id')
        group = q.get('group_stimulus')
        j = i + 1
        while group and j < len(questions) and questions[j].get('group_stimulus') == group:
            j += 1
        members = questions[i:j]
        hint = item_hints.get(q['id'], {})
        for block in hint.get('blocks_before', []):
            add(block)
        emitted, carriers = set(), []
        if group:
            everyone = [x for x in questions if x.get('group_stimulus') == group]
            label = hint.get('group_label')
            if (label is None and len(everyone) > 1 and everyone[0].get('number') is not None and
                    everyone[-1].get('number') is not None and everyone[0]['number'] != everyone[-1]['number']):
                label = f'第 {everyone[0]["number"]} 至 {everyone[-1]["number"]} 題為題組'
            splits = q.get('group_stimulus_page_splits') or {}
            segments = ([(int(page), text_) for page, text_ in sorted(splits.items(), key=lambda item: int(item[0]))]
                        if splits else [(None, group)])
            placed = set()
            if 'group_blocks' in hint:
                for block in hint['group_blocks']:
                    add(block)
                    carriers.append(block)
            else:
                for position, (page, segment) in enumerate(segments):
                    where = f'group of {q["id"]}'
                    if english:
                        segment_blocks, rows = english_segment(q['id'], segment, members, where,
                                                               q.get('stimulus_layout') or 'prose')
                        emitted |= rows
                    else:
                        text_ = printed(segment, where + ' stimulus')
                        segment_blocks = [{'kind': 'stimulus', 'id': q['id'], 'text': text_}]
                    for block in segment_blocks:
                        if block['kind'] in {'passage', 'stimulus'}:
                            carriers.append(block)
                            if plain_length(block.get('text') or ' '.join(
                                    p['rich'] if isinstance(p, dict) else p for p in block.get('paragraphs', []))) >= SPLIT_MIN_CHARACTERS:
                                block['split'] = 'paragraphs'
                    if position == 0 and label and segment_blocks:
                        segment_blocks[0]['group_label'] = printed(label, where + ' label')
                        if english:
                            segment_blocks[0]['group_label_style'] = 'underline'
                    last_text = next((b for b in reversed(segment_blocks) if b['kind'] in {'passage', 'stimulus'}), None)
                    if last_text is not None and hint.get('group_keep_with_next', True) and last_text is segment_blocks[-1]:
                        last_text['keep_with_next'] = True
                    for block in segment_blocks:
                        add(block)
                    # With explicit page segments, the questions printed on a
                    # segment's page follow that segment.
                    if page is not None and position < len(segments) - 1:
                        for member in members:
                            if member.get('page') == page and not member.get('suppress_question_display'):
                                emit_question(member)
                                placed.add(member['id'])
        for member in members:
            if member['id'] in emitted or (group and member['id'] in placed):
                continue
            if member.get('suppress_question_display'):
                suppressed.append((member, carriers[0]['id'] if carriers else None))
                continue
            emit_question(member)
        if blocks and blocks[-1].get('keep_with_next') and blocks[-1]['kind'] in {'passage', 'stimulus'}:
            # Nothing of this group follows its material: do not keep it with the next group.
            blocks[-1].pop('keep_with_next')
        i = j
    # Items printed inside shared material or a same-number item are covered by
    # that block's reviewed crop; resolved once every printed block exists.
    for member, carrier in suppressed:
        owner = carrier or number_owner.get(member.get('number'))
        if owner is None:
            raise ValueError(f'item {member["id"]}: suppressed display needs printed shared material or a same-number item')
        if owner != member['id']:
            cover(owner, [member['id']])

    solution_section = None
    for q in questions:
        hint = item_hints.get(q['id'], {})
        where = 'item ' + q['id']
        if q.get('section_id') != solution_section and hints.get('solution_section_headings', True):
            solutions.append({'kind': 'section',
                              'title': printed(sections[q['section_id']]['title'], 'section ' + q['section_id'])})
        solution_section = q.get('section_id')
        if 'solution_blocks' in hint:
            solutions.extend(hint['solution_blocks'])
            continue
        saved = answers.get(q['id']) or []
        if len(saved) != 1:
            raise ValueError(where + ': exactly one saved answer is required for its solution')
        answer = saved[0]
        steps = [printed(step, where + ' reasoning', english=english) for step in answer.get('reasoning') or []]
        for part in answer.get('explanation_blocks') or []:
            steps.append(printed(f'{part.get("title") or "說明"}：{part.get("content")}', where + ' explanation', english=english))
        if not steps:
            raise ValueError(where + ': saved answer has no printable solution steps')
        solution = {'kind': 'solution', 'id': q['id'],
                    'text': printed(hint.get('solution_text') or '答案：' + answer_text(answer.get('final_answer')),
                                    where + ' final_answer', english=english),
                    'steps': steps}
        number = hint.get('number', q.get('number'))
        if type(number) is int:
            solution['number'] = number
        label = hint.get('solution_label') or q.get('answer_label') or (None if type(number) is int else q.get('number_display'))
        if label:
            solution['label'] = printed(label, where + ' label')
        if len(steps) >= 4 or sum(plain_length(step) for step in steps) >= 2 * SPLIT_MIN_CHARACTERS:
            solution['split'] = 'paragraphs'
        attach_assets(solution, answer, where, body_width, hint.get('solution', {}), figure_key='solution-figure',
                      position='below')
        solutions.append(solution)
    return [{'subject': subject, 'blocks': blocks}, {'subject': subject, 'blocks': solutions}]


def specs(state_path, question_output, solution_output, hints=None):
    """Write both body specs from the saved exam; never author or alter content."""
    started = time.time()
    state_path = Path(state_path).resolve()
    root = state_path.parent
    state = read(state_path)
    exam_path = inside(root, root / state['exam']['path'])
    if record(root, exam_path) != state['exam']:
        raise ValueError('Save a checkpoint for the current exam before projecting specs')
    exam = read(exam_path)
    hint_record = None
    hint_data = {}
    if hints:
        hints = inside(root, hints)
        hint_data = read(hints)
        hint_record = record(root, hints)
        if not isinstance(hint_data, dict) or set(hint_data) - {'items', 'solution_heading', 'solution_section_headings'}:
            raise ValueError('Hints allow items, solution_heading and solution_section_headings only')
    manifest = read(DEFAULT_MAP)
    body = next(s for s in manifest['subjects'] if s['subject'] == exam['metadata']['subject'])['overlay_geometry_pt']['body']
    projections = project_specs(exam, hint_data, body[2] - body[0] - 8)
    outputs = []
    for path, spec in zip((question_output, solution_output), projections):
        path = inside(root, path)
        if path.parent != root:
            raise ValueError('Write specs directly inside the run so asset paths resolve from exam.json')
        if path.exists():
            existing = read(path)
            if (existing.get('generated_by') != SPEC_GENERATOR or
                    canonical_sha(existing.get('blocks')) != existing.get('blocks_sha256')):
                raise ValueError(f'{path.name} contains hand-written layout; preserve it or move decisions into hints')
        spec.update(generated_by=SPEC_GENERATOR, exam_sha256=state['exam']['sha256'], hints=hint_record,
                    blocks_sha256=canonical_sha(spec['blocks']))
        save(path, spec)
        outputs.append(path.relative_to(root).as_posix())
    event(root, 'specs', started)
    return {'status': 'specs-written', 'question_spec': outputs[0], 'solution_spec': outputs[1],
            'block_counts': [len(p['blocks']) for p in projections], 'content_authored_by_tool': False,
            'next': 'Render new items with proof (or both booklets with build) and review the actual images.'}


def proof(state_path, question_spec, solution_spec, items, font, output, *, reading_font=None):
    """Render selected saved items alone for early crop review; never a deliverable.

    Uses the production renderer and the fixed-page transform, so an unchanged
    item's later final crop can retain this actual review.
    """
    started = time.time()
    state_path = Path(state_path).resolve()
    root = state_path.parent
    state = read(state_path)
    exam_path = inside(root, root / state['exam']['path'])
    if record(root, exam_path) != state['exam']:
        raise ValueError('Save a checkpoint for the current exam before an item proof')
    exam = read(exam_path)
    subject = exam['metadata']['subject']
    wanted = [i.strip() for i in (items.split(',') if isinstance(items, str) else items) if str(i).strip()]
    missing = set(wanted) - {q.get('id') for q in exam.get('questions', [])}
    if not wanted or missing:
        raise ValueError('Proof items must be saved question ids: ' + ', '.join(sorted(missing)))
    output = inside(root, output)
    if output.parent != root:
        raise ValueError('Proof output must be a direct child directory of the run')
    if output.exists():
        raise ValueError('Proof output exists; preserve it and use a new name')
    assets = inside(root, root / state['template_asset_dir'])
    with pymupdf.open(assets / 'inner-odd-blank.pdf') as template:
        page_size = [template[0].rect.width, template[0].rect.height]
    hashes = item_hashes(exam)
    identity = render_identity(Path(font), Path(reading_font) if reading_font else None)
    loaded = []
    for role, spec_path in (('question', question_spec), ('solution', solution_spec)):
        spec_path = inside(root, spec_path)
        spec = read(spec_path)
        if spec.get('subject') != subject:
            raise ValueError('Body spec must match the actual exam subject')
        current_generated_spec(spec, state)
        blocks = [{k: v for k, v in block.items() if k != 'keep_with_next'}
                  for block in spec.get('blocks', []) if block.get('kind') != 'section' and
                  (block.get('id') in wanted or set(block.get('covers', [])) & set(wanted))]
        absent = set(wanted) - {item for block in blocks for item in [block.get('id'), *block.get('covers', [])]}
        if absent:
            raise ValueError(f'{role} spec has no blocks for: ' + ', '.join(sorted(absent)))
        loaded.append((role, spec_path, {**spec, 'blocks': blocks}))
    output.mkdir()
    queue, template = [], {}
    by_item = {qid: [] for qid in wanted}
    for role, spec_path, spec in loaded:
        body = output / (role + '-body.pdf')
        # Item proofs review crops, not page count: skip the last-page spacing retry.
        layout = render(spec, body, output / (role + '-layout.json'), Path(font), asset_root=spec_path.parent,
                        reading_font=Path(reading_font) if reading_font else None, balance_last_page=False)
        crops = output / role / 'items'
        crops.mkdir(parents=True)
        parts = []
        with pymupdf.open(body) as source:
            errors = geometry_errors(source, layout['parts'])
            if errors:
                raise ValueError('; '.join(errors))
        with projected(body, tuple(page_size)) as painted:
            for number, part in enumerate(layout['parts'], 1):
                data = crop_bytes(painted[part['page'] - 1], part['bbox'])
                path = crops / f'item-part-{number:03}.png'
                path.write_bytes(data)
                parts.append({**part, 'raster_path': path.relative_to(root).as_posix(),
                              'raster_sha256': hashlib.sha256(data).hexdigest(), 'status': 'pending', 'observations': ''})
        annotate_parts(parts, hashes)
        save(output / (role + '-items.json'), {
            'kind': 'pre-pagination-item-proof', 'role': role, 'paper_id': state['paper_id'],
            'exam_sha256': state['exam']['sha256'], 'pdf_sha256': layout['pdf_sha256'],
            'render_identity': identity,
            'source': {**record(root, body), 'projected': True, 'page_size': page_size},
            'parts': parts,
            'scope': 'Early crop review only; final booklets still need every page reviewed and fresh final crops.'})
        # Absolute paths: the helper's working directory is not the run.
        notes = template.setdefault(role, {'items': {}})
        for part, key in zip(parts, crop_keys(parts)):
            image = str((root / part['raster_path']).resolve())
            queue.append(image)
            by_item.setdefault(part['id'], []).append((image, {'role': role, 'items': key}))
            notes['items'][key] = pending_note()
    save(output / 'proof-manifest.json', {'kind': 'hosted-item-proof', 'paper_id': state['paper_id'], 'items': wanted})
    save(output / 'observations-template.json', template)
    transition(root / 'generation-timing.json', state['paper_id'], 'visual_qa')
    event(root, 'proof', started, items=wanted)
    # An item's question and solution crops side by side: separate native images.
    return {'status': 'proof-review-pending', 'proof': output.name, 'proof_dir': str(output),
            'review_queue': queue,
            'review_batches': [{'item': qid, 'images': [image for image, _ in rows],
                                'record_as': [target for _, target in rows]} for qid, rows in by_item.items()],
            'observations_template': str(output / 'observations-template.json'),
            'reviews_approved_by_tool': False,
            'next': ('Open each crop at readable scale, fill status and observations in a copy of observations_template, '
                     'and record them with one record-review --proof ' + str(output) + ' call')}


REVIEW_STATUSES = {'pass', 'fail', 'pending'}


def apply_review(row, note, where, issues=None):
    if not isinstance(note, dict) or set(note) - {'status', 'observations', 'issue_dispositions'}:
        raise ValueError(where + ': use status, observations and optional issue_dispositions')
    status, observations = note.get('status'), note.get('observations', '')
    if status not in REVIEW_STATUSES:
        raise ValueError(where + ': status must be pass, fail or pending; the tool never assumes pass')
    if isinstance(observations, list) and all(isinstance(line, str) for line in observations):
        # Reviewers naturally list what they saw; joining the lines keeps every word.
        observations = '; '.join(line.strip() for line in observations if line.strip())
    if not isinstance(observations, str) or (status != 'pending' and not observations.strip()):
        raise ValueError(where + ': record the actual observation behind this status as text')
    row.update(status=status, observations=observations.strip())
    row.pop('review_basis', None)
    for issue, finding in (note.get('issue_dispositions') or {}).items():
        if issues is None or issue not in issues:
            raise ValueError(where + f': no mechanical issue {issue} on this page')
        finding = dict(finding)
        choice = finding.pop('embedded_reference', None)
        if choice is not None:
            references = (row.get('density_evidence') or {}).get('embedded_references', [])
            if issue != 'large-bottom-void-review' or type(choice) is not int or not 0 <= choice < len(references):
                raise ValueError(where + ': no qualifying embedded page measurement at that index; reflow this page')
            finding.update({k: references[choice][k] for k in ('kind', 'source_sha256', 'reference_page', 'page_role')})
        if finding.get('decision') != 'justified' or not str(finding.get('reason', '')).strip():
            raise ValueError(where + f': {issue} needs decision justified and the actual reason, or a repaired PDF')
        row.setdefault('issue_dispositions', {})[issue] = finding


def record_review(observations, *, state=None, proof=None):
    """Write the reviewer's actual findings into pending reports; never supplies a pass.

    observations: {"question": {"pages": {"3": {...}}, "items": {"q7": {...}, "q9#2": {...}}}, ...}
    Final booklets use --state and refresh registered review hashes; item proofs use --proof.
    """
    if (state is None) == (proof is None):
        raise ValueError('Use --state for final booklets or --proof for an item proof')
    notes = read(observations)
    if state:
        state_path = Path(state).resolve()
        root = state_path.parent
        bundles = read(state_path).get('pdfs', {})
        targets = {role: {'items': root / b['item_review']['path'], 'pages': root / b['visual_review']['path'],
                          'inspection': root / b['inspection']['path']} for role, b in bundles.items()}
    else:
        folder = Path(proof).resolve()
        root = folder.parent
        targets = {role: {'items': folder / (role + '-items.json')} for role in ('question', 'solution')
                   if (folder / (role + '-items.json')).is_file()}
    for paths in targets.values():
        for path in paths.values():
            inside(root, path)
    if not isinstance(notes, dict) or not notes or set(notes) - set(targets):
        raise ValueError('Observations must map existing booklet roles: ' + ', '.join(sorted(targets)))

    def intact(row):
        path = inside(root, root / row['raster_path'])
        if digest(path) != row['raster_sha256']:
            raise ValueError('Reviewed image changed: ' + row['raster_path'])

    summary = {}
    for role, sections in notes.items():
        if not isinstance(sections, dict) or set(sections) - {'pages', 'items'}:
            raise ValueError(role + ': use pages and/or items')
        if sections.get('pages'):
            if 'pages' not in targets[role]:
                raise ValueError('Item proofs have crops only; review pages on the final booklets')
            report = read(targets[role]['pages'])
            scan = {p['page']: p for p in read(targets[role]['inspection'])['pages']}
            rows = {str(row['page']): row for row in report['pages']}
            for key, note in sections['pages'].items():
                row = rows.get(str(key))
                if row is None:
                    raise ValueError(f'{role}: no page {key}')
                intact(scan[row['page']])
                apply_review(row, note, f'{role} page {key}', scan[row['page']]['issues'])
            save(targets[role]['pages'], report)
        if sections.get('items'):
            report = read(targets[role]['items'])
            keyed = dict(zip(crop_keys(report['parts']), report['parts']))
            for key, note in sections['items'].items():
                part = keyed.get(key)
                if part is None:
                    raise ValueError(f'{role}: unknown crop {key}; multi-part items use id#n: ' + ', '.join(keyed))
                intact(part)
                apply_review(part, note, f'{role} item {key}')
            save(targets[role]['items'], report)
    if state:
        refresh_review_hashes(state_path)
    for role, paths in targets.items():
        items = read(paths['items'])['parts']
        remaining = {'items_pending': [p['raster_path'] for p in items if p.get('status') != 'pass']}
        if 'pages' in paths:
            report = read(paths['pages'])
            scan = {p['page']: p for p in read(paths['inspection'])['pages']}
            remaining['pages_pending'] = [scan[r['page']]['raster_path'] for r in report['pages'] if r.get('status') != 'pass']
            remaining['unresolved_issues'] = [f"page {r['page']}: {issue}" for r in report['pages']
                                              for issue in scan[r['page']]['issues']
                                              if issue not in r.get('issue_dispositions', {})]
        summary[role] = remaining
    return {'status': 'observations-recorded', 'remaining': summary, 'reviews_approved_by_tool': False}


def finalize(state_path, output):
    started = time.time()
    state_path = Path(state_path).resolve()
    root = state_path.parent
    state = read(state_path)
    output = inside(root, output)
    protected = {state_path, root / 'exam.json', root / 'generation-timing.json', root / 'preflight.json'}
    # Gate files may exist before their first registration. Never replace their
    # real observations with the final result, even when absent from old state.
    protected.update(root / (gate + '.json') for gate in ITEM_GATES + PAPER_GATES)
    def collect(value):
        if isinstance(value, dict):
            if isinstance(value.get('path'), str):
                protected.add((root / value['path']).resolve())
            for nested in value.values(): collect(nested)
        elif isinstance(value, list):
            for nested in value: collect(nested)
    collect(state)
    if output in protected or output.suffix.lower() != '.json':
        raise ValueError('Final report must not overwrite input or evidence artifacts')
    if output.exists():
        previous = read(output)
        if (not isinstance(previous, dict) or
                previous.get('scope') != 'Evidence completeness and freshness only; recorded judgments need real review.' or
                previous.get('status') not in {'pending', 'evidence-complete'} or
                previous.get('formal_acceptance') is not False or not isinstance(previous.get('errors'), list)):
            raise ValueError('Final report must not overwrite unrelated existing work')
    exam_path = inside(root, root / state['exam']['path'])
    if record(root, exam_path) != state['exam']:
        raise ValueError('Exam changed; recheck affected content and rebuild before finalizing')
    register_reviews(root, state)
    timing = root / 'generation-timing.json'
    if read(timing).get('active') is not None:
        transition(timing, state['paper_id'])
    state['timing'] = record(root, timing)
    save(state_path, state)
    result = check(state_path)
    if result.get('status') == 'evidence-complete':
        result['delivery'] = deliver(root, state)
    save(output, result)
    event(root, 'finalize', started, status=result['status'])
    return result


def recorded_font(state_path):
    """The body font prepare_hosted_run.py chose for this run."""
    root = Path(state_path).resolve().parent
    recorded = (read(root / 'preflight.json').get('body_font') or {}).get('path')
    if not recorded:
        raise ValueError('The preflight recorded no body font; rerun prepare_hosted_run.py or pass --font')
    return Path(recorded) if Path(recorded).is_absolute() else inside(root, root / recorded)


def deliver(root, state):
    """Copies of the checked booklets to hand over: same pixels and text, no unused font data."""
    folder = root / 'delivery'
    folder.mkdir(exist_ok=True)
    copies = {}
    for role, bundle in sorted(state.get('pdfs', {}).items()):
        source = inside(root, root / bundle['file']['path'])
        if digest(source) != bundle['file']['sha256']:
            raise ValueError('Checked booklet changed before delivery: ' + bundle['file']['path'])
        compact, report = compact_fonts(source.read_bytes())
        target = folder / (role + '.pdf')
        target.write_bytes(compact)
        copies[role] = {'path': str(target), 'bytes': len(compact), 'sha256': hashlib.sha256(compact).hexdigest(),
                        'checked_pdf': bundle['file'], 'font_compaction': report}
    return copies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    start = commands.add_parser('checkpoint')
    start.add_argument('--run-dir', type=Path, required=True)
    start.add_argument('--phase', choices=sorted(PHASES))
    start.add_argument('--review-bundle', type=Path)
    start.add_argument('--state', type=Path, help='On repair, continue the latest review state')
    build_parser = commands.add_parser('build')
    for name in ('state', 'question-spec', 'solution-spec', 'output'):
        build_parser.add_argument('--' + name, type=Path, required=True)
    build_parser.add_argument('--font', type=Path, help='Defaults to the body font recorded by the preflight')
    build_parser.add_argument('--year', required=True)
    build_parser.add_argument('--title', default='學科能力測驗模擬試題')
    build_parser.add_argument('--running-name', default='學測')
    build_parser.add_argument('--reading-font', type=Path)
    spec_parser = commands.add_parser('specs', help='Project saved items into both body layout specs')
    spec_parser.add_argument('--state', type=Path, required=True)
    spec_parser.add_argument('--question-output', type=Path, required=True)
    spec_parser.add_argument('--solution-output', type=Path, required=True)
    spec_parser.add_argument('--hints', type=Path, help='Layout-only choices and special-structure blocks')
    proof_parser = commands.add_parser('proof', help='Render selected saved items for early crop review')
    for name in ('state', 'question-spec', 'solution-spec', 'output'):
        proof_parser.add_argument('--' + name, type=Path, required=True)
    proof_parser.add_argument('--font', type=Path, help='Defaults to the body font recorded by the preflight')
    proof_parser.add_argument('--items', required=True, help='Comma-separated saved question ids')
    proof_parser.add_argument('--reading-font', type=Path)
    notes = commands.add_parser('record-review', help="Write the reviewer's actual page/crop findings")
    notes.add_argument('--observations', type=Path, required=True)
    target = notes.add_mutually_exclusive_group(required=True)
    target.add_argument('--state', type=Path, help='Review state returned by build')
    target.add_argument('--proof', type=Path, help='Item proof directory')
    finish = commands.add_parser('finalize')
    finish.add_argument('--state', type=Path, required=True)
    finish.add_argument('--output', type=Path, required=True)
    args = vars(parser.parse_args())
    action = args.pop('action')
    try:
        if action == 'checkpoint':
            result = checkpoint(**args)
        elif action == 'record-review':
            result = record_review(args.pop('observations'), **args)
        else:
            args['state_path'] = args.pop('state')
            if action in {'build', 'proof'} and args['font'] is None:
                args['font'] = recorded_font(args['state_path'])
            result = {'build': build, 'specs': specs, 'proof': proof, 'finalize': finalize}[action](**args)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(json.dumps({'status': 'pending', 'errors': [str(exc)]}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result.get('status') == 'pending' else 0


if __name__ == '__main__':
    raise SystemExit(main())
