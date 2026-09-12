#!/usr/bin/env python3
"""Maintainer-only: measure verified source PDFs; publish numbers, never PDF text."""
import argparse
import hashlib
import json
from pathlib import Path

import pymupdf
from hosted_calibration import ROOT, SOURCE_PATH, METRICS_PATH, algorithm_hash
from inspect_hosted_pdf import bottom_void


def build(source_root):
    source_map = json.loads((ROOT / SOURCE_PATH).read_text(encoding='utf-8'))
    pages = []
    for subject in source_map['subjects']:
        year = max(subject['years'], key=lambda y: y['roc_year'])
        for kind in ('question', 'scoring_rule'):
            record = year['documents'][kind]
            data = (source_root / record['local_path']).read_bytes()
            if (not data.startswith(b'%PDF') or len(data) != record['bytes'] or
                    hashlib.sha256(data).hexdigest() != record['sha256']):
                raise ValueError(f"Unverified source: {subject['subject']}/{kind}")
            with pymupdf.open(stream=data, filetype='pdf') as doc:
                if len(doc) != record['pages']:
                    raise ValueError('Source page count mismatch')
                for index, page in enumerate(doc):
                    role = 'solutions' if kind == 'scoring_rule' else 'cover' if index == 0 else 'body'
                    if kind == 'question' and subject['subject'] in {'數學A', '數學B'} and index == len(doc)-1:
                        if '參考公式' not in ''.join(page.get_text().split()):
                            raise ValueError('Expected formula page is not identifiable')
                        role = 'formula'
                    pages.append({'subject': subject['subject'], 'roc_year': year['roc_year'],
                                  'source_sha256': record['sha256'], 'document_role': kind,
                                  'page': index+1, 'page_role': role, 'bottom_void': bottom_void(page)})
    return {'schema_version': 1, 'algorithm_sha256': algorithm_hash(),
            'scope': 'Numeric bottom-void measurements, not page images or a visual approval. '
                     'Scoring-rule pages are rubric references, not full worked solutions.', 'pages': pages}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / METRICS_PATH)
    args = parser.parse_args()
    result = build(args.source_root)
    args.output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode())
    print(f"Measured {len(result['pages'])} verified source pages")
