#!/usr/bin/env python3
"""Make a figure file byte-reproducible so an unchanged drawing keeps its sha256.

Plotting libraries stamp each export with the current time (SVG ``<dc:date>``,
PDF ``/CreationDate``), a random document ID and randomly salted element ids.
Re-running an unchanged figure script therefore changes every hash, which
invalidates the saved item, its reviews and the content lock for no printed
change. This helper removes only that non-printing noise: SVG metadata blocks
and id salt, PDF info dictionary dates/producer and the trailer ID. Paths,
glyphs, images and page geometry are untouched, so the printed figure is the
same. It never creates, scales or repairs artwork.

    python scripts/normalize_figure_asset.py run/fig-12.svg run/fig-16.pdf

Each file is rewritten in place (``--output DIR`` writes copies instead) and
its final sha256 is printed for the item record. Draw each figure with its own
script so a repair redraws one file; do not regenerate a whole batch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

SVG_METADATA = re.compile(r'\s*<metadata\b.*?</metadata>', re.S)
SVG_DATE = re.compile(r'\s*<dc:date>[^<]*</dc:date>')
SVG_ID = re.compile(r'\bid="([^"]+)"')
PDF_ID = re.compile(rb'/ID *\[ *<([0-9A-Fa-f]+)> *<([0-9A-Fa-f]+)> *\]')


def normalize_svg(text: str) -> str:
    """Drop export metadata and rename ids in first-appearance order."""
    text = SVG_DATE.sub('', SVG_METADATA.sub('', text))
    names = {}
    for match in SVG_ID.finditer(text):
        names.setdefault(match.group(1), f'n{len(names) + 1}')
    # Longest first so an id that prefixes another is never partially rewritten.
    for old in sorted(names, key=len, reverse=True):
        new = names[old]
        escaped = re.escape(old)
        text = re.sub(rf'\bid="{escaped}"', f'id="{new}"', text)
        text = re.sub(rf'#{escaped}(?=["\s)])', f'#{new}', text)
    return text


def normalize_pdf(data: bytes) -> bytes:
    """Blank the info dictionary dates/producer and fix the trailer ID."""
    import pymupdf

    with pymupdf.open(stream=data, filetype='pdf') as document:
        if not document.is_pdf:
            raise ValueError('Not a PDF figure')
        document.set_metadata({'creationDate': '', 'modDate': '', 'producer': '', 'creator': ''})
        rewritten = document.tobytes(garbage=4, deflate=True)
    # Same-length zero IDs keep every byte offset valid; /ID is optional for
    # an unencrypted file, so readers accept a constant value.
    return PDF_ID.sub(lambda m: b'/ID[<' + b'0' * len(m.group(1)) + b'><' + b'0' * len(m.group(2)) + b'>]',
                      rewritten)


def normalize(path: Path, output: Path | None = None) -> dict:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == '.svg':
        result = normalize_svg(path.read_text(encoding='utf-8')).encode('utf-8')
    elif suffix == '.pdf':
        result = normalize_pdf(path.read_bytes())
    else:
        raise ValueError('Normalize SVG or single-page PDF figures only: ' + path.name)
    target = (Path(output) / path.name) if output else path
    changed = not target.exists() or target.read_bytes() != result
    if changed:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result)
    return {'path': str(target), 'sha256': hashlib.sha256(result).hexdigest(),
            'bytes': len(result), 'changed': changed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('figures', nargs='+', type=Path)
    parser.add_argument('--output', type=Path, help='Write normalized copies into this directory')
    args = parser.parse_args()
    try:
        rows = [normalize(figure, args.output) for figure in args.figures]
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({'status': 'pending', 'errors': [str(exc)]}, ensure_ascii=False))
        return 2
    print(json.dumps({'status': 'normalized', 'figures': rows,
                      'note': 'Record each sha256 in the item; a redrawn unchanged figure now keeps it.'},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
