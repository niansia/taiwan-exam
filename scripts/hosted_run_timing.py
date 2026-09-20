#!/usr/bin/env python3
"""Conversation-aware phase clock. Wall time and estimated activity stay distinct.

phase PHASE starts work; touch records activity; pause (or idle) closes work
before yielding to the user; resume starts a new interval; finish closes the run.
Idle detection is evaluated on the next call, not by a background monitor.
Legacy intervals are never retrospectively labelled as measured active work.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time

PHASES = {'reference_preflight', 'authoring', 'solving', 'render_repair', 'visual_qa', 'difficulty_qa'}
IDLE_SECONDS = 600


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def timing_errors(report, paper_id):
    errors = []
    rows = report.get('intervals', [])
    if report.get('paper_id') != paper_id or report.get('active') is not None or report.get('paused'):
        errors.append('timing: wrong paper or unfinished interval')
    if {r.get('phase') for r in rows if r.get('state') != 'waiting'} != PHASES:
        errors.append('timing: all six measured phases required')
    previous = None
    for row in rows:
        start, end = row.get('start'), row.get('end')
        if not all(finite(v) for v in (start, end)):
            errors.append('timing: invalid clock reading')
            continue
        if end <= start or (previous is not None and start < previous):
            errors.append('timing: reversed or overlapping intervals')
        if row.get('state') not in (None, 'active', 'waiting'):
            errors.append('timing: unknown interval state')
        previous = end
    if not rows:
        errors.append('timing: no measured intervals')
    return errors


def transition(path, paper_id, phase=None, *, action=None, question_ids=None,
               page_numbers=None, revision_id=None, idle_seconds=IDLE_SECONDS):
    path = Path(path)
    now = time.time()
    action = action or ('phase' if phase else 'finish')
    if action not in {'phase', 'finish', 'pause', 'idle', 'resume', 'touch'}:
        raise ValueError('Unknown clock action')
    if (action == 'phase' and phase not in PHASES) or (phase is not None and phase not in PHASES):
        raise ValueError('Unknown phase')
    if not finite(idle_seconds) or idle_seconds <= 0:
        raise ValueError('Idle threshold must be positive and finite')
    report = json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {
        'schema_version': 2, 'paper_id': paper_id, 'intervals': [], 'active': None,
        'started_at': now}
    if report['paper_id'] != paper_id:
        raise ValueError('Refusing to mix paper clocks')
    active, paused = report.get('active'), report.get('paused')
    boundaries = [r['end'] for r in report['intervals']]
    boundaries += [r.get('last_activity', r['start']) for r in (active, paused) if r]
    if boundaries and now < max(boundaries):
        raise ValueError('Clock moved backwards; retain log and investigate')
    if action == 'touch' and not active:
        raise ValueError('Resume a phase before recording activity')
    next_phase = phase or (active or paused or {}).get('phase') or report.get('last_phase')
    if action == 'resume' and next_phase not in PHASES:
        raise ValueError('No phase to resume')
    # A duplicate finish is read-only, including the original stop boundary.
    if action == 'finish' and report.get('finished_at') and not (active or paused):
        return report
    report.pop('finished_at', None)
    report.pop('ended_at', None)

    def append(row, end, **extra):
        if end > row['start']:
            report['intervals'].append({**row, 'end': end, **extra})

    if active:
        active = dict(active)
        # Workflow tools already leave actual start/end events. Consume them
        # here instead of modifying a clock hash after a state was saved.
        if 'last_activity' in active:
            activity = []
            for event in workflow_events(path.parent):
                if not isinstance(event, dict):
                    continue
                start, seconds = event.get('started_at'), event.get('elapsed_seconds')
                if finite(start) and finite(seconds) and seconds >= 0:
                    end = start + seconds
                    if active['start'] <= end <= now and end > active['last_activity']:
                        activity.append((max(start, active['start']), end))
            for start, end in sorted(activity):
                cutoff = active['last_activity'] + active.get('idle_seconds', idle_seconds)
                if start > cutoff:
                    append(active, cutoff)
                    append({**active, 'start': cutoff}, start, state='waiting', estimated=True,
                           reason='no recorded activity beyond idle threshold')
                    active['start'] = start
                active['last_activity'] = max(active['last_activity'], end)
            report['active'] = active
        # Old logs have no heartbeat contract: preserve their unknown duration.
        cutoff = min(now, active.get('last_activity', now) + active.get('idle_seconds', idle_seconds))
        if action == 'touch' and cutoff == now:
            active['last_activity'] = now
        else:
            append(active, cutoff)
            if cutoff < now:
                append({**active, 'start': cutoff}, now, state='waiting', estimated=True,
                       reason='no recorded activity beyond idle threshold')
            report['active'] = None
    if paused:
        append(paused, now)
        report.pop('paused', None)
    context = {k: v for k, v in {'question_ids': question_ids, 'page_numbers': page_numbers,
                                'revision_id': revision_id}.items() if v is not None}
    if action in {'phase', 'resume', 'touch'}:
        if report.get('active') is None:
            inherited = {k: v for k, v in (active or paused or {}).items()
                         if k in {'question_ids', 'page_numbers', 'revision_id'}}
            report['active'] = {'phase': next_phase, 'start': now, 'last_activity': now,
                                'state': 'active', 'idle_seconds': idle_seconds, **inherited, **context}
        else:
            report['active'].update(context)
        report['last_phase'] = next_phase
    elif action in {'pause', 'idle'}:
        inherited = {k: v for k, v in (active or paused or {}).items()
                     if k in {'question_ids', 'page_numbers', 'revision_id'}}
        report['paused'] = {'phase': next_phase, 'start': now, 'state': 'waiting',
                            'estimated': False, 'reason': 'explicit pause', **inherited, **context}
        report['last_phase'] = next_phase
    else:
        report['finished_at'] = datetime.fromtimestamp(now, timezone.utc).isoformat()
        report['ended_at'] = now
    report['updated_at'] = datetime.fromtimestamp(now, timezone.utc).isoformat()
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(report, indent=2), encoding='utf-8')
    temporary.replace(path)
    return report


def workflow_events(root):
    path = Path(root) / 'workflow-events.jsonl'
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue  # A interrupted event write is not a measured tool interval.
    return events


def summary(report, tool_events=()):
    rows = list(report['intervals'])
    # Open intervals are excluded; the displayed stop is the latest recorded activity.
    boundaries = [r['end'] for r in rows]
    boundaries += [r.get('last_activity', r['start']) for r in (report.get('active'), report.get('paused')) if r]
    start = report.get('started_at', rows[0]['start'] if rows else min(boundaries, default=0))
    end = report.get('ended_at', max(boundaries, default=start))
    elapsed = end - start
    # Expose only the observed portion of an open interval, never time.time().
    opened = report.get('active')
    if opened and opened.get('last_activity', opened['start']) > opened['start']:
        rows.append({**opened, 'end': opened['last_activity']})
    duration = lambda r: r['end'] - r['start']
    waiting = sum(duration(r) for r in rows if r.get('state') == 'waiting')
    active = sum(duration(r) for r in rows if r.get('state') == 'active')
    unknown = max(0, elapsed - active - waiting)
    windows = []
    for event in tool_events:
        if not isinstance(event, dict):
            continue
        a, seconds = event.get('started_at'), event.get('elapsed_seconds')
        if finite(a) and finite(seconds) and seconds >= 0:
            b, a = min(end, a + seconds), max(start, a)
            if b > a:
                windows.append((a, b))
    tool_seconds, last = 0, start
    for a, b in sorted(windows):
        tool_seconds += max(0, b - max(a, last))
        last = max(last, b)
    closed = not report.get('active') and not report.get('paused')
    return {'wall_seconds': elapsed, 'target_seconds': 1200,
            'target_met': closed and elapsed <= 1200, 'target_basis': 'inclusive wall time',
            'agent_active_seconds': active if not unknown else None,
            'activity_basis': 'estimated from phase boundaries and activity heartbeats; not CPU or thinking time',
            'waiting_seconds': waiting,
            'estimated_waiting_seconds': sum(duration(r) for r in rows if r.get('state') == 'waiting' and r.get('estimated')),
            'unclassified_seconds': unknown,
            'tool_seconds': tool_seconds if windows else None,
            'tool_coverage': 'recorded workflow commands only; overlapping intervals counted once',
            'phase_seconds': {p: sum(duration(r) for r in rows if r['phase'] == p and r.get('state') != 'waiting')
                              for p in sorted(PHASES)}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('paper_id')
    parser.add_argument('action', choices=('phase', 'finish', 'pause', 'idle', 'resume', 'touch'))
    parser.add_argument('phase', nargs='?', choices=sorted(PHASES))
    parser.add_argument('--question-ids', nargs='*')
    parser.add_argument('--page-numbers', nargs='*', type=int)
    parser.add_argument('--revision-id')
    parser.add_argument('--idle-seconds', type=float, default=IDLE_SECONDS)
    args = vars(parser.parse_args())
    path = args.pop('path')
    report = transition(path, **args)
    print(json.dumps(summary(report, workflow_events(path.parent)), indent=2))
