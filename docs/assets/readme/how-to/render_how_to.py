"""Record how-to-claude.html frame by frame and encode how-to-claude.gif for the README.

    python docs/assets/readme/how-to/render_how_to.py [--fps 12] [--width 960]

Needs Playwright with Chrome and ffmpeg on PATH. The page's timeline is seekable (window.seek), so every frame is
rendered exactly instead of being screen-recorded; ffmpeg then builds one palette for the whole clip.
"""
from __future__ import annotations

import argparse
import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "how-to-claude.html"
OUT = HERE / "how-to-claude.gif"


async def record(frames_dir: Path, fps: int) -> int:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")
        page = await browser.new_page(viewport={"width": 1000, "height": 600}, device_scale_factor=1)
        await page.goto(PAGE.as_uri() + "?still")
        await page.evaluate("document.fonts.ready")
        await page.wait_for_function("typeof window.seek === 'function'")
        await page.wait_for_timeout(600)  # images and the measured layout
        duration = await page.evaluate("window.DURATION")
        stage = page.locator("#stage")
        n = int(duration * fps)
        for i in range(n):
            await page.evaluate(f"window.seek({i / fps})")
            await stage.screenshot(path=str(frames_dir / f"f{i:04d}.png"))
        await browser.close()
    return n


def encode(frames_dir: Path, fps: int, width: int) -> None:
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    scale = f"scale={width}:-1:flags=lanczos"
    src = ["-framerate", str(fps), "-i", str(frames_dir / "f%04d.png")]
    palette = frames_dir / "palette.png"
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", *src, "-vf", f"{scale},palettegen=max_colors=192:stats_mode=diff", str(palette)], check=True)
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", *src, "-i", str(palette), "-lavfi",
                    f"{scale}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle", "-loop", "0", str(OUT)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--width", type=int, default=960)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        n = asyncio.run(record(Path(tmp), a.fps))
        encode(Path(tmp), a.fps, a.width)
    print(f"{n} frames -> {OUT.name} ({OUT.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
