"""A 社會 run need not fetch the CEEC specification or the NAER curriculum: the maintainer pinned
their URLs and hashes (a hosted run stopped when the CEEC site refused its connection)."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import validate_social_item_design as social

SECTIONS = ['測驗目標', '測驗內容', '題型配分', '試題舉例']


def scope_errors(contract):
    return social._scope_contract_errors({'metadata': {'social_scope_contract': contract}})


def test_a_contract_with_only_the_reviewed_sections_uses_the_pinned_record():
    assert scope_errors({'examined_spec_sections': SECTIONS}) == []


def test_sections_are_still_required():
    errors = scope_errors({'examined_spec_sections': SECTIONS[:2]})
    assert errors and errors[0]['code'] == 'social_specification_sections_not_reviewed'


def test_a_run_that_fetched_the_documents_keeps_its_own_record():
    own = {'ceec_specification_url': 'https://www.ceec.edu.tw/x.pdf', 'ceec_specification_sha256': 'abc',
           'ceec_specification_retrieved_at': '2026-10-01', 'examined_spec_sections': SECTIONS}
    assert scope_errors(own) == []


def test_the_pinned_record_names_both_documents_and_all_four_sections():
    record = json.loads((ROOT / 'references' / 'social-scope-sources.json').read_text(encoding='utf-8'))
    for key in ('ceec_specification', 'naer_curriculum'):
        assert record[key]['url'].startswith('https://') and len(record[key]['sha256']) == 64
    assert sorted(record['ceec_specification']['sections']) == sorted(SECTIONS)
    pinned = social.pinned_scope_sources()
    assert pinned['ceec_specification_sha256'] == '521c04293b3822f7931eafe824730d984eb210bb35a6edb00e8197247d2766e3'
    assert pinned['naer_curriculum_sha256'] == '5ad53d3db32505c11213c05fefca761c727753dbfc7b76aef91260cf8c0568f5'
