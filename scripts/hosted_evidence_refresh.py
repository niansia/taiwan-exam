#!/usr/bin/env python3
"""Evidence freshness at checkpoint time, drafts after a content change, and a figure self-check.

Three measured hosted runs (2026-09-22) learned about stale gate reports only
from `finalize`, up to five times in one paper; every content correction
silently orphaned nine reports, and figure defects (missing glyphs, labels on
strokes, colour-only distinctions) were found by eye on a full build, one
rebuild per defect.

This module gives the workflow three mechanical helpers:

* `evidence_gaps` says at every checkpoint which gate reports are missing,
  stale (with the items that changed since that review) or structurally
  incomplete, in the same terms the final checker uses.
* `refresh` writes `<gate>.draft.json` files after a content change: rows for
  items whose authored record is unchanged are copied from the earlier actual
  review, changed or new items are `pending`, the paper-level status is
  `pending`, and the difficulty blind packet is regenerated. The reviewer
  completes the pending rows and saves the result as `<gate>.json`; the checker
  never reads a draft, and nothing here writes a `pass`.
* `figure_selfcheck` opens every figure the exam references and reports what a
  machine can see before any PDF exists: missing or renamed files, HTML saved
  as an image, unreadable artwork, printed-size defects, colour-only pixels,
  glyphs that CJK-only fonts lack, and labels sitting on strokes.

Structural passes are never editorial passes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

import pymupdf

from check_hosted_run import ITEM_GATES, PAPER_GATES
from hosted_blind_review import packet, review_errors, REVIEW_MODES

HISTORY = 'exam-history.json'
ORIGINALITY_SCOPES = {'available-history', 'no-history-available'}
HTML_MAGIC = (b'<!doctype', b'<html', b'<head', b'<body')
# Superscript/subscript digits and signs: matplotlib's DejaVu draws them, CJK-only
# fonts and several system fonts print boxes.
RISKY_GLYPHS = re.compile('[⁰-₟−]')
MISSING_GLYPH = re.compile('[�□⬚]')
COLOUR_SPREAD = 48
COLOUR_SHARE_WARN = 0.01
RASTER_MAX_WIDTH = 600


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def _write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    return {'path': Path(path).name, 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def _digest_value(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


# Author-only planning and review metadata: never printed and never shown to a gate's
# reviewer. A hosted 數B run synced difficulty labels after review and every item gate
# re-opened although no reviewed content changed.
AUTHOR_ONLY_QUESTION_FIELDS = frozenset({'item_spec', 'expected_minutes', 'difficulty', 'difficulty_label'})
AUTHOR_ONLY_ANSWER_FIELDS = frozenset({'independent_review', 'difficulty_label', 'verification_status',
                                       'verification_notes'})


def item_digests(exam):
    """{item id: digest of its reviewed question and answer records}, in exam order."""
    answers = {a.get('question_id'): a for a in exam.get('answers') or [] if isinstance(a, dict)}
    def reviewed(record, hidden):
        return {k: v for k, v in record.items() if k not in hidden} if isinstance(record, dict) else record
    return {str(q.get('id')): _digest_value({'question': reviewed(q, AUTHOR_ONLY_QUESTION_FIELDS),
                                             'answer': reviewed(answers.get(q.get('id')), AUTHOR_ONLY_ANSWER_FIELDS)})
            for q in exam.get('questions') or [] if isinstance(q, dict)}


def record_history(root, exam_sha, exam):
    """Remember which items each checkpointed exam contained, so a stale report can name what changed."""
    path = Path(root) / HISTORY
    history = _read(path) if path.exists() else {'kind': 'hosted-exam-history', 'exams': {}}
    if exam_sha not in history['exams']:
        history['exams'][exam_sha] = item_digests(exam)
        _write(path, history)
    return history


def item_changes(history, old_sha, current):
    old = ((history or {}).get('exams') or {}).get(old_sha)
    if old is None:
        return None
    return {'changed': sorted(i for i in current if i in old and old[i] != current[i]),
            'added': sorted(i for i in current if i not in old),
            'removed': sorted(i for i in old if i not in current)}


def _gate_path(root, state, gate):
    registered = ((state.get('checks') or {}).get(gate) or {}).get('path')
    return Path(root) / (registered or gate + '.json')


def evidence_gaps(root, state, exam):
    """Missing, stale and structurally incomplete gate reports, in the checker's terms.

    Freshness and shape only: a `current` report still had to be a real review.
    """
    root = Path(root)
    exam_sha = state['exam']['sha256']
    current = item_digests(exam)
    expected = set(current)
    history_path = root / HISTORY
    history = _read(history_path) if history_path.exists() else {}
    gates = {}
    for gate in ITEM_GATES + PAPER_GATES:
        path = _gate_path(root, state, gate)
        if not path.is_file():
            gates[gate] = {'status': 'missing', 'action': f'save the actual {gate} review as {gate}.json'}
            continue
        try:
            report = _read(path)
        except ValueError:
            gates[gate] = {'status': 'unreadable', 'action': f'{path.name} is not valid JSON'}
            continue
        if not isinstance(report, dict):
            gates[gate] = {'status': 'unreadable', 'action': f'{path.name} must be one JSON object'}
            continue
        if report.get('exam_sha256') != exam_sha:
            entry = {'status': 'stale', 'reviewed_exam_sha256': report.get('exam_sha256'),
                     'action': 'run refresh-evidence: it drafts the report with unchanged rows retained; '
                               're-review the pending rows and save the result as ' + gate + '.json'}
            changes = item_changes(history, report.get('exam_sha256'), current)
            if changes is not None:
                entry['items'] = changes
            gates[gate] = entry
            continue
        problems = []
        if report.get('status') != 'pass':
            problems.append(f"status is {report.get('status')!r}, not 'pass'")
        if not report.get('observations'):
            problems.append('observations are empty')
        if gate in ITEM_GATES:
            rows = [r for r in report.get('items') or [] if isinstance(r, dict)]
            ids = [str(r.get('id')) for r in rows]
            missing = sorted(expected - set(ids))
            extra = sorted(set(ids) - expected)
            if missing:
                problems.append('items without a review row: ' + ', '.join(missing))
            if extra:
                problems.append('rows for items no longer in the exam: ' + ', '.join(extra))
            if len(ids) != len(set(ids)):
                problems.append('duplicate item rows')
            allowed = {'pass', 'not_applicable'} if gate == 'visuals' else {'pass'}
            pending = sorted(str(r.get('id')) for r in rows if r.get('status') not in allowed or not r.get('observations'))
            if pending:
                problems.append('rows pending or without observations: ' + ', '.join(pending))
        if gate == 'difficulty':
            blind = report.get('blind_packet') or {}
            blind_path = root / str(blind.get('path') or '')
            if not blind or not blind_path.is_file():
                problems.append('blind_packet is missing')
            else:
                mode = report.get('review_mode', 'independent-context')
                if mode in REVIEW_MODES:
                    try:
                        if _read(blind_path) != packet(exam, mode):
                            problems.append('blind packet no longer matches the exam')
                    except ValueError:
                        problems.append('blind packet is not valid JSON')
            if not report.get('author_context'):
                problems.append('author_context is missing')
            # The final checker's own difficulty rules, now at every checkpoint: two hosted
            # 數學 runs first learned at finalize that a row called routine was labelled 中偏難.
            problems.extend(error.split(': ', 1)[-1] if error.startswith('difficulty: ') else error
                            for error in review_errors(exam, report))
        if gate == 'originality' and report.get('comparison_scope') not in ORIGINALITY_SCOPES:
            problems.append('comparison_scope must disclose available-history or no-history-available')
        gates[gate] = {'status': 'incomplete', 'problems': problems} if problems else {'status': 'current'}
    ready = all(g['status'] == 'current' for g in gates.values())
    return {'ready': ready, 'gates': gates,
            'attention': sorted(g for g, v in gates.items() if v['status'] != 'current'),
            'note': 'Freshness and structure only; a current report still had to be an actual review.'}


def refresh(root, state, exam):
    """Draft every stale gate report against the current exam; never write <gate>.json."""
    root = Path(root)
    exam_sha = state['exam']['sha256']
    record_history(root, exam_sha, exam)
    gaps = evidence_gaps(root, state, exam)
    current = item_digests(exam)
    drafts = {}
    for gate, gap in gaps['gates'].items():
        if gap['status'] != 'stale':
            continue
        old = _read(_gate_path(root, state, gate))
        changes = gap.get('items')
        draft = dict(old)
        draft.update(exam_sha256=exam_sha, status='pending', observations='',
                     previous_observations=old.get('observations'))
        retained, pending = [], []
        if gate in ITEM_GATES:
            rows = {str(r.get('id')): r for r in old.get('items') or [] if isinstance(r, dict)}
            new_rows = []
            for qid in current:
                row = rows.get(qid)
                unchanged = (changes is not None and row is not None
                             and qid not in changes['changed'] and qid not in changes['added'])
                if unchanged:
                    new_rows.append(row)
                    retained.append(qid)
                else:
                    new_rows.append({'id': qid, 'status': 'pending', 'observations': ''})
                    pending.append(qid)
            draft['items'] = new_rows
        if gate == 'difficulty':
            mode = old.get('review_mode', 'independent-context')
            if mode in REVIEW_MODES:
                draft['blind_packet'] = _write(root / f'blind-packet-{exam_sha[:12]}.json', packet(exam, mode))
        draft['refresh'] = {
            'from_exam_sha256': old.get('exam_sha256'), 'retained_rows': retained, 'pending_rows': pending,
            'history_known': changes is not None,
            'note': ('Draft written by refresh-evidence. Rows for items whose authored record is unchanged are '
                     'copied from the earlier actual review; pending rows and the paper-level status and '
                     'observations need the reviewer. Save the completed review as ' + gate + '.json; the '
                     'checker never reads this draft and no draft is a pass.')}
        target = root / f'{gate}.draft.json'
        _write(target, draft)
        drafts[gate] = {'path': str(target), 'retained_rows': len(retained), 'pending_rows': len(pending),
                        'paper_level': 'pending'}
    return {'status': 'evidence-current' if gaps['ready'] else 'review-pending', 'evidence': gaps,
            'drafts': drafts, 'reviews_approved_by_tool': False}


def referenced_figures(exam):
    """Every asset record the exam references: (label, record, inline?)."""
    found = []

    def visit(value, label, inline):
        if isinstance(value, dict):
            if isinstance(value.get('path'), str) and value.get('sha256'):
                found.append((label, value, inline))
                return
            for key, child in value.items():
                visit(child, f'{label}.{key}', inline or key == 'inline_assets')
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f'{label}[{index}]', inline)

    answers = {a.get('question_id'): a for a in exam.get('answers') or [] if isinstance(a, dict)}
    for question in exam.get('questions') or []:
        if not isinstance(question, dict):
            continue
        qid = str(question.get('id'))
        visit(question, f'item {qid}', False)
        answer = answers.get(question.get('id'))
        if isinstance(answer, dict):
            visit(answer, f'item {qid} answer', False)
    return found


def _stable_raster(path, dpi=150):
    """Two fresh rasterizations of the figure's first page give the same pixels."""
    digests = []
    for _ in range(2):
        with pymupdf.open(path) as document:
            digests.append(hashlib.sha256(document[0].get_pixmap(dpi=dpi, alpha=False).samples).hexdigest())
    return digests[0] == digests[1]


