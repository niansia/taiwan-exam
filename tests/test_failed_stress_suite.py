"""Optional negative regression against the user-reported failed local suite.

Private output is intentionally not shipped. Removing the output skips these
tests; the self-contained release-contract tests remain reproducible everywhere.
"""
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_exam_release import validate

PAPERS = sorted((ROOT / 'output/pdf/116學測模擬考壓力測試/json').glob('*.json'))


@pytest.mark.parametrize('paper', PAPERS, ids=lambda p: p.stem)
def test_failed_stress_paper_cannot_pass_formal_content_gate(paper, tmp_path):
    meta = json.loads(paper.read_text(encoding='utf-8'))['metadata']
    contract = tmp_path / 'request.json'
    contract.write_text(json.dumps({'requested_mode': 'full-paper', 'user_request': 'User-requested formal multi-form acceptance test',
        'exam': meta['exam'], 'subject': meta.get('paper_subject') or meta['subject'], 'curriculum': meta['curriculum']}, ensure_ascii=False), encoding='utf-8')
    report = validate(paper, contract, 'content')
    assert report['status'] == 'fail'
    assert 'request downgraded to custom/generic preview' in report['errors']
    common = {r['check']: r['exit_code'] for r in report['checks']}
    assert common['validate_paper_difficulty_balance.py'] != 0
    assert common['validate_llm_originality_contract.py'] != 0
