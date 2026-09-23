#!/usr/bin/env python3
"""Check offline calibration and fixed-PDF production BEFORE authoring a paper."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import time

import ensure_pymupdf

ensure_pymupdf.require()  # Installs the bundled wheel offline when the runtime lacks PyMuPDF.
import pymupdf  # noqa: E402
from compose_hosted_pdf import compose
from fetch_hosted_template_assets import DEFAULT_MAP, PRODUCTION_COMPONENTS, materialize, production_records, verify
from hosted_calibration import SUBJECTS, snapshot
from hosted_run_timing import transition
from hosted_blind_review import REVIEW_MODES
from verify_fixed_template_pdf import verify_pdf


PREFLIGHT_DEPENDENCIES = (
    'prepare_hosted_run.py', 'compose_hosted_pdf.py', 'fetch_hosted_template_assets.py',
    'verify_fixed_template_pdf.py', 'inspect_hosted_pdf.py', 'validate_math_context.py',
    'hosted_calibration.py', 'hosted_run_timing.py', 'hosted_blind_review.py', 'ensure_pymupdf.py',
)


TEMPLATE_GAP_ACTION = (
    'Stop before drafting. Formal PDFs require the original fixed template components; never typeset or '
    'redraw a cover, running header/footer, answer-marking example or formula page with LaTeX, HTML, Word '
    'or drawing tools, and never deliver such a substitute. Tell the user which component failed and ask '
    'them to attach taiwan-exam-template-resources.pdf from '
    'https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates, then rerun with --resource-pdf.')


class TemplateUnavailable(ValueError):
    """The fixed template components needed for formal PDFs could not be verified."""


BUILTIN_FONT = 'pymupdf-builtin-droid-sans-fallback'
# Hosted runtimes rarely carry a Traditional Chinese serif face, and official
# booklets are set in 明體. The same fixed-URL route as the PyMuPDF wheel
# fetches a static Noto Serif TC Regular (SIL OFL 1.1) before falling back to
# the built-in sans-serif; the download is verified against a pinned digest.
SERIF_FONT_URL = ('https://github.com/niansia/taiwan-exam/releases/download/fonts-noto-serif-tc-1/'
                  'NotoSerifTC-Regular.ttf')
SERIF_FONT_SHA256 = '08cfd4736956f3edd4270e86f009c049cce3a44a9a297b13a66dbec96a66fda8'
SERIF_FONT_BYTES = 10001820
SERIF_FONT_TIMEOUT = 40
# Every booklet prints these in its cover title and running headers.
FIELD_TEXT = '0123456789學年度學科能力測驗模擬試題學測'
# The kai face for 說明 boxes (every subject) and 國寫 reading materials: LXGW WenKai TC
# Regular, OFL 1.1, unmodified upstream release asset re-hosted with its licence notes.
KAI_FONT_URL = ('https://github.com/niansia/taiwan-exam/releases/download/fonts-lxgw-wenkai-tc-1/'
                'LXGWWenKaiTC-Regular.ttf')
KAI_FONT_SHA256 = 'b1a0795862c1415bf3f393ea50b2a4ea6275012cf5bad3f94feeb1222f555731'
KAI_FONT_BYTES = 15267616
KAI_FONT_TIMEOUT = 60
KAI_TEXT = '說明本部分共有二大題請依各題指示作答'
# Hosted images usually install Noto/Source Han CJK as one collection file whose
# FIRST face is Japanese. MuPDF loads that face, so a paper would print Japanese
# glyph forms with every glyph present and no warning.
REGION_MARKERS = {
    'tc': ('traditional', 'hant', 'cjktc', 'cjk tc', 'tc-', ' tc', 'tw-', ' tw'),
    'hk': ('cjkhk', 'cjk hk', 'hk-', ' hk'),
    'jp': ('japan', 'cjkjp', 'cjk jp', 'jp-', ' jp'),
    'sc': ('simplified', 'hans', 'cjksc', 'cjk sc', 'sc-', ' sc'),
    'kr': ('korea', 'cjkkr', 'cjk kr', 'kr-', ' kr'),
}


def sfnt_names(data, offset=0):
    """A face's own family, full and PostScript names, from its name table."""
    count = struct.unpack('>H', data[offset + 4:offset + 6])[0]
    tables = [struct.unpack('>4sIII', data[offset + 12 + 16 * i:offset + 28 + 16 * i]) for i in range(count)]
    table = next((data[start:start + length] for tag, _, start, length in tables if tag == b'name'), None)
    if table is None:
        return []
    records, strings = struct.unpack('>H', table[2:4])[0], struct.unpack('>H', table[4:6])[0]
    names = []
    for index in range(records):
        platform, _, _, name_id, size, start = struct.unpack('>6H', table[6 + 12 * index:18 + 12 * index])
        if name_id in (1, 4, 6):
            try:
                names.append(table[strings + start:strings + start + size].decode('utf-16-be' if platform == 3 else 'latin-1'))
            except UnicodeDecodeError:
                continue
    return names


