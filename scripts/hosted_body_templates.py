#!/usr/bin/env python3
"""Flow-layout components only. Never generate, select or reuse exam questions."""
from __future__ import annotations
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import inspect
from pathlib import Path
import re
import time

import pymupdf
from fetch_hosted_template_assets import DEFAULT_MAP
from hosted_item_layout import draw_rail

HTML_OPTIONS = {'_scale_word_width':False} if '_scale_word_width' in inspect.signature(pymupdf.Page.insert_htmlbox).parameters else {}

KINDS = ('section', 'choice', 'multiple', 'fill', 'constructed', 'stimulus', 'solution', 'passage', 'table')
CSS = '''
@font-face {font-family:Body;src:url(body-font.ttf)}
* {box-sizing:border-box} body {font-family:Body;font-size:11pt;line-height:1.65;margin:0;color:#000;background:transparent}
p {margin:0 0 5pt} table {border-collapse:collapse;width:100%;margin:0} td {padding:0 4pt 3pt 0;vertical-align:top}
.direction {border:0.6pt solid black;padding:3pt 5pt;font-size:12pt;line-height:1.3}
.heading {font-size:13pt;font-weight:bold;margin-bottom:4pt}
.number {width:24pt} .figure {text-align:center} .score {font-size:11pt}
sup,sub {font-size:70%} .options {margin-top:3pt}
.passage {font-family:Reading,Body} .english {font-family:Latin,Body}
.data td,.data th {border:0.6pt solid black;padding:5pt;text-align:left;font-weight:normal}
'''


