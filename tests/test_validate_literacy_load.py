"""The reading-load gate must reject a collapsed paper and accept a current-form one."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_literacy_load.py"
SHARED = ROOT / "exam_packs" / "學測" / "shared-data"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_literacy_load", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROSE = (
    "研究團隊在同一測站連續記錄兩項指標，並與鄰近對照樣區的同期資料比較。"
    "觀測期間的儀器校正紀錄、取樣頻率與環境條件都一併登載，用以判斷差異"
    "是否來自量測誤差。依據下列圖表與說明回答各題。"
)


def prose(length: int, salt: str) -> str:
    """Distinct stimulus text of a requested length; groups must not merge."""
    body = salt + "：" + PROSE * (length // len(PROSE) + 2)
    return body[:length]


def natural_paper(
    *,
    part_1_groups: int,
    part_1_items_per_group: int,
    part_2_stimulus_chars: int,
    cross_discipline: int,
    standalone_prompt_chars: int = 150,
    option_chars: int = 40,
) -> dict:
    disciplines = ["物理", "化學", "生物", "地科"]
    questions = []
    number = 1
    # 第壹部分: grouped items first, then standalone items to 36.
    for index in range(part_1_groups):
        stimulus = prose(220, f"甲{index}")
        for _ in range(part_1_items_per_group):
            questions.append({
                "id": f"q{number}", "number": number, "section_id": "section-1",
                "type": "single_choice", "score": 2,
                "group_stimulus": stimulus,
                "prompt": prose(standalone_prompt_chars, f"乙{number}"),
                "options": [{"label": letter, "text": prose(option_chars, f"丙{number}{letter}")} for letter in "ABCDE"],
                "item_spec": {"domain": disciplines[index % 4]},
            })
            number += 1
    while number <= 36:
        questions.append({
            "id": f"q{number}", "number": number, "section_id": "section-1",
            "type": "single_choice", "score": 2,
            "prompt": prose(standalone_prompt_chars, f"丁{number}"),
            "options": [{"label": letter, "text": prose(option_chars, f"戊{number}{letter}")} for letter in "ABCDE"],
            "item_spec": {"domain": disciplines[(number - 1) % 4]},
        })
        number += 1

    designs = []
    for index in range(6):
        stimulus = prose(part_2_stimulus_chars, f"己{index}")
        crossing = index < cross_discipline
        primary = disciplines[index % 4]
        second = disciplines[(index + 1) % 4]
        for offset in range(3):
            questions.append({
                "id": f"q{number}", "number": number, "section_id": "section-2",
                "type": "single_choice" if offset < 2 else "constructed_response", "score": 2,
                "group_stimulus": stimulus,
                "prompt": prose(standalone_prompt_chars, f"庚{number}"),
                "options": [{"label": letter, "text": prose(option_chars, f"辛{number}{letter}")} for letter in "ABCDE"],
                "item_spec": {"domain": second if (crossing and offset == 2) else primary},
            })
            number += 1
        if crossing:
            # Only cross-disciplinary groups are declared; that is the field's
            # existing convention in validate_chinese_natural_scope.py.
            designs.append({
                "question_numbers": [number - 3, number - 2, number - 1],
                "required_domains": [primary, second],
                "second_discipline_removable": False,
                "evidence_bridge": f"{primary}的量測值決定{second}的判斷條件，刪去後無法作答。",
            })

    return {
        "metadata": {
            "title": "測試卷", "exam": "學測", "subject": "自然",
            "calibration_level": "historically-calibrated",
            "natural_mixed_group_designs": designs,
        },
        "instructions": [],
        "sections": [
            {"id": "section-1", "title": "第壹部分、選擇題"},
            {"id": "section-2", "title": "第貳部分、混合題或非選擇題"},
        ],
        "questions": questions,
    }


def run(tmp_path: Path, exam: dict, subject: str) -> dict:
    path = tmp_path / "exam.json"
    path.write_text(json.dumps(exam, ensure_ascii=False), encoding="utf-8")
    report = tmp_path / "report.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--subject", subject, "--report", str(report)],
        capture_output=True, check=False,
    )
    return json.loads(report.read_text(encoding="utf-8"))


def test_current_form_natural_paper_passes(tmp_path):
    exam = natural_paper(
        part_1_groups=4, part_1_items_per_group=2,
        part_2_stimulus_chars=300, cross_discipline=4,
    )
    report = run(tmp_path, exam, "自然")
    assert report["status"] == "pass", report["errors"]


def test_standalone_items_and_thin_stimulus_are_rejected(tmp_path):
    """The shape of the reviewed ROC 116 draft: no 第壹部分 題組, 80-character groups."""
    exam = natural_paper(
        part_1_groups=0, part_1_items_per_group=0,
        part_2_stimulus_chars=80, cross_discipline=0,
        standalone_prompt_chars=40, option_chars=8,
    )
    report = run(tmp_path, exam, "自然")
    assert report["status"] == "fail"
    joined = " | ".join(report["errors"])
    assert "第壹部分 has 0 題組" in joined
    assert "stimulus median" in joined
    assert "substantive characters" in joined


def test_single_discipline_mixed_groups_are_rejected(tmp_path):
    exam = natural_paper(
        part_1_groups=4, part_1_items_per_group=2,
        part_2_stimulus_chars=300, cross_discipline=1,
    )
    report = run(tmp_path, exam, "自然")
    assert report["status"] == "fail"
    assert any("cross-disciplinary" in error for error in report["errors"])


def test_declared_crossing_needs_a_second_domain_on_the_items(tmp_path):
    """A declaration alone never establishes a cross-disciplinary group."""
    exam = natural_paper(
        part_1_groups=4, part_1_items_per_group=2,
        part_2_stimulus_chars=300, cross_discipline=4,
    )
    for question in exam["questions"]:
        spec = question.get("item_spec") or {}
        if question["section_id"] == "section-2":
            spec["domain"] = "物理"
    report = run(tmp_path, exam, "自然")
    assert report["status"] == "fail"
    assert any("every subpart records " in error for error in report["errors"])


def test_floors_sit_below_every_official_year():
    """A floor that would reject an official paper is miscalibrated.

    The comparison must use the item-content basis, not the whole booklet: this
    gate reads the exam record, which never holds the cover page or the section
    說明 blocks.
    """
    module = load_module()
    envelope = json.loads((SHARED / "current-form-literacy-envelope.json").read_text(encoding="utf-8"))
    measured = {row["subject"]: row for row in envelope["subjects"]}
    for subject, floors in module.SUBJECT_FLOORS.items():
        papers = measured[subject]["papers"]
        if floors["unit"] == "chars":
            weakest = min(p["item_content_compact_chars"] for p in papers)
            assert floors["min_paper_chars"] < weakest, subject
            assert floors["official_weakest"] == weakest, subject
        else:
            weakest = min(p["item_content_english_words"] for p in papers)
            assert floors["min_paper_words"] < weakest, subject
            assert floors["official_weakest"] == weakest, subject


def test_writing_task_floors_sit_below_every_official_year():
    module = load_module()
    envelope = json.loads((SHARED / "current-form-literacy-envelope.json").read_text(encoding="utf-8"))
    papers = {row["subject"]: row for row in envelope["subjects"]}["國寫"]["papers"]
    floors = module.SUBJECT_FLOORS["國寫"]
    assert floors["min_task_1_chars"] < min(p["task_1_compact_chars"] for p in papers)
    assert floors["min_task_2_chars"] < min(p["task_2_compact_chars"] for p in papers)


@pytest.mark.parametrize("subject", ["自然", "社會"])
def test_group_floors_do_not_exceed_measured_medians(subject):
    module = load_module()
    envelope = json.loads((SHARED / "current-form-literacy-envelope.json").read_text(encoding="utf-8"))
    measured = {row["subject"]: row for row in envelope["subjects"]}[subject]
    floors = module.SUBJECT_FLOORS[subject]
    key = "part_2_stimulus_median" if subject == "自然" else "group_stimulus_median"
    observed = measured["part_2_group_stimulus_chars"]["median"]
    assert floors[key] < observed


def test_cross_discipline_floor_matches_the_weakest_official_year():
    """The floor is bound to CEEC's own 合科 count, not the wider maintainer reading."""
    module = load_module()
    record = json.loads((SHARED / "natural-mixed-group-cross-discipline.json").read_text(encoding="utf-8"))
    floor = module.SUBJECT_FLOORS["自然"]["min_cross_discipline_groups"]
    for year in record["years"]:
        declared = [g for g in year["groups"] if g.get("ceec_declared")]
        assert len(declared) == year["ceec_declared_cross_discipline_groups"]
        assert all(g["cross_discipline"] for g in declared)
        assert floor <= year["ceec_declared_cross_discipline_groups"] <= year["cross_discipline_groups"]
    assert record["summary"]["release_floor"] == floor


