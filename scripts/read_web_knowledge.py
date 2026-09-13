#!/usr/bin/env python3
"""Extract hash-checked reference sections, not questions, from Web Knowledge.

No network, installation, question generation or PDF rendering occurs here.
Without --output-dir, list the selected paths and sizes without dumping content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


SUBJECT_REFERENCES = {
    "數學A": {"current-gsat-math-form.md", "current-gsat-math-scope.md", "math-difficulty-design.md", "math-current-events-and-sourcing.md"},
    "數學B": {"current-gsat-math-form.md", "current-gsat-math-scope.md", "math-difficulty-design.md", "math-current-events-and-sourcing.md"},
    "英文": {"current-gsat-english-form.md"},
    "社會": {"current-gsat-social-form.md", "social-required-content-codes.json"},
    "自然": {"current-gsat-chinese-natural-form.md"},
    "國綜": {"current-gsat-chinese-natural-form.md"},
    "國寫": {"current-gsat-writing-form.md", "gsat-writing-111-115-selection-calibration.md",
             "gsat-writing-source-ecology.md"},
}
SUBJECT_ONLY = set().union(*SUBJECT_REFERENCES.values())
LAYOUT_SLUGS = {'國綜':'chinese','英文':'english','數學A':'math-a','數學B':'math-b',
                '自然':'science','社會':'social','國寫':'writing'}

# Reading order for model context; executable files remain intact on disk.
READING_PHASES = {
    'preflight': ('SKILL.md', 'references/web-platform-use.md',
                  'references/exam-pack-execution-contract.md',
                  'references/hosted-pdf-production.md'),
    'authoring': ('references/generation-protocol.md', 'references/originality-firewall.md',
                  'references/llm-original-item-generation.md', 'references/current-source-transformation.md',
                  'references/stimulus-generation.md', 'references/visual-generation.md',
                  'references/hosted-run-evidence.md', 'references/hosted-quality-gates.md',
                  'schemas/exam.schema.json', 'schemas/question.schema.json',
                  'schemas/answer.schema.json', 'schemas/visual-spec.schema.json'),
    'layout': ('references/hosted-body-workflow.md', 'references/layout-fidelity.md',
               'references/rendering.md', 'references/pdf-provenance.md'),
    'review': ('references/difficulty-calibration.md', 'references/evidence-backed-editorial-audit.md',
               'references/pack-and-release-verification.md'),
}


def relevant(path: str, subject: str) -> bool:
    """Initial read route, not a claim that every transitive dependency is loaded."""
    if subject not in SUBJECT_REFERENCES:
        raise ValueError(f"Unknown GSAT subject: {subject}")
    if any(path == f'templates/hosted-{slug}-{role}.json'
           for slug in LAYOUT_SLUGS.values() for role in ('questions','solutions')):
        return path in {f'templates/hosted-{LAYOUT_SLUGS[subject]}-{role}.json' for role in ('questions','solutions')}
    if path.startswith("references/"):
        return Path(path).name not in SUBJECT_ONLY or Path(path).name in SUBJECT_REFERENCES[subject]
    if path.startswith("exam_packs/"):
        if not path.startswith("exam_packs/學測/") or path.endswith("source-pack-manifest.json"):
            return False
        if "/subjects/" in path:
            folder = "國文" if subject in {"國綜", "國寫"} else subject
            return path.startswith(f"exam_packs/學測/subjects/{folder}/")
    return True


def sections(knowledge: str) -> dict[str, tuple[dict, bytes]]:
    start = knowledge.index("## Source manifest\n")
    manifest_text = knowledge[start:].split("```json\n", 1)[1].split("\n```", 1)[0]
    manifest = json.loads(manifest_text)
    records = {row["path"]: row for row in manifest}
    if len(records) != len(manifest):
        raise ValueError("Duplicate manifest path")
    found = {}
    for match in re.finditer(r'^<canonical-source path="([^"]+)">\n(.*?)^</canonical-source>$',
                             knowledge, re.MULTILINE | re.DOTALL):
        path, payload = match.groups()
        parts = PurePosixPath(path).parts
        if not parts or path.startswith("/") or ".." in parts or "\\" in path or ":" in path:
            raise ValueError("Unsafe canonical path")
        if path in found or path not in records:
            raise ValueError(f"Duplicate or unlisted section: {path}")
        found[path] = (records[path], payload.encode("utf-8"))
    if found.keys() != records.keys():
        raise ValueError("Missing canonical sections")
    return found


def extract(knowledge_path: Path, *, subject: str | None = None,
            paths: list[str] | None = None, output_dir: Path | None = None) -> dict:
    source = knowledge_path.read_text(encoding="utf-8-sig")
    entries = sections(source)
    chosen = sorted(paths or [p for p in entries if subject is None or relevant(p, subject)])
    verified = []
    for path in chosen:
        record, data = entries[path]
        # Original source hashes can differ under CRLF/BOM. Only the explicitly
        # recorded portable payload hash verifies the normalized embedded bytes.
        if (len(data) != record["embedded_bytes"]
                or hashlib.sha256(data).hexdigest() != record["embedded_sha256"]):
            raise ValueError(f"Embedded checksum mismatch: {path}")
        verified.append((path, data))
    if output_dir is not None:
        root = output_dir.resolve()
        for path, data in verified:
            destination = (root / path).resolve()
            if not destination.is_relative_to(root):
                raise ValueError(f"Destination outside workspace: {path}")
            if destination.exists() and destination.read_bytes() != data:
                raise ValueError(f"Preserve existing different file; use a versioned reference directory: {path}")
        for path, data in verified:
            destination = root / path
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
    return {"subject": subject, "section_count": len(verified),
            "selected_bytes": sum(len(data) for _, data in verified),
            "knowledge_bytes": knowledge_path.stat().st_size,
            "files": [{"path": p, "bytes": len(data)} for p, data in verified]}


def reading_plan(knowledge_path: Path, subject: str, output_dir: Path) -> dict:
    """Create phase reading views without changing any canonical helper inputs.

    Views are navigation aids, not a replacement for linked quality rules. JSON
    projections retain exact selected records with their source hash and pointer.
    """
    result = extract(knowledge_path, subject=subject, output_dir=output_dir)
    entries = sections(knowledge_path.read_text(encoding='utf-8-sig'))
    selected = {row['path'] for row in result['files']}
    planned = set()
    views = {}
    source_path = 'exam_packs/學測/metadata/official-current-web-sources.json'
    map_path = 'exam_packs/學測/templates/115/hosted-web-template-assets.json'
    projected_bytes = 0
    for phase, paths in READING_PHASES.items():
        route = list(paths)
        if phase == 'authoring':
            route += ['references/' + name for name in sorted(SUBJECT_REFERENCES[subject])]
            route += sorted(p for p in selected if '/subjects/' in p and p.endswith('.json'))
        if phase == 'layout':
            route += [f'templates/hosted-{LAYOUT_SLUGS[subject]}-{role}.json'
                      for role in ('questions', 'solutions')]
        parts = [f'# {subject}: {phase}\n',
                 'Navigation view only. Canonical files remain unchanged in the parent directory. '
                 'Read once at this phase, follow applicable links, and reuse observations within this run. '
                 'Do not read all phase packets before preflight or print executable source merely to run it.\n']
        for path in route:
            if path not in selected:
                raise ValueError('Reading route requires missing canonical source: ' + path)
            if path in planned:
                continue
            planned.add(path)
            parts.append(f'\n## {path}\n\n' + entries[path][1].decode('utf-8'))
        if phase == 'preflight':
            for path in (source_path, map_path):
                record, payload = entries[path]
                document = json.loads(payload)
                matches = [(i, row) for i, row in enumerate(document['subjects']) if row['subject'] == subject]
                if len(matches) != 1:
                    raise ValueError('Expected one exact subject record in ' + path)
                index, row = matches[0]
                projection = {'canonical_source': path, 'embedded_sha256': record['embedded_sha256'],
                              'json_pointer': f'/subjects/{index}', 'record': row}
                encoded = json.dumps(projection, ensure_ascii=False, indent=2)
                projected_bytes += len(encoded.encode('utf-8'))
                parts.append(f'\n## Selected record from {path}\n\n```json\n{encoded}\n```\n')
        if phase == 'review':
            parts.append('\n## Additional applicable references (read on demand)\n\n' +
                         '\n'.join('- ' + p for p in sorted(selected - planned)
                                   if p.startswith('references/')) + '\n')
        views[f'reading/{phase}.md'] = '\n'.join(parts).encode('utf-8')
    root = output_dir.resolve()
    for path, data in views.items():
        destination = root / path
        if not destination.resolve().is_relative_to(root):
            raise ValueError('Reading view outside reference directory')
        if destination.exists() and destination.read_bytes() != data:
            raise ValueError('Preserve existing reading view; use a versioned reference directory: ' + path)
    for path, data in views.items():
        destination = root / path
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    return {'subject': subject, 'canonical_files': result['section_count'],
            'canonical_bytes': result['selected_bytes'], 'first_read': 'reading/preflight.md',
            'views': [{'path': p, 'bytes': len(data)} for p, data in views.items()],
            'selected_record_bytes': projected_bytes,
            'note': 'Disk extraction size is not model reading time. Views schedule, not waive, required rules.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("knowledge", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--subject", choices=sorted(SUBJECT_REFERENCES))
    group.add_argument("--path", action="append", dest="paths")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--reading-plan", action="store_true",
                        help="Extract canonical runtime once and write staged, subject-specific reading views")
    args = parser.parse_args()
    if args.reading_plan:
        if not args.subject or args.output_dir is None:
            parser.error('--reading-plan requires --subject and --output-dir')
        print(json.dumps(reading_plan(args.knowledge, args.subject, args.output_dir), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(extract(args.knowledge, subject=args.subject, paths=args.paths,
                             output_dir=args.output_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
