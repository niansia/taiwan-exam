import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_chinese_natural_scope.py"
sys.path.insert(0, str(ROOT / "scripts"))
from render_gsat_internal_review import _natural_cover, _question


def _innovation(subject, number):
    return {
        "subject": subject,
        "mechanism_family": f"{subject}-evidence-mechanism-{number % 7}",
        "candidate_competition_linked": True,
        "routine_template_recoverable": False,
        "surface_or_topic_novelty_only": False,
        "new_subject_mechanism": "two observations constrain competing models before the final curriculum inference",
        "evidence_or_reasoning_architecture": "compare observations, reject one model, apply the curriculum relation, and check consistency",
        "nearest_neighbor_difference": f"item {number}'s nearest neighbor uses one observation and direct substitution without competing-model elimination",
        "reviewer_decision": "pass-subject-novelty",
    }


def _paper_innovation_review(subject):
    return {
        "subject": subject,
        "all_scored_items_reviewed": True,
        "mechanism_saturation_review": "pass: repeated mechanisms were screened across the paper",
        "representation_saturation_review": "pass: evidence and visual roles were compared",
        "section_or_domain_diversity_review": "pass: all sections and domains were reviewed",
        "reviewer_decision": "pass-subject-novelty",
    }


CODE_PREFIX = {"物理": "P", "化學": "C", "生物": "B", "地科": "E"}


def _content_code(domain, number):
    """Rotate 主題 letters so each discipline covers several chapters, as the official booklets do."""
    return f"{CODE_PREFIX[domain]}{'ABCD'[(number // 4 + number) % 4]}a-Vc-1"


SPEC_CODES = " ".join(sorted({f"{prefix}{letter}a-Vc-1" for prefix in CODE_PREFIX.values() for letter in "ABCD"} | {"pa-Ⅴc-2"}))


