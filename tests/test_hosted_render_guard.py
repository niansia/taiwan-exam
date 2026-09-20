"""Native hangs are bounded without sacrificing prior proofs or full-size text."""
from pathlib import Path
import sys
import time

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import hosted_body_templates as body


def test_timeout_kills_worker_and_preserves_old_proof(tmp_path, monkeypatch):
    prior = tmp_path / 'prior.pdf'
    prior.write_bytes(b'previous reviewed bytes')
    spawn = body.subprocess.Popen
    children = []
    def stalled(*args, **kwargs):
        worker = spawn([sys.executable, '-c', 'import time; time.sleep(60)'], **kwargs)
        children.append(worker)
        return worker
    monkeypatch.setattr(body.subprocess, 'Popen', stalled)
    started = time.monotonic()
    with pytest.raises(ValueError, match='Render stalled.*renderer startup'):
        body.guarded_render({}, tmp_path / 'new.pdf', tmp_path / 'new.json', tmp_path / 'font',
                            asset_root=tmp_path, timeout=.15)
    assert time.monotonic() - started < 5
    assert children[0].poll() is not None
    assert prior.read_bytes() == b'previous reviewed bytes'
    assert not (tmp_path / 'new.pdf').exists()


def test_each_measured_block_is_painted_without_second_html_fit(tmp_path, monkeypatch):
    original = pymupdf.Page.insert_htmlbox
    calls = []
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(pymupdf.Page, 'insert_htmlbox', counted)
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec = {'subject': '數學A', 'blocks': [
        {'kind': 'stimulus', 'id': str(n), 'text': f'Measured block {n}. ' * 12}
        for n in range(18)]}
    result = body.render(spec, tmp_path / 'body.pdf', tmp_path / 'body.json', font, asset_root=tmp_path)
    assert len(calls) == 18
    assert result['page_plan']['page_count'] > 1
    with pymupdf.open(tmp_path / 'body.pdf') as pdf:
        text = ''.join(p.get_text() for p in pdf)
        assert all(f'Measured block {n}.' in text for n in range(18))


def test_guarded_worker_returns_real_layout_and_errors(tmp_path):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    spec = {'subject': '數學A', 'blocks': [{'kind': 'stimulus', 'id': 'q1', 'text': 'Actual fixture'}]}
    layout = body.guarded_render(spec, tmp_path / 'body.pdf', tmp_path / 'body.json', font, asset_root=tmp_path)
    assert layout['page_plan']['pages'][0]['question_ids'] == ['q1']
    spec['blocks'][0]['text'] = 'An oversized unbroken item. ' * 5000
    with pytest.raises(ValueError, match='exceeds a page'):
        body.guarded_render(spec, tmp_path / 'bad.pdf', tmp_path / 'bad.json', font, asset_root=tmp_path)
    assert not (tmp_path / 'bad.pdf').exists()
