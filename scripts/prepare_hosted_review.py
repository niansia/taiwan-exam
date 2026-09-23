#!/usr/bin/env python3
"""Prepare actual final-PDF page/item review in one batch; never approve content."""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import hashlib
import html
import json
from pathlib import Path
import time

import pymupdf
from hosted_density import page_void_limit
from hosted_calibration import snapshot
from hosted_item_layout import crop_items, crop_bytes, geometry_errors, render_signature, equivalent_render
from hosted_item_triage import crop_required_ids, part_reviewed_on_page
from inspect_hosted_pdf import audit
from validate_paper_difficulty_balance import printable

# Review and design metadata change while real reviews are recorded; they are
# never printed. Printed question/answer fields stay in the item binding.
REVIEW_ONLY_QUESTION_FIELDS = frozenset({'item_spec', 'expected_minutes'})
REVIEW_ONLY_ANSWER_FIELDS = frozenset({'independent_review', 'difficulty_label',
                                       'verification_status', 'verification_notes'})
# One page with its pending crops per viewing call: separate native-resolution
# images, never stitched or downscaled into a contact sheet.
REVIEW_BATCH_IMAGES = 6


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def item_hashes(exam):
    """Authored printable record per question id; a shared stimulus binds its group."""
    questions = [q for q in exam.get('questions', []) if isinstance(q, dict)]
    answers = {}
    for answer in exam.get('answers', []) or []:
        if isinstance(answer, dict):
            answers.setdefault(answer.get('question_id'), []).append(
                {k: v for k, v in answer.items() if k not in REVIEW_ONLY_ANSWER_FIELDS})
    # Asset paths are storage, not print: printable() keys a figure by its bytes.
    records = {q.get('id'): printable({'question': {k: v for k, v in q.items() if k not in REVIEW_ONLY_QUESTION_FIELDS},
                                       'answers': answers.get(q.get('id'), [])}) for q in questions}
    result = {}
    for question in questions:
        group = question.get('group_stimulus')
        members = [q.get('id') for q in questions if group and q.get('group_stimulus') == group]
        result[question.get('id')] = canonical_sha([records[m] for m in members or [question.get('id')]])
    return result


def paper_print_hash(exam):
    return canonical_sha({key: exam.get(key) for key in ('instructions', 'sections')})


def projected(body, sizes):
    """Paint body pages exactly as the compositor does onto its fixed-page size.

    sizes: one (width, height) per body page, or one pair for every page.
    """
    target = pymupdf.open()
    with pymupdf.open(body) as source:
        for page in source:
            width, height = sizes[page.number] if isinstance(sizes[0], (list, tuple)) else sizes
            copy_page = target.new_page(width=width, height=height)
            copy_page.show_pdf_page(copy_page.rect, source, page.number)
    return target


def crop_keys(parts):
    """record-review keys: the item id, or id#n when one item prints several crops."""
    totals, seen, keys = Counter(part['id'] for part in parts), Counter(), []
    for part in parts:
        seen[part['id']] += 1
        keys.append(part['id'] if totals[part['id']] == 1 else f"{part['id']}#{seen[part['id']]}")
    return keys


def pending_note():
    """Blank reviewer entry: pending until the reviewer writes status and observations."""
    return {'status': 'pending', 'observations': ''}


def mark_page_reviewed_parts(parts, exam):
    """Text-only crops are read on their page; the decision comes from the exam."""
    required = crop_required_ids(exam)
    count = 0
    for part in parts:
        if part.get('item_sha256') and part_reviewed_on_page(part, required):
            part['review_via'] = 'page'
            count += 1
        else:
            part.pop('review_via', None)
    return count


def propagate_page_reviews(parts, page_rows):
    """A passed page review is the review of the text-only crops printed on it.

    A failed or pending page leaves them pending; the reviewer's own item note,
    if any, still overrides. Returns how many crops were settled this way.
    """
    rows = {row.get('page'): row for row in page_rows}
    settled = 0
    for part in parts:
        row = rows.get(part.get('page'))
        if part.get('review_via') != 'page' or part.get('status') == 'pass' or not row:
            continue
        if row.get('status') == 'pass' and row.get('observations'):
            part.update(status='pass', observations=f"text-only item read on page {part['page']}: {row['observations']}",
                        review_basis='reviewed on its passed page image; no separate crop opened')
            settled += 1
    return settled


