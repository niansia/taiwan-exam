"""Subject-specific examples must be distinct, portable and visually grounded."""
import hashlib
import json
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_web_knowledge import source_paths
from hosted_body_templates import render
from hosted_item_layout import geometry_errors
from read_web_knowledge import relevant
from package_skill import should_include
from verify_fixed_template_pdf import verify_pdf

CATALOG=json.loads((ROOT/'templates/hosted-subject-layouts.json').read_text(encoding='utf-8'))
PREVIEWS=ROOT/'docs/layout-examples/2026.09.22.22'


@pytest.mark.parametrize('entry',CATALOG['subjects'],ids=lambda e:e['slug'])
def test_subject_pair_is_routed_without_loading_other_subjects(entry,tmp_path):
    font=tmp_path/'font.ttf';font.write_bytes(pymupdf.Font('cjk').buffer)
    paths={p.relative_to(ROOT).as_posix() for p in source_paths()}
    for role in ('questions','solutions'):
        source=ROOT/'templates'/entry[role]
        spec=json.loads(source.read_text(encoding='utf-8'))
        assert spec['purpose']=='layout-reference-only' and spec['subject']==entry['subject']
        assert spec['booklet_role']==role and should_include(source)
        assert 'templates/'+entry[role] in paths
        assert relevant('templates/'+entry[role],entry['subject'])
        for other in CATALOG['subjects']:
            if other['subject']!=entry['subject']:assert not relevant('templates/'+entry[role],other['subject'])
        assert all(b['kind']!='solution' for b in spec['blocks']) if role=='questions' else any(b['kind']=='solution' for b in spec['blocks'])
        if entry['subject'] not in {'數學A','數學B'}:assert all(b['kind']!='fill' for b in spec['blocks'])
        with pytest.raises(ValueError,match='Placeholder'):
            render(spec,tmp_path/(role+'.pdf'),tmp_path/(role+'.json'),font,asset_root=source.parent)
        layout=render(spec,tmp_path/(role+'.pdf'),tmp_path/(role+'.json'),font,asset_root=source.parent,proof=True)
        with pymupdf.open(tmp_path/(role+'.pdf')) as doc:
            assert not geometry_errors(doc,layout['parts'])
            assert all(len(p.get_text())>0 for p in doc)


@pytest.mark.parametrize('entry',CATALOG['subjects'],ids=lambda e:e['slug'])
def test_downloaded_pair_keeps_its_own_fixed_layers(entry):
    manifest=json.loads((PREVIEWS/'manifest.json').read_text(encoding='utf-8'))
    row=next(r for r in manifest['subjects'] if r['subject']==entry['subject'])
    assert manifest['purpose']=='layout-reference-only' and manifest['full_exam'] is False
    for role,record in row['booklets'].items():
        pdf=PREVIEWS/record['file']
        assert hashlib.sha256(pdf.read_bytes()).hexdigest()==record['sha256']
        assert not should_include(pdf)  # Preview binaries must not bloat the Skill.
        assert verify_pdf(pdf,entry['subject'],'questions' if role=='questions' else 'answers')['status']=='pass-fixed-template'


def test_english_actual_inline_gaps_have_visible_underlines_and_one_bank():
    spec=json.loads((ROOT/'templates/hosted-english-questions.json').read_text(encoding='utf-8'))
    discourse=next(b for b in spec['blocks'] if b.get('id')=='layout-english-discourse')
    assert len(discourse['bank'])==5 and discourse['columns']==1
    completion=next(b for b in spec['blocks'] if b.get('id')=='layout-english-completion')
    assert len(completion['bank'])==10
    with pymupdf.open(PREVIEWS/'english-questions.pdf') as doc:
        for identifier in ('11','12','21','22','31','32','33','34'):
            found=False
            for page in doc:
                # Match the digits themselves: PDF word extraction can join
                # ideographic padding and the following punctuation to a gap.
                for box in page.search_for(identifier):
                    for drawing in page.get_drawings():
                        rect=drawing['rect']
                        if (rect.height<=2 and rect.width+0.01>=box.width and rect.x0<=box.x0+1 and
                            rect.x1>=box.x1-1 and box.y0+box.height/2<=rect.y0<=box.y1+5):found=True
            assert found, 'Missing actual gap underline: '+identifier


def test_writing_has_two_roles_and_does_not_turn_the_question_booklet_into_answer_grids():
    spec=json.loads((ROOT/'templates/hosted-writing-questions.json').read_text(encoding='utf-8'))
    assert [b['heading'] for b in spec['blocks'] if b['kind']=='passage']==['一、','二、']
    tasks=[b for b in spec['blocks'] if b['kind']=='constructed']
    assert [b['score'] for b in tasks]==[4,21,25]
    assert '80字' in tasks[0]['text'] and '400字' in tasks[1]['text']
    assert all(b['kind'] not in {'choice','multiple','fill'} for b in spec['blocks'])
