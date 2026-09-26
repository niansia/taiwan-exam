"""The 社會 run checklist states the floors the gates enforce: a hosted run read 「four real photos」
there after the floor fell to two, and asked the user for four licensed photographs."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from prepare_hosted_run import authoring_requirements
from validate_social_item_design import FRESH_MIN, WITHIN_YEAR_MIN
from validate_visual_item_contract import PROVISIONAL_FLOORS

WORDS = {2: 'two', 3: 'three', 4: 'four', 5: 'five', 10: 'ten', 18: '18'}


def test_social_checklist_states_the_enforced_floors():
    text = ' '.join(authoring_requirements('社會'))
    floor = PROVISIONAL_FLOORS['社會']
    assert f'at least {WORDS[floor["sourced_photos"]]} real photographs' in text
    assert f'{WORDS[floor["count"]]} answer-bearing visuals' in text
    assert f'{floor["visual_items"]} items that cite' in text
    assert f'{WORDS[WITHIN_YEAR_MIN]} within-year items' in text and f'{WORDS[FRESH_MIN]} within 180 days' in text
    assert 'four real photos' not in text and 'no license needed' in text


def test_no_reference_asks_for_four_photographs_or_a_license():
    social = (ROOT / 'references' / 'current-gsat-social-form.md').read_text(encoding='utf-8')
    skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
    assert 'four-photo release floor' not in social and 'three or four photographs' not in social
    assert 'must be original, public-domain, licensed, or explicitly user-authorized' not in skill


def test_natural_checklist_states_the_enforced_photo_floor():
    text = ' '.join(authoring_requirements('自然'))
    floor = PROVISIONAL_FLOORS['自然']
    assert f'{floor["count"]} answer-bearing visuals with at least one real photograph' in text and floor['sourced_photos'] == 1
    assert '3 real photos' not in text and 'no license needed' in text
