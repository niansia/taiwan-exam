"""One fixed density rule for plan, inspector and checker, and balanced pagination in the renderer."""
import json
from pathlib import Path
import sys

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import hosted_body_templates as hb
import hosted_density as density
import inspect_hosted_pdf as inspector
import prepare_hosted_review as review


def test_fixed_limits_follow_the_page_role_and_the_last_body_page():
    pages = [(1, '－作答注意事項－ 請於考試開始鈴響起'), (2, '1. 題目'), (3, '2. 題目'), (4, '參考公式及可能用到的數值')]
    limits = density.booklet_limits(pages, '數學A')
    assert limits[1] == ('cover', None) and limits[4] == ('formula', None)
    assert limits[2] == ('body', 0.32) and limits[3] == ('body', 0.60)  # page 3 is the last body page
    prose = density.booklet_limits([(1, '－作答注意事項－'), (2, 'a'), (3, 'b')], '英文')
    assert prose[2] == ('body', 0.42) and prose[3] == ('body', 0.60)
    solutions = density.booklet_limits([(1, '第1題 答案'), (2, '第2題')], '國綜', solutions=True)
    assert solutions[1] == ('solutions', 0.32) and solutions[2] == ('solutions', 0.60)
    assert density.verdict(0.35, 0.32)['over_limit'] and not density.verdict(0.35, 0.60)['over_limit']
    assert density.verdict(0.9, None)['over_limit'] is False


def _booklet(tmp_path, fills):
    """A booklet whose page n is filled down to `fills[n]` of the body; page 1 is a cover."""
    doc = pymupdf.open()
    cover = doc.new_page(width=595.28, height=841.89)
    cover.insert_text((80, 200), '－作答注意事項－', fontsize=14, fontname='china-t')
    for fill in fills:
        page = doc.new_page(width=595.28, height=841.89)
        y = 100
        while y < 87 + (775 - 87) * fill:
            page.insert_text((70, y), 'Synthetic density line ' * 3, fontsize=11)
            y += 16
    path = tmp_path / 'booklet.pdf'
    doc.save(path)
    return path


def test_inspector_flags_only_pages_over_their_own_limit(tmp_path):
    scan = inspector.audit(_booklet(tmp_path, [0.5, 0.95, 0.5]), tmp_path / 'r', subject='國綜')
    by_page = {p['page']: p for p in scan['pages']}
    assert by_page[1]['page_role'] == 'cover' and by_page[1]['bottom_void_limit'] is None
    assert 'large-bottom-void-review' not in by_page[1]['issues']
    assert by_page[2]['bottom_void_limit'] == 0.32 and 'large-bottom-void-review' in by_page[2]['issues']
    assert by_page[3]['bottom_void_limit'] == 0.32 and 'large-bottom-void-review' not in by_page[3]['issues']
    assert by_page[4]['bottom_void_limit'] == 0.60 and 'large-bottom-void-review' not in by_page[4]['issues']


def test_density_evidence_reports_the_fixed_limit_and_keeps_references_as_information():
    inside = review.density_evidence('數學A', 'question', 3, 8, 0.30)
    assert inside['status'] == 'within-fixed-limit' and inside['limit'] == 0.32
    outside = review.density_evidence('數學A', 'question', 3, 8, 0.5)
    assert outside['status'] == 'exceeds-fixed-limit' and 'largest_embedded_reference' in outside
    last = review.density_evidence('數學A', 'question', 7, 8, 0.5)
    assert last['status'] == 'within-fixed-limit' and last['limit'] == 0.60  # page 7 precedes the formula page
    assert review.density_evidence('數學A', 'solution', 2, 3, 0.5)['page_role'] == 'solutions'


def _paragraphs(n, seed):
    return [f'段落{seed}-{i}。' + '這是一段可以在段落邊界續頁的說明文字，用來測試分頁是否平均。' * 3 for i in range(n)]


def test_balanced_pagination_spreads_a_remainder_instead_of_stranding_it(tmp_path):
    font = tmp_path / 'font.ttf'
    font.write_bytes(pymupdf.Font('cjk').buffer)
    blocks = []
    for k in range(9):
        blocks.append({'kind': 'passage', 'id': f'p{k}', 'paragraphs': _paragraphs(10, k), 'split': 'paragraphs'})
    spec = {'subject': '國綜', 'blocks': blocks}
    layout = hb.render(spec, tmp_path / 'b.pdf', tmp_path / 'b.json', font, asset_root=tmp_path, proof=True)
    ratios = layout['bottom_void_ratios']
    assert layout['page_plan']['page_count'] == len(ratios) >= 2
    limits = [0.60 if n == len(ratios) else 0.32 for n in range(1, len(ratios) + 1)]
    assert all(v <= l for v, l in zip(ratios, limits)), (layout['pagination'], ratios)
    greedy = hb.render(spec, tmp_path / 'g.pdf', tmp_path / 'g.json', font, asset_root=tmp_path, proof=True,
                       balance_last_page=False)
    assert greedy['pagination'] == 'greedy'
    assert max(layout['bottom_void_ratios']) <= max(greedy['bottom_void_ratios']) + 1e-9