def _colour_share(page):
    box = page.rect
    scale = min(1.0, RASTER_MAX_WIDTH / box.width) if box.width else 1.0
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False, colorspace=pymupdf.csRGB)
    samples = pixmap.samples
    total = pixmap.width * pixmap.height
    if not total:
        return 0.0
    coloured = 0
    for offset in range(0, len(samples), 3):
        r, g, b = samples[offset], samples[offset + 1], samples[offset + 2]
        if max(r, g, b) - min(r, g, b) > COLOUR_SPREAD:
            coloured += 1
    return coloured / total


TABLE_KINDS = {'data_table', 'table', 'evidence_matrix'}
TABLE_OVERFLOW_ADVICE = ('table text runs past its cell borders ({where}): widen that column or the table, or break the '
                         'header onto two lines (「生態最低量」 over 「（萬噸）」); never shrink the text below the body size')


def is_table_figure(asset):
    """A figure the paper prints as a table: its kind, or a 「表N」 caption."""
    spec = asset.get('visual_spec') if isinstance(asset.get('visual_spec'), dict) else {}
    caption = str(asset.get('caption') or spec.get('caption') or '').strip()
    return str(spec.get('kind') or '') in TABLE_KINDS or caption.startswith('表')


def table_text_overflow(page, *, rule=160, ink=150):
    """Rows of a drawn table where text crosses a cell border, read from pixels.

    A hosted 社會 table printed its header 「生態最低量（萬噸）」 past the table's right edge.
    Most generated figures are PNG, so the check reads ink, not text objects: it finds the
    table's rules (long dark rows and full-height dark columns) and reports a border that
    has ink pressed against both of its sides inside one row, as text running across it does.
    Rules are found at gray < `rule` (a header's border under a light fill measured 147, the
    fill 215); text ink at gray < `ink`.
    """
    zoom = min(4.0, max(1.0, 1400 / max(page.rect.width, 1)))
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csGRAY, alpha=False)
    width, height, samples = pix.width, pix.height, pix.samples
    rows = [samples[y * pix.stride:y * pix.stride + width] for y in range(height)]

    def longest_run(row):
        best = run = start = best_start = 0
        for x, value in enumerate(row):
            if value < rule:
                if not run:
                    start = x
                run += 1
                if run > best:
                    best, best_start = run, start
            else:
                run = 0
        return best, best_start

    horizontal = []
    for y, row in enumerate(rows):
        length, start = longest_run(row)
        if length >= 0.35 * width:
            if horizontal and y - horizontal[-1][1] <= 1:
                horizontal[-1][1] = y
            else:
                horizontal.append([y, y, start, start + length])
    if len(horizontal) < 2:
        return []
    top, bottom = horizontal[0][0], horizontal[-1][1]
    left = min(h[2] for h in horizontal)
    right = max(h[3] for h in horizontal)
    span = bottom - top + 1
    vertical = []
    for x in range(max(0, left - 3), min(width, right + 4)):
        drawn = sum(1 for y in range(top, bottom + 1) if rows[y][x] < rule)
        if drawn >= 0.9 * span:
            if vertical and x - vertical[-1][1] <= 1:
                vertical[-1][1] = x
            else:
                vertical.append([x, x])
    if len(vertical) < 2:
        return []
    found = []
    reach = max(2, round(0.9 * zoom))  # about 1 pt beside the rule; tidy cells pad their text by more
    for upper, lower in zip(horizontal, horizontal[1:]):
        y0, y1 = upper[1] + 3, lower[0] - 3
        if y1 - y0 < 4:
            continue
        band = range(y0, y1 + 1)
        for column, (x0, x1) in enumerate(vertical):
            if x0 - reach - 1 < 0 or x1 + reach + 1 >= width:
                continue

            def side(xs):
                return {y for y in band if any(rows[y][x] < ink for x in xs)}
            left_ink = side(range(x0 - reach, x0))
            right_ink = side(range(x1 + 1, x1 + reach + 1))
            if max(len(left_ink), len(right_ink)) >= 0.8 * len(band):
                continue  # the rule itself is thicker here, not text beside it
            # Strokes that cross a rule touch both of its sides in a few pixel rows; three is
            # enough, since a tidy cell never inks the pixel beside its own border.
            if len(left_ink & right_ink) >= 3:
                edge = 'right edge' if column == len(vertical) - 1 else 'left edge' if column == 0 else 'a cell border'
                found.append(f'row {horizontal.index(upper) + 1}: text runs across {edge}')
    return found


