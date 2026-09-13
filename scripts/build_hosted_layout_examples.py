#!/usr/bin/env python3
"""Maintainer preview build: seven subject-specific PLACEHOLDER booklet pairs."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import time

from hosted_body_templates import render
from compose_hosted_pdf import compose
from fetch_hosted_template_assets import DEFAULT_MAP, ROOT
from inspect_hosted_pdf import audit
from hosted_item_layout import crop_items
from prepare_hosted_review import bind_layout


def build(output, work, font, reading_font=None):
    if output.exists() or work.exists():raise ValueError('Use fresh preview and work directories')
    manifest=json.loads((ROOT/'templates/hosted-subject-layouts.json').read_text(encoding='utf-8'))
    assets=json.loads(DEFAULT_MAP.read_text(encoding='utf-8'))['subjects']
    output.mkdir(parents=True);work.mkdir(parents=True)
    records=[];started=time.monotonic()
    for row in manifest['subjects']:
        record={'subject':row['subject'],'slug':row['slug'],'booklets':{}}
        for role in ('questions','solutions'):
            spec_path=ROOT/'templates'/row[role]
            spec=json.loads(spec_path.read_text(encoding='utf-8'))
            if (spec['subject']!=row['subject'] or spec.get('booklet_role')!=role or
                spec.get('purpose')!='layout-reference-only'):
                raise ValueError('Wrong-subject or non-placeholder preview input')
            stem=row['slug']+'-'+role
            body=work/(stem+'-body.pdf');layout_path=work/(stem+'-layout.json')
            layout=render(spec,body,layout_path,font,asset_root=spec_path.parent,proof=True,reading_font=reading_font)
            asset_row=next(a for a in assets if a['subject']==row['subject'])
            asset_dir=ROOT/Path(asset_row['assets'][0]['repository_path']).parent
            pdf=output/(stem+'.pdf')
            composition=compose(row['subject'],body,asset_dir,pdf,year='116',title='版型示範',
                                running_name='學測',font_path=font,kind='questions' if role=='questions' else 'answers')
            final_layout=bind_layout(body,pdf,layout,1 if role=='questions' else 0)
            items=crop_items(pdf,final_layout,work/stem/'crops')
            scan=audit(pdf,work/stem/'pages',math=row['subject'] in {'數學A','數學B'})
            if scan['blocking_pages']:raise ValueError('Preview has mechanical blocking pages: '+stem)
            review_path=work/(stem+'-review.json')
            review_path.write_text(json.dumps({'inspection':scan,'items':items},ensure_ascii=False,indent=2),encoding='utf-8')
            record['booklets'][role]={'file':pdf.name,'sha256':scan['pdf_sha256'],'pages':scan['page_count'],
                                      'fixed_template':composition['fixed_template_verification']['status'],
                                      'visual_review':'pending','source':row[role]}
        records.append(record)
    result={'purpose':'layout-reference-only','full_exam':False,'subjects':records,
            'scope':'Placeholder layout previews; no authored questions, difficulty or full-paper acceptance',
            'build_seconds':round(time.monotonic()-started,3)}
    (output/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    page=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
          '<title>七科題本與詳解版型</title><style>body{font:18px/1.7 system-ui,sans-serif;max-width:880px;margin:40px auto;padding:0 20px;color:#172126}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:12px;border-bottom:1px solid #ccd3d7}a{color:#07579b}small{font-size:15px}</style>',
          '<h1>七科題本與詳解版型</h1><p>每科各有題本、詳解兩份 PDF。只供排版參考，包含占位材料、選項與圖框，不能直接當作試題。篇幅與題數也不代表完整考卷。</p>',
          '<p>封面、頁首尾與數學公式保留當科原始固定 PDF 圖層；正文則展示各科不同題型。正式出卷時，必須重新命題、製圖、驗算及檢查。</p><table><tr><th>科目</th><th>題本版型</th><th>詳解版型</th></tr>']
    for row in records:
        page.append('<tr><td>'+html.escape(row['subject'])+'</td>'+''.join(
            '<td><a href="'+row['booklets'][role]['file']+'">開啟 PDF</a><br><small>'+str(row['booklets'][role]['pages'])+' 頁</small></td>' for role in ('questions','solutions'))+'</tr>')
    page.append('</table><p><a href="../../download-web-knowledge.html">更新網頁版知識檔</a></p><p><small>這些 PDF 是視覺參考；可執行版型已隨新版知識檔提供，不必在每次出卷時下載全部示範。</small></p></html>')
    (output/'index.html').write_text('\n'.join(page),encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output','work','font'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--reading-font',type=Path)
    a=p.parse_args();r=build(a.output,a.work,a.font,a.reading_font)
    print(json.dumps({'subject_count':len(r['subjects']),'pdf_count':14,'build_seconds':r['build_seconds']},ensure_ascii=False))
