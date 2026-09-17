#!/usr/bin/env python3
"""Build an unpublished multi-file hosted Skill candidate; never scan or publish it.

The short native SKILL.md is an entry point. Portable helpers and canonical
references are ordinary separate files, not a megabyte-sized instruction body.
Publication requires the existing exact-archive security and browser workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from build_web_knowledge import ROOT, source_paths
from validate_attribution import validate as validate_attribution


ENTRY = """---
name: taiwan-exam-generator
description: Create original Taiwan GSAT/CAP exams with separate question and solution PDFs, fixed templates, answer checks, difficulty, originality and visual QA. Use for Taiwan exam generation.
---

# Taiwan Exam Generator

Native hosted Skill, version {version}.

Start with [references/hosted-execution.md](references/hosted-execution.md).
This multi-file Skill already contains its executable `scripts/`, subject
references, schemas, and template maps. First use the reader's `--source-dir`
route in hosted-execution.md to materialize the selected subject into a writable
reference directory; run all subsequent helpers from that directory. ZIP member
names use ASCII; PACKAGE_MANIFEST.json maps them to original runtime paths without
changing file contents. Do not manually rename folders. Do not extract
or reconstruct the large web-knowledge Markdown, download the repository, or
reinstall this Skill for an ordinary paper request. Run helpers without printing
their source. Read the requested subject's guidance at the phase that uses it.

Write new questions and solutions for this run. Subject layout examples contain
placeholders only; reuse their layout conventions, never their question content
or diagram mechanisms. Use the user's uploaded resource PDF for original fixed
template attachments. Without it, the provided preflight has bounded retrieval.
Keep original fixed PDF layers, curriculum and score structure, difficulty and
originality requirements, answer verification, and real page/item visual review.
An unavailable second model uses the documented honest same-context second pass;
never invent an independent reviewer or passing observation.

Create one paper ID and run directory. On continuation, verify and resume saved
work and its first unfinished action. Reuse unchanged verified inputs and actual
reviews; do not restart authoring or repeat completed setup merely for a new turn.
Project body specs from saved items with `run_hosted_workflow.py specs`, review
each batch's item crops with `proof`, and record findings with `record-review`.
Deliver separate question and full-solution PDFs only after the final checks.
If incomplete, save actual recoverable work and name what remains.

The full source manual is preserved in
[references/full-skill.md](references/full-skill.md) for applicable detailed rules;
its original relative paths are rooted at this Skill directory. It is not an
initial reading requirement. The hosted execution route controls hosted
scheduling; local repository maintenance and source rebuilding are separate.
Preserve LICENSE, NOTICE, ORIGIN.json and attribution records when packaging.
"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_member(zipped, path, data):
    validate_member_path(path)
    info = ZipInfo('taiwan-exam-generator/' + path, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    zipped.writestr(info, data, compresslevel=9)


def validate_member_path(path):
    """Our conservative upload-compatible path policy, not vendor certification."""
    if (not re.fullmatch(r'[A-Za-z0-9_./-]+', path)
            or any(part in {'', '.', '..'} for part in path.split('/'))):
        raise ValueError('Non-portable hosted archive path: ' + path)


def archive_path(runtime_path):
    # Preserve the original bytes and internal references. Only the transport
    # filename changes; the reader restores the original path in the run folder.
    if re.fullmatch(r'[A-Za-z0-9_./-]+', runtime_path):
        validate_member_path(runtime_path)
        return runtime_path
    suffix = Path(runtime_path).suffix
    target = 'resources/canonical/' + sha(runtime_path.encode('utf-8')) + suffix
    validate_member_path(target)
    return target


def build(version, output, *, root=ROOT):
    if not isinstance(version, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}', version):
        raise ValueError('Use a short version identifier without whitespace or path separators')
    root = root.resolve()
    output = output.resolve()
    if output.suffix.lower() != '.zip' or output.exists():
        raise ValueError('Choose a new .zip candidate path; never overwrite a scanned archive')
    attribution = validate_attribution(root)
    if attribution['status'] != 'pass':
        raise ValueError('Attribution validation failed: ' + '; '.join(attribution['errors']))
    selected = {p.relative_to(root).as_posix(): p for p in source_paths(root)}
    for relative in ('LICENSE', 'NOTICE', 'ORIGIN.json', 'AGENTS.md',
                     'references/attribution-and-forks.md', 'references/hosted-execution.md'):
        selected[relative] = root / relative
    members = {'SKILL.md': ENTRY.format(version=version).encode('utf-8')}
    records = [{'path': 'SKILL.md', 'bytes': len(members['SKILL.md']),
                'sha256': sha(members['SKILL.md']), 'source': 'generated-native-entry'}]
    for relative, path in sorted(selected.items()):
        if not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError('Missing or external canonical file: ' + relative)
        if path.suffix and path.suffix not in {'.md', '.py', '.json', '.svg', '.csv'}:
            raise ValueError('Unreviewed hosted archive file type: ' + relative)
        if path.name == 'writer-calibration-additions.json':
            from writer_calibration import load_writer
            load_writer(path.parent.parent)
        runtime_path = 'references/full-skill.md' if relative == 'SKILL.md' else relative
        target = archive_path(runtime_path)
        if target in members:
            raise ValueError('Duplicate hosted archive target: ' + target)
        data = path.read_bytes()
        members[target] = data
        records.append({'path': target, 'runtime_path': runtime_path,
                        'bytes': len(data), 'sha256': sha(data),
                        'source': relative, 'source_sha256': sha(data)})
    if len({p.casefold() for p in members}) != len(members):
        raise ValueError('Case-colliding hosted archive paths')
    manifest = {'schema_version': 2, 'name': 'taiwan-exam-generator', 'version': version,
                'distribution_status': 'internal-review-not-published',
                'format': 'native-multi-file-hosted-skill', 'origin': attribution['origin'],
                'archive_path_policy': 'ascii-letters-digits-dot-underscore-hyphen-slash',
                'claude_upload_acceptance': 'not-performed-by-builder',
                'attribution_check': {k: attribution[k] for k in ('status', 'scope', 'notice_sha256', 'warnings')},
                'security_acceptance': 'not-performed-by-builder',
                'browser_acceptance': 'not-performed-by-builder',
                'exam_acceptance': 'not-established-by-packager', 'contains_original_exam_files': False,
                'file_count': len(records), 'files': sorted(records, key=lambda row: row['path'])}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.zip.partial')
    if temporary.exists():
        raise ValueError('Preserve existing partial candidate; select another output path')
    with ZipFile(temporary, 'w', compression=ZIP_DEFLATED, compresslevel=9) as zipped:
        for relative, data in sorted(members.items()):
            write_member(zipped, relative, data)
        write_member(zipped, 'PACKAGE_MANIFEST.json',
                     (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    temporary.replace(output)
    return {'archive': str(output), 'version': version, 'sha256': sha(output.read_bytes()),
            'bytes': output.stat().st_size, 'file_count': len(records),
            'entry_bytes': len(members['SKILL.md']), 'distribution_status': manifest['distribution_status'],
            'security_acceptance': manifest['security_acceptance'],
            'next_action': 'Run the existing exact-archive security and normal-browser acceptance workflow before publishing.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.version, args.output), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
