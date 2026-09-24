"""Synthetic source records test the recent-context gate, not real-world facts."""
import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_current_context import FLOORS, progress, validate

LOCK = '2026-09-21'


def source(sid, event='2026-08-18', published=None, family='government_data'):
    return {'source_id': sid, 'publisher': f'Synthetic publisher {sid}', 'title': 'Synthetic release',
            'canonical_url': f'https://example.org/{sid}', 'source_family': family, 'authority_class': 'primary',
            'event_date': event, 'published_at': published or event, 'accessed_at': '2026-09-20',
            'fact_check_status': 'verified', 'rights_status': 'facts_only_synthesis',
            'verified_facts': ['Synthetic fact, not a real measurement']}


def context(sid, freshness='current_event'):
    return {'source_id': sid, 'freshness_class': freshness, 'relation': 'Synthetic series drives the answer',
            'removal_counterfactual': 'Without the series the item is unanswerable', 'outside_knowledge_required': False}


def natural_paper():
    sources = [source('nobel-2025', event='2025-10-06', family='research'),
               source('typhoon-2026', event='2026-08-18'),
               source('mission-2026', event='2026-03-02', family='research', published='2026-03-05'),
               source('energy-2026', event='2026-01-15', published='2026-02-01', family='news'),
               source('quake-2026', event='2026-06-20', family='government_data')]
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 'p1' if n <= 36 else 'p2', 'item_spec': {}} for n in range(1, 57)]
    recent = {5: 'nobel-2025', 6: 'nobel-2025', 30: 'energy-2026', 44: 'typhoon-2026', 45: 'typhoon-2026', 50: 'mission-2026',
              52: 'quake-2026', 53: 'quake-2026'}
    for number, sid in recent.items():
        questions[number - 1]['item_spec']['current_context'] = context(sid)
        questions[number - 1]['group_stimulus'] = f'Synthetic material from {sid}'
    questions[43]['item_spec']['context_tags'] = ['typhoon', 'taiwan', 'weather_hazard']
    questions[44]['item_spec']['context_tags'] = ['typhoon', 'taiwan']
    for number in (29, 30, 31, 32):
        questions[number]['item_spec']['context_tags'] = ['climate_energy']
    questions[8]['item_spec']['context_tags'] = ['taiwan', 'earthquake']
    return {'metadata': {'subject': '自然', 'generation_mode': 'full-paper',
                         'current_context_plan': {'editorial_lock_date': LOCK, 'sources': sources},
                         'natural_source_ecology_plan': {'recent_item_numbers': [5, 6, 30, 44, 45, 50, 52, 53]}},
            'sections': [{'id': 'p1', 'title': '第壹部分'}, {'id': 'p2', 'title': '第貳部分'}], 'questions': questions}


def test_a_natural_paper_shaped_like_the_official_form_passes():
    assert validate(natural_paper()) == []
    counts = progress(natural_paper())['counts']
    assert counts['recent_sources'] == 5 and counts['recent_items'] == 8 and counts['fresh_sources'] == 2
    assert counts['tags'] == {'climate_energy': 4, 'taiwan': 3, 'taiwan_hazard': 3}


def test_other_subjects_and_partial_papers_are_left_alone():
    paper = natural_paper()
    paper['metadata']['subject'] = '數學A'
    assert validate(paper) == []
    partial = natural_paper()
    partial['metadata'].pop('generation_mode')
    partial['questions'] = partial['questions'][:10]
    assert validate(partial) == []


