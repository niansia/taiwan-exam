"""Final bytes, not a pass report, decide fixed-template fidelity for all seven subjects."""
import json
from pathlib import Path
import sys
import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from verify_fixed_template_pdf import verify_pdf, DEFAULT_MAP, masked_pixels
from compose_hosted_pdf import compose
from pdf_provenance import publish_pdf
from hosted_blind_review import review_errors, packet
from test_hosted_run_evidence import saved_run, fixed_evidence_pdfs, evaluate


@pytest.mark.parametrize('alpha',[False,True])
def test_scanline_masks_match_original_pixel_algorithm_exactly(alpha):
    with pymupdf.open() as doc:
        page=doc.new_page(width=180,height=240)
        page.draw_rect(page.rect,fill=(.3,.3,.3))
        page.insert_text((10,30),'Mask boundary regression')
        regions=[[-10.2,-5,5.1,90],[20.2,40.4,170.7,220.9],[25,210,200,260], [99,88,99,88]]
        pix=page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),colorspace=pymupdf.csGRAY,alpha=alpha)
        for rect in regions:
            pix.set_rect((pymupdf.Rect(rect)*pymupdf.Matrix(1.5,1.5)).irect,(0,0) if alpha else (255,))
        assert masked_pixels(page,regions,alpha=alpha)==pix.samples


@pytest.fixture(scope='module')
def body_and_font(tmp_path_factory):
    folder = tmp_path_factory.mktemp('fixed-delivery')
    body = folder/'body.pdf'
    with pymupdf.open() as doc:
        for i in range(2):
            page = doc.new_page(width=595.28, height=841.89)
            page.insert_text((75,120), f'Internal layout proof {i+1}, no academic acceptance.')
        doc.save(body)
    font = folder/'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    return body, font


@pytest.mark.parametrize('subject', ['國綜','國寫','英文','數學A','數學B','社會','自然'])
def test_answers_all_subjects_survive_provenance_and_reject_rebuilt_pages(subject,body_and_font,tmp_path):
    body, font = body_and_font
    record = next(r for r in json.loads(DEFAULT_MAP.read_text(encoding='utf-8'))['subjects'] if r['subject']==subject)
    assets = ROOT/Path(record['assets'][0]['repository_path']).parent
    out, final = tmp_path/'answers.pdf', tmp_path/'final.pdf'
    compose(subject,body,assets,out,year='116',title='模擬試題',running_name='學測',font_path=font,kind='answers')
    publish_pdf(out,final)
    assert verify_pdf(final,subject,'answers')['status']=='pass-fixed-template'
    assert verify_pdf(body,subject,'answers')['status']=='fail-fixed-template'
    with pymupdf.open(final) as doc:
        doc[1].draw_rect((65,42,531,73), color=None,fill=(1,1,1))
        changed=tmp_path/'changed.pdf';doc.save(changed)
    assert any('locked-pixels-changed' in e for e in verify_pdf(changed,subject,'answers')['errors'])
    # Reusing correct pixels as a screenshot does not preserve the PDF layer.
    with pymupdf.open(final) as doc, pymupdf.open() as rebuilt:
        for p in doc:
            page=rebuilt.new_page(width=p.rect.width,height=p.rect.height)
            page.insert_image(page.rect,pixmap=p.get_pixmap())
        image_only=tmp_path/'screenshot.pdf';rebuilt.save(image_only)
    assert any('original-template-stream-missing' in e for e in verify_pdf(image_only,subject,'answers')['errors'])


def test_fake_passing_template_report_cannot_release_generic_pdf(saved_run):
    state,save=saved_run
    import check_hosted_run as gate
    with pymupdf.open() as doc:
        page=doc.new_page(width=595.28,height=841.89)
        page.insert_text((75,120),'Rebuilt booklet')
        doc.save('generic.pdf')
    state['pdfs']['question']['file']={'path':'generic.pdf','sha256':gate.sha(Path('generic.pdf'))}
    assert any('fixed-template' in e for e in evaluate(state,save)['errors'])


