"""Synthetic evidence fixtures test contracts, NOT successful exam generation."""
import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pack_verification as pv
import validate_exam_release as release
from audit_exam_pack import audit
from audit_generated_suite import audit as audit_suite
import build_paper_profiles
import render_exam
import package_skill


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    return path


def reviewed_profile(tmp_path):
    source = tmp_path / 'source.pdf'; source.write_bytes(b'local synthetic reference bytes')
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    p = {'paper_id': 'test', 'exam': '學測', 'subject': '自然', 'section': None,
         'year': 2026, 'curriculum': '108', 'regime': '111學年度起', 'source_kind': 'official_past_exam',
         'source_files': [{'relative_path': 'source.pdf', 'sha256': sha, 'page_count': 2, 'role': 'question'}],
         'structure_status': 'verified', 'scored_item_count': 1, 'numbered_question_count': 1,
         'duration_minutes': 110, 'total_score': 2,
         'sections': [{'id': 's1', 'title': '選擇題', 'order': 1, 'scored_item_count': 1,
             'numbered_question_count': 1, 'question_type_mix': {'single_choice': 1},
             'instructions_pattern': 'synthetic reviewed instruction', 'score_rule': 'two points', 'subtotal_score': 2}],
         'evidence': {'method': 'manual_review', 'confidence': 0.8}}
    p['evidence']['structure_review'] = {'profile_sha256': pv.profile_digest(p), 'reviewer': 'test-fixture',
        'reviewed_at': '2026-09-09T00:00:00Z', 'method': 'page-by-page', 'unresolved': [],
        'pages': [{'source_sha256': sha, 'page': 2, 'observations': 'synthetic observation'}],
        'slots': [{'id': 'one', 'number': 1, 'section_id': 's1', 'type': 'single_choice', 'score': 2,
                   'option_count': 2, 'source_sha256': sha, 'page': 2}]}
    return p


def reviewed_layout(p):
    l = {k: copy.deepcopy(p[k]) for k in ('exam', 'subject', 'section', 'curriculum', 'regime', 'source_files')}
    l.update(profile_id='layout-test', fidelity_status='verified',
        instructions={'transcription_status': 'verified', 'blocks': [{'text': 'synthetic instructions'}]},
        typography={'body_pt': 11}, page_geometry={'width_mm': 210}, question_styles={'body': 'Ming'},
        pagination={'physical_pages': 2}, cover={'title': 'fixture'}, running_elements={'page': 'fixture'})
    sha = p['source_files'][0]['sha256']
    l['evidence'] = {'layout_review': {'profile_sha256': pv.profile_digest(l), 'reviewer': 'test-fixture',
        'reviewed_at': '2026-09-09T00:00:00Z', 'method': 'page-by-page', 'unresolved': [],
        'pages': [{'source_sha256': sha, 'page': i, 'observations': 'synthetic measured page'} for i in [1, 2]]}}
    return l


def test_positive_profile_and_layout_contract(tmp_path):
    p = reviewed_profile(tmp_path)
    assert pv.paper_errors(p, tmp_path) == []
    assert pv.layout_errors(reviewed_layout(p), tmp_path, p) == []


def test_verified_string_is_not_evidence(tmp_path):
    p = reviewed_profile(tmp_path); p['evidence'].pop('structure_review')
    assert pv.paper_errors(p, tmp_path)


def test_changed_source_and_profile_invalidate_review(tmp_path):
    p = reviewed_profile(tmp_path)
    (tmp_path / 'source.pdf').write_bytes(b'changed')
    assert any('hash mismatch' in e for e in pv.paper_errors(p, tmp_path))
    p['total_score'] = 3
    assert any('stale profile' in e for e in pv.paper_errors(p))


def test_mixed_group_is_not_response_type(tmp_path):
    p = reviewed_profile(tmp_path)
    p['evidence']['structure_review']['slots'][0]['type'] = 'mixed_group'
    assert any('actual response type' in e for e in pv.paper_errors(p))


def test_missing_option_count_is_rejected(tmp_path):
    p = reviewed_profile(tmp_path)
    p['evidence']['structure_review']['slots'][0].pop('option_count')
    assert any('option count' in e for e in pv.paper_errors(p))


def test_layout_must_match_subject_and_cover_all_pages(tmp_path):
    p = reviewed_profile(tmp_path); l = reviewed_layout(p)
    l['evidence']['layout_review']['pages'].pop()
    assert any('every reference page' in e for e in pv.layout_errors(l))
    other = copy.deepcopy(p); other['subject'] = '英文'
    assert any('subject mismatch' in e for e in pv.layout_errors(reviewed_layout(p), paper=other))


