import hashlib
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "visual_contract", ROOT / "scripts" / "validate_visual_item_contract.py"
)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


def visual_question(tmp_path: Path, number: int, section: str, kind: str, domain: str = ""):
    asset = tmp_path / f"q{number}.svg"
    asset.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
    return {
        "number": number,
        "section_id": section,
        "visual_asset": {
            "path": asset.name,
            "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
            "visual_spec": {
                "kind": kind,
                "role": "required_for_solution",
                "generation_mode": "deterministic_svg",
                "information_density": 3,
                "visual_reasoning_steps": 2,
                "precision": "data_exact",
                "alt_text": "Exact labels and relations in a test diagram.",
                "difficulty_basis": "expert_review",
                "answer_bearing_features": ["exact labels"],
                "color_dependency": False,
                "answer_evidence_survives_grayscale": True,
                "grayscale_review": {"status": "pass", "evidence_notes": "black lines and labels remain distinct"},
                "source_rights": "original",
                "validation_checks": sorted(module.REQUIRED_CHECKS),
            },
        },
        "item_spec": {
            "domain": domain,
            "requires_diagram": True,
            "stimulus_required": True,
            "stimulus_removal_test": "fail_without_stimulus",
        },
    }


def sourced_photo_question(tmp_path: Path, number: int, section: str, domain: str = ""):
    q = visual_question(tmp_path, number, section, "photo", domain)
    processed = tmp_path / f"q{number}.jpg"
    original = tmp_path / f"q{number}-source.jpg"
    processed.write_bytes(b"processed grayscale photo fixture")
    original.write_bytes(b"original color photo fixture")
    q["visual_asset"].update({
        "path": processed.name,
        "sha256": hashlib.sha256(processed.read_bytes()).hexdigest(),
        "grayscale": True,
    })
    q["visual_asset"]["visual_spec"].update({
        "generation_mode": "licensed_source",
        "tonal_transform": "grayscale",
        "source_rights": "public_domain",
        "source_url": "https://example.invalid/archive/photo",
        "source_creator": "public archive",
        "license_or_authorization": "public domain fixture",
        "source_asset_path": original.name,
        "source_asset_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        "crop_description": "fixed test crop",
        "processing_steps": ["crop", "grayscale"],
        "min_raster_dpi": 300,
    })
    return q


def test_full_math_floor_passes(tmp_path):
    questions = [
        visual_question(tmp_path, 1, "s1", "statistical_chart"),
        visual_question(tmp_path, 2, "s2", "coordinate_graph"),
        visual_question(tmp_path, 3, "s3", "coordinate_graph"),
        visual_question(tmp_path, 4, "s3", "data_table"),
    ]
    exam = {"metadata": {"subject": "數學B", "generation_mode": "full-paper"}, "questions": questions}
    assert module.validate_exam(exam, tmp_path)["status"] == "pass"


def test_decorative_visual_does_not_count(tmp_path):
    q = visual_question(tmp_path, 1, "s1", "photo")
    q["visual_asset"]["visual_spec"]["role"] = "decorative"
    exam = {"metadata": {"subject": "英文", "generation_mode": "full-paper"}, "questions": [q]}
    report = module.validate_exam(exam, tmp_path)
    assert report["status"] == "fail"
    assert any("decorative" in error for error in report["errors"])


def test_natural_requires_domain_spread(tmp_path):
    kinds = ["circuit", "experimental_setup", "biological_illustration", "map"] * 2
    questions = [visual_question(tmp_path, n, "s1" if n < 5 else "s2", kind, "物理") for n, kind in enumerate(kinds, 1)]
    exam = {"metadata": {"subject": "自然", "generation_mode": "full-paper"}, "questions": questions}
    report = module.validate_exam(exam, tmp_path)
    assert report["status"] == "fail"
    assert any("subject domains" in error for error in report["errors"])


def test_changed_asset_hash_fails(tmp_path):
    q = visual_question(tmp_path, 1, "s1", "data_table")
    q["visual_asset"]["sha256"] = "0" * 64
    exam = {"metadata": {"subject": "英文", "generation_mode": "custom-practice"}, "questions": [q]}
    report = module.validate_exam(exam, tmp_path)
    assert any("hash" in error for error in report["errors"])


def test_natural_full_paper_requires_two_real_photo_items(tmp_path):
    domains = ["物理", "化學", "生物", "地科"] * 2
    kinds = ["circuit", "experimental_setup", "biological_illustration", "map"] * 2
    questions = [
        sourced_photo_question(tmp_path, 1, "s1", domains[0]),
        *[
            visual_question(tmp_path, number, "s1" if number < 5 else "s2", kinds[number - 1], domains[number - 1])
            for number in range(2, 9)
        ],
    ]
    report = module.validate_exam(
        {"metadata": {"subject": "自然", "generation_mode": "full-paper"}, "questions": questions},
        tmp_path,
    )
    assert report["sourced_photo_count"] == 1
    assert any("real-photo items" in error for error in report["errors"])


def test_social_photo_floor_has_no_upper_bound(tmp_path):
    domains = ["歷史", "地理", "公民", "歷史", "地理", "公民"]
    questions = [
        sourced_photo_question(tmp_path, number, "objective" if number <= 3 else "mixed", domain)
        for number, domain in enumerate(domains, 1)
    ]
    questions[4]["visual_asset"]["visual_spec"]["kind"] = "map"
    questions[5]["visual_asset"]["visual_spec"]["kind"] = "data_table"
    report = module.validate_exam(
        {"metadata": {"subject": "社會", "generation_mode": "full-paper"}, "questions": questions},
        tmp_path,
    )
    assert report["status"] == "pass"
    assert report["sourced_photo_count"] == 4
    assert report["sourced_photo_minimum"] == 2
    assert report["sourced_photo_upper_bound"] is None


def test_english_full_paper_accepts_one_traceable_photo(tmp_path):
    questions = [
        sourced_photo_question(tmp_path, 1, "reading"),
        visual_question(tmp_path, 2, "mixed", "data_table"),
        visual_question(tmp_path, 3, "mixed", "statistical_chart"),
    ]
    report = module.validate_exam(
        {"metadata": {"subject": "英文", "generation_mode": "full-paper"}, "questions": questions},
        tmp_path,
    )
    assert report["status"] == "pass"
