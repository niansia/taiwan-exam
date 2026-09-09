#!/usr/bin/env python3
"""Build labeled contact sheets from page PNGs rendered by pdftoppm."""

from __future__ import annotations

import argparse
import math
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw


PAGE_SUFFIX = re.compile(r"-\d+$")


def build(input_dir: Path, output_dir: Path, columns: int, thumb_width: int) -> list[Path]:
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(input_dir.glob("*.png")):
        groups[PAGE_SUFFIX.sub("", path.stem)].append(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for stem, paths in sorted(groups.items()):
        tiles: list[Image.Image] = []
        for path in paths:
            with Image.open(path) as source:
                page = source.convert("RGB")
            height = round(page.height * thumb_width / page.width)
            page = page.resize((thumb_width, height), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (thumb_width + 20, height + 38), "white")
            tile.paste(page, (10, 28))
            ImageDraw.Draw(tile).text((10, 7), path.stem, fill="black")
            tiles.append(tile)
        if not tiles:
            continue
        cell_width = max(tile.width for tile in tiles)
        cell_height = max(tile.height for tile in tiles)
        rows = math.ceil(len(tiles) / columns)
        sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), (225, 225, 225))
        for index, tile in enumerate(tiles):
            sheet.paste(tile, ((index % columns) * cell_width, (index // columns) * cell_height))
        target = output_dir / f"{stem}-contact.jpg"
        sheet.save(target, quality=88, optimize=True)
        outputs.append(target)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--thumb-width", type=int, default=360)
    args = parser.parse_args()
    if args.columns < 1 or args.thumb_width < 100:
        parser.error("--columns must be >= 1 and --thumb-width must be >= 100")
    outputs = build(args.input_dir.resolve(), args.output_dir.resolve(), args.columns, args.thumb_width)
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