def annotate_parts(parts, hashes):
    """Ordinal distinguishes continuation parts that share one owner id.

    A crop that also prints covered items binds all of their authored records.
    """
    seen = {}
    for part in parts:
        seen[part['id']] = seen.get(part['id'], 0) + 1
        part['ordinal'] = seen[part['id']]
        members = [part['id'], *part.get('covers', [])]
        bound = [hashes.get(member) for member in members]
        part['item_sha256'] = (None if None in bound else bound[0] if len(bound) == 1
                               else canonical_sha(list(zip(members, bound))))
    return parts


def refresh_review_hashes(state_path):
    """After real review, refresh only review-file digests; never change results."""
    state=json.loads(state_path.read_text(encoding='utf-8'))
    root=state_path.resolve().parent
    for bundle in state.get('pdfs',{}).values():
        for key in ('inspection','item_review','visual_review'):
            record=bundle[key];path=(root/record['path']).resolve()
            if not path.is_relative_to(root):raise ValueError('External review file')
            report=json.loads(path.read_text(encoding='utf-8'))
            if report.get('pdf_sha256')!=bundle['file']['sha256']:raise ValueError('Review belongs to a different PDF')
            record['sha256']=sha(path)
    state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'status':'review-hashes-refreshed','state':str(state_path),'reviews_approved_by_tool':False}


def bind_layout(body, final, layout, offset):
    """Bind measured body parts only after comparing their actual final pixels."""
    if layout.get('pdf_sha256') != sha(body):
        raise ValueError('Measured layout has stale body PDF hash')
    result=copy.deepcopy(layout)
    with pymupdf.open(body) as source, pymupdf.open(final) as target:
        errors=geometry_errors(source, result['parts'])
        if errors:raise ValueError('; '.join(errors))
        if len(source)+offset>len(target):raise ValueError('Final PDF has missing body pages')
        # Reproduce the compositor's exact fixed-page transform (594.96 pt
        # template pages versus 595.28 pt body pages), not an unscaled copy.
        with projected(body,[tuple(target[n+offset].rect)[2:] for n in range(len(source))]) as painted:
            for part in result['parts']:
                page=part['page']
                if crop_bytes(painted[page-1],part['bbox']) != crop_bytes(target[page+offset-1],part['bbox']):
                    raise ValueError('Final item pixels differ from measured body; repair or measure final layout explicitly')
                part['page']+=offset
    result['pdf_sha256']=sha(final)
    return result


def density_evidence(subject, role, page_number, page_count, void, limit=None):
    """The fixed limit verdict plus same-role embedded official measurements as reference."""
    try:
        calibration = snapshot(subject)
    except (OSError, ValueError, KeyError, StopIteration):
        return None
    expected = ('solutions' if role == 'solution' else 'cover' if page_number == 1 else
                'formula' if page_number == page_count and subject in {'數學A', '數學B'} else 'body')
    if limit is None:
        limit = page_void_limit(subject, expected, page_number == page_count or
                                (subject in {'數學A', '數學B'} and role != 'solution' and page_number == page_count - 1))
    metrics = [m for m in calibration['page_metrics'] if m['page_role'] == expected]
    qualifying = sorted((m for m in metrics if void <= m['bottom_void'] + .10),
                        key=lambda m: (-m['bottom_void'], m['source_sha256'], m['page']))
    over = limit is not None and void > limit
    return {'candidate_bottom_void': void, 'page_role': expected, 'limit': limit,
            'rule': ('fixed limit shared by plan, inspector and final checker (hosted_density.py): body pages 0.32 '
                     '(英文 0.42), last body page 0.60; embedded official measurements are reference only'),
            'status': 'exceeds-fixed-limit' if over else 'within-fixed-limit',
            'largest_embedded_reference': round(max(m['bottom_void'] for m in metrics), 3) if metrics else None,
            'embedded_references': [{'kind': 'embedded-page-metric', 'source_sha256': m['source_sha256'],
                                     'reference_page': m['page'], 'page_role': expected,
                                     'reference_bottom_void': m['bottom_void'],
                                     'limit': round(m['bottom_void'] + .10, 3),
                                     'roc_year': m.get('roc_year'), 'document_role': m.get('document_role')}
                                    for m in qualifying[:3]],
            'decision': 'not-made-by-tool'}


