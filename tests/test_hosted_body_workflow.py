"""Real body layout, final-template composition and pending review regression."""
import copy
import hashlib
import json
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from hosted_body_templates import render
from hosted_item_layout import draw_rail, geometry_errors
from inspect_hosted_pdf import rail_format_samples
from compose_hosted_pdf import compose
from verify_fixed_template_pdf import DEFAULT_MAP, verify_pdf
from prepare_hosted_review import bind_layout, prepare, refresh_review_hashes
from hosted_blind_review import review_errors
from test_hosted_review_modes import row, review


@pytest.fixture(scope='module')
def gallery(tmp_path_factory):
    folder=tmp_path_factory.mktemp('body-gallery')
    font=folder/'font.ttf';font.write_bytes(pymupdf.Font('cjk').buffer)
    spec=json.loads((ROOT/'templates/hosted-body-blocks.json').read_text(encoding='utf-8'))
    return folder,font,spec


@pytest.mark.parametrize('subject',['國綜','英文','數學A','數學B','自然','社會','國寫'])
def test_blocks_preserve_all_subject_fixed_templates_and_review_starts_pending(subject,gallery,tmp_path):
    folder,font,spec=gallery
    spec=copy.deepcopy(spec);spec['subject']=subject
    body=tmp_path/'body.pdf';layout_file=tmp_path/'body-layout.json'
    layout=render(spec,body,layout_file,font,asset_root=ROOT/'templates',proof=True)
    with pymupdf.open(body) as doc:
        assert not geometry_errors(doc,layout['parts'])
        # Regression: an image must fit its recorded block, not extend into the
        # next question while HTML's reported line height pretends it fits.
        for part in layout['parts']:
            block=pymupdf.Rect(part['bbox'])
            for image in doc[part['page']-1].get_image_info():
                rect=pymupdf.Rect(image['bbox'])
                if block.intersects(rect):assert block.contains(rect)
    record=next(s for s in json.loads(DEFAULT_MAP.read_text(encoding='utf-8'))['subjects'] if s['subject']==subject)
    assets=ROOT/Path(record['assets'][0]['repository_path']).parent
    pairs={}
    for role,kind in [('question','questions'),('solution','answers')]:
        pdf=tmp_path/(role+'.pdf')
        compose(subject,body,assets,pdf,year='116',title='版型示範',running_name='學測',font_path=font,kind=kind)
        assert verify_pdf(pdf,subject,kind)['status']=='pass-fixed-template'
        pairs[role]=(pdf,body,layout_file)
        final_layout=bind_layout(body,pdf,layout,1 if role=='question' else 0)
        assert final_layout['pdf_sha256']==hashlib.sha256(pdf.read_bytes()).hexdigest()
    exam=tmp_path/'exam.json';exam.write_text(json.dumps({'metadata':{'subject':subject}}),encoding='utf-8')
    state=tmp_path/'run-state.json';state.write_text(json.dumps({'exam':{'path':'exam.json','sha256':hashlib.sha256(exam.read_bytes()).hexdigest()}}),encoding='utf-8')
    result=prepare(state,pairs,tmp_path/'qa')
    assert result['status']=='review-pending'
    saved=json.loads(Path(result['state']).read_text(encoding='utf-8'))
    for bundle in saved['pdfs'].values():
        for key,rows in [('item_review','parts'),('visual_review','pages')]:
            report=json.loads((tmp_path/bundle[key]['path']).read_text(encoding='utf-8'))
            assert report[rows] and all(r['status']=='pending' and not r['observations'] for r in report[rows])
    if subject=='數學A':
        for bundle in saved['pdfs'].values():
            for key,rows in [('item_review','parts'),('visual_review','pages')]:
                report_path=tmp_path/bundle[key]['path']
                report=json.loads(report_path.read_text(encoding='utf-8'))
                for row in report[rows]:row.update(status='pass',observations='Synthetic layout fixture review')
                report_path.write_text(json.dumps(report),encoding='utf-8')
        refresh_review_hashes(Path(result['state']))
        retained=prepare(Path(result['state']),pairs,tmp_path/'qa2')
        assert retained['retained_actual_reviews']['pages']>0
        assert retained['retained_actual_reviews']['parts']>0
        changed=json.loads(Path(retained['state']).read_text(encoding='utf-8'))
        exam.write_text(json.dumps({'metadata':{'subject':subject,'revision':2}}),encoding='utf-8')
        changed['exam']['sha256']=hashlib.sha256(exam.read_bytes()).hexdigest()
        Path(retained['state']).write_text(json.dumps(changed),encoding='utf-8')
        invalidated=prepare(Path(retained['state']),pairs,tmp_path/'qa3')
        assert invalidated['retained_actual_reviews']=={'pages':0,'parts':0}


def test_placeholder_gallery_cannot_be_used_as_production(gallery,tmp_path):
    _,font,spec=gallery
    with pytest.raises(ValueError,match='Placeholder gallery'):
        render(spec,tmp_path/'body.pdf',tmp_path/'layout.json',font,asset_root=ROOT/'templates')


def test_changed_body_cannot_reuse_measured_layout(gallery,tmp_path):
    _,font,spec=gallery
    body=tmp_path/'body.pdf'
    layout=render(spec,body,tmp_path/'layout.json',font,asset_root=ROOT/'templates',proof=True)
    with pymupdf.open(body) as doc:
        doc[0].insert_text((100,170),'Changed');doc.save(tmp_path/'changed.pdf')
    with pytest.raises(ValueError,match='stale body'):
        bind_layout(tmp_path/'changed.pdf',body,layout,0)
    with pytest.raises(ValueError,match='pixels differ'):
        bind_layout(body,tmp_path/'changed.pdf',layout,0)


def test_native_rail_format_rejects_detached_labels_and_missing_rules():
    with pymupdf.open() as doc:
        good=doc.new_page()
        draw_rail(good,{'bbox':[100,100,186.94,128.98]},17,3)
        assert not rail_format_samples(good)
        wrong=doc.new_page()
        wrong.insert_text((60,110),'(17-1)',fontsize=10)
        wrong.draw_circle((110,108),13)
        assert any(r['issue']=='position-id-outside-circle' for r in rail_format_samples(wrong))
        missing=doc.new_page()
        missing.draw_circle((113,113),13)
        missing.insert_text((104,116),'17-1',fontsize=10)
        assert any(r['issue']=='position-row-missing-answer-rule' for r in rail_format_samples(missing))


@pytest.mark.parametrize('subject',['數學A','數學B'])
def test_math_easy_ten_is_rejected_and_hard_points_are_required(subject):
    exam={'metadata':{'subject':subject},'questions':[{'id':str(i),'score':5} for i in range(20)]}
    r=review([row(i) for i in range(20)])
    bands=['easy']+['medium']*4+['hard']*8+['very_hard']*7
    for item,band in zip(r['items'],bands):item['difficulty_band']=band
    assert not review_errors(exam,r)
    r['items'][1]['difficulty_band']='easy'
    assert any('below 10' in e for e in review_errors(exam,r))
    for item in r['items']:item['difficulty_band']='medium'
    errors=review_errors(exam,r)
    assert any('70 points' in e for e in errors) and any('30 points' in e for e in errors)
