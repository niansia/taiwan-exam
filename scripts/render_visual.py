#!/usr/bin/env python3
"""Render exact exam visuals from a semantic visual-spec JSON file to SVG."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


WIDTH = 720
HEIGHT = 480
MARGIN = 64
INK = "#161616"
GRID = "#d2d2d2"
FILL = "#dedede"
SUBSCRIPT_CHARS = "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"
SUPERSCRIPT_CHARS = "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ"
SUBSCRIPT_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ", "0123456789+-=()aehijklmnoprstuvx")
SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ", "0123456789+-=()ni")


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def svg_text(value: Any) -> str:
    """Render presentation scripts as SVG tspans with controlled metrics."""
    rendered = esc(value)
    rendered = re.sub(
        f"([{re.escape(SUBSCRIPT_CHARS)}]+)",
        lambda match: f'<tspan baseline-shift="sub" font-size="70%">{match.group(1).translate(SUBSCRIPT_MAP)}</tspan>',
        rendered,
    )
    rendered = re.sub(
        f"([{re.escape(SUPERSCRIPT_CHARS)}]+)",
        lambda match: f'<tspan baseline-shift="super" font-size="70%">{match.group(1).translate(SUPERSCRIPT_MAP)}</tspan>',
        rendered,
    )
    return re.sub(
        r"([A-Za-z])(?=<tspan baseline-shift=)",
        r'<tspan font-style="italic">\1</tspan>',
        rendered,
    )


def number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} 必須是有限數值")
    return float(value)


def svg_document(body: str, title: str = "") -> str:
    title_node = f"<title>{esc(title)}</title>" if title else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img">{title_node}'
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#161616" stroke="none"/></marker></defs>'
        '<rect width="100%" height="100%" fill="white"/>'
        f'<g font-family="Times New Roman, PMingLiU, MingLiU, serif" fill="{INK}" '
        f'stroke="{INK}" stroke-width="2">{body}</g></svg>'
    )


def render_coordinate(data: dict[str, Any]) -> str:
    x_min = number(data.get("x_min"), "x_min")
    x_max = number(data.get("x_max"), "x_max")
    y_min = number(data.get("y_min"), "y_min")
    y_max = number(data.get("y_max"), "y_max")
    if x_min >= x_max or y_min >= y_max:
        raise ValueError("座標範圍上限必須大於下限")
    plot_w = WIDTH - 2 * MARGIN
    plot_h = HEIGHT - 2 * MARGIN

    def px(x: float) -> float:
        return MARGIN + (x - x_min) / (x_max - x_min) * plot_w

    def py(y: float) -> float:
        return HEIGHT - MARGIN - (y - y_min) / (y_max - y_min) * plot_h

    parts: list[str] = []
    x_tick = number(data.get("x_tick", 1), "x_tick")
    y_tick = number(data.get("y_tick", 1), "y_tick")
    if x_tick <= 0 or y_tick <= 0:
        raise ValueError("刻度間距必須大於 0")
    x = math.ceil(x_min / x_tick) * x_tick
    while x <= x_max + 1e-9:
        xp = px(x)
        parts.append(f'<line x1="{xp:.2f}" y1="{MARGIN}" x2="{xp:.2f}" y2="{HEIGHT-MARGIN}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{xp:.2f}" y="{HEIGHT-MARGIN+23}" text-anchor="middle" stroke="none" font-size="16">{esc(f"{x:g}")}</text>')
        x += x_tick
    y = math.ceil(y_min / y_tick) * y_tick
    while y <= y_max + 1e-9:
        yp = py(y)
        parts.append(f'<line x1="{MARGIN}" y1="{yp:.2f}" x2="{WIDTH-MARGIN}" y2="{yp:.2f}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{MARGIN-12}" y="{yp+5:.2f}" text-anchor="end" stroke="none" font-size="16">{svg_text(f"{y:g}")}</text>')
        y += y_tick
    axis_x = py(0) if y_min <= 0 <= y_max else HEIGHT - MARGIN
    axis_y = px(0) if x_min <= 0 <= x_max else MARGIN
    parts.extend([
        f'<line x1="{MARGIN}" y1="{axis_x:.2f}" x2="{WIDTH-MARGIN}" y2="{axis_x:.2f}"/>',
        f'<line x1="{axis_y:.2f}" y1="{MARGIN}" x2="{axis_y:.2f}" y2="{HEIGHT-MARGIN}"/>',
        f'<text x="{WIDTH-MARGIN+20}" y="{axis_x+5:.2f}" stroke="none" font-size="18">{svg_text(data.get("x_label", "x"))}</text>',
        f'<text x="{axis_y+8:.2f}" y="{MARGIN-18}" stroke="none" font-size="18">{svg_text(data.get("y_label", "y"))}</text>',
    ])
    for series_index, series in enumerate(data.get("series") or []):
        points = series.get("points") or []
        if not points:
            continue
        parsed = [(number(p[0], "point.x"), number(p[1], "point.y")) for p in points]
        if any(not (x_min <= x <= x_max and y_min <= y <= y_max) for x, y in parsed):
            raise ValueError("資料點超出座標範圍")
        if series.get("connect", True) and len(parsed) > 1:
            coords = " ".join(f"{px(x):.2f},{py(y):.2f}" for x, y in parsed)
            dash = ' stroke-dasharray="9 6"' if series_index % 2 else ""
            parts.append(f'<polyline points="{coords}" fill="none" stroke-width="3"{dash}/>')
        for point_index, (x, y) in enumerate(parsed):
            parts.append(f'<circle cx="{px(x):.2f}" cy="{py(y):.2f}" r="5" fill="white"/>')
            labels = series.get("point_labels") or []
            if point_index < len(labels) and labels[point_index]:
                parts.append(f'<text x="{px(x)+9:.2f}" y="{py(y)-9:.2f}" stroke="none" font-size="16">{svg_text(labels[point_index])}</text>')
    return svg_document("".join(parts), str(data.get("title") or "座標圖"))


def render_chart(data: dict[str, Any]) -> str:
    chart_type = data.get("chart_type", "bar")
    categories = [str(item) for item in (data.get("categories") or [])]
    series = data.get("series") or []
    if not categories or not series:
        raise ValueError("統計圖需要 categories 與 series")
    parsed: list[tuple[str, list[float]]] = []
    for item in series:
        values = [number(value, "series.values") for value in (item.get("values") or [])]
        if len(values) != len(categories):
            raise ValueError("每個數列的 values 數量必須等於 categories")
        parsed.append((str(item.get("label") or ""), values))
    all_values = [value for _, values in parsed for value in values]
    y_min = number(data.get("y_min", min(0, min(all_values))), "y_min")
    y_max = number(data.get("y_max", max(all_values)), "y_max")
    if y_min >= y_max:
        raise ValueError("y_max 必須大於 y_min")
    plot_w = WIDTH - 2 * MARGIN
    plot_h = HEIGHT - 2 * MARGIN

    def py(value: float) -> float:
        return HEIGHT - MARGIN - (value - y_min) / (y_max - y_min) * plot_h

    parts: list[str] = []
    for step in range(6):
        value = y_min + (y_max - y_min) * step / 5
        yp = py(value)
        parts.append(f'<line x1="{MARGIN}" y1="{yp:.2f}" x2="{WIDTH-MARGIN}" y2="{yp:.2f}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{MARGIN-10}" y="{yp+5:.2f}" text-anchor="end" stroke="none" font-size="15">{svg_text(f"{value:g}")}</text>')
    parts.append(f'<line x1="{MARGIN}" y1="{HEIGHT-MARGIN}" x2="{WIDTH-MARGIN}" y2="{HEIGHT-MARGIN}"/>')
    group_w = plot_w / len(categories)
    for index, category in enumerate(categories):
        cx = MARGIN + group_w * (index + 0.5)
        parts.append(f'<text x="{cx:.2f}" y="{HEIGHT-MARGIN+24}" text-anchor="middle" stroke="none" font-size="16">{svg_text(category)}</text>')
    if chart_type == "bar":
        bar_w = group_w * 0.68 / len(parsed)
        zero_y = py(max(y_min, min(0, y_max)))
        for series_index, (_, values) in enumerate(parsed):
            for index, value in enumerate(values):
                x = MARGIN + group_w * index + group_w * 0.16 + bar_w * series_index
                top = min(py(value), zero_y)
                height = abs(py(value) - zero_y)
                pattern = FILL if series_index % 2 == 0 else "white"
                parts.append(f'<rect x="{x:.2f}" y="{top:.2f}" width="{bar_w:.2f}" height="{height:.2f}" fill="{pattern}"/>')
                if data.get("show_values"):
                    parts.append(f'<text x="{x + bar_w / 2:.2f}" y="{top - 7:.2f}" text-anchor="middle" stroke="none" font-size="14">{svg_text(f"{value:g}")}</text>')
    elif chart_type == "line":
        for series_index, (_, values) in enumerate(parsed):
            coords = " ".join(f"{MARGIN + group_w * (i + 0.5):.2f},{py(v):.2f}" for i, v in enumerate(values))
            dash = ' stroke-dasharray="9 6"' if series_index % 2 else ""
            parts.append(f'<polyline points="{coords}" fill="none" stroke-width="3"{dash}/>')
            for i, value in enumerate(values):
                parts.append(f'<circle cx="{MARGIN + group_w * (i + 0.5):.2f}" cy="{py(value):.2f}" r="5" fill="white"/>')
                if data.get("show_values"):
                    parts.append(f'<text x="{MARGIN + group_w * (i + 0.5) + 8:.2f}" y="{py(value) - 8:.2f}" stroke="none" font-size="14">{svg_text(f"{value:g}")}</text>')
    else:
        raise ValueError("chart_type 僅支援 bar 或 line")
    legend_y = 27
    for index, (label, _) in enumerate(parsed):
        if label:
            x = MARGIN + index * 150
            parts.append(f'<line x1="{x}" y1="{legend_y}" x2="{x+25}" y2="{legend_y}" stroke-width="4"/>')
            parts.append(f'<text x="{x+33}" y="{legend_y+5}" stroke="none" font-size="15">{svg_text(label)}</text>')
    return svg_document("".join(parts), str(data.get("title") or "統計圖"))


def render_geometry(data: dict[str, Any]) -> str:
    raw_points = data.get("points") or []
    if not raw_points:
        raise ValueError("幾何圖需要 points")
    points: dict[str, tuple[float, float]] = {}
    labels: dict[str, str] = {}
    point_shapes: dict[str, str] = {}
    for item in raw_points:
        point_id = str(item.get("id") or "")
        if not point_id or point_id in points:
            raise ValueError("每個幾何點需要唯一 id")
        points[point_id] = (number(item.get("x"), f"{point_id}.x"), number(item.get("y"), f"{point_id}.y"))
        labels[point_id] = str(item.get("label", point_id))
        point_shapes[point_id] = str(item.get("shape") or "dot")
    xs = [p[0] for p in points.values()]
    ys = [p[1] for p in points.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_min == x_max or y_min == y_max:
        raise ValueError("幾何圖的點不可全部共用同一 x 或 y")
    pad_x = (x_max - x_min) * 0.18
    pad_y = (y_max - y_min) * 0.18
    x_min, x_max = x_min - pad_x, x_max + pad_x
    y_min, y_max = y_min - pad_y, y_max + pad_y

    def px(x: float) -> float:
        return MARGIN + (x - x_min) / (x_max - x_min) * (WIDTH - 2 * MARGIN)

    def py(y: float) -> float:
        return HEIGHT - MARGIN - (y - y_min) / (y_max - y_min) * (HEIGHT - 2 * MARGIN)

    parts: list[str] = []
    for index, segment in enumerate(data.get("segments") or []):
        if isinstance(segment, dict):
            start = str(segment.get("from") or "")
            end = str(segment.get("to") or "")
            label = str(segment.get("label") or "")
            directed = bool(segment.get("directed"))
            dashed = bool(segment.get("dashed"))
            label_dx = number(segment.get("label_dx", 0), f"segment[{index}].label_dx")
            label_dy = number(segment.get("label_dy", 0), f"segment[{index}].label_dy")
        else:
            if not isinstance(segment, list) or len(segment) != 2:
                raise ValueError("segment 必須引用兩個已存在的 point id")
            start, end = str(segment[0]), str(segment[1])
            label, directed, dashed, label_dx, label_dy = "", False, False, 0.0, 0.0
        if start not in points or end not in points:
            raise ValueError("segment 必須引用兩個已存在的 point id")
        a, b = points[start], points[end]
        x1, y1, x2, y2 = px(a[0]), py(a[1]), px(b[0]), py(b[1])
        dx, dy = x2 - x1, y2 - y1
        distance = math.hypot(dx, dy)
        if distance and point_shapes[start] == "circle":
            x1 += 24 * dx / distance
            y1 += 24 * dy / distance
        if distance and point_shapes[end] == "circle":
            x2 -= 27 * dx / distance
            y2 -= 27 * dy / distance
        marker = ' marker-end="url(#arrow)"' if directed else ""
        dash = ' stroke-dasharray="8 6"' if dashed else ""
        parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke-width="3"{marker}{dash}/>')
        if label:
            mid_x = (px(a[0]) + px(b[0])) / 2 + label_dx
            mid_y = (py(a[1]) + py(b[1])) / 2 + label_dy
            parts.append(f'<rect x="{mid_x-18:.2f}" y="{mid_y-14:.2f}" width="36" height="20" fill="white" stroke="none"/>')
            parts.append(f'<text x="{mid_x:.2f}" y="{mid_y+2:.2f}" text-anchor="middle" stroke="none" font-size="16">{svg_text(label)}</text>')
    for point_id, (x, y) in points.items():
        if point_shapes[point_id] == "circle":
            parts.append(f'<circle cx="{px(x):.2f}" cy="{py(y):.2f}" r="22" fill="white" stroke-width="3"/>')
            if labels[point_id]:
                parts.append(f'<text x="{px(x):.2f}" y="{py(y)+6:.2f}" text-anchor="middle" stroke="none" font-size="18">{svg_text(labels[point_id])}</text>')
        else:
            parts.append(f'<circle cx="{px(x):.2f}" cy="{py(y):.2f}" r="4" fill="{INK}"/>')
            if labels[point_id]:
                parts.append(f'<text x="{px(x)+9:.2f}" y="{py(y)-9:.2f}" stroke="none" font-size="18">{svg_text(labels[point_id])}</text>')
    for index, annotation in enumerate(data.get("annotations") or []):
        x = number(annotation.get("x"), f"annotation[{index}].x")
        y = number(annotation.get("y"), f"annotation[{index}].y")
        if not (x_min <= x <= x_max and y_min <= y <= y_max):
            raise ValueError("annotation 超出幾何圖範圍")
        parts.append(f'<text x="{px(x):.2f}" y="{py(y):.2f}" text-anchor="middle" stroke="none" font-size="18">{svg_text(annotation.get("text") or "")}</text>')
    return svg_document("".join(parts), str(data.get("title") or "幾何圖"))


def render(spec: dict[str, Any]) -> str:
    if spec.get("generation_mode") not in {"deterministic_svg", "chart_renderer"}:
        raise ValueError("此工具只處理 deterministic_svg 或 chart_renderer")
    data = spec.get("semantic_data")
    if not isinstance(data, dict):
        raise ValueError("visual spec 缺少 semantic_data")
    kind = spec.get("kind")
    if kind == "coordinate_graph":
        return render_coordinate(data)
    if kind == "statistical_chart":
        return render_chart(data)
    if kind == "geometry_diagram":
        return render_geometry(data)
    raise ValueError(f"目前不支援的精確 SVG 類型：{kind}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="從 visual-spec JSON 產生可驗算 SVG")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        spec = json.loads(args.input.read_text(encoding="utf-8-sig"))
        output = render(spec)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    print(f"已輸出：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
