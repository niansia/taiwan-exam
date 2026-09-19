#!/usr/bin/env python3
"""Flow-layout components only. Never generate, select or reuse exam questions."""
from __future__ import annotations
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import inspect
import math
from pathlib import Path
import re
import time

import pymupdf
from fetch_hosted_template_assets import DEFAULT_MAP
from hosted_item_layout import draw_rail

HTML_OPTIONS = {'_scale_word_width':False} if '_scale_word_width' in inspect.signature(pymupdf.Page.insert_htmlbox).parameters else {}

KINDS = ('section', 'choice', 'multiple', 'fill', 'constructed', 'stimulus', 'solution', 'passage', 'table')
# Blocks and crop edges sit on a 0.5 pt grid (one pixel at the 2 px/pt review
# scale), so crops carry no partial-pixel clip noise and a proof crop matches the
# final crop of the same block. Figure leading adds 0.025 pt so image edges avoid
# device-pixel boundaries, where float32 noise otherwise flips image gridfitting.
BLOCK_GRID_PT = 0.5
FIGURE_LEADING_PT = 4.05
# A last page filled below this fraction triggers a retry with closer blocks.
TRAILING_PAGE_FILL = 0.2
TIGHTER_GAPS = (0.75, 0.5)
OPTION_COLUMNS = (1, 2, 3, 4, 5)


def snap_block_top(value):
    return math.ceil(value / BLOCK_GRID_PT - 1e-9) * BLOCK_GRID_PT


# MuPDF applies a cell's vertical-align to every inline run inside it: top-aligned
# text cells flattened <sup> onto the baseline, so T<sup>2</sup> printed like a
# subscript. Text cells align first baselines instead; figure cells stay on top.
CSS = '''
@font-face {font-family:Body;src:url(body-font.ttf)}
* {box-sizing:border-box} body {font-family:Body;font-size:11pt;line-height:1.65;margin:0;color:#000;background:transparent}
p {margin:0 0 5pt} table {border-collapse:collapse;width:100%;margin:0} td {padding:0 4pt 3pt 0;vertical-align:baseline}
td.figure {vertical-align:top}
.direction {border:0.6pt solid black;padding:3pt 5pt;font-size:12pt;line-height:1.3}
.heading {font-size:13pt;font-weight:bold;margin-bottom:4pt}
.number {width:24pt} .figure {text-align:center} .score {font-size:11pt}
sup,sub {font-size:70%} .options {margin-top:3pt}
.passage {font-family:Reading,Body} .english {font-family:Latin,Body}
.data td,.data th {border:0.6pt solid black;padding:5pt;text-align:left;font-weight:normal}
.group-label {font-weight:bold;margin-bottom:3pt} .group-label.underline {font-weight:normal;text-decoration:underline}
p.indent {text-indent:2em;text-align:justify} .english .score {font-family:Body}
'''
# Long text may continue on the next page at paragraph (or solution-step)
# boundaries when a block opts in with split: paragraphs. The label/heading
# stays with the first piece; options, bank, figure and score with the last.
SPLITTABLE = {'stimulus', 'passage', 'constructed', 'solution', 'choice', 'multiple'}
PARAGRAPH_BREAK = re.compile(r'\n\s*\n|(?:<br>\s*){2,}')


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


def fragment(block, archive, asset_root, index, width=467.7, font_metric=None, scaled=None):
    """Resolve verified inline assets after ALL authored fields are escaped.

    Choices, table cells, passages and solution steps use the same substitution
    as stems. Resolving only stems silently printed formula tokens in options
    and skipped early-return blocks, forcing callers to rebuild valid layouts.
    """
    images={};image_heights={}
    # Numbered blocks print beside a 28pt number column plus cell padding.
    column_width=width-32 if block.get('kind') in {'choice','multiple','constructed','solution'} else width
    for key,asset in block.get('assets',{}).items():
        path=(asset_root/asset['path']).resolve()
        if not path.is_relative_to(asset_root.resolve()): raise ValueError('Asset outside current run')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=asset['sha256']:raise ValueError('Changed body asset')
        asset_width=asset['width_pt']
        if type(asset_width) not in (int,float) or not 1<=asset_width<=460:raise ValueError('Invalid asset width')
        if asset_width>column_width:
            # A figure wider than its text column would overflow the body; print
            # it at the column width instead of failing after a full render.
            if scaled is not None:
                scaled[(index,key)]={'block':index,'asset':key,'requested_pt':asset_width,'printed_pt':round(column_width,2)}
            asset_width=column_width
        extension=path.suffix
        with pymupdf.open(stream=raw) as image_doc:
            rect=image_doc[0].rect
            if image_doc.is_pdf:
                if len(image_doc)!=1:raise ValueError('Inline body PDF asset must have exactly one page')
                # MuPDF's HTML img does not render PDF sources: without this it
                # silently prints [image]. Convert only newly authored body
                # artwork, never the immutable fixed-template PDF layers.
                scale=3*asset_width/rect.width
                raw=image_doc[0].get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=True).tobytes('png')
                extension='.png'
        height=asset_width*rect.height/rect.width
        name=f'asset-{index}-{len(images)}'+extension
        archive.add((raw,name))
        images[key]=f'<img src="{html.escape(name,quote=True)}" width="{asset_width}" height="{height}">'
        image_heights[key]=height
    content=_fragment_html(block,archive,index,width,font_metric,images,image_heights)
    for key,image in images.items():
        content=content.replace(html.escape('{{asset:'+key+'}}'),image)
    if '{{asset:' in content:raise ValueError('Missing inline asset')
    return content


