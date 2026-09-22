#!/usr/bin/env python3
"""Extract hash-checked reference sections, not questions, from Web Knowledge.

No network, installation, question generation or PDF rendering occurs here.
Without --output-dir, list the selected paths and sizes without dumping content.
"""
from __future__ import annotations
from hosted_bundles import BUNDLE_DIR, parse as parse_bundle, safe_path

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


SUBJECT_REFERENCES = {
    "數學A": {"current-gsat-math-form.md", "current-gsat-math-scope.md", "math-difficulty-design.md", "math-current-events-and-sourcing.md"},
    "數學B": {"current-gsat-math-form.md", "current-gsat-math-scope.md", "math-difficulty-design.md", "math-current-events-and-sourcing.md"},
    # 國綜／國寫／英文／社會／自然 read current-form-literacy-load.md for the same
    # reason 數學A／數學B read math-difficulty-design.md: it is the subject's
    # pre-writing difficulty and reading-load gate.
    "英文": {"current-gsat-english-form.md", "current-form-literacy-load.md"},
    "社會": {"current-gsat-social-form.md", "social-required-content-codes.json",
             "current-form-literacy-load.md"},
    "自然": {"current-gsat-chinese-natural-form.md", "current-form-literacy-load.md"},
    "國綜": {"current-gsat-chinese-natural-form.md", "current-form-literacy-load.md"},
    "國寫": {"current-gsat-writing-form.md", "gsat-writing-111-115-selection-calibration.md",
             "gsat-writing-source-ecology.md", "current-form-literacy-load.md"},
}
SUBJECT_ONLY = set().union(*SUBJECT_REFERENCES.values())
LAYOUT_SLUGS = {'國綜':'chinese','英文':'english','數學A':'math-a','數學B':'math-b',
                '自然':'science','社會':'social','國寫':'writing'}
# Fixed template PDFs bundled with the native Skill; copy only the chosen subject's.
TEMPLATE_ASSETS = 'exam_packs/學測/templates/115/assets/'
TEMPLATE_SLUGS = {'國綜':'chinese-comprehensive','國寫':'chinese-writing','英文':'english',
                  '數學A':'math-a','數學B':'math-b','社會':'social','自然':'science'}
# Placeholder layout previews bundled with the native Skill, likewise per subject.
LAYOUT_PREVIEWS = 'layout-previews/'

# Reading order for model context; executable files remain intact on disk.
READING_PHASES = {
    'preflight': ('references/hosted-execution.md',),
    'authoring': ('references/generation-protocol.md', 'references/originality-firewall.md',
                  'references/llm-original-item-generation.md', 'references/current-source-transformation.md',
                  'references/stimulus-generation.md', 'references/visual-generation.md',
                  'references/difficulty-field-contract.md', 'schemas/exam.schema.json',
                  'schemas/answer.schema.json', 'schemas/visual-spec.schema.json',
                  'schemas/difficulty-design.schema.json'),
    'layout': ('references/hosted-body-workflow.md', 'references/layout-fidelity.md',
               'references/rendering.md', 'references/pdf-provenance.md'),
    'review': ('references/hosted-run-evidence.md', 'references/hosted-quality-gates.md',
               'references/difficulty-calibration.md', 'references/evidence-backed-editorial-audit.md'),
}


