#!/usr/bin/env python3
"""Build or parameter-fill the reusable 115 GSAT layout-only PDF assets."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from gsat_115_templates import PACK_ROOT, SUBJECT_ORDER, SUBJECTS, cover_markup, document, formula_markup, inner_markup
from render_pdf import find_browser
from safe_rendering import browser_flags, prepare_html


COMPONENTS = ("cover", "inner-odd", "inner-even", "formula", "packet")


def _packet_markup(subject: str, *, year: str = "", exam_name: str = "", current_page: str = "", total_pages: str = "") -> str:
    parts = [cover_markup(subject, year=year, exam_name=exam_name)]
    parts.append(inner_markup(subject, parity="odd", year=year, exam_name=exam_name, current_page=current_page, total_pages=total_pages))
    parts.append(inner_markup(subject, parity="even", year=year, exam_name=exam_name, current_page=current_page, total_pages=total_pages))
    if subject in {"數學A", "數學B"}:
        parts.append(inner_markup(subject, parity="odd", year=year, exam_name=exam_name, current_page=current_page,
                                  total_pages=total_pages, body=formula_markup(subject)))
    return ''.join(parts)


def component_markup(subject: str, component: str, *, year: str = "", exam_name: str = "", current_page: str = "", total_pages: str = "") -> str:
    if component == "cover":
        return cover_markup(subject, year=year, exam_name=exam_name)
    if component == "inner-odd":
        return inner_markup(subject, parity="odd", year=year, exam_name=exam_name, current_page=current_page, total_pages=total_pages)
    if component == "inner-even":
        return inner_markup(subject, parity="even", year=year, exam_name=exam_name, current_page=current_page, total_pages=total_pages)
    if component == "formula":
        return inner_markup(subject, parity="odd", year=year, exam_name=exam_name, current_page=current_page,
                            total_pages=total_pages, body=formula_markup(subject))
    if component == "packet":
        return _packet_markup(subject, year=year, exam_name=exam_name, current_page=current_page, total_pages=total_pages)
    raise ValueError(f"未知模板元件：{component}")


def _print_pdf(browser: Path, markup: str, output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gsat-115-template-") as temp:
        work = Path(temp)
        html_path = work / "template.html"
        runtime = work / "runtime"
        runtime.mkdir()
        html_path.write_text(prepare_html(document(markup, title=output.stem)), encoding="utf-8")
        completed = subprocess.run(
            [str(browser), *browser_flags(runtime), "--no-pdf-header-footer",
             f"--print-to-pdf={output}", html_path.as_uri()],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90,
        )
        if not output.is_file() or output.stat().st_size < 1000:
            raise RuntimeError(completed.stderr or completed.stdout or "PDF輸出失敗")


def _extract_page(source: Path, page_index: int, output: Path) -> None:
    import pymupdf
    doc = pymupdf.open(source)
    if page_index >= len(doc):
        doc.close()
        raise ValueError(f"模板封包缺少第{page_index + 1}頁")
    single = pymupdf.open()
    single.insert_pdf(doc, from_page=page_index, to_page=page_index)
    output.parent.mkdir(parents=True, exist_ok=True)
    single.save(output, garbage=4, deflate=True)
    single.close()
    doc.close()


def _validate_packet(path: Path, subject: str) -> None:
    """Fail closed on stale fields, wrong formula variant, or shifted cover frame."""
    import json
    import pymupdf

    config = SUBJECTS[subject]
    doc = pymupdf.open(path)
    expected_pages = 4 if subject in {"數學A", "數學B"} else 3
    if len(doc) != expected_pages:
        doc.close()
        raise ValueError(f"{subject}模板封包應為{expected_pages}頁，實際為{len(doc)}頁")
    for index, page in enumerate(doc):
        if abs(page.rect.width - 595.28) > 1 or abs(page.rect.height - 841.89) > 1:
            doc.close()
            raise ValueError(f"{subject}模板第{index + 1}頁不是A4")
    extracted = ''.join(page.get_text() for page in doc)
    if "115學年度" in extracted or "115年學測" in extracted:
        doc.close()
        raise ValueError(f"{subject}空白模板殘留參考年度")
    if subject == "數學A" and "和角公式" not in extracted:
        doc.close()
        raise ValueError("數學A模板缺少和角公式")
    if subject == "數學B" and "和角公式" in extracted:
        doc.close()
        raise ValueError("數學B模板誤用了數學A公式版本")
    if subject in {"數學A", "數學B"}:
        # Browser layout can keep all characters while aligning the surrounding
        # prose to the numerator instead of the fraction's visual centre.  Test
        # the actual PDF glyph boxes so that regression is build-blocking.
        lines = [line for block in doc[0].get_text("dict")["blocks"] for line in block.get("lines", [])]
        anchor = next((line for line in lines if "而依題意計算出來的答案是" in ''.join(span["text"] for span in line["spans"])), None)
        if anchor is None:
            doc.close()
            raise ValueError(f"{subject}封面找不到3/8範例的文字錨點")
        ax0, ay0, ax1, ay1 = anchor["bbox"]
        nearby = [line for line in lines
                  if ''.join(span["text"] for span in line["spans"]).strip() in {"3", "8"}
                  and line["bbox"][0] >= ax1 and ay0 - 15 <= line["bbox"][1] <= ay1 + 20]
        numerator = next((line for line in nearby if ''.join(span["text"] for span in line["spans"]).strip() == "3"), None)
        denominator = next((line for line in nearby if ''.join(span["text"] for span in line["spans"]).strip() == "8"), None)
        if numerator is None or denominator is None:
            doc.close()
            raise ValueError(f"{subject}封面找不到完整3/8行內分數")
        prose_center = (ay0 + ay1) / 2
        fraction_center = (min(numerator["bbox"][1], denominator["bbox"][1]) +
                           max(numerator["bbox"][3], denominator["bbox"][3])) / 2
        if abs(prose_center - fraction_center) > 2.5:
            doc.close()
            raise ValueError(f"{subject}封面3/8未與前後文字垂直置中")

    profile_path = (Path(__file__).resolve().parents[1] / "exam_packs" / "學測" / "subjects" /
                    config["folder"] / "blueprints" / "layout-profiles" / f'{config["profile"]}.json')
    profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    expected = tuple(float(value) for value in profile["page_geometry"]["cover_frame_pt"])
    frames = [drawing["rect"] for drawing in doc[0].get_drawings()
              if drawing.get("rect") and 300 < drawing["rect"].width < 550 and drawing["rect"].height > 200]
    if not frames:
        doc.close()
        raise ValueError(f"{subject}模板找不到作答注意事項外框")
    actual = min(frames, key=lambda rect: sum(abs(a - b) for a, b in zip((rect.x0, rect.y0, rect.x1, rect.y1), expected)))
    error = max(abs(a - b) for a, b in zip((actual.x0, actual.y0, actual.x1, actual.y1), expected))
    doc.close()
    if error > 4:
        raise ValueError(f"{subject}封面外框偏離115量測位置{error:.1f}pt")


def build_all(browser: Path, output_root: Path = PACK_ROOT / "assets") -> list[Path]:
    """Use one browser print per subject, then split deterministic components."""
    outputs: list[Path] = []
    for subject in SUBJECT_ORDER:
        folder = output_root / SUBJECTS[subject]["slug"]
        packet = folder / "blank-template.pdf"
        _print_pdf(browser, _packet_markup(subject), packet)
        _validate_packet(packet, subject)
        outputs.append(packet)
        for index, name in enumerate(("cover-blank.pdf", "inner-odd-blank.pdf", "inner-even-blank.pdf")):
            path = folder / name
            _extract_page(packet, index, path)
            outputs.append(path)
        if subject in {"數學A", "數學B"}:
            path = folder / "formula-blank.pdf"
            _extract_page(packet, 3, path)
            outputs.append(path)
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="產生115學測版型資產（不產生題目）")
    parser.add_argument("--build-all", action="store_true", help="建立七科挖空版模板資產")
    parser.add_argument("--subject", choices=SUBJECT_ORDER)
    parser.add_argument("--component", choices=COMPONENTS, default="packet")
    parser.add_argument("--year", default="")
    parser.add_argument("--exam-name", default="")
    parser.add_argument("--current-page", default="")
    parser.add_argument("--total-pages", default="")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--browser", type=Path)
    args = parser.parse_args(argv)
    try:
        browser = find_browser(args.browser)
        if args.build_all:
            outputs = build_all(browser)
            print(f"已建立{len(outputs)}個115學測版型PDF資產：{PACK_ROOT / 'assets'}")
            return 0
        if not args.subject or not args.output:
            raise ValueError("單一輸出須同時指定 --subject 與 --output")
        markup = component_markup(args.subject, args.component, year=args.year, exam_name=args.exam_name,
                                  current_page=args.current_page, total_pages=args.total_pages)
        _print_pdf(browser, markup, args.output)
        print(f"已輸出115學測版型PDF：{args.output}")
        return 0
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