def review_sources(root, state):
    """Actual item reviews already in this run: earlier final builds and item proofs."""
    paths = [root / bundle['item_review']['path'] for bundle in state.get('pdfs', {}).values()
             if bundle.get('item_review')]
    paths += sorted(root.glob('*/question-items.json')) + sorted(root.glob('*/solution-items.json'))
    reports, seen = [], set()
    for path in paths:
        path = path.resolve()
        if path in seen or not path.is_relative_to(root) or not path.is_file():
            continue
        seen.add(path)
        try:
            report = json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError, ValueError):
            continue
        if isinstance(report, dict) and isinstance(report.get('parts'), list):
            reports.append((path, report))
    return reports


class Renderings:
    """Open each earlier source once; signatures compare printed primitives."""
    def __init__(self, root):
        self.root, self.docs, self.signatures = root, {}, {}

    def document(self, source):
        if not isinstance(source, dict):
            return None
        path = (self.root / str(source.get('path', ''))).resolve()
        key = (str(path), source.get('sha256'), bool(source.get('projected')))
        if key not in self.docs:
            self.docs[key] = None
            if path.is_relative_to(self.root) and path.is_file() and sha(path) == source.get('sha256'):
                self.docs[key] = (projected(path, tuple(source['page_size'])) if source.get('projected')
                                  else pymupdf.open(path))
        return self.docs[key]

    def signature(self, source, page, bbox):
        key = (json.dumps(source, sort_keys=True), page, tuple(bbox))
        if key not in self.signatures:
            doc = self.document(source)
            self.signatures[key] = (render_signature(doc[page - 1], bbox)
                                    if doc is not None and 1 <= page <= len(doc) else None)
        return self.signatures[key]

    def close(self):
        for doc in self.docs.values():
            if doc is not None:
                doc.close()


def retain_parts(root, role, parts, source, identity, sources, renderings, legacy):
    """Copy an actual earlier pass only for the same authored item and same printed rendering.

    Matching needs the item's current authored record, an intact reviewed image,
    and either identical crop pixels or identical glyph/rule/image primitives
    within 0.02 pt (float placement noise). Any recorded non-pass finding on an
    equivalent rendering blocks retention. Changed items stay pending.
    """
    counts = {'pixel-identical': 0, 'vector-equivalent': 0}
    candidates = {}
    for path, report in sources:
        if (report.get('role') or path.name.split('-', 1)[0]) != role:
            continue
        for old in report['parts']:
            if old.get('item_sha256'):
                candidates.setdefault((old.get('id'), old.get('ordinal'), old['item_sha256']), []).append(
                    (path, report, old))
    for fresh in parts:
        if not fresh.get('item_sha256'):
            old = legacy.get((fresh['id'], fresh['page'], tuple(fresh['bbox']), fresh['raster_sha256']), {})
            if old.get('status') == 'pass' and old.get('observations'):
                fresh.update(status='pass', observations=old['observations'],
                             review_basis='unchanged pixels and exam; retained actual prior review')
                counts['pixel-identical'] += 1
            continue
        equivalent = []
        for path, report, old in candidates.get((fresh['id'], fresh['ordinal'], fresh['item_sha256']), []):
            raster = (root / str(old.get('raster_path', ''))).resolve()
            if not (raster.is_relative_to(root) and raster.is_file() and sha(raster) == old.get('raster_sha256')):
                continue
            if old.get('raster_sha256') == fresh['raster_sha256']:
                mode = 'pixel-identical'
            elif (identity and report.get('render_identity') == identity and
                  equivalent_render(renderings.signature(report.get('source'), old.get('page'), old.get('bbox')),
                                    renderings.signature(source, fresh['page'], fresh['bbox']))):
                mode = 'vector-equivalent'
            else:
                continue
            equivalent.append((path, old, mode))
        if any(old.get('status') != 'pass' and old.get('observations') for _, old, _ in equivalent):
            # A recorded defect on this rendering keeps its own crop in the queue,
            # even for a text-only item that would otherwise be read on its page.
            fresh.pop('review_via', None)
            fresh['prior_finding'] = 'a non-pass finding was recorded on an equivalent rendering'
            continue
        if not equivalent:
            continue
        passed = [(path, old, mode) for path, old, mode in equivalent
                  if old.get('status') == 'pass' and old.get('observations')]
        if not passed:
            continue
        path, old, mode = max(passed, key=lambda row: (row[2] == 'pixel-identical', row[0].stat().st_mtime))
        fresh.update(status='pass', observations=old['observations'],
                     review_basis=(f'unchanged authored item; {mode} rendering of an actual earlier review '
                                   f'({path.relative_to(root).as_posix()}, raster {old["raster_sha256"][:12]})'))
        counts[mode] += 1
    return counts