def pointer_value(document, pointer: str):
    """Resolve a JSON pointer so reading projections contain exact source values."""
    value = document
    for part in pointer.split('/')[1:]:
        key = part.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def phase_projections(entries: dict, subject: str, selected: set[str]) -> dict:
    """Keep runtime inputs intact, selecting current-regime model reading only.

    Values stay on disk. Reading views carry only exact JSON pointers and source
    digests, never duplicate large canonical records into model context.
    """
    result = {phase: [] for phase in READING_PHASES}

    def add(phase, path, pointers):
        record, raw = entries[path]
        document = json.loads(raw)
        result[phase].append({'canonical_source': path,
                              'embedded_sha256': record['embedded_sha256'],
                              'json_pointers': pointers})
        for pointer in pointers:
            pointer_value(document, pointer)  # Fail on a stale pointer, without serializing its value.

    source_path = 'exam_packs/學測/metadata/official-current-web-sources.json'
    source = json.loads(entries[source_path][1])
    index, source_row = next((i, row) for i, row in enumerate(source['subjects'])
                             if row['subject'] == subject)
    prefix = f'/subjects/{index}'
    add('preflight', source_path, [prefix + '/subject', prefix + '/catalog_subject'])
    year_index, _ = max(enumerate(source_row['years']), key=lambda pair: pair[1]['roc_year'])
    add('authoring', source_path, [f'{prefix}/years/{year_index}/paper_profile'])

    map_path = 'exam_packs/學測/templates/115/hosted-web-template-assets.json'
    mapping = json.loads(entries[map_path][1])
    map_index, map_row = next((i, row) for i, row in enumerate(mapping['subjects'])
                             if row['subject'] == subject)
    add('preflight', map_path, [f'/subjects/{map_index}/{key}'
                                for key in ('subject', 'slug', 'layout_profile')])
    add('layout', map_path, [f'/subjects/{map_index}/overlay_geometry_pt'])

    base = f"exam_packs/學測/subjects/{source_row['catalog_subject']}/"
    writer_path = base + 'blueprints/writer-blueprint.json'
    writer = json.loads(entries[writer_path][1])
    paths = ['/' + key for key in ('subject', 'metadata_fingerprint', 'source_visibility',
                                   'distribution_policy')]
    paths.append('/calibration_by_curriculum/108')
    # Do not feed 國寫 the 國綜 mechanism families (or vice versa) just because
    # both happen to share a storage folder. Other old-regime clusters stay on disk.
    for i, cluster in enumerate(writer['aggregate_pattern_clusters']):
        pattern = cluster['pattern']
        if pattern.get('curriculum') == '108' and (
                subject not in {'國綜', '國寫'} or pattern.get('section', '').startswith(subject)):
            paths.append(f'/aggregate_pattern_clusters/{i}')
    add('authoring', writer_path, paths)

    addition_path = base + 'blueprints/writer-calibration-additions.json'
    if addition_path in selected:
        additions = json.loads(entries[addition_path][1])
        paths = ['/' + key for key in additions if key != 'aggregate_pattern_clusters']
        for i, cluster in enumerate(additions['aggregate_pattern_clusters']):
            pattern = cluster['pattern']
            if pattern.get('curriculum') == '108' and (
                    subject not in {'國綜', '國寫'} or pattern.get('section', '').startswith(subject)):
                paths.append(f'/aggregate_pattern_clusters/{i}')
        add('authoring', addition_path, paths)

    if subject != '國寫':
        # Preserve ALL current-regime slot/section values and limitations. Never
        # substitute whole-corpus (including curriculum 99) totals as targets.
        difficulty_path = base + 'blueprints/difficulty-profile.json'
        add('authoring', difficulty_path, ['/subject', '/band_definition', '/curricula/108'])
    layout_path = base + 'blueprints/layout-profiles/' + map_row['layout_profile'] + '.json'
    layout = json.loads(entries[layout_path][1])
    add('layout', layout_path, ['/' + key for key in layout if key not in {'evidence', 'source_files'}])
    return result


def relevant(path: str, subject: str) -> bool:
    """Initial read route, not a claim that every transitive dependency is loaded."""
    if subject not in SUBJECT_REFERENCES:
        raise ValueError(f"Unknown GSAT subject: {subject}")
    if any(path == f'templates/hosted-{slug}-{role}.json'
           for slug in LAYOUT_SLUGS.values() for role in ('questions','solutions')):
        return path in {f'templates/hosted-{LAYOUT_SLUGS[subject]}-{role}.json' for role in ('questions','solutions')}
    if path.startswith("references/"):
        return Path(path).name not in SUBJECT_ONLY or Path(path).name in SUBJECT_REFERENCES[subject]
    if path.startswith(TEMPLATE_ASSETS):
        return path.startswith(TEMPLATE_ASSETS + TEMPLATE_SLUGS[subject] + '/')
    if path.startswith(LAYOUT_PREVIEWS):
        return path in {f'{LAYOUT_PREVIEWS}{LAYOUT_SLUGS[subject]}-{role}.pdf' for role in ('questions', 'solutions')}
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


