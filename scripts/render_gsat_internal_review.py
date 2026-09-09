#!/usr/bin/env python3
"""Render explicitly uncalibrated, full-length GSAT review proofs.

This renderer is deliberately separate from the formal renderer.  It accepts
only custom-practice data carrying a reference-only layout status and prints a
visible internal-review label on every page.  Fixed page assignments make the
paper useful for density review without weakening the formal layout gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from render_exam import esc, image_data_uri, text_block, validate_exam


STYLE = r"""
@page { size:A4; margin:0; }
* { box-sizing:border-box; }
html,body { margin:0; padding:0; background:#fff; color:#111;
  font-family:"Noto Serif TC","PMingLiU","Times New Roman",serif; }
body { font-size:10.35pt; line-height:1.56; }
body.paper-英文 { font-size:9.75pt; line-height:1.49; }
body.paper-英文 .sheet:not(.cover) { padding-left:20.5mm; padding-right:20.5mm; }
body.paper-英文 .group-label { font-weight:400; text-decoration:underline; }
body.paper-英文 .stimulus { line-height:1.48; white-space:normal; }
body.paper-英文 .stimulus p { margin:0 0 .75mm; }
body.paper-英文 .stimulus.english-prose p { text-indent:2em; }
body.paper-英文 .stimulus.english-prose p.source-line { text-indent:0; }
body.paper-英文 .stimulus.english-blocks p { margin-bottom:1.35mm; text-indent:0; }
body.paper-英文 .stimulus.english-completion { line-height:1.94; }
body.paper-英文 .stimulus.english-completion p { margin-bottom:2mm; }
body.paper-英文 .stimulus.english-discourse { line-height:1.84; }
body.paper-英文 .stimulus.english-discourse p { margin-bottom:2.1mm; }
body.paper-英文 .question.section-reading { margin-bottom:2.35mm; }
.english-blank { display:inline-block; min-width:13mm; border-bottom:.65px solid #222;
  text-align:center; line-height:1.12; text-indent:0; margin:0 .45mm; }
