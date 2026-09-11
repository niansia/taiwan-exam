#!/usr/bin/env python3
"""Render a full GSAT paper in a CEEC-like print layout for internal mock use."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from gsat_115_templates import COVER_CSS as GSAT_115_COVER_CSS
from gsat_115_templates import SUBJECTS as GSAT_115_SUBJECTS
from gsat_115_templates import cover_markup as gsat_115_cover_markup
from render_exam import esc, image_data_uri, text_block, validate_exam


STYLE = r"""
@page { size: A4; margin: 13mm 17mm 15mm 17mm; }
* { box-sizing: border-box; }
html { background:#ddd; color:#111; font-family:"Noto Serif TC","PMingLiU","Times New Roman",serif; }
body { width:210mm; margin:0 auto; background:#fff; font-size:9.4pt; line-height:1.48; }
.cover { position:relative; z-index:3; background:#fff; min-height:269mm; break-after:page; padding:14mm 7mm 0; }
.brand { text-align:center; font-size:13pt; letter-spacing:.11em; margin-top:10mm; }
.mock-title { text-align:center; font-size:15pt; margin-top:4mm; letter-spacing:.07em; }
.subject-name { text-align:center; font-size:22pt; font-weight:700; letter-spacing:.24em; margin:8mm 0 5mm; }
.notice { text-align:center; font-weight:700; font-size:11.5pt; text-decoration:underline; margin:0 0 7mm; }
.notice-box { width:82%; margin:0 auto; border:1.5px solid #111; padding:8mm 9mm 6mm; }
.notice-box h2 { text-align:center; font-size:12pt; font-weight:400; letter-spacing:.25em; margin:0 0 5mm; }
.notice-box p { margin:0 0 3mm; }
.notice-box ul { margin:0 0 3mm 1.4em; padding:0; }
.notice-box li { margin:0 0 1.2mm; }
.internal-mark { position:absolute; bottom:6mm; left:0; right:0; text-align:center; font-family:sans-serif; font-size:8pt; color:#555; }
.running-head { display:none; }
.running-head .center { text-align:center; font-weight:700; border-bottom:1px solid #111; padding-bottom:.8mm; }
.running-head .right { text-align:right; }
.paper { padding-top:1mm; }
.section { margin:0 0 4mm; }
.section-title { font-size:12pt; margin:0 0 1mm; font-weight:700; }
.section-rule { border:1px solid #555; padding:.7mm 2mm; margin:0 0 3mm; font-size:8.5pt; }
.question-group { break-inside:avoid; }
.group-label { font-weight:700; margin:3mm 0 1mm; break-after:avoid-page; page-break-after:avoid; }
.group-label.allow-following-split { break-after:auto; page-break-after:auto; }
.stimulus { margin:1mm 0 2mm; text-align:justify; white-space:pre-wrap; orphans:2; widows:2; }
.stimulus.keep-together { break-inside:avoid-page; page-break-inside:avoid; }
.stimulus-question-tail { break-inside:avoid-page; page-break-inside:avoid; }
.question { display:flex; align-items:flex-start; gap:1mm; margin:0 0 3mm; break-inside:avoid-page; page-break-inside:avoid; }
.question>.qno { flex:0 0 6mm; }
.question>div:nth-child(2) { flex:1 1 auto; min-width:0; }
.question.allow-split { display:grid; grid-template-columns:6mm 1fr; break-inside:auto; page-break-inside:auto; }
.page-break { break-before:page; }
.qno { font-weight:400; }
.prompt { text-align:justify; }
.score { float:right; font-size:8pt; color:#444; }
.options { display:grid; gap:.6mm 4mm; margin-top:1mm; }
.cols-5 { grid-template-columns:repeat(5,minmax(0,1fr)); }
.cols-4 { grid-template-columns:repeat(4,minmax(0,1fr)); }
.cols-2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.cols-1 { grid-template-columns:1fr; }
.option { display:grid; grid-template-columns:6mm 1fr; }
.figure { margin:2mm auto; text-align:center; break-inside:avoid; }
.figure img { display:block; max-width:100%; max-height:88mm; margin:0 auto; object-fit:contain; }
.figure figcaption { font-size:8pt; margin-top:.8mm; }
.answer-lines { margin-top:2mm; }
.answer-line { height:7mm; border-bottom:.55px solid #aaa; }
.response-format { width:88%; margin:3mm auto 1mm; border-collapse:collapse; break-inside:avoid-page; page-break-inside:avoid; }
.response-format caption { caption-side:top; font-weight:400; margin-bottom:.7mm; }
.response-format th,.response-format td { border:1px solid #222; padding:2mm 3mm; }
.response-format th { text-align:center; font-weight:400; }
.response-format td { height:17mm; vertical-align:top; text-align:justify; }
.response-format .slot-label { display:inline-block; min-width:8mm; font-weight:700; }
.trace { font-family:sans-serif; font-size:7pt; color:#666; border-top:.5px solid #aaa; padding-top:1mm; margin-top:4mm; }
.answer-key { break-before:page; padding-top:2mm; font-size:9pt; line-height:1.38; }
.writing-continuation { break-before:page; min-height:245mm; padding-top:4mm; }
.writing-continuation h1 { font-size:12pt; margin:0 0 5mm; }
.answer-key h1 { font-size:15pt; text-align:center; letter-spacing:.2em; margin:0 0 3mm; }
.answer-summary { width:100%; border-collapse:collapse; font-size:7.8pt; line-height:1.15; }
.answer-summary th,.answer-summary td { border:1px solid #333; padding:.6mm 1.2mm; text-align:center; }
.details { columns:2; column-gap:7mm; column-rule:.5px solid #bbb; margin-top:4mm; }
.solution { break-inside:auto; border-bottom:.5px solid #ccc; padding-bottom:1.2mm; margin-bottom:1.8mm; }
.solution h2 { font-size:9.4pt; margin:0 0 .7mm; break-after:avoid-column; }
.solution p,.solution ol { margin:0 0 .7mm; }
.solution ol { padding-left:1.5em; }
@media print { html{background:#fff} body{width:auto;margin:0} }
"""


DISPLAY_NAMES = {
    "國綜":"國語文綜合能力測驗", "國寫":"國語文寫作能力測驗", "英文":"英文考科",
    "數學A":"數學A考科", "數學B":"數學B考科", "社會":"社會考科", "自然":"自然考科",
}


def verified_layout_css(meta: dict[str, Any], subject: str) -> str:
    """Bind the renderer to the measured type and horizontal page geometry.

    A paper-level page-count target must never be met by silently shrinking the
    body type or widening the text frame.  The selected verified Layout Profile
    is therefore applied after any author-provided CSS override.
    """
    folder = "國文" if subject in {"國綜", "國寫"} else subject
    profile_id = str(meta.get("layout_profile") or "")
    profile_dir = Path(__file__).resolve().parents[1] / "exam_packs" / str(meta.get("exam") or "學測") / "subjects" / folder / "blueprints" / "layout-profiles"
    profile_path = next((path for path in profile_dir.glob("*.json") if json.loads(path.read_text(encoding="utf-8-sig")).get("profile_id") == profile_id), None)
    if profile_path is None:
        return ""
    profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    typography = profile.get("typography") or {}
    body = typography.get("body") or {}
    geometry = profile.get("page_geometry") or {}
    try:
        size = float(body.get("size_pt"))
        width = float(geometry.get("width_pt"))
        left = float(geometry.get("body_left_pt")) * 25.4 / 72
        right = (width - float(geometry.get("body_right_pt"))) * 25.4 / 72
    except (TypeError, ValueError):
        return ""
    raw_families = [part.strip() for part in str(body.get("family") or "").split("/") if part.strip()]
    fallbacks = ["PMingLiU", "MingLiU", "Times New Roman", "serif"]
    families = []
    for family in [*raw_families, *fallbacks]:
        if family not in families:
            families.append(family)
    family_css = ",".join(f'"{family}"' if family != "serif" else family for family in families)
    running = profile.get("running_elements") or {}
    page_css = ''
    if running.get("alternating_headers"):
        # Reserve the measured inner-page header band.  The PDF wrapper writes
        # the actual page/total values only after pagination; the first (cover)
        # page retains the cover-sized content box.
        page_css = (
            '@page { margin-top:30mm; margin-bottom:15mm; }\n'
            '@page :first { margin:0; }\n'
        )
    return (
        page_css +
        f'@page {{ margin-left:{left:.2f}mm; margin-right:{right:.2f}mm; }}\n'
        f'body {{ font-family:{family_css}; font-size:{size:.2f}pt; }}\n'
        '.section-rule,.notice-box { font-family:"DFKai-SB","KaiTi","PMingLiU",serif; }\n'
        '.section-title,.group-label,.qno { font-family:"PMingLiU","MingLiU",serif; }'
    )


def render_visual(asset: Any, base: Path | None) -> str:
    if not asset:
        return ""
    src=image_data_uri(str(asset["path"]),base)
    width=asset.get("width_percent") or 62
    caption=f'<figcaption>{text_block(asset.get("caption"))}</figcaption>' if asset.get("caption") else ""
    return f'<figure class="figure" style="width:{width}%"><img src="{src}" alt="{esc(asset["alt"])}">{caption}</figure>'


def option_columns(options: list[dict[str,Any]], subject: str) -> int:
    if not options: return 1
    longest=max(len(str(x.get("text", ""))) for x in options)
    if longest > 42: return 1
    if longest > 19: return 2
    if subject in {"數學A","數學B"} and len(options)==5: return 5
    if subject=="英文" and len(options)==4: return 4
    return 2


def render_response_format(spec: Any, subject: str) -> str:
    """Render only measured, subject-specific answer-format evidence."""
    if not isinstance(spec, dict) or spec.get("kind") != "social_monitoring_table" or subject != "社會":
        return ""
    rows = spec.get("rows") or []
    if not rows:
        return ""
    cells = "".join(
        f'<tr><td><span class="slot-label">{esc(row.get("label"))}</span>{text_block(row.get("instruction"))}</td></tr>'
        for row in rows
    )
    caption = f'<caption>{text_block(spec.get("caption"))}</caption>' if spec.get("caption") else ""
    heading = text_block(spec.get("heading") or "作答格式")
    return f'<table class="response-format">{caption}<thead><tr><th>{heading}</th></tr></thead><tbody>{cells}</tbody></table>'


def render_question(q: dict[str,Any], base:Path|None, subject:str, *, show_stimulus:bool, show_visual:bool, group_range:str|None) -> str:
    # A Social Studies manual break must cite a measured page-role reason.
    # Otherwise let the evidence flow naturally; an ungrounded break previously
    # stranded half of the penultimate page.
    allow_break = q.get("page_break_before") and (subject != "社會" or q.get("page_break_basis"))
    page_break='<div class="page-break"></div>' if allow_break else ""
    raw_stimulus = str(q.get("group_stimulus") or "")
    # Avoid orphaning short evidence packets, but do not force a long packet to
    # the next page and leave a large terminal void.  Long material may split
    # naturally under the widow/orphan rules and keep each question intact.
    keep_stimulus = q.get("keep_stimulus_together") and len(raw_stimulus) <= 260
    label_class = "group-label" if keep_stimulus else "group-label allow-following-split"
    label=f'<div class="{label_class}">{esc(group_range)}</div>' if group_range else ""
    stimulus_class = "stimulus keep-together" if keep_stimulus else "stimulus"
    stimulus=f'<div class="{stimulus_class}">{text_block(q.get("group_stimulus"))}</div>' if show_stimulus and q.get("group_stimulus") else ""
    # A long terminal Social Studies packet may otherwise fill the penultimate
    # page with all of its evidence and strand only its questions on the final
    # page.  Split solely after a complete Chinese sentence, leaving meaningful
    # evidence on both pages and keeping the latter evidence with question 1.
    social_split = None
    if subject == "社會" and show_stimulus and group_range and len(raw_stimulus) >= 420:
        stops = [match.end() for match in re.finditer("。", raw_stimulus)]
        viable = [stop for stop in stops if stop >= 140 and len(raw_stimulus) - stop >= 180]
        if viable:
            split_at = min(viable, key=lambda stop: abs(stop - len(raw_stimulus) * 0.45))
            social_split = (raw_stimulus[:split_at], raw_stimulus[split_at:])
    visual=render_visual(q.get("visual_asset"),base) if show_visual else ""
    # Cloze, text-completion, and discourse items are printed inside their
    # shared passage.  Their scored-unit records still retain options/answers
    # for validation, but duplicating a worksheet row after the passage is not
    # the official English booklet convention.
    if q.get("suppress_question_display"):
        return f'{page_break}{label}{stimulus}{visual}'
    opts=q.get("options") or []
    cols=option_columns(opts,subject)
    options=""
    if opts:
        cells="".join(f'<div class="option"><span>({esc(o["label"])})</span><span>{text_block(o["text"])}</span></div>' for o in opts)
        options=f'<div class="options cols-{cols}">{cells}</div>'
    response_format = render_response_format(q.get("response_format_table"), subject)
    lines=""
    # Current Social Studies and English constructed responses are written on
    # the separate answer sheet.  Do not turn legacy authoring hints into
    # worksheet lines in either student booklet.
    if q.get("answer_space_lines") and subject not in {"社會", "英文"}:
        lines='<div class="answer-lines">'+('<div class="answer-line"></div>'*int(q["answer_space_lines"]))+'</div>'
    # Shared section directions normally carry objective-item scores.  A
    # per-item score is printed only when the selected role explicitly opts in;
    # authored prompts may already contain their official inline score wording.
    score=f'<span class="score">（{esc(q.get("score"))}分）</span>' if q.get("score") is not None and q.get("show_score_label", False) else ""
    split_class=" allow-split" if q.get("allow_page_split") else ""
    article = f'<article class="question{split_class}"><div class="qno">{esc(q["number"])}.</div><div><div class="prompt">{score}{text_block(q["prompt"])}</div>{visual}{options}{response_format}{lines}</div></article>'
    if social_split:
        lead, tail = social_split
        return (
            f'{page_break}{label}<div class="stimulus">{text_block(lead)}</div>'
            f'<div class="stimulus-question-tail"><div class="stimulus">{text_block(tail)}</div>{article}</div>'
        )
    return f'{page_break}{label}{stimulus}{article}'


def _cover_year(meta: dict[str, Any]) -> str:
    raw = str(meta.get("academic_year") or meta.get("running_year_label") or "116")
    match = re.search(r"\d{3}", raw)
    return match.group(0) if match else raw


def cover(meta:dict[str,Any], instructions:list[str]) -> str:
    subject = meta.get("paper_subject") or meta.get("subject")
    if subject in GSAT_115_SUBJECTS:
        return gsat_115_cover_markup(
            subject,
            year=_cover_year(meta),
            exam_name=str(meta.get("cover_exam_name") or "學科能力測驗模擬試題"),
            # The measured hierarchy is reusable; the official organisation
            # name is not.  Keep generated papers unmistakably downstream.
            organization="Taiwan Exam 模擬試題",
            cover_title=str(meta.get("cover_year_title") or ""),
        )
    label=meta.get("paper_label") or DISPLAY_NAMES.get(meta.get("subject"),meta.get("subject"))
    duration=meta.get("duration_minutes")
    bullets="".join(f'<li>{text_block(x)}</li>' for x in instructions)
    disclaimer=meta.get("cover_disclaimer") or "本卷為原創內部測試題，不是大學入學考試中心正式試題。"
    internal_mark=meta.get("internal_mark") or "版式參照 115 學年度正式題本｜內容原創｜禁止對外冒充正式試題"
    return f'''<section class="cover"><div class="brand">Taiwan Exam 內部測試</div><div class="mock-title">116學年度學科能力測驗模擬試題</div><div class="subject-name">{esc(label)}</div><div class="notice">請於考試開始鈴響起，在答題卷簽名欄位以正楷簽名</div><div class="notice-box"><h2>作答注意事項</h2><p>考試時間：{esc(duration)} 分鐘</p><p>作答方式：</p><ul>{bullets}</ul><p>※ {text_block(disclaimer)}</p></div><div class="internal-mark">{text_block(internal_mark)}</div></section>'''


def solutions(exam:dict[str,Any]) -> str:
    answers=exam.get("answers") or []
    if not answers:return ""
    number={q["id"]:q["number"] for q in exam["questions"]}
    rows="".join(f'<tr><td>{esc(number.get(a["question_id"],a["question_id"]))}</td><td>{text_block(a.get("final_answer"))}</td><td>{esc(a.get("difficulty_label") or "-")}</td></tr>' for a in answers)
    details=[]
    for a in answers:
        reasoning=a.get("reasoning") or []
        body='<ol>'+''.join(f'<li>{text_block(x)}</li>' for x in reasoning)+'</ol>' if reasoning else ""
        for block in a.get("explanation_blocks") or []:
            body+=f'<p><b>{esc(block.get("title") or "說明")}：</b>{text_block(block.get("content"))}</p>'
        details.append(f'<article class="solution"><h2>第 {esc(number.get(a["question_id"]))} 題　答案：{text_block(a.get("final_answer"))}</h2>{body}</article>')
    return f'<section class="answer-key"><h1>答案與解析</h1><table class="answer-summary"><thead><tr><th>題號</th><th>答案</th><th>難度</th></tr></thead><tbody>{rows}</tbody></table><div class="details">{"".join(details)}</div></section>'


def render(exam:dict[str,Any], *, include_answers:bool=True, asset_base:Path|None=None, run_contract:Path|None=None) -> str:
    from validate_exam_pack_contract import require_handoff
    require_handoff(exam, asset_base, run_contract)
    errors=validate_exam(exam)
    if errors: raise ValueError("；".join(errors))
    meta=exam["metadata"]; subject=meta.get("paper_subject") or meta["subject"]
    short=meta.get("paper_label") or DISPLAY_NAMES.get(subject,subject)
    sections=[]
    sorted_q=sorted(exam["questions"],key=lambda x:x["number"])
    by_section={s["id"]:[] for s in exam["sections"]}
    for q in sorted_q:by_section[q["section_id"]].append(q)
    for section in exam["sections"]:
        qs=by_section[section["id"]]; notes=" ".join(section.get("instructions") or [])
        parts=[f'<section class="section"><h1 class="section-title">{esc(section["title"])}</h1>',f'<div class="section-rule">{text_block(notes)}</div>' if notes else ""]
        i=0
        while i<len(qs):
            q=qs[i]; stimulus=q.get("group_stimulus"); j=i+1
            if stimulus:
                while j<len(qs) and qs[j].get("group_stimulus")==stimulus:j+=1
            group_range=f'第 {q["number"]} 至 {qs[j-1]["number"]} 題為題組' if stimulus and j-i>1 else None
            shown_visuals=set()
            group_parts=[]
            for k in range(i,j):
                asset=qs[k].get("visual_asset") or {}; path=asset.get("path")
                show_visual=not path or path not in shown_visuals
                if path:shown_visuals.add(path)
                group_parts.append(render_question(qs[k],asset_base,subject,show_stimulus=(k==i),show_visual=show_visual,group_range=group_range if k==i else None))
            rendered_group=''.join(group_parts)
            parts.append('<div class="question-group">'+rendered_group+'</div>' if q.get("keep_group_together") else rendered_group)
            i=j
        parts.append('</section>'); sections.append("".join(parts))
    answer_html=solutions(exam) if include_answers else ""
    continuation='''<section class="writing-continuation"><h1>第二題續頁</h1><p>請再檢視題目要求，確認文章具備具體經驗或想像、清楚的認知轉折與完整結構。實際作答請書寫於答案卷指定範圍內。</p><p style="margin-top:210mm;text-align:center;font-weight:700">試題至此結束</p></section>''' if meta.get("paper_subject")=="國寫" else ""
    custom_css=str(meta.get("layout_css_override") or "")
    profile_css=verified_layout_css(meta,subject)
    # Chromium fragments fixed elements unpredictably after a full-page cover.
    # Keep the semantic hook in the HTML but hide it in print; an unreliable
    # repeated header/footer must never cover an option or source line.
    year = _cover_year(meta)
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>{esc(meta["title"])}</title><style>{STYLE}\n{GSAT_115_COVER_CSS}\n{custom_css}\n{profile_css}</style></head><body><div class="running-head"><span>第　頁<br>共　頁</span><span class="center">請記得在答題卷簽名欄位以正楷簽全名</span><span class="right">{esc(year)}年學測<br>{esc(short)}</span></div>{cover(meta,exam["instructions"])}<main class="paper">{"".join(sections)}{continuation}</main>{answer_html}</body></html>'''


def main(argv=None)->int:
    p=argparse.ArgumentParser();p.add_argument("input",type=Path);p.add_argument("output",type=Path);p.add_argument("--student-only",action="store_true");p.add_argument('--contract',type=Path);args=p.parse_args(argv)
    try:
        exam=json.loads(args.input.read_text(encoding="utf-8-sig")); html=render(exam,include_answers=not args.student_only,asset_base=args.input.resolve().parent,run_contract=args.contract);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(html,encoding="utf-8")
    except (OSError,ValueError,json.JSONDecodeError) as e:print(f"錯誤：{e}",file=sys.stderr);return 2
    print(f"已輸出學測正式版型 HTML：{args.output}");return 0


if __name__=="__main__":raise SystemExit(main())
