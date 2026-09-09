#!/usr/bin/env python3
"""Run current-form Math A/B semantic, typography, and page-image QA."""

from __future__ import annotations

import argparse
import json
import logging
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import pdfplumber
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


PRESENTATION_SCRIPTS = set("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ")


def compact(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def page_text_counts(path: Path) -> list[int]:
    return [len(compact(page.extract_text() or "")) for page in PdfReader(str(path)).pages]


def font_profile(path: Path) -> list[dict[str, Any]]:
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    counts: Counter[tuple[str, float]] = Counter()
    with pdfplumber.open(path) as document:
        for page in document.pages:
            for char in page.chars:
                counts[(str(char.get("fontname") or ""), round(float(char.get("size") or 0), 2))] += 1
    return [
        {"font": font, "size_pt": size, "character_count": count}
        for (font, size), count in counts.most_common(24)
    ]


def render_pages(path: Path, output_dir: Path) -> tuple[Path, list[Path]]:
    document = pdfium.PdfDocument(str(path))
    page_paths: list[Path] = []
    thumbs: list[Image.Image] = []
    for index in range(len(document)):
        image = document[index].render(scale=1.7).to_pil().convert("RGB")
        page_path = output_dir / f"page-{index + 1}.png"
        image.save(page_path)
        page_paths.append(page_path)
        thumb_width = 390
        thumb_height = round(image.height * thumb_width / image.width)
        thumb = image.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (thumb_width, thumb_height + 26), "white")
        canvas.paste(thumb, (0, 26))
        ImageDraw.Draw(canvas).text((8, 6), f"page {index + 1}", fill="black", font=ImageFont.load_default())
        thumbs.append(canvas)
    columns = 4
    rows = (len(thumbs) + columns - 1) // columns
    contact = Image.new("RGB", (columns * thumbs[0].width, rows * thumbs[0].height), "#d0d0d0")
    for index, image in enumerate(thumbs):
        contact.paste(image, ((index % columns) * image.width, (index // columns) * image.height))
    contact_path = output_dir / "contact-sheet.png"
    contact.save(contact_path)
    return contact_path, page_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exam_json", type=Path)
    parser.add_argument("student_pdf", type=Path)
    parser.add_argument("official_reference", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    exam = json.loads(args.exam_json.read_text(encoding="utf-8-sig"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    generated_counts = page_text_counts(args.student_pdf)
    official_counts = page_text_counts(args.official_reference)
    generated_content = generated_counts[1:]
    official_content = official_counts[1:]
    extracted = "".join(page.extract_text() or "" for page in PdfReader(str(args.student_pdf)).pages)
    content_extracted = compact("".join(page.extract_text() or "" for page in PdfReader(str(args.student_pdf)).pages[1:]))
    profile = font_profile(args.student_pdf)
    font_names = {item["font"] for item in profile}
    selected = [item for item in exam["questions"] if item.get("options")]
    mixed_section_ids = {
        section.get("id")
        for section in exam.get("sections") or []
        if section.get("id") == "mixed" or "混合" in str(section.get("title") or "")
    }
    lengths = [
        len(compact(str(item.get("group_stimulus") or "") + str(item.get("prompt") or "") + "".join(str(option["text"]) for option in item["options"])))
        for item in selected
    ]
    contact_path, page_paths = render_pages(args.student_pdf, args.output_dir)
    official_image_dir = args.output_dir / "official-reference"
    official_image_dir.mkdir(parents=True, exist_ok=True)
    official_contact_path, _ = render_pages(args.official_reference, official_image_dir)
    checks = {
        "page_count_8": len(generated_counts) == int(exam["metadata"]["target_page_count"]) == 8,
        "question_count_20": len(exam["questions"]) == 20,
        "score_100": sum(float(item["score"]) for item in exam["questions"]) == 100,
        "selected_median_at_least_160": statistics.median(lengths) >= 160,
        "no_presentation_script_glyphs_in_pdf_text": not any(char in PRESENTATION_SCRIPTS for char in extracted),
        "pmingliu_present": any("PMingLiU" in name for name in font_names),
        "times_new_roman_present": any("TimesNewRoman" in name for name in font_names),
        "dfkai_present": any("DFKai" in name for name in font_names),
        "no_sparse_content_page": min(generated_content) >= 120,
        "section_headings_not_repeated": all(
            content_extracted.count(token) == 1
            for token in ("第壹部分", "二、多選題", "三、選填題", "第貳部分")
        ),
        "no_per_item_parenthesized_score_labels": not re.search(
            r"[（(]\s*5\s*分\s*[）)]", extracted
        ),
        "no_workbook_answer_lines_in_mixed_section": all(
            int(item.get("answer_space_lines") or 0) == 0
            for item in exam["questions"]
            if item.get("section_id") in mixed_section_ids
        ),
    }
    report = {
        "status": "pass-automated; visual inspection still required" if all(checks.values()) else "fail",
        "student_pdf": str(args.student_pdf.resolve()),
        "official_reference": str(args.official_reference.resolve()),
        "checks": checks,
        "selected_compact_character_median": statistics.median(lengths),
        "generated_page_text_counts": generated_counts,
        "official_page_text_counts": official_counts,
        "content_density_ratio": round(statistics.mean(generated_content) / statistics.mean(official_content), 3),
        "dominant_fonts": profile,
        "contact_sheet": str(contact_path.resolve()),
        "official_contact_sheet": str(official_contact_path.resolve()),
        "page_images": [str(path.resolve()) for path in page_paths],
    }
    report_path = args.output_dir / "qa-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
