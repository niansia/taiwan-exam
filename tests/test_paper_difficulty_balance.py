import copy,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('difficulty_balance',Path(__file__).parents[1]/'scripts/validate_paper_difficulty_balance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def paper():
    d={'metadata':{'difficulty_balance_plan':{'basis':'fixture','target_counts':{b:1 for b in m.BANDS},'target_points':{b:2 for b in m.BANDS}}},'questions':[],'answers':[]}
    for i,b in enumerate(m.BANDS):
        q={'id':str(i),'number':i+1,'score':2,'prompt':'fixture','options':[],'item_spec':{'difficulty':{'label':b}}}
        q['item_spec']['difficulty_design']={'band':b,'basis':'fixture','confidence':'provisional','short_route':f'review route {i}','misconception':'fixture','linked_decisions':['a','b','c'],'bottleneck':['a','b'],'expected_minutes':1,'shortcut_status':'reviewed-no-direct-collapse','content_sha256':m.content_hash(q)}
        d['questions'].append(q);d['answers'].append({'question_id':str(i),'difficulty_label':b})
    return d
def test_structure_is_not_psychometric_certificate():
    r=m.validate(paper());assert r['status']=='pass-structural-only';assert r['estimated_minutes']==4
def test_changed_question_requires_new_review():
    d=paper();d['questions'][0]['prompt']='changed';assert any('changed content' in e for e in m.validate(d)['errors'])
def test_labels_and_totals_must_match():
    d=paper();d['answers'][0]['difficulty_label']='中';d['questions'][1]['score']=3
    assert len(m.validate(d)['errors'])>=2
def test_missing_band_and_invalid_time_fail_cleanly():
    d=paper();d['questions'][0]['item_spec']['difficulty_design']['expected_minutes']=None
    d['questions'].pop();d['answers'].pop();r=m.validate(d)
    assert r['status']=='fail';assert any('missing 難' in e for e in r['errors'])
def test_hard_requires_bottleneck_and_shortcut_record():
    d=paper();r=d['questions'][-1]['item_spec']['difficulty_design'];r['bottleneck']=[];r.pop('shortcut_status')
    assert any('hard bottleneck' in e for e in m.validate(d)['errors']);assert any('shortcut' in e for e in m.validate(d)['errors'])
def test_changed_figure_invalidates_review(tmp_path):
    d=paper();p=tmp_path/'chart.svg';p.write_text('<svg/>',encoding='utf-8')
    q=d['questions'][0];q['visual_asset']={'path':'chart.svg','sha256':m.hashlib.sha256(p.read_bytes()).hexdigest()}
    q['item_spec']['difficulty_design']['content_sha256']=m.content_hash(q)
    assert not m.validate(d,tmp_path)['errors']
    p.write_text('<svg>new labels</svg>',encoding='utf-8')
    assert any('visual asset changed' in e for e in m.validate(d,tmp_path)['errors'])

def test_repeated_hard_reasoning_and_unrealistic_time_are_rejected():
    d=paper();d['metadata']['duration_minutes']=3
    d['questions'][3]['item_spec']['difficulty_design']['short_route']=d['questions'][2]['item_spec']['difficulty_design']['short_route']
    errors=m.validate(d)['errors']
    assert any('repeated hard-item' in e for e in errors)
    assert any('exceeds paper duration' in e for e in errors)

def test_small_booklet_declares_only_feasible_required_bands():
    d=paper();d['questions']=d['questions'][:2];d['answers']=d['answers'][:2]
    d['metadata']['difficulty_balance_plan']={
        'basis':'two-major-question writing booklet',
        'required_bands':['簡單','中'],
        'target_counts':{'簡單':1,'中':1,'中偏難':0,'難':0},
        'target_points':{'簡單':2,'中':2,'中偏難':0,'難':0},
    }
    assert m.validate(d)['status']=='pass-structural-only'

def test_printed_continuation_changes_content_hash():
    d=paper();q=d['questions'][0];before=m.content_hash(q)
    q['continuation_pages']={'3':'新增的續頁材料'}
    assert m.content_hash(q)!=before
