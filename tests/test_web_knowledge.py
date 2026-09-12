from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_web_knowledge
import build_hosted_web_source_map
import build_hosted_web_template_map
import fetch_hosted_template_assets
import package_skill
import read_web_knowledge
import pytest
import base64
import threading
import pack_verification


def test_web_knowledge_is_deterministic_and_uses_canonical_skill():
    first = build_web_knowledge.build("test")
    second = build_web_knowledge.build("test")
    assert first == second
    assert '<canonical-source path="SKILL.md">' in first
    assert '<canonical-source path="references/web-platform-use.md">' in first
    assert "student question paper" in first
    assert "answer-with-full-solutions paper" in first
    assert "apply it immediately in the same conversation" in first
    assert "do not download any template PDF binaries during setup" in first
    assert "Do not report `0/30` as an installation failure" in first
    assert "source_calibration: embedded_release_verified" in first
    assert "validator_mode: hosted_equivalent" in first
    assert "GitHub Contents API base64 is a valid" in first
    assert "Never download or deliver `github-pages.zip`" in first


def test_checked_in_knowledge_matches_its_canonical_sources():
    path = ROOT / 'web/taiwan-exam-web-knowledge.md'
    saved = path.read_text(encoding='utf-8')
    version = saved.splitlines()[0].removeprefix('# Taiwan Exam Web Knowledge v')
    assert saved == build_web_knowledge.build(version)


def test_web_knowledge_covers_all_current_gsat_subject_blueprints():
    paths = {path.relative_to(ROOT).as_posix() for path in build_web_knowledge.source_paths()}
    for subject in ("國文", "英文", "數學A", "數學B", "社會", "自然"):
        base = f"exam_packs/學測/subjects/{subject}/blueprints"
        assert f"{base}/writer-blueprint.json" in paths
        assert f"{base}/difficulty-profile.json" in paths


def test_hosted_web_source_map_is_complete_current_form_evidence():
    path = ROOT / "exam_packs/學測/metadata/official-current-web-sources.json"
    checked_in = json.loads(path.read_text(encoding="utf-8"))
    sources_present = all((ROOT / d['local_path']).is_file()
                          for s in checked_in['subjects'] for y in s['years']
                          for d in y['documents'].values())
    if sources_present:
        assert checked_in == build_hosted_web_source_map.build()
    else:
        # Public checkouts deliberately omit original PDFs. Projection checks
        # below still run; the actual source-map builder must fail closed.
        with pytest.raises(ValueError, match='Local source failed hash verification'):
            build_hosted_web_source_map.build()
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
            profile = year["paper_profile"]
            registry = ROOT / subject["paper_profile_registry"]
            originals = [json.loads(line) for line in registry.read_text(encoding="utf-8-sig").splitlines() if line]
            assert profile == next(p for p in originals if p["paper_id"] == profile["paper_id"])
            assert any(s["sha256"] == documents["question"]["sha256"] for s in profile["source_files"])
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


