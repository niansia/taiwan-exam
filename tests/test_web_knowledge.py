from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_web_knowledge
import package_skill


def test_web_knowledge_is_deterministic_and_uses_canonical_skill():
    first = build_web_knowledge.build("test")
    second = build_web_knowledge.build("test")
    assert first == second
    assert '<canonical-source path="SKILL.md">' in first
    assert '<canonical-source path="references/web-platform-use.md">' in first
    assert "student question paper" in first
    assert "answer-with-full-solutions paper" in first


def test_web_knowledge_covers_all_current_gsat_subject_blueprints():
    paths = {path.relative_to(ROOT).as_posix() for path in build_web_knowledge.source_paths()}
    for subject in ("國文", "英文", "數學A", "數學B", "社會", "自然"):
        base = f"exam_packs/學測/subjects/{subject}/blueprints"
        assert f"{base}/writer-blueprint.json" in paths
        assert f"{base}/difficulty-profile.json" in paths


def test_web_builder_is_maintainer_only_not_skill_payload():
    assert not package_skill.should_include(ROOT / "scripts/build_web_knowledge.py")
    assert not package_skill.should_include(ROOT / "web/taiwan-exam-web-knowledge.md")


def test_web_knowledge_excludes_private_intake_and_security_incident():
    paths = {path.relative_to(ROOT).as_posix() for path in build_web_knowledge.source_paths()}
    assert not any("歷屆試題" in path or "模擬考" in path for path in paths)
    assert "references/security-incident-2026-09-09.md" not in paths
