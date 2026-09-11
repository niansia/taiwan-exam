import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_math_curriculum.py"


def _paper():
    questions = []
    for index in range(20):
        context = "dated-source" if index < 5 else ("pure-math" if index < 10 else "neutral-application")
        topic = f"topic-{index}"
        code = "G-10-2"
        if index == 0:
            topic, code = "combinatorics", "D-10-3"
        elif index == 1:
            topic, code = "sequence", "N-10-6"
        elif index == 2:
            topic, code = "sphere-coordinate", "G-11B-4"
        questions.append({
            "id": f"q{index + 1}",
            "prompt": "solve",
            "options": [],
            "item_spec": {
                "scope_codes": [code],
                "scope_status": "direct",
                "context_class": context,
                "topic_family": topic,
                "originality_record": {"curriculum_reduction": {"mapped_operations": ["compare distances"]}},
            },
        })
        if index == 2:
            questions[-1]["item_spec"]["math_b_sphere_application"] = {
                "application_family": "route_comparison",
                "direct_coordinate_conversion_only": False,
                "requires_comparison_or_constraint": True,
                "reasoning_operations": ["convert endpoints", "derive route lengths", "compare constraints"],
            }
    strands = [
        "number_and_algebra", "functions_and_models", "geometry_and_space",
        "data_and_statistics", "counting_and_probability",
    ]
    bands = {}
    for strand_index, strand in enumerate(strands):
        start = strand_index * 4 + 1
        bands[strand] = {"minimum": 2, "maximum": 6, "question_ids": [f"q{i}" for i in range(start, start + 4)]}
    return {
        "metadata": {
            "subject": "數學B",
            "content_distribution_plan": {"strand_bands": bands},
            "math_b_distinctive_rotation": {
                "suite_window_size": 3,
                "this_form_mechanisms": {"latitude_longitude_to_sphere_coordinate": ["q3"]},
                "audit_status": "pass",
            },
        },
        "questions": questions,
    }


def _run(tmp_path, paper):
    path = tmp_path / "exam.json"
    path.write_text(json.dumps(paper), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)


def test_math_b_balanced_blueprint_passes(tmp_path):
    result = _run(tmp_path, _paper())
    assert result.returncode == 0, result.stdout + result.stderr


def test_math_b_rejects_counting_concentration(tmp_path):
    paper = _paper()
    for question in paper["questions"][:3]:
        question["item_spec"]["scope_codes"] = ["D-10-3"]
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "counting-and-combinatorics concentration exceeds 2" in result.stdout


def test_math_b_rejects_direct_coordinate_conversion_sphere_item(tmp_path):
    paper = _paper()
    paper["questions"][2]["item_spec"]["math_b_sphere_application"] = {
        "application_family": "coordinate_conversion",
        "direct_coordinate_conversion_only": True,
        "requires_comparison_or_constraint": False,
        "reasoning_operations": ["substitute latitude", "substitute longitude"],
    }
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "sphere item must assess distance, route comparison, or navigation constraints" in result.stdout
