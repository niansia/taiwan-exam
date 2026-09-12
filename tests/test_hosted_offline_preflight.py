"""Resource/acceptance regressions, not generated-exam or academic certification."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import time

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import hosted_calibration as calibration
import prepare_hosted_run as preflight
import check_hosted_run as gate
import inspect_hosted_pdf as inspector
from hosted_item_layout import crop_items
from test_hosted_run_evidence import saved_run, fixed_evidence_pdfs, evaluate
from read_web_knowledge import extract
from build_web_knowledge import build

ROOT = calibration.ROOT


def forbid_network(*args, **kwargs):
    raise AssertionError('Offline workflow attempted a network connection')


@pytest.mark.parametrize('subject', calibration.SUBJECTS)
def test_all_subjects_prepare_offline_from_extracted_knowledge(subject, tmp_path, monkeypatch):
    knowledge = tmp_path / 'knowledge.md'
    knowledge.write_bytes(build('offline-test').encode())
    references = tmp_path / 'references'
    extract(knowledge, subject=subject, output_dir=references)
    # The saved capsule must also match LF-normalized hosted files.
    assert calibration.snapshot(subject, references) == calibration.snapshot(subject)
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    monkeypatch.setattr(socket.socket, 'connect', forbid_network)
    run = tmp_path / 'run'
    report = preflight.prepare(subject, run, 'test', font,
                               resource_pdf=ROOT / 'web/taiwan-exam-template-resources.pdf')
    assert report['status'] == 'ready-for-authoring', report
    assert report['original_pdf_required'] is False
    assert all((run / row['path']).is_file() for row in report['proofs'].values())
    assert not (run / 'exam.json').exists()
    assert not (run / 'run-state.json').exists()
    assert json.loads((run/'generation-timing.json').read_text())['active']['phase'] == 'reference_preflight'
    # Run the real portable CLI from the extracted tree, without source PDFs.
    if subject == '數學A':
        result = subprocess.run([sys.executable, str(references/'scripts/prepare_hosted_run.py'),
                                 '--subject', subject, '--run-dir', str(tmp_path/'portable-run'),
                                 '--paper-id', 'portable', '--font', str(font), '--resource-pdf',
                                 str(ROOT/'web/taiwan-exam-template-resources.pdf')],
                                capture_output=True, timeout=40)
        assert result.returncode == 0, result.stderr


def test_offline_basis_preserves_scope_and_correct_subject():
    math = calibration.snapshot('數學A')
    assert math['objective_profile']['full_paper_status'] == 'insufficient-data'
    writing = calibration.snapshot('國寫')
    assert writing['objective_profile'] is None and writing['writing_rubric']
    assert all(c['pattern']['section'].startswith('國寫') for c in writing['aggregate_patterns'])
    assert calibration.anchor_errors({'number': 3}, {'kind':'embedded-calibration','key':'slot:3'}, math) == []
    assert calibration.anchor_errors({'number': 3}, {'kind':'embedded-calibration','key':'slot:1'}, math)
    assert calibration.anchor_errors({'type':'constructed_response'},
                                     {'kind':'embedded-calibration','key':'objective'}, writing)


def test_metrics_reject_wrong_subject_role_and_stale_algorithm(tmp_path):
    c = calibration.snapshot('數學A')
    page = next(p for p in c['page_metrics'] if p['page_role']=='formula')
    finding = {**page, 'reference_page':page['page']}
    assert calibration.density_limit(c, finding, 'formula') == page['bottom_void'] + .10
    with pytest.raises(ValueError, match='actual page role'):
        calibration.density_limit(c, finding, 'body')
    with pytest.raises(ValueError):
        calibration.density_limit(calibration.snapshot('數學B'), finding, 'formula')
    knowledge = tmp_path / 'knowledge.md'
    knowledge.write_bytes(build('test').encode())
    extract(knowledge, subject='數學A', output_dir=tmp_path/'refs')
    path = tmp_path/'refs'/calibration.METRICS_PATH
    data = json.loads(path.read_text(encoding='utf-8'))
    data['algorithm_sha256'] = 'stale'
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match='stale algorithm'):
        calibration.snapshot('數學A', tmp_path/'refs')


def test_timeout_is_whole_process_deadline_not_socket_timeout(tmp_path, monkeypatch):
    # A real non-responsive child must be killed, not merely return a mocked error.
    (tmp_path/'fetch_hosted_template_assets.py').write_text('import time\ntime.sleep(30)\n', encoding='utf-8')
    monkeypatch.setattr(preflight, '__file__', str(tmp_path/'prepare_hosted_run.py'))
    started = time.monotonic()
    result = preflight.acquire('數學A', tmp_path, deadline=.3)
    assert time.monotonic() - started < 5
    assert result['status'] == 'partial'
    assert 'Overall' in result['errors'][0]['message']


def test_failed_preflight_preserves_authored_run_and_no_network_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(socket.socket, 'connect', forbid_network)
    exam = b'{"questions": ["saved work"]}'
    state = b'{"paper_id":"existing", "next_action":"review saved questions"}'
    (tmp_path/'exam.json').write_bytes(exam)
    (tmp_path/'run-state.json').write_bytes(state)
    corrupt = tmp_path/'stripped.pdf'
    with pymupdf.open() as doc:
        doc.new_page()
        doc.save(corrupt)
    report = preflight.prepare('數學A', tmp_path, 'existing', tmp_path/'unused.ttf', resource_pdf=corrupt)
    assert report['status'] == 'pending' and 'Missing PDF attachment' in report['errors'][0]
    assert (tmp_path/'exam.json').read_bytes() == exam
    assert (tmp_path/'run-state.json').read_bytes() == state
    with pytest.raises(ValueError, match='another paper'):
        preflight.prepare('數學A', tmp_path, 'different', tmp_path/'unused.ttf', resource_pdf=corrupt)


def offline_fixture(saved):
    """Use synthetic content with realistic density; keep genuine canonical gates."""
    state, save = saved
    c = calibration.snapshot('英文')
    state['calibration'] = save('calibration.json', c)
    review = json.loads(Path('difficulty.json').read_text())
    for row in review['items']:
        row['anchor'] = {'kind':'embedded-calibration','key':'objective'}
    state['checks']['difficulty'] = save('difficulty.json', review)
    for role in ('question','solution'):
        pdf = Path(role+'.pdf')
        with pymupdf.open(pdf) as doc:
            doc[-1].insert_text((75, 500), 'Synthetic continuation for density regression')
            data = doc.tobytes()
        pdf.write_bytes(data)
        bundle = state['pdfs'][role]
        bundle['file']['sha256'] = gate.sha(pdf)
        layout = json.loads(Path(role+'-items.json').read_text())
        layout['pdf_sha256'] = gate.sha(pdf)
        item_review = crop_items(pdf, layout, Path('crops')/role)
        for part in item_review['parts']:
            part.update(status='pass',observations='Synthetic fixture only')
        bundle['item_review'] = save(role+'-items.json', item_review)
        scan = inspector.audit(pdf, Path('rasters')/role)
        bundle['inspection'] = save(role+'-inspection.json', scan)
        visual = {'pdf_sha256':gate.sha(pdf), 'pages':[]}
        for page in scan['pages']:
            page_role = 'solutions' if role=='solution' else 'cover' if page['page']==1 else 'body'
            metric = max((p for p in c['page_metrics'] if p['page_role']==page_role), key=lambda p:p['bottom_void'])
            finding = {'decision':'justified','reason':'Synthetic density regression compared with canonical metric',
                       'kind':'embedded-page-metric','source_sha256':metric['source_sha256'],
                       'reference_page':metric['page'],'page_role':page_role}
            visual['pages'].append({'page':page['page'],'raster_sha256':page['raster_sha256'],
                                    'status':'pass','observations':'Synthetic fixture only',
                                    'issue_dispositions':{issue:finding for issue in page['issues']}})
        bundle['visual_review'] = save(role+'-review.json', visual)
        Path(role+'-reference.pdf').unlink()  # Only disposable test fixture files.
    return state, save


def test_final_checker_offline_without_originals_preserves_real_review_gate(saved_run, monkeypatch):
    state, save = offline_fixture(saved_run)
    monkeypatch.setattr(socket.socket, 'connect', forbid_network)
    assert evaluate(state, save)['status'] == 'evidence-complete'
    review = json.loads(Path('difficulty.json').read_text())
    review['reviewer_context'] = review['author_context']
    state['checks']['difficulty'] = save('difficulty.json', review)
    result = evaluate(state, save)
    assert result['status']=='pending' and any('separate blind reviewer' in e for e in result['errors'])


@pytest.mark.parametrize('change', ['missing','altered','wrong-subject','wrong-slot'])
def test_forged_or_missing_calibration_cannot_clear_final_gate(saved_run, change):
    state, save = offline_fixture(saved_run)
    if change=='missing':
        state.pop('calibration')
    elif change=='wrong-slot':
        report = json.loads(Path('difficulty.json').read_text())
        report['items'][0]['anchor']['key'] = 'constructed-response'
        state['checks']['difficulty'] = save('difficulty.json', report)
    else:
        c = calibration.snapshot('數學B' if change=='wrong-subject' else '英文')
        if change=='altered':
            c['page_metrics'][0]['bottom_void'] = 1.0
        state['calibration'] = save('calibration.json', c)
    result = evaluate(state, save)
    assert result['status']=='pending'
    assert any('calibration' in e or 'offline anchor' in e for e in result['errors'])
