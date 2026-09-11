import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_official_question_queue",
    ROOT / "scripts" / "build_official_question_queue.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_chinese_writing_does_not_inherit_guozong_item_statistics():
    metric = {"difficulty_overall": 5}
    statistics = {(2026, 1): metric}

    assert MODULE.metric_for_profile(
        {"year": 2026, "section": "國寫"}, 1, statistics
    ) is None
    assert MODULE.metric_for_profile(
        {"year": 2026, "section": "國綜"}, 1, statistics
    ) is metric


def test_verified_slots_preserve_split_and_unnumbered_scored_units():
    profile = {
        "structure_status": "verified",
        "numbered_question_count": 1,
        "evidence": {
            "structure_review": {
                "slots": [
                    {"id": "q1a", "number": 1, "type": "guided_writing"},
                    {"id": "q1b", "number": 1, "type": "guided_writing"},
                    {"id": "composition", "number": None, "type": "guided_writing"},
                ]
            }
        },
    }

    assert [item["id"] for item in MODULE.reviewed_items(profile)] == [
        "q1a", "q1b", "composition"
    ]
