"""自然 form bands measured on ROC 111–115: 12–19 多選 in Q1–36, six 3–6-item mixed 題組 each with a 非選, 應選2或3項."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("natural_blocks", HERE / "test_natural_reasoning_and_blocks.py")
BLOCKS = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BLOCKS)

GROUPS = [(37, 39), (40, 43), (44, 46), (47, 49), (50, 53), (54, 56)]


def paper_111_shape():
    """111 shape: 18 單選 + 18 多選 in Q1–36, six mixed 題組 with shared stimuli."""
    paper = BLOCKS._paper()
    contract = paper["metadata"]["natural_choice_form_contract"]
    for q in paper["questions"]:
        n = q["number"]
        if n <= 36 and n % 2 == 0 and q["type"] == "single_choice":
            q["type"] = "multiple_choice"
            q["required_selection_count"] = 2
        if n <= 36 and n % 2 == 1 and q["type"] == "multiple_choice":
            q["type"] = "single_choice"
            q.pop("required_selection_count", None)
        for a, b in GROUPS:
            if a <= n <= b:
                q["group_stimulus"] = f"第{a}至{b}題共用的實驗材料與圖表說明。"
    for a in paper["answers"]:
        q = next(x for x in paper["questions"] if x["id"] == a["question_id"])
        a["final_answer"] = "AB" if q["type"] == "multiple_choice" else ("A" if q["type"] == "single_choice" else "response")
    first = [q for q in paper["questions"] if q["number"] <= 36]
    contract["profile_roc_year"] = 111
    contract["first_part_multiple_choice_count"] = sum(q["type"] == "multiple_choice" for q in first)
    contract["first_part_single_choice_count"] = 36 - contract["first_part_multiple_choice_count"]
    return paper


def test_111_shaped_first_part_and_six_groups_pass(tmp_path):
    paper = paper_111_shape()
    assert paper["metadata"]["natural_choice_form_contract"]["first_part_multiple_choice_count"] == 18
    result = BLOCKS._run(tmp_path, paper)
    assert result.returncode == 0, result.stdout


def test_multiple_choice_count_outside_the_official_band_and_declared_mismatch_are_named(tmp_path):
    paper = paper_111_shape()
    for q in paper["questions"]:
        if q["number"] <= 36 and q["type"] == "multiple_choice" and q["number"] > 12:
            q["type"] = "single_choice"
            q.pop("required_selection_count", None)
    for a in paper["answers"]:
        q = next(x for x in paper["questions"] if x["id"] == a["question_id"])
        if q["type"] == "single_choice":
            a["final_answer"] = "A"
    result = BLOCKS._run(tmp_path, paper)
    assert result.returncode == 1
    assert "12–19" in result.stdout and "official 111–115: 18, 15, 19, 18, 12" in result.stdout
    assert "declares 18 first-part multiple-choice items but the paper has 6" in result.stdout


def test_selection_count_four_and_a_group_without_a_constructed_item_are_rejected(tmp_path):
    paper = paper_111_shape()
    paper["questions"][1]["required_selection_count"] = 4
    paper["answers"][1]["final_answer"] = "ABCD"
    for q in paper["questions"]:
        if 44 <= q["number"] <= 46 and q["type"] == "constructed_response":
            q["type"] = "single_choice"
            q["score"] = 2
            q["options"] = [{"label": l, "text": f"option {l}"} for l in "ABCDE"]
    for a in paper["answers"]:
        q = next(x for x in paper["questions"] if x["id"] == a["question_id"])
        if q["type"] == "single_choice":
            a["final_answer"] = "A"
    result = BLOCKS._run(tmp_path, paper)
    assert result.returncode == 1
    assert "required_selection_count 2 or 3" in result.stdout
    assert "44–46 has no 非選擇題" in result.stdout