def _paper(interleaved=False):
    order = ["物理", "化學", "生物", "地科"]
    first_multiple = {7, 8, 9, 11, 12, 23, 25, 26, 27, 31, 32, 35}
    mixed_multiple = {37, 39, 44, 45, 48, 52}
    mixed_constructed = {38, 41, 42, 46, 49, 50, 53, 54}
    questions = []
    answers = []
    for number in range(1, 57):
        if number <= 36:
            domain = order[((number - 1) % 4) if interleaved else ((number - 1) // 9)]
        else:
            domain = order[(number - 37) % 4]
        if number in first_multiple or number in mixed_multiple:
            question_type = "multiple_choice"
        elif number in mixed_constructed:
            question_type = "constructed_response"
        else:
            question_type = "single_choice"
        question_id = f"q{number}"
        questions.append({
            "id": question_id, "number": number,
            "section_id": "section-1" if number <= 36 else "section-2",
            "type": question_type,
            "score": 4 if question_type == "constructed_response" else 2,
            "prompt": "根據題內資料判斷下列敘述。",
            "options": [] if question_type == "constructed_response" else [
                {"label": label, "text": f"option {label}"} for label in "ABCDE"
            ],
            **({"required_selection_count": 2} if question_type == "multiple_choice" else {}),
            "item_spec": {
                "domain": domain,
                "curriculum_codes": [_content_code(domain, number), "pa-Ⅴc-2"],
                "subject_innovation_audit": _innovation("自然", number),
                "difficulty_design": {"band": "中"},
                "natural_reasoning_contract": {
                    "recall_only": False,
                    "direct_formula_substitution_only": False,
                    "core_curriculum_anchor": "evidence-based model reasoning",
                    "curriculum_centrality": "core",
                    "reasoning_operations": ["compare evidence", "control a variable", "evaluate a model"],
                    "material_or_model_dependency": "removing the experiment removes the tested relation",
                },
            },
        })
        answers.append({"question_id": question_id, "final_answer": "AB" if question_type == "multiple_choice" else ("A" if question_type == "single_choice" else "response")})
    return {
        "metadata": {
            "paper_subject": "自然",
            "reference_year": 2026,
            "layout_contract_version": 5,
            "subject_innovation_review": _paper_innovation_review("自然"),
            "natural_objective_block_order": order,
            "natural_choice_form_contract": {
                "profile_roc_year": 115,
                "first_part_score": 72,
                "first_part_item_score": 2,
                "first_part_single_choice_count": 24,
                "first_part_multiple_choice_count": 12,
                "mixed_part_single_choice_count": 6,
                "mixed_part_multiple_choice_count": 6,
                "mixed_part_constructed_response_count": 8,
                "option_labels": ["A", "B", "C", "D", "E"],
                "multiple_selection_cue": "（應選n項）",
                "cover_scoring_rules": ["single_choice_all_or_zero", "multiple_choice_n_minus_2k_over_n"],
            },
            "natural_source_ecology_plan": {
                "mode": "current-affairs-emphasis",
                "as_of_date": "2026-09-10",
                "editorial_lock_date": "2026-09-03",
                "recent_window_months": 12,
                "recent_item_numbers": [1, 10, 19, 28, 37, 38],
                "recent_source_groups": ["group-a", "group-b", "group-c", "group-d"],
                "older_dated_source_policy": "stratified random sampling across years and source families",
                "balance_note": "recency is spread across domains and both paper parts",
            },
        },
        "sections": [
            {"id": "section-1", "title": "第壹部分、選擇題（占72分）", "instructions": ["說明：第1題至第36題，含單選題及多選題，每題2分。"]},
            {"id": "section-2", "title": "第貳部分、混合題或非選擇題（占56分）", "instructions": []},
        ],
        "questions": questions,
        "answers": answers,
    }


def _run(tmp_path, paper):
    path = tmp_path / "exam.json"
    spec_path = tmp_path / "science-spec.txt"
    path.write_text(json.dumps(paper, ensure_ascii=False), encoding="utf-8")
    spec_path.write_text(SPEC_CODES, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--science-spec", str(spec_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def test_natural_rejects_interleaved_objective_disciplines(tmp_path):
    result = _run(tmp_path, _paper(interleaved=True))
    assert result.returncode == 1
    assert "interleaved or not in nine-item blocks" in result.stdout


def test_natural_rejects_definition_recall_contract(tmp_path):
    paper = _paper()
    paper["questions"][0]["item_spec"]["natural_reasoning_contract"]["recall_only"] = True
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "pure definition/recall has not been rejected" in result.stdout


def test_declared_cross_discipline_group_with_bridge_passes(tmp_path):
    paper = _paper()
    paper["metadata"]["natural_mixed_group_designs"] = [{
        "question_numbers": [37, 38],
        "required_domains": ["物理", "化學"],
        "evidence_bridge": "機械能輸出必須和電池反應所接收的能量共同檢核。",
    }]
    result = _run(tmp_path, paper)
    assert result.returncode == 0, result.stdout + result.stderr


def test_declared_cross_discipline_group_rejects_cosmetic_domain(tmp_path):
    paper = _paper()
    paper["metadata"]["natural_mixed_group_designs"] = [{
        "question_numbers": [37], "required_domains": ["物理"], "evidence_bridge": ""
    }]
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "at least two valid domains" in result.stdout
    assert "evidence bridge missing" in result.stdout


def test_full_natural_requires_current_affairs_ecology_plan(tmp_path):
    paper = _paper()
    del paper["metadata"]["natural_source_ecology_plan"]
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "requires natural_source_ecology_plan" in result.stdout


def test_natural_current_affairs_must_span_domains_and_paper_parts(tmp_path):
    paper = _paper()
    paper["metadata"]["natural_source_ecology_plan"]["recent_item_numbers"] = [1, 2, 3, 4, 5, 6]
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "span at least 3 science disciplines" in result.stdout
    assert "both selected and mixed-response parts" in result.stdout


def test_natural_multiple_choice_cue_must_match_verified_key(tmp_path):
    paper = _paper()
    paper["questions"][6]["required_selection_count"] = 3
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "cue disagrees with verified key" in result.stdout


def test_natural_renderer_prints_selection_count_and_full_cover_rules(tmp_path):
    paper = _paper()
    q7 = paper["questions"][6]
    rendered = _question(q7, "自然", tmp_path, False, False, None)
    assert "（應選2項）" in rendered
    assert "(A)" in rendered and "(E)" in rendered
    cover = _natural_cover({"cover_year_title": "116學年度學科能力測驗模擬試題"})
    assert "單選題：" in cover
    assert "多選題：" in cover
    assert "得分低於零分" in cover


def test_natural_rejects_surface_only_novelty_claim(tmp_path):
    paper = _paper()
    paper["questions"][0]["item_spec"]["subject_innovation_audit"]["surface_or_topic_novelty_only"] = True
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "surface/topic-only novelty has not been rejected" in result.stdout


def _chinese_paper():
    codes = ["A1", "B1", "B2", "B3", "B4", "B5"]
    return {
        "metadata": {
            "paper_subject": "國綜",
            "generation_mode": "full-paper",
            "subject_innovation_review": _paper_innovation_review("國綜"),
        },
        "questions": [
            {
                "id": f"q{number}",
                "number": number,
                "score": 2,
                "item_spec": {
                    "curriculum_codes": [codes[(number - 1) % len(codes)]],
                    "subject_innovation_audit": _innovation("國綜", number),
                    "difficulty_design": {"band": "中"},
                    "chinese_reasoning_contract": {
                        "recall_or_definition_only": False,
                        "single_cue_recognition_only": False,
                        "reasoning_operations": [
                            "locate the governing clause",
                            "compare two speakers' stances",
                            "test the inference against the later turn",
                        ],
                        "textual_evidence_span": "第二段末至第三段首",
                        "material_dependency": "刪去對照段落後無法判定立場轉折",
                    },
                },
            }
            for number in range(1, 31)
        ],
    }


def test_complete_chinese_paper_accepts_subject_innovation_contract(tmp_path):
    result = _run(tmp_path, _chinese_paper())
    assert result.returncode == 0, result.stdout + result.stderr


def test_chinese_source_novelty_cannot_replace_item_innovation_audit(tmp_path):
    paper = _chinese_paper()
    del paper["questions"][0]["item_spec"]["subject_innovation_audit"]
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "Q1: missing subject_innovation_audit" in result.stdout


def test_chinese_definition_recall_contract_is_rejected(tmp_path):
    """國綜 had no per-item reasoning floor; a recall item could pass scope review."""
    paper = _chinese_paper()
    paper["questions"][0]["item_spec"]["chinese_reasoning_contract"]["recall_or_definition_only"] = True
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "definition or vocabulary recall has not been rejected" in result.stdout


def test_chinese_medium_band_needs_three_reasoning_operations(tmp_path):
    paper = _chinese_paper()
    contract = paper["questions"][0]["item_spec"]["chinese_reasoning_contract"]
    contract["reasoning_operations"] = contract["reasoning_operations"][:2]
    result = _run(tmp_path, paper)
    assert result.returncode == 1
    assert "only 2 reasoning operations; require 3" in result.stdout


def test_mixed_group_record_shape_is_shared_with_the_literacy_gate(tmp_path):
    """One declaration must satisfy both gates; two record shapes would be a trap."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "validate_literacy_load", ROOT / "scripts" / "validate_literacy_load.py"
    )
    literacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(literacy)

    design = {
        "question_numbers": [37, 38],
        "required_domains": ["物理", "化學"],
        "evidence_bridge": "機械能輸出必須和電池反應所接收的能量共同檢核。",
        "second_discipline_removable": False,
    }
    paper = _paper()
    paper["metadata"]["natural_mixed_group_designs"] = [design]
    assert _run(tmp_path, paper).returncode == 0

    groups = [{
        "part": 2, "numbers": [37, 38], "group": "37-38",
        "domains": ["化學", "物理"], "secondary_domains": [],
        "stimulus_compact_chars": 300, "items": 2,
    }]
    errors, qualifying = literacy.cross_discipline_errors(
        {"metadata": {"natural_mixed_group_designs": [design]}}, groups, floor=1
    )
    assert errors == [] and qualifying == 1
