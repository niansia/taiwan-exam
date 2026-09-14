import sys
from pathlib import Path
import pymupdf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from inspect_hosted_pdf import audit

def test_risk_flags_prioritize_resolution_without_claiming_review(tmp_path):
    pdf=tmp_path/'fixture.pdf'
    with pymupdf.open() as doc:
        p=doc.new_page(width=595.28,height=841.89)
        for y in range(100,760,20):p.insert_text((70,y),'Readable full-page synthetic prose only.',fontsize=11)
        p=doc.new_page(width=595.28,height=841.89)
        for y in range(100,760,20):p.insert_text((70,y),'Readable synthetic prose.',fontsize=11)
        p.draw_circle((400,300),20,color=(0,0,0))
        p.insert_text((350,330),'Small axis label',fontsize=7)
        doc.save(pdf)
    result=audit(pdf,tmp_path/'raster')
    plain,risk=result['pages']
    assert plain['needs_full_resolution_review'] is False
    assert risk['needs_full_resolution_review'] is True
    assert 'small-body-type-or-script' in risk['full_resolution_reasons']
    assert result['full_resolution_review_pages']==[2]
    assert plain['raster_scale']==1.5 and risk['raster_scale']==2.5
    assert all(p['visual_review']=='not-performed-by-this-tool' for p in result['pages'])
    assert 'every final page' in result['review_policy']
