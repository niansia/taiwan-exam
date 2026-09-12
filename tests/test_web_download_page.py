from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_URL = "https://niansia.github.io/taiwan-exam/download-web-knowledge.html"
RAW_URL = "https://raw.githubusercontent.com/niansia/taiwan-exam/main/web/taiwan-exam-web-knowledge.md?v=2026.09.12.4"


def test_readme_uses_one_click_web_download():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert DOWNLOAD_URL in readme
    assert "直接下載網頁版知識檔" in readme


def test_download_page_preserves_markdown_filename_and_source():
    page = (ROOT / "docs" / "download-web-knowledge.html").read_text(encoding="utf-8")
    assert RAW_URL in page
    assert 'const filename = "taiwan-exam-web-knowledge.md"' in page
    assert 'link.download = filename' in page
    assert "downloadKnowledge();" in page
    assert "不是 ZIP 或執行檔" in page
    assert "版本：2026.09.12.4" in page
