#!/usr/bin/env python3
"""Render subject-specific GSAT proofs after the maintained content handoff.

Full papers require actual verified pack evidence; a rendered proof still needs
the independent PDF delivery gate. Custom practice remains explicitly labelled.
This module renders authored data, never generates question content.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from gsat_115_templates import formula_markup as gsat_115_formula_markup
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
body.paper-英文 .question.section-reading { margin-bottom:1.35mm; line-height:1.38; }
.english-blank { display:inline-block; min-width:13mm; border-bottom:.65px solid #222;
  text-align:center; line-height:1.12; text-indent:0; margin:0 .45mm; }
body.paper-國寫 {
  font-family:"DFKai-SB","BiauKai","標楷體","PMingLiU",serif;
  font-size:12pt;
  line-height:1.69;
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
.prompt { text-align:justify; line-break:anywhere; overflow-wrap:anywhere; }
.paper-英文 .prompt { line-break:auto; overflow-wrap:normal; word-break:normal; }
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
.trace { font-size:7.2pt; color:#666; border-top:.5px solid #999; margin-top:3mm; padding-top:1mm;
  overflow-wrap:anywhere; word-break:break-word; }
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
/* Measured 115 Math A roles. Opt-in v4 leaves unrelated subject proofs intact. */
.measured-math { color:#000; font-size:10.98pt; line-height:20pt; }
.measured-math .sheet:not(.cover) { padding:15mm 21.378mm 15mm; }
.measured-math .header { height:14.5mm; font-size:10.98pt; line-height:14pt;
  grid-template-columns:31mm 1fr 35mm; gap:1mm; margin:0 3.18pt; }
.measured-math .header .mid { border:0; padding:0; font-weight:400;
  font-family:"DFKai-SB",serif; background:#d9d9d9; line-height:14pt; white-space:nowrap;
  width:max-content; max-width:100%; justify-self:center; }
.measured-math .content { height:241mm; padding:0 3.18pt; }
.measured-math .section-head { font-family:"PMingLiU",serif; font-size:13.02pt;
  line-height:21pt; margin:0 0 4pt; letter-spacing:0; }
.measured-math .section-rule { font-size:12pt; line-height:15.6pt;
  border:.75pt solid #000; padding:1.5pt 2pt; margin:0 -3.18pt 8pt; }
.measured-math .question { grid-template-columns:15pt 1fr; column-gap:3pt; margin-bottom:14.4pt; }
.measured-math .content > .question:last-child { margin-bottom:0; }
.measured-math .qno { font-weight:400; }
.measured-math .prompt,.measured-math .stimulus { line-height:20pt;
  line-break:strict; overflow-wrap:normal; word-break:normal; }
.measured-math .options { margin-top:1pt; row-gap:0; }
.measured-math .option { line-height:20pt; }
.measured-math .group-label { font-weight:400; text-decoration:underline; }
.measured-math .score { float:none; font:inherit; margin:0; }
.measured-math .footer { left:22.5mm; right:22.5mm; bottom:15mm; font-size:10.02pt; color:#000; }
.measured-math .footer .center { grid-column:1; text-align:left; }
.measured-math .footer .outer-right { grid-column:3; text-align:right; }
.measured-math math { font-size:1em; font-family:"Times New Roman","Cambria Math",serif;
  padding-block:4px; }
.measured-math math[display="inline"] { display:inline-block; }
.measured-math math[display="block"] { margin:4pt 0; }
.measured-math .math-with-punctuation { white-space:nowrap; }
.measured-math .math-cover { padding:30mm 19.5mm 14mm; }
.measured-math .math-cover .org { margin:0; line-height:26pt; letter-spacing:0; }
.measured-math .math-cover .year { margin:0; line-height:26pt; letter-spacing:0; }
.measured-math .math-cover .subject { margin:7pt 0 8pt; line-height:32pt; letter-spacing:0; }
.measured-math .math-cover .sign { background:#d9d9d9; text-decoration:none;
  width:max-content; max-width:100%; margin:0 auto 5pt; line-height:23.46pt; }
.measured-math .math-cover .notice { font-size:12pt; line-height:15.6pt;
  padding:3pt 8pt 3pt; min-height:0; border:.75pt solid #000; }
.measured-math .math-cover .notice h1 { font-size:16.02pt; line-height:21pt; margin:0 0 1pt; letter-spacing:0; }
.measured-math .math-cover .notice p,.measured-math .math-cover .notice li { margin:0; }
.measured-math .math-cover .notice ul { padding-left:24pt; }
.measured-math .math-cover .notice h2 { font-size:12pt; line-height:15.6pt; font-weight:400; margin:0; }
.measured-math .mark-example { margin:1pt 0 4pt 112pt; }
.measured-math .mark-row { display:grid; width:250pt; grid-template-columns:25pt repeat(12,1fr);
  border:0; border-left:1.5pt solid #000; border-right:1.5pt solid #000; }
.measured-math .mark-row + .mark-row { border-top:.75pt solid #000; }
.measured-math .mark-row > span { height:22pt; line-height:22pt; border:0; font-size:10.02pt; }
.measured-math .mark-row .mark-cell { font-size:7pt; line-height:11pt; }
.measured-math .mark-cell b { display:block; width:11pt; height:5pt; margin:0 auto 3pt;
  border:.5pt solid #000; font-size:0; }
.measured-math .mark-cell.marked { background:none; color:#000; font-weight:400; }
.measured-math .mark-cell.marked b { background:#000; }
.measured-math .cover-fill-example { display:block; margin:0 0 1pt 24pt; max-width:calc(100% - 24pt); }
.measured-math .cover-fill-example .fill-format { margin:0 1pt; }
.measured-math .cover-fill-example .fill-slot { width:9.16mm; height:9.16mm; font-size:10.98pt; }
.measured-math .cover-fill-example .fill-slot::before { font-size:25.98pt; }
.measured-math .cover-fill-example .fill-fraction .fill-slots { min-width:0; padding:0 .4pt .75pt; }
.measured-math .cover-fill-direction { margin:0 0 1pt 48pt; }
.measured-math .fill-format { display:inline-flex; }
.measured-math .fill-fraction .fixed-denominator { display:block; text-align:center;
  border-bottom:.75pt solid #000; line-height:18pt; }
.measured-math .formula-sheet { font-size:10.98pt; line-height:20pt; padding:0; }
.measured-math .formula-title { font-size:13.02pt; line-height:21pt; margin-bottom:23pt; }
.measured-math .formula-block { margin:0; display:grid; grid-template-columns:15pt 1fr; gap:3pt; }
.measured-math .formula-a .formula-block:nth-child(2) { min-height:90pt; }
.measured-math .formula-a .formula-block:nth-child(3) { min-height:102pt; }
.measured-math .formula-a .formula-block:nth-child(3) p:not(:first-child) { padding-left:135pt; }
.measured-math .formula-a .formula-block:nth-child(4) { min-height:70.02pt; }
.measured-math .formula-a .formula-block:nth-child(5) { min-height:128.4pt; }
.measured-math .formula-a .formula-block:nth-child(6) { min-height:133.38pt; }
.measured-math .formula-a .formula-block:nth-child(7) { min-height:48pt; }
.measured-math .formula-b .formula-block:nth-child(2) { min-height:100pt; }
.measured-math .formula-b .formula-block:nth-child(3) { min-height:78pt; }
.measured-math .formula-b .formula-block:nth-child(4) { min-height:139pt; }
.measured-math .formula-b .formula-block:nth-child(5) { min-height:143pt; }
.measured-math .formula-block p { margin:0 0 3pt; }
.measured-math .answer-grid { font-size:10.98pt; }
.measured-math .answer-page { padding:15mm 22.5mm; }
.measured-math .two-col { columns:1; }
.measured-math .solution h2 { font-size:12pt; }
.measured-math .solution { margin-bottom:12pt; padding-bottom:6pt; }
.measured-math .answer-header { height:10mm; margin:0 3.18pt; display:flex;
  justify-content:space-between; font-size:10.02pt; line-height:15pt; }
.measured-math .answer-content { height:250mm; line-height:18pt; }
.measured-math .answer-content h1 { font-size:14pt; line-height:21pt; text-align:center; margin:0 0 9pt; }
.measured-math .answer-content > p { margin:0 0 9pt; }
.measured-math .answer-content .solution { line-height:18pt;
  line-break:strict; overflow-wrap:normal; word-break:normal; }
.measured-math .answer-content .solution h2 { line-height:20pt; }
.measured-social { font-family:"Times New Roman","PMingLiU","MingLiU",serif; font-size:11.04pt; line-height:17.4pt; }
.measured-social .sheet:not(.cover) { padding:30mm 20.59mm 15mm 22.056mm; }
.measured-social .content { height:247mm; padding-top:0; }
.measured-social .header { position:absolute; left:22.056mm; right:20.59mm; top:14.78mm; height:12mm; font:10pt/13pt "DFKai-SB","Times New Roman",serif; }
.measured-social .header .mid { font:10pt/13pt "DFKai-SB",serif; background:#ddd; text-decoration:none; }
.measured-social .footer { left:22.056mm; right:20.59mm; bottom:13.56mm; font:10pt "Times New Roman",serif; }
.measured-social .footer .center { grid-column:1; text-align:left; }
.measured-social .footer .outer-right { grid-column:3; text-align:right; }
.measured-social .section-head { font-size:12.96pt; line-height:18pt; margin:0 0 5pt; }
.measured-social .section-rule { font:12pt/16pt "DFKai-SB",serif; border:1px solid #777; padding:2pt; margin:0 0 6pt; }
.measured-social .question { grid-template-columns:15pt minmax(0,1fr); column-gap:3pt; margin:0 0 6pt; }
.measured-social .qno { font-weight:400; }
.measured-social .score { float:none; font-size:inherit; margin-left:0; }
.measured-social .prompt,.measured-social .stimulus { text-align:justify; line-break:strict; line-height:17.4pt; }
.measured-social .options { margin-top:0; row-gap:0; }
.measured-social .option { grid-template-columns:20pt minmax(0,1fr); line-height:17.4pt; }
.measured-social .group-label { font-weight:400; text-decoration:underline; margin:6pt 0 3pt; }
.measured-social .stimulus { margin:0 0 5pt; padding:0 0 0 18pt; white-space:normal; }
.measured-social .figure { margin:7pt auto; }
.measured-social .figure figcaption { font-size:10pt; line-height:14pt; }
.measured-social .social-cover { padding:31.5mm 28.52mm 18mm; font-family:"DFKai-SB",serif; }
.measured-social .social-cover .org,.measured-social .social-cover .year { margin:0; font-size:18pt; line-height:30pt; letter-spacing:0; }
.measured-social .social-cover .subject { margin:1pt 0 25pt; font-size:24pt; line-height:30pt; letter-spacing:0; }
.measured-social .social-cover .sign { margin:0 0 18pt; font-size:16pt; line-height:21pt; background:#ddd; text-decoration:none; white-space:nowrap; }
.measured-social .social-cover .notice { width:100%; padding:15pt 32pt 14pt; min-height:0; font-size:11.04pt; line-height:18pt; }
.measured-social .social-cover .notice h1 { font-size:14pt; margin:0 0 14pt; text-align:center; }
.measured-social .social-cover .notice p { margin:0 0 8pt; }
.measured-social .social-cover .notice ul { margin:0 0 12pt; padding-left:25pt; }
.measured-social .social-cover .notice li { margin:0; }
.measured-social .answer-sheet { padding-top:17mm!important; }
.measured-social .answer-header { display:flex; justify-content:space-between; height:12mm; font:10pt "DFKai-SB",serif; }
.measured-social .answer-content { height:250mm; }
.measured-social .answer-content h1 { font-size:16pt; line-height:23pt; margin:0 0 8pt; text-align:center; }
.measured-social .answer-grid { font-size:11.04pt; line-height:15pt; table-layout:fixed; }
.measured-social .answer-grid th:first-child { width:45pt; }
.measured-social .answer-grid th:last-child { width:65pt; }
.measured-social .answer-grid th { white-space:nowrap; }
.measured-social .answer-grid td,.measured-social .answer-grid th { padding:3pt 6pt; }
.measured-social .solution { margin:0 0 12pt; padding:0 0 8pt; line-height:18pt;
  line-break:strict; overflow-wrap:normal; word-break:normal; }
.measured-social .solution h2 { font-size:12pt; line-height:18pt; margin:0 0 5pt; }
.measured-social .solution ol,.measured-social .solution p { margin:0 0 5pt; }
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


def _math_text_block(value: Any, *, keep_closing_punctuation: bool = False) -> str:
    """Render delimited mathematics statically, and escape all ordinary prose.

