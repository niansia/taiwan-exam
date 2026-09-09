"""Behavioral security and geometry regressions using only benign fixtures."""
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import safe_rendering as safe
import render_exam
import render_pdf
import render_visual
import validate_fixed_page_html as fixed
import validate_svg_text_geometry as geometry


def svg(body):
    return '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" viewBox="0 0 200 100">' + body + '</svg>'


@pytest.mark.parametrize('body', [
    '<script>void 0</script>', '<rect onload="void 0"/>',
    '<foreignObject><div>text</div></foreignObject>',
    '<image href="https://example.invalid/image.png"/>',
    '<use href="file:///outside.svg#shape"/>',
    '<path style="fill:url(https://example.invalid/a)"/>',
    '<animate attributeName="href" to="https://example.invalid"/>',
    '<style>@import "https://example.invalid/a.css";</style>',
])
def test_svg_active_or_external_content_is_rejected(body):
    with pytest.raises(ValueError):
        safe.validate_svg(svg(body))


@pytest.mark.parametrize('prefix', ['<!DOCTYPE svg>', '<?xml-stylesheet href="x"?>', '<!ENTITY x "y">'])
def test_svg_declarations_rejected(prefix):
    with pytest.raises(ValueError):
        safe.validate_svg(prefix + svg(''))


@pytest.mark.parametrize('source', [
    '<script>void 0</script>', '<img src="https://example.invalid/a.png">',
    '<img src="file:///outside.png">', '<div onclick="void 0">text</div>',
    '<iframe srcdoc="text"></iframe>', '<meta http-equiv="refresh" content="0;url=https://example.invalid">',
    '<style>@import "https://example.invalid/a.css";</style>',
    '<div style="background:u\\72l(https://example.invalid)">text</div>',
    '<a href="https://example.invalid">link</a>', '<img srcset="a.png 1x">',
])
def test_html_rejects_active_and_external_resources(source):
    with pytest.raises(ValueError):
        safe.prepare_html(source)


def test_csp_allows_only_installed_measurement_script():
    script = 'document.body.dataset.measured = "yes";'
    prepared = safe.prepare_html('<html><head></head><body>中文</body></html>', measurement_script=script)
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    assert "script-src 'sha256-" + digest + "'" in prepared
    assert "default-src 'none'" in prepared
    assert prepared.index('Content-Security-Policy') < prepared.index('<body>')
    assert script in prepared
    assert "script-src 'none'" in safe.prepare_html('<p>中文</p>')


def test_generated_visual_and_exam_keep_text_and_geometry():
    spec = json.loads((ROOT / 'templates/visual-spec.json').read_text(encoding='utf-8'))
    original = render_visual.render(spec)
    assert safe.validate_svg(original) == original
    assert '<svg' in safe.prepare_html(original)
    exam = json.loads((ROOT / 'examples/synthetic-exam.json').read_text(encoding='utf-8'))
    prepared = safe.prepare_html(render_exam.render_exam(exam))
    assert '會考數學版型測試卷' in prepared and '@page' in prepared


def test_path_escape_and_mislabeled_image_fail(tmp_path):
    base = tmp_path / 'exam'
    base.mkdir()
    outside = tmp_path / 'outside.png'
    outside.write_bytes(b'not an image')
    with pytest.raises(ValueError, match='資料夾外'):
        render_exam.image_data_uri('../outside.png', base)
    inside = base / 'fake.png'
    inside.write_bytes(b'<html>text</html>')
    with pytest.raises(ValueError, match='declared image format'):
        render_exam.image_data_uri('fake.png', base)


def test_forged_layout_report_is_rejected():
    with pytest.raises(ValueError, match='reserved'):
        fixed._instrument('<pre id="' + fixed.REPORT_ID + '">{"pages": []}</pre>')


def test_browser_profile_is_new_and_security_is_not_disabled(tmp_path):
    flags = safe.browser_flags(tmp_path)
    assert '--user-data-dir=' + str(tmp_path / 'browser-profile') in flags
    assert '--no-sandbox' not in flags and '--disable-web-security' not in flags
    with pytest.raises(FileExistsError):
        safe.browser_flags(tmp_path)


def test_rejected_svg_never_launches_browser(tmp_path, monkeypatch):
    path = tmp_path / 'active.svg'
    path.write_text(svg('<script>void 0</script>'), encoding='utf-8')
    def forbidden(*args, **kwargs):
        pytest.fail('Untrusted SVG reached the browser')
    monkeypatch.setattr(geometry.subprocess, 'run', forbidden)
    with pytest.raises(ValueError):
        geometry.measure(path)


@pytest.fixture
def browser():
    try:
        return render_pdf.find_browser()
    except ValueError:
        pytest.skip('Local Chromium is unavailable; pure input checks still run')


@pytest.mark.parametrize('body,expected', [
    ('<text x="20" y="30" font-size="16">Label</text><line x1="0" y1="80" x2="150" y2="80" stroke="black"/>', None),
    ('<text x="20" y="30" font-size="16">Label</text><line x1="0" y1="25" x2="150" y2="25" stroke="black"/>', 'label-stroke-intersection'),
    ('<text x="-10" y="30" font-size="16">Label</text>', 'label-outside-viewport'),
    ('<text x="20" y="30">First</text><text x="20" y="30">Second</text>', 'label-overlap'),
    ('<text x="20" y="30" font-size="16">Label</text><g transform="translate(0,-55)"><line x1="0" y1="80" x2="150" y2="80" stroke="black"/></g>', 'label-stroke-intersection'),
])
def test_real_browser_geometry(tmp_path, browser, body, expected):
    path = tmp_path / 'figure.svg'
    path.write_text(svg(body), encoding='utf-8')
    report = geometry.measure(path, browser)
    if expected:
        assert report['status'] == 'fail'
        assert expected in {issue['kind'] for issue in report['issues']}
    else:
        assert report['status'] == 'pass-geometry-only' and report['labels'] == 1


def test_real_browser_layout_probe_runs_under_csp(tmp_path, browser):
    path = tmp_path / 'paper.html'
    path.write_text('<html><head><style>.sheet{width:500px;height:500px}.content{width:400px;height:400px}</style></head><body><div class="sheet"><div class="content"><p>中文 layout</p></div></div></body></html>', encoding='utf-8')
    report = fixed.validate_html(path, browser)
    assert len(report['pages']) == 1 and report['status'] == 'pass'


def test_empty_svg_directory_is_not_a_pass(tmp_path):
    (tmp_path / 'report.json').write_text('{"status":"pass-geometry-only"}', encoding='utf-8')
    assert geometry.main([str(tmp_path), str(tmp_path / 'report.json')]) == 2
    assert json.loads((tmp_path / 'report.json').read_text(encoding='utf-8'))['status'] == 'fail'


def test_real_pdf_keeps_chinese_text_and_pages(tmp_path, browser):
    import fitz
    source = ROOT / 'examples/synthetic-exam.json'
    target = tmp_path / 'proof.pdf'
    render_pdf.render_pdf(source, target, browser, provenance=False)
    with fitz.open(target) as document:
        text = ''.join(page.get_text() for page in document)
        assert document.page_count >= 1
        assert '會考數學版型測試卷' in text


def test_missing_static_source_does_not_create_passing_measurements(tmp_path, monkeypatch):
    source = tmp_path / 'bad.html'
    source.write_text('<script>void 0</script>', encoding='utf-8')
    def forbidden(*args, **kwargs):
        pytest.fail('Active document reached the browser')
    monkeypatch.setattr(fixed.subprocess, 'run', forbidden)
    with pytest.raises(ValueError):
        fixed.validate_html(source)
