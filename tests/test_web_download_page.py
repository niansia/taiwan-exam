from pathlib import Path
import json
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_URL = "https://niansia.github.io/taiwan-exam/download-web-knowledge.html"
VERSION = (ROOT / 'web/taiwan-exam-web-knowledge.md').read_text(encoding='utf-8').splitlines()[0].removeprefix('# Taiwan Exam Web Knowledge v')
RAW_URL = "https://raw.githubusercontent.com/niansia/taiwan-exam/main/web/taiwan-exam-web-knowledge.md?v=" + VERSION


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
    assert "版本：" + VERSION in page
    assert 'link.download = "taiwan-exam-template-resources.pdf"' in page
    assert 'location.hash === "#templates"' in page
    assert DOWNLOAD_URL + "#templates" in (ROOT / "README.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("fragment,bad,expected", [
    ("", False, "taiwan-exam-web-knowledge.md"),
    ("#templates", False, "taiwan-exam-template-resources.pdf"),
    ("#templates", True, None),
])
def test_download_javascript_selects_exactly_one_file_and_rejects_html(fragment, bad, expected):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node unavailable for DOM-free download control test")
    code = r'''
const fs = require('fs'), vm = require('vm');
const html = fs.readFileSync(process.argv[1], 'utf8');
const elements = Object.fromEntries(['status','download','templates'].map(id => [id, {addEventListener(){}}]));
const downloads = [], requests = [];
const fragment = process.argv[2], bad = process.argv[3] === 'true';
const ctx = vm.createContext({
  Blob, location: {hash: fragment},
  URL: {createObjectURL: () => 'blob:test', revokeObjectURL(){}},
  setTimeout: () => 0,
  document: {getElementById: id => elements[id], body: {appendChild(){}},
    createElement: () => ({click(){downloads.push(this.download)}, remove(){}})},
  fetch: async url => {requests.push(url); return {ok: true, blob: async () =>
    new Blob([(url.includes('.pdf') && !bad ? '%PDF-' : '<html>') + 'x'.repeat(1100000)])};}
});
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], ctx);
(async () => {
  for(let i=0;i<12;i++) await new Promise(resolve => setImmediate(resolve));
  process.stdout.write(JSON.stringify({downloads, requests, disabled: elements.templates.disabled}));
})();
'''
    completed = subprocess.run([node, "-e", code, str(ROOT / "docs/download-web-knowledge.html"),
                                fragment, str(bad).lower()], capture_output=True, text=True, check=True)
    result = json.loads(completed.stdout)
    assert len(result["requests"]) == 1
    assert result["downloads"] == ([expected] if expected else [])
    if fragment:
        assert not result["disabled"]