@pytest.mark.parametrize('mutation,expected', [
    ('no_records', 'at least 5 verified recent source'),
    ('old_event', '365 days'),
    ('republished_old_event', '365 days'),
    ('future_access', 'between publication and the lock'),
    ('http_url', 'https'),
    ('unverified', 'verified_facts'),
    ('missing_relation', 'current_context.relation'),
    ('outside_knowledge', 'outside_knowledge_required'),
    ('unknown_source', 'no record'),
    ('nothing_fresh', 'last 180 days'),
    ('one_part_only', 'both 第壹部分'),
    ('no_taiwan_hazard', 'Taiwan hazard'),
    ('few_climate', 'climate_energy'),
    ('numbers_without_records', 'recent_item_numbers'),
    ('one_family', 'two unrelated source families'),
    ('lock_missing', 'editorial_lock_date'),
])
def test_each_floor_and_record_defect_is_named(mutation, expected):
    paper = natural_paper()
    plan = paper['metadata']['current_context_plan']
    questions = paper['questions']
    if mutation == 'no_records':
        for q in questions:
            q['item_spec'].pop('current_context', None)
        paper['metadata'].pop('natural_source_ecology_plan')
    elif mutation == 'old_event':
        plan['sources'][1]['event_date'] = plan['sources'][1]['published_at'] = '2025-06-01'
    elif mutation == 'republished_old_event':
        plan['sources'][1]['event_date'] = '2024-08-18'
    elif mutation == 'future_access':
        plan['sources'][1]['accessed_at'] = '2026-09-25'
    elif mutation == 'http_url':
        plan['sources'][1]['canonical_url'] = 'http://example.org/typhoon'
    elif mutation == 'unverified':
        plan['sources'][1]['fact_check_status'] = 'single_source'
    elif mutation == 'missing_relation':
        questions[43]['item_spec']['current_context']['relation'] = ''
    elif mutation == 'outside_knowledge':
        questions[43]['item_spec']['current_context']['outside_knowledge_required'] = True
    elif mutation == 'unknown_source':
        questions[43]['item_spec']['current_context']['source_id'] = 'ghost'
    elif mutation == 'nothing_fresh':
        plan['sources'][1]['event_date'] = plan['sources'][1]['published_at'] = '2026-03-01'
        plan['sources'][4]['event_date'] = plan['sources'][4]['published_at'] = '2026-03-02'
    elif mutation == 'one_part_only':
        for n in (44, 45, 50, 52, 53):
            questions[n - 1]['number'] = n - 36
            questions[n - 37]['number'] = n
    elif mutation == 'no_taiwan_hazard':
        for q in questions:
            tags = q['item_spec'].get('context_tags')
            if tags and 'taiwan' in tags:
                q['item_spec']['context_tags'] = [t for t in tags if t not in {'typhoon', 'earthquake', 'weather_hazard'}]
    elif mutation == 'few_climate':
        questions[29]['item_spec']['context_tags'] = []
    elif mutation == 'numbers_without_records':
        paper['metadata']['natural_source_ecology_plan']['recent_item_numbers'].append(12)
    elif mutation == 'one_family':
        for record in plan['sources']:
            record['source_family'] = 'news'
    elif mutation == 'lock_missing':
        plan.pop('editorial_lock_date')
    errors = validate(paper)
    assert any(expected in e for e in errors), errors


def english_paper():
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 'reading', 'item_spec': {}} for n in range(1, 51)]
    questions += [{'id': 'translation', 'number': None, 'number_display': '中譯英', 'section_id': 'nonselected', 'item_spec': {}},
                  {'id': 'composition', 'number': None, 'number_display': '英文作文', 'section_id': 'nonselected', 'item_spec': {}}]
    for n in (47, 48, 49):
        questions[n - 1]['item_spec']['current_context'] = context('reopening-2026')
    for n in (21, 22, 23):
        questions[n - 1]['item_spec']['current_context'] = context('festival-2026')
    questions[-1]['item_spec']['current_context'] = context('pet-survey-2025', 'current_trend')
    return {'metadata': {'subject': '英文', 'generation_mode': 'full-paper', 'current_context_plan': {
                'editorial_lock_date': LOCK, 'sources': [source('reopening-2026', event='2026-08-01', family='news'),
                                                         source('festival-2026', event='2026-05-01', family='research'),
                                                         source('pet-survey-2025', event='2025-03-01', family='government_data')]}},
            'sections': [{'id': 'reading', 'title': '第壹部分'}, {'id': 'nonselected', 'title': '第貳部分、非選擇題'}],
            'questions': questions}