body.paper-國寫 {
  font-family:"DFKai-SB","BiauKai","標楷體","PMingLiU",serif;
  font-size:12pt;
  line-height:1.70;
}
body.paper-國寫 .sheet:not(.cover) { padding-left:22mm; padding-right:22mm; }
body.paper-國寫 .prompt,body.paper-國寫 .stimulus,body.paper-國寫 .writing-continuation {
  text-align:justify;
  letter-spacing:.01em;
}
body.paper-數學A,body.paper-數學B {
  font-family:"Times New Roman","PMingLiU","MingLiU","新細明體",serif;
  font-size:11pt;
  line-height:1.58;
}
body.paper-數學A .math-cover .notice,body.paper-數學B .math-cover .notice,
body.paper-數學A .section-head,body.paper-數學B .section-head,
body.paper-數學A .section-rule,body.paper-數學B .section-rule {
  font-family:"DFKai-SB","BiauKai","標楷體","PMingLiU",serif;
}
body.paper-數學A .math-inline,body.paper-數學B .math-inline,
body.paper-數學A .option,body.paper-數學B .option {
  font-family:"Times New Roman","PMingLiU","新細明體",serif;
}
.paper-數學A sub,.paper-數學A sup,.paper-數學B sub,.paper-數學B sup {
  font-family:"Times New Roman",serif;
  font-size:.76em;
  line-height:0;
  position:relative;
}
.paper-數學A sub,.paper-數學B sub { vertical-align:baseline; bottom:-.22em; }
.paper-數學A sup,.paper-數學B sup { vertical-align:baseline; top:-.43em; }
.sheet { position:relative; width:210mm; height:297mm; padding:15mm 17mm 15mm;
  overflow:hidden; break-after:page; background:#fff; }
.cover { padding:23mm 23mm 16mm; }
.org { text-align:center; font-size:13pt; letter-spacing:.08em; margin-top:8mm; }
.year { text-align:center; font-size:15pt; letter-spacing:.06em; margin-top:5mm; }
.subject { text-align:center; font-size:23pt; font-weight:700; letter-spacing:.24em;
  margin:10mm 0 6mm; }
.sign { text-align:center; font-size:11pt; font-weight:700; text-decoration:underline;
  margin-bottom:8mm; }
.notice { width:86%; margin:0 auto; border:1.4px solid #222; padding:7mm 9mm 6mm; }
.notice h1 { margin:0 0 4mm; text-align:center; font-size:12pt; font-weight:400;
  letter-spacing:.22em; }
.notice h2 { margin:3mm 0 1mm; font-size:9.6pt; }
.notice p { margin:0 0 1.3mm; }
.notice ul { padding-left:1.35em; margin:0; }
.notice li { margin:0 0 1.1mm; }
.math-cover { padding:20mm 22mm 14mm; }
.math-cover .org { margin-top:5mm; font:19.98pt/1.15 "DFKai-SB","BiauKai","標楷體",serif; }
.math-cover .year { margin-top:3mm; font:19.98pt/1.15 "DFKai-SB","BiauKai","標楷體",serif; }
.math-cover .subject { margin:5mm 0 3mm; font:25.98pt/1.12 "DFKai-SB","BiauKai","標楷體",serif; }
.math-cover .sign { margin-bottom:4mm; font:18pt/1.2 "DFKai-SB","BiauKai","標楷體",serif; }
.math-cover .notice { width:100%; padding:3.5mm 5mm 3mm; font-size:12pt; line-height:1.30; min-height:162mm; }
.math-cover .notice h1 { margin-bottom:2mm; font-size:16.02pt; }
.math-cover .notice h2 { margin:1.8mm 0 .7mm; font-size:12pt; }
.math-cover .notice li { margin-bottom:.55mm; }
.writing-cover { padding:22mm 23mm 16mm; }
.writing-cover .org { margin-top:7mm; font-size:12pt; }
.writing-cover .year { margin-top:5mm; font-size:18pt; }
.writing-cover .subject { margin:9mm 0 6mm; font-size:25pt; letter-spacing:.16em; }
.writing-cover .notice { width:92%; min-height:138mm; padding:8mm 10mm; font-size:11pt; line-height:1.55; }
.writing-cover .notice h1 { font-size:14pt; }
.writing-cover .notice h2 { font-size:11pt; }
.mark-example { max-width:100%; margin:.7mm 0 1mm 6mm; font-family:"Times New Roman",sans-serif; white-space:nowrap; }
.mark-row { display:inline-grid; grid-template-columns:13mm repeat(12,4.8mm); border:.6px solid #444; }
.mark-row span { text-align:center; border-right:.4px solid #888; line-height:4.2mm; height:4.2mm; }
.mark-row span:last-child { border-right:0; }
.mark-row + .mark-row { border-top:0; }
.mark-row .marked { background:#222; color:#fff; font-weight:700; }
.cover-fill-example { display:grid; grid-template-columns:max-content max-content minmax(0,1fr);
  align-items:center; gap:1.2mm; max-width:calc(100% - 6mm); margin:.7mm 0 .4mm 6mm; white-space:normal; }
.cover-fill-example > span:last-child { min-width:0; }
.cover-fill-example .fill-format { margin:0; transform:none; }
.cover-fill-example .fill-slot { width:7.15mm; height:7.15mm; font-size:7.8pt; }
.cover-fill-example .fill-slot::before { inset:-.08mm 0 0; font-size:20.2pt; }
.cover-fill-example .fill-fraction .fill-slots { min-width:15mm; padding:0 .8mm .45mm; }
.cover-fill-direction { margin:.1mm 0 .35mm 6mm; }
.prototype { position:absolute; left:18mm; right:18mm; bottom:8mm; border-top:.6px solid #777;
  padding-top:2mm; text-align:center; font:7.8pt/1.35 sans-serif; color:#555; }
.header { height:9mm; display:grid; grid-template-columns:31mm 1fr 35mm; gap:2mm;
  align-items:start; font-size:7.7pt; }
.header .mid { text-align:center; border-bottom:.7px solid #222; font-weight:700; padding-bottom:.8mm; }
.header .right { text-align:right; }
.content { height:251mm; overflow:hidden; padding-top:1mm; }
.section-head { font-size:12pt; font-weight:700; letter-spacing:.03em; line-height:1.72; margin:0 0 1.2mm; }
.section-rule { border:1px solid #555; padding:.8mm 2mm; margin:0 0 2.2mm; font-size:8.4pt; }
.group-label { font-weight:700; margin:2.2mm 0 .8mm; }
.stimulus { white-space:pre-wrap; text-align:justify; margin:.9mm 0 2mm;
  line-height:1.6; }
.stimulus + .question { margin-top:1.4mm; }
.question { display:grid; grid-template-columns:6.5mm 1fr; column-gap:.6mm;
  margin:0 0 3.2mm; break-inside:avoid; }
.paper-數學A .question,.paper-數學B .question { margin-bottom:5.1mm; }
.qno { font-weight:700; }
.prompt { text-align:justify; }
.score { float:right; font-size:8pt; margin-left:2mm; }
.options { display:grid; gap:.8mm 5.2mm; margin-top:1.1mm; }
.layout-row-5 { grid-template-columns:repeat(5,max-content); justify-content:space-between; }
.layout-row-4 { grid-template-columns:repeat(4,max-content); justify-content:space-between; }
.layout-grid-3-2 { grid-template-columns:repeat(3,minmax(0,1fr)); column-gap:9mm; }
.layout-grid-2 { grid-template-columns:repeat(2,minmax(0,1fr)); column-gap:12mm; }
.layout-stack { grid-template-columns:1fr; row-gap:.65mm; }
.paper-數學A .layout-stack,.paper-數學B .layout-stack { row-gap:1.15mm; }
.layout-auto-5 { grid-template-columns:repeat(5,minmax(0,1fr)); }
.layout-auto-4 { grid-template-columns:repeat(4,minmax(0,1fr)); }
.layout-auto-2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.layout-auto-1 { grid-template-columns:1fr; }
.option { display:grid; grid-template-columns:6.2mm 1fr; align-items:baseline; min-width:0; }
.layout-row-5 .option,.layout-row-4 .option { grid-template-columns:auto auto; column-gap:1.2mm; white-space:nowrap; }
.figure { margin:1.5mm auto; text-align:center; break-inside:avoid; }
.figure img { display:block; max-width:100%; max-height:69mm; margin:0 auto; object-fit:contain; }
.figure img.grayscale { filter:grayscale(100%) contrast(1.08); }
.figure figcaption { font-size:7.7pt; margin-top:.6mm; }
.stem-side { display:grid; grid-template-columns:minmax(0,1.08fr) minmax(0,.92fr); gap:5mm; align-items:start; }
.stem-side .figure { width:100% !important; margin:.2mm auto 0; }
.answer-lines { margin-top:1.5mm; }
.answer-line { height:6mm; border-bottom:.5px solid #aaa; }
.fill-format { display:inline-flex; align-items:center; margin:0 .8mm; vertical-align:middle; }
.fill-slots { display:inline-flex; gap:.35mm; align-items:center; justify-content:center; }
.fill-slot { position:relative; display:inline-flex; width:9.16mm; height:9.16mm; align-items:center; justify-content:center; font:10.02pt/1 "Times New Roman",serif; background:#fff; }
.fill-slot::before { content:"○"; position:absolute; inset:-.1mm 0 0; display:flex; align-items:center; justify-content:center; font:25.98pt/1 "DFKai-SB","BiauKai","標楷體",serif; z-index:0; }
.fill-slot > span { position:relative; z-index:1; white-space:nowrap; }
.integer-rail { display:inline-flex; justify-content:center; padding:0 1mm .75mm; border-bottom:1px solid #222; }
.fill-fraction { display:inline-grid; grid-template-rows:auto auto; gap:.45mm; align-items:center; vertical-align:middle; }
.fill-fraction .fill-slots { min-width:19mm; padding:0 1mm .75mm; border-bottom:1px solid #222; }
.footer { position:absolute; left:17mm; right:17mm; bottom:5mm; display:grid;
  grid-template-columns:1fr auto 1fr; font-size:7.5pt; color:#444; }
.footer .center { text-align:center; }
.footer .right { text-align:right; }
.trace { font-size:7.2pt; color:#666; border-top:.5px solid #999; margin-top:3mm; padding-top:1mm; }
.formula-sheet { font-size:9.2pt; line-height:1.72; padding:3mm 1mm; }
.formula-title { font-weight:700; font-size:10.2pt; margin-bottom:2.4mm; }
.formula-lines { white-space:pre-wrap; }
.answer-cover h1 { text-align:center; margin:55mm 0 8mm; font-size:22pt; letter-spacing:.18em; }
.answer-cover p { text-align:center; font-family:sans-serif; }
.answer-page { min-height:267mm; padding:15mm 17mm; break-after:page; }
.answer-page h1 { font-size:14pt; text-align:center; letter-spacing:.12em; }
.answer-grid { width:100%; border-collapse:collapse; font-size:8.5pt; }
.answer-grid th,.answer-grid td { border:1px solid #444; padding:1.2mm; text-align:center; }
.solution { break-inside:avoid; border-bottom:.5px solid #bbb; margin:0 0 2.3mm; padding-bottom:1.5mm; }
.solution h2 { font-size:9.6pt; margin:0 0 .6mm; }
.solution p,.solution ol { margin:.5mm 0; }
.solution ol { padding-left:1.5em; }
.two-col { columns:2; column-gap:8mm; column-rule:.5px solid #bbb; }
.writing-note { border:1px solid #777; padding:4mm; margin:4mm 0; }
.writing-continuation { border-top:1px solid #333; padding-top:3mm; white-space:pre-wrap; }
.writing-continuation h2 { font-size:12pt; margin:0 0 2mm; }
"""


def _columns(options: list[dict[str, Any]], subject: str) -> int:
    if not options:
        return 1
    longest = max(len(str(o.get("text", ""))) for o in options)
    if longest > 52:
        return 1
    if longest > 23:
        return 2
    if subject in {"數學A", "數學B"} and len(options) == 5:
        return 5
    if subject == "英文" and len(options) == 4:
        return 4
    return 2


OPTION_LAYOUTS = {"row-5", "row-4", "grid-3-2", "grid-2", "stack"}

SUBSCRIPT_CHARS = "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"
SUPERSCRIPT_CHARS = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ"
SUBSCRIPT_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ", "0123456789+-=()aehijklmnoprstuvx")
SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ", "0123456789+-=()ni")


def _math_text_block(value: Any) -> str:
    """Replace font-dependent Unicode scripts with semantic HTML scripts."""
    rendered = esc(value)
    rendered = re.sub(
        f"([{re.escape(SUBSCRIPT_CHARS)}]+)",
        lambda match: f'<sub>{match.group(1).translate(SUBSCRIPT_MAP)}</sub>',
        rendered,
    )
    rendered = re.sub(
        f"([{re.escape(SUPERSCRIPT_CHARS)}]+)",
        lambda match: f'<sup>{match.group(1).translate(SUPERSCRIPT_MAP)}</sup>',
        rendered,
    )
    rendered = re.sub(r"([A-Za-z])(?=<(?:sub|sup)>)", r"<i>\1</i>", rendered)
    return rendered.replace("\n", "<br>\n")


def _paper_text(value: Any, subject: str) -> str:
    if subject in {"數學A", "數學B"}:
        return _math_text_block(value)
    rendered = text_block(value)
    if subject == "英文":
        rendered = re.sub(r"\[\[(\d+)\]\]", r'<span class="english-blank">\1</span>', rendered)
        rendered = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", rendered)
    return rendered


def _option_layout(q: dict[str, Any], subject: str) -> str:
    requested = q.get("option_layout")
    if requested:
        if requested not in OPTION_LAYOUTS:
            raise ValueError(f'第 {q.get("number")} 題 option_layout 不合法：{requested}')
        return f"layout-{requested}"
    if subject in {"數學A", "數學B"} and int(q.get("layout_contract_version") or 0) >= 3:
        raise ValueError(f'數學第 {q.get("number")} 題缺少明確 option_layout')
    return f"layout-auto-{_columns(q.get('options') or [], subject)}"


def _visual(asset: dict[str, Any] | None, base: Path, *, side: bool = False) -> str:
    if not asset:
        return ""
    src = image_data_uri(asset["path"], base)
    width = 100 if side else int(asset.get("width_percent") or 62)
    image_class = "grayscale" if asset.get("grayscale") else ""
    caption = f'<figcaption>{text_block(asset.get("caption"))}</figcaption>' if asset.get("caption") else ""
    max_height = asset.get("max_height_mm")
    height_style = f'max-height:{float(max_height):g}mm' if max_height else ''
    image_style = f' style="{height_style}"' if height_style else ""
    return f'<figure class="figure" style="width:{width}%"><img class="{image_class}"{image_style} src="{src}" alt="{esc(asset["alt"])}">{caption}</figure>'


def _fill_format(q: dict[str, Any]) -> str:
    spec = q.get("answer_format") or {}
    if not spec:
        return ""
    number = esc(q.get("number"))
    def slots(count: int, start: int = 1) -> str:
        cells = "".join(f'<span class="fill-slot"><span>{number}-{start + i}</span></span>' for i in range(count))
        return f'<span class="fill-slots">{cells}</span>'
    if spec.get("kind") == "fraction":
        numerator = int(spec.get("numerator_slots") or 1)
        denominator = int(spec.get("denominator_slots") or 1)
        top = slots(numerator, 1)
        bottom = slots(denominator, numerator + 1)
        return f'<div class="fill-format"><span class="fill-fraction">{top}{bottom}</span></div>'
    return f'<div class="fill-format"><span class="integer-rail">{slots(int(spec.get("slots") or 1))}</span></div>'


def _question(q: dict[str, Any], subject: str, base: Path, show_stimulus: bool, show_visual: bool,
              label: str | None, stimulus_override: str | None = None) -> str:
    group = f'<div class="group-label">{esc(label)}</div>' if label else ""
    stimulus = ""
    if show_stimulus and q.get("group_stimulus"):
        raw_stimulus = stimulus_override if stimulus_override is not None else str(q["group_stimulus"])
        if subject == "英文":
            layout = q.get("stimulus_layout") or "prose"
            paragraphs = [part.strip() for part in re.split(r"\n\s*\n", raw_stimulus) if part.strip()]
            rendered = []
            for part in paragraphs:
                source_class = " source-line" if part.startswith("(") else ""
                rendered.append(f'<p class="{source_class.strip()}">{_paper_text(part, subject)}</p>')
            stimulus = f'<div class="stimulus english-{esc(layout)}">{"".join(rendered)}</div>'
        else:
            stimulus = f'<div class="stimulus">{_paper_text(raw_stimulus, subject)}</div>'
    side_visual = q.get("visual_layout") == "side-right" and show_visual
    visual = _visual(q.get("visual_asset"), base, side=side_visual) if show_visual else ""
    if q.get("suppress_question_display"):
        return f'{group}{stimulus}{visual}'
    options = q.get("options") or []
    option_html = ""
    if options:
        cells = "".join(
            f'<div class="option"><span>({esc(o["label"])})</span><span>{_paper_text(o["text"], subject)}</span></div>'
            for o in options
        )
        option_html = f'<div class="options {_option_layout(q, subject)}">{cells}</div>'
    lines = ""
    if q.get("answer_space_lines"):
        lines = '<div class="answer-lines">' + '<div class="answer-line"></div>' * int(q["answer_space_lines"]) + '</div>'
    fill = _fill_format(q)
    # Keep points in the source JSON for validation.  Official GSAT-style
    # sections normally state a shared score once, so per-item labels are an
    # explicit opt-in rather than the renderer default.
    score = f'<span class="score">（{esc(q.get("score"))}分）</span>' if q.get("score") is not None and q.get("show_score_label", False) else ""
    target_height = q.get("target_height_mm")
    height_style = f' style="min-height:{float(target_height):g}mm"' if target_height else ""
    prompt_text = _paper_text(q["prompt"], subject)
    if fill and "______" in prompt_text:
        prompt_text = prompt_text.replace("______", fill, 1)
        fill = ""
    prompt = f'<div class="prompt">{score}{prompt_text}</div>'
    if side_visual:
        core = f'<div class="stem-side"><div>{prompt}{fill}</div>{visual}</div>{option_html}{lines}'
    else:
        core = f'{prompt}{visual}{option_html}{fill}{lines}'
    number_display = q.get("number_display") or f'{q["number"]}.'
    section_class = f' section-{esc(q.get("section_id") or "")}' if q.get("section_id") else ""
    return f'{group}{stimulus}<article class="question{section_class}"{height_style}><div class="qno">{esc(number_display)}</div><div>{core}</div></article>'


def _cover(meta: dict[str, Any], instructions: list[str]) -> str:
    if (meta.get("paper_subject") or meta.get("subject")) in {"數學A", "數學B"} and int(meta.get("layout_contract_version") or 0) >= 3:
        return _math_cover(meta)
    if (meta.get("paper_subject") or meta.get("subject")) == "國寫" and int(meta.get("layout_contract_version") or 0) >= 3:
        return _writing_cover(meta)
    bullets = "".join(f'<li>{text_block(x)}</li>' for x in instructions)
    scoring = meta.get("scoring_note") or "各題計分方式依題本各大題說明。"
    return f'''<section class="sheet cover"><div class="org">Taiwan Exam 命題系統｜內部校樣</div>
<div class="year">116學年度學科能力測驗完整規格校樣卷</div>
<div class="subject">{esc(meta.get("paper_label") or meta["subject"])}</div>
<div class="sign">請於考試開始鈴響起，在答題卷簽名欄位以正楷簽全名</div>
<div class="notice"><h1>作答注意事項</h1><p><b>考試時間：</b>{esc(meta.get("duration_minutes"))}分鐘</p>
<h2>作答方式：</h2><ul>{bullets}</ul><h2>計分方式：</h2><p>{text_block(scoring)}</p></div>
<div class="prototype">完整題數／配分／時間內部校樣｜內容原創、未經代表性考生預試｜版面為115題本參照校樣，非大考中心正式試題</div></section>'''


def _writing_cover(meta: dict[str, Any]) -> str:
    return f'''<section class="sheet cover writing-cover"><div class="org">Taiwan Exam 內部命題測試</div>
<div class="year">116學年度學科能力測驗校樣試題</div>
<div class="subject">國語文寫作能力測驗</div>
<div class="sign">請於考試開始鈴響起，在答題卷簽名欄位以正楷簽全名</div>
<div class="notice"><h1>— 作答注意事項 —</h1><p><b>考試時間：</b>{esc(meta.get("duration_minutes"))}分鐘。請妥善分配作答時間。</p>
<p><b>題型與數：</b>非選擇題共二大題</p>
<h2>作答方式：</h2><ul>
<li>限用中文書寫；違者該作答部分不予評閱計分。唯專有名詞或試題有特殊要求者不在此限。</li>
<li>限在作答區範圍內作答。第一大題限作答於答題卷「正面」，第二大題限作答於答題卷「背面」。</li>
<li>使用筆尖較粗（建議約0.5mm～0.7mm）之黑色墨水的筆書寫；更正時，可以使用修正帶（液）。若未依規定而導致答案難以辨識或評閱，恐將影響成績。</li>
<li>答題卷每人一張，不得要求增補。</li>
</ul></div>
<div class="prototype">111–115當代卷型參照｜完整題數、配分與時間｜原創內容、未經代表性考生預試｜非大考中心正式試題</div></section>'''


def _math_cover(meta: dict[str, Any]) -> str:
    label = esc(meta.get("paper_label") or meta["subject"])
    fraction_example = _fill_format({"number": "18", "answer_format": {"kind": "fraction", "numerator_slots": 1, "denominator_slots": 1}})
    return f'''<section class="sheet cover math-cover"><div class="org">Taiwan Exam 內部命題測試</div>
<div class="year">116學年度學科能力測驗校樣試題</div>
<div class="subject">{label}</div>
<div class="sign">請於考試開始鈴響起，在答題卷簽名欄位以正楷簽全名</div>
<div class="notice"><h1>— 作答注意事項 —</h1><p><b>考試時間：</b>{esc(meta.get("duration_minutes"))}分鐘</p>
<h2>作答方式：</h2><ul>
<li>選擇（填）題用2B鉛筆在「答題卷」上作答；更正時以橡皮擦擦拭，切勿使用修正帶（液）。</li>
<li>除題目另有規定外，非選擇題用筆尖較粗之黑色墨水的筆在「答題卷」上作答；更正時，可以使用修正帶（液）。</li>
<li>考生須依上述規定劃記或作答；若未依規定而導致答案難以辨識或評閱時，恐將影響成績。</li>
<li>答題卷每人一張，不得要求增補。</li>
<li>選填題須依各題印出的格式填答，每一列號只能在一個格子劃記。請仔細閱讀下列例子。</li></ul>
<div class="cover-fill-example"><span>例：若答案格式是</span>{fraction_example}<span>，而依題意算得3/8。</span></div>
<div class="cover-fill-direction">應在第18-1列劃記3、第18-2列劃記8，如下：</div>
<div class="mark-example"><span class="mark-row"><span>18-1</span><span>1</span><span>2</span><span class="marked">3</span><span>4</span><span>5</span><span>6</span><span>7</span><span>8</span><span>9</span><span>0</span><span>−</span><span>±</span></span><br><span class="mark-row"><span>18-2</span><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span><span>6</span><span>7</span><span class="marked">8</span><span>9</span><span>0</span><span>−</span><span>±</span></span></div>
<h2>選擇（填）題計分方式：</h2><ul>
<li><b>單選題：</b>每題只有一個正確或最適當的選項。答對得該題分數；答錯、未作答或劃記多於一個選項者以零分計。</li>
<li><b>多選題：</b>每題有n個選項且至少一個正確；各選項獨立判定。全部答對得滿分，答錯k個選項時得該題(n−2k)/n的分數；所得低於零分或全部未作答者以零分計。</li>
<li><b>選填題：</b>每題各空格須全部答對才給分，答錯不倒扣。</li></ul>
<p>※ 試題中參考附圖均為示意圖；題本末頁附參考公式及數值。</p></div>
<div class="prototype">111–115當代卷型閘門校樣｜完整題數、配分與時間｜原創內容、未經代表性考生預試｜非大考中心正式試題</div></section>'''


def _pages(exam: dict[str, Any], base: Path) -> str:
    meta = exam["metadata"]
    subject = meta.get("paper_subject") or meta["subject"]
    total = int(meta["target_page_count"])
    section_map = {s["id"]: s for s in exam["sections"]}
    pages: list[str] = []
    prior_stimulus: str | None = None
    current_section: str | None = None
    for page_no in range(2, total + 1):
        qs = sorted((q for q in exam["questions"] if int(q.get("page", 2)) == page_no), key=lambda x: x["number"])
        body: list[str] = []
        shown_paths: set[str] = set()
        i = 0
        while i < len(qs):
            q = qs[i]
            if q["section_id"] != current_section:
                section = section_map[q["section_id"]]
                notes = " ".join(section.get("instructions") or [])
                body.append(f'<h1 class="section-head">{_paper_text(section["title"], subject)}</h1>')
                if notes:
                    body.append(f'<div class="section-rule">{text_block(notes)}</div>')
                current_section = q["section_id"]
            stimulus = q.get("group_stimulus")
            j = i + 1
            while stimulus and j < len(qs) and qs[j].get("group_stimulus") == stimulus:
                j += 1
            label = None
            if stimulus:
                global_group = [x for x in exam["questions"] if x.get("group_stimulus") == stimulus]
                if len(global_group) > 1:
                    label = f'第 {global_group[0]["number"]} 至 {global_group[-1]["number"]} 題為題組'
                    if prior_stimulus == stimulus:
                        if subject == "英文":
                            label = None
                        else:
                            label += '（續）'
            for k in range(i, j):
                asset = qs[k].get("visual_asset") or {}
                path = asset.get("path")
                show_visual = bool(path) and path not in shown_paths
                if path:
                    shown_paths.add(path)
                split_text = (qs[k].get("group_stimulus_page_splits") or {}).get(str(page_no)) if k == i else None
                show_stimulus = k == i and (prior_stimulus != stimulus or split_text is not None)
                body.append(_question(
                    qs[k], subject, base, show_stimulus=show_stimulus,
                    show_visual=show_visual, label=label if k == i else None,
                    stimulus_override=split_text,
                ))
            prior_stimulus = stimulus
            i = j
        preview_id = (meta.get("section_header_previews") or {}).get(str(page_no))
        if preview_id and preview_id != current_section:
            section = section_map[preview_id]
            notes = " ".join(section.get("instructions") or [])
            body.append(f'<h1 class="section-head">{_paper_text(section["title"], subject)}</h1>')
            if notes:
                body.append(f'<div class="section-rule">{text_block(notes)}</div>')
            current_section = preview_id
        extra = (meta.get("page_extras") or {}).get(str(page_no), "")
        for source_q in exam["questions"]:
            continuation = (source_q.get("continuation_pages") or {}).get(str(page_no))
            if continuation:
                body.append(f'<div class="writing-continuation"><h2>第 {esc(source_q["number"])} 題（續）</h2>{_paper_text(continuation, subject)}</div>')
        if extra:
            klass = "formula-sheet" if subject in {"數學A", "數學B"} and page_no == total else "writing-note"
            if klass == "formula-sheet":
                # Official formula lists do not use empty paragraphs between
                # consecutive identities.  Normalize accidental authoring
                # whitespace before applying the measured line rhythm, and
                # make the heading an explicit bold block rather than relying
                # on the less predictable CSS ::first-line pseudo-element.
                lines = [line for line in str(extra).splitlines() if line.strip()]
                title = lines[0] if lines else ""
                formulae = "\n".join(lines[1:])
                body.append(
                    f'<div class="formula-sheet"><div class="formula-title">{_paper_text(title, subject)}</div>'
                    f'<div class="formula-lines">{_paper_text(formulae, subject)}</div></div>'
                )
            else:
                body.append(f'<div class="{klass}">{_paper_text(extra, subject)}</div>')
        if page_no == total:
            reference_year = meta.get("layout_reference_year", 115)
            body.append(f'<div class="trace">Paper Profile：{esc(meta.get("paper_profile_id"))}｜參照：{esc(reference_year)}學年度｜難度：專家估計、待預試｜Layout：reference-only</div>')
        page_mark = f'第 {page_no-1} 頁<br>共 {total-1} 頁'
        subject_mark = f'116年學測校樣<br>{esc(meta.get("paper_label") or subject)}'
        left_mark, right_mark = (page_mark, subject_mark) if (page_no - 1) % 2 else (subject_mark, page_mark)
        pages.append(f'''<section class="sheet"><div class="header"><span>{left_mark}</span><span class="mid">請記得在答題卷簽名欄位以正楷簽全名</span><span class="right">{right_mark}</span></div><main class="content">{"".join(body)}</main><div class="footer"><span>內部測試</span><span class="center">- {page_no-1} -</span><span class="right">未經預試</span></div></section>''')
    return "".join(pages)


def _answers(exam: dict[str, Any]) -> str:
    meta = exam["metadata"]
    number = {q["id"]: q["number"] for q in exam["questions"]}
    answers = exam.get("answers") or []
    difficulty_names = {
        "easy": "易", "medium": "中等", "hard": "難", "very_hard": "較難",
    }
    row_items = [
        (
            f'<tr><td>{esc(number.get(a["question_id"], a["question_id"]))}</td><td>{text_block(a.get("final_answer"))}</td><td>{esc(difficulty_names.get(a.get("difficulty_label"), a.get("difficulty_label") or "-"))}</td></tr>',
            # A constructed-response key can occupy several table lines.  A
            # fixed item count allowed Chromium to strand one wrapped row on
            # an otherwise empty page, so budget the quick-key pages by an
            # intentionally conservative line-equivalent weight instead.
            max(1, (len(str(a.get("final_answer") or "")) + 35) // 36),
        )
        for a in answers
    ]
    details = []
    for a in answers:
        reasoning = a.get("reasoning") or []
        body = '<ol>' + ''.join(f'<li>{text_block(x)}</li>' for x in reasoning) + '</ol>' if reasoning else ""
        for block in a.get("explanation_blocks") or []:
            body += f'<p><b>{esc(block.get("title") or "說明")}：</b>{text_block(block.get("content"))}</p>'
        details.append(f'<article class="solution"><h2>第 {esc(number.get(a["question_id"]))} 題　答案：{text_block(a.get("final_answer"))}</h2>{body}</article>')
    quick_pages = []
    # Keep each table inside an explicit page-sized chunk.  The capacity is
    # slightly below the physical maximum so borders and wrapped CJK text do
    # not trigger an implicit spill page at print time.
    row_chunks: list[list[str]] = []
    current_rows: list[str] = []
    current_weight = 0
    for row_html, row_weight in row_items:
        if current_rows and current_weight + row_weight > 33:
            row_chunks.append(current_rows)
            current_rows = []
            current_weight = 0
        current_rows.append(row_html)
        current_weight += row_weight
    if current_rows:
        row_chunks.append(current_rows)
    for index, chunk in enumerate(row_chunks):
        title = "答案速查" if index == 0 else "答案速查（續）"
        rows = "".join(chunk)
        quick_pages.append(f'<section class="answer-page"><h1>{title}</h1><table class="answer-grid"><thead><tr><th>題號</th><th>答案</th><th>估計難度</th></tr></thead><tbody>{rows}</tbody></table></section>')
    return f'''<section class="sheet answer-cover"><h1>{esc(meta.get("paper_label") or meta["subject"])}答案與評分參考</h1><p>內部命題檢核用｜請勿與學生卷合併發放</p><p>難度標示均為專家估計，須經代表性考生預試後才可轉為實測難度。</p></section>
{"".join(quick_pages)}
<section class="answer-page"><h1>解析與評分參考</h1><div class="two-col">{"".join(details)}</div></section>'''


def current_math_layout_errors(exam: dict[str, Any]) -> list[str]:
    meta = exam.get("metadata") or {}
    subject = meta.get("paper_subject") or meta.get("subject")
    if subject not in {"數學A", "數學B"} or int(meta.get("layout_contract_version") or 0) < 3:
        return []
    mixed_sections = {
        section.get("id")
        for section in exam.get("sections") or []
        if section.get("id") == "mixed" or "混合" in str(section.get("title") or "")
    }
    return [
        f"數學第 {question.get('number')} 題位於混合題區，題本不可加入練習用作答橫線"
        for question in exam.get("questions") or []
        if question.get("section_id") in mixed_sections and int(question.get("answer_space_lines") or 0) > 0
    ]


def render(exam: dict[str, Any], *, answers_only: bool = False, base: Path, run_contract: Path | None = None) -> str:
    from validate_exam_pack_contract import require_handoff
    require_handoff(exam, base, run_contract)
    errors = validate_exam(exam)
    errors.extend(current_math_layout_errors(exam))
    if errors:
        raise ValueError("；".join(errors))
    meta = exam["metadata"]
    if (meta.get("generation_mode"), meta.get("layout_fidelity_status")) not in {
        ("custom-practice", "reference-only"), ("full-paper", "verified")
    }:
        raise ValueError("校樣須為完整卷通過內容檢查，或明確的 custom-practice + reference-only 排版測試")
    body = _answers(exam) if answers_only else _cover(meta, exam["instructions"]) + _pages(exam, base)
    paper_subject = meta.get("paper_subject") or meta["subject"]
    return f'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>{esc(meta["title"])}</title><style>{STYLE}</style></head><body class="paper-{esc(paper_subject)}">{body}</body></html>'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--answers-only", action="store_true")
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args(argv)
    try:
        exam = json.loads(args.input.read_text(encoding="utf-8-sig"))
        html = render(exam, answers_only=args.answers_only, base=args.input.resolve().parent, run_contract=args.contract)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html, encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    print(f"已輸出內部校樣 HTML：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
