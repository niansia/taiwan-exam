import hashlib
import json
from pathlib import Path
import sys

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_template_resource_pdf as resource
import compose_hosted_pdf as compositor
import fetch_hosted_template_assets as fetcher
import inspect_hosted_pdf as inspector


@pytest.fixture(scope="module")
def carrier(tmp_path_factory):
    path = tmp_path_factory.mktemp("resources") / "templates.pdf"
    resource.build(path)
    return path


def test_carrier_is_deterministic_data_only_and_all_30_bytes_match(carrier, tmp_path):
    other = tmp_path / "other.pdf"
    resource.build(other)
    assert other.read_bytes() == carrier.read_bytes()
    assert (ROOT / "web/taiwan-exam-template-resources.pdf").read_bytes() == carrier.read_bytes()
    manifest = json.loads(fetcher.DEFAULT_MAP.read_text(encoding="utf-8"))
    with pymupdf.open(carrier) as doc:
        assert len(doc) == 1 and len(doc.embfile_names()) == 30
        assert all(n.endswith(".pdf") for n in doc.embfile_names())
        assert not doc[0].get_links()
        for xref in range(1, doc.xref_length()):
            obj = doc.xref_object(xref)
            assert not any(token in obj for token in ("/JavaScript", "/Launch", "/OpenAction", "/RichMedia"))
        for subject in manifest["subjects"]:
            for record in subject["assets"]:
                data = doc.embfile_get(resource.attachment_name(subject, record))
                fetcher.verify(record, data)
                assert data == (ROOT / record["repository_path"]).read_bytes()