def region_of(names):
    """'tc', 'jp', ... when a font's own names state one regional form."""
    text = ' ' + ' '.join(names).lower().replace('_', ' ')
    found = {region for region, markers in REGION_MARKERS.items() if any(marker in text for marker in markers)}
    return found.pop() if len(found) == 1 else None


def sfnt_face(data, offset):
    """Standalone font bytes for one face of a TrueType/OpenType collection."""
    count = struct.unpack('>H', data[offset + 4:offset + 6])[0]
    header = bytearray(data[offset:offset + 12 + 16 * count])
    body = bytearray()
    for index in range(count):
        tag, checksum, start, length = struct.unpack('>4sIII', data[offset + 12 + 16 * index:offset + 28 + 16 * index])
        struct.pack_into('>4sIII', header, 12 + 16 * index, tag, checksum, len(header) + len(body), length)
        body += data[start:start + length].ljust((length + 3) // 4 * 4, b'\0')
    return bytes(header + body)


def collection_face(data, path, run_dir):
    """(file, description) of the collection's Traditional Chinese face, else its first."""
    count = struct.unpack('>I', data[8:12])[0]
    faces = [(offset, sfnt_names(data, offset))
             for offset in struct.unpack(f'>{count}I', data[12:12 + 4 * count])]
    offset, names = next((face for face in faces if region_of(face[1]) in ('tc', 'hk')), faces[0])
    label = names[0] if names else path.stem
    target = run_dir / 'fonts' / ((re.sub(r'[^A-Za-z0-9]+', '-', label).strip('-') or 'face') + '.ttf')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(sfnt_face(data, offset))
    return target, f'{label} of {path.name} ({len(faces)} faces)'


def supplied_font(path, run_dir):
    """(file, record, rejection) for a supplied body font, one face at a time."""
    face = None
    try:
        data = path.read_bytes()
        chosen, face = collection_face(data, path, run_dir) if data[:4] == b'ttcf' else (path, None)
        font = pymupdf.Font(fontfile=str(chosen))
        missing = ''.join(sorted({c for c in FIELD_TEXT if not font.has_glyph(ord(c))}))
    except Exception as exc:  # MuPDF and the collection reader raise their own error types
        return None, None, f'cannot use {path.name}: {exc}'
    if missing:
        return None, None, f'{path.name} lacks {missing}'
    record = {'path': str(chosen.resolve()), 'source': 'supplied' if face is None else 'supplied-collection-face',
              'sha256': digest(chosen)}
    if face:
        record.update(face=face, collection=str(path.resolve()))
    region = region_of(sfnt_names(chosen.read_bytes()))
    if region in ('jp', 'sc', 'kr'):
        record['regional_form_note'] = (f'{chosen.name} draws {region.upper()} glyph forms; keep going, say so in the '
                                        'delivery message, and use a Traditional Chinese face (for example Noto Serif '
                                        'CJK TC) when one is available')
    return chosen, record, None


def authoring_requirements(subject):
    """What every saved item must already carry, stated before the first batch.

    A 3-hour hosted run learned each of these from a later gate and rebuilt the
    paper each time; the batch saver now reports the same messages per item.
    """
    common = [
        'item_spec.curriculum_codes: 108 課綱 codes for every item (scope validator fails per item without them)',
        'item_spec.difficulty_design: band, basis, confidence, short_route, misconception, linked_decisions, bottleneck, '
        'expected_minutes, content_sha256 (difficulty-field-contract.md)',
        'item_spec.originality_record: candidate_count>=3, 3 mechanism families, novelty_dimensions>=3, skin_swap_test and '
        'lexical_screen pass; items of one shared stimulus, or subparts of one printed number (國寫 問題（二）), may set '
        'item_spec.inherits_audit_from to the leading item',
        'item_spec.subject_innovation_audit for 國綜/自然/社會 items (candidate_competition_linked, routine rejected, text fields)',
        'any printed material (group_stimulus, long prompt, continuation pages): item_spec.literacy.source_ids naming a real '
        'registered source plus item_spec.source_grounding {status: verified, proposition_map, material_mode/data_mode}; '
        'never a self-written passage labelled 自擬/自撰/編者撰成',
        'recent items: item_spec.current_context bound to metadata.current_context_plan (current-form-topicality.md floors)',
        'answers: final_answer is a printed label; reasoning names the chosen option; explanations never cite a label that '
        'was reordered away',
        'metadata: difficulty_balance_plan (also read as paper_difficulty_plan), mixed_group_originality_records for every '
        'shared stimulus, subject_innovation_review',
    ]
    by_subject = {
        '國綜': ['Q1 pairs two different look-alike characters in four-character phrases; Q2 錯別字 sentences >= 16 characters; '
               '排序 is 古文; 填詞 quotes an attributed work with two candidates per slot; every 題組 prints 改寫自 作者〈篇名〉 or '
               'the 文言 title; >= 30 attribution tokens; absolute-word options <= 12%; one ①②研判 single-choice item; '
               'stems quote 「…」 exactly as the material prints it; options one per line unless four options <= 16 chars'],
        '自然': ['five verified recent sources carrying eight items in both parts, two within 180 days, a Taiwan hazard, '
               'climate/energy and Taiwan contexts; 16 answer-bearing visuals with 3 real photos; curriculum codes per item',
               'each discipline spreads over at least three 108 主題 letters (official 4-7 chapters a year) and no chapter '
               'above six items; Q1-36: 12-19 多選 (應選2項 or 應選3項 only) in four nine-item discipline blocks; Q37-56..60: six 題組 of 3-6 '
               'items, each with a 非選, 3-9 單選, 5-10 多選, 8-9 非選; metadata.natural_choice_form_contract records the '
               'actual counts (official 111-115 bands, not the 115 mix alone)'],
        '數學A': ['item_spec.scope_codes: 108 codes from templates/current-gsat-math-scope.json on every item (validate_math_context '
                'fails without them); five options (1)-(5); stems without method hints or disclaimers'],
        '數學B': ['item_spec.scope_codes: 108 codes (10年級 common core plus 11B) on every item, never 11A codes; every paper has '
                'matrix, sphere/space, polynomial, line-circle, trigonometry, exp-log, counting, probability and data items; '
                'sequence <= 2, counting <= 2, probability <= 3, no unit above 5 items; 3-10 items carry 11B codes'],
        '國寫': ['two 大題: 一、 material 331-606 字 then 問題（一）文長限80字以內（至多4行）（占4分） and 問題（二）文長限400字以內'
               '（至多19行）（占21分）; 二、 material 226-443 字 then 請以「題目」為題 (情意: 書寫經驗、感受、體悟或想像)（占25分）; '
               'at least one material attributed inline（改寫自 作者《書名》）; no 文言, no 自擬; the section 說明 prints the '
               'full official 115 wording (answer sheet front/back, black ink, no pencil, illegible handwriting); 一、 prints '
               '「請分項回答下列問題：」 before 問題（一） and 二、 prints 「請回答下列問題：」; the renderer sets materials in 楷體 '
               'with a two-character indent and 問題（一）／（二） with a six-character hanging indent'],
        '社會': ['six within-year items, two within 180 days; ten answer-bearing visuals of four kinds with four real photos; '
               'subject_innovation_audit per item; content codes only in curriculum_codes',
               'printed form (official 111-115 bands): 第壹部分 35-46 單選 of 2 points with (A)-(D), 第貳部分 21-29 numbered items '
               'in 8-11 題組 with 11-19 單選 and 9-11 非選, 64-67 items, no 多選; curriculum codes spread over 臺灣史／中國與東亞／'
               '世界史 (歷A-F／G-J／K-O), 地理技能／系統／視野 (地A／B／C) and at least three 公民 主題 with four 公B items'],
        '英文': ['ten official headings with A-D labels; passage lengths in the official bands; two recent passages carrying six '
               'items; composition prompt in Chinese with 提示/第一段/第二段 and a picture; unpatterned answer keys',
               'vocabulary stems 13-24 words; reading 35-46 with 2-4 refer-to/closest-in-meaning items, one global item and at '
               'most four is-true/NOT checks; mixed 47-50 = 4-point fill/short pair + 4-point 多選 + 2-point 簡答; 中譯英 18-28 字 each',
               'CEEC 參考詞彙表 (shipped list): every 詞彙題 carries item_spec.lexical_scope (target_word, target_surface_form, '
               'target_pos, option_pos x4, disambiguating_evidence >=2, three distractor_confusion_basis records, allowed_proper_nouns/'
               'glossed_terms for names) and answers.lexical_explanation; targets 6-9 of 10 at levels 1-4 and 1-3 at levels 5-6, at most '
               'one level-6 target; 文意選填 (A)-(J) from the list with 2-4 words at level 4+; items 1-34 at most 5% off-list and 7% '
               'level-6 tokens (proper nouns, contractions and compounds excluded)'],
    }
    return common + by_subject.get(subject, [])


def body_font(run_dir, requested=None):
    """(path, record) of the run's body font.

    Hosted runtimes may have no Traditional Chinese font and no permission to
    install one. PyMuPDF, already required here, ships Droid Sans Fallback with
    full CJK coverage, so a missing or incomplete font never stops a paper.
    """
    # Fixed typography for every subject: the pinned Traditional Chinese serif
    # (明體-style Noto Serif TC) for CJK and Times for digits and Latin letters,
    # as in the official booklets. A supplied font is used only when the pinned
    # serif cannot be obtained; the built-in sans-serif is the last resort.
    note = None
    serif, serif_note = downloaded_serif_font(run_dir)
    if serif is not None:
        path, record = serif
        if requested:
            record['supplied_font_ignored'] = f'{Path(requested).name}: the pinned serif body font is fixed for every subject'
        return path, record
    if requested:
        path, record, note = supplied_font(Path(requested), run_dir)
        if path is not None:
            record['serif_download'] = serif_note
            return path, record
    target = run_dir / 'fonts' / 'builtin-cjk.ttf'
    if not target.is_file():
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(pymupdf.Font('cjk').buffer)
    record = {'path': target.relative_to(run_dir).as_posix(), 'source': BUILTIN_FONT, 'sha256': digest(target),
              'style': 'sans-serif CJK; keep going and mention it in the delivery message; '
                       'use a Traditional Chinese serif font file if the user supplies one',
              'serif_download': serif_note}
    if note:
        record['replaced'] = note
    return target, record


def downloaded_serif_font(run_dir, url=SERIF_FONT_URL, timeout=SERIF_FONT_TIMEOUT):
    """((path, record), None) for the pinned Noto Serif TC body font, or (None, why not)."""
    target = run_dir / 'fonts' / 'NotoSerifTC-Regular.ttf'
    if os.environ.get('TAIWAN_EXAM_NO_FONT_DOWNLOAD') and not target.is_file():
        return None, 'serif font download disabled by TAIWAN_EXAM_NO_FONT_DOWNLOAD; the built-in sans-serif face was used'
    if not (target.is_file() and digest(target) == SERIF_FONT_SHA256):
        import urllib.request
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'taiwan-exam-generator'})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read(SERIF_FONT_BYTES + 1)
        except Exception as exc:  # blocked network, DNS, TLS or HTTP failure: fall back, say why
            return None, f'serif font download failed ({type(exc).__name__}: {exc}); the built-in sans-serif face was used'
        if len(data) != SERIF_FONT_BYTES or hashlib.sha256(data).hexdigest() != SERIF_FONT_SHA256:
            return None, 'serif font download did not match the pinned digest; the built-in sans-serif face was used'
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
    try:
        font = pymupdf.Font(fontfile=str(target))
        if any(not font.has_glyph(ord(c)) for c in FIELD_TEXT):
            return None, 'downloaded serif font lacks field glyphs; the built-in sans-serif face was used'
    except Exception as exc:  # MuPDF raises its own error types
        return None, f'downloaded serif font unusable ({exc}); the built-in sans-serif face was used'
    record = {'path': target.relative_to(run_dir).as_posix(), 'source': 'downloaded-noto-serif-tc',
              'sha256': SERIF_FONT_SHA256, 'url': url,
              'style': 'serif Traditional Chinese (Noto Serif TC Regular, SIL Open Font License 1.1), '
                       'the same family as the published layout previews'}
    return (target, record), None


