"""Measured 115 typography proof. Does not certify content or full-paper fidelity."""
import argparse
import json
import re
import subprocess
import tempfile
import html as html_lib
from pathlib import Path
import pymupdf
import render_gsat_official
from render_gsat_official import render
from render_pdf import find_browser
from pdf_provenance import publish_pdf

STYLE = '''
@page { size:A4; margin:31mm 22.5mm 22mm; }
@font-face {font-family:ExamKai;src:local("DFKai-SB")}
@font-face {font-family:ExamMing;src:local("PMingLiU")}
html {font-family:"Times New Roman",ExamMing,serif;color:#000}
body {font-size:BODYPTpt;line-height:18pt}
.cover {height:240mm;min-height:0;padding:0; font-family:ExamKai,serif}
.brand,.mock-title {font-size:19.92pt;letter-spacing:0;margin:1mm 0 5mm}
.brand {font-size:16pt}
.subject-name {font-size:28pt;font-weight:normal;letter-spacing:0;margin:10mm 0 9mm}
.notice {font-size:13.92pt;line-height:20pt;background:#ddd;text-decoration:none;margin:0 0 6mm}
.notice-box {width:100%;padding:6mm 12mm;border:1.4pt solid black;font-size:11.04pt;line-height:18pt}
.notice-box h2 {font-size:13.92pt;letter-spacing:0;margin:0 0 4mm}
.notice-box p {margin:0 0 3mm}.notice-box ul {margin:0 0 3mm 1.5em}
.notice-box li {margin:0 0 1mm}
.internal-mark {bottom:0;font-size:9pt;font-family:ExamMing,serif}
.paper {padding:0}
.section-title {font-family:ExamKai,serif;font-size:13.92pt;line-height:21pt;margin:0 0 2mm;break-after:avoid}
.section-rule {font-family:ExamKai,serif;font-size:11.04pt;line-height:17pt;padding:.5mm 1mm;margin:0 0 2mm;border:.6pt solid black;break-after:avoid}
.section {margin:0 0 3mm}
.section-subtitle {font-family:ExamKai,serif;font-size:13.92pt;line-height:21pt;margin:0 0 2mm}
.group-label {font-weight:normal;margin:2mm 0 1mm;text-decoration:underline;break-after:avoid}
.stimulus {font-family:STIMFONT;font-size:BODYPTpt;line-height:18pt;white-space:normal;margin:0 0 2mm 7mm;orphans:3;widows:3}
.question {margin:0 0 2mm;gap:1mm;line-height:18pt}
.option {break-inside:avoid-page}
.qno {font-weight:normal}.prompt{text-align:justify}
.score {float:none;font-size:BODYPTpt;color:black;white-space:nowrap;display:inline-block}
.answer-summary th:nth-child(3),.answer-summary td:nth-child(3) {white-space:nowrap}
.options {gap:0 4mm;margin-top:0;grid-auto-flow:row}
.option {line-height:18pt;grid-template-columns:6mm 1fr}
.figure {margin:2mm auto;break-inside:avoid}
.figure img {max-height:none;width:100%;height:auto}
.figure figcaption {font-size:10pt;line-height:15pt}
.answer-lines {display:none}
.trace {display:none}
.answer-key {font-size:11.04pt;line-height:18pt}
.answer-key h1 {font-family:ExamKai,serif;font-size:16pt}
.answer-summary {font-size:11.04pt;line-height:17pt}
.answer-summary {table-layout:fixed}
.answer-summary td:first-child,.answer-summary th:first-child {width:13mm}
.answer-summary td:last-child,.answer-summary th:last-child {width:20mm}
.question-continuation {margin:0 0 2mm 7mm}
.answer-summary td,.answer-summary th {padding:1mm 2mm}
.details {columns:1;column-rule:none}
.solution {break-inside:avoid-page;margin-bottom:3mm}
.solution h2 {font-size:11.04pt;line-height:18pt}
'''

