#!/usr/bin/env python3
"""Compose a GSAT fixed PDF; legacy HTML output is internal proof only."""
from __future__ import annotations
import argparse,json,shutil,subprocess,sys,tempfile
from pathlib import Path
from render_gsat_official import render
from render_pdf import find_browser
from pdf_provenance import publish_pdf
from safe_rendering import browser_flags, prepare_html
from gsat_115_templates import SIGNATURE_RUNNING, SUBJECTS as GSAT_115_SUBJECTS


def _layout_profile(exam, input_path):
    meta = exam.get('metadata') or {}
    subject = meta.get('paper_subject') or meta.get('subject')
    folder = '國文' if subject in {'國綜', '國寫'} else subject
    root = Path(__file__).resolve().parents[1]
    profile_dir = root / 'exam_packs' / str(meta.get('exam') or '學測') / 'subjects' / str(folder) / 'blueprints' / 'layout-profiles'
    for path in profile_dir.glob('*.json'):
        profile = json.loads(path.read_text(encoding='utf-8-sig'))
        if profile.get('profile_id') == meta.get('layout_profile'):
            return profile
    return None


def _print_html(executable, profile_dir, html, pdf_path):
    html_path = profile_dir / (pdf_path.stem + '.html')
    runtime_dir = profile_dir / (pdf_path.stem + '-runtime')
    runtime_dir.mkdir(exist_ok=False)
    html_path.write_text(prepare_html(html), encoding='utf-8')
    completed = subprocess.run(
        [str(executable), *browser_flags(runtime_dir), '--no-pdf-header-footer',
         f'--print-to-pdf={pdf_path}', html_path.as_uri()],
        capture_output=True, text=True, timeout=90,
    )
    if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        raise RuntimeError(completed.stderr or completed.stdout or 'PDF output missing')


def _decorate_student_pages(source, destination, exam, layout, student_pages):
    """Add measured alternating headers after the real page total is known."""
    import pymupdf

    running = (layout or {}).get('running_elements') or {}
    if not running.get('alternating_headers'):
        shutil.copyfile(source, destination)
        return
    meta = exam.get('metadata') or {}
    raw_year = str(meta.get('academic_year') or meta.get('running_year_label') or '116')
    cover_exam_name = str(meta.get('cover_exam_name') or '學科能力測驗模擬試題')
    running_exam_name = str(meta.get('running_exam_name') or ('學測' if '學科能力測驗' in cover_exam_name else cover_exam_name))
    year_label = f'{raw_year}年{running_exam_name}' if raw_year.isdigit() else raw_year
    subject = str(meta.get('paper_subject') or meta.get('subject') or '')
    subject_label = str(meta.get('paper_label') or (GSAT_115_SUBJECTS.get(subject) or {}).get('label') or subject)
    signature = str(running.get('signature') or SIGNATURE_RUNNING)
    inner_total = max(0, student_pages - 1)
    fontfile = Path('C:/Windows/Fonts/kaiu.ttf')
    doc = pymupdf.open(source)
    for physical_index in range(1, min(student_pages, len(doc))):
        page = doc[physical_index]
        inner = physical_index
        page.insert_font(fontname='KaiuExam', fontfile=str(fontfile) if fontfile.is_file() else None)
        page_mark = f'第 {inner:2d} 頁\n共 {inner_total:2d} 頁'
        subject_mark = f'{year_label}\n{subject_label}'
        left, right = (page_mark, subject_mark) if inner % 2 else (subject_mark, page_mark)
        page.insert_textbox(pymupdf.Rect(62.5, 41.5, 155, 72), left,
                            fontname='KaiuExam', fontsize=10, lineheight=1.28, align=0)
        page.insert_textbox(pymupdf.Rect(444, 41.5, 536.8, 72), right,
                            fontname='KaiuExam', fontsize=10, lineheight=1.28, align=2)
        strip = pymupdf.Rect(195.5, 42, 400, 57.5)
        page.draw_rect(strip, color=None, fill=(0.86, 0.86, 0.86), overlay=True)
        page.insert_textbox(strip, signature, fontname='KaiuExam', fontsize=10,
                            lineheight=1.0, align=1, overlay=True)
        footer = pymupdf.Rect(62.5 if inner % 2 else 455, 794, 140 if inner % 2 else 536.8, 814)
        page.insert_textbox(footer, f'- {inner} -', fontname='Times-Roman', fontsize=10,
                            align=0 if inner % 2 else 2, overlay=True)
    doc.save(destination, garbage=4, deflate=True)
    doc.close()