def test_english_needs_one_recent_passage_and_a_trend_tied_composition():
    assert validate(english_paper()) == []
    paper = english_paper()
    paper['questions'][-1]['item_spec'].pop('current_context')
    assert any('composition' in e for e in validate(paper))
    paper = english_paper()
    paper['questions'][48]['item_spec'].pop('current_context')
    assert any('at least 6 scored items' in e for e in validate(paper))
    paper = english_paper()
    paper['metadata']['current_context_plan']['sources'][2]['event_date'] = '2024-01-01'
    paper['metadata']['current_context_plan']['sources'][2]['published_at'] = '2024-01-01'
    assert any('730 days' in e for e in validate(paper))


def test_chinese_paper_needs_one_recent_group_and_taiwan_passages():
    questions = [{'id': f'q{n}', 'number': n, 'section_id': 's', 'item_spec': {}} for n in range(1, 37)]
    for n in (13, 14, 15):
        questions[n - 1]['item_spec']['current_context'] = context('film-2026')
    for n in (19, 20):
        questions[n - 1]['item_spec']['current_context'] = context('museum-2026')
    questions[3]['item_spec']['context_tags'] = ['taiwan']
    questions[27]['item_spec']['context_tags'] = ['taiwan']
    paper = {'metadata': {'subject': '國綜', 'generation_mode': 'full-paper', 'current_context_plan': {
                 'editorial_lock_date': LOCK, 'sources': [source('film-2026', event='2026-06-20', family='news'),
                                                          source('museum-2026', event='2026-04-10', family='government_data')]}},
             'sections': [{'id': 's', 'title': '第壹部分'}], 'questions': questions}
    assert validate(paper) == []
    thin = copy.deepcopy(paper)
    thin['questions'][27]['item_spec']['context_tags'] = []
    assert any('tagged taiwan' in e for e in validate(thin))


def test_writing_paper_needs_one_trend_tied_task_only():
    tasks = [{'id': 'task-1', 'number': None, 'number_display': '一', 'section_id': 'w', 'item_spec': {
                  'current_context': context('ageing-report', 'current_trend')}},
             {'id': 'task-2', 'number': None, 'number_display': '二', 'section_id': 'w', 'item_spec': {}}]
    paper = {'metadata': {'subject': '國寫', 'generation_mode': 'full-paper', 'current_context_plan': {
                 'editorial_lock_date': LOCK, 'sources': [source('ageing-report', event='2025-11-01', family='government_data')]}},
             'sections': [{'id': 'w', 'title': '非選擇題'}], 'questions': tasks}
    assert validate(paper) == []
    paper['questions'][0]['item_spec'].pop('current_context')
    assert any('current_trend' in e for e in validate(paper))
    assert FLOORS['國寫'] == {'trend_tasks': 1}


def test_one_nobel_prize_and_varied_publishers_and_families():
    paper = natural_paper()
    sources = paper["metadata"]["current_context_plan"]["sources"]
    sources[1]["title"] = "2025 Nobel Prize in Chemistry"
    assert any("Nobel prizes" in e for e in validate(paper))
    paper = natural_paper()
    for record in paper["metadata"]["current_context_plan"]["sources"][:3]:
        record["publisher"] = "NASA"
    assert any("from one publisher" in e for e in validate(paper))
    paper = natural_paper()
    for record in paper["metadata"]["current_context_plan"]["sources"]:
        record["source_family"] = "research"
    assert any("source families" in e for e in validate(paper))


def test_one_event_feeds_one_group():
    paper = natural_paper()
    paper["questions"][29]["item_spec"]["current_context"] = context("typhoon-2026")
    assert any("recent material of 2 different groups" in e for e in validate(paper))