def instruction_box(duration):
    return f'''<div class="notice-box"><h2>－作答注意事項－</h2>
<p>考試時間： {duration} 分鐘</p><p>作答方式：</p><ul>
<li>選擇題用 2B 鉛筆在「答題卷」上作答；更正時以橡皮擦擦拭，切勿使用修正帶（液）。</li>
<li>除題目另有規定外，非選擇題用筆尖較粗之黑色墨水的筆在「答題卷」上作答；更正時，可以使用修正帶（液）。</li>
<li>考生須依上述規定劃記或作答，若未依規定而導致答案難以辨識或評閱時，恐將影響成績。</li>
<li>答題卷每人一張，不得要求增補。</li></ul><p>選擇題計分方式：</p><ul>
<li>單選題：每題有 <i>n</i> 個選項，其中只有一個是正確或最適當的選項。各題答對者，得該題的分數；答錯、未作答或劃記多於一個選項者，該題以零分計算。</li>
<li>多選題：每題有 <i>n</i> 個選項，其中至少有一個是正確的選項。各題之選項獨立判定，所有選項均答對者，得該題全部的分數；答錯 <i>k</i> 個選項者，得該題 <span style="display:inline-flex;vertical-align:middle;flex-direction:column;text-align:center;line-height:13pt"><span style="border-bottom:.6pt solid black"><i>n</i> − 2<i>k</i></span><span><i>n</i></span></span> 的分數；但得分低於零分或所有選項均未作答者，該題以零分計算。</li></ul></div>'''

def add_furniture(doc,subject,answers=False):
    archive=pymupdf.Archive('C:/Windows/Fonts')
    css='@font-face{font-family:Kai;src:url(kaiu.ttf)}@font-face{font-family:Ming;src:url(mingliu.ttc)}body{font-family:Ming;font-size:11pt;line-height:14pt;margin:0}'
    # Cover is unnumbered. Pagination follows booklet content, including appended solutions.
    for index in range(0 if answers else 1,len(doc)):
        page=doc[index];n=index+1 if answers else index
        count=f'第 {n} 頁<br>共 {len(doc) if answers else len(doc)-1} 頁'
        label='116年學測模擬<br>'+('國語文綜合能力測驗' if subject=='國綜' else '自然考科')
        if answers:label='116年學測模擬<br>'+subject+'答案與解析'
        left,right=(count,label) if n%2 else (label,count)
        for rect,html in [(pymupdf.Rect(63.8,42,193,72),left),(pymupdf.Rect(411,42,532,72),f'<div style="text-align:right">{right}</div>')]:
            spare,scale=page.insert_htmlbox(rect,html,css=css,archive=archive,scale_low=1)
            if spare<0:raise ValueError('header does not fit')
        reminder='答案與評分參考' if answers else '請記得在答題卷簽名欄位以正楷簽全名'
        page.insert_htmlbox(pymupdf.Rect(194,40,406,61),f'<div style="font-family:Kai;font-size:10.5pt;background:#ddd;text-align:center">{reminder}</div>',css=css,archive=archive,scale_low=1)
        x=63.8 if n%2 else 505
        page.insert_text((x,800),f'- {n} -',fontname='tiro',fontsize=10)

