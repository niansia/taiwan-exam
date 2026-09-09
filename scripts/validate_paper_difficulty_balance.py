"""Structural four-band audit, deliberately not a achieved-difficulty certificate."""
import argparse,collections,hashlib,json
from pathlib import Path
BANDS=('簡單','中','中偏難','難')
def content_hash(q):
    content={k:q.get(k) for k in ('prompt','group_stimulus','options','visual_asset')}
    return hashlib.sha256(json.dumps(content,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def validate(d,asset_root=None):
    errors=[]; counts=collections.Counter(); points=collections.Counter();rows=[]; hard_evidence=collections.Counter()
    plan=d.get('metadata',{}).get('difficulty_balance_plan',{})
    answers={a['question_id']:a for a in d.get('answers',[])}
    for q in d.get('questions',[]):
        rec=q.get('item_spec',{}).get('difficulty_design',{});band=rec.get('band');n=q.get('number')
        if band not in BANDS:errors.append(f'Q{n}: missing four-band estimate');continue
        counts[band]+=1;points[band]+=float(q.get('score',0))
        if answers.get(q['id'],{}).get('difficulty_label')!=band:errors.append(f'Q{n}: answer label mismatch')
        if q.get('item_spec',{}).get('difficulty',{}).get('label')!=band:errors.append(f'Q{n}: item label mismatch')
        for f in ('basis','confidence','short_route','misconception','linked_decisions','bottleneck'):
            if not rec.get(f):errors.append(f'Q{n}: missing {f}')
        if rec.get('content_sha256')!=content_hash(q):errors.append(f'Q{n}: changed content requires review')
        asset=q.get('visual_asset')
        if asset and asset_root is not None:
            path=Path(asset_root)/asset.get('path','')
            if not path.is_file() or asset.get('sha256')!=hashlib.sha256(path.read_bytes()).hexdigest():errors.append(f'Q{n}: visual asset changed or missing hash; review required')
        if not isinstance(rec.get('expected_minutes'),(float,int)) or rec['expected_minutes']<=0:errors.append(f'Q{n}: invalid time')
        if band=='難' and (len(rec.get('linked_decisions',[]))<3 or len(rec.get('bottleneck',[]))<2):errors.append(f'Q{n}: insufficient declared hard bottlenecks')
        if band in ('中偏難','難') and rec.get('shortcut_status')!='reviewed-no-direct-collapse':errors.append(f'Q{n}: shortcut review missing')
        if band in ('中偏難','難'):
            key=json.dumps([rec.get('linked_decisions'),rec.get('bottleneck'),rec.get('short_route')],ensure_ascii=False,sort_keys=True)
            hard_evidence[key]+=1
        rows.append(dict(number=n,band=band,score=q.get('score'),minutes=rec.get('expected_minutes')))
    for band in BANDS:
        if not counts[band]:errors.append(f'paper missing {band}')
        if counts[band]!=plan.get('target_counts',{}).get(band):errors.append(f'{band}: count differs from declared plan')
        if points[band]!=plan.get('target_points',{}).get(band):errors.append(f'{band}: score differs from declared plan')
    if not plan.get('basis'):errors.append('paper target basis missing')
    if any(n>1 for n in hard_evidence.values()):errors.append('repeated hard-item reasoning evidence: review template reuse rather than quota labels')
    shared=plan.get('shared_reading_minutes',0)
    if not isinstance(shared,(int,float)) or shared<0:errors.append('invalid shared reading time');shared=0
    duration=d.get('metadata',{}).get('duration_minutes')
    minutes=sum(r['minutes'] for r in rows if isinstance(r['minutes'],(int,float)))+shared
    if isinstance(duration,(int,float)) and minutes>duration:errors.append('estimated solving time exceeds paper duration')
    total=sum(points.values());count=sum(counts.values())
    return dict(status='pass-structural-only' if not errors else 'fail',errors=errors,count=dict(counts),points=dict(points),
        count_percent={b:round(100*counts[b]/count,1)for b in BANDS} if count else {},
        score_percent={b:round(100*points[b]/total,1)for b in BANDS} if total else {},items=rows,
        estimated_minutes=minutes,
        caution='Expert estimates and recorded short routes require substantive review; no achieved P/D is inferred.')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('exam',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
    r=validate(json.loads(a.exam.read_text(encoding='utf-8-sig')),a.exam.parent)
    if a.output:a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items()if k!='items'},ensure_ascii=False));return bool(r['errors'])
if __name__=='__main__':raise SystemExit(main())
