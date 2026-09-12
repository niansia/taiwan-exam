#!/usr/bin/env python3
"""Persist actual phase transitions; time targets never waive QA.

Usage: hosted_run_timing.py generation-timing.json PAPER_ID phase PHASE
       hosted_run_timing.py generation-timing.json PAPER_ID finish
Switching phase closes the previous interval. Repeat phases for repairs. Gaps
and interruptions remain wall time, not falsely reported as active CPU time.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time

PHASES = {'reference_preflight', 'authoring', 'solving', 'render_repair', 'visual_qa', 'difficulty_qa'}


def timing_errors(report, paper_id):
    errors = []
    rows = report.get('intervals', [])
    if report.get('paper_id') != paper_id or report.get('active') is not None:
        errors.append('timing: wrong paper or unfinished interval')
    if {r.get('phase') for r in rows} != PHASES:
        errors.append('timing: all six measured phases required')
    previous = None
    for row in rows:
        start, end = row.get('start'), row.get('end')
        if not all(type(v) in (int,float) and math.isfinite(v) for v in (start,end)):
            errors.append('timing: invalid clock reading')
            continue
        if end <= start or (previous is not None and start < previous):
            errors.append('timing: reversed or overlapping intervals')
        previous = end
    if not rows:
        errors.append('timing: no measured intervals')
    return errors


def transition(path, paper_id, phase=None):
    now = time.time()
    report = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
        'paper_id': paper_id, 'intervals': [], 'active': None}
    if report['paper_id'] != paper_id:
        raise ValueError('Refusing to mix paper clocks')
    if report.get('finished_at'):
        report.pop('finished_at')  # A later repair reopens the SAME measured run.
    if report['active']:
        active = report['active']
        if now <= active['start']:
            raise ValueError('Clock moved backwards; retain log and investigate')
        report['intervals'].append({**active, 'end': now})
    report['active'] = {'phase': phase, 'start': now} if phase else None
    if phase is None:
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
    report['updated_at'] = datetime.now(timezone.utc).isoformat()
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(report, indent=2), encoding='utf-8')
    temporary.replace(path)
    return report


def summary(report):
    rows = report['intervals']
    elapsed = rows[-1]['end'] - rows[0]['start'] if rows else 0
    return {'wall_seconds': elapsed, 'target_seconds': 1200, 'target_met': elapsed <= 1200,
            'phase_seconds': {phase: sum(r['end']-r['start'] for r in rows if r['phase']==phase)
                              for phase in sorted(PHASES)}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('paper_id')
    parser.add_argument('action', choices=('phase','finish'))
    parser.add_argument('phase', nargs='?', choices=sorted(PHASES))
    args = parser.parse_args()
    if (args.action == 'phase') != (args.phase is not None):
        parser.error('phase requires a phase name; finish takes none')
    report = transition(args.path, args.paper_id, args.phase)
    print(json.dumps(summary(report), indent=2))