def _group_label(block):
    if not block.get('group_label') or not block.get('_head', True):
        return ''
    style = block.get('group_label_style', 'bold')
    if style not in {'bold', 'underline'}: raise ValueError('group_label_style must be bold or underline')
    return f'<div class="group-label{" underline" if style=="underline" else ""}">{text(block["group_label"])}</div>'


def _fragment_html(block, archive, index, width, font_metric, images, image_heights):
    kind=block.get('kind')
    if kind not in KINDS: raise ValueError('Unknown body block kind')
    head,tail=block.get('_head',True),block.get('_tail',True)
    if kind=='section':
        heading=f'<div class="heading">{text(block["title"])}</div>'
        # Answer booklets may print a plain part heading; question-booklet
        # directions stay explicit and are never invented here.
        if 'directions' not in block:return heading
        return heading+f'<div class="direction">{text(block["directions"])}</div>'
    if kind=='passage':
        paragraphs=block.get('paragraphs',[])
        if not paragraphs:raise ValueError('Passage needs actual paragraphs')
        def paragraph(value):
            plain=value['rich'] if isinstance(value,dict) else value
            # Source lines and option/bank rows are never first-line indented.
            indent=block.get('indent') and not re.match(r'\s*[(（]',str(plain))
            return ('<p class="indent">' if indent else '<p>')+text(value)+'</p>'
        content=''.join(paragraph(p) for p in paragraphs)
        content=re.sub(r'\{\{gap:(\d{1,2})\}\}',r'<u>　\1　</u>',content)
        if '{{gap:' in content:raise ValueError('Invalid passage gap number')
        cls='english' if block.get('language')=='en' else 'passage'
        heading=f'<div class="heading">{text(block["heading"])}</div>' if block.get('heading') and head else ''
        bank=block.get('bank',[]) if tail else []
        if bank:
            columns=block.get('columns',2)
            if columns not in (1,2,5):raise ValueError('Unsupported option-bank columns')
            if columns==1:
                content+=''.join('<p>'+text(o['label'])+' '+text(o['text'])+'</p>' for o in bank)
            else:
                cells=[f'<td style="width:{100/columns}%">{text(o["label"])} {text(o["text"])}</td>' for o in bank]
                content+='<table>'+''.join('<tr>'+''.join(cells[i:i+columns])+'</tr>' for i in range(0,len(cells),columns))+'</table>'
        return _group_label(block)+heading+f'<div class="{cls}">{content}</div>'
    if kind=='table':
        headers=block.get('headers',[]);rows=block.get('rows',[])
        if not headers or not rows or any(len(r)!=len(headers) for r in rows):
            raise ValueError('Table rows must match nonempty headers')
        content='<tr>'+''.join('<th>'+text(c)+'</th>' for c in headers)+'</tr>'
        content+=''.join('<tr>'+''.join('<td>'+text(c)+'</td>' for c in r)+'</tr>' for r in rows)
        return '<p>'+text(block.get('text',''))+'</p><table class="data">'+content+'</table>'
    numbered=type(block.get('number')) is int and block['number']>=1
    if kind!='stimulus' and not numbered and not (kind in {'choice','multiple','constructed','solution'} and 'label' in block):
        raise ValueError('Supply a positive integer question number, or a printed label for an unnumbered task')
    stem=text(block.get('text',''))
    if kind=='solution':
        steps=block.get('steps')
        if not steps:raise ValueError('Supply actual authored solution steps')
        stem=''.join('<p>'+text(p)+'</p>' for p in [*([block.get('text','')] if head else []),*steps])
    if kind=='fill':
        if stem.count('{{answer}}')!=1: raise ValueError('Place exactly one {{answer}} at the semantic answer position')
        data,w,h=rail_image(block['number'],block['rows'])
        name=f'rail-{index}.png';archive.add((data,name))
        before,after=stem.split('{{answer}}')
        # Use paragraph flow: MuPDF top-aligned table cells paint their inline
        # image below the text despite a valid non-colliding bounding box.
        rail=f'<img src="{name}" width="{w}" height="{h}" style="vertical-align:middle">'
        prefix=re.search(r'([A-Za-zα-ωΑ-Ω][A-Za-z0-9_]*\s*[=＝]\s*)$',before)
        if prefix:
            stem=before[:prefix.start()]+f'<span style="white-space:nowrap">{prefix.group(0)}{rail}</span>'+after
        else:stem=before+rail+after
    elif '{{answer}}' in stem: raise ValueError('Answer position token requires a fill block')
    if 'label' in block:
        label=text(block['label']) if head else ''
    elif kind=='solution':
        label=f'第{block["number"]}題'
    else:
        label=f'{block["number"]}.' if head and numbered else ''
    if kind=='constructed':
        score=block.get('score')
        if type(score) not in (int,float) or score<=0:raise ValueError('Constructed response must show its actual positive score')
        if block.get('score_in_text'):
            # The authored text already prints the official score wording,
            # possibly the whole printed question's total across subparts.
            printed_score=block.get('printed_score',score)
            if not block.get('_score_checked') and not re.search(rf'(?<![0-9.]){printed_score:g}\s*分',html.unescape(re.sub('<[^>]+>','',stem))):
                raise ValueError('score_in_text requires the printed text to state the actual score')
        elif tail:
            # The score closes the item text, before any figure or response area.
            stem+=f'<span class="score">（{score:g}分）</span>'
    figure=block.get('figure') if tail else None
    column=kind in {'choice','multiple','constructed'}
    if figure:
        if figure not in images:raise ValueError('Figure must name a hash-verified asset')
        image_box=f'<div style="line-height:{image_heights[figure]+FIGURE_LEADING_PT:g}pt">{images[figure]}</div>'
        if block.get('figure_position','below')=='right':
            if kind=='fill':raise ValueError('Fill figures use below placement; keep answer rails in paragraph flow')
            if block['assets'][figure]['width_pt']>180:raise ValueError('Right-hand figure exceeds reserved column')
            # Numbered items keep their hanging number column beside the pair.
            text_width=width-189-(28 if column else 0)
            stem=f'<table><tr><td style="width:{text_width:g}pt">{stem}</td><td style="width:185pt" class="figure">{image_box}</td></tr></table>'
        elif kind=='fill':
            stem=f'<p style="margin-left:28pt;text-indent:-28pt">{label}　{stem}</p><div class="figure">{image_box}</div>'
        else:stem+=f'<div class="figure">{image_box}</div>'
    if kind in {'choice','multiple'} and tail:
        options=block.get('options',[])
        if len(options)<2:raise ValueError('Choice block needs authored options')
        columns=block.get('columns',1)
        if columns not in OPTION_COLUMNS:raise ValueError('Use 1-5 option columns; never shrink font to fit')
        if not stem.strip() and not figure and head:
            # Option-only rows (English cloze): the number shares the first
            # option row so both sit on one baseline.
            cells=[f'<td style="width:{(width-28)/columns:g}pt">{html.escape(str(o["label"]))} {text(o["text"])}</td>' for o in options]
            rows=[''.join(cells[j:j+columns]) for j in range(0,len(cells),columns)]
            result=('<table class="options">'+''.join(f'<tr><td class="number">{label if n==0 else ""}</td>{row}</tr>'
                                                     for n,row in enumerate(rows))+'</table>')
            return f'<div class="english">{result}</div>' if block.get('language')=='en' else result
        cells=[f'<td style="width:{100/columns}%">{html.escape(str(o["label"]))} {text(o["text"])}</td>' for o in options]
        stem+='<table class="options">'+''.join('<tr>'+''.join(cells[j:j+columns])+'</tr>' for j in range(0,len(cells),columns))+'</table>'
    if kind=='solution':
        result=(f'<div class="heading">{label}</div>' if head else '')+stem
    elif kind=='fill':
        result=stem if figure else f'<p style="margin-left:28pt;text-indent:-28pt">{label}　{stem}</p>'
    elif kind=='stimulus':
        result=_group_label(block)+stem
    else:
        # An explicit stem width keeps option rows full width when the stem is
        # empty (English cloze option rows print only their number).
        result=f'<table><tr><td class="number">{label}</td><td style="width:{width-28:g}pt">{stem}</td></tr></table>'
    return f'<div class="english">{result}</div>' if block.get('language')=='en' else result


