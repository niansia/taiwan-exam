"""A continuation must reuse intact readiness, but never stale or altered proofs."""
import json
from pathlib import Path
import sys

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_hosted_run as preflight
from hosted_run_timing import transition

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def ready(tmp_path):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    run = tmp_path / 'run'
    report = preflight.prepare('數學A', run, 'resume', font,
                               resource_pdf=ROOT / 'web/taiwan-exam-template-resources.pdf')
    assert report['status'] == 'ready-for-authoring', report
    transition(run / 'generation-timing.json', 'resume', 'authoring')
    (run / 'exam.json').write_bytes(b'{"authored": "saved work"}')
    return run, font, report


def test_resume_does_not_rebuild_download_or_change_phase_clock(ready, monkeypatch):
    run, font, report = ready
    before = {p.relative_to(run): (p.read_bytes(), p.stat().st_mtime_ns)
              for p in run.rglob('*') if p.is_file()}
    def forbidden(*args, **kwargs):
        pytest.fail('An intact continuation must not download or compose again')
    monkeypatch.setattr(preflight, 'acquire', forbidden)
    monkeypatch.setattr(preflight, 'compose', forbidden)
    # The original upload need no longer exist: verified run components suffice.
    result = preflight.prepare('數學A', run, 'resume', font)
    assert result['reused_preflight'] is True
    assert result['status'] == 'ready-for-authoring'
    assert result['proofs'] == report['proofs']
    after = {p.relative_to(run): (p.read_bytes(), p.stat().st_mtime_ns)
             for p in run.rglob('*') if p.is_file()}
    assert after == before
    assert json.loads((run / 'generation-timing.json').read_text())['active']['phase'] == 'authoring'
    # A caller may persist the returned readiness summary; its binding remains valid.
    preflight.save(run / 'preflight.json', result)
    assert preflight.prepare('數學A', run, 'resume', font)['reused_preflight'] is True


@pytest.mark.parametrize('changed', ['proof', 'raster', 'calibration', 'asset', 'font',
                                   'metadata', 'runtime', 'review-mode', 'incomplete', 'legacy'])
def test_changed_readiness_cannot_take_resume_shortcut(ready, monkeypatch, changed):
    run, font, report = ready
    if changed in {'proof', 'raster', 'calibration', 'asset', 'font'}:
        paths = {'proof': run / report['proofs']['questions']['path'],
                 'raster': run / report['proofs']['questions']['rasters'][0]['path'],
                 'calibration': run / 'calibration.json',
                 'asset': run / report['template_asset_dir'] / 'cover-blank.pdf', 'font': font}
        path = paths[changed]
        path.write_bytes(path.read_bytes() + b'\nchanged')
    elif changed in {'metadata', 'incomplete', 'legacy'}:
        if changed == 'metadata':
            report['calibration_basis'] = 'unreviewed replacement'
        elif changed == 'incomplete':
            report['status'] = 'pending'
        else:
            report.pop('cache_inputs')
        preflight.save(run / 'preflight.json', report)
    elif changed == 'runtime':
        original = preflight.cache_inputs
        monkeypatch.setattr(preflight, 'cache_inputs', lambda f: {**original(f), 'version': 999})
    called = []
    def repair_required(*args, **kwargs):
        called.append(True)
        raise ValueError('A real preflight is required')
    monkeypatch.setattr(preflight, 'acquire', repair_required)
    kwargs = {'review_mode': 'independent-context'} if changed == 'review-mode' else {}
    result = preflight.prepare('數學A', run, 'resume', font, **kwargs)
    assert called and result['status'] == 'pending'
    assert not result.get('reused_preflight')
    assert (run / 'exam.json').read_bytes() == b'{"authored": "saved work"}'


def test_explicit_independence_cannot_be_dropped_on_cached_resume(ready, monkeypatch):
    run, font, _ = ready
    preflight.save(run / 'run-state.json', {'paper_id': 'resume', 'subject': '數學A',
                                          'require_independent_review': True})
    def forbidden(*args, **kwargs):
        pytest.fail('Resolve explicit reviewer requirement before any asset work')
    monkeypatch.setattr(preflight, 'acquire', forbidden)
    result = preflight.prepare('數學A', run, 'resume', font)
    assert result['status'] == 'pending'
    assert result['require_independent_review'] is True
    assert 'actual separate reviewer' in result['errors'][0]
    assert not result.get('reused_preflight')


def test_wrong_subject_cannot_reuse_another_run(ready):
    run, font, _ = ready
    with pytest.raises(ValueError, match='another paper or subject'):
        preflight.prepare('數學B', run, 'resume', font)