def _label_collisions(page):
    """Text spans whose box a drawn stroke crosses (frames that contain the label do not count)."""
    spans = []
    for block in page.get_text('dict').get('blocks', []):
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                text = (span.get('text') or '').strip()
                if text:
                    spans.append((text, pymupdf.Rect(span['bbox'])))
    if not spans:
        return []
    strokes = []
    for drawing in page.get_drawings():
        for item in drawing.get('items', []):
            if item[0] == 'l':
                strokes.append(pymupdf.Rect(item[1], item[2]).normalize())
            elif item[0] in {'c', 'qu', 're'}:
                rect = drawing.get('rect')
                if rect is not None:
                    strokes.append(pymupdf.Rect(rect))
    hits = []
    for text, box in spans:
        inner = pymupdf.Rect(box.x0 + 0.5, box.y0 + 0.5, box.x1 - 0.5, box.y1 - 0.5)
        if inner.is_empty:
            continue
        for stroke in strokes:
            probe = pymupdf.Rect(stroke)
            if probe.width < 0.6:
                probe.x0 -= 0.3
                probe.x1 += 0.3
            if probe.height < 0.6:
                probe.y0 -= 0.3
                probe.y1 += 0.3
            if probe.intersects(inner) and not probe.contains(inner):
                hits.append(text)
                break
    return hits


