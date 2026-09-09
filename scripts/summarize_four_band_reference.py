"""Reproducible 111–115 objective-item display; never a generated-item P estimator."""
import argparse,collections,hashlib,json
from pathlib import Path
BANDS=('簡單','中','中偏難','難')
def band(p):return BANDS[0]if p>=.65 else BANDS[1]if p>=.5 else BANDS[2]if p>=.4 else BANDS[3]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=Path('exam_packs/學測/metadata/official-difficulty-analysis.json'));ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    raw=a.input.read_bytes();d=json.loads(raw.decode('utf-8-sig'));groups=collections.defaultdict(list)
    for p in d['by_paper']:
        if 111<=p['roc_year']<=115:groups[p['subject']].extend(dict(x,roc_year=p['roc_year'])for x in p['item_curve'])
    out={'years':[111,112,113,114,115],'source_sha256':hashlib.sha256(raw).hexdigest(),'source':a.input.as_posix(),'cutoffs':{'簡單':'P >= .65','中':'.50 <= P < .65','中偏難':'.40 <= P < .50','難':'P < .40'},'caution':'Local four-band display, not CEEC labels. Counts are unweighted objective items; answer_rate and score_rate are separate below. Constructed-response calibration is not supplied. Do not infer generated item P.','subjects':{}}
    for sub,rows in groups.items():
        parts={}
        for metric in ['all-objective-counts','answer_rate','score_rate']:
            r=rows if metric=='all-objective-counts'else[x for x in rows if x['metric_type']==metric]
            c=collections.Counter(band(x['p_value'])for x in r)
            parts[metric]={'count':len(r),'bands':{b:c[b]for b in BANDS},'percent':{b:round(100*c[b]/len(r),2)for b in BANDS}if r else {}}
        out['subjects'][sub]=parts
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out['subjects'],ensure_ascii=False))
if __name__=='__main__':main()
