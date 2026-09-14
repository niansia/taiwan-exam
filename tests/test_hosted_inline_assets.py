"""Formula assets must survive every authored field through actual PDF layout."""
import copy
import hashlib
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from hosted_body_templates import fragment, render


@pytest.fixture
def formula(tmp_path):
    path=tmp_path/'formula.png'
    with pymupdf.open() as doc:
        page=doc.new_page(width=24,height=24)
        page.insert_text((8,10),'1',fontname='tiro',fontsize=10)
        page.draw_line((5,12),(19,12),width=.5)
        page.insert_text((8,22),'2',fontname='tiro',fontsize=10)
        page.get_pixmap(matrix=pymupdf.Matrix(3,3),alpha=True).save(path)
    return {'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'width_pt':24}


CASES=[
    {'kind':'section','title':'Inline {{asset:formula}}','directions':'Directions'},
    {'kind':'choice','text':'Stem','options':[{'label':'(1)','text':'{{asset:formula}}'},{'label':'(2)','text':'One'}]},
    {'kind':'multiple','text':'Stem','options':[{'label':'(1)','text':{'rich':'<b>Value</b> {{asset:formula}}'}},{'label':'(2)','text':'One'}]},
    {'kind':'fill','text':'Given {{asset:formula}}, answer {{answer}}.','rows':[1]},
    {'kind':'constructed','text':'Compute {{asset:formula}}.','score':3},
    {'kind':'stimulus','text':'Given {{asset:formula}}.'},
    {'kind':'solution','text':'Answer','steps':['The fraction is {{asset:formula}}.']},
    {'kind':'passage','paragraphs':['A fraction {{asset:formula}}.'],
     'bank':[{'label':'(A)','text':'{{asset:formula}}'}]},
    {'kind':'table','headers':['Value {{asset:formula}}'],'rows':[['{{asset:formula}}']]},
]


@pytest.mark.parametrize('case',CASES,ids=lambda case:case['kind'])
def test_formula_assets_render_in_every_block_kind(case,formula,tmp_path):
    block={'id':'fixture','number':1,**copy.deepcopy(case),'assets':{'formula':formula}}
    # Kept section headings must precede a body block in actual pagination.
    blocks=[block]+([{'kind':'stimulus','id':'next','text':'Synthetic following content'}]
                    if block['kind']=='section' else [])
    font=tmp_path/'font.ttf';font.write_bytes(pymupdf.Font('cjk').buffer)
    pdf=tmp_path/'body.pdf'
    render({'subject':'數學A','blocks':blocks},pdf,tmp_path/'layout.json',font,asset_root=tmp_path)
    with pymupdf.open(pdf) as doc:
        assert all('{{asset:' not in page.get_text() for page in doc)
        images=[image for page in doc for image in page.get_image_info()]
        # Fill rails have their own image. The formula remains an actual 24pt image.
        assert any(abs(pymupdf.Rect(image['bbox']).width-24)<.1 for image in images)


@pytest.mark.parametrize('case',CASES,ids=lambda case:case['kind'])
def test_missing_formula_assets_fail_for_every_field(case,tmp_path):
    block={'id':'fixture','number':1,**copy.deepcopy(case)}
    with pytest.raises(ValueError,match='Missing inline asset'):
        fragment(block,pymupdf.Archive(),tmp_path,0)


def test_early_return_blocks_check_asset_hash_and_local_path(formula,tmp_path):
    block={'kind':'passage','paragraphs':['{{asset:formula}}'],'assets':{'formula':copy.deepcopy(formula)}}
    block['assets']['formula']['sha256']='0'*64
    with pytest.raises(ValueError,match='Changed body asset'):
        fragment(block,pymupdf.Archive(),tmp_path,0)
    block['assets']['formula'].update(formula,path='../outside.png')
    with pytest.raises(ValueError,match='Asset outside current run'):
        fragment(block,pymupdf.Archive(),tmp_path,0)


def test_asset_substitution_keeps_rich_text_allowlist(formula,tmp_path):
    block={'kind':'choice','number':1,'text':'Stem','assets':{'formula':formula},
           'options':[{'label':'(1)','text':{'rich':'<img src="external">{{asset:formula}}'}},
                      {'label':'(2)','text':'One'}]}
    with pytest.raises(ValueError,match='Use only'):
        fragment(block,pymupdf.Archive(),tmp_path,0)
    block['options'][0]['text']='<script>alert(1)</script> {{asset:formula}}'
    content=fragment(block,pymupdf.Archive(),tmp_path,0)
    assert '<script>' not in content and '&lt;script&gt;' in content
    assert '<img src="asset-0-0.png"' in content


def test_asset_filename_is_not_html_markup(formula,tmp_path):
    # Quotes cannot occur in Windows filenames, so use a legal ampersand instead.
    # Archive names still have to be escaped on every platform.
    path=tmp_path/'formula.p&ng';path.write_bytes((tmp_path/formula['path']).read_bytes())
    block={'kind':'stimulus','text':'{{asset:formula}}','assets':{'formula':{**formula,'path':path.name}}}
    content=fragment(block,pymupdf.Archive(),tmp_path,0)
    assert 'src="asset-0-0.p&amp;ng"' in content


def test_single_page_body_pdf_asset_is_actually_visible(tmp_path):
    source=tmp_path/'authored-formula.pdf'
    with pymupdf.open() as doc:
        page=doc.new_page(width=24,height=24)
        page.insert_text((6,16),'x',fontname='tiro',fontsize=12)
        doc.save(source)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    asset={'path':source.name,'sha256':digest,'width_pt':24}
    spec={'subject':'數學A','blocks':[{'kind':'choice','id':'fixture','number':1,'text':'Stem',
        'options':[{'label':'(1)','text':'{{asset:formula}}'},{'label':'(2)','text':'One'}],
        'assets':{'formula':asset}}]}
    font=tmp_path/'font.ttf';font.write_bytes(pymupdf.Font('cjk').buffer)
    pdf=tmp_path/'body.pdf'
    render(spec,pdf,tmp_path/'layout.json',font,asset_root=tmp_path)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    with pymupdf.open(pdf) as doc:
        assert '[image]' not in doc[0].get_text()
        images=doc[0].get_image_info()
        assert len(images)==1 and images[0]['width']==72 and images[0]['height']==72
        assert abs(pymupdf.Rect(images[0]['bbox']).width-24)<.1


def test_multi_page_body_pdf_asset_cannot_silently_drop_pages(tmp_path):
    source=tmp_path/'two-pages.pdf'
    with pymupdf.open() as doc:
        doc.new_page();doc.new_page();doc.save(source)
    asset={'path':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'width_pt':24}
    with pytest.raises(ValueError,match='exactly one page'):
        fragment({'kind':'stimulus','text':'{{asset:formula}}','assets':{'formula':asset}},
                 pymupdf.Archive(),tmp_path,0)


@pytest.mark.parametrize('rows',[[1],[3],[2,1]])
@pytest.mark.parametrize('prefix',['若條件成立，則 λ = ', '這是一段較長的題幹，用來測試自動換行。所有變數符合指定條件且需檢查端點，再由所得關係解出 n = '])
def test_answer_rail_remains_next_to_equation_at_actual_text_height(rows,prefix,tmp_path):
    font=tmp_path/'font.ttf';font.write_bytes(pymupdf.Font('cjk').buffer)
    pdf=tmp_path/'body.pdf'
    render({'subject':'數學A','blocks':[{'kind':'fill','id':'q14','number':14,'rows':rows,
            'text':prefix+'{{answer}}（化為最簡形式）。'}]},pdf,tmp_path/'layout.json',font,asset_root=tmp_path)
    with pymupdf.open(pdf) as doc:
        p=doc[0];rail=pymupdf.Rect(p.get_image_info()[0]['bbox'])
        spans=[s for b in p.get_text('dict')['blocks'] for line in b.get('lines',[]) for s in line['spans']]
        adjacent=[pymupdf.Rect(s['bbox']) for s in spans if '=' in s['text']]
        assert len(adjacent)==1
        text_box=adjacent[0]
        assert 0<=rail.x0-text_box.x1<2
        assert abs((rail.y0+rail.y1-text_box.y0-text_box.y1)/2)<5
        # Conditions follow at the same readable line; they are not compressed
        # into a narrow third table column or displaced above the answer rail.
        suffix=next(pymupdf.Rect(s['bbox']) for s in spans if '化為' in s['text'])
        assert suffix.x0>=rail.x1-.1
        assert abs(suffix.y0-text_box.y0)<.1
