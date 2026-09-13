#!/usr/bin/env python3
"""Prepare actual final-PDF page/item review in one batch; never approve content."""
from __future__ import annotations
import argparse
import copy
import hashlib
import html
import json
from pathlib import Path
import time

import pymupdf
from hosted_item_layout import crop_items, crop_bytes, geometry_errors
from inspect_hosted_pdf import audit


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    with pymupdf.open(body) as source, pymupdf.open(final) as target, pymupdf.open() as projected:
        errors=geometry_errors(source, result['parts'])
        if errors:raise ValueError('; '.join(errors))
        for source_page in source:
            destination=target[source_page.number+offset].rect
            page=projected.new_page(width=destination.width,height=destination.height)
            page.show_pdf_page(page.rect,source,source_page.number)
        for part in result['parts']:
            page=part['page']
            if not 1 <= page+offset <= len(target):raise ValueError('Final PDF has missing body pages')
            # Reproduce the compositor's exact A4 rounding transform, rather
            # than comparing slightly different 595.28 / 595.276 page widths.
            if crop_bytes(projected[page-1],part['bbox']) != crop_bytes(target[page+offset-1],part['bbox']):
                raise ValueError('Final item pixels differ from measured body; repair or measure final layout explicitly')
            part['page']+=offset
    result['pdf_sha256']=sha(final)
    return result


def prepare(state_path, pairs, output):
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
    if set(pairs)!={'question','solution'}:raise ValueError('Supply both booklets')
    for paths in pairs.values():
        for path in paths:record(path)
    output.mkdir(parents=True)
    def save(name,value):
        path=output/name
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
        return record(path)
    def relative_rasters(rows):
        for row in rows:row['raster_path']=record(Path(row['raster_path']))['path']
    index=['<!doctype html><meta charset="utf-8"><title>待審版面</title>',
           '<style>body{font:18px sans-serif;max-width:1200px;margin:24px auto}img{max-width:100%;border:1px solid #ddd}section{margin:30px 0}</style>',
           '<h1>待審版面 — 尚未通過</h1><p>逐頁與逐題開啟原尺寸圖片，核對實際內容，填寫觀察及修正。此頁不會自動核准。</p>']
    state.setdefault('pdfs',{})
    reused={'pages':0,'parts':0}
    for role,(pdf,body,layout_path) in pairs.items():
        layout=bind_layout(body,pdf,json.loads(layout_path.read_text(encoding='utf-8')),1 if role=='question' else 0)
        items=crop_items(pdf,layout,output/role/'items')
        scan=audit(pdf,output/role/'pages',math=exam['metadata']['subject'] in {'數學A','數學B'})
        relative_rasters(items['parts']);relative_rasters(scan['pages'])
        visual={'pdf_sha256':sha(pdf),'pages':[
            {'page':p['page'],'raster_sha256':p['raster_sha256'],'status':'pending',
             'observations':'','issue_dispositions':{}} for p in scan['pages']]}
        prior=state['pdfs'].get(role,{})
        if prior.get('exam_sha256')==state['exam']['sha256']:
            if record(root/prior['file']['path'])!=prior['file']:
                raise ValueError('Prior PDF changed; retain its original reviewed bytes')
            def prior_report(key):
                saved=prior.get(key)
                if not saved:return None
                path=root/saved['path']
                if record(path)!=saved:raise ValueError('Prior review hash is stale; refresh after actual review')
                report=json.loads(path.read_text(encoding='utf-8'))
                if report.get('pdf_sha256')!=prior.get('file',{}).get('sha256'):
                    raise ValueError('Prior review belongs to another PDF')
                return report
            old_scan=prior_report('inspection');old_visual=prior_report('visual_review');old_items=prior_report('item_review')
            if old_scan and old_visual:
                old_pages={p['page']:p for p in old_scan['pages']}
                old_rows={p['page']:p for p in old_visual['pages']}
                for fresh,mechanical in zip(visual['pages'],scan['pages']):
                    old=old_rows.get(fresh['page'],{});seen=old_pages.get(fresh['page'],{})
                    if (old.get('status')=='pass' and old.get('observations') and
                        old.get('raster_sha256')==seen.get('raster_sha256')==fresh['raster_sha256'] and
                        seen.get('issues')==mechanical['issues']):
                        fresh.update(copy.deepcopy(old));fresh['review_basis']='unchanged pixels and exam; retained actual prior review'
                        reused['pages']+=1
            if old_items:
                def signature(p):return (p['id'],p['page'],tuple(p['bbox']),p['raster_sha256'])
                old_parts={signature(p):p for p in old_items['parts']}
                for fresh in items['parts']:
                    old=old_parts.get(signature(fresh),{})
                    if old.get('status')=='pass' and old.get('observations'):
                        fresh.update(status='pass',observations=old['observations'],
                                     review_basis='unchanged pixels and exam; retained actual prior review')
                        reused['parts']+=1
        state['pdfs'][role]={'file':record(pdf),'exam_sha256':state['exam']['sha256'],
                            'inspection':save(role+'-inspection.json',scan),
                            'item_review':save(role+'-items.json',items),
                            'visual_review':save(role+'-review.json',visual)}
        index.append('<h2>'+role+'</h2>')
        for label,rows in [('頁',scan['pages']),('題目區塊',items['parts'])]:
            for row in rows:
                src=(root/row['raster_path']).relative_to(output).as_posix()
                name=html.escape(str(row.get('id',row['page'])))
                index.append(f'<section><h3>{label} {name}</h3><a href="{src}"><img src="{src}" loading="lazy"></a></section>')
    # Save a new state rather than overwriting active reviewer records.
    # Relative paths in run-state are rooted at the RUN, not review directory.
    # Put the candidate state beside its original so the checker resolves them.
    candidate.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    index_path=output/'index.html';index_path.write_text('\n'.join(index),encoding='utf-8')
    return {'status':'review-pending','state':str(candidate),'index':str(index_path),
            'retained_actual_reviews':reused,
            'elapsed_seconds':round(time.monotonic()-started,3),
            'next':'Actually review images, update observations and saved report hashes, then run check_hosted_run.py'}


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
