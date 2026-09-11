from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_web_knowledge
import build_hosted_web_source_map
import build_hosted_web_template_map
import package_skill


def test_web_knowledge_is_deterministic_and_uses_canonical_skill():
    first = build_web_knowledge.build("test")
    second = build_web_knowledge.build("test")
    assert first == second
    assert '<canonical-source path="SKILL.md">' in first
    assert '<canonical-source path="references/web-platform-use.md">' in first
    assert "student question paper" in first
    assert "answer-with-full-solutions paper" in first
    assert "template_asset_installation" in first
    assert "verified: 30" in first


def test_web_knowledge_covers_all_current_gsat_subject_blueprints():
    paths = {path.relative_to(ROOT).as_posix() for path in build_web_knowledge.source_paths()}
    for subject in ("國文", "英文", "數學A", "數學B", "社會", "自然"):
        base = f"exam_packs/學測/subjects/{subject}/blueprints"
        assert f"{base}/writer-blueprint.json" in paths
        assert f"{base}/difficulty-profile.json" in paths


def test_hosted_web_source_map_is_complete_current_form_evidence():
    path = ROOT / "exam_packs/學測/metadata/official-current-web-sources.json"
    checked_in = json.loads(path.read_text(encoding="utf-8"))
    assert checked_in == build_hosted_web_source_map.build()
    assert checked_in["question_pdf_count"] == 35
    assert checked_in["document_count"] == 100
    all_urls = []
    assert {row["subject"] for row in checked_in["subjects"]} == {
        "國綜", "國寫", "英文", "數學A", "數學B", "社會", "自然"
    }
    for subject in checked_in["subjects"]:
        assert [row["roc_year"] for row in subject["years"]] == [115, 114, 113, 112, 111]
        for year in subject["years"]:
            documents = year["documents"]
            assert {"question", "scoring_rule"} <= documents.keys()
            if subject["subject"] != "國寫":
                assert "answer" in documents
            for document in documents.values():
                all_urls.append(document["url"])
                assert document["url"].startswith("https://www.ceec.edu.tw/")
                assert len(document["sha256"]) == 64
                assert document["bytes"] > 0
                assert document["pages"] > 0

    assert len(all_urls) == len(set(all_urls)) == 100

    paths = {path.relative_to(ROOT).as_posix() for path in build_web_knowledge.source_paths()}
    assert "exam_packs/學測/metadata/official-current-web-sources.json" in paths
    built = build_web_knowledge.build("test")
    assert '<canonical-source path="exam_packs/學測/metadata/official-current-web-sources.json">' in built
    assert package_skill.should_include(path)
    assert not package_skill.should_include(ROOT / "scripts/build_hosted_web_source_map.py")


def test_web_builder_is_maintainer_only_not_skill_payload():
    assert not package_skill.should_include(ROOT / "scripts/build_web_knowledge.py")
    assert not package_skill.should_include(ROOT / "web/taiwan-exam-web-knowledge.md")


def test_hosted_web_template_map_covers_exact_fixed_assets():
    path = ROOT / "exam_packs/學測/templates/115/hosted-web-template-assets.json"
    checked_in = json.loads(path.read_text(encoding="utf-8"))
    assert checked_in == build_hosted_web_template_map.build()
    assert checked_in["asset_count"] == 30
    assert len(checked_in["subjects"]) == 7
    assert checked_in["formal_composition"]["exact_binary_base_required"] is True
    assert checked_in["formal_composition"]["template_retypesetting_allowed"] is False
    assert checked_in["formal_composition"]["template_rasterization_allowed"] is False
    assert checked_in["github_template_folder"].startswith("https://github.com/niansia/taiwan-exam/tree/main/")
    all_urls = []
    for subject in checked_in["subjects"]:
        assert subject["github_folder_url"].startswith("https://github.com/niansia/taiwan-exam/tree/main/")
        components = {row["component"] for row in subject["assets"]}
        assert {"blank-template", "cover-blank", "inner-even-blank", "inner-odd-blank"} <= components
        if subject["subject"] in {"數學A", "數學B"}:
            assert "formula-blank" in components
        for asset in subject["assets"]:
            all_urls.append(asset["download_url"])
            assert asset["download_url"].startswith("https://raw.githubusercontent.com/niansia/taiwan-exam/main/")
            assert len(asset["sha256"]) == 64
            assert asset["bytes"] > 1000
            assert asset["pages"] > 0
    assert len(all_urls) == len(set(all_urls)) == 30

    paths = {source.relative_to(ROOT).as_posix() for source in build_web_knowledge.source_paths()}
    assert "exam_packs/學測/templates/115/hosted-web-template-assets.json" in paths
    assert "scripts/gsat_115_templates.py" not in paths
    built = build_web_knowledge.build("test")
    assert '<canonical-source path="exam_packs/學測/templates/115/hosted-web-template-assets.json">' in built
    assert '<canonical-source path="scripts/gsat_115_templates.py">' not in built
    assert package_skill.should_include(path)
    assert not package_skill.should_include(ROOT / "scripts/build_hosted_web_template_map.py")


def test_web_knowledge_excludes_private_intake_and_security_incident():
    paths = {path.relative_to(ROOT).as_posix() for path in build_web_knowledge.source_paths()}
    assert not any("歷屆試題" in path or "模擬考" in path for path in paths)
    assert "references/security-incident-2026-09-09.md" not in paths
