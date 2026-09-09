#!/usr/bin/env python3
"""Prepare a NEW sanitized Git checkout candidate; never commit or publish it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_TESTS = set('''
test_attribution.py test_audit_corpus_overlap.py test_exam_pack_contract.py
test_failed_stress_suite.py test_paper_difficulty_balance.py test_pdf_provenance.py
test_release_contract.py test_skill.py test_validate_english_layout_contract.py
test_validate_english_vocabulary_scope.py test_validate_social_item_design.py
test_validate_writing_source_grounding.py test_public_export.py
'''.split())


def export(destination: Path, version: str, *, internal_review: bool = False) -> dict:
    # Refuse reuse: no deletion, overwrites, merges into private data, or implicit
    # git mutations. Review the resulting tree before any authorized push.
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Destination must be a new, nonexistent directory')
    with tempfile.TemporaryDirectory(prefix='taiwan-exam-export-') as temp:
        archive = Path(temp) / 'taiwan-exam-generator.zip'
        command = [sys.executable, str(ROOT / 'scripts/package_skill.py'),
                   '--version', version, '--output', str(archive)]
        if not internal_review:
            command.append('--public-release')
        completed = subprocess.run(command, capture_output=True, encoding='utf-8', errors='replace')
        if completed.returncode:
            raise ValueError('Packaging checks failed: ' + completed.stdout + completed.stderr)
        with ZipFile(archive) as zipped:
            records = []
            for member in zipped.infolist():
                rel = PurePosixPath(member.filename)
                if rel.is_absolute() or '..' in rel.parts or '\\' in member.filename:
                    raise ValueError('Unsafe archive member')
                if len(rel.parts) < 2 or rel.parts[0] != 'taiwan-exam-generator':
                    raise ValueError('Unexpected Skill archive root')
                records.append((member, Path(*rel.parts[1:])))
            destination.mkdir(parents=True, exist_ok=False)
            for member, rel in records:
                target = destination / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zipped.read(member))
        test_count = 0
        for name in sorted(PUBLIC_TESTS):
            source = ROOT / 'tests' / name
            if source.is_file():
                target = destination / 'tests' / name
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(source, target)
                test_count += 1
        (destination / 'downloads').mkdir()
        shutil.copyfile(archive, destination / 'downloads/taiwan-exam-generator.zip')
    return dict(destination=str(destination), public_test_files=test_count,
                status='internal-review' if internal_review else 'publication-candidate',
                published=False, exam_acceptance=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--version', default='0.6.0-preview.1')
    parser.add_argument('--internal-review', action='store_true',
                        help='Prepare locally with pending declarations; NOT public-release approval')
    args = parser.parse_args()
    try:
        result = export(args.output, args.version, internal_review=args.internal_review)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