def reading_plan_from_directory(source_dir: Path, subject: str, output_dir: Path) -> dict:
    """Use an already installed native Skill without loading a giant Markdown file.

    Validate its package manifest first. This verifies consistency with the
    manifest, not the authenticity of an untrusted package publisher.
    """
    if subject not in SUBJECT_REFERENCES:
        raise ValueError(f'Unknown GSAT subject: {subject}')
    source_root = source_dir.resolve()
    manifest = json.loads((source_root / 'PACKAGE_MANIFEST.json').read_text(encoding='utf-8-sig'))
    entries, verified, seen, runtime_seen = {}, [], set(), set()
    bundles = {}

    def bundled_bytes(row, stored_path):
        # Text sources travel inside a few bundle members; each restored file is
        # still verified against its own manifest digest below.
        bundle = row['bundle']
        if bundle not in bundles:
            if not safe_path(bundle) or not bundle.startswith(BUNDLE_DIR):
                raise ValueError('Unsafe bundle path: ' + str(bundle))
            source = (source_root / bundle).resolve()
            if not source.is_relative_to(source_root) or not source.is_file():
                raise ValueError('Missing or external package bundle: ' + bundle)
            data = source.read_bytes()
            record = (manifest.get('bundles') or {}).get(bundle)
            if (not isinstance(record, dict) or len(data) != record.get('bytes')
                    or hashlib.sha256(data).hexdigest() != record.get('sha256')):
                raise ValueError('Bundle digest mismatch: ' + bundle)
            bundles[bundle] = parse_bundle(data)
        text = bundles[bundle].get(stored_path)
        if text is None:
            raise ValueError('Missing or external package file: ' + stored_path)
        return text.encode('utf-8')

    for row in manifest['files']:
        stored_path = row['path']
        path = row.get('runtime_path', stored_path)
        for candidate, names in ((stored_path, seen), (path, runtime_seen)):
            if (not isinstance(candidate, str) or not candidate
                    or any(part in {'', '.', '..'} for part in candidate.split('/'))
                    or '\\' in candidate or ':' in candidate or '\x00' in candidate
                    or candidate.casefold() in names):
                raise ValueError('Unsafe or duplicate package path: ' + str(candidate))
            names.add(candidate.casefold())
        if not relevant(path, subject):
            continue
        source = (source_root / stored_path).resolve()
        if not source.is_relative_to(source_root):
            raise ValueError('Missing or external package file: ' + path)
        if row.get('bundle') and not source.is_file():
            # An installed ZIP keeps the bundle; a scanner-extracted copy already
            # holds the loose file. Both are verified against the row's digest.
            raw = bundled_bytes(row, stored_path)
        elif source.is_file():
            raw = source.read_bytes()
        else:
            raise ValueError('Missing or external package file: ' + path)
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Package checksum mismatch: ' + path)
        # Native packages preserve source bytes. Views normalize text exactly as
        # the web builder does; copied runtime files keep the package's bytes.
        if Path(stored_path).suffix in {'.md', '.json', '.py', '.txt', '.yaml', '.yml', ''}:
            payload = (raw.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n').rstrip() + '\n').encode('utf-8')
            record = dict(row, path=path, embedded_bytes=len(payload),
                          embedded_sha256=hashlib.sha256(payload).hexdigest())
            entries[path] = (record, payload)
        verified.append((path, raw))
    required = {path for paths in READING_PHASES.values() for path in paths}
    missing = required - entries.keys()
    if missing:
        raise ValueError('Native package is missing reading sources: ' + ', '.join(sorted(missing)))
    root = output_dir.resolve()
    for path, raw in verified:
        destination = (root / path).resolve()
        if not destination.is_relative_to(root):
            raise ValueError('Destination outside workspace: ' + path)
        if destination.exists() and destination.read_bytes() != raw:
            raise ValueError('Preserve existing different file; use a versioned reference directory: ' + path)
    for path, raw in verified:
        destination = root / path
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
    result = {'section_count': len(verified), 'selected_bytes': sum(len(raw) for _, raw in verified),
              'files': [{'path': path, 'bytes': len(raw)} for path, raw in verified]}
    plan = _write_reading_plan(entries, result, subject, output_dir)
    # The native entry already routes the model through hosted-execution.md.
    plan['first_read_note'] = ('reading/preflight.md holds references/hosted-execution.md in full; if you already '
                               'read that file from this Skill, skip these chunks and run the preflight.')
    previews = sorted(str(root / path) for path, _ in verified if path.startswith(LAYOUT_PREVIEWS))
    if previews:
        plan['layout_previews'] = previews
        plan['layout_preview_note'] = ('Placeholder layout only; the renderer already applies it and users need '
                                       'not attach previews. Open one only for a specific layout question.')
    return plan


def reading_plan(knowledge_path: Path, subject: str, output_dir: Path) -> dict:
    """Create phase reading views without changing any canonical helper inputs.

    The hosted contract is the execution entry, not the local maintenance manual.
    JSON references retain exact current-regime pointers and source hashes;
    records and all canonical helper inputs remain unchanged on disk.
    """
    result = extract(knowledge_path, subject=subject, output_dir=output_dir)
    entries = sections(knowledge_path.read_text(encoding='utf-8-sig'))
    return _write_reading_plan(entries, result, subject, output_dir)


READING_CHUNK_LIMIT = 12000
READING_CONTENT_MARKER = '<!-- reading-content -->\n'


def _chunk_text(text, limit):
    """Lossless slices, preferably at line ends. Never truncate a source."""
    pieces=[]
    while text:
        end=min(len(text),limit)
        if end<len(text):
            boundary=text.rfind('\n',0,end)
            if boundary>=limit//2:end=boundary+1
        pieces.append(text[:end]);text=text[end:]
    return pieces or ['']


def _write_reading_plan(entries: dict, result: dict, subject: str, output_dir: Path) -> dict:
    selected={row['path'] for row in result['files']}
    planned=set();views={};phase_records={};embedded={};reference_records=[]
    projections=phase_projections(entries,subject,selected)
    for phase,paths in READING_PHASES.items():
        route=list(paths)
        if phase=='authoring':
            route+=['references/'+name for name in sorted(SUBJECT_REFERENCES[subject])]
        if phase=='layout':
            route += [f'templates/hosted-{LAYOUT_SLUGS[subject]}-{role}.json'
                      for role in ('questions','solutions')]
        parts=[];phase_embedded=[];references=[]
        for path in route:
            if path not in selected:raise ValueError('Reading route requires missing canonical source: '+path)
            if path in planned:continue
            planned.add(path)
            record,raw=entries[path]
            if path.endswith('.json'):
                references.append({'canonical_source':path,'embedded_sha256':record['embedded_sha256'],
                                   'json_pointers':['']})
                continue
            embedded[path]={'phase':phase,'embedded_sha256':record['embedded_sha256']}
            phase_embedded.append(path)
            parts.append(f'\n<reading-source path="{path}">\n'+raw.decode('utf-8')+'</reading-source>\n')
        references.extend(projections[phase])
        if references:
            parts.append('\n## Read JSON only by the relevant field or pointer\n\n'
                         'The following records remain on disk. Do not read entire JSON files merely '
                         'to populate a field. Use emit_item_skeleton.py for generated item fields. '
                         'An empty pointer denotes the schema/document root; inspect its needed fields only.\n')
            for reference in references:
                reference_records.append(dict(reference,phase=phase))
                parts.append('\n- File: `'+reference['canonical_source']+'`\n'
                             '  SHA-256 of normalized canonical text: `'+reference['embedded_sha256']+'`\n'
                             '  JSON pointers: '+', '.join('`'+p+'`' if p else '`(root)`'
                                                          for p in reference['json_pointers'])+'\n')
        if phase=='review':
            parts.append('\n## Additional references: lookup only\n\n'
                         'These are not a recursive reading checklist. Full sources named in this '
                         'phase or an earlier phase are already embedded in its ordered chunks; '
                         'do not read their canonical files again. Maintenance manuals are not hosted steps.\n'+
                         '\n'.join('- '+p for p in sorted(selected-planned) if p.startswith('references/'))+'\n')
        full=''.join(parts)
        # Reserve room for navigation. Count Unicode characters, matching common
        # tool-output limits; each final chunk is checked after its header is added.
        payloads=_chunk_text(full,READING_CHUNK_LIMIT-700)
        chunks=[];offset=0
        for ordinal,payload in enumerate(payloads,1):
            path=f'reading/{phase}-{ordinal:02}.md'
            header=(f'# {subject}: {phase} {ordinal}/{len(payloads)}\n\n'
                    f'Read in order after {phase}.md. This is a continuation of the same phase, '
                    'not a new task. Canonical Markdown in these chunks is embedded in full across '
                    'the ordered sequence; do not reopen it for a duplicate reading. '
                    'Read JSON fields from disk only when needed.\n\n')
            content=header+READING_CONTENT_MARKER+payload
            if len(content)>READING_CHUNK_LIMIT:raise ValueError('Reading chunk exceeds character limit')
            views[path]=content.encode('utf-8')
            chunks.append({'path':path,'characters':len(content),'content_start':offset,
                           'content_end':offset+len(payload),'content_sha256':hashlib.sha256(payload.encode()).hexdigest()})
            offset+=len(payload)
        index=(f'# {subject}: {phase} reading order\n\n'
               'Read this phase only when its work begins. Open each chunk below separately in order; '
               'do not concatenate them into one tool output. Each chunk is at most 12,000 characters.\n\n'+
               '\n'.join(f'{i}. [{Path(row["path"]).name}]({Path(row["path"]).name})' for i,row in enumerate(chunks,1))+
               '\n\nCanonical Markdown embedded in FULL across those chunks (do not reread separately):\n'+
               ('\n'.join('- `'+path+'`' for path in phase_embedded) or '- None')+
               '\n\nCanonical JSON is reference-only: no raw records are duplicated in these packets. '
               'Actual files, hashes and exact pointers remain available. Preserve the previous phases’ observations.\n')
        if len(index)>READING_CHUNK_LIMIT:raise ValueError('Reading index exceeds character limit')
        views[f'reading/{phase}.md']=index.encode('utf-8')
        phase_records[phase]={'index':f'reading/{phase}.md','chunks':chunks,
                              'embedded_sources':phase_embedded,
                              'content_sha256':hashlib.sha256(full.encode()).hexdigest(),
                              'content_characters':len(full)}
    manifest={'schema_version':1,'subject':subject,'chunk_character_limit':READING_CHUNK_LIMIT,
              'phases':phase_records,'embedded_sources':embedded,'json_references':reference_records}
    files=dict(views)
    files['reading/reading-plan.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    root=output_dir.resolve()
    for path,data in files.items():
        destination=root/path
        if not destination.resolve().is_relative_to(root):raise ValueError('Reading view outside reference directory')
        if destination.exists() and destination.read_bytes()!=data:
            raise ValueError('Preserve existing reading view; use a versioned reference directory: '+path)
    for path,data in files.items():
        destination=root/path
        if not destination.exists():
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
    return {'subject':subject,'canonical_files':result['section_count'],
            'canonical_bytes':result['selected_bytes'],'first_read':'reading/preflight.md',
            'reading_manifest':'reading/reading-plan.json',
            'views':[{'path':f'reading/{phase}.md','bytes':len(views[f'reading/{phase}.md'])}
                     for phase in READING_PHASES],
            'chunks':[row for record in phase_records.values() for row in record['chunks']],
            'selected_record_bytes':0,
            'note':'Indexes and ordered chunks are bounded to 12,000 characters. JSON records stay on disk; '
                   'no content is truncated and canonical validator inputs remain unchanged.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("knowledge", nargs='?', type=Path)
    parser.add_argument('--source-dir', type=Path,
                        help='Installed native Skill directory containing PACKAGE_MANIFEST.json')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--subject", choices=sorted(SUBJECT_REFERENCES))
    group.add_argument("--path", action="append", dest="paths")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--reading-plan", action="store_true",
                        help="Extract canonical runtime once and write staged, subject-specific reading views")
    args = parser.parse_args()
    if bool(args.knowledge) == bool(args.source_dir):
        parser.error('Supply either the knowledge file or --source-dir, not both')
    if args.source_dir:
        if not args.reading_plan or not args.subject or args.output_dir is None:
            parser.error('--source-dir requires --reading-plan, --subject and --output-dir')
        print(json.dumps(reading_plan_from_directory(args.source_dir, args.subject, args.output_dir),
                         ensure_ascii=False, indent=2))
        return 0
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