def kai_font_record(run_dir, url=KAI_FONT_URL, timeout=KAI_FONT_TIMEOUT):
    """Record of the pinned kai face, or why the serif body face stands in for it."""
    target = run_dir / 'fonts' / 'LXGWWenKaiTC-Regular.ttf'
    fallback = 'the 說明 boxes and 國寫 materials print in the serif body face instead of 楷體'

    def unavailable(note):
        return {'unavailable': note + '; ' + fallback, 'url': url}

    if os.environ.get('TAIWAN_EXAM_NO_FONT_DOWNLOAD') and not target.is_file():
        return unavailable('kai font download disabled by TAIWAN_EXAM_NO_FONT_DOWNLOAD')
    if not (target.is_file() and digest(target) == KAI_FONT_SHA256):
        import urllib.request
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'taiwan-exam-generator'})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read(KAI_FONT_BYTES + 1)
        except Exception as exc:  # blocked network, DNS, TLS or HTTP failure: fall back, say why
            return unavailable(f'kai font download failed ({type(exc).__name__}: {exc})')
        if len(data) != KAI_FONT_BYTES or hashlib.sha256(data).hexdigest() != KAI_FONT_SHA256:
            return unavailable('kai font download did not match the pinned digest')
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
    try:
        font = pymupdf.Font(fontfile=str(target))
        if any(not font.has_glyph(ord(c)) for c in KAI_TEXT):
            return unavailable('downloaded kai font lacks 說明 glyphs')
    except Exception as exc:  # MuPDF raises its own error types
        return unavailable(f'downloaded kai font unusable ({exc})')
    return {'path': target.relative_to(run_dir).as_posix(), 'source': 'downloaded-lxgw-wenkai-tc', 'sha256': KAI_FONT_SHA256,
            'url': url, 'style': '楷體 Traditional Chinese (LXGW WenKai TC Regular, SIL Open Font License 1.1) for the '
                                 'bordered 說明 boxes of every subject and the 國寫 reading materials, as the official '
                                 'booklets set them in 標楷體'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cache_inputs(font):
    """Local runtime identity, not an installation or educational approval."""
    scripts = Path(__file__).resolve().parent
    return {'version': 1, 'font': {'path': str(font.resolve()), 'sha256': digest(font)},
            'pymupdf': pymupdf.VersionBind, 'template_map_sha256': digest(DEFAULT_MAP),
            'helpers': {name: digest(scripts / name) for name in PREFLIGHT_DEPENDENCIES}}


def cached_ready(previous, report, run_dir, font, calibration):
    """Reuse only intact readiness proofs; never touch a resumed paper's clock."""
    if not previous or previous.get('status') != 'ready-for-authoring' or previous.get('errors'):
        return False
    for key in ('paper_id', 'subject', 'review_mode', 'require_independent_review', 'scope'):
        if previous.get(key) != report.get(key):
            return False
    try:
        if previous.get('cache_inputs') != cache_inputs(font):
            return False
        # Detect a changed preflight record before trusting its artifact table.
        bound = {k: v for k, v in previous.items() if k != 'record_sha256'}
        if previous.get('record_sha256') != hashlib.sha256(
                json.dumps(bound, ensure_ascii=False, sort_keys=True).encode()).hexdigest():
            return False
        def intact(record, expected):
            path = run_dir / expected
            return (record.get('path') == expected and path.resolve().is_relative_to(run_dir)
                    and path.is_file() and record.get('sha256') == digest(path))
        if not intact(previous.get('calibration', {}), 'calibration.json'):
            return False
        if json.loads((run_dir / 'calibration.json').read_text(encoding='utf-8-sig')) != calibration:
            return False
        manifest = json.loads(DEFAULT_MAP.read_text(encoding='utf-8-sig'))
        subject = next(r for r in manifest['subjects'] if r['subject'] == report['subject'])
        relative = 'templates/' + subject['slug']
        asset_dir = (run_dir / relative).resolve()
        if previous.get('template_asset_dir') != relative or not asset_dir.is_relative_to(run_dir):
            return False
        for asset in subject['assets']:
            if asset['component'] in PRODUCTION_COMPONENTS:
                path = asset_dir / (asset['component'] + '.pdf')
                if not path.resolve().is_relative_to(run_dir):
                    return False
                verify(asset, path.read_bytes())
        if set(previous.get('proofs', {})) != {'questions', 'answers'}:
            return False
        for kind, proof in previous['proofs'].items():
            expected = f'preflight-proofs/{kind}.pdf'
            if not intact(proof, expected):
                return False
            verified = verify_pdf(run_dir / expected, report['subject'], kind, asset_dir)
            if verified['status'] != 'pass-fixed-template':
                return False
            rasters = proof.get('rasters', [])
            if len(rasters) != len(verified['pages']):
                return False
            if not all(intact(row, f'preflight-proofs/{kind}-{index}.png')
                       for index, row in enumerate(rasters, 1)):
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        return False


def save(path, data):
    raw = (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(raw)
    temporary.replace(path)
    return hashlib.sha256(raw).hexdigest()


def bundled_root(subject):
    """This Skill's own root when it carries every component the subject needs."""
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(DEFAULT_MAP.read_text(encoding='utf-8-sig'))
    row = next((r for r in manifest['subjects'] if r['subject'] == subject), None)
    if row is None or not all((root / r['repository_path']).is_file() for r in production_records(row)):
        return None
    return root


def acquire(subject, output, resource_pdf=None, local_root=None, deadline=45):
    if not 0 < deadline <= 60:
        raise ValueError('Resource deadline must be positive and at most 60 seconds')
    if resource_pdf:
        return dict(materialize(subject, output, map_path=DEFAULT_MAP, local_root=None,
                                timeout=10, attempts=1, resource_pdf=resource_pdf), source='uploaded-resource-pdf')
    bundled = None if local_root else bundled_root(subject)
    if bundled:
        # Bundled bytes are checked against the map; a damaged copy fails closed
        # instead of falling back to a download.
        return dict(materialize(subject, output, map_path=DEFAULT_MAP, local_root=bundled,
                                timeout=10, attempts=1), source='bundled-with-skill')
    # A socket timeout does not bound repeated reads. Isolate the existing
    # parallel fetcher in a killable child so slow streams cannot consume a turn.
    command = [sys.executable, str(Path(__file__).with_name('fetch_hosted_template_assets.py')),
               '--subject', subject, '--output-dir', str(output), '--map', str(DEFAULT_MAP),
               '--timeout', '10', '--attempts', '1']
    if local_root:
        command += ['--local-root', str(local_root)]
    try:
        result = subprocess.run(command, capture_output=True, encoding='utf-8',
                                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, timeout=deadline)
    except subprocess.TimeoutExpired:
        return {'status': 'partial', 'errors': [{'message': 'Overall template acquisition deadline reached; '
                'retain verified cached components and use the offline resource PDF.'}]}
    if result.returncode and not result.stdout.strip():
        raise ValueError('Template helper failed: ' + result.stderr[-500:])
    return dict(json.loads(result.stdout), source='local-root' if local_root else 'download')


def prepare(subject, run_dir, paper_id, font, *, resource_pdf=None, local_root=None, deadline=45,
            review_mode='single-context', require_independent_review=False):
    started = time.monotonic()
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    timing = run_dir / 'generation-timing.json'
    previous_preflight = None
    # Never replace authored content, reviews or run-state on resume.
    for name in ('preflight.json', 'run-state.json'):
        if (run_dir / name).exists():
            previous = json.loads((run_dir / name).read_text(encoding='utf-8-sig'))
            if previous.get('paper_id') != paper_id or previous.get('subject', subject) != subject:
                raise ValueError('Refusing to reuse another paper or subject run directory')
            if previous.get('require_independent_review') is True:
                require_independent_review = True  # Never drop an explicit requirement on resume.
            if name == 'preflight.json':
                previous_preflight = previous
    report = {'paper_id': paper_id, 'subject': subject, 'status': 'pending', 'errors': [],
              'review_mode': review_mode, 'require_independent_review': require_independent_review,
              'scope': 'Resource readiness and small layout proofs only; no exam or quality approval.'}
    try:
        if review_mode not in REVIEW_MODES:
            raise ValueError('Unknown difficulty review mode')
        if require_independent_review and review_mode != 'independent-context':
            raise ValueError('Explicit independent review requirement needs an actual separate reviewer; resolve before authoring')
        calibration = snapshot(subject)
        font, report['body_font'] = body_font(run_dir, font)
        report['kai_font'] = kai_font_record(run_dir)
        report['authoring_requirements'] = authoring_requirements(subject)
        if timing.is_file() and cached_ready(previous_preflight, report, run_dir, font, calibration):
            clock = json.loads(timing.read_text(encoding='utf-8-sig'))
            if clock.get('paper_id') != paper_id:
                raise ValueError('Refusing to mix paper clocks')
            resumed = dict(previous_preflight)
            resumed.update(reused_preflight=True, elapsed_seconds=round(time.monotonic() - started, 3),
                           next_action='Resume the saved paper and its next_action; readiness artifacts were verified '
                           'without rebuilding proofs, repeating their visual review, or changing the active phase clock.')
            resumed['record_sha256'] = hashlib.sha256(json.dumps(
                {k: v for k, v in resumed.items() if k != 'record_sha256'},
                ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            return resumed
        transition(timing, paper_id, 'reference_preflight')
        calibration_digest = save(run_dir / 'calibration.json', calibration)
        report['calibration'] = {'path': 'calibration.json', 'sha256': calibration_digest}
        report['calibration_basis'] = calibration['basis']
        report['original_pdf_required'] = False
        try:
            assets = acquire(subject, run_dir / 'templates', resource_pdf, local_root, deadline)
        except (OSError, ValueError, RuntimeError) as exc:
            raise TemplateUnavailable(str(exc)) from exc
        if assets['status'] != 'verified':
            raise TemplateUnavailable('Required template components unavailable: '
                                      + json.dumps(assets['errors'], ensure_ascii=False))
        report['template_source'] = assets.get('source', 'unspecified')
        asset_dir = Path(assets['assets'][0]['path']).parent
        report['template_asset_dir'] = asset_dir.relative_to(run_dir).as_posix()
        proof_dir = run_dir / 'preflight-proofs'
        proof_dir.mkdir(exist_ok=True)
        body = proof_dir / 'body.pdf'
        with pymupdf.open() as doc:
            page = doc.new_page(width=595.28, height=841.89)
            page.insert_text((80, 140), 'Layout preflight only: 1 + 1 = 2', fontsize=12)
            body.write_bytes(doc.tobytes())
        proofs = {}
        for kind in ('questions', 'answers'):
            output = proof_dir / f'{kind}.pdf'
            result = compose(subject, body, asset_dir, output, year='116', title='學科能力測驗模擬試題',
                             running_name='學測', font_path=font, kind=kind)
            proofs[kind] = {'path': output.relative_to(run_dir).as_posix(), 'sha256': result['pdf_sha256'],
                            'rasters': []}
            with pymupdf.open(output) as doc:
                for index, page in enumerate(doc, 1):
                    raster = proof_dir / f'{kind}-{index}.png'
                    page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(raster)
                    proofs[kind]['rasters'].append({'path': raster.relative_to(run_dir).as_posix(),
                                                   'sha256': digest(raster)})
        report['cache_inputs'] = cache_inputs(font)
        report.update(status='ready-for-authoring', proofs=proofs,
                      next_action='Continue in this same response; do not end it to report the preflight. '
                      'Open the small proof rasters and check field/font fit, then run checkpoint --phase authoring '
                      'and read the authoring view (subject calibration and curriculum guidance). proof and build '
                      'default to body_font; if it is the built-in font, say in the delivery message that the body '
                      'is sans-serif. Use the recorded review_mode for small batches: '
                      'single-context means a fresh answer-free solving pass followed by answer comparison, '
                      'not independent blind review. Never invent a reviewer context. '
                      'Use aggregate anchors honestly; final QA needs no original-PDF download. '
                      'Test actual body math typography separately before full composition.')
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        if not timing.exists():
            transition(timing, paper_id, 'reference_preflight')
        report['errors'].append(str(exc))
        report['next_action'] = (TEMPLATE_GAP_ACTION if isinstance(exc, TemplateUnavailable) else
                                 'Resolve the named resource/rendering gap before drafting; retain existing work.')
    report['elapsed_seconds'] = round(time.monotonic() - started, 3)
    report['record_sha256'] = hashlib.sha256(
        json.dumps(report, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    save(run_dir / 'preflight.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subject', required=True, choices=SUBJECTS)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--paper-id', required=True)
    parser.add_argument('--font', type=Path,
                        help='Traditional Chinese body font; without one, or if it lacks a needed glyph, '
                             "PyMuPDF's built-in CJK font is used")
    parser.add_argument('--resource-pdf', type=Path)
    parser.add_argument('--local-root', type=Path)
    parser.add_argument('--deadline', type=float, default=45)
    parser.add_argument('--review-mode', choices=REVIEW_MODES, default='single-context',
                        help='Select independent-context only when a real separate reviewer is available')
    parser.add_argument('--require-independent-review', action='store_true',
                        help='Preserve an explicit user requirement; do not enable merely because it is preferred')
    args = parser.parse_args()
    result = prepare(args.subject, args.run_dir, args.paper_id, args.font,
                     resource_pdf=args.resource_pdf, local_root=args.local_root, deadline=args.deadline,
                     review_mode=args.review_mode, require_independent_review=args.require_independent_review)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'ready-for-authoring' else 2)