def test_auto_recipe_is_not_all_single_choice_science():
    recipe = build_paper_profiles.official_current_structure(115, '自然', None)
    assert recipe[2][0]['question_type_mix'] == {}
    assert build_paper_profiles.section_type_mix('選擇題', 36) == {}


def test_audit_revokes_without_deleting_source(tmp_path):
    p = reviewed_profile(tmp_path); p['evidence'].pop('structure_review')
    path = write(tmp_path / 'exam_packs/學測/subjects/自然/metadata/papers.jsonl', p)
    source = (tmp_path / 'source.pdf').read_bytes()
    r = audit(tmp_path, repair=True)
    assert r['changed_profiles'] == 1
    assert json.loads(path.read_text(encoding='utf-8'))['structure_status'] == 'needs_review'
    assert (tmp_path / 'source.pdf').read_bytes() == source


def test_generic_renderer_rejects_full_paper_even_verified_label():
    with pytest.raises(ValueError, match='[Gg]eneric renderer'):
        render_exam.render_exam({'metadata': {'generation_mode': 'full-paper', 'layout_fidelity_status': 'verified'}})


def test_legacy_suite_and_selftest_are_excluded_from_package():
    for name in ('build_gsat_stress_suite_116.py', 'self_test_chinese_natural_v2.py'):
        assert not package_skill.should_include(ROOT / 'scripts' / name)
    assert not package_skill.should_include(ROOT / 'scripts/new_unreviewed_batch_builder.py')
    assert package_skill.should_include(ROOT / 'scripts/validate_exam_release.py')


def answer_fixture():
    q = {'id': 'q1', 'number': 1, 'prompt': 'fixture', 'type': 'single_choice', 'options': [{'label': 'A', 'text': 'yes'}, {'label': 'B', 'text': 'no'}]}
    a = {'question_id': 'q1', 'final_answer': 'A', 'reasoning': ['specific fixture reason']}
    a['independent_review'] = {'question_sha256': release.content_hash(q), 'answer_sha256': pv.digest(a),
        'reviewer': 'fixture', 'reviewed_at': '2026-09-09T00:00:00Z', 'solution': 'fixture solution',
        'difficulty_rationale': 'fixture distinction', 'shortest_route': 'fixture route',
        'answer_visible_during_solve': False, 'derived_answer': 'A', 'option_verdicts': {'A': 'true evidence', 'B': 'false evidence'}, 'unresolved': []}
    return {'questions': [q], 'answers': [a]}


def test_answers_positive_and_stale_key():
    d = answer_fixture(); assert not release.independent_answer_errors(d)
    d['answers'][0]['final_answer'] = 'B'
    assert any('stale' in e for e in release.independent_answer_errors(d))


def test_single_pass_and_missing_option_analysis_fail():
    d = answer_fixture(); d['answers'][0]['independent_review'].pop('solution')
    d['answers'][0]['independent_review']['option_verdicts'].pop('B')
    assert len(release.independent_answer_errors(d)) >= 2


def test_nested_source_ids_are_not_ignored():
    d = {'questions': [{'number': 1, 'item_spec': {'literacy': {'source_ids': ['missing']}}}]}
    assert release.source_link_errors(d, [])
    assert not release.source_link_errors(d, {'sources': [{'source_id': 'missing'}]})


def test_number_swaps_flagged_across_forms(tmp_path):
    paths = [write(tmp_path / f'{n}.json', {'metadata': {'subject': '自然'}, 'questions': [
        {'id': str(n), 'number': 1, 'prompt': f'物體沿直線移動{n}公尺，歷時21秒，平均速率最接近何者？'}]}) for n in (131, 143)]
    r = audit_suite(paths)
    assert len(r['collisions']) == 1
    assert r['semantic_originality'] == 'not-verified'


def test_no_lexical_flags_is_not_originality_pass(tmp_path):
    path = write(tmp_path / 'one.json', {'metadata': {}, 'questions': []})
    assert audit_suite([path])['status'] == 'no-lexical-flags'


def test_release_downgrade_and_missing_pdf_fail_closed(tmp_path):
    exam = write(tmp_path / 'exam.json', {'metadata': {'subject': '自然', 'exam': '學測', 'curriculum': '108',
        'generation_mode': 'custom-practice', 'layout_fidelity_status': 'generic'}, 'questions': [], 'answers': []})
    contract = write(tmp_path / 'contract.json', {'requested_mode': 'full-paper', 'user_request': 'full paper',
        'subject': '自然', 'exam': '學測', 'curriculum': '108'})
    r = release.validate(exam, contract, 'delivery', root=tmp_path, execute=False)
    assert r['status'] == 'fail'
    assert any('downgraded' in e for e in r['errors'])
    assert any('missing or changed PDF' in e for e in r['errors'])


