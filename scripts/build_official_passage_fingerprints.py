#!/usr/bin/env python3
"""Maintainer build: hashed fingerprints of the official ROC 111–115 國綜 booklets.

A hosted 116 國綜 paper reprinted 114's 30–31 passage (〈晚遊六橋待月記〉, same segment and
item position); nothing on the hosted side could see it. The file stores no official text:
only a 10-hex SHA-1 prefix of every 30-ideograph window that starts at a multiple of 10 in
each booklet's CJK-ideograph stream. Any copied stretch of 39 or more ideographs contains
one such window, so `validate_chinese_layout_contract.py` hashes every 30-ideograph window of
a candidate's material and prompts and reports the official year it matches.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path
import re

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exam_packs' / '學測' / 'shared-data' / 'official-passage-fingerprints.json'
WINDOW, STEP = 30, 10
IDEOGRAPH = re.compile('[㐀-鿿]')


def ideographs(text: str) -> str:
    return ''.join(IDEOGRAPH.findall(text))


def window_hash(window: str) -> str:
    return hashlib.sha1(window.encode('utf-8')).hexdigest()[:10]


def booklet(year: int) -> Path:
    folder = ROOT / 'exam_packs' / '學測' / 'subjects' / '國文' / '歷屆試題' / str(year)
    return next(Path(p) for p in sorted(glob.glob(str(folder / '*.pdf')))
                if '國綜' in Path(p).name and ('試卷' in Path(p).name or '試題' in Path(p).name))


def build() -> dict:
    years = {}
    for year in range(111, 116):
        with pymupdf.open(booklet(year)) as document:
            stream = ideographs(''.join(page.get_text() for page in document))
        years[str(year)] = sorted({window_hash(stream[i:i + WINDOW]) for i in range(0, len(stream) - WINDOW + 1, STEP)})
    return {'kind': 'official-passage-fingerprints', 'subject': '國綜', 'window': WINDOW, 'step': STEP,
            'hash': 'sha1-hex10 of 30 consecutive CJK ideographs', 'years': years,
            'note': 'No official text is stored; a candidate window hash that matches means a copied stretch.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    data = build()
    args.output.write_bytes((json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
    print(json.dumps({'output': str(args.output), 'windows': {y: len(v) for y, v in data['years'].items()}}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