def prepare(state_path, pairs, output, *, render_identity=None):
    """pairs: role -> (final_pdf, body_pdf, body_layout); all files inside run."""
    started=time.monotonic()
    root=state_path.resolve().parent
    output=output.resolve()
    candidate=root/(output.name+'-run-state.json')
    if not output.is_relative_to(root) or output.exists():
        raise ValueError('Use a new review directory inside this run; preserve earlier evidence')
    if candidate.exists():raise ValueError('Candidate run state already exists')
    state=json.loads(state_path.read_text(encoding='utf-8'))
    def record(path):
        path=path.resolve()
        if not path.is_relative_to(root):raise ValueError('Artifact outside this run')
        return {'path':path.relative_to(root).as_posix(),'sha256':sha(path)}
    exam_path=root/state['exam']['path']
    if record(exam_path)!=state['exam']:raise ValueError('Save the current exam hash before preparing review')
    exam=json.loads(exam_path.read_text(encoding='utf-8'))
    subject=exam.get('metadata',{}).get('subject')
    hashes=item_hashes(exam)
    paper_hash=paper_print_hash(exam)
    if set(pairs)!={'question','solution'}:raise ValueError('Supply both booklets')
    for paths in pairs.values():
        for path in paths:record(path)
    sources=review_sources(root,state)
    output.mkdir(parents=True)
    def save(name,value):
        path=output/name
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
        return record(path)
    def relative_rasters(rows):
        for row in rows:row['raster_path']=record(Path(row['raster_path']))['path']
    index=['<!doctype html><meta charset="utf-8"><title>待審版面</title>',
           '<style>body{font:18px sans-serif;max-width:1200px;margin:24px auto}img{max-width:100%;border:1px solid #ddd}section{margin:30px 0}details{margin:30px 0}</style>',
           '<h1>待審版面 — 尚未通過</h1><p>逐頁與逐題開啟原尺寸圖片，核對實際內容，填寫觀察及修正。此頁不會自動核准。'
           '已沿用的項目來自同一份未變更內容的實際審閱，列在最後。</p>']
    state.setdefault('pdfs',{})
    reused={'pages':0,'parts':0}
    basis={'pixel-identical':0,'vector-equivalent':0}
    page_read={}
    queue={};density_flags=[];batches=[];template={}
    renderings=Renderings(root)
    try:
        for role,(pdf,body,layout_path) in pairs.items():
            layout=bind_layout(body,pdf,json.loads(layout_path.read_text(encoding='utf-8')),1 if role=='question' else 0)
            items=crop_items(pdf,layout,output/role/'items')
            scan=audit(pdf,output/role/'pages',math=subject in {'數學A','數學B'},subject=subject,solutions=role=='solution')
            relative_rasters(items['parts']);relative_rasters(scan['pages'])
            annotate_parts(items['parts'],hashes)
            page_read[role]=mark_page_reviewed_parts(items['parts'],exam)
            items.update(role=role,render_identity=render_identity,source=record(pdf),paper_print_sha256=paper_hash)
            by_page={}
            for part in items['parts']:by_page.setdefault(part['page'],[]).append(part)
            visual={'pdf_sha256':sha(pdf),'paper_print_sha256':paper_hash,'pages':[]}
            for p in scan['pages']:
                bound=by_page.get(p['page'],[])
                row={'page':p['page'],'raster_sha256':p['raster_sha256'],'status':'pending',
                     'observations':'','issue_dispositions':{}}
                # Cover/formula pages carry no item content: their pixels and
                # printed section text decide reuse. Unbound part ids fall back
                # to whole-exam equality.
                if all(part['item_sha256'] for part in bound):
                    row['content_items']=[[part['id'],part['ordinal'],part['item_sha256']] for part in bound]
                if 'large-bottom-void-review' in p['issues'] and subject:
                    evidence=density_evidence(subject,role,p['page'],scan['page_count'],p['bottom_void_ratio'],p.get('bottom_void_limit'))
                    if evidence:
                        row['density_evidence']=evidence
                        density_flags.append({'role':role,'page':p['page'],'bottom_void':p['bottom_void_ratio'],
                                              'page_role':evidence['page_role'],'status':evidence['status'],
                                              'limit':evidence['limit'],'largest_embedded_reference':evidence['largest_embedded_reference']})
                visual['pages'].append(row)
            prior=state['pdfs'].get(role,{})
            same_exam=prior.get('exam_sha256')==state['exam']['sha256']
            legacy_parts={}
            if prior.get('file'):
                intact=(root/prior['file']['path']).is_file() and record(root/prior['file']['path'])==prior['file']
                if same_exam and not intact:
                    raise ValueError('Prior PDF changed; retain its original reviewed bytes')
                def prior_report(key):
                    saved=prior.get(key)
                    if not saved:return None
                    path=root/saved['path']
                    if not path.is_file() or record(path)!=saved:
                        if same_exam:raise ValueError('Prior review hash is stale; refresh after actual review')
                        return None
                    report=json.loads(path.read_text(encoding='utf-8'))
                    if report.get('pdf_sha256')!=prior.get('file',{}).get('sha256'):
                        raise ValueError('Prior review belongs to another PDF')
                    return report
                old_scan=prior_report('inspection') if intact else None
                old_visual=prior_report('visual_review') if intact else None
                old_items=prior_report('item_review') if intact else None
                if old_scan and old_visual:
                    old_pages={p['page']:p for p in old_scan['pages']}
                    old_rows={p['page']:p for p in old_visual['pages']}
                    for fresh,mechanical in zip(visual['pages'],scan['pages']):
                        old=old_rows.get(fresh['page'],{});seen=old_pages.get(fresh['page'],{})
                        if 'content_items' in fresh and 'content_items' in old:
                            same_content=(old['content_items']==fresh['content_items'] and
                                          old_visual.get('paper_print_sha256')==paper_hash)
                        else:
                            same_content=same_exam
                        whole_same=old.get('raster_sha256')==seen.get('raster_sha256')==fresh['raster_sha256']
                        body_same=(bool(seen.get('body_raster_sha256')) and
                                   seen.get('body_raster_sha256')==mechanical.get('body_raster_sha256'))
                        if (same_content and old.get('status')=='pass' and old.get('observations') and
                            (whole_same or body_same) and seen.get('issues')==mechanical['issues']):
                            kept={k:copy.deepcopy(v) for k,v in old.items()
                                  if k not in {'density_evidence','content_items','raster_sha256'}}
                            fresh.update(kept)
                            fresh['review_basis']=('unchanged page pixels and authored content; retained actual prior review'
                                                   if whole_same else
                                                   'unchanged body pixels and authored content (only the running page count changed); retained actual prior review')
                            reused['pages']+=1
                if old_items and same_exam:
                    legacy_parts={(p['id'],p['page'],tuple(p['bbox']),p['raster_sha256']):p
                                  for p in old_items['parts'] if not p.get('item_sha256')}
            counts=retain_parts(root,role,items['parts'],items['source'],render_identity,sources,renderings,legacy_parts)
            for mode,count in counts.items():
                basis[mode]+=count;reused['parts']+=count
            # A retained passed page already reviews the text-only crops on it.
            propagate_page_reviews(items['parts'],visual['pages'])
            state['pdfs'][role]={'file':record(pdf),'exam_sha256':state['exam']['sha256'],
                                'inspection':save(role+'-inspection.json',scan),
                                'item_review':save(role+'-items.json',items),
                                'visual_review':save(role+'-review.json',visual)}
            # Absolute image paths: the helper's working directory is not the run.
            absolute=lambda relative:str((root/relative).resolve())
            keys={id(part):key for part,key in zip(items['parts'],crop_keys(items['parts']))}
            queue[role]={'pages':[absolute(p['raster_path']) for p,row in zip(scan['pages'],visual['pages']) if row['status']!='pass'],
                         'items':[absolute(p['raster_path']) for p in items['parts']
                                  if p['status']!='pass' and p.get('review_via')!='page']}
            notes=template.setdefault(role,{'pages':{},'items':{}})
            for p,row in zip(scan['pages'],visual['pages']):
                images=([(absolute(p['raster_path']),{'pages':str(p['page'])})] if row['status']!='pass' else [])+[
                    (absolute(part['raster_path']),{'items':keys[id(part)]})
                    for part in by_page.get(p['page'],[]) if part['status']!='pass' and part.get('review_via')!='page']
                for _,target in images:
                    (kind,key),=target.items()
                    notes[kind][key]=pending_note()
                for start in range(0,len(images),REVIEW_BATCH_IMAGES):
                    chunk=images[start:start+REVIEW_BATCH_IMAGES]
                    batches.append({'role':role,'page':p['page'],'images':[path for path,_ in chunk],
                                    'record_as':[target for _,target in chunk]})
            index.append('<h2>'+role+'</h2>')
            retained_html=[]
            for label,rows,reviews in [('頁',scan['pages'],visual['pages']),('題目區塊',items['parts'],items['parts'])]:
                for row,review in zip(rows,reviews):
                    src=(root/row['raster_path']).relative_to(output).as_posix()
                    name=html.escape(str(row.get('id',row['page'])))
                    entry=f'<section><h3>{label} {name}</h3><a href="{src}"><img src="{src}" loading="lazy"></a></section>'
                    (retained_html if review.get('status')=='pass' else index).append(entry)
            if retained_html:
                index.append(f'<details><summary>已沿用實際審閱（{len(retained_html)}）</summary>'+''.join(retained_html)+'</details>')
    finally:
        renderings.close()
    # Save a new state rather than overwriting active reviewer records.
    # Relative paths in run-state are rooted at the RUN, not review directory.
    # Put the candidate state beside its original so the checker resolves them.
    candidate.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    index_path=output/'index.html';index_path.write_text('\n'.join(index),encoding='utf-8')
    template_path=output/'observations-template.json'
    template_path.write_text(json.dumps(template,ensure_ascii=False,indent=2),encoding='utf-8')
    blocked=[flag for flag in density_flags if flag['status']=='exceeds-fixed-limit']
    return {'status':'review-pending','state':str(candidate),'index':str(index_path),
            'retained_actual_reviews':reused,'retention_basis':basis,
            'items_read_on_pages':page_read,
            'review_queue':queue,'review_batches':batches,'observations_template':str(template_path),
            'density_flags':density_flags,
            'reflow_before_review':blocked,
            'elapsed_seconds':round(time.monotonic()-started,3),
            'next':('Reflow pages listed in reflow_before_review first: they exceed the fixed density limit and no '
                    'disposition can justify them. ' if blocked else '')+
                   'Open every image in review_batches at readable scale. Fill status and observations in a copy of '
                   'observations_template (keys match record_as), record them with one run_hosted_workflow.py '
                   'record-review call, then finalize.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--refresh-state',type=Path)
    p.add_argument('--state',type=Path);p.add_argument('--output',type=Path)
    for role in ('question','solution'):
        for suffix in ('','-body','-layout'):p.add_argument('--'+role+suffix,type=Path)
    a=p.parse_args()
    if a.refresh_state:
        if any(v for k,v in vars(a).items() if k!='refresh_state'):p.error('Use --refresh-state alone')
        print(json.dumps(refresh_review_hashes(a.refresh_state),ensure_ascii=False));raise SystemExit(0)
    if not all(v for k,v in vars(a).items() if k!='refresh_state'):p.error('Supply state, output, both PDFs, bodies and layouts')
    pairs={role:tuple(getattr(a,role+suffix) for suffix in ('','_body','_layout')) for role in ('question','solution')}
    print(json.dumps(prepare(a.state,pairs,a.output),ensure_ascii=False,indent=2))
