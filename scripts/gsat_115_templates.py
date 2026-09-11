#!/usr/bin/env python3
"""Deterministic 115-regime GSAT booklet furniture.

This module owns layout-only material: covers, running page furniture, and the
two subject-specific mathematics formula sheets.  It never creates questions.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = ROOT / "exam_packs" / "學測" / "templates" / "115"
SIGNATURE_COVER = "請於考試開始鈴響起，在答題卷簽名欄位以正楷簽全名"
SIGNATURE_RUNNING = "請記得在答題卷簽名欄位以正楷簽全名"

SUBJECT_ORDER = ("國綜", "國寫", "英文", "數學A", "數學B", "社會", "自然")
SUBJECTS: dict[str, dict[str, Any]] = {
    "國綜": {
        "slug": "chinese-comprehensive", "folder": "國文",
        "label": "國語文綜合能力測驗", "duration": 90,
        "profile": "gsat-chinese-comprehensive-115-measured-v1", "inner_pages": 11,
    },
    "國寫": {
        "slug": "chinese-writing", "folder": "國文",
        "label": "國語文寫作能力測驗", "duration": 90,
        "profile": "gsat-chinese-writing-115-measured-v1", "inner_pages": 3,
    },
    "英文": {
        "slug": "english", "folder": "英文", "label": "英文考科", "duration": 100,
        "profile": "gsat-english-115-measured-v1", "inner_pages": 11,
    },
    "數學A": {
        "slug": "math-a", "folder": "數學A", "label": "數學A考科", "duration": 100,
        "profile": "gsat-math-a-115-measured-v1", "inner_pages": 7, "formula": "math-a",
    },
    "數學B": {
        "slug": "math-b", "folder": "數學B", "label": "數學B考科", "duration": 100,
        "profile": "gsat-math-b-115-measured-v1", "inner_pages": 7, "formula": "math-b",
    },
    "社會": {
        "slug": "social", "folder": "社會", "label": "社會考科", "duration": 110,
        "profile": "gsat-social-115-measured-v1", "inner_pages": 19,
    },
    "自然": {
        "slug": "science", "folder": "自然", "label": "自然考科", "duration": 110,
        "profile": "gsat-science-115-measured-v1", "inner_pages": 19,
    },
}


COVER_CSS = r"""
.gsat115-cover { position:relative; padding:31.5mm 28.5mm 18mm;
  break-after:page; background:#fff; color:#000; font-family:"DFKai-SB","BiauKai","KaiTi","PMingLiU",serif; }
.gsat115-cover .tpl-brand,.gsat115-cover .tpl-title { margin:0; text-align:center; font-size:18pt;
  line-height:30pt; letter-spacing:0; min-height:30pt; }
.gsat115-cover .tpl-subject { margin:1pt 0 25pt; text-align:center; font-size:24pt;
  font-weight:700; line-height:30pt; letter-spacing:0; }
.gsat115-cover .tpl-signature { width:max-content; max-width:100%; margin:0 auto 18pt;
  padding:0 5pt; background:#d9d9d9; text-align:center; font-size:16pt; line-height:21pt;
  white-space:nowrap; }
.gsat115-cover .tpl-notice { width:100%; margin:0 auto; padding:15pt 32pt 14pt;
  border:.75pt solid #000; font-size:11.04pt; line-height:18pt; }
.gsat115-cover .tpl-notice h1 { margin:0 0 14pt; text-align:center; font-size:14pt;
  font-weight:400; line-height:18pt; }
.gsat115-cover .tpl-notice p { margin:0 0 8pt; }
.gsat115-cover .tpl-notice ul { margin:0 0 12pt; padding-left:25pt; }
.gsat115-cover .tpl-notice li { margin:0; }
.gsat115-cover .tpl-notice .scoring { margin-top:1pt; }
.gsat115-cover .math-var { font:italic 1em "Times New Roman",serif; }
.gsat115-cover .frac { display:inline-flex; flex-direction:column; align-items:stretch;
  vertical-align:middle; min-width:2em; margin:0 .16em; text-align:center;
  white-space:nowrap; break-inside:avoid; font-family:"Times New Roman",serif; line-height:.94; }
.gsat115-cover .frac > span { display:block; padding:0 .16em; white-space:nowrap; }
.gsat115-cover .frac > span:first-child { border-bottom:.6pt solid #000; }
.gsat115-cover.subject-chinese-comprehensive .tpl-notice { min-height:153.5mm; transform:translateY(8mm); }
.gsat115-cover.subject-social .tpl-notice { min-height:123.5mm; transform:translateY(3.5mm); }
.gsat115-cover.subject-science .tpl-notice { min-height:150.4mm; transform:translateY(10mm); }
.gsat115-cover.subject-english .tpl-notice { min-height:175.7mm; }
.gsat115-cover.cover-writing { padding:31.5mm 34mm 18mm; }
.gsat115-cover.cover-writing .tpl-subject { margin-bottom:25pt; }
.gsat115-cover.cover-writing .tpl-notice { min-height:158mm; padding:17pt 27pt;
  transform:translateY(12mm); font-size:11.5pt; line-height:19pt; }
.gsat115-cover.cover-writing .tpl-notice li { margin-bottom:2pt; }
.gsat115-cover.cover-math { padding:27mm 19.5mm 14mm; }
.gsat115-cover.cover-math .tpl-brand,.gsat115-cover.cover-math .tpl-title { font-size:19.98pt; line-height:26pt; }
.gsat115-cover.cover-math .tpl-subject { margin:7pt 0 8pt; font-size:25.98pt; line-height:32pt; }
.gsat115-cover.cover-math .tpl-signature { margin-bottom:5pt; font-size:18pt; line-height:23.46pt; }
.gsat115-cover.cover-math .tpl-notice { padding:3pt 8pt; font-size:11.25pt; line-height:14.6pt; }
.gsat115-cover.cover-math .tpl-notice { min-height:200.7mm; }
.gsat115-cover.subject-math-b .tpl-notice { min-height:204.5mm; transform:translateY(-2.4mm); }
.gsat115-cover.cover-math .tpl-notice h1 { margin:0 0 1pt; font-size:15pt; line-height:19pt; }
.gsat115-cover.cover-math .tpl-notice p,.gsat115-cover.cover-math .tpl-notice li { margin:0; }
.gsat115-cover.cover-math .tpl-notice ul { margin:0; padding-left:24pt; }
.cover-fill-example { margin:1pt 0 1pt 24pt; }
.fill-format { display:inline-flex; align-items:center; vertical-align:middle; margin:0 2pt;
  white-space:nowrap; break-inside:avoid; line-height:1; }
.fill-slots { display:inline-flex; align-items:center; justify-content:center; gap:1pt; }
.fill-slot { position:relative; display:inline-flex; width:25.98pt; height:25.98pt;
  align-items:center; justify-content:center; font:8.5pt/1 "Times New Roman",serif; }
.fill-slot::before { content:"○"; position:absolute; inset:0; display:flex; align-items:center;
  justify-content:center; font:25.98pt/1 "DFKai-SB","KaiTi",serif; }
.fill-slot > span { position:relative; z-index:1; }
.fill-fraction { display:inline-grid; grid-template-rows:auto auto; gap:1pt; }
.fill-fraction .fill-slots { min-width:32pt; padding:0 1pt 1pt; border-bottom:.75pt solid #000; }
.fill-fraction .fixed-denominator { display:block; min-width:32pt; text-align:center;
  line-height:17pt; }
.mark-example { width:250pt; margin:1pt 0 3pt 112pt; font-family:"Times New Roman",sans-serif; }
.mark-row { display:grid; width:250pt; grid-template-columns:25pt repeat(12,1fr);
  border-left:1.5pt solid #000; border-right:1.5pt solid #000; }
.mark-row + .mark-row { border-top:.75pt solid #000; }
.mark-label,.mark-cell { height:20pt; text-align:center; font-size:7pt; line-height:10pt; }
.mark-label { font-size:9pt; line-height:20pt; }
.mark-cell b { display:block; width:11pt; height:5pt; margin:0 auto 2pt; border:.5pt solid #000; }
.mark-cell.marked b { background:#000; }
"""


DOCUMENT_CSS = r"""
@page { size:A4; margin:0; }
* { box-sizing:border-box; }
html,body { margin:0; padding:0; background:#fff; color:#000; }
.sheet { position:relative; width:210mm; height:297mm; overflow:hidden; background:#fff; }
.sheet:not(:last-child) { break-after:page; }
.gsat115-inner { --left:22mm; --right:20.5mm; font-family:"DFKai-SB","BiauKai","KaiTi","PMingLiU",serif; }
.inner-header { position:absolute; left:var(--left); right:var(--right); top:14.75mm; height:13mm;
  display:grid; grid-template-columns:31mm 1fr 35mm; column-gap:2mm; align-items:start;
  font-size:10pt; line-height:13pt; }
.inner-header .head-center { width:max-content; max-width:100%; justify-self:center; padding:0 5pt;
  background:#d9d9d9; text-align:center; white-space:nowrap; }
.inner-header .head-right { text-align:right; }
.inner-body { position:absolute; left:var(--left); right:var(--right); top:30mm; bottom:17mm; }
.inner-footer { position:absolute; left:var(--left); right:var(--right); bottom:12.6mm;
  display:grid; grid-template-columns:1fr auto 1fr; font:10pt/1 "Times New Roman",serif; }
.inner-footer .outer-left { grid-column:1; text-align:left; }
.inner-footer .outer-right { grid-column:3; text-align:right; }
.blank-number { display:inline-block; min-width:2.1em; }
.blank-year { display:inline-block; min-width:2.4em; }
.formula-sheet { color:#000; font:10.98pt/20pt "Times New Roman","PMingLiU",serif; }
.formula-title { margin:0 0 23pt; font-weight:700; font-size:13.02pt; line-height:21pt; }
.formula-block { display:grid; grid-template-columns:15pt 1fr; gap:3pt; margin:0; }
.formula-block p { margin:0 0 3pt; }
.formula-sheet math { display:inline-block; padding-block:3px; font-size:1em; font-family:"Cambria Math","Times New Roman",serif; }
.formula-a .formula-block:nth-child(2) { min-height:90pt; }
.formula-a .formula-block:nth-child(3) { min-height:102pt; }
.formula-a .formula-block:nth-child(4) { min-height:70pt; }
.formula-a .formula-block:nth-child(5) { min-height:128pt; }
.formula-a .formula-block:nth-child(6) { min-height:133pt; }
.formula-b .formula-block:nth-child(2) { min-height:100pt; }
.formula-b .formula-block:nth-child(3) { min-height:78pt; }
.formula-b .formula-block:nth-child(4) { min-height:139pt; }
.formula-b .formula-block:nth-child(5) { min-height:143pt; }
"""


COMMON_ANSWER_MODE = (
    "選擇題用 2B 鉛筆在「答題卷」上作答；更正時以橡皮擦擦拭，切勿使用修正帶（液）。",
    "除題目另有規定外，非選擇題用筆尖較粗之黑色墨水的筆在「答題卷」上作答；更正時，可以使用修正帶（液）。",
    "考生須依上述規定劃記或作答，若未依規定而導致答案難以辨識或評閱時，恐將影響成績。",
    "答題卷每人一張，不得要求增補。",
)


def _e(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def subject_config(subject: str) -> dict[str, Any]:
    try:
        return SUBJECTS[subject]
    except KeyError as exc:
        raise ValueError(f"不支援的115學測模板科目：{subject}") from exc


def _fraction(top: str, bottom: str) -> str:
    return f'<span class="frac"><span>{_e(top)}</span><span>{_e(bottom)}</span></span>'


def _single_scoring() -> str:
    return ('<li>單選題：每題有 <span class="math-var">n</span> 個選項，其中只有一個是正確或最適當的選項。'
            '各題答對者，得該題的分數；答錯、未作答或劃記多於一個選項者，該題以零分計算。</li>')


def _multiple_scoring() -> str:
    fraction = _fraction('n−2k', 'n')
    return ('<li>多選題：每題有 <span class="math-var">n</span> 個選項，其中至少有一個是正確的選項。'
            '各題之選項獨立判定，所有選項均答對者，得該題全部的分數；答錯 '
            f'<span class="math-var">k</span> 個選項者，得該題 {fraction} 的分數；'
            '但得分低於零分或所有選項均未作答者，該題以零分計算。</li>')


def _standard_notice(subject: str, duration: int) -> str:
    bullets = ''.join(f'<li>{_e(line)}</li>' for line in COMMON_ANSWER_MODE)
    scoring = _single_scoring()
    if subject in {"國綜", "英文", "自然"}:
        scoring += _multiple_scoring()
    return (f'<div class="tpl-notice"><h1>－作答注意事項－</h1>'
            f'<p>考試時間：{duration}分鐘</p><p>作答方式：</p><ul>{bullets}</ul>'
            f'<p class="scoring">選擇題計分方式：</p><ul>{scoring}</ul></div>')


def _writing_notice() -> str:
    return '''<div class="tpl-notice"><h1>－作答注意事項－</h1>
<p>考試時間：90分鐘。請妥善分配作答時間。</p>
<p>題型題數：</p><ul><li>非選擇題共二大題</li></ul><p>作答方式：</p><ul>
<li>限用中文書寫，違者該作答部分不予評閱計分，惟專有名詞或試題有特殊要求者不在此限。</li>
<li>限在作答區範圍內作答，第一大題須作答於答題卷「正面」，第二大題須作答於答題卷「背面」。</li>
<li>使用筆尖較粗（建議約0.5mm～0.7mm）之黑色墨水的筆書寫於答題卷上之非選擇題作答區，更正時，可以使用修正帶（液）。力求字跡清晰且字體大小適中（若因字跡潦草致評閱人員無法或難以辨識該內容，恐將影響成績）。</li>
<li>答題卷每人一張，不得要求增補。</li></ul></div>'''


def _fill_fraction(number: str, *, numerator: int, denominator: int = 0, fixed_denominator: str = "") -> str:
    def slots(count: int, offset: int = 1) -> str:
        return '<span class="fill-slots">' + ''.join(
            f'<span class="fill-slot"><span>{_e(number)}-{i}</span></span>' for i in range(offset, offset + count)
        ) + '</span>'
    top = slots(numerator)
    bottom = f'<span class="fixed-denominator">{_e(fixed_denominator)}</span>' if fixed_denominator else slots(denominator, numerator + 1)
    return f'<span class="fill-format fill-fraction">{top}{bottom}</span>'


def _marking_rows(rows: tuple[tuple[str, str], ...]) -> str:
    symbols = tuple("1234567890") + ("−", "±")
    rendered = []
    for label, selected in rows:
        cells = ''.join(
            f'<span class="mark-cell{" marked" if symbol == selected else ""}">{_e(symbol)}<b></b></span>'
            for symbol in symbols
        )
        rendered.append(f'<div class="mark-row"><span class="mark-label">{_e(label)}</span>{cells}</div>')
    return '<div class="mark-example">' + ''.join(rendered) + '</div>'


def _math_notice(duration: int) -> str:
    bullets = list(COMMON_ANSWER_MODE)
    bullets[0] = "選擇（填）題用 2B 鉛筆在「答題卷」上作答；更正時以橡皮擦擦拭，切勿使用修正帶（液）。"
    bullets.append("選填題考生必須依各題的格式填答，且每一個列號只能在一個格子劃記。請仔細閱讀下面的例子。")
    bullet_html = ''.join(f'<li>{_e(line)}</li>' for line in bullets)
    frac18 = _fill_fraction("18", numerator=1, denominator=1)
    frac19 = _fill_fraction("19", numerator=2, fixed_denominator="50")
    return f'''<div class="tpl-notice"><h1>－作答注意事項－</h1>
<p>考試時間：{duration}分鐘</p><p>作答方式：</p><ul>{bullet_html}</ul>
<div class="cover-fill-example">例：若答案格式是{frac18}，而依題意計算出來的答案是{_fraction("3", "8")}，則考生必須分別在答題卷上的第18-1列的3與第18-2列的8劃記，如：</div>
{_marking_rows((("18-1", "3"), ("18-2", "8")))}
<div class="cover-fill-example">例：若答案格式是{frac19}，而答案是{_fraction("−7", "50")}時，則考生必須分別在答題卷的第19-1列的−與第19-2列的7劃記，如：</div>
{_marking_rows((("19-1", "−"), ("19-2", "7")))}
<p class="scoring">選擇（填）題計分方式：</p><ul>{_single_scoring()}{_multiple_scoring()}
<li>選填題每題有 <span class="math-var">n</span> 個空格，須全部答對才給分，答錯不倒扣。</li></ul>
<p>※試題中參考的附圖均為示意圖，試題後附有參考公式及數值。</p></div>'''


def cover_markup(
    subject: str, *, year: str = "", exam_name: str = "", organization: str = "Taiwan Exam 模擬試題",
    cover_title: str = "",
) -> str:
    """Return one locked, subject-specific cover with only named fields variable."""
    config = subject_config(subject)
    title = cover_title or ((f"{year}學年度" if year else "") + exam_name)
    kind = "cover-math" if subject in {"數學A", "數學B"} else "cover-writing" if subject == "國寫" else "cover-standard"
    if subject in {"數學A", "數學B"}:
        notice = _math_notice(config["duration"])
    elif subject == "國寫":
        notice = _writing_notice()
    else:
        notice = _standard_notice(subject, config["duration"])
    return (f'<section class="sheet cover gsat115-cover {kind} subject-{config["slug"]}">'
            f'<div class="tpl-brand">{_e(organization)}</div><div class="tpl-title">{_e(title)}</div>'
            f'<div class="tpl-subject">{_e(config["label"])}</div>'
            f'<div class="tpl-signature">{SIGNATURE_COVER}</div>{notice}</section>')


def _profile_path(subject: str) -> Path:
    config = subject_config(subject)
    return ROOT / "exam_packs" / "學測" / "subjects" / config["folder"] / "blueprints" / "layout-profiles" / f'{config["profile"]}.json'


def page_margins(subject: str) -> tuple[float, float]:
    """Return measured body left/right margins in millimetres."""
    import json
    profile = json.loads(_profile_path(subject).read_text(encoding="utf-8-sig"))
    geometry = profile["page_geometry"]
    width = float(geometry["width_pt"])
    left = float(geometry["body_left_pt"]) * 25.4 / 72
    right = (width - float(geometry["body_right_pt"])) * 25.4 / 72
    return left, right


def inner_markup(
    subject: str, *, parity: str, year: str = "", exam_name: str = "", current_page: str = "", total_pages: str = "",
    body: str = "",
) -> str:
    if parity not in {"odd", "even"}:
        raise ValueError("parity 必須是 odd 或 even")
    config = subject_config(subject)
    left_margin, right_margin = page_margins(subject)
    page_mark = (f'第 <span class="blank-number">{_e(current_page)}</span> 頁<br>'
                 f'共 <span class="blank-number">{_e(total_pages)}</span> 頁')
    running_name = "學測" if "學科能力測驗" in exam_name else exam_name
    year_line = ((f'<span class="blank-year">{_e(year)}</span>年' if year else '<span class="blank-year"></span>') +
                 _e(running_name))
    year_mark = f'{year_line}<br>{_e(config["label"])}'
    left, right = (page_mark, year_mark) if parity == "odd" else (year_mark, page_mark)
    footer_class = "outer-left" if parity == "odd" else "outer-right"
    footer = f'- {_e(current_page)} -' if current_page else '-　-'
    return f'''<section class="sheet gsat115-inner" style="--left:{left_margin:.3f}mm;--right:{right_margin:.3f}mm">
<div class="inner-header"><span>{left}</span><span class="head-center">{SIGNATURE_RUNNING}</span><span class="head-right">{right}</span></div>
<main class="inner-body">{body}</main><div class="inner-footer"><span class="{footer_class}">{footer}</span></div></section>'''


FORMULA_GROUPS = {
    "數學A": (
        (r"首項為 \(a\)，公差為 \(d\) 的等差數列前 \(n\) 項和為 \(S=\frac{n(2a+(n-1)d)}{2}\)",
         r"首項為 \(a\)，公比為 \(r\;(r\ne1)\) 的等比數列前 \(n\) 項和為 \(S=\frac{a(1-r^n)}{1-r}\)"),
        (r"三角函數的和角公式：\(\sin(A+B)=\sin A\cos B+\cos A\sin B\)",
         r"\(\cos(A+B)=\cos A\cos B-\sin A\sin B\)",
         r"\(\tan(A+B)=\frac{\tan A+\tan B}{1-\tan A\tan B}\)"),
        (r"\(\triangle ABC\) 的正弦定理：\(\frac{a}{\sin A}=\frac{b}{\sin B}=\frac{c}{\sin C}=2R\)（\(R\) 為外接圓半徑）",
         r"\(\triangle ABC\) 的餘弦定理：\(c^2=a^2+b^2-2ab\cos C\)"),
        (r"一維數據 \(X:x_1,x_2,\ldots,x_n\)，", r"算術平均數 \(\mu_X=\frac{1}{n}(x_1+x_2+\cdots+x_n)\)",
         r"標準差 \(\sigma_X=\sqrt{\frac{1}{n}[(x_1-\mu_X)^2+\cdots+(x_n-\mu_X)^2]}=\sqrt{\frac{1}{n}[(x_1^2+\cdots+x_n^2)-n\mu_X^2]}\)"),
        (r"二維數據 \((X,Y):(x_1,y_1),(x_2,y_2),\ldots,(x_n,y_n)\)，",
         r"相關係數 \(r_{XY}=\frac{(x_1-\mu_X)(y_1-\mu_Y)+\cdots+(x_n-\mu_X)(y_n-\mu_Y)}{n\sigma_X\sigma_Y}\)",
         r"迴歸直線（最適合直線）方程式 \(y-\mu_Y=r_{XY}\frac{\sigma_Y}{\sigma_X}(x-\mu_X)\)"),
        (r"參考數值：\(\sqrt{2}\approx1.414,\;\sqrt{3}\approx1.732,\;\sqrt{5}\approx2.236,\;\sqrt{6}\approx2.449,\;\pi\approx3.142\)",),
        (r"對數值：\(\log2\approx0.3010,\;\log3\approx0.4771,\;\log5\approx0.6990,\;\log7\approx0.8451\)",),
    ),
    "數學B": (
        (r"首項為 \(a\)，公差為 \(d\) 的等差數列前 \(n\) 項和為 \(S=\frac{n(2a+(n-1)d)}{2}\)",
         r"首項為 \(a\)，公比為 \(r\;(r\ne1)\) 的等比數列前 \(n\) 項和為 \(S=\frac{a(1-r^n)}{1-r}\)"),
        (r"\(\triangle ABC\) 的正弦定理：\(\frac{a}{\sin A}=\frac{b}{\sin B}=\frac{c}{\sin C}=2R\)（\(R\) 為外接圓半徑）",
         r"\(\triangle ABC\) 的餘弦定理：\(c^2=a^2+b^2-2ab\cos C\)"),
        (r"一維數據 \(X:x_1,x_2,\ldots,x_n\)，", r"算術平均數 \(\mu_X=\frac{1}{n}(x_1+x_2+\cdots+x_n)\)",
         r"標準差 \(\sigma_X=\sqrt{\frac{1}{n}[(x_1-\mu_X)^2+\cdots+(x_n-\mu_X)^2]}=\sqrt{\frac{1}{n}[(x_1^2+\cdots+x_n^2)-n\mu_X^2]}\)"),
        (r"二維數據 \((X,Y):(x_1,y_1),(x_2,y_2),\ldots,(x_n,y_n)\)，",
         r"相關係數 \(r_{XY}=\frac{(x_1-\mu_X)(y_1-\mu_Y)+\cdots+(x_n-\mu_X)(y_n-\mu_Y)}{n\sigma_X\sigma_Y}\)",
         r"迴歸直線（最適合直線）方程式 \(y-\mu_Y=r_{XY}\frac{\sigma_Y}{\sigma_X}(x-\mu_X)\)"),
        (r"參考數值：\(\sqrt{2}\approx1.414,\;\sqrt{3}\approx1.732,\;\sqrt{5}\approx2.236,\;\sqrt{6}\approx2.449,\;\pi\approx3.142\)",),
        (r"對數值：\(\log2\approx0.3010,\;\log3\approx0.4771,\;\log5\approx0.6990,\;\log7\approx0.8451\)",),
    ),
}


def _formula_text(value: str) -> str:
    from latex2mathml.converter import convert
    out: list[str] = []
    cursor = 0
    for match in re.finditer(r"\\\((.+?)\\\)", value):
        out.append(_e(value[cursor:match.start()]))
        out.append(convert(match.group(1), display="inline"))
        cursor = match.end()
    out.append(_e(value[cursor:]))
    return ''.join(out)


def formula_markup(subject: str) -> str:
    if subject not in FORMULA_GROUPS:
        raise ValueError("只有數學A、數學B有115參考公式模板")
    blocks = ''.join(
        f'<div class="formula-block"><span>{index}.</span><div>' +
        ''.join(f'<p>{_formula_text(line)}</p>' for line in group) + '</div></div>'
        for index, group in enumerate(FORMULA_GROUPS[subject], 1)
    )
    variant = "formula-a" if subject == "數學A" else "formula-b"
    return f'<div class="formula-sheet {variant}"><div class="formula-title">參考公式及可能用到的數值</div>{blocks}</div>'


def document(markup: str, *, title: str) -> str:
    return (f'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>{_e(title)}</title>'
            f'<style>{DOCUMENT_CSS}\n{COVER_CSS}</style></head><body>{markup}</body></html>')