def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);p.add_argument('--answers',action='store_true');p.add_argument('--no-provenance',action='store_true');a=p.parse_args()
    exam=json.loads(a.input.read_text(encoding='utf-8-sig'))
    subject=exam['metadata'].get('paper_subject') or exam['metadata']['subject']
    if subject not in ['國綜','自然']:raise ValueError('This profile only supports 國綜 / 自然')
    exam['metadata']['layout_css_override']=STYLE.replace('BODYPT','11.04' if subject=='國綜' else '10.98').replace('STIMFONT','"Times New Roman",ExamKai,serif' if subject=='國綜' else '"Times New Roman",ExamMing,serif')
    if subject=='國綜':
        exam['metadata']['layout_css_override']+='\nbody,.question,.option,.stimulus{line-height:17pt}.question{margin-bottom:1.5mm}.stimulus{margin-bottom:0;text-indent:2em}.stimulus.continued-paragraph{text-indent:0}.stimulus.source-line{text-indent:0;text-align:right;margin-bottom:1mm}'
    for q in exam['questions']:
        q['answer_space_lines']=0
        q['allow_page_split']=False
    render_gsat_official.option_columns=lambda options,sub: (5 if len(options)==5 and max(len(o.get('text','')) for o in options)<=6 else (1 if max((len(o.get('text','')) for o in options),default=0)>(34 if sub=='國綜' else 18) or (sub=='自然' and len(options)==5) else 2))
    original_text=render_gsat_official.text_block
    render_gsat_official.text_block=lambda value: re.sub(r'10\^(-?\d+(?:\.\d+)?)',r'10<sup>\1</sup>',original_text(value)).replace('[H+]','[H⁺]')
    html=render(exam,include_answers=a.answers,asset_base=a.input.resolve().parent)
    if a.answers:
        html=html.replace('<th>難度</th>','<th>估計難度</th>')
        html=html.replace('<h1>答案與解析</h1>','<h1>答案與解析<br><span style="font-family:ExamMing;font-size:10pt;font-weight:normal">難度為命題估計，未經考生預試；非實測答對率。</span></h1>')
    html=re.sub(r'<div class="notice-box">.*?</div><div class="internal-mark">',instruction_box(exam['metadata']['duration_minutes'])+'<div class="internal-mark">',html,flags=re.S)
    html=html.replace('版式參照 115 學年度正式題本｜內容原創｜禁止對外冒充正式試題','排版修訂校樣｜非正式試題｜作答請另備答題卷')
    html=re.sub(r'<span class="score">(.*?)</span>(.*?)(?=</div>)',r'\2<span class="score">\1</span>',html)
    if subject=='國綜':
        html=html.replace('第壹部分、一、單選題（占48分）','第壹部分、選擇題（占76分）</h1><h2 class="section-subtitle">一、單選題（占48分）')
        html=html.replace('第壹部分、二、多選題（占28分）','二、多選題（占28分）')
    # Uniformly scored selection items need section-level scores only.
    sections=html.split('<section class="section">')
    for i in range(1,len(sections)):
        if '第貳部分' not in sections[i].split('</h1>',1)[0]:
            sections[i]=re.sub(r'<span class="score">.*?</span>','',sections[i])
    html='<section class="section">'.join(sections)
    html=html.replace('以正楷簽名</div>','以正楷簽全名</div>')
    target=exam['metadata'].get('verified_layout_target_pages','')
    html=html.replace('<html lang="zh-Hant">',f'<html lang="zh-Hant" data-target-pages="{target}" data-proof-subject="{subject}" data-proof-mode="{"answers" if a.answers else "student"}">')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='cn-layout-') as tmp:
        source=Path(tmp)/'source.html'
        pagination=Path(__file__).with_name('paginate_chinese_natural.js').read_text(encoding='utf-8')
        source.write_text(html.replace('</body>',f'<script>{pagination}</script></body>'),encoding='utf-8')
        dumped=subprocess.run([str(find_browser(None)),'--headless=new','--disable-gpu','--dump-dom','--virtual-time-budget=5000',source.as_uri()],capture_output=True,encoding='utf-8',timeout=60)
        if 'data-paginated="true"' not in dumped.stdout:
            diagnostic=re.search(r'<pre id="pagination-error">(.*?)</pre>',dumped.stdout,re.S)
            raise RuntimeError('Pagination failed: '+(html_lib.unescape(diagnostic.group(1)) if diagnostic else dumped.stdout[-1200:]))
        fixed=dumped.stdout
        match=re.search(r'<script id="fixed-page-report" type="application/json">(.*?)</script>',fixed,re.S)
        report=json.loads(html_lib.unescape(match.group(1)))
        if any(p.get('overflowCount') for p in report):raise RuntimeError('Fixed-page overflow')
        a.output.with_suffix('.layout.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        a.output.with_suffix('.html').write_text(fixed,encoding='utf-8')
        out=Path(tmp)/'raw.pdf'
        proc=subprocess.run([str(find_browser(None)),'--headless=new','--disable-gpu','--no-pdf-header-footer',f'--print-to-pdf={out}',a.output.with_suffix('.html').resolve().as_uri()],capture_output=True,timeout=90)
        if not out.exists():raise RuntimeError(proc.stderr)
        clean=Path(tmp)/'clean.pdf'
        doc=pymupdf.open(out);doc.save(clean,garbage=3,deflate=True)
        pages=len(doc);doc.close()
        publish_pdf(clean,a.output,provenance=not a.no_provenance)
    print(json.dumps({'output':str(a.output),'pages':pages},ensure_ascii=False))

if __name__=='__main__':main()
