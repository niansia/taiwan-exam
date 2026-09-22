#!/usr/bin/env python3
"""Transport bundles: many small text sources travel as a few JSON members.

Claude's Skill uploader accepts at most 200 files in one ZIP; it rejected the
2026.09.22.3 archive (222 members) with "Zip contains too many files". The
Python helpers, the entry, the licence files, the first reference and the fixed
template PDFs stay separate members. Every other text source (references,
schemas, layout templates, exam-pack data) travels inside
`resources/bundles/*.json` as {archive path: exact UTF-8 text}.

The reader (`read_web_knowledge.py --source-dir`) and the release scanner
expand a bundle back to its files and verify every file against the package
manifest, so the run directory, the helpers and the security scan see the
original files. A bundle is transport only; it changes no bytes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re

BUNDLE_DIR = 'resources/bundles/'
BUNDLE_KIND = 'hosted-text-bundle'
BUNDLE_FORMAT = 1
# The uploader's limit, counted over every member of the ZIP.
MAX_MEMBERS = 200
LOOSE_FILES = {'SKILL.md', 'LICENSE', 'NOTICE', 'ORIGIN.json', 'AGENTS.md',
               'references/hosted-execution.md', 'PACKAGE_MANIFEST.json'}
LOOSE_PREFIXES = ('scripts/',)
TEXT_SUFFIXES = {'.md', '.json', '.svg', '.csv', '.txt', '.yaml', '.yml'}
SAFE_PATH = re.compile(r'[A-Za-z0-9_./-]+')


def safe_path(path):
    return (isinstance(path, str) and bool(SAFE_PATH.fullmatch(path))
            and not any(part in {'', '.', '..'} for part in path.split('/')))


def bundle_for(path):
    """The bundle a member travels in, or None when it stays a separate file."""
    if path in LOOSE_FILES or path.startswith(LOOSE_PREFIXES):
        return None
    if PurePosixPath(path).suffix not in TEXT_SUFFIXES:
        return None
    return BUNDLE_DIR + ('references.json' if path.endswith('.md') else 'data.json')


def pack(members):
    """Split {path: bytes} into loose members, bundle members and each bundled path's bundle."""
    loose, groups, placement = {}, {}, {}
    for path, data in members.items():
        target = bundle_for(path)
        if target is None:
            loose[path] = data
            continue
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError(f'Bundled text member is not UTF-8: {path}: {exc}') from None
        if text.encode('utf-8') != data:
            raise ValueError('Bundled text member does not round-trip through UTF-8: ' + path)
        groups.setdefault(target, {})[path] = text
        placement[path] = target
    bundles = {}
    for target, files in sorted(groups.items()):
        payload = {'kind': BUNDLE_KIND, 'format': BUNDLE_FORMAT, 'file_count': len(files),
                   'files': dict(sorted(files.items()))}
        bundles[target] = (json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + '\n').encode('utf-8')
    return loose, bundles, placement


def parse(data):
    """{path: text} from bundle bytes, refusing anything but the documented shape."""
    try:
        payload = json.loads(data.decode('utf-8'))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f'Bundle is not valid UTF-8 JSON: {exc}') from None
    if (not isinstance(payload, dict) or payload.get('kind') != BUNDLE_KIND
            or payload.get('format') != BUNDLE_FORMAT or not isinstance(payload.get('files'), dict)):
        raise ValueError('Unexpected bundle shape')
    files = payload['files']
    if payload.get('file_count') != len(files):
        raise ValueError('Bundle file count disagrees with its contents')
    for path, text in files.items():
        if not safe_path(path) or bundle_for(path) is None or not isinstance(text, str):
            raise ValueError('Unsafe or misplaced bundled path: ' + str(path))
    return files


def bundle_records(bundles):
    """Manifest entries for the bundle members themselves."""
    return {path: {'kind': BUNDLE_KIND, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                   'file_count': len(parse(data))}
            for path, data in sorted(bundles.items())}


def expand(files, manifest):
    """Replace bundle members in {path: bytes} by the files they carry, verifying the manifest's digests."""
    declared = manifest.get('bundles') or {}
    if not isinstance(declared, dict):
        raise ValueError('Manifest bundles must be an object')
    expanded = dict(files)
    for bundle_path, record in declared.items():
        if not safe_path(bundle_path) or not bundle_path.startswith(BUNDLE_DIR):
            raise ValueError('Unsafe bundle path: ' + str(bundle_path))
        data = expanded.pop(bundle_path, None)
        if data is None:
            raise ValueError('Missing bundle member: ' + bundle_path)
        if (not isinstance(record, dict) or len(data) != record.get('bytes')
                or hashlib.sha256(data).hexdigest() != record.get('sha256')):
            raise ValueError('Bundle digest mismatch: ' + bundle_path)
        for path, text in parse(data).items():
            if path in expanded:
                raise ValueError('Bundled file collides with a separate member: ' + path)
            expanded[path] = text.encode('utf-8')
    stray = sorted(path for path in expanded if path.startswith(BUNDLE_DIR))
    if stray:
        raise ValueError('Undeclared bundle member: ' + ', '.join(stray))
    return expanded