def _units(block):
    """Paragraph/step units of a block that opted into page continuation."""
    if block.get('split')!='paragraphs' or block['kind'] not in SPLITTABLE:
        return None,[]
    if block['kind']=='passage':
        return 'paragraphs',list(block.get('paragraphs',[]))
    if block['kind']=='solution':
        return 'steps',list(block.get('steps',[]))
    if block.get('figure'):
        return None,[]  # A figure keeps its measured place with the item.
    value=block.get('text','')
    rich=isinstance(value,dict)
    pieces=[piece for piece in PARAGRAPH_BREAK.split(value['rich'] if rich else value) if piece.strip()]
    if rich:
        try:
            for piece in pieces:text({'rich':piece})
        except ValueError:
            return None,[]  # An inline tag spanning paragraphs cannot be divided.
        pieces=[{'rich':piece} for piece in pieces]
    return 'text',pieces


def _chunk(block,key,units,head,tail):
    chunk={k:v for k,v in block.items() if k!='keep_with_next' or tail}
    chunk.update(_head=head and block.get('_head',True),_tail=tail and block.get('_tail',True),_score_checked=True)
    if key=='text':
        if isinstance(units[0],dict):
            chunk['text']={'rich':'<br><br>'.join(unit['rich'] for unit in units)}
        else:
            chunk['text']='\n\n'.join(units)
    else:
        chunk[key]=units
    return chunk