def writing_paper(task_1_chars: int, task_2_chars: int, subparts: int = 2) -> dict:
    questions = []
    for index, size in enumerate((task_1_chars, task_2_chars), start=1):
        packet = prose(size, f"任務{index}")
        for part in range(subparts):
            questions.append({
                "id": f"w{index}-{part}", "number": len(questions) + 1,
                "section_id": "non-selected", "type": "constructed_response", "score": 25,
                "group_stimulus": packet,
                "prompt": prose(60, f"問{index}{part}"),
            })
    return {
        "metadata": {"title": "國寫", "exam": "學測", "subject": "國寫",
                     "calibration_level": "historically-calibrated"},
        "instructions": [],
        "sections": [{"id": "non-selected", "title": "非選擇題"}],
        "questions": questions,
    }


def test_writing_paper_with_two_real_packets_passes(tmp_path):
    report = run(tmp_path, writing_paper(900, 500), "國寫")
    assert report["status"] == "pass", report["errors"]


def test_one_task_packet_cannot_satisfy_both_writing_floors(tmp_path):
    """Counting the two largest questions would let task one's packet count twice."""
    exam = writing_paper(900, 500)
    shared = exam["questions"][0]["group_stimulus"]
    for question in exam["questions"]:
        question["group_stimulus"] = shared
    report = run(tmp_path, exam, "國寫")
    assert report["status"] == "fail"
    assert any("distinct packet" in error for error in report["errors"])


def test_short_second_writing_packet_is_rejected(tmp_path):
    report = run(tmp_path, writing_paper(900, 120), "國寫")
    assert report["status"] == "fail"
    assert any("shorter 國寫 packet" in error for error in report["errors"])
