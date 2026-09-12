"""Public-metadata and planner regressions, not an educational acceptance suite."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import exam_data
import pack_verification
from audit_exam_pack import readiness
import render_exam
import render_gsat_official
import render_gsat_internal_review


@pytest.mark.parametrize('subject,numbered,scored', [
    ('國綜', 36, 40), ('英文', 50, 53), ('數A', 20, 20),
    ('數B', 20, 20), ('自然', 56, 67), ('社會', 65, 68), ('國寫', 2, 3),
])
def test_full_plan_preserves_every_reviewed_slot(tmp_path, monkeypatch, subject, numbered, scored):
    pack = exam_data.resolve_subject(ROOT, '學測', subject)
    records, errors = exam_data.read_jsonl(pack / 'metadata/papers.jsonl')
    assert not errors
    paper = next(p for p in records if p['year'] == 2026 and p['source_kind'] == 'official_past_exam'
                 and (subject not in {'國綜', '國寫'} or p['section'] == subject))
    assert pack_verification.paper_errors(paper) == []
    # This test targets planning, without asserting local source availability.
    monkeypatch.setattr(exam_data, 'select_paper_profile', lambda *args: paper)
    monkeypatch.setattr(exam_data, 'select_layout_profile', lambda *args: None)
    import writer_calibration
    original_loader = writer_calibration.load_writer
    monkeypatch.setattr(writer_calibration, 'load_writer', lambda path, root=None: original_loader(path))
    output = tmp_path / 'plan.json'
    code = exam_data.generate_plan(ROOT, '學測', subject, None, 1, '108', None, [], output, False, True)
    plan = json.loads(output.read_text(encoding='utf-8'))
    assert plan['numbered_question_count'] == numbered
    assert plan['count'] == len(plan['items']) == scored
    slots = paper['evidence']['structure_review']['slots']
    for item, slot in zip(plan['items'], slots):
        assert item['target_slot_id'] == slot['id']
        assert item['target_number'] == slot.get('number')
        assert item['target_question_type'] == slot['type']
        assert item['target_score'] == slot['score']
        assert item['target_option_count'] == slot.get('option_count')
        if slot['type'] not in {'single_choice', 'multiple_choice'}:
            assert item.get('target_difficulty') is None
    missing = plan['historical_pattern_coverage']['missing_slots']
    assert code == (2 if missing else 0)
    assert (plan['calibration_level'] == 'incomplete-pattern-coverage') == bool(missing)


def test_readiness_never_confuses_no_sources_with_generation_ready(tmp_path):
    report = readiness(tmp_path)
    assert report['status'] == 'blocked'
    assert len(report['papers']) == 7
    assert all(p['errors'] for p in report['papers'])


def test_current_public_structure_and_layout_evidence_reconcile():
    report = readiness(ROOT, check_sources=False)
    assert report['source_files_checked'] is False
    for paper in report['papers']:
        assert paper['paper_id'] and paper['layout_id']
        assert all(e.startswith('writer:') for e in paper['errors'])
        assert (paper['status'] == 'blocked') == bool(paper['errors'])


def test_chinese_booklet_selection_is_explicit(monkeypatch):
    monkeypatch.setattr(pack_verification, 'paper_errors', lambda *args: [])
    path = exam_data.resolve_subject(ROOT, '學測', '國文')
    with pytest.raises(ValueError, match='國文包含兩份不同試卷'):
        exam_data.select_paper_profile(path, '108', None, 2026)
    assert exam_data.select_paper_profile(path, '108', None, 2026, '國寫')['section'] == '國寫'


def test_distributed_status_uses_writer_blueprint(capsys):
    assert exam_data.status(ROOT) == 0
    output = capsys.readouterr().out
    assert 'Writer 校準狀態' in output
    for line in output.splitlines():
        if any(line.startswith('學測  ' + s + ' ') for s in ('國文', '英文', '數學A', '數學B', '自然', '社會')):
            assert 'ready' in line


def unnumbered_fixture():
    return {'metadata': {'title': 'Software fixture', 'exam': '學測', 'subject': '英文',
                         'generation_mode': 'custom-practice', 'calibration_level': 'exploratory-uncalibrated',
                         'target_page_count': 2, 'layout_fidelity_status': 'reference-only'},
            'instructions': [], 'sections': [{'id': 'translation', 'title': '中譯英'}],
            'questions': [
                {'id': 't1', 'number': None, 'number_display': '1.', 'answer_label': '中譯英1',
                 'section_id': 'translation', 'type': 'constructed_response', 'prompt': 'First fixture task',
                 'score': 4, 'item_spec': {'slot_id': 'translation-1'}},
                {'id': 't2', 'number': None, 'number_display': '2.', 'answer_label': '中譯英2',
                 'section_id': 'translation', 'type': 'constructed_response', 'prompt': 'Second fixture task',
                 'score': 4, 'item_spec': {'slot_id': 'translation-2'}}],
            'answers': [{'question_id': 't1', 'final_answer': 'A', 'reasoning': ['Fixture solution']},
                        {'question_id': 't2', 'final_answer': 'B', 'reasoning': ['Fixture solution']}]}


@pytest.mark.parametrize('renderer', [render_exam.render_exam, render_gsat_official.render,
                                     render_gsat_internal_review.render])
def test_unnumbered_tasks_render_in_order_with_named_solutions(renderer):
    exam = unnumbered_fixture()
    assert render_exam.validate_exam(exam) == []
    html = renderer(exam, include_answers=True, **({'base': ROOT} if renderer is render_gsat_internal_review.render else {}))
    assert html.index('First fixture task') < html.index('Second fixture task')
    assert '中譯英1' in html and '中譯英2' in html
    assert 'None' not in html and '第  題' not in html


def test_unnumbered_task_requires_a_bound_slot_and_solution_label():
    exam = unnumbered_fixture()
    exam['questions'][0]['item_spec'] = {}
    assert render_exam.validate_exam(exam)
