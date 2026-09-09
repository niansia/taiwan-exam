"""Check SVG text boxes against viewport, text boxes and stroked geometry in Chromium.

Reports are geometry triage, not a substitute for reviewing rasterized print pages.
"""
import argparse,html,json,re,subprocess,tempfile
from pathlib import Path
from render_pdf import find_browser

JS=r'''<script>
document.fonts.ready.then(()=>{
const reports=[...document.querySelectorAll('svg')].map(svg=>{
const viewport=svg.getBoundingClientRect(),texts=[...svg.querySelectorAll('text')].map(t=>({text:t.textContent,b:t.getBoundingClientRect()})),errors=[];
const inside=(p,b)=>p.x>b.left+2&&p.x<b.right-2&&p.y>b.top+2&&p.y<b.bottom-2;
texts.forEach((t,i)=>{
 if(t.b.left<viewport.left+1||t.b.top<viewport.top+1||t.b.right>viewport.right-1||t.b.bottom>viewport.bottom-1)errors.push({type:'viewport',text:t.text});
 for(let j=i+1;j<texts.length;j++){const u=texts[j];if(Math.min(t.b.right,u.b.right)-Math.max(t.b.left,u.b.left)>1&&Math.min(t.b.bottom,u.b.bottom)-Math.max(t.b.top,u.b.top)>1)errors.push({type:'text-text',text:t.text,other:u.text});}
 for(const shape of svg.querySelectorAll('path,line,polyline,polygon,rect,circle,ellipse')){
  if(getComputedStyle(shape).stroke==='none')continue;
  const matrix=shape.getScreenCTM(),length=shape.getTotalLength();let hit=false;
  for(let d=0;d<=length;d+=1){const v=shape.getPointAtLength(d);const p=new DOMPoint(v.x,v.y).matrixTransform(matrix);if(inside(p,t.b)){hit=true;break;}}
  if(hit)errors.push({type:'text-stroke',text:t.text,shape:shape.tagName});
 }
});return {name:svg.dataset.name,labels:texts.length,errors};
});const out=document.createElement('pre');out.id='geometry-report';out.textContent=JSON.stringify(reports);document.body.append(out);
});</script>'''

def main():
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    svgs=[]
    for path in sorted(a.directory.glob('*.svg')):
        svgs.append(path.read_text(encoding='utf-8').replace('<svg ',f'<svg data-name="{html.escape(path.name)}" ',1))
    with tempfile.TemporaryDirectory(prefix='svg-geometry-') as tmp:
        src=Path(tmp)/'check.html';src.write_text('<html><meta charset="utf-8"><body>'+''.join(svgs)+JS+'</body></html>',encoding='utf-8')
        c=subprocess.run([str(find_browser(None)),'--headless=new','--disable-gpu','--dump-dom','--virtual-time-budget=2500',src.as_uri()],capture_output=True,encoding='utf-8',timeout=60)
    match=re.search(r'<pre id="geometry-report">(.*?)</pre>',c.stdout,re.S)
    if not match:raise RuntimeError('No geometry report produced')
    rows=json.loads(html.unescape(match.group(1)))
    report={'status':'fail' if any(r['errors'] for r in rows) else 'pass-geometry-only','figures':rows}
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False));return int(report['status']=='fail')
if __name__=='__main__':raise SystemExit(main())
