from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import exam_data  # noqa: E402
import build_paper_profiles  # noqa: E402
import ingest_gsat_bundle  # noqa: E402
import package_skill  # noqa: E402
import render_exam  # noqa: E402
import render_gsat_internal_review  # noqa: E402
import render_visual  # noqa: E402
import validate_fixed_page_html  # noqa: E402
import validate_llm_originality_contract  # noqa: E402
import validate_math_difficulty_design  # noqa: E402


class ExamDataTests(unittest.TestCase):
    def test_synthetic_metadata_is_valid(self) -> None:
        record = json.loads((ROOT / "examples" / "synthetic-question.jsonl").read_text(encoding="utf-8"))
        self.assertEqual([], exam_data.validate_record(record, "會考", "數學"))

    def test_invalid_difficulty_is_rejected(self) -> None:
        record = json.loads((ROOT / "examples" / "synthetic-question.jsonl").read_text(encoding="utf-8"))
        record["difficulty"]["overall"] = 7
        self.assertTrue(any("1-5" in error for error in exam_data.validate_record(record)))

    def test_unnumbered_scored_unit_requires_stable_slot_id(self) -> None:
        record = json.loads((ROOT / "examples" / "synthetic-question.jsonl").read_text(encoding="utf-8"))
        record["question_number"] = None
        self.assertTrue(any("scored_slot_id" in error for error in exam_data.validate_record(record)))
        record["scored_slot_id"] = "translation"
        self.assertEqual([], exam_data.validate_record(record))

    def test_unnumbered_scored_units_sort_after_numbered_items(self) -> None:
        numbered = {"year": 2026, "question_number": 50, "question_id": "q50"}
        composition = {
            "year": 2026, "question_number": None, "scored_slot_id": "composition", "question_id": "composition"
        }
        translation = {
            "year": 2026, "question_number": None, "scored_slot_id": "translation", "question_id": "translation"
        }
        ordered = sorted([translation, numbered, composition], key=exam_data.record_order_key)
        self.assertEqual(["q50", "composition", "translation"], [item["question_id"] for item in ordered])

    def test_official_section_titles_match_numbered_metadata_titles(self) -> None:
        self.assertTrue(exam_data.section_labels_match("一、詞彙題（占 10 分）", "詞彙題"))
        self.assertTrue(exam_data.section_labels_match("第貳部分、混合題（占 10 分）", "混合題"))
        self.assertFalse(exam_data.section_labels_match("五、閱讀測驗（占 24 分）", "詞彙題"))

    def test_renderer_produces_print_html(self) -> None:
        exam = json.loads((ROOT / "examples" / "synthetic-exam.json").read_text(encoding="utf-8"))
        rendered = render_exam.render_exam(exam)
        self.assertIn("@page", rendered)
        self.assertIn("答案與詳解", rendered)
        self.assertIn("已獨立驗證", rendered)
        self.assertIn("會考數學版型測試卷", rendered)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "exam.html"
            output.write_text(rendered, encoding="utf-8")
            self.assertGreater(output.stat().st_size, 1000)

    def test_visual_spec_renders_and_embeds_self_contained_svg(self) -> None:
        spec = json.loads((ROOT / "templates" / "visual-spec.json").read_text(encoding="utf-8"))
        svg = render_visual.render(spec)
        self.assertIn("<svg", svg)
        self.assertIn("<polyline", svg)
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            asset = base / "graph.svg"
            asset.write_text(svg, encoding="utf-8")
            exam = json.loads((ROOT / "examples" / "synthetic-exam.json").read_text(encoding="utf-8"))
            exam["questions"][0]["visual_asset"] = {
                "path": "graph.svg",
                "alt": spec["alt_text"],
                "caption": "圖一",
                "width_percent": 65,
                "placement": "after_prompt",
                "visual_spec": spec,
            }
            rendered = render_exam.render_exam(exam, asset_base=base)
            self.assertIn("data:image/svg+xml;base64,", rendered)
            self.assertIn("圖一", rendered)

    def test_requires_diagram_needs_visual_spec(self) -> None:
        record = json.loads((ROOT / "examples" / "synthetic-question.jsonl").read_text(encoding="utf-8"))
        record["requires_diagram"] = True
        self.assertTrue(any("visual spec" in error for error in exam_data.validate_record(record)))

    def test_full_paper_renderer_requires_verified_layout(self) -> None:
        exam = json.loads((ROOT / "examples" / "synthetic-exam.json").read_text(encoding="utf-8"))
        exam["metadata"].update(
            {
                "generation_mode": "full-paper",
                "paper_profile_id": "test-paper",
                "expected_question_count": 2,
                "expected_section_counts": {"choice": 1, "constructed": 1},
                "expected_section_scores": {"choice": 1, "constructed": 3},
            }
        )
        errors = render_exam.validate_exam(exam)
        self.assertTrue(any("layout_profile" in error for error in errors))
        self.assertTrue(any("layout_fidelity_status" in error for error in errors))
        exam["metadata"]["layout_profile"] = "verified-test-layout"
        exam["metadata"]["layout_fidelity_status"] = "verified"
        self.assertFalse(any("layout" in error for error in render_exam.validate_exam(exam)))

    def test_current_math_mixed_items_reject_workbook_answer_lines(self) -> None:
        exam = {
            "metadata": {"paper_subject": "數學A", "layout_contract_version": 3},
            "sections": [{"id": "mixed", "title": "混合題或非選擇題"}],
            "questions": [
                {"number": 19, "section_id": "mixed", "answer_space_lines": 3},
                {"number": 20, "section_id": "mixed"},
            ],
        }
        errors = render_gsat_internal_review.current_math_layout_errors(exam)
        self.assertEqual(1, len(errors))
        self.assertIn("第 19 題", errors[0])

    def test_fixed_page_horizontal_overflow_is_a_hard_failure(self) -> None:
        pages = [{"overflowPx": 0, "horizontalOverflowPx": 12, "clipped": []}]
        validate_fixed_page_html._finalize_pages(pages)
        self.assertEqual("fail", pages[0]["status"])

    def test_math_difficulty_gate_scales_irreducible_decisions_by_target_p(self) -> None:
        self.assertEqual(2, validate_math_difficulty_design.required_decisions(0.78, 1, "single_choice"))
        self.assertEqual(3, validate_math_difficulty_design.required_decisions(0.41, 3, "single_choice"))
        self.assertEqual(3, validate_math_difficulty_design.required_decisions(0.25, 15, "fill_in"))
        self.assertEqual(4, validate_math_difficulty_design.required_decisions(0.18, 16, "fill_in"))
        self.assertEqual(4, validate_math_difficulty_design.required_decisions(None, 20, "constructed_response"))

    def test_empirical_p_target_maps_to_local_descriptive_level(self) -> None:
        self.assertEqual(1, exam_data.overall_from_target_p(0.84))
        self.assertEqual(3, exam_data.overall_from_target_p(0.50))
        self.assertEqual(5, exam_data.overall_from_target_p(0.12))

    def test_math_a_counting_depth_contract_is_documented(self) -> None:
        reference = (ROOT / "references" / "math-difficulty-design.md").read_text(encoding="utf-8")
        self.assertIn("D-10-3", reference)
        self.assertIn("three genuinely linked decisions", reference)
        validator = (ROOT / "scripts" / "validate_math_difficulty_design.py").read_text(encoding="utf-8")
        self.assertIn("counting/combinatorics item", validator)

    def test_blueprint_and_plan_integration(self) -> None:
        base = json.loads((ROOT / "examples" / "synthetic-question.jsonl").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subject = root / "exam_packs" / "會考" / "subjects" / "數學"
            (subject / "metadata").mkdir(parents=True)
            (subject / "subject.json").write_text(
                json.dumps({"id": "math", "name": "數學", "sections": ["選擇題"], "domains": []}, ensure_ascii=False),
                encoding="utf-8",
            )
            (root / "exam_packs" / "會考" / "manifest.json").write_text(
                json.dumps(
                    {
                        "id": "cap",
                        "name": "國中教育會考",
                        "folder": "會考",
                        "pack_version": "0.1.0",
                        "schema_version": 1,
                        "subjects": ["數學"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            records = []
            for index in range(30):
                record = json.loads(json.dumps(base, ensure_ascii=False))
                record["year"] = 2021 + (index % 5)
                record["question_id"] = f"integration-{index:02d}"
                record["question_number"] = index % 6 + 1
                record["literacy"] = {"classification": "basic", "stimulus_required": False}
                records.append(record)
            (subject / "metadata" / "questions.jsonl").write_text(
                "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
                encoding="utf-8",
            )
            self.assertEqual(0, exam_data.build_blueprints(root))
            blueprint = json.loads((subject / "blueprints" / "learned-blueprint.json").read_text(encoding="utf-8"))
            self.assertEqual("ready", blueprint["calibration_by_curriculum"]["108"]["status"])
            plan_path = root / "plan.json"
            self.assertEqual(
                0,
                exam_data.generate_plan(root, "會考", "數學", 5, 7, "108", None, [], plan_path, False),
            )
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual("historically-calibrated", plan["calibration_level"])
            self.assertEqual(5, len(plan["items"]))
            self.assertTrue(all("source_pattern_ids" not in item for item in plan["items"]))
            self.assertTrue(all(item["originality_contract"]["writer_source_visibility"] == "aggregate-only" for item in plan["items"]))
            self.assertTrue(all(item["current_form_cluster_id"].startswith("aggregate-") for item in plan["items"]))

            paper = {
                "paper_id": "cap-2026-test-paper",
                "exam": "會考",
                "year": 2026,
                "subject": "數學",
                "section": None,
                "curriculum": "108",
                "regime": "108課綱",
                "publisher": None,
                "bundle": None,
                "source_kind": "reference_paper",
                "source_files": [{
                    "sha256": "0" * 64,
                    "relative_path": "test.pdf",
                    "role": "question",
                    "page_count": 1,
                }],
                "duration_minutes": 30,
                "total_score": 5,
                "numbered_question_count": 5,
                "scored_item_count": 5,
                "structure_status": "auto_parsed",
                "sections": [{
                    "id": "choice",
                    "title": "選擇題",
                    "order": 1,
                    "question_number_start": 1,
                    "question_number_end": 5,
                    "numbered_question_count": 5,
                    "scored_item_count": 5,
                    "group_count": None,
                    "question_type_mix": {"single_choice": 5},
                    "subtotal_score": 5,
                    "score_rule": "每題 1 分",
                    "instructions_pattern": None,
                }],
                "layout": {"paper_size": "A4", "columns": 1, "answer_sheet_mode": "題卷分開"},
                "evidence": {"method": "text_layer_parse", "confidence": 0.95, "notes": None, "reviewed_at": None},
            }
            (subject / "metadata" / "papers.jsonl").write_text(
                json.dumps(paper, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            full_path = root / "full-plan.json"
            with self.assertRaises(ValueError):
                exam_data.generate_plan(
                    root, "會考", "數學", None, 9, "108", None, [], full_path, False,
                    True, "cap-2026-test-paper", None,
                )
            self.assertFalse(full_path.exists())

    def test_legacy_hard_coded_generators_are_not_packaged(self) -> None:
        for name in package_skill.REJECTED_GENERATOR_SCRIPTS:
            self.assertFalse(package_skill.should_include(ROOT / "scripts" / name))
        for name in package_skill.SOURCE_LEVEL_METADATA:
            self.assertFalse(package_skill.should_include(ROOT / "exam_packs" / "學測" / "metadata" / name))
        self.assertFalse(
            package_skill.should_include(
                ROOT / "exam_packs" / "學測" / "metadata" / "bundle-analyses" / "115-e2.json"
            )
        )
        self.assertTrue(
            package_skill.should_include(
                ROOT / "exam_packs" / "學測" / "shared-data" / "current-math-form-writer-profile.json"
            )
        )
        for name in (
            "validate_english_difficulty_design.py",
            "validate_visual_item_contract.py",
        ):
            self.assertTrue(package_skill.should_include(ROOT / "scripts" / name))

    def test_packaged_paper_profiles_preserve_source_bindings(self) -> None:
        path = ROOT / "exam_packs" / "學測" / "subjects" / "英文" / "metadata" / "papers.jsonl"
        rows = [
            json.loads(line)
            for line in package_skill.packaged_data(path).decode("utf-8").splitlines()
            if line.strip()
        ]
        local_rows, errors = exam_data.read_jsonl(path)
        self.assertFalse(errors)
        self.assertEqual(local_rows, rows)
        self.assertTrue(any(row["source_kind"] == "mock_exam" for row in rows))
        self.assertTrue(all(row["source_files"][0]["relative_path"] != "official-source-withheld.pdf" for row in rows))

    def test_current_english_distinguishes_numbered_and_scored_items(self) -> None:
        result = build_paper_profiles.official_current_structure(115, "英文", "英文")
        self.assertIsNotNone(result)
        numbered, scored, sections, total_score = result
        self.assertEqual(50, numbered)
        self.assertEqual(53, scored)
        self.assertEqual(100, total_score)
        mixed = next(section for section in sections if section["title"] == "混合題")
        self.assertEqual(4, mixed["numbered_question_count"])
        self.assertEqual(4, mixed["scored_item_count"])
        constructed = [section for section in sections if section["title"] in {"中譯英", "英文作文"}]
        self.assertTrue(all(section["numbered_question_count"] is None for section in constructed))
        self.assertEqual([2, 1], [section['scored_item_count'] for section in constructed])

    def test_public_english_profile_has_bound_review_but_requires_local_sources(self) -> None:
        subject_path = ROOT / "exam_packs" / "學測" / "subjects" / "英文"
        profiles, errors = exam_data.read_jsonl(subject_path / "metadata" / "papers.jsonl")
        self.assertFalse(errors)
        profile = next(
            row for row in profiles
            if row.get("year") == 2026 and row.get("source_kind") == "official_past_exam"
        )
        import pack_verification
        self.assertEqual("verified", profile["structure_status"])
        self.assertFalse(pack_verification.paper_errors(profile))
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(any('reference unavailable' in error for error in pack_verification.paper_errors(profile, Path(directory))))

    def test_bundle_registry_merge_is_hash_idempotent(self) -> None:
        existing = [{"sha256": "a" * 64, "destination_relative_path": "old.pdf", "year": 2025}]
        duplicate = [{"sha256": "a" * 64, "destination_relative_path": "duplicate.pdf", "year": 2026}]
        added = [{"sha256": "b" * 64, "destination_relative_path": "new.pdf", "year": 2026}]
        merged = ingest_gsat_bundle.merge_registry(existing, duplicate + added)
        self.assertEqual(2, len(merged))
        self.assertEqual({"a" * 64, "b" * 64}, {row["sha256"] for row in merged})

    def test_old_mock_bundle_name_is_recognized(self) -> None:
        metadata = ingest_gsat_bundle.bundle_metadata("104學年度全國模考試題03(南一版)")
        self.assertEqual(104, metadata["roc_year"])
        self.assertEqual("N3", metadata["series"])
        self.assertEqual("南一", metadata["publisher"])
        self.assertEqual("全模", metadata["scope"])

    def test_short_subject_tokens_and_q_a_suffixes_are_recognized(self) -> None:
        self.assertEqual(
            ("英文", "英文", "path-token"),
            ingest_gsat_bundle.classify_subject(Path("某套卷/第一次模擬考_題目英.pdf")),
        )
        self.assertEqual("question", ingest_gsat_bundle.classify_role(Path("某套卷/英文考科_Q.pdf")))
        self.assertEqual("solution", ingest_gsat_bundle.classify_role(Path("某套卷/英文考科_A.pdf")))

    def test_bundle_resolution_does_not_cross_publishers(self) -> None:
        existing = [{
            "roc_year": 111,
            "series": "N1",
            "publisher": "南一",
            "scope": "全模",
            "bundle": "111-N1 全模 (南一)",
        }]
        metadata = ingest_gsat_bundle.resolve_bundle_metadata(
            Path("111學年度全國模考試題01(翰林版)/數學A.pdf"),
            existing,
            None,
            None,
            None,
        )
        self.assertEqual("翰林", metadata["publisher"])
        self.assertNotEqual("111-N1 全模 (南一)", metadata["bundle"])

    def test_originality_contract_rejects_placeholder_or_missing_record(self) -> None:
        missing = {"number": 1, "item_spec": {}}
        self.assertTrue(validate_llm_originality_contract.validate_item(missing))
        placeholder = json.loads((ROOT / "templates" / "llm-originality-record.json").read_text(encoding="utf-8"))
        item = {"number": 1, "item_spec": {"originality_record": placeholder}}
        errors = validate_llm_originality_contract.validate_item(item)
        self.assertTrue(any("has not passed" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
