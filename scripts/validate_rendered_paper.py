#!/usr/bin/env python3
"""Reject papers that match page count only through sparse forced pagination."""
from __future__ import annotations
import argparse,json,statistics
from pathlib import Path
from pypdf import PdfReader

def page_counts(path:Path):
    return [len((p.extract_text() or '').replace(' ','').replace('\n','')) for p in PdfReader(str(path)).pages[1:]]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('generated',type=Path);ap.add_argument('reference',type=Path);ap.add_argument('--ratio',type=float,default=.70);ap.add_argument('--output',type=Path);a=ap.parse_args()
    got,ref=page_counts(a.generated),page_counts(a.reference);ag,ar=statistics.mean(got),statistics.mean(ref)
    report={'generated':str(a.generated),'reference':str(a.reference),'generated_total_pages':len(got)+1,'reference_total_pages':len(ref)+1,'generated_average_text_chars_per_content_page':round(ag,1),'reference_average_text_chars_per_content_page':round(ar,1),'density_ratio':round(ag/ar,3),'minimum_ratio':a.ratio,'page_count_pass':len(got)==len(ref),'density_pass':ag/ar>=a.ratio}
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text,encoding='utf-8')
    else:print(text)
    return 0 if report['page_count_pass'] and report['density_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
