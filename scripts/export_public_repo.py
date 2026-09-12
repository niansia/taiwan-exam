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
# Source-checkout tooling, never part of the end-user Skill archive. Keep this
# explicit so ZIP minimization cannot silently remove publication/CI safeguards.
MAINTAINER_FILES = (
    'scripts/package_skill.py',
    'scripts/build_source_release.py',
    'scripts/build_hosted_web_source_map.py',
    'scripts/build_hosted_web_template_map.py',
    'scripts/build_web_knowledge.py',
    'scripts/build_template_resource_pdf.py',
    'web/taiwan-exam-web-knowledge.md',
    'web/taiwan-exam-template-resources.pdf',
    'scripts/export_public_repo.py',
    'scripts/scan_skill_release.py',
    'maintenance/test_download_attachment.ps1',
    '.github/workflows/distribution-security.yml',
    '.github/workflows/tests.yml',
    'requirements-test.txt',
    'SOFTWARE_RELEASE_STATUS.json',
    'references/rendering-security-review.md',
    'references/security-incident-2026-09-09.md',
    'references/security-resolution-2026-09-11.md',
    'references/security-resolution-2026-09-12.md',
    'maintenance/security-scan-2026-09-12.json',
    'references/software-release-security.md',
    'docs/production-readiness-2026-09-12.md',
)
PUBLIC_TESTS = set('''
test_attribution.py test_audit_corpus_overlap.py test_build_official_question_queue.py
test_density_content_volume.py test_exam_pack_contract.py test_failed_stress_suite.py
test_gsat_115_templates.py test_math_b_content_distribution.py
test_math_scope_polysemy.py test_measured_math_renderer.py
test_natural_reasoning_and_blocks.py test_optional_statistics_dependency.py
test_paper_difficulty_balance.py test_pdf_provenance.py test_public_export.py
test_release_contract.py test_safe_rendering.py test_scan_skill_release.py
test_source_bootstrap.py test_production_readiness.py test_writer_calibration.py
test_skill.py test_validate_english_difficulty_design.py
test_validate_english_layout_contract.py test_validate_english_vocabulary_scope.py
test_validate_social_item_design.py test_validate_source_grounding.py
test_validate_visual_item_contract.py test_validate_writing_source_grounding.py
test_web_knowledge.py test_web_download_page.py test_hosted_pdf_runtime.py
'''.split())


def copy_maintainer_files(destination: Path) -> None:
    for relative in MAINTAINER_FILES:
        source = ROOT / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError('Required maintainer tool missing or symlinked: ' + relative)
    for relative in MAINTAINER_FILES:
        target = destination / relative
        if target.exists() or target.is_symlink():
            raise ValueError('Maintainer export must not overwrite: ' + relative)
    for relative in MAINTAINER_FILES:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


def export(destination: Path, version: str, *, internal_review: bool = False, source_url: str | None = None) -> dict:
    # Refuse reuse: no deletion, overwrites, merges into private data, or implicit
    # git mutations. Review the resulting tree before any authorized push.
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('Destination must be a new, nonexistent directory')
    if not internal_review:
        from scan_skill_release import validate_source_url
        validate_source_url(source_url)
    with tempfile.TemporaryDirectory(prefix='taiwan-exam-export-') as temp:
        archive = Path(temp) / 'taiwan-exam-generator.zip'
        command = [sys.executable, str(ROOT / 'scripts/package_skill.py'),
                   '--version', version, '--output', str(archive)]
        if not internal_review:
            command.extend(['--public-release', '--source-url', source_url])
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
        # The source repository never carries an install ZIP. Distribution is
        # a separately reviewed Release asset; a suspended export must remain
        # suspended and retain the policy that enforces that boundary.
        if not internal_review:
            (destination / 'downloads').mkdir()
            shutil.copyfile(archive.with_suffix('.security.json'), destination / 'downloads/security-scan.json')
        copy_maintainer_files(destination)
    return dict(destination=str(destination), public_test_files=test_count,
                status='internal-review' if internal_review else 'publication-candidate',
                published=False, exam_acceptance=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--version', default='0.7.0')
    parser.add_argument('--source-url', help='Actual stable public HTTPS download URL; required unless internal-review')
    parser.add_argument('--internal-review', action='store_true',
                        help='Prepare locally with pending declarations; NOT public-release approval')
    args = parser.parse_args()
    try:
        result = export(args.output, args.version, internal_review=args.internal_review, source_url=args.source_url)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
