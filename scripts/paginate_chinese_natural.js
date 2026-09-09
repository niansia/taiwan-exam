/* Fixed-page proof pagination: measured text, unchanged type size, balanced page breaks. */
document.fonts.ready.then(async () => {
  await Promise.all([...document.images].map(im=>im.decode().catch(()=>{})));
  const pxmm=96/25.4, height=244*pxmm;
  const root=document.querySelector('main.paper');
  const answer=document.querySelector('.answer-key');
  const mode=document.documentElement.dataset.proofMode;
  const chinese=document.documentElement.dataset.proofSubject==='國綜';
  const flow=document.createElement('div');flow.className='measure-flow';
  flow.style.cssText='width:165mm;position:absolute;left:0;top:0;visibility:hidden';
  document.body.append(flow);
  const atoms=[];
  const add=(node,keep=false)=>{node.style.marginTop='0';flow.append(node);
    // A source line belongs to the preceding material, never alone atop a page.
    if(node.matches('.stimulus')&&/^\s*[（(]/.test(node.textContent)&&atoms.length)atoms.at(-1).keep=true;
    atoms.push({node,keep});};
  const paragraphChunks=(node)=>{
    const paragraphs=node.innerHTML.split(/<br\s*\/?>(?:\s*\n)?/i).filter(x=>x.trim());
    for(const para of paragraphs){
      const probe=node.cloneNode(false);probe.innerHTML=para;
      if(/^\s*[（(]/.test(probe.textContent))probe.classList.add('source-line');
      flow.append(probe);
      if(probe.getBoundingClientRect().height<(chinese?100:155)){probe.remove();add(probe);continue;}
      const content=probe.textContent;probe.remove();
      // Split at sentence/clause boundaries, preserving every character and order.
      const units=content.match(/[^。；！？]+[。；！？]?/g)||[content];let chunk='',hasPrevious=false;
      for(const unit of units){
        const test=node.cloneNode(false);test.textContent=chunk+unit;flow.append(test);
        const tooHigh=test.getBoundingClientRect().height>(chinese?95:150);test.remove();
        if(tooHigh&&chunk){const part=node.cloneNode(false);part.textContent=chunk;if(hasPrevious)part.classList.add('continued-paragraph');part.style.marginBottom='0';add(part);hasPrevious=true;chunk=unit;}else chunk+=unit;
      }
      if(chunk){const part=node.cloneNode(false);part.textContent=chunk;if(hasPrevious)part.classList.add('continued-paragraph');add(part);}
    }
  };
  if(mode==='answers'){
    add(answer.querySelector('h1').cloneNode(true),true);
    const table=answer.querySelector('table');
    const heading=table.cloneNode(false);heading.append(table.querySelector('thead').cloneNode(true));add(heading,true);
    for(const row of table.querySelectorAll('tbody tr')){
      const t=table.cloneNode(false);t.append(row.cloneNode(true));add(t);
    }
    for(const solution of answer.querySelectorAll('.solution')) add(solution.cloneNode(true));
  }else{
    for(const section of root.querySelectorAll(':scope>.section')){
      for(const node of section.children){
        if(node.matches('.stimulus'))paragraphChunks(node);
        else if(node.matches('.question')){
          const copy=node.cloneNode(true);flow.append(copy);const h=copy.getBoundingClientRect().height;copy.remove();
          if(h>310&&copy.querySelector('.figure')&&copy.querySelector('.options')){
            const options=copy.querySelector('.options'),figure=copy.querySelector('.figure');options.remove();figure.remove();add(copy,true);
            const figureWrap=document.createElement('div');figureWrap.className='question-continuation';figureWrap.append(figure);add(figureWrap);
            const optionWrap=document.createElement('div');optionWrap.className='question-continuation';optionWrap.append(options);add(optionWrap);
          }else if(!chinese&&h>120&&copy.querySelector('.options.cols-1')&&copy.querySelectorAll('.option').length===5){
            const options=copy.querySelector('.options'),rest=options.cloneNode(false);
            [...options.children].slice(2).forEach(o=>rest.append(o));copy.style.marginBottom='0';add(copy);
            const wrap=document.createElement('div');wrap.className='question-continuation';wrap.append(rest);add(wrap);
          }else add(copy);
        }else add(node.cloneNode(true),node.matches('.section-title,.section-subtitle,.section-rule,.group-label'));
      }
    }
  }
  const heights=atoms.map(a=>a.node.getBoundingClientRect().height+parseFloat(getComputedStyle(a.node).marginBottom||0));
  const prefix=[0];heights.forEach(h=>prefix.push(prefix.at(-1)+h));
  const N=atoms.length,cost=Array(N+1).fill(Infinity),next=Array(N).fill(-1);cost[N]=0;
  for(let i=N-1;i>=0;i--){
    for(let j=i+1;j<=N;j++){
      const used=prefix[j]-prefix[i];if(used>height-2)break;
      if(j<N&&atoms[j-1].keep)continue;
      const ratio=used/height;
      const penalty=(chinese?100:1)+Math.pow(1-ratio,2)*4+(ratio<.78?Math.pow(.78-ratio,2)*100:0);
      if(penalty+cost[j]<cost[i]){cost[i]=penalty+cost[j];next[i]=j;}
    }
  }
  if(next[0]<0)throw new Error('An indivisible content unit is taller than the printable frame');
  const wanted=Number(document.documentElement.dataset.targetPages)-1;
  if(mode!=='answers'&&wanted>0){
    // A historical page target is permitted only with substantive content on every page.
    // No font changes, artificial spacers or blank pages are introduced by this solver.
    const dp=Array.from({length:wanted+1},()=>Array(N+1).fill(Infinity));
    const route=Array.from({length:wanted+1},()=>Array(N).fill(-1));dp[0][N]=0;
    for(let k=1;k<=wanted;k++)for(let i=N-1;i>=0;i--)for(let j=i+1;j<=N;j++){
      const used=prefix[j]-prefix[i],ratio=used/height;if(used>height-2)break;
      if(ratio<.77||(j<N&&atoms[j-1].keep)||!Number.isFinite(dp[k-1][j]))continue;
      const value=Math.pow(1-ratio,2)+dp[k-1][j];
      if(value<dp[k][i]){dp[k][i]=value;route[k][i]=j;}
    }
    if(!Number.isFinite(dp[wanted][0])){
      const reachable=Array(N+1).fill(false);reachable[0]=true;
      for(let i=0;i<N;i++)if(reachable[i])for(let j=i+1;j<=N;j++){const used=prefix[j]-prefix[i];if(used>height-2)break;if(used/height>=.78&&!(j<N&&atoms[j-1].keep))reachable[j]=true;}
      const far=reachable.lastIndexOf(true);
      const diagnostic=document.createElement('pre');diagnostic.id='pagination-error';
      diagnostic.textContent=JSON.stringify({wanted,available:dp.map((r,k)=>Number.isFinite(r[0])?k:null).filter(x=>x!==null),N,far,tail:atoms.slice(-17).map((a,j)=>({i:N-17+j,reachable:reachable[N-17+j],text:a.node.textContent.slice(0,20),toEnd:(prefix[N]-prefix[N-17+j])/height,keep:a.keep}))});document.body.append(diagnostic);
      throw new Error('Requested historical page target cannot meet the 78% substantive density floor');
    }
    let i=0;for(let k=wanted;k>0;k--){next[i]=route[k][i];i=next[i];}
  }
  const sheets=[];let cursor=0;
  while(cursor<N){const end=next[cursor];const sheet=document.createElement('section');sheet.className='sheet';const content=document.createElement('div');content.className='content';sheet.append(content);for(let i=cursor;i<end;i++)content.append(atoms[i].node);
    // A small distributed inter-item adjustment is allowed; never expand paragraphs,
    // fonts, figures or response spaces to manufacture page density.
    const used=prefix[end]-prefix[cursor];
    const gaps=[...content.children].slice(0,-1).filter(n=>n.matches('.question,.solution'));
    const extra=Math.min(2*pxmm,Math.max(0,.80*height-used)/Math.max(1,gaps.length));
    for(const n of gaps)n.style.marginBottom=(parseFloat(getComputedStyle(n).marginBottom)||2*pxmm)+extra+'px';
    sheets.push(sheet);cursor=end;}
  const cover=document.querySelector('.cover');
  if(mode!=='answers'){const coverSheet=document.createElement('section');coverSheet.className='sheet cover-sheet';coverSheet.append(cover);sheets.unshift(coverSheet);}
  document.body.replaceChildren(...sheets);
  const css=document.createElement('style');css.textContent='@page{size:A4;margin:0}body{width:210mm!important;margin:0!important}.sheet{width:210mm;height:297mm;padding:31mm 22.5mm 22mm;break-after:page;box-sizing:border-box}.sheet:last-child{break-after:auto}.content{height:244mm;display:flow-root}.question-continuation{margin:0 0 2mm 7mm}.sheet .cover{height:240mm;break-after:auto}.answer-summary{table-layout:fixed}.answer-summary td:first-child{width:13mm}.answer-summary td:last-child{width:20mm}';document.head.append(css);
  const furnitureCSS=document.createElement('style');furnitureCSS.textContent='.sheet{position:relative}.booklet-head{position:absolute;left:22.5mm;right:22.5mm;top:14.8mm;display:flex;justify-content:space-between;font-family:"Times New Roman",ExamMing,serif;font-size:11pt;line-height:14pt}.booklet-head .head-right{text-align:right}.booklet-reminder{position:absolute;top:14mm;left:68.5mm;width:74.5mm;background:#ddd;font-family:ExamKai,serif;font-size:10.5pt;line-height:15pt;text-align:center}.booklet-footer{position:absolute;bottom:11.5mm;font-family:"Times New Roman",serif;font-size:10pt;line-height:12pt}';document.head.append(furnitureCSS);
  sheets.forEach((s,i)=>{if(s.classList.contains('cover-sheet'))return;const n=mode==='answers'?i+1:i,total=mode==='answers'?sheets.length:sheets.length-1,sub=document.documentElement.dataset.proofSubject;
    const count=`第 ${n} 頁<br>共 ${total} 頁`,label=mode==='answers'?`116年學測模擬<br>${sub}答案與解析`:`116年學測模擬<br>${sub==='國綜'?'國語文綜合能力測驗':'自然考科'}`;
    const head=document.createElement('div');head.className='booklet-head';head.innerHTML=`<div>${n%2?count:label}</div><div class="head-right">${n%2?label:count}</div>`;s.append(head);
    const reminder=document.createElement('div');reminder.className='booklet-reminder';reminder.textContent=mode==='answers'?'答案與評分參考':'請記得在答題卷簽名欄位以正楷簽全名';s.append(reminder);
    const footer=document.createElement('div');footer.className='booklet-footer';footer.style[n%2?'left':'right']='22.5mm';footer.textContent=`- ${n} -`;s.append(footer);
  });
  // Audit the final fixed frame; block overflows are never hidden or clipped.
  const report=sheets.map((s,i)=>{const c=s.querySelector('.content');if(!c)return {page:i+1,role:'cover'};const b=c.getBoundingClientRect(),children=[...c.children],bottom=Math.max(b.top,...children.map(n=>n.getBoundingClientRect().bottom));const overflow=children.filter(n=>{const r=n.getBoundingClientRect();return r.right>b.right+.75||r.bottom>b.bottom+.75||r.left<b.left-.75});return {page:i+1,role:'content',usedRatio:(bottom-b.top)/b.height,overflowCount:overflow.length};});
  const data=document.createElement('script');data.id='fixed-page-report';data.type='application/json';data.textContent=JSON.stringify(report);document.body.append(data);
  if(mode!=='answers'&&report.some(p=>p.role==='content'&&(p.usedRatio<.78||p.overflowCount)))throw new Error('Final rendered content fails the 78% density or no-overflow gate');
  document.documentElement.dataset.paginated='true';
}).catch(e=>{document.documentElement.dataset.paginationError=String(e)});