def figure_selfcheck(root, exam, *, asset_issues=None):
    """Open every referenced figure and report what a machine can see before a build."""
    root = Path(root)
    figures = []
    seen_hashes = {}
    for label, asset, inline in referenced_figures(exam):
        entry = {'referenced_by': label, 'path': asset['path'], 'errors': [], 'warnings': []}
        figures.append(entry)
        path = (root / asset['path']).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            entry['errors'].append('path leaves the run directory')
            continue
        if not path.is_file():
            entry['errors'].append('file is missing; the item references a figure that was never saved or was renamed')
            continue
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != asset['sha256']:
            entry['errors'].append('sha256 differs from the saved record: the figure was redrawn after the item was saved; '
                                   'save the item again with the new hash')
        if not data:
            entry['errors'].append('file is empty (0 bytes)')
            continue
        head = data[:256].lstrip().lower()
        if head.startswith(HTML_MAGIC):
            entry['errors'].append('file is an HTML page saved under an image name (a blocked download); '
                                   'use a bundled asset or draw the figure from verified data')
            continue
        seen_hashes.setdefault(actual, []).append(asset['path'])
        try:
            document = pymupdf.open(path)
        except Exception as exc:  # MuPDF raises its own error types for unreadable artwork
            entry['errors'].append(f'cannot be opened as a figure: {exc}')
            continue
        with document:
            if not len(document):
                entry['errors'].append('figure has no pages')
                continue
            page = document[0]
            if not page.rect.width or not page.rect.height:
                entry['errors'].append('figure has no size')
                continue
            if asset_issues is not None:
                entry['errors'].extend(asset_issues(path, asset, inline=inline))
            if is_table_figure(asset):
                overflow = table_text_overflow(page)
                if overflow:
                    entry['errors'].append(TABLE_OVERFLOW_ADVICE.format(where='; '.join(overflow[:4])))
            if isinstance(asset.get('visual_spec'), dict):
                from validate_visual_item_contract import english_label_errors
                subject = (exam.get('metadata') or {}).get('subject')
                entry['errors'].extend(e.split(': ', 1)[1] for e in english_label_errors(label, asset['visual_spec'], path, subject))
            text = page.get_text() or ''
            missing = sorted(set(MISSING_GLYPH.findall(text)))
            if missing:
                entry['errors'].append('contains replacement or box glyphs (' + ', '.join(f'U+{ord(c):04X}' for c in missing)
                                       + '): a character the figure font lacks was drawn as a box')
            risky = sorted(set(RISKY_GLYPHS.findall(text)))
            if risky:
                entry['warnings'].append('uses ' + ', '.join(f'U+{ord(c):04X}' for c in risky) +
                                         ': confirm the figure font draws these superscript/subscript glyphs '
                                         '(DejaVu does; CJK-only fonts print boxes) or write them with mathtext')
            try:
                share = _colour_share(page)
            except Exception:  # very large or odd colour spaces: leave the eye to judge
                share = None
            if share is not None and share > COLOUR_SHARE_WARN:
                entry['warnings'].append(f'{share:.0%} of pixels carry colour: the paper prints in grayscale, so the '
                                         'answer-bearing distinction must also be carried by labels, patterns, '
                                         'markers or line styles')
            if not _stable_raster(path):
                # A hosted 英文 run learned this at the final check, after two builds:
                # the booklet page carrying the figure rasterized differently each time,
                # so its recorded page review could never bind.
                entry['errors'].append('renders to different pixels on two consecutive rasterizations: re-export it '
                                       'as a flat PNG (no transparency groups or soft masks) before the first proof')
            try:
                hits = _label_collisions(page)
            except Exception:
                hits = []
            if hits:
                entry['warnings'].append('labels sit on strokes: ' + ', '.join(hits[:6]) +
                                         ('…' if len(hits) > 6 else '') + '; move the labels or shorten the strokes')
    for digest_, paths in seen_hashes.items():
        if len(set(paths)) > 1:
            for entry in figures:
                if entry['path'] in paths:
                    entry['warnings'].append('identical bytes are saved under several paths: ' + ', '.join(sorted(set(paths))))
    errors = sum(len(f['errors']) for f in figures)
    warnings = sum(len(f['warnings']) for f in figures)
    return {'status': 'pass' if not errors else 'pending', 'figures': figures, 'figure_count': len(figures),
            'errors': errors, 'warnings': warnings,
            'note': ('Mechanical checks only. Whether a dashed line reads as dashed at print size, whether the '
                     'legend matches the drawn series and whether the labels are true still needs the eye on the '
                     'proof crop; a pass here removes the redraw round trips, not the review.')}
