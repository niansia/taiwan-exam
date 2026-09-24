#!/usr/bin/env python3
"""Build Taiwan Exam's school-story title identity and 1280x640 sharing PNG.

Requires fontTools and PyMuPDF. Letterforms are outlined from local fonts.
Outputs are self-contained SVGs without external font or network dependencies.
"""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets/readme"
INK = "#392F46"
PAPER = "#FFFCF8"
DARK = "#17131E"
ROSE = "#CC7893"


def lettering(value, font_path, size, x, y, color=INK, tracking=0, accents=None,
              vertical_scales=None):
    font = TTFont(font_path, fontNumber=0)
    glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    cursor, paths = 0, []
    for char in value:
        name = cmap.get(ord(char))
        if name is None:
            raise ValueError(f"Font missing character: {char}")
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        if pen.getCommands():
            vertical_scale = (vertical_scales or {}).get(char, 1)
            paths.append(f'<path fill="{(accents or {}).get(char, color)}" '
                         f'transform="translate({cursor:.3f} 0) scale(1 {vertical_scale})" '
                         f'd="{pen.getCommands()}"/>')
        cursor += glyphs[name].width + tracking / scale
    font.close()
    return (f'<g aria-label="{escape(value, quote=True)}" fill="{color}" '
            f'transform="translate({x} {y}) scale({scale:.6f} {-scale:.6f})">'
            + "".join(paths) + "</g>")


def title_logo(latin_font, caption_font, dark=False):
    """Interlocked title composition, with a rose rising stroke crossing the x."""
    ink = "#EEE7F1" if dark else INK
    accent = "#E6A1B8" if dark else ROSE
    # Rounded, soft-serif shapes keep the accepted title layout. Optical cap
    # scaling preserves the tall T/E rhythm without crowding the small letters.
    result = lettering("Taiwan", latin_font, 119, 238, 151, ink, 2,
                       {"i": accent}, {"T": 1.22})
    result += lettering("Exam", latin_font, 257, 78, 371, ink, 2,
                        vertical_scales={"E": 1.11})
    # Original tapered answer stroke: completes the ascending gesture of x.
    result += f'''<path fill="{accent}" d="M277 381 C350 287 425 234 521 200 C650 155 808 138 864 169 C911 195 883 225 860 232 C884 211 889 189 859 177 C798 147 658 171 534 214 C431 249 362 308 277 381Z"/>
      <circle cx="368" cy="218" r="18" fill="none" stroke="{accent}" stroke-width="2.5"/>
      <path d="M359 219L366 226L384 205" fill="none" stroke="{accent}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'''
    result += lettering("大型考試自動化命題", caption_font, 28, 295, 432, ink, 7)
    result += f'<path d="M224 422H264M634 422H674" stroke="{accent}" stroke-width="2" stroke-linecap="round"/>'
    return result


def svg(width, height, title, body, description):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
            f'<title id="title">{escape(title)}</title>\n<desc id="desc">{escape(description)}</desc>\n'
            + body + "\n</svg>\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latin-font", type=Path, default=Path("C:/Windows/Fonts/COOPBL.TTF"))
    parser.add_argument("--caption-font", type=Path, default=Path("C:/Windows/Fonts/mingliu.ttc"))
    parser.add_argument("--cjk-font", type=Path, default=Path("C:/Windows/Fonts/msjhbd.ttc"))
    args = parser.parse_args()
    ASSETS.mkdir(parents=True, exist_ok=True)
    cjk = lambda t, s, x, y, c=INK: lettering(t, args.cjk_font, s, x, y, c)
    description = "日系輕小說與校園番片名式 Taiwan Exam 字標，圓潤軟襯線字形、上下交錯排版、霧玫瑰色答題筆畫與繁體中文『大型考試自動化命題』。"
    for theme in ["light", "dark"]:
        body = title_logo(args.latin_font, args.caption_font, dark=theme == "dark")
        (ASSETS / f"wordmark-{theme}.svg").write_text(svg(920, 470, "Taiwan Exam", body,
            description), encoding="utf-8", newline="\n")

    body = f'<rect width="1280" height="640" fill="{PAPER}"/>'
    body += '<g transform="translate(-8 80) scale(.89)">' + title_logo(args.latin_font, args.caption_font) + '</g>'
    body += cjk("你的下一份模擬考，", 30, 870, 262)
    body += cjk("讓 AI 出題。", 40, 870, 327)
    body += cjk("原創命題・解題驗算", 22, 874, 397, "#706278")
    body += cjk("套用大考正式版面", 22, 874, 433, "#706278")
    body += '<path d="M78 540H1202" stroke="#E6D5DF" stroke-width="1.5"/>'
    body += cjk("學測七科", 22, 81, 590, "#97566D")
    body += cjk("題目 PDF ＋ 答案詳解 PDF", 22, 865, 590)
    share = ASSETS / "social-preview.svg"
    share.write_text(svg(1280, 640, "Taiwan Exam：你的下一份模擬考，讓 AI 出題。", body,
        description), encoding="utf-8", newline="\n")
    import pymupdf
    with pymupdf.open(share) as document:
        document[0].get_pixmap(alpha=False).save(ASSETS / "social-preview.png")
    print("Built school-story title identity, light/dark SVGs, and 1280x640 social preview.")


if __name__ == "__main__":
    main()