class RichText(HTMLParser):
    """Only inline typographic tags; layout, images and CSS belong to components."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in {'sup','sub','i','em','b','strong','br'} or attrs:
            raise ValueError('Use only sup/sub/i/em/b/strong/br without attributes in rich text')
        self.output.append('<'+tag+'>')
        if tag != 'br': self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise ValueError('Unbalanced rich-text tags')
        self.output.append('</'+tag+'>')

    def handle_data(self, data): self.output.append(html.escape(data))


def text(value):
    if isinstance(value, dict) and set(value) == {'rich'}:
        parser = RichText(); parser.feed(value['rich']); parser.close()
        if parser.stack: raise ValueError('Unclosed rich-text tag')
        return ''.join(parser.output)
    if not isinstance(value, str): raise ValueError('Text must be a string or {rich: inline HTML}')
    if re.search(r'\\(?:frac|sqrt|begin|\()|\$\$', value):
        raise ValueError('Render complex math to a verified inline asset; do not print raw LaTeX')
    return html.escape(value).replace('\n','<br>')


def rail_image(number, rows):
    if not isinstance(rows,list) or not 1 <= len(rows) <= 2 or any(type(n) is not int or not 1<=n<=6 for n in rows):
        raise ValueError('Use one integer row or two fraction rows; specify other response forms as verified assets')
    width = max(rows)*28.98 + 4
    height = len(rows)*32.98 + 4
    with pymupdf.open() as doc:
        page = doc.new_page(width=width, height=height)
        ordinal = 1
        for index, count in enumerate(rows):
            # draw_rail starts row IDs at 1, so shift subsequent fraction labels
            # in this local body-only component before rasterizing.
            x = (width-count*28.98)/2
            reservation = {'bbox':[x,2+index*32.98,x+count*28.98,30.98+index*32.98]}
            if ordinal == 1:
                draw_rail(page,reservation,number,count)
            else:
                font=pymupdf.Font('tiro')
                for j in range(count):
                    cx=x+j*28.98+12.99;cy=2+index*32.98+12.99
                    label=f'{number}-{ordinal+j}';size=10.02
                    page.draw_circle((cx,cy),12.99,width=.7)
                    page.insert_text((cx-font.text_length(label,fontsize=size)/2,
                                      cy+size*(font.ascender+font.descender)/2),label,fontname='tiro',fontsize=size)
                page.draw_line((x,30.98+index*32.98),(x+count*28.98,30.98+index*32.98),width=.7)
            ordinal += count
        return page.get_pixmap(matrix=pymupdf.Matrix(4,4),alpha=True).tobytes('png'),width,height


def fragment(block, archive, asset_root, index, width=467.7, font_metric=None):
    kind=block.get('kind')
    if kind not in KINDS: raise ValueError('Unknown body block kind')
    if kind=='section':
        return f'<div class="heading">{text(block["title"])}</div><div class="direction">{text(block["directions"])}</div>'
    if kind=='passage':
        paragraphs=block.get('paragraphs',[])
        if not paragraphs:raise ValueError('Passage needs actual paragraphs')
        content=''.join('<p>'+text(p)+'</p>' for p in paragraphs)
        content=re.sub(r'\{\{gap:(\d{1,2})\}\}',r'<u>　\1　</u>',content)
        if '{{gap:' in content:raise ValueError('Invalid passage gap number')
        cls='english' if block.get('language')=='en' else 'passage'
        heading=f'<div class="heading">{text(block["heading"])}</div>' if block.get('heading') else ''
        bank=block.get('bank',[])
        if bank:
            columns=block.get('columns',2)
            if columns not in (1,2,5):raise ValueError('Unsupported option-bank columns')
            if columns==1:
                content+=''.join('<p>'+text(o['label'])+' '+text(o['text'])+'</p>' for o in bank)
            else:
                cells=[f'<td style="width:{100/columns}%">{text(o["label"])} {text(o["text"])}</td>' for o in bank]
                content+='<table>'+''.join('<tr>'+''.join(cells[i:i+columns])+'</tr>' for i in range(0,len(cells),columns))+'</table>'
        return heading+f'<div class="{cls}">{content}</div>'
    if kind=='table':
        headers=block.get('headers',[]);rows=block.get('rows',[])
        if not headers or not rows or any(len(r)!=len(headers) for r in rows):
            raise ValueError('Table rows must match nonempty headers')
        content='<tr>'+''.join('<th>'+text(c)+'</th>' for c in headers)+'</tr>'
        content+=''.join('<tr>'+''.join('<td>'+text(c)+'</td>' for c in r)+'</tr>' for r in rows)
        return '<p>'+text(block.get('text',''))+'</p><table class="data">'+content+'</table>'
    if kind!='stimulus' and (type(block.get('number')) is not int or block['number']<1):
        raise ValueError('Supply a positive integer question number')
    stem=text(block.get('text',''))
    if kind=='solution':
        if not block.get('steps'):raise ValueError('Supply actual authored solution steps')
        stem=''.join('<p>'+text(p)+'</p>' for p in [block.get('text',''),*block['steps']])
    if kind=='fill':
        if stem.count('{{answer}}')!=1: raise ValueError('Place exactly one {{answer}} at the semantic answer position')
        data,w,h=rail_image(block['number'],block['rows'])
        name=f'rail-{index}.png';archive.add((data,name))
        before,after=stem.split('{{answer}}')
        before=str(block['number'])+'. '+before
        font_metric=font_metric or pymupdf.Font('cjk')
        measure=lambda value:font_metric.text_length(html.unescape(re.sub('<[^>]*>','',value)),fontsize=11)+6
        after_width=min(160,max(18,measure(after)))
        before_width=min(width-w-16-after_width,measure(before))
        table_width=before_width+w+16+after_width
        stem=(f'<table style="width:{table_width}pt"><tr><td style="width:{before_width}pt;vertical-align:middle">{before}</td>'
              f'<td style="width:{w+8}pt;line-height:{h+4}pt"><img src="{name}" width="{w}" height="{h}"></td>'
              f'<td style="width:{after_width}pt;vertical-align:middle">{after}</td></tr></table>')
    elif '{{answer}}' in stem: raise ValueError('Answer position token requires a fill block')
    # Inline complex math/diagrams are supplied by the author, never by a stored
    # question or graph menu. Every referenced binary must match its saved hash.
    images={};image_heights={}
    for key,asset in block.get('assets',{}).items():
        path=(asset_root/asset['path']).resolve()
        if not path.is_relative_to(asset_root.resolve()): raise ValueError('Asset outside current run')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=asset['sha256']:raise ValueError('Changed body asset')
        asset_width=asset['width_pt']
        if type(asset_width) not in (int,float) or not 1<=asset_width<=460:raise ValueError('Invalid asset width')
        with pymupdf.open(stream=raw) as image_doc:
            rect=image_doc[0].rect
        height=asset_width*rect.height/rect.width
        name=f'asset-{index}-{len(images)}'+path.suffix
        archive.add((raw,name))
        images[key]=f'<img src="{name}" width="{asset_width}" height="{height}">'
        image_heights[key]=height
        stem=stem.replace('{{asset:'+key+'}}',images[key])
    if '{{asset:' in stem:raise ValueError('Missing inline asset')
    figure=block.get('figure')
    if figure:
        if figure not in images:raise ValueError('Figure must name a hash-verified asset')
        if kind not in {'stimulus','solution'}:stem=str(block.get('number',''))+'. '+stem
        image_box=f'<div style="line-height:{image_heights[figure]+4}pt">{images[figure]}</div>'
        if block.get('figure_position','below')=='right':
            if block['assets'][figure]['width_pt']>180:raise ValueError('Right-hand figure exceeds reserved column')
            stem=f'<table><tr><td style="width:{width-189}pt">{stem}</td><td style="width:185pt" class="figure">{image_box}</td></tr></table>'
        else:stem+=f'<div class="figure">{image_box}</div>'
    if kind in {'choice','multiple'}:
        options=block.get('options',[])
        if len(options)<2:raise ValueError('Choice block needs authored options')
        columns=block.get('columns',1)
        if columns not in (1,2,5):raise ValueError('Use 1, 2 or 5 option columns; never shrink font to fit')
        cells=[f'<td style="width:{100/columns}%">{html.escape(str(o["label"]))} {text(o["text"])}</td>' for o in options]
        stem+='<table class="options">'+''.join('<tr>'+''.join(cells[j:j+columns])+'</tr>' for j in range(0,len(cells),columns))+'</table>'
    if kind=='constructed':
        if type(block.get('score')) not in (int,float) or block['score']<=0:raise ValueError('Constructed response must show its actual positive score')
        stem+=f'（{block["score"]}分）'
    label=text(block['label']) if 'label' in block else (f'第{block["number"]}題' if kind=='solution' else str(block.get('number',''))+'.')
    if kind=='solution':return f'<div class="heading">{label}</div>'+stem
    if kind=='fill' or figure:return stem
    return stem if kind=='stimulus' else f'<table><tr><td class="number">{label}</td><td>{stem}</td></tr></table>'


def render(spec, output, layout_path, font, *, asset_root, proof=False, reading_font=None):
    started=time.monotonic()
    if output.exists() or layout_path.exists():raise ValueError('Use new output names; preserve previous reviewable bytes')
    if spec.get('purpose')=='layout-reference-only' and not proof:raise ValueError('Placeholder gallery cannot become a production exam')
    if not proof and any(str(b.get('id','')).startswith('layout-') for b in spec.get('blocks',[])):
        raise ValueError('Placeholder gallery IDs cannot become production questions')
    manifest=json.loads(DEFAULT_MAP.read_text(encoding='utf-8'))
    subject=next(s for s in manifest['subjects'] if s['subject']==spec['subject'])
    allowed=pymupdf.Rect(subject['overlay_geometry_pt']['body'])
    body=allowed+(4,4,-4,-4)
    archive=pymupdf.Archive();archive.add((font.read_bytes(),'body-font.ttf'))
    archive.add((pymupdf.Font('tiro').buffer,'latin-font.ttf'))
    css=CSS+'\n@font-face {font-family:Latin;src:url(latin-font.ttf)}'
    if reading_font:
        archive.add((reading_font.read_bytes(),'reading-font.ttf'))
        css+='\n@font-face {font-family:Reading;src:url(reading-font.ttf)}'
    blocks=spec['blocks']
    if not blocks:raise ValueError('No authored blocks')
    parts=[];pages=[]
    contents=[fragment(block,archive,asset_root,index,body.width,pymupdf.Font(fontfile=str(font))) for index,block in enumerate(blocks)]
    # Measure each whole block once using the SAME engine, width and font.
    # Production painting never clips, scales, or estimates height from lines.
    heights=[];tops=[]
    with pymupdf.open() as measure:
        for index,content in enumerate(contents):
            sample=measure.new_page(width=595.28,height=841.89)
            spare,scale=sample.insert_htmlbox(body,content,css=css,archive=archive,scale_low=1,**HTML_OPTIONS)
            if spare<0 or scale!=1:raise ValueError(f'Block {index} exceeds a page; explicitly split its continuation')
            native=sample.get_text('dict')['blocks']
            for text_block in sample.get_text('rawdict')['blocks']:
                for line in text_block.get('lines',[]):
                    for span in line['spans']:
                        for left,right in zip(span['chars'],span['chars'][1:]):
                            if (all(0x4e00<=ord(c['c'])<=0x9fff for c in (left,right)) and
                                abs(left['origin'][1]-right['origin'][1])<.1 and
                                right['origin'][0]-left['origin'][0]<span['size']*.75):
                                raise ValueError('Font collapses adjacent CJK glyph advances; use a verified compatible font')
            ink=[pymupdf.Rect(b['bbox']) for b in native]
            if any(not allowed.contains(rect) for rect in ink):
                raise ValueError(f'Block {index}: actual painted content exceeds the body')
            native=sample.get_text('dict')['blocks']
            images=[pymupdf.Rect(b['bbox']) for b in native if b['type']==1]
            spans=[pymupdf.Rect(s['bbox']) for b in native for line in b.get('lines',[]) for s in line['spans']]
            if any((a & b).width>1 and (a & b).height>1 for a in images for b in spans):
                raise ValueError(f'Block {index}: image overlaps actual text; use a reserved figure block')
            tops.append(min(0,min((r.y0-body.y0 for r in ink),default=0))-1)
            heights.append(max(20,body.height-spare,max((r.y1-body.y0+2 for r in ink),default=0)))
    with pymupdf.open() as doc:
        page=doc.new_page(width=595.28,height=841.89);y=body.y0
        for index,(block,content,used) in enumerate(zip(blocks,contents,heights)):
            required=used
            following=index
            while blocks[following]['kind']=='section' or blocks[following].get('keep_with_next'):
                gap=8 if blocks[following]['kind']=='section' else 12
                following+=1
                if following==len(blocks):raise ValueError('A kept heading or block must precede content')
                required+=gap+heights[following]
            if required>body.height:raise ValueError('Section and following item exceed page; split the item explicitly')
            if y+required>body.y1:
                page=doc.new_page(width=595.28,height=841.89);y=body.y0
            rect=pymupdf.Rect(body.x0,y,body.x1,body.y1)
            spare,scale=page.insert_htmlbox(rect,content,css=css,archive=archive,scale_low=1,**HTML_OPTIONS)
            if spare<0 or scale!=1:raise ValueError(f'Block {index} does not fit at full font size')
            box=[allowed.x0,y+tops[index],allowed.x1,y+used]
            if block['kind']!='section':
                ids=block.get('ids') or [block['id']]
                if len(ids)!=1:raise ValueError('Assign a shared block one owner ID; avoid overlapping crop parts')
                parts.append({'id':ids[0],'page':len(doc),'bbox':box,
                              'components':[{'role':'flow-content','bbox':box}]})
            pages.append({'block':index,'kind':block['kind'],'page':len(doc),'bbox':box})
            y+=used+(8 if block['kind']=='section' else 12)
        output.parent.mkdir(parents=True,exist_ok=True)
        raw=doc.tobytes(garbage=4,deflate=True);output.write_bytes(raw)
    layout={'pdf_sha256':hashlib.sha256(raw).hexdigest(),'parts':parts,'blocks':pages,
            'scope':'Body layout only; compose onto original fixed PDFs and perform actual QA',
            'elapsed_seconds':round(time.monotonic()-started,3)}
    layout_path.parent.mkdir(parents=True,exist_ok=True)
    layout_path.write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
    return layout


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('spec',type=Path)
    for name in ('output','layout','font'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--proof',action='store_true')
    p.add_argument('--reading-font',type=Path)
    args=p.parse_args()
    result=render(json.loads(args.spec.read_text(encoding='utf-8')),args.output,args.layout,args.font,
                  asset_root=args.spec.resolve().parent,proof=args.proof,reading_font=args.reading_font)
    print(json.dumps({'body_pdf':str(args.output),'layout':str(args.layout),'elapsed_seconds':result['elapsed_seconds']}))