def test_extracted_hosted_checker_has_all_runtime_dependencies(tmp_path):
    import read_web_knowledge
    import subprocess
    read_web_knowledge.extract(ROOT/'web/taiwan-exam-web-knowledge.md', subject='數學A', output_dir=tmp_path)
    result = subprocess.run([sys.executable, str(tmp_path/'scripts/check_hosted_run.py'), '--help'],
                            cwd=tmp_path, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert (tmp_path/'exam_packs/學測/metadata/official-current-web-sources.json').is_file()


def test_hosted_template_fetcher_is_packaged_and_embedded(tmp_path):
    script = ROOT / "scripts/fetch_hosted_template_assets.py"
    assert package_skill.should_include(script)
    paths = {path.relative_to(ROOT).as_posix() for path in build_web_knowledge.source_paths()}
    assert "scripts/fetch_hosted_template_assets.py" in paths
    for helper in ("compose_hosted_pdf.py", "inspect_hosted_pdf.py", "check_hosted_run.py",
                   "hosted_item_layout.py", "hosted_run_timing.py", "hosted_blind_review.py"):
        assert "scripts/" + helper in paths
        assert package_skill.should_include(ROOT / "scripts" / helper)
    assert "references/hosted-pdf-production.md" in paths
    assert not package_skill.should_include(ROOT / "scripts/build_template_resource_pdf.py")
    assert not package_skill.should_include(ROOT / "web/taiwan-exam-template-resources.pdf")
    result = fetch_hosted_template_assets.materialize(
        "數學A",
        tmp_path,
        map_path=ROOT / "exam_packs/學測/templates/115/hosted-web-template-assets.json",
        local_root=ROOT,
        timeout=1,
        attempts=1,
    )
    assert result["status"] == "verified"
    assert result["expected"] == result["verified"] == 4
    assert {row["component"] for row in result["assets"]} == {
        "cover-blank", "inner-odd-blank", "inner-even-blank", "formula-blank"
    }
    assert {row["transport"] for row in result["assets"]} == {"local-mirror"}


def test_hosted_web_template_map_covers_exact_fixed_assets():
    path = ROOT / "exam_packs/學測/templates/115/hosted-web-template-assets.json"
    checked_in = json.loads(path.read_text(encoding="utf-8"))
    assert checked_in == build_hosted_web_template_map.build()
    assert checked_in["asset_count"] == 30
    assert len(checked_in["subjects"]) == 7
    assert checked_in["installation_contract"] == {
        "required_subject_count": 7,
        "required_download_url_count": 30,
        "store_all_download_url_records": True,
        "download_pdf_binaries_during_installation": False,
        "download_timing": "after installation, when generation starts for the requested subject",
    }
    assert checked_in["formal_composition"]["exact_binary_base_required"] is True
    assert checked_in["formal_composition"]["template_retypesetting_allowed"] is False
    assert checked_in["formal_composition"]["template_rasterization_allowed"] is False
    assert checked_in["formal_composition"]["persistent_cache_required_for_skill_installation"] is False
    assert checked_in["formal_composition"]["runtime_fetch_scope"] == "requested_subject_production_components_only"
    assert checked_in["formal_composition"]["runtime_asset_count"] == {
        "non_mathematics_subject": 3,
        "mathematics_a_or_b": 4,
    }
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


def test_scoped_extraction_preserves_content_and_all_template_urls(tmp_path):
    knowledge = tmp_path / "knowledge.md"
    knowledge.write_text(build_web_knowledge.build("test"), encoding="utf-8")
    out = tmp_path / "refs"
    result = read_web_knowledge.extract(knowledge, subject="數學A", output_dir=out)
    selected = {row["path"] for row in result["files"]}
    assert result["selected_bytes"] < result["knowledge_bytes"] * 0.8
    assert "references/current-gsat-math-scope.md" in selected
    assert "references/current-gsat-social-form.md" not in selected
    assert not any("/subjects/社會/" in p or "/會考/" in p for p in selected)
    for path in selected:
        assert (out / path).read_text(encoding="utf-8") == (ROOT / path).read_text(encoding="utf-8-sig").rstrip() + "\n"
    manifest = json.loads((out / "exam_packs/學測/templates/115/hosted-web-template-assets.json").read_text(encoding="utf-8"))
    assert sum(len(s["assets"]) for s in manifest["subjects"]) == 30
    # An unchanged reference directory is reusable without overwriting content.
    assert read_web_knowledge.extract(knowledge, subject="數學A", output_dir=out) == result
    (out / "SKILL.md").write_text("user change", encoding="utf-8")
    with pytest.raises(ValueError, match="Preserve existing"):
        read_web_knowledge.extract(knowledge, subject="數學A", output_dir=out)


def test_embedded_checksum_and_safe_paths(tmp_path):
    knowledge = tmp_path / "knowledge.md"
    content = build_web_knowledge.build("test")
    knowledge.write_text(content.replace("# Taiwan Exam Generator\n", "# Changed Skill\n", 1), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        read_web_knowledge.extract(knowledge, paths=["SKILL.md"], output_dir=tmp_path / "out")
    assert not (tmp_path / "out/SKILL.md").exists()
    knowledge.write_text(content.replace('"SKILL.md"', '"../escape.md"'), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsafe"):
        read_web_knowledge.extract(knowledge, subject="數學A")
    assert package_skill.should_include(ROOT / "scripts/read_web_knowledge.py")


def test_template_parallel_partial_resume_and_zero_network_cache(tmp_path, monkeypatch):
    original = fetch_hosted_template_assets.fetch_record
    barrier = threading.Barrier(4)
    calls = []

    def flaky(record, **kwargs):
        calls.append(record["component"])
        barrier.wait(timeout=5)  # Sequential fetching cannot pass this test.
        if record["component"] == "formula-blank":
            raise RuntimeError("simulated timeout")
        return original(record, **kwargs)

    monkeypatch.setattr(fetch_hosted_template_assets, "fetch_record", flaky)
    args = dict(map_path=fetch_hosted_template_assets.DEFAULT_MAP, local_root=ROOT, timeout=1, attempts=1)
    result = fetch_hosted_template_assets.materialize("數學A", tmp_path, **args)
    assert result["status"] == "partial" and result["verified"] == 3
    assert len(result["errors"]) == 1
    calls.clear()

    def recovered(record, **kwargs):
        calls.append(record["component"])
        return original(record, **kwargs)

    monkeypatch.setattr(fetch_hosted_template_assets, "fetch_record", recovered)
    result = fetch_hosted_template_assets.materialize("數學A", tmp_path, **args)
    assert result["status"] == "verified"
    assert calls == ["formula-blank"]
    calls.clear()
    result = fetch_hosted_template_assets.materialize("數學A", tmp_path, **args)
    assert calls == [] and result["verified"] == 4
    corrupted = Path(result["assets"][0]["path"])
    corrupted.write_bytes(b"bad cache")
    result = fetch_hosted_template_assets.materialize("數學A", tmp_path, **args)
    assert result["status"] == "partial" and corrupted.read_bytes() == b"bad cache"


def test_template_api_fallback_decodes_exact_bytes(monkeypatch):
    manifest = json.loads(fetch_hosted_template_assets.DEFAULT_MAP.read_text(encoding="utf-8"))
    record = manifest["subjects"][0]["assets"][0]
    expected = (ROOT / record["repository_path"]).read_bytes()
    calls = []

    def fake_request(url, **kwargs):
        calls.append(url)
        if url == record["download_url"]:
            raise RuntimeError("raw timeout")
        return json.dumps({"encoding": "base64", "content": base64.encodebytes(expected).decode()}).encode()

    monkeypatch.setattr(fetch_hosted_template_assets, "request_bytes", fake_request)
    data, transport = fetch_hosted_template_assets.fetch_record(record, timeout=1, attempts=1, local_root=None)
    fetch_hosted_template_assets.verify(record, data)
    assert data == expected and transport == "github-contents-base64" and len(calls) == 2


def test_hosted_math_a_controlling_structure_is_source_reviewed():
    manifest = json.loads((ROOT / "exam_packs/學測/metadata/official-current-web-sources.json").read_text(encoding="utf-8"))
    year = next(s for s in manifest["subjects"] if s["subject"] == "數學A")["years"][0]
    profile = year["paper_profile"]
    assert year["roc_year"] == 115
    assert pack_verification.paper_errors(profile) == []
    if all((ROOT / s['relative_path']).is_file() for s in profile['source_files']):
        assert pack_verification.paper_errors(profile, ROOT) == []
    review = profile["evidence"]["structure_review"]
    for source in profile["source_files"]:
        assert {p["page"] for p in review["pages"] if p["source_sha256"] == source["sha256"]} == set(range(1, source["page_count"] + 1))
    assert [(s["number"], s["type"], s["score"]) for s in review["slots"][-3:]] == [
        (18, "single_choice", 3), (19, "constructed_response", 4), (20, "constructed_response", 8)
    ]