def test_release_positive_coordinator_and_failing_child(tmp_path, monkeypatch):
    # Stub only the external subject check execution: this tests orchestration,
    # not the educational adequacy of a one-item synthetic fixture.
    p = reviewed_profile(tmp_path); pack = tmp_path / 'exam_packs/學測/subjects/自然'
    write(pack.parents[1] / 'manifest.json', {'subjects': ['自然']})
    write(pack / 'subject.json', {'name': '自然'})
    write(pack / 'metadata/papers.jsonl', p)
    write(pack / 'blueprints/layout-profiles/test.json', reviewed_layout(p))
    write(pack / 'blueprints/writer-blueprint.json', {'metadata_fingerprint': 'fixture', 'calibration_status': 'ready'})
    d = answer_fixture(); d['questions'][0].update(section_id='s1', score=2)
    d['metadata'] = {'subject': '自然', 'paper_subject': '自然', 'exam': '學測', 'curriculum': '108',
        'generation_mode': 'full-paper', 'layout_fidelity_status': 'verified', 'layout_profile': 'layout-test',
        'paper_profile_id': 'test', 'duration_minutes': 110, 'total_score': 2, 'blueprint_fingerprint': 'fixture'}
    exam = write(tmp_path / 'exam.json', d)
    contract = write(tmp_path / 'contract.json', {'requested_mode': 'full-paper', 'user_request': 'full paper',
        'subject': '自然', 'exam': '學測', 'curriculum': '108'})
    calls = []
    def check(name, args):
        calls.append(name); return {'check': name, 'exit_code': 0}
    monkeypatch.setattr(release, 'run_check', check)
    r = release.validate(exam, contract, root=tmp_path)
    assert r['status'] == 'pass-content-evidence', r['errors']
    assert 'validate_paper_difficulty_balance.py' in calls and 'validate_source_grounding.py' in calls
    monkeypatch.setattr(release, 'run_check', lambda name, args: {'check': name, 'exit_code': 1})
    assert release.validate(exam, contract, root=tmp_path)['status'] == 'fail'


def test_duplicate_options_and_wrong_independent_result_fail():
    d = answer_fixture(); d['questions'][0]['options'][1]['text'] = 'yes'
    d['answers'][0]['independent_review']['derived_answer'] = 'B'
    errors = release.independent_answer_errors(d)
    assert any('duplicate' in e for e in errors)
    assert any('disagree' in e for e in errors)


def test_english_completion_requires_actual_reinsertion():
    d = answer_fixture(); d['metadata'] = {'subject': '英文'}
    d['questions'][0].update(section_id='cloze')
    d['sections'] = [{'id': 'cloze', 'title': '綜合測驗'}]
    assert any('reinsertion' in e for e in release.independent_answer_errors(d))
    d['answers'][0]['independent_review']['completed_text'] = 'Actual completed fixture sentence.'
    assert not any('reinsertion' in e for e in release.independent_answer_errors(d))


def test_page_review_complete_then_stale_or_missing_page(tmp_path):
    from pypdf import PdfWriter
    writer = PdfWriter(); writer.add_blank_page(width=595, height=842)
    path = tmp_path / 'test.pdf'
    with path.open('wb') as stream:writer.write(stream)
    raster = tmp_path / 'page.png'; raster.write_bytes(b'synthetic raster fixture, not visual acceptance')
    checks = {k: 'pass' for k in ('font_glyphs', 'font_roles_sizes', 'formula_geometry', 'overflow',
        'whitespace', 'source_notes', 'figure_grayscale', 'headers_numbering', 'content_legibility')}
    r = {'pdf_sha256': release.file_hash(path), 'exam_sha256': 'fixture-sha', 'reviewer': 'fixture',
         'reviewed_at': '2026-09-09T00:00:00Z', 'unresolved': [], 'pages': [
         {'page': 1, 'checks': checks, 'observations': 'synthetic fixture observations',
          'reference_page': 'fixture page 1', 'raster_path': 'page.png', 'raster_sha256': release.file_hash(raster)}]}
    review = write(tmp_path / 'review.json', r)
    artifact = {'path': 'test.pdf', 'sha256': release.file_hash(path), 'expected_page_count': 1, 'review_path': 'review.json'}
    assert not release.artifact_review_errors(artifact, tmp_path, 'fixture-sha', 'student')
    assert any('stale' in e for e in release.artifact_review_errors(artifact, tmp_path, 'changed-exam', 'student'))
    r['pages'] = []; write(review, r)
    assert any('every PDF page' in e for e in release.artifact_review_errors(artifact, tmp_path, 'fixture-sha', 'student'))
