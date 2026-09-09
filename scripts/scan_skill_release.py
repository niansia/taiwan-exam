#!/usr/bin/env python3
"""Hash-bound Windows Defender check of a Skill ZIP and its extracted members.

No execution of archive contents, security-setting changes or third-party upload.
Attachment Services may quarantine its disposable copy. Existing Defender cloud
policy remains unchanged. Passing is not vendor clearance or browser acceptance.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
from zipfile import ZipFile

RETIRED = {'scripts/paginate_chinese_natural.js', 'scripts/render_chinese_natural_proof.py',
           'scripts/qa_gsat_internal_layout.js'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_archive(archive, destination):
    """Validate exact manifest coverage and safe paths before extracting data."""
    with ZipFile(archive) as zipped:
        members = zipped.infolist()
        names = [member.filename for member in members]
        if len(names) != len(set(name.casefold() for name in names)):
            raise ValueError('Duplicate or case-colliding archive members')
        if sum(member.file_size for member in members) > 100_000_000:
            raise ValueError('Skill archive exceeds 100 MB unpacked review limit')
        files = {}
        for member in members:
            path = PurePosixPath(member.filename)
            if (path.is_absolute() or '..' in path.parts or '\\' in member.filename
                    or ':' in member.filename or len(path.parts) < 2
                    or path.parts[0] != 'taiwan-exam-generator' or member.is_dir()
                    or ((member.external_attr >> 16) & 0o170000) == 0o120000):
                raise ValueError('Unsafe or unexpected archive member')
            rel = '/'.join(path.parts[1:])
            if rel in RETIRED:
                raise ValueError('Retired proof tool must not be distributed')
            files[rel] = zipped.read(member)
        manifest = json.loads(files.pop('PACKAGE_MANIFEST.json'))
        records = manifest['files']
        if len(records) != len(files) or {row['path'] for row in records} != set(files):
            raise ValueError('Manifest coverage mismatch')
        for row in records:
            data = files[row['path']]
            if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError('Manifest digest mismatch')
        for rel, data in files.items():
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (destination / 'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest), encoding='utf-8')
        return {str(path.relative_to(destination)): digest(path)
                for path in destination.rglob('*') if path.is_file()}


def windows_powershell_env():
    # Python inherits PS7's module paths, unlike a direct powershell.exe launch.
    # Reset only the child's module discovery, never device/security settings.
    return {key: value for key, value in os.environ.items() if key.upper() != 'PSMODULEPATH'}


def defender_status():
    if os.name != 'nt':
        raise RuntimeError('Publication scanner requires Windows Defender; no unchecked fallback')
    command = ('Get-MpComputerStatus | Select-Object AMEngineVersion,AMProductVersion,'
               'AntivirusSignatureVersion,AntivirusSignatureAge,AntivirusEnabled,'
               'RealTimeProtectionEnabled | ConvertTo-Json -Compress')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', command],
                            capture_output=True, text=True, timeout=60, check=True, env=windows_powershell_env())
    status = json.loads(result.stdout)
    if not status['AntivirusEnabled'] or not status['RealTimeProtectionEnabled']:
        raise RuntimeError('Defender must be enabled; scanner does not change its settings')
    if status['AntivirusSignatureAge'] > 1:
        raise RuntimeError('Update Defender security intelligence before publishing')
    return status


def defender_scan(path):
    platform = Path(os.environ['ProgramData']) / 'Microsoft/Windows Defender/Platform'
    scanners = list(platform.glob('*/MpCmdRun.exe'))
    if not scanners:
        raise RuntimeError('Defender command-line scanner unavailable')
    scanner = max(scanners, key=lambda item: tuple(int(n) for n in item.parent.name.replace('-', '.').split('.')))
    # This custom-scan flag scans archives and ignores file exclusions, while
    # disabling remediation for THIS scan only. Real-time protection stays on.
    result = subprocess.run([str(scanner), '-Scan', '-ScanType', '3', '-File', str(path),
                             '-DisableRemediation'], capture_output=True, text=True,
                            errors='replace', timeout=600)
    output = (result.stdout + result.stderr).replace(str(path), '<scan-target>')
    # Scanner console encoding may corrupt non-ASCII paths before replacement.
    output = re.sub(r'(?im)^Scanning .*?( found no threats\.)$', r'Scanning <scan-target>\1', output)
    return {'returncode': result.returncode, 'output': output}


def attachment_scan(archive):
    checker = Path(__file__).resolve().parents[1] / 'maintenance/test_download_attachment.ps1'
    if not checker.is_file():
        raise RuntimeError('Maintainer attachment checker is required for publication')
    command = ['powershell.exe', '-NoProfile', '-NonInteractive', '-File', str(checker),
               '-Archive', str(archive), '-SourceUrl',
               'https://raw.githubusercontent.com/niansia/taiwan-exam/refs/heads/main/downloads/taiwan-exam-generator.zip']
    result = subprocess.run(command, capture_output=True, text=True, errors='replace', timeout=180,
                            env=windows_powershell_env())
    try:
        raw = json.loads(result.stdout)
    except (ValueError, TypeError):
        return {'status': 'fail', 'returncode': result.returncode, 'error': 'Attachment checker produced no valid JSON'}
    # Retain diagnostic codes, not arbitrary stderr or device paths. A checker
    # failure must not be mislabeled as an antivirus detection or lose its cause.
    report = {key: raw[key] for key in ('status', 'method', 'archive_sha256', 'hresult', 'hresult_hex', 'error_type', 'stage', 'missing_command') if key in raw}
    report['returncode'] = result.returncode
    if result.returncode or report.get('status') != 'pass' or report.get('hresult') != 0:
        report['status'] = 'fail'
    return report


def scan_release(archive, *, status_fn=defender_status, scan_fn=defender_scan, attachment_fn=attachment_scan):
    report = {'schema_version': 2, 'status': 'fail',
              'checked_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'ZIP, extracted members and Windows attachment Save; browser/vendor acceptance remains separate',
              'scans': []}
    try:
        archive = Path(archive).resolve(strict=True)
        report['archive_sha256'] = digest(archive)
        report['engine'] = status_fn()
        with tempfile.TemporaryDirectory(prefix='taiwan-exam-security-') as directory:
            extracted = Path(directory)
            # Scan the archive before reading/extracting its payload.
            for role, path in [('archive', archive), ('extracted-members', extracted)]:
                result = scan_fn(path)
                report['scans'].append({'target': role, **result})
                if result['returncode'] != 0:
                    raise ValueError('Detection or scanner failure: publication blocked')
                if role == 'archive':
                    extracted_hashes = inspect_archive(archive, extracted)
                    report['file_count'] = len(extracted_hashes) - 1
            actual_hashes = {str(path.relative_to(extracted)): digest(path)
                             for path in extracted.rglob('*') if path.is_file()}
            if actual_hashes != extracted_hashes:
                raise ValueError('Extracted files changed or were quarantined during scanning')
            if digest(archive) != report['archive_sha256']:
                raise ValueError('Archive changed during scanning')
        report['attachment_check'] = attachment_fn(archive)
        if (report['attachment_check'].get('status') != 'pass'
                or report['attachment_check'].get('hresult') != 0
                or report['attachment_check'].get('archive_sha256') != report['archive_sha256']):
            raise ValueError('Attachment check evidence mismatch')
        if digest(archive) != report['archive_sha256']:
            raise ValueError('Archive changed during attachment check')
        report['status'] = 'pass'
    except Exception as exc:
        # Avoid publishing machine/user paths in failure reports.
        report['error'] = type(exc).__name__ + ': publication scan did not pass'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.archive.resolve() == args.report.resolve():
        parser.error('Report must not overwrite the archive')
    report = scan_release(args.archive)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())
