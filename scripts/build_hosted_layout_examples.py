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


def render_index(records):
    page=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
          '<title>下載七科題本與詳解版型</title><style>body{font:18px/1.7 system-ui,sans-serif;max-width:880px;margin:40px auto;padding:0 20px;color:#172126}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:12px;border-bottom:1px solid #ccd3d7}a{color:#07579b}small{font-size:15px}.download{display:inline-block;padding:9px 14px;background:#07579b;color:white;border-radius:6px;text-decoration:none;font-weight:600}.download:focus-visible{outline:3px solid #d57a00;outline-offset:3px}pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:18px;background:#f3f5f7;font:inherit}li{margin:8px 0}@media(max-width:560px){th,td{padding:8px 4px}.download{padding:8px;font-size:16px}}</style>',
          '<h1>下載七科題本與詳解版型</h1><p>出卷前，先下載當科的兩份 PDF，再一起附到 AI 對話，讓 AI 參考各大題的排版。</p>',
          '<ol><li>在下方找到科目，分別按「下載題本版型」和「下載詳解版型」。</li><li>回到已設定 Taiwan Exam 的 AI 對話，按「＋」或迴紋針，上傳剛下載的兩份 PDF。</li><li>貼上<a href="#prompt">本頁出卷文字</a>，將年份和科目改成需要的內容。</li></ol>',
          '<p>尚未設定 Taiwan Exam？先<a href="../../download-web-knowledge.html">下載知識檔</a>並加入 AI。若無法取得固定模板，再附上<a href="../../download-web-knowledge.html#templates">離線模板資源 PDF</a>。</p>',
          '<p>版型只供排版參考，內含占位材料、選項與圖框。題目、圖形和解答必須重新設計；示範題數、配分與留白不代表完整考卷。</p>',
          '<table><thead><tr><th scope="col">科目</th><th scope="col">題本版型</th><th scope="col">詳解版型</th></tr></thead><tbody>']
    for row in records:
        subject=html.escape(row['subject'])
        cells=[]
        for role,label in (('questions','題本'),('solutions','詳解')):
            record=row['booklets'][role];filename=html.escape(record['file'],quote=True)
            cells.append('<td><a class="download" href="'+filename+'" download="'+filename+'" aria-label="下載'+subject+label+'版型 PDF">下載'+label+'版型</a><br><small>'+str(record['pages'])+' 頁 · <a href="'+filename+'" target="_blank" rel="noopener">預覽 PDF</a></small></td>')
        page.append('<tr id="'+html.escape(row['slug'],quote=True)+'"><th scope="row">'+subject+'</th>'+''.join(cells)+'</tr>')
    page.extend(['</tbody></table>',
          '<h2 id="prompt">附上兩份 PDF 後，複製這段給 AI</h2>',
          '<pre>請依 Taiwan Exam Skill 出一份 116 學測數 A 完整模擬考。\n我已附上當科的題本版型與詳解版型 PDF，請先閱讀並參考各大題排版。\n範例只供排版參考，不可使用占位文字命題，也不要照抄示範題號、配分或留白。\n請依 Skill 取得並核對當科原始固定模板，重新命題、製圖、驗算與檢查難度。\n完成後逐頁檢查最終 PDF，分開交付題目 PDF 與答案詳解 PDF。</pre>',
          '<p>檔案通常存於電腦的「下載」資料夾。若按鈕仍開啟 PDF，請按閱讀器的下載圖示再上傳；不用下載其他科目。</p>',
          '<p><a href="https://github.com/niansia/taiwan-exam#readme">查看完整新手使用說明</a></p></html>'])
    return '\n'.join(page)+'\n'


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
    (output/'index.html').write_bytes(render_index(records).encode('utf-8'))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output','work','font'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--reading-font',type=Path)
    a=p.parse_args();r=build(a.output,a.work,a.font,a.reading_font)
    print(json.dumps({'subject_count':len(r['subjects']),'pdf_count':14,'build_seconds':r['build_seconds']},ensure_ascii=False))
