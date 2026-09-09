"""Find within/across-paper repeated stems after number normalization.

This is triage, never a semantic originality approval. Shared generic prompts
may be legitimate; compare stimuli, solution graphs and options in review.
"""
import argparse
import json
import re
import hashlib
from collections import defaultdict
from pathlib import Path


def audit(paths):
    groups = defaultdict(list); inputs = []
    for path in paths:
        raw = path.read_bytes(); exam = json.loads(raw.decode('utf-8-sig'))
        inputs.append({'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()})
        meta = exam.get('metadata') or {}
        subject = meta.get('paper_subject') or meta.get('subject')
        for q in exam.get('questions', []):
            prompt = re.sub(r'\s+', '', q.get('prompt') or '')
            if len(prompt) < 16:  # Short shared question labels are not useful lexical evidence.
                continue
            normalized = re.sub(r'\d+(?:\.\d+)?', '#', prompt)
            groups[(subject, normalized)].append({'exam': str(path), 'question_id': q.get('id'),
                'number': q.get('number'), 'group_id': q.get('group_id')})
    collisions = [{'subject': key[0], 'normalized_stem': key[1], 'items': rows}
                  for key, rows in groups.items() if len(rows) > 1]
    return {'status': 'needs-review' if collisions else 'no-lexical-flags', 'inputs': inputs,
            'collisions': collisions, 'semantic_originality': 'not-verified',
            'note': 'Adjudicate collisions and low-lexical structural neighbors; zero hits is not approval.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('exams', type=Path, nargs='+'); ap.add_argument('--output', type=Path)
    a = ap.parse_args(); r = audit(a.exams)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(r, ensure_ascii=False)); return int(bool(r['collisions']))


if __name__ == '__main__':raise SystemExit(main())
