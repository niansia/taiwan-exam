from __future__ import annotations

import importlib.util
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def make_two_page_pdf(path: Path, text: str) -> None:
    doc = pymupdf.open()
    doc.new_page()
    page = doc.new_page()
    page.insert_text((72, 700), text, fontsize=8)
    doc.save(path)


def test_current_form_volume_rejects_padding_without_text():
    module = load_script("validate_current_form_density.py")
    metrics = module.content_volume_metrics(
        [{"compact_chars": 100}, {"compact_chars": 500}],
        [{"aggregate": {"compact_chars": 1000}}],
    )
    assert metrics["content_volume_ratio"] == 0.6
    assert metrics["minimum_compact_chars"] == 800
    assert metrics["content_volume_pass"] is False


def test_reference_density_rejects_short_text_even_when_bottom_matches(tmp_path: Path):
    module = load_script("validate_reference_page_density.py")
    candidate = tmp_path / "candidate.pdf"
    reference = tmp_path / "reference.pdf"
    make_two_page_pdf(candidate, "A" * 40)
    make_two_page_pdf(reference, "A" * 100)
    report = module.validate(candidate, reference, "數學B", tolerance=0.12)
    assert report["content_volume_pass"] is False
    assert any(error["code"] == "insufficient_substantive_text_volume" for error in report["errors"])
    assert report["status"] == "fail"