def render(spec, output, layout_path, font, *, asset_root, proof=False, reading_font=None, balance_last_page=True):
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
    if not spec['blocks']:raise ValueError('No authored blocks')
    font_metric=pymupdf.Font(fontfile=str(font))
    blocks=[]
    for index,block in enumerate(spec['blocks']):
        if block['kind']!='section':
            ids=block.get('ids') or [block['id']]
            if len(ids)!=1:raise ValueError('Assign a shared block one owner ID; list other printed items in covers')
            covers=block.get('covers',[])
            if (not isinstance(covers,list) or len(set(covers))!=len(covers) or ids[0] in covers or
                    any(not isinstance(item,str) or not item.strip() for item in covers)):
                raise ValueError(f'Block {index}: covers must list other distinct item IDs printed in this block')
        blocks.append({**block,'_source':index})
    prepared={};scaled={}
    measure=pymupdf.open()

    def prepare(block):
        """Measure a whole block or piece once with the SAME engine, width and font.

        Production painting never clips, scales, or estimates height from lines.
        A block taller than a page reports infinite height so it can continue.
        """
        # Content key, not id(): discarded trial pieces must never alias.
        key=json.dumps(block,sort_keys=True,ensure_ascii=False)
        if key in prepared:return prepared[key]
        index=block['_source']
        content=fragment(block,archive,asset_root,index,body.width,font_metric,scaled)
        sample=measure.new_page(width=595.28,height=841.89)
        spare,scale=sample.insert_htmlbox(body,content,css=css,archive=archive,scale_low=1,**HTML_OPTIONS)
        if spare<0 or scale!=1:
            prepared[key]=(content,0,math.inf)
            return prepared[key]
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
        images=[pymupdf.Rect(b['bbox']) for b in native if b['type']==1]
        spans=[pymupdf.Rect(s['bbox']) for b in native for line in b.get('lines',[]) for s in line['spans']]
        if any((a & b).width>1 and (a & b).height>1 for a in images for b in spans):
            raise ValueError(f'Block {index}: image overlaps actual text; use a reserved figure block')
        top=min(0,min((r.y0-body.y0 for r in ink),default=0))-1
        prepared[key]=(content,top,max(20,body.height-spare,max((r.y1-body.y0+2 for r in ink),default=0)))
        return prepared[key]

    def split_to_fit(block,available):
        """Largest leading paragraphs that fit; None keeps the block whole."""
        key,units=_units(block)
        # A short remainder is left blank rather than stranding one line.
        if available<body.height*.12:
            return None
        for count in range(len(units)-1,0,-1):
            first=_chunk(block,key,units[:count],True,False)
            if prepare(first)[2]<=available:
                return [first,_chunk(block,key,units[count:],False,True)]
        return None

    def paginate(tightness):
        """One pagination pass. Only the gaps between blocks scale with tightness."""
        def gap_after(block):
            return (8 if block['kind']=='section' else 12)*tightness

        work=list(blocks)
        parts=[];pages=[]
        with pymupdf.open() as doc:
            top=snap_block_top(body.y0)
            page=doc.new_page(width=595.28,height=841.89);y=top
            fresh_page=True
            i=0
            while i<len(work):
                y=snap_block_top(y)
                chain=[work[i]]
                while chain[-1]['kind']=='section' or chain[-1].get('keep_with_next'):
                    if i+len(chain)==len(work):raise ValueError('A kept heading or block must precede content')
                    chain.append(work[i+len(chain)])
                heights=[prepare(block)[2] for block in chain]
                # A kept block may start up to one grid step lower.
                required=sum(heights)+sum(gap_after(block)+BLOCK_GRID_PT for block in chain[:-1])
                if y+required>body.y1:
                    # Fill this page with leading paragraphs of the first block in
                    # the kept chain that allows continuation, instead of leaving
                    # a terminal void or failing on an over-long block.
                    offset=0;split=None
                    for position,block in enumerate(chain):
                        if _units(block)[1]:
                            split=split_to_fit(block,body.y1-y-offset)
                            if split:
                                work[i+position:i+position+1]=split
                            break
                        if heights[position]==math.inf:break
                        offset+=heights[position]+gap_after(block)+BLOCK_GRID_PT
                    if split:continue
                    if not fresh_page:
                        page=doc.new_page(width=595.28,height=841.89);y=top;fresh_page=True
                        continue
                    if math.inf in heights:
                        raise ValueError(f'Block {chain[heights.index(math.inf)]["_source"]} exceeds a page; explicitly split its continuation')
                    raise ValueError('Section and following item exceed page; split the item explicitly')
                block=work[i]
                content,block_top,used=prepare(block)
                rect=pymupdf.Rect(body.x0,y,body.x1,body.y1)
                spare,scale=page.insert_htmlbox(rect,content,css=css,archive=archive,scale_low=1,**HTML_OPTIONS)
                if spare<0 or scale!=1:raise ValueError(f'Block {block["_source"]} does not fit at full font size')
                # Crop edges on the same grid avoid partial-pixel clip noise.
                box=[math.floor(allowed.x0/BLOCK_GRID_PT)*BLOCK_GRID_PT,
                     math.floor((y+block_top)/BLOCK_GRID_PT+1e-9)*BLOCK_GRID_PT,
                     math.ceil(allowed.x1/BLOCK_GRID_PT)*BLOCK_GRID_PT,
                     snap_block_top(y+used)]
                piece='whole' if block.get('_head',True) and block.get('_tail',True) else (
                    'first' if block.get('_head',True) else 'last' if block.get('_tail',True) else 'middle')
                if block['kind']!='section':
                    owner=(block.get('ids') or [block['id']])[0]
                    covers=sorted(block.get('covers',[]))
                    previous=parts[-1] if parts else None
                    if (previous and pages and pages[-1]['kind']!='section' and previous['page']==len(doc) and
                            previous['id']==owner and previous.get('covers',[])==covers):
                        # One crop per owner per page: shared material and its
                        # item, or paragraphs continued on the same page.
                        previous['bbox']=[min(previous['bbox'][0],box[0]),min(previous['bbox'][1],box[1]),
                                          max(previous['bbox'][2],box[2]),max(previous['bbox'][3],box[3])]
                        previous['components'].append({'role':'flow-content','bbox':box})
                    else:
                        part={'id':owner,'page':len(doc),'bbox':box,'components':[{'role':'flow-content','bbox':box}]}
                        if covers:part['covers']=covers
                        parts.append(part)
                pages.append({'block':block['_source'],'kind':block['kind'],'piece':piece,'page':len(doc),'bbox':box})
                y+=used+gap_after(block)
                fresh_page=False
                i+=1
            last=max(row['bbox'][3] for row in pages if row['page']==len(doc))
            return doc.tobytes(garbage=4,deflate=True),parts,pages,len(doc),(last-top)/body.height

    try:
        raw,parts,pages,count,fill=paginate(1)
        tightness=1
        if balance_last_page and count>1 and fill<TRAILING_PAGE_FILL:
            # A last page holding a line or two fails the density check and costs
            # a rewrite; closer block spacing may pull it back onto earlier pages.
            for trial in TIGHTER_GAPS:
                attempt=paginate(trial)
                if attempt[3]<count:
                    raw,parts,pages,count,fill=attempt;tightness=trial
                    break
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(raw)
    finally:
        measure.close()
    layout={'pdf_sha256':hashlib.sha256(raw).hexdigest(),'parts':parts,'blocks':pages,
            'gap_scale':tightness,'scaled_assets':[scaled[key] for key in sorted(scaled)],
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