No TeX engine, shell escape, browser script, remote font or remote asset is used.
LaTeX fragments are presentation data; reject active/unknown MathML output.
"""
    raw = str(value if value is not None else "")
    parts = re.split(r"(\\\(.*?\\\)|\\\[.*?\\\])", raw, flags=re.S)
    if len(parts) > 1:
        rendered = []
        for index, part in enumerate(parts):
            if not part.startswith((r"\(", r"\[")):
                rendered.append(_math_plain_text(part))
                continue
            block = part.startswith(r"\[")
            math = _static_mathml(part[2:-2], block=block)
            # Bind only an inline formula and its immediate closing punctuation.
            # Never make an entire solution, adjacent formula, or display block
            # unbreakable. Escaping/MathML screening remains mandatory.
            punctuation = (re.match(r"^[，。、；：！？）」』】〕〉》]+", parts[index + 1])
                           if keep_closing_punctuation and not block and index + 1 < len(parts) else None)
            if punctuation:
                suffix = punctuation.group()
                parts[index + 1] = parts[index + 1][len(suffix):]
                math = f'<span class="math-with-punctuation">{math}{esc(suffix)}</span>'
            rendered.append(math)
        return "".join(rendered)
    if any(token in raw for token in (r"\(", r"\)", r"\[", r"\]")):
        raise ValueError("Unpaired mathematics delimiter")
    return _math_plain_text(raw)


def _static_mathml(latex: str, *, block: bool = False) -> str:
    if len(latex) > 6000 or latex.count("{") > 250:
        raise ValueError("Mathematics fragment exceeds the rendering budget")
    if re.search(r"\\(?:href|url|include|input|write|read|html|style|class|def|newcommand|require)", latex, re.I):
        raise ValueError("Active or external TeX commands are not allowed")
    # The static converter tokenizes a bare multi-digit argument differently
    # from TeX. Never let e.g. \\binom63 consume '=' as its second argument.
    for match in re.finditer(r"\\(?:frac|dfrac|tfrac|binom|dbinom|tbinom)(?![A-Za-z])", latex):
        cursor = match.end()
        for _ in range(2):
            while cursor < len(latex) and latex[cursor].isspace():
                cursor += 1
            if cursor >= len(latex) or latex[cursor] != "{":
                raise ValueError("Fractions and binomials require two explicitly braced arguments")
            depth = 1
            cursor += 1
            while cursor < len(latex) and depth:
                depth += (latex[cursor] == "{") - (latex[cursor] == "}")
                cursor += 1
            if depth:
                raise ValueError("Unclosed braced mathematics argument")
    from latex2mathml.converter import convert
    rendered = convert(latex, display="block" if block else "inline")
    # CEEC's printed fractions keep full-sized main numerators/denominators.
    # Native inline MathML otherwise shrinks them to script size by default.
    rendered = rendered.replace('<math ', '<math displaystyle="true" ', 1)
    allowed = set("math mrow mi mn mo mtext mspace mfrac msqrt mroot msub msup msubsup mover munder munderover mtable mtr mtd mstyle mpadded mphantom mfenced menclose mmultiscripts mprescripts none".split())
    try:
        tree = ET.fromstring(rendered)
    except ET.ParseError as exc:
        raise ValueError("Invalid static mathematical markup") from exc
    # Space functions at expression-row level only. A text replacement inside
    # msub/msup adds a third child, silently turning log bases and powers into
    # baseline text in browsers. Preserve every fixed-arity MathML structure.
    local = lambda node: node.tag.rsplit("}", 1)[-1]
    namespace = "http://www.w3.org/1998/Math/MathML"
    def is_function(node):
        if local(node) in {"msub", "msup", "msubsup"} and len(node):
            node = node[0]
        return local(node) == "mi" and node.text in {"sin", "cos", "tan", "log", "ln"}
    for row in list(tree.iter()):
        if local(row) != "mrow":
            continue
        children = list(row)
        for index in range(len(children) - 2, -1, -1):
            if is_function(children[index]) and local(children[index + 1]) in {"mi", "mn", "mrow", "msub", "msup", "msubsup"}:
                row.insert(index + 1, ET.Element(f"{{{namespace}}}mspace", {"width": "0.1667em"}))
    arities = {"msub": 2, "msup": 2, "msubsup": 3, "mfrac": 2,
               "mroot": 2, "mover": 2, "munder": 2, "munderover": 3}
    for node in tree.iter():
        tag = local(node)
        if tag not in allowed:
            raise ValueError("Unsupported mathematical presentation element")
        if tag in arities and len(node) != arities[tag]:
            raise ValueError(f"Invalid child count for mathematical {tag}")
        for key, val in node.attrib.items():
            if key.lower().startswith("on") or key in {"href", "src", "style"} or re.search(r"url\s*\(|javascript:|https?://", val, re.I):
                raise ValueError("Active mathematics attributes are not allowed")
    ET.register_namespace("", namespace)
    return ET.tostring(tree, encoding="unicode")


def _math_plain_text(value: Any) -> str:
    """Normalize legacy Unicode scripts while leaving prose as escaped text."""
    if any(token in str(value) for token in (r"\(", r"\)", r"\[", r"\]")):
        raise ValueError("Unpaired mathematics delimiter")
    if re.search(r"[A-Za-z0-9)\]][_^]", str(value)):
        raise ValueError("Unrendered subscript/exponent: delimit mathematical notation explicitly")
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
        bottom = (f'<span class="fixed-denominator">{esc(spec["fixed_denominator"])}</span>'
                  if spec.get("fixed_denominator") is not None else slots(denominator, numerator + 1))
        return f'<span class="fill-format"><span class="fill-fraction">{top}{bottom}</span></span>'
    return f'<span class="fill-format"><span class="integer-rail">{slots(int(spec.get("slots") or 1))}</span></span>'


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
    response_html = ""
    response_spec = q.get("response_format_table") or {}
    if subject == "社會" and response_spec.get("kind") == "social_monitoring_table":
        rows = "".join(
            f'<tr><td><b>{esc(row.get("label"))}</b>{_paper_text(row.get("instruction"), subject)}</td></tr>'
            for row in (response_spec.get("rows") or [])
        )
        if rows:
            caption = f'<caption>{_paper_text(response_spec.get("caption"), subject)}</caption>' if response_spec.get("caption") else ""
            response_html = f'<table class="answer-grid">{caption}<thead><tr><th>{_paper_text(response_spec.get("heading") or "作答格式", subject)}</th></tr></thead><tbody>{rows}</tbody></table>'
    lines = ""
    # Current GSAT Social Studies and English write constructed responses on
    # the separate answer sheet.  Legacy worksheet-style line counts must not
    # leak into either verified student booklet.
    if q.get("answer_space_lines") and subject not in {"社會", "英文"}:
        lines = '<div class="answer-lines">' + '<div class="answer-line"></div>' * int(q["answer_space_lines"]) + '</div>'
    fill = _fill_format(q)
    # Keep points in the source JSON for validation.  Official GSAT-style
    # sections normally state a shared score once, so per-item labels are an
    # explicit opt-in rather than the renderer default.
    score = f'<span class="score">（{esc(q.get("score"))}分）</span>' if q.get("score") is not None and q.get("show_score_label", False) else ""
    target_height = q.get("target_height_mm")
    height_style = f' style="min-height:{float(target_height):g}mm"' if target_height else ""
    prompt_text = _paper_text(q["prompt"], subject)
    if subject == "自然" and q.get("type") == "multiple_choice":
        if "應選" in str(q.get("prompt") or ""):
            raise ValueError(f'自然第 {q.get("number")} 題的應選項數必須由 required_selection_count 統一產生，不可手寫在題幹')
        required_count = q.get("required_selection_count")
        if not isinstance(required_count, int) or required_count < 2 or required_count >= len(options):
            raise ValueError(f'自然第 {q.get("number")} 題缺少有效 required_selection_count')
        prompt_text += f'（應選{required_count}項）'
    if fill and "______" in prompt_text:
        prompt_text = prompt_text.replace("______", fill, 1)
        fill = ""
    prompt = (f'<div class="prompt">{prompt_text}{score}</div>' if subject == "社會"
              else f'<div class="prompt">{score}{prompt_text}</div>')
    if side_visual:
        core = f'<div class="stem-side"><div>{prompt}{fill}</div>{visual}</div>{option_html}{response_html}{lines}'
    else:
        core = f'{prompt}{visual}{option_html}{fill}{response_html}{lines}'
    number_display = q.get("number_display") or f'{q["number"]}.'
    section_class = f' section-{esc(q.get("section_id") or "")}' if q.get("section_id") else ""
    return f'{group}{stimulus}<article class="question{section_class}"{height_style}><div class="qno">{esc(number_display)}</div><div>{core}</div></article>'


def _cover(meta: dict[str, Any], instructions: list[str]) -> str:
    if (meta.get("paper_subject") or meta.get("subject")) == "社會" and int(meta.get("layout_contract_version") or 0) >= 4:
        return _social_cover(meta)
    if (meta.get("paper_subject") or meta.get("subject")) in {"數學A", "數學B"} and int(meta.get("layout_contract_version") or 0) >= 3:
        return _math_cover(meta)
    if (meta.get("paper_subject") or meta.get("subject")) == "國寫" and int(meta.get("layout_contract_version") or 0) >= 3:
        return _writing_cover(meta)
    if (meta.get("paper_subject") or meta.get("subject")) == "自然" and int(meta.get("layout_contract_version") or 0) >= 5:
        return _natural_cover(meta)
    bullets = "".join(f'<li>{text_block(x)}</li>' for x in instructions)
    scoring = meta.get("scoring_note") or "各題計分方式依題本各大題說明。"
    return f'''<section class="sheet cover"><div class="org">Taiwan Exam 命題系統｜內部校樣</div>
<div class="year">116學年度學科能力測驗完整規格校樣卷</div>
<div class="subject">{esc(meta.get("paper_label") or meta["subject"])}</div>
<div class="sign">請於考試開始鈴響起，在答題卷簽名欄位以正楷簽全名</div>
<div class="notice"><h1>作答注意事項</h1><p><b>考試時間：</b>{esc(meta.get("duration_minutes"))}分鐘</p>
<h2>作答方式：</h2><ul>{bullets}</ul><h2>計分方式：</h2><p>{text_block(scoring)}</p></div>
<div class="prototype">完整題數／配分／時間內部校樣｜內容原創、未經代表性考生預試｜版面為115題本參照校樣，非大考中心正式試題</div></section>'''


def _natural_cover(meta: dict[str, Any]) -> str:
    """Measured 115 Natural Science cover with the complete choice scoring contract."""
    score_fraction = _static_mathml(r"\frac{n-2k}{n}")
    title = esc(meta.get("cover_year_title") or "116學年度學科能力測驗模擬試題")
    return f'''<section class="sheet cover natural-cover"><div class="org">Taiwan Exam 模擬試題</div>
<div class="year">{title}</div><div class="subject">自然考科</div>
<div class="sign">請於考試開始鈴響起，在答題卷簽名欄位以正楷簽全名</div>
<div class="notice"><h1>－作答注意事項－</h1>
<p>考試時間：110分鐘</p><p>作答方式：</p><ul>
<li>選擇題用 2B 鉛筆在「答題卷」上作答；更正時以橡皮擦擦拭，切勿使用修正帶（液）。</li>
<li>除題目另有規定外，非選擇題用筆尖較粗之黑色墨水的筆在「答題卷」上作答；更正時，可以使用修正帶（液）。</li>
<li>考生須依上述規定劃記或作答，若未依規定而導致答案難以辨識或評閱時，恐將影響成績。</li>
<li>答題卷每人一張，不得要求增補。</li></ul>
<p>選擇題計分方式：</p><ul>
<li><b>單選題：</b>每題有 <i>n</i> 個選項，其中只有一個是正確或最適當的選項。各題答對者，得該題的分數；答錯、未作答或劃記多於一個選項者，該題以零分計算。</li>
<li><b>多選題：</b>每題有 <i>n</i> 個選項，其中至少有一個是正確的選項。各題之選項獨立判定，所有選項均答對者，得該題全部的分數；答錯 <i>k</i> 個選項者，得該題 {score_fraction} 的分數；但得分低於零分或所有選項均未作答者，該題以零分計算。</li>
</ul></div><div class="prototype">115當代卷型參照｜完整題數、配分與時間｜原創內容、未經代表性考生預試｜非大考中心正式試題</div></section>'''


def _social_cover(meta: dict[str, Any]) -> str:
    """115 measured social cover; display branding never impersonates CEEC."""
    return f'''<section class="sheet cover social-cover"><div class="org">Taiwan Exam 模擬試題</div>
<div class="year">{esc(meta.get("cover_year_title") or "116學年度學科能力測驗模擬試題")}</div>
<div class="subject">社會考科</div>
<div class="sign">請於考試開始鈴響起，在答題卷簽名欄位以正楷簽全名</div>
<div class="notice"><h1>－作答注意事項－</h1>
<p>考試時間：110分鐘</p><p>作答方式：</p><ul>
<li>選擇題用 2B 鉛筆在「答題卷」上作答；更正時以橡皮擦擦拭，切勿使用修正帶（液）。</li>
<li>除題目另有規定外，非選擇題用筆尖較粗之黑色墨水的筆在「答題卷」上作答；更正時，可以使用修正帶（液）。</li>
<li>考生須依上述規定劃記或作答，若未依規定而導致答案難以辨識或評閱時，恐將影響成績。</li>
<li>答題卷每人一張，不得要求增補。</li></ul>
<p>選擇題計分方式：</p><ul><li>單選題：每題有 4 個選項，其中只有一個是正確或最適當的選項。各題答對者，得該題的分數；答錯、未作答或劃記多於一個選項者，該題以零分計算。</li></ul></div></section>'''


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
    if int(meta.get("layout_contract_version") or 0) >= 4:
        return _measured_math_cover(meta)
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


def _marking_rows(rows: list[tuple[str, str]]) -> str:
    """Official response-example geometry, not an answer-sheet substitute."""
    symbols = list("1234567890") + ["−", "±"]
    return '<div class="mark-example">' + "".join(
        '<div class="mark-row"><span>' + esc(label) + '</span>' + "".join(
            f'<span class="mark-cell{" marked" if symbol == selected else ""}">{esc(symbol)}<b></b></span>'
            for symbol in symbols
        ) + '</div>' for label, selected in rows
    ) + '</div>'


def _measured_math_cover(meta: dict[str, Any]) -> str:
    fraction = _fill_format({"number":18, "answer_format":{"kind":"fraction","numerator_slots":1,"denominator_slots":1}})
    signed = _fill_format({"number":19, "answer_format":{"kind":"fraction","numerator_slots":2,"fixed_denominator":"50"}})
    fraction_value = _static_mathml(r"\frac{3}{8}")
    signed_value = _static_mathml(r"\frac{-7}{50}")
    score_fraction = _static_mathml(r"\frac{n-2k}{n}")
    title = esc(meta.get("cover_year_title") or "116學年度學科能力測驗模擬試題")
    label = esc(meta.get("paper_subject") or meta["subject"]) + "考科"
    return f'''<section class="sheet cover math-cover">
<div class="org">Taiwan Exam 模擬試題</div><div class="year">{title}</div>
<div class="subject">{label}</div>
<div class="sign">請於考試開始鈴響起，在答題卷簽名欄位以正楷簽全名</div>
<div class="notice"><h1>—作答注意事項—</h1>
<p>考試時間：{esc(meta.get("duration_minutes"))}分鐘</p><p>作答方式：</p><ul>
<li>選擇（填）題用 2B 鉛筆在「答題卷」上作答；更正時以橡皮擦擦拭，切勿使用修正帶（液）。</li>
<li>除題目另有規定外，非選擇題用筆尖較粗之黑色墨水的筆在「答題卷」上作答；更正時，可以使用修正帶（液）。</li>
<li>考生須依上述規定劃記或作答，若未依規定而導致答案難以辨識或評閱時，恐將影響成績。</li>
<li>答題卷每人一張，不得要求增補。</li>
<li>選填題考生必須依各題的格式填答，且每一個列號只能在一個格子劃記。請仔細閱讀下面的例子。</li></ul>
<div class="cover-fill-example">例：若答案格式是{fraction}，而依題意計算出來的答案是{fraction_value}，則考生必須分別在答題卷</div>
<div class="cover-fill-direction">上的第 18-1 列的 3 與第 18-2 列的 8 劃記，如：</div>
{_marking_rows([("18-1","3"),("18-2","8")])}
<div class="cover-fill-example">例：若答案格式是{signed}，而答案是{signed_value}時，則考生必須分別在答題卷的第19-1列</div>
<div class="cover-fill-direction">的 − 與第 19-2 列的 7 劃記，如：</div>
{_marking_rows([("19-1","−"),("19-2","7")])}
<p>選擇（填）題計分方式：</p><ul>
<li>單選題：每題有 <i>n</i> 個選項，其中只有一個是正確或最適當的選項。各題答對者，得該題的分數；答錯、未作答或劃記多於一個選項者，該題以零分計算。</li>
<li>多選題：每題有 <i>n</i> 個選項，其中至少有一個是正確的選項。各題之選項獨立判定，所有選項均答對者，得該題全部的分數；答錯 <i>k</i> 個選項者，得該題 {score_fraction} 的分數；但得分低於零分或所有選項均未作答者，該題以零分計算。</li>
<li>選填題每題有 <i>n</i> 個空格，須全部答對才給分，答錯不倒扣。</li></ul>
<p>※試題中參考的附圖均為示意圖，試題後附有參考公式及數值。</p></div></section>'''


def _measured_math_formulas(subject: str = "數學A") -> str:
    """The canonical reviewed subject formula asset; never question content."""
    return gsat_115_formula_markup(subject)


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
                if subject in {"數學A", "數學B"} and int(meta.get("layout_contract_version") or 0) >= 4 and q["number"] == 1:
                    first_part_score = sum(item.get("score", 0) for item in exam["questions"] if item.get("type") != "constructed_response" and item.get("number", 0) < 18)
                    body.append(f'<h1 class="section-head part-head">第壹部分、選擇（填）題（占{first_part_score:g}分）</h1>')
                body.append(f'<h1 class="section-head">{_paper_text(section["title"], subject)}</h1>')
                if notes:
                    body.append(f'<div class="section-rule">{_paper_text(notes, subject)}</div>')
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
        measured_math = subject in {"數學A", "數學B"} and int(meta.get("layout_contract_version") or 0) >= 4
        if measured_math and page_no == total:
            body.append(_measured_math_formulas(subject))
        elif extra:
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
        measured_social = subject == "社會" and int(meta.get("layout_contract_version") or 0) >= 4
        if page_no == total and not (measured_math or measured_social) and not meta.get("suppress_student_trace"):
            reference_year = meta.get("layout_reference_year", 115)
            body.append(f'<div class="trace">Paper Profile：{esc(meta.get("paper_profile_id"))}｜參照：{esc(reference_year)}學年度｜難度：專家估計、待預試｜Layout：reference-only</div>')
        page_mark = f'第 {page_no-1} 頁<br>共 {total-1} 頁'
        raw_year_label = str(meta.get("running_year_label") or "116年學測")
        year_label = f'{raw_year_label}年學測' if raw_year_label.isdigit() else raw_year_label
        subject_mark = f'{esc(year_label)}<br>{esc(meta.get("paper_label") or subject)}'
        left_mark, right_mark = (page_mark, subject_mark) if (page_no - 1) % 2 else (subject_mark, page_mark)
        outer = " outer-right" if (page_no - 1) % 2 == 0 else ""
        footer = f'<span class="center{outer}">- {page_no-1} -</span>' if (measured_math or measured_social) else f'<span>內部測試</span><span class="center">- {page_no-1} -</span><span class="right">未經預試</span>'
        pages.append(f'''<section class="sheet"><div class="header"><span>{left_mark}</span><span class="mid">請記得在答題卷簽名欄位以正楷簽全名</span><span class="right">{right_mark}</span></div><main class="content">{"".join(body)}</main><div class="footer">{footer}</div></section>''')
    return "".join(pages)


def _answers(exam: dict[str, Any]) -> str:
    meta = exam["metadata"]
    subject = meta.get("paper_subject") or meta["subject"]
    measured_math = subject in {"數學A", "數學B"} and int(meta.get("layout_contract_version") or 0) >= 4
    def answer_text(value: Any) -> str:
        def item_text(item: Any) -> str:
            if measured_math:
                return _math_text_block(item, keep_closing_punctuation=True)
            return _paper_text(item, subject)
        if isinstance(value, list):
            return "、".join(item_text(item) for item in value)
        return item_text(value)
    number = {q["id"]: q["number"] for q in exam["questions"]}
    answers = exam.get("answers") or []
    difficulty_names = {
        "easy": "簡單", "medium": "中", "medium_hard": "中偏難", "hard": "難", "very_hard": "難",
    }
    row_items = [
        (
            f'<tr><td>{esc(number.get(a["question_id"], a["question_id"]))}</td><td>{answer_text(a.get("final_answer"))}</td><td>{esc(difficulty_names.get(a.get("difficulty_label"), a.get("difficulty_label") or "-"))}</td></tr>',
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
        body = '<ol>' + ''.join(f'<li>{answer_text(x)}</li>' for x in reasoning) + '</ol>' if reasoning else ""
        for block in a.get("explanation_blocks") or []:
            body += f'<p><b>{esc(block.get("title") or "說明")}：</b>{answer_text(block.get("content"))}</p>'
        details.append(f'<article class="solution"><h2>第 {esc(number.get(a["question_id"]))} 題　答案：{answer_text(a.get("final_answer"))}</h2>{body}</article>')
    quick_pages = []
    # Keep each table inside an explicit page-sized chunk.  The capacity is
    # slightly below the physical maximum so borders and wrapped CJK text do
    # not trigger an implicit spill page at print time.
    row_chunks: list[list[str]] = []
    current_rows: list[str] = []
    current_weight = 0
    # Social's measured 11.04 pt table needs a smaller row budget than the
    # generic 8.5 pt quick key. This is layout only, never item generation.
    quick_row_budget = 25 if subject == "社會" and int(meta.get("layout_contract_version") or 0) >= 4 else 33
    for row_html, row_weight in row_items:
        if current_rows and current_weight + row_weight > quick_row_budget:
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
    if measured_math or (subject == "社會" and int(meta.get("layout_contract_version") or 0) >= 4):
        heading = f'<h1>{esc(meta.get("paper_label") or subject)}答案與詳解</h1><p>難度為命題者估計，尚非考生預試結果。學生試題與本檔分開發放。</p>'
        quick_pages[0] = quick_pages[0].replace('<h1>答案速查</h1>', heading, 1)
        # The author/editor supplies a page plan for the actual explanations.
        # Do not use a dummy fixed cover to hide unmeasured flowing pages.
        groups = meta.get("answer_page_groups")
        expected_ids = [a["question_id"] for a in answers]
        if not isinstance(groups, list) or not groups or any(not isinstance(g, list) or not g for g in groups):
            raise ValueError("實測格式詳解需要事先規劃 answer_page_groups，並實測每頁容納範圍")
        flat_ids = [qid for group in groups for qid in group]
        if flat_ids != expected_ids:
            raise ValueError("answer_page_groups 必須依題序恰好包含每題詳解一次")
        by_id = dict(zip(expected_ids, details))
        contents = [re.sub(r'^<section class="answer-page">|</section>$', '', page) for page in quick_pages]
        contents.extend(''.join(by_id[qid] for qid in group) for group in groups)
        if meta.get("answer_expected_page_count") != len(contents):
            raise ValueError("詳解頁面規劃數與 answer_expected_page_count 不符")
        total = len(contents)
        title = esc(meta.get("paper_label") or subject)
        return ''.join(
            f'<section class="sheet answer-sheet"><div class="answer-header"><span>{title}　教師用詳解</span>'
            f'<span>第 {i} 頁／共 {total} 頁</span></div><main class="content answer-content">{body}</main>'
            f'<div class="footer"><span class="center{" outer-right" if i % 2 == 0 else ""}">- {i} -</span></div></section>'
            for i, body in enumerate(contents, 1)
        )
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


def render(exam: dict[str, Any], *, answers_only: bool = False, include_answers: bool = False,
           base: Path, run_contract: Path | None = None) -> str:
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
    if answers_only:
        body = _answers(exam)
    else:
        body = _cover(meta, exam["instructions"]) + _pages(exam, base)
        if include_answers:
            body += _answers(exam)
    paper_subject = meta.get("paper_subject") or meta["subject"]
    mode_class = " measured-math" if paper_subject in {"數學A", "數學B"} and int(meta.get("layout_contract_version") or 0) >= 4 else ""
    if paper_subject == "社會" and int(meta.get("layout_contract_version") or 0) >= 4:
        mode_class = " measured-social"
    return f'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>{esc(meta["title"])}</title><style>{STYLE}</style></head><body class="paper-{esc(paper_subject)}{mode_class}">{body}</body></html>'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--answers-only", action="store_true")
    parser.add_argument("--include-answers", action="store_true")
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args(argv)
    try:
        exam = json.loads(args.input.read_text(encoding="utf-8-sig"))
        if args.answers_only and args.include_answers:
            raise ValueError("--answers-only 與 --include-answers 不可同時使用")
        html = render(exam, answers_only=args.answers_only, include_answers=args.include_answers,
                      base=args.input.resolve().parent, run_contract=args.contract)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html, encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    print(f"已輸出內部校樣 HTML：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