@pytest.mark.parametrize("subject", ["國綜", "國寫", "英文", "數學A", "數學B", "社會", "自然"])
def test_offline_acquisition_all_subjects_without_network(subject, carrier, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Offline route attempted network")
    monkeypatch.setattr(fetcher, "request_bytes", forbidden)
    result = fetcher.materialize(subject, tmp_path, map_path=fetcher.DEFAULT_MAP,
                                resource_pdf=carrier, local_root=None, timeout=1, attempts=1)
    assert result["status"] == "verified"
    assert result["verified"] == (4 if subject in {"數學A", "數學B"} else 3)
    assert all(a["transport"] == "uploaded-resource-pdf" for a in result["assets"])


def test_missing_and_corrupt_attachments_are_not_downgraded(carrier, tmp_path):
    args = dict(map_path=fetcher.DEFAULT_MAP, local_root=None, timeout=1, attempts=1)
    for missing in (True, False):
        with pymupdf.open(carrier) as source, pymupdf.open() as doc:
            doc.new_page()
            name = "math-a--cover-blank.pdf"
            for existing in source.embfile_names():
                if existing == name and missing:
                    continue
                data = b"%PDF-corrupt" if existing == name else source.embfile_get(existing)
                doc.embfile_add(existing, data)
            bad = tmp_path / f"bad-{missing}.pdf"
            doc.save(bad)
        with pytest.raises(ValueError):
            fetcher.materialize("數學A", tmp_path / "out", resource_pdf=bad, **args)
        assert not (tmp_path / "out").exists()


def make_body(path, *, pages=2, bad=False, white=False):
    with pymupdf.open() as doc:
        for i in range(pages):
            page = doc.new_page(width=595.28, height=841.89)
            if white:
                page.draw_rect(page.rect, color=None, fill=(1, 1, 1))
            page.insert_text((70, 120), f"Layout-only test {i + 1}; not an exam.")
            if bad:
                page.insert_text((70, 45), "wrong rebuilt header")
        doc.save(path)


@pytest.mark.parametrize("subject,slug", [("數學A", "math-a"), ("數學B", "math-b"), ("社會", "social"),
                                         ("自然", "science"), ("英文", "english"),
                                         ("國綜", "chinese-comprehensive"), ("國寫", "chinese-writing")])
@pytest.mark.parametrize("pages", [1, 2])
def test_composition_preserves_cover_headers_formula_and_parity(subject, slug, pages, carrier, tmp_path):
    result = fetcher.materialize(subject, tmp_path / "assets", map_path=fetcher.DEFAULT_MAP,
                                resource_pdf=carrier, local_root=None, timeout=1, attempts=1)
    body = tmp_path / "body.pdf"
    make_body(body, pages=pages)
    font = tmp_path / "font.ttf"
    font.write_bytes(pymupdf.Font("cjk").buffer)
    output = tmp_path / "proof.pdf"
    report = compositor.compose(subject, body, tmp_path / "assets" / slug, output,
                                year="116", title="模擬試題", running_name="學測", font_path=font)
    assert report["status"] == "layout-proof-only"
    assert len(report["template_hashes"]) == result["verified"]
    manifest = json.loads(fetcher.DEFAULT_MAP.read_text(encoding="utf-8"))
    record = next(s for s in manifest["subjects"] if s["subject"] == subject)
    g = record["overlay_geometry_pt"]
    with pymupdf.open(output) as doc, pymupdf.open(tmp_path / "assets" / slug / "cover-blank.pdf") as cover:
        assert "116" in doc[0].get_text()
        assert compositor.masked_pixels(doc[0], [g["cover_title"]]) == compositor.masked_pixels(cover[0], [g["cover_title"]])
        for i in range(1, len(doc)):
            parity = "odd" if i % 2 else "even"
            with pymupdf.open(tmp_path / "assets" / slug / f"inner-{parity}-blank.pdf") as base:
                masks = [g["body"], *g[parity].values()]
                assert compositor.masked_pixels(doc[i], masks) == compositor.masked_pixels(base[0], masks)
        if subject.startswith("數學"):
            with pymupdf.open(tmp_path / "assets" / slug / "formula-blank.pdf") as formula:
                clip = pymupdf.Rect(g["body"])
                assert doc[-1].get_pixmap(clip=clip).samples == formula[0].get_pixmap(clip=clip).samples


@pytest.mark.parametrize("bad,white", [(True, False), (False, True)])
def test_body_rebuilt_headers_and_opaque_white_background_fail(tmp_path, bad, white):
    body = tmp_path / "bad.pdf"
    make_body(body, bad=bad, white=white)
    with pymupdf.open(body) as doc, pytest.raises(ValueError, match="outside measured"):
        compositor.check_body(doc[0], [64, 87, 532, 775])


def test_raw_math_and_large_void_are_review_findings_not_passes(tmp_path):
    pdf = tmp_path / "bad-math.pdf"
    with pymupdf.open() as doc:
        page = doc.new_page(width=595.28, height=841.89)
        # Real fixed templates contain an opaque white page-size vector.
        page.draw_rect(page.rect, color=None, fill=(1, 1, 1))
        page.insert_text((70, 100), "x^2 + log_2(x); [[3,1],[1,3]]")
        doc.save(pdf)
    report = inspector.audit(pdf, tmp_path / "raster", math=True)
    assert report["status"] == "mechanical-review-only"
    page = report["pages"][0]
    assert set(page["issues"]) == {"raw-math-markup-review", "large-bottom-void-review"}
    assert page["visual_review"] == "not-performed-by-this-tool"
    assert page["raster_sha256"] == hashlib.sha256(Path(page["raster_path"]).read_bytes()).hexdigest()


@pytest.mark.parametrize("font_path", ["C:/Windows/Fonts/kaiu.ttf", "C:/Windows/Fonts/mingliu.ttc"])
def test_dynamic_chinese_fields_have_full_width_advances(tmp_path, font_path):
    if not Path(font_path).is_file():
        pytest.skip("Windows Kai/Ming font regression requires the installed font")
    font = pymupdf.Font(fontfile=font_path)
    value = "116年學測"
    with pymupdf.open() as doc:
        page = doc.new_page()
        compositor.write_field(page, [70, 90, 200, 130], value, font, 20, align="left")
        data = doc.tobytes()
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        chars = [c for b in doc[0].get_text("rawdict")["blocks"] for l in b.get("lines", [])
                 for s in l["spans"] for c in s["chars"] if not c["c"].isspace()]
        assert len(chars) == len(value)
        expected_x = 70
        for character, actual in zip(value, chars):
            assert abs(actual["origin"][0] - expected_x) < .05
            expected_x += font.text_length(character, fontsize=20)


def test_grid_collision_is_checked_inside_page_not_just_page_boundary():
    with pymupdf.open() as doc:
        page = doc.new_page()
        for y in (100, 140, 180):
            page.draw_line((70, y), (400, y))
        for x in (70, 160, 400):
            page.draw_line((x, 100), (x, 180))
        page.insert_text((80, 120), "Fits")
        assert inspector.table_collision_samples(page) == []
        page.insert_text((149, 160), "LONG ANSWER", fontsize=15)
        assert inspector.table_collision_samples(page)
