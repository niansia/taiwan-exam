#!/usr/bin/env python3
"""Summarize competence-item sources, editorial lead times, and joint difficulty patterns."""
from __future__ import annotations
import argparse,collections,json
from pathlib import Path

def band(days):
    if days is None:return "unknown"
    if days<=30:return "0-30d"
    if days<=90:return "31-90d"
    if days<=180:return "91-180d"
    if days<=365:return "181-365d"
    return ">365d"

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--exam',required=True);ap.add_argument('--subject',required=True);ap.add_argument('--output',type=Path);a=ap.parse_args()
    path=a.root/'exam_packs'/a.exam/'subjects'/a.subject/'metadata'/'questions.jsonl'
    rows=[json.loads(x) for x in path.read_text(encoding='utf-8-sig').splitlines() if x.strip()] if path.exists() else []
    usable=[];missing=[]
    for r in rows:
        lit=r.get('literacy') or {}; prov=r.get('stimulus_provenance') or {}
        if lit.get('classification')!='competence_oriented':continue
        required=['source_family','exam_date','freshness_class']
        if any(prov.get(k) is None for k in required):missing.append(r.get('question_id'));continue
        usable.append(r)
    joint=collections.Counter()
    families=collections.Counter();lead=collections.Counter();fresh=collections.Counter();removal=collections.Counter()
    for r in usable:
        p=r['stimulus_provenance'];l=r.get('literacy') or {};d=(r.get('difficulty') or {}).get('overall')
        families[p.get('source_family')]+=1;lead[band(p.get('lead_time_days'))]+=1;fresh[p.get('freshness_class')]+=1;removal[l.get('stimulus_removal_test')]+=1
        joint[(r.get('section'),p.get('source_family'),band(p.get('lead_time_days')),d,tuple(l.get('reasoning_operations') or []))]+=1
    report={'exam':a.exam,'subject':a.subject,'total_records':len(rows),'competence_records':len(usable)+len(missing),'usable_source_ecology_records':len(usable),'missing_provenance_question_ids':missing,'calibration_status':'ready' if len(usable)>=100 and len({r.get('year') for r in usable})>=3 else 'insufficient-data','source_family_distribution':families,'lead_time_distribution':lead,'freshness_distribution':fresh,'stimulus_removal_results':removal,'joint_patterns':[{'section':k[0],'source_family':k[1],'lead_time_band':k[2],'difficulty':k[3],'reasoning_operations':list(k[4]),'count':v} for k,v in joint.most_common()]}
    text=json.dumps(report,ensure_ascii=False,indent=2,default=dict)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text,encoding='utf-8')
    else:print(text)
if __name__=='__main__':main()