def main(argv=None)->int:
    p=argparse.ArgumentParser();p.add_argument("input",type=Path);p.add_argument("output",type=Path);p.add_argument("--student-only",action="store_true");p.add_argument("--browser",type=Path);p.add_argument("--no-provenance",action="store_true");p.add_argument('--contract',type=Path);p.add_argument('--proof-only',action='store_true')
    p.add_argument('--body', type=Path, help='Measured transparent A4 body-only PDF; no cover, formula or furniture')
    p.add_argument('--kind', choices=('questions','answers'), default='questions')
    p.add_argument('--asset-dir', type=Path)
    p.add_argument('--font', type=Path)
    a=p.parse_args(argv)
    try:
        if not a.proof_only:
            if not a.body or not a.font or not a.contract:
                raise ValueError('Fixed PDF requires --contract, --body and --font. Rebuilt HTML is --proof-only; formal booklets use compose_hosted_pdf with original assets.')
            if a.output.exists():
                raise ValueError('Preserve existing output; choose a new filename')
            from validate_exam_pack_contract import require_handoff
            from compose_hosted_pdf import compose
            from verify_fixed_template_pdf import verify_pdf
            from fetch_hosted_template_assets import DEFAULT_MAP
            exam=json.loads(a.input.read_text(encoding='utf-8-sig'))
            require_handoff(exam, a.input.resolve().parent, a.contract)
            meta=exam['metadata']; subject=meta.get('paper_subject') or meta['subject']
            records=json.loads(DEFAULT_MAP.read_text(encoding='utf-8-sig'))['subjects']
            record=next(r for r in records if r['subject']==subject)
            asset_dir=a.asset_dir or Path(__file__).resolve().parents[1]/Path(record['assets'][0]['repository_path']).parent
            with tempfile.TemporaryDirectory(prefix='gsat-fixed-') as folder:
                composed=Path(folder)/'composed.pdf'; final=Path(folder)/'final.pdf'
                compose(subject, a.body, asset_dir, composed,
                        year=str(meta.get('academic_year') or '116'),
                        title=str(meta.get('cover_exam_name') or '學科能力測驗模擬試題'),
                        running_name=str(meta.get('running_exam_name') or '學測'),
                        font_path=a.font, kind=a.kind)
                publish_pdf(composed, final, provenance=not a.no_provenance)
                report=verify_pdf(final, subject, a.kind, asset_dir)
                if report['errors']:raise ValueError('; '.join(report['errors']))
                a.output.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(final,a.output)
            print(f'已輸出固定 PDF 待驗收校樣：{a.output}')
            return 0
        exam=json.loads(a.input.read_text(encoding="utf-8-sig"));html=render(exam,include_answers=not a.student_only,asset_base=a.input.resolve().parent,run_contract=a.contract);browser=find_browser(a.browser);layout=_layout_profile(exam,a.input)
        if a.proof_only:
            html=html.replace('</body>', '<div style="position:fixed;bottom:2mm;left:20mm;font-size:8pt">內部排版校樣：未通過正式試卷交付驗收</div></body>')
        with tempfile.TemporaryDirectory(prefix="gsat-official-") as d:
            d=Path(d);pp=d/"paper.pdf";decorated=d/"paper-decorated.pdf"
            _print_html(browser,d,html,pp)
            if a.student_only:
                import pymupdf
                student_pages=len(pymupdf.open(pp))
            else:
                student_pdf=d/"student-count.pdf"
                student_html=render(exam,include_answers=False,asset_base=a.input.resolve().parent,run_contract=a.contract)
                _print_html(browser,d,student_html,student_pdf)
                import pymupdf
                student_pages=len(pymupdf.open(student_pdf))
            _decorate_student_pages(pp,decorated,exam,layout,student_pages)
            a.output.parent.mkdir(parents=True,exist_ok=True);publish_pdf(decorated,a.output,provenance=not a.no_provenance)
    except Exception as e:print(f"錯誤：{e}",file=sys.stderr);return 2
    print(f"已輸出{'內部校樣' if a.proof_only else '待逐頁驗收'} PDF：{a.output}");return 0
if __name__=="__main__":raise SystemExit(main())
