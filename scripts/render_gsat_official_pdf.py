#!/usr/bin/env python3
"""Render the GSAT-specific HTML layout to PDF with local Chromium."""
from __future__ import annotations
import argparse,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from render_gsat_official import render
from render_pdf import find_browser
from pdf_provenance import publish_pdf

def main(argv=None)->int:
    p=argparse.ArgumentParser();p.add_argument("input",type=Path);p.add_argument("output",type=Path);p.add_argument("--student-only",action="store_true");p.add_argument("--browser",type=Path);p.add_argument("--no-provenance",action="store_true");p.add_argument('--contract',type=Path);p.add_argument('--proof-only',action='store_true');a=p.parse_args(argv)
    try:
        if not a.proof_only:
            if not a.contract:raise ValueError('Formal PDF requires --contract and a passing content gate; use --proof-only solely for internal layout diagnostics.')
        exam=json.loads(a.input.read_text(encoding="utf-8-sig"));html=render(exam,include_answers=not a.student_only,asset_base=a.input.resolve().parent,run_contract=a.contract);browser=find_browser(a.browser)
        if a.proof_only:
            html=html.replace('</body>', '<div style="position:fixed;bottom:2mm;left:20mm;font-size:8pt">內部排版校樣：未通過正式試卷交付驗收</div></body>')
        with tempfile.TemporaryDirectory(prefix="gsat-official-") as d:
            d=Path(d);hp=d/"paper.html";pp=d/"paper.pdf";hp.write_text(html,encoding="utf-8")
            c=subprocess.run([str(browser),"--headless=new","--disable-gpu","--no-pdf-header-footer",f"--print-to-pdf={pp}",hp.as_uri()],capture_output=True,text=True,timeout=90)
            if not pp.exists() or pp.stat().st_size<1000:raise RuntimeError(c.stderr or c.stdout or "PDF output missing")
            a.output.parent.mkdir(parents=True,exist_ok=True);publish_pdf(pp,a.output,provenance=not a.no_provenance)
    except Exception as e:print(f"錯誤：{e}",file=sys.stderr);return 2
    print(f"已輸出{'內部校樣' if a.proof_only else '待逐頁驗收'} PDF：{a.output}");return 0
if __name__=="__main__":raise SystemExit(main())
