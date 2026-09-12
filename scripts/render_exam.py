#!/usr/bin/env python3
"""Render structured exam JSON to a print-ready, self-contained HTML file."""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import sys
from pathlib import Path
from typing import Any


STYLE = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
:root { --ink: #111; --muted: #555; --rule: #222; --light: #e8e8e8; }
* { box-sizing: border-box; }
html { color: var(--ink); background: #ececec; font-family: "Noto Serif TC", "Noto Serif CJK TC", "PMingLiU", "Times New Roman", serif; }
body { width: 210mm; margin: 0 auto; padding: 14mm 16mm; background: white; line-height: 1.65; font-size: 11.5pt; }
.exam-header { text-align: center; border-bottom: 2px solid var(--rule); padding-bottom: 5mm; margin-bottom: 5mm; }
.exam-title { margin: 0; font-size: 21pt; letter-spacing: .08em; font-weight: 700; }
.exam-subtitle { margin: 1.5mm 0 0; color: var(--muted); font-size: 11pt; }
.meta-grid { display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid var(--rule); margin: 4mm 0; }
.meta-grid div { padding: 2.2mm 3mm; border-right: 1px solid var(--rule); }
.meta-grid div:last-child { border-right: 0; }
.candidate { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8mm; margin: 4mm 0; }
.blank { display: inline-block; width: 34mm; border-bottom: 1px solid var(--ink); min-height: 1em; }
.instructions { border: 1px solid var(--rule); padding: 3mm 5mm; margin: 4mm 0 7mm; }
.instructions h2 { font-size: 12pt; margin: 0 0 1mm; }
.instructions ol { margin: 0 0 0 1.4em; padding: 0; }
.section { margin-top: 7mm; }
.section-title { font-size: 14pt; border-bottom: 1.5px solid var(--rule); margin: 0 0 3mm; padding-bottom: 1mm; }
.section-note { color: var(--muted); margin: 0 0 4mm; }
.question { display: grid; grid-template-columns: 8mm 1fr; column-gap: 2mm; break-inside: avoid; margin: 0 0 6mm; }
.question-number { font-weight: 700; }
.question-body p { margin: 0 0 2mm; }
.score { float: right; color: var(--muted); font-size: 9.5pt; }
.stimulus { border-left: 3px solid #777; padding: 2mm 4mm; margin: 1mm 0 3mm; background: #f8f8f8; white-space: pre-wrap; }
.question-figure { margin: 3mm auto; text-align: center; break-inside: avoid; }
.question-figure img { display: block; max-width: 100%; max-height: 118mm; margin: 0 auto; object-fit: contain; }
.question-figure figcaption { margin-top: 1.2mm; color: var(--muted); font-size: 9.5pt; }
.options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.5mm 7mm; margin: 2mm 0 0; }
.option { display: grid; grid-template-columns: 7mm 1fr; }
.answer-lines { margin-top: 3mm; }
.answer-line { border-bottom: 1px solid #aaa; height: 8mm; }
.answer-key { break-before: page; }
.answer-key table { width: 100%; border-collapse: collapse; }
.answer-key th, .answer-key td { border: 1px solid var(--rule); padding: 2mm 3mm; text-align: left; vertical-align: top; }
.answer-summary th, .answer-summary td { text-align: center; }
.solution-details { columns: 2; column-gap: 10mm; column-rule: 1px solid var(--light); margin-top: 7mm; }
.solution-card { break-inside: avoid-column; margin: 0 0 6mm; padding-bottom: 4mm; border-bottom: 1px solid var(--light); }
.solution-card h2 { margin: 0 0 2mm; font-size: 13pt; }
.solution-card h3 { margin: 2.5mm 0 1mm; font-size: 10.5pt; font-family: sans-serif; }
.solution-meta { margin: 0 0 2mm; font-size: 9.5pt; color: var(--muted); }
.solution-meta span { display: inline-block; margin-right: 3mm; }
.solution-card p { margin: 0 0 1.5mm; white-space: pre-wrap; }
.solution-card ol { margin: 1mm 0 2mm 1.5em; padding: 0; }
.trace { margin-top: 8mm; font-family: sans-serif; font-size: 8.5pt; color: var(--muted); border-top: 1px solid var(--light); padding-top: 2mm; overflow-wrap: anywhere; }
@media print {
  html { background: white; }
  body { width: auto; margin: 0; padding: 0; }
  .no-print { display: none; }
}
@media screen and (max-width: 800px) {
  body { width: 100%; padding: 24px; }
  .meta-grid { grid-template-columns: repeat(2, 1fr); }
  .options { grid-template-columns: 1fr; }
}
"""


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def text_block(value: Any) -> str:
    return esc(value).replace("\n", "<br>\n")


def verification_label(value: Any) -> str:
    return {
        "unverified": "未驗證",
        "single_pass": "單次驗證",
        "independently_verified": "已獨立驗證",
    }.get(str(value), str(value or ""))


BLOCK_LABELS = {
    "concept": "觀念",
    "analysis": "解析",
    "option_analysis": "選項辨析",
    "translation": "翻譯",
    "vocabulary": "重要字詞",
    "alternate_solution": "另解",
    "writing_guidance": "寫作引導",
    "sample_response": "參考作答",
    "scoring_rubric": "評分規準",
    "note": "補充",
}


def validate_exam(exam: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(exam, dict):
        return ["exam 必須是 JSON object"]
    for key in ("metadata", "instructions", "sections", "questions"):
        if key not in exam:
            errors.append(f"缺少 {key}")
    if errors:
        return errors
    metadata = exam["metadata"]
    for key in ("title", "exam", "subject", "calibration_level"):
        if key not in metadata:
            errors.append(f"metadata 缺少 {key}")
    section_ids = {section.get("id") for section in exam["sections"]}
    seen_numbers: set[int] = set()
    seen_ids = set()
    for index, question in enumerate(exam["questions"], 1):
        for key in ("id", "number", "section_id", "type", "prompt"):
            if key not in question:
                errors.append(f"第 {index} 筆 question 缺少 {key}")
        if question.get("section_id") not in section_ids:
            errors.append(f"第 {index} 筆 question 指向未知 section")
        number = question.get("number")
        if not question.get('id') or question.get('id') in seen_ids:
            errors.append(f'第 {index} 筆 question 的 id 缺少或重複')
        seen_ids.add(question.get('id'))
        if number is None:
            if not question.get('answer_label') or not (question.get('item_spec') or {}).get('slot_id'):
                errors.append(f'第 {index} 筆無連續題號的 question 需要 answer_label 與 item_spec.slot_id')
        elif not isinstance(number, int) or isinstance(number, bool) or number < 1:
            errors.append(f'第 {index} 筆 question 的題號必須為正整數或 null')
        else:
            if number in seen_numbers:
                errors.append(f"題號 {number} 重複")
            seen_numbers.add(number)
    if metadata.get("generation_mode") == "full-paper":
        expected = metadata.get("expected_question_count")
        if not metadata.get("paper_profile_id"):
            errors.append("完整卷缺少 paper_profile_id")
        if not metadata.get("layout_profile"):
            errors.append("完整卷缺少 layout_profile；不可用通用版型冒充正式考卷")
        if metadata.get("layout_fidelity_status") != "verified":
            errors.append("完整卷的 layout_fidelity_status 必須為 verified 才能宣稱正式排版")
        if expected is None:
            errors.append("完整卷缺少 expected_question_count")
        elif len(exam["questions"]) != expected:
            errors.append(f"完整卷題數不符 Paper Profile：應為 {expected} 題，實為 {len(exam['questions'])} 題")
        total = metadata.get("total_score")
        actual_total = sum((question.get("score") or 0) for question in exam["questions"])
        if total is not None and abs(actual_total - total) > 1e-9:
            errors.append(f"完整卷總分不符：metadata 為 {total}，逐題加總為 {actual_total}")
        expected_counts = metadata.get("expected_section_counts") or {}
        expected_scores = metadata.get("expected_section_scores") or {}
        for section_id, count in expected_counts.items():
            actual = sum(question.get("section_id") == section_id for question in exam["questions"])
            if actual != count:
                errors.append(f"{section_id} 題數不符：應為 {count}，實為 {actual}")
        for section_id, score in expected_scores.items():
            actual = sum((question.get("score") or 0) for question in exam["questions"] if question.get("section_id") == section_id)
            if abs(actual - score) > 1e-9:
                errors.append(f"{section_id} 配分不符：應為 {score}，實為 {actual}")
    return errors


def image_data_uri(path_value: str, asset_base: Path | None) -> str:
    from safe_rendering import validate_image
    if path_value.startswith(('\\\\', '//')):
        raise ValueError('Network image paths are not allowed')
    base = (asset_base or Path.cwd()).resolve()
    path = Path(path_value)
    if not path.is_absolute():
        path = (asset_base or Path.cwd()) / path
    path = path.resolve()
    if not path.is_relative_to(base):
        raise ValueError('題目圖片必須位於 exam.json 的資料夾內，不能讀取資料夾外的檔案')
    if not path.is_file():
        raise ValueError(f"找不到題目圖片：{path}")
    mime, _ = mimetypes.guess_type(path.name)
    if mime not in {"image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"}:
        raise ValueError(f"不支援的題目圖片格式：{path.suffix or path.name}")
    data = path.read_bytes()
    validate_image(data, mime)
    payload = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{payload}"


def render_visual(asset: Any, asset_base: Path | None) -> str:
    if not asset:
        return ""
    if not isinstance(asset, dict) or not asset.get("path") or not asset.get("alt"):
        raise ValueError("visual_asset 必須包含 path 與不洩漏答案的 alt")
    width = asset.get("width_percent") or 72
    if not isinstance(width, int) or not 20 <= width <= 100:
        raise ValueError("visual_asset.width_percent 必須為 20 至 100 的整數")
    source = image_data_uri(str(asset["path"]), asset_base)
    caption = asset.get("caption")
    caption_html = f"<figcaption>{text_block(caption)}</figcaption>" if caption else ""
    return (
        f'<figure class="question-figure" style="width:{width}%">'
        f'<img src="{source}" alt="{esc(asset["alt"])}">{caption_html}</figure>'
    )


def question_number_display(question: dict[str, Any]) -> str:
    if 'number_display' in question:
        return question['number_display']
    return f"{question['number']}." if question.get('number') is not None else ''


def answer_question_label(question: dict[str, Any]):
    return question['number'] if question.get('number') is not None else question.get('answer_label') or question['id']


def answer_heading(label) -> str:
    return f'第 {esc(label)} 題' if isinstance(label, int) else esc(label)


def render_question(question: dict[str, Any], asset_base: Path | None = None) -> str:
    score = question.get("score")
    score_html = f'<span class="score">（{esc(score)} 分）</span>' if score is not None else ""
    stimulus = question.get("group_stimulus")
    stimulus_html = f'<div class="stimulus">{text_block(stimulus)}</div>' if stimulus else ""
    options = question.get("options", [])
    options_html = ""
    if options:
        rendered = "".join(
            f'<div class="option"><span>({esc(option["label"])})</span><span>{text_block(option["text"])}</span></div>'
            for option in options
        )
        options_html = f'<div class="options">{rendered}</div>'
    line_count = question.get("answer_space_lines") or 0
    lines_html = ""
    if line_count:
        lines_html = '<div class="answer-lines">' + '<div class="answer-line"></div>' * line_count + "</div>"
    visual = render_visual(question.get("visual_asset"), asset_base)
    placement = (question.get("visual_asset") or {}).get("placement", "after_prompt")
    prompt_html = f"<p>{text_block(question['prompt'])}</p>"
    content = f"{visual}{prompt_html}" if placement == "before_prompt" else f"{prompt_html}{visual}"
    return (
        '<article class="question">'
        f'<div class="question-number">{esc(question_number_display(question))}</div>'
        '<div class="question-body">'
        f'{score_html}{stimulus_html}{content}{options_html}{lines_html}'
        "</div></article>"
    )


def render_answer_detail(answer: dict[str, Any], number: Any, asset_base: Path | None) -> str:
    difficulty = answer.get("difficulty_label")
    meta_parts = [f"答案：{esc(answer.get('final_answer'))}"]
    if difficulty:
        meta_parts.append(f"難度：{esc(difficulty)}")
    anchor = answer.get("curriculum_anchor") or {}
    for key, label in (
        ("source_unit", "出處"),
        ("curriculum_code", "課綱"),
        ("objective", "目標"),
        ("content_summary", "內容"),
    ):
        if anchor.get(key):
            meta_parts.append(f"{label}：{esc(anchor[key])}")
    meta_html = "".join(f"<span>{part}</span>" for part in meta_parts)
    reasoning = answer.get("reasoning") or []
    reasoning_html = ""
    if reasoning:
        reasoning_html = "<h3>解題步驟</h3><ol>" + "".join(f"<li>{text_block(step)}</li>" for step in reasoning) + "</ol>"
    blocks = []
    for block in answer.get("explanation_blocks") or []:
        title = block.get("title") or BLOCK_LABELS.get(block.get("type"), block.get("type", "說明"))
        blocks.append(f"<h3>{esc(title)}</h3><p>{text_block(block.get('content'))}</p>")
    common_errors = answer.get("common_errors") or []
    errors_html = ""
    if common_errors:
        errors_html = "<h3>常見錯誤</h3><ul>" + "".join(f"<li>{text_block(item)}</li>" for item in common_errors) + "</ul>"
    visual_html = render_visual(answer.get("visual_asset"), asset_base)
    verification = verification_label(answer.get("verification_status"))
    verification_notes = answer.get("verification_notes")
    verification_html = f'<p class="solution-meta">驗證：{esc(verification)}'
    if verification_notes:
        verification_html += f"｜{text_block(verification_notes)}"
    verification_html += "</p>"
    return (
        f'<article class="solution-card"><h2>{answer_heading(number)}</h2>'
        f'<p class="solution-meta">{meta_html}</p>{reasoning_html}{visual_html}'
        f'{"".join(blocks)}{errors_html}{verification_html}</article>'
    )


def render_exam(exam: dict[str, Any], include_answers: bool = True, asset_base: Path | None = None) -> str:
    from validate_exam_pack_contract import is_complete_paper
    if is_complete_paper(exam):
        raise ValueError("The generic renderer cannot render a complete exam, including previews; use the validated subject renderer and exam_packs contract.")
    errors = validate_exam(exam)
    if errors:
        raise ValueError("；".join(errors))
    meta = exam["metadata"]
    instructions = "".join(f"<li>{text_block(item)}</li>" for item in exam["instructions"])
    sections_html = []
    questions_by_section: dict[str, list[dict[str, Any]]] = {section["id"]: [] for section in exam["sections"]}
    for question in exam["questions"]:
        questions_by_section[question["section_id"]].append(question)
    for section in exam["sections"]:
        notes = "".join(f"<p>{text_block(item)}</p>" for item in section.get("instructions", []))
        questions = "".join(render_question(question, asset_base) for question in questions_by_section[section["id"]])
        sections_html.append(
            f'<section class="section"><h2 class="section-title">{esc(section["title"])}</h2>'
            f'<div class="section-note">{notes}</div>{questions}</section>'
        )

    answers_html = ""
    answers = exam.get("answers", [])
    if include_answers and answers:
        rows = []
        details = []
        number_by_id = {question["id"]: answer_question_label(question) for question in exam["questions"]}
        for answer in answers:
            number = number_by_id.get(answer["question_id"], answer["question_id"])
            rows.append(
                f'<tr><td>{esc(number)}</td><td>{text_block(answer.get("final_answer"))}</td>'
                f'<td>{esc(answer.get("difficulty_label") or "—")}</td></tr>'
            )
            details.append(render_answer_detail(answer, number, asset_base))
        answers_html = (
            '<section class="answer-key"><h1>答案與詳解</h1><table class="answer-summary">'
            '<thead><tr><th>題號</th><th>答案</th><th>難度</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table><div class="solution-details">'
            f'{"".join(details)}</div></section>'
        )

    metadata_items = [
        ("考試", meta.get("exam")),
        ("科目", meta.get("subject")),
        ("時間", f'{meta["duration_minutes"]} 分鐘' if meta.get("duration_minutes") else "依題組需求"),
        ("滿分", meta.get("total_score") if meta.get("total_score") is not None else "未指定"),
    ]
    meta_html = "".join(f"<div><strong>{esc(label)}</strong><br>{esc(value)}</div>" for label, value in metadata_items)
    trace = (
        f'校準：{esc(meta.get("calibration_level"))} ｜ 課綱：{esc(meta.get("curriculum"))} ｜ '
        f'Blueprint：{esc(meta.get("blueprint_fingerprint"))}'
    )
    subtitle = f'<p class="exam-subtitle">{esc(meta.get("subtitle"))}</p>' if meta.get("subtitle") else ""
    return f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,">
<title>{esc(meta['title'])}</title><style>{STYLE}</style></head>
<body>
<header class="exam-header"><h1 class="exam-title">{esc(meta['title'])}</h1>{subtitle}</header>
<div class="meta-grid">{meta_html}</div>
<div class="candidate"><div>姓名：<span class="blank"></span></div><div>班級：<span class="blank"></span></div><div>座號：<span class="blank"></span></div></div>
<section class="instructions"><h2>作答說明</h2><ol>{instructions}</ol></section>
<div class="trace">{trace}</div>
{"".join(sections_html)}
{answers_html}
</body></html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="將 exam.json 轉成正式列印 HTML")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--student-only", action="store_true", help="不附答案頁")
    args = parser.parse_args(argv)
    try:
        exam = json.loads(args.input.read_text(encoding="utf-8-sig"))
        rendered = render_exam(exam, include_answers=not args.student_only, asset_base=args.input.resolve().parent)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    print(f"已輸出：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