def test_math_missing_design_cannot_use_filled_passing_reviews(saved_run):
    state,save=saved_run
    exam=json.loads(Path('exam.json').read_text())
    exam['metadata']['subject']='數學A'
    exam['questions']=[{'id':str(i),'number':i+1,'score':5} for i in range(20)]
    state['exam']=save('exam.json',exam)
    result=evaluate(state,save)
    assert any('math_design:' in e for e in result['errors'])
    assert any('difficulty_balance:' in e for e in result['errors'])


def test_scaffolded_direct_substitution_cannot_be_counted_as_hard_work():
    exam={'metadata':{'subject':'數學A'},'questions':[{'id':str(i),'score':5} for i in range(20)]}
    rows=[{'id':str(i),'shortest_route':'Use the normal supplied in prior item, insert point',
           'decisive_steps':['Substitute x','Substitute y','Simplify'],
           'shortcut_search':'Prior normal removes the modelling step',
           'anchor_comparison':'Fixture','expected_minutes':4.2,'difficulty_band':'hard',
           'routine_only':True,'scaffolding_audit':'Previous answer supplies normal',
           'uses_prior_results':[str(i-1)] if i else [],'unresolved':[]} for i in range(20)]
    errors=review_errors(exam,{'author_context':'a','reviewer_context':'b','items':rows})
    assert any('hard label' in e for e in errors)
    assert any('50-point' in e for e in errors)
    assert any('routine-only' in e for e in errors)
    assert not any('outside existing 80-92' in e for e in errors) # Inflating time alone cannot pass.


def test_blind_packet_keeps_continuations_and_printed_explanations():
    exam={'metadata':{'subject':'自然'},'questions':[{'id':'1','prompt':'Read figure',
          'continuation_pages':[{'text':'additional observation'}], 'item_spec':{'difficulty':'hard'}}],
          'answers':[{'question_id':'1','explanation_blocks':[{'title':'Why','content':'Evidence'}],
                      'difficulty_label':'hard'}]}
    result=packet(exam)
    assert result['questions'][0]['continuation_pages']
    assert result['answers'][0]['explanation_blocks']
    assert 'difficulty' not in json.dumps(result)


def test_legacy_renderer_cannot_label_rebuilt_html_formal(tmp_path,capsys):
    from render_gsat_official_pdf import main
    assert main([str(tmp_path/'absent.json'),str(tmp_path/'out.pdf'),'--contract',str(tmp_path/'fake.json')])==2
    assert '--body' in capsys.readouterr().err
    assert not (tmp_path/'out.pdf').exists()


def test_local_fixed_wrapper_reuses_math_layers_and_final_tampering_fails(tmp_path,body_and_font,monkeypatch):
    import render_gsat_official_pdf as renderer
    import validate_exam_pack_contract as handoff
    body,font=body_and_font
    calls=[]
    monkeypatch.setattr(handoff,'require_handoff',lambda *args:calls.append(args))
    def forbidden(*args):
        pytest.fail('Formal wrapper called the legacy furniture renderer')
    monkeypatch.setattr(renderer,'_decorate_student_pages',forbidden)
    exam=tmp_path/'exam.json'
    exam.write_text(json.dumps({'metadata':{'subject':'數學A','academic_year':116}}),encoding='utf-8')
    output=tmp_path/'fixed.pdf'
    assert renderer.main([str(exam),str(output),'--contract',str(tmp_path/'test-contract.json'),
                          '--body',str(body),'--font',str(font)])==0
    assert calls and verify_pdf(output,'數學A','questions')['errors']==[]
    for index in (0,-1):
        with pymupdf.open(output) as doc:
            doc[index].draw_rect((70,200,500,700),fill=(1,1,1),color=None)
            changed=tmp_path/f'tampered-{index}.pdf';doc.save(changed)
        errors=verify_pdf(changed,'數學A','questions')['errors']
        assert any(('locked-pixels-changed' if index==0 else 'original-formula-body-changed') in e for e in errors)
