#!/usr/bin/env python3
"""Build a shareable Skill archive without copyrighted/private source papers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
from validate_attribution import validate as validate_attribution


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_TOP_LEVEL = {".git", ".github", ".playwright-cli", ".pytest_cache", "dist", "downloads", "maintenance", "output", "tests", "tmp"}
PRIVATE_INTAKE_DIRS = {"歷屆試題", "模擬考", "format-references", "answer-profiles", "official-statistics", "命題範圍"}
KEEP_IN_PRIVATE_DIRS = {
    "放資料到這裡.md",
    "放格式範例到這裡.md",
    "放詳解格式到這裡.md",
    "放命題範圍到這裡.md",
}
REJECTED_GENERATOR_SCRIPTS = {
    "build_gsat_stress_suite_116.py",
    "self_test_chinese_natural_v2.py",
    "qa_gsat_stress_suite_116.py",
    "build_gsat_full_set.py",
    "build_gsat_internal_review_set.py",
    "build_gsat_math_gate_v3.py",
    "build_gsat_math_visual_gate_v4.py",
    "build_gsat_math_originality_gate_v5.py",
    "build_mathA_third_paper.py",
    "build_gsat_pilot_set.py",
    "build_gsat_chinese_natural_v2.py",
    "prepare_chinese_natural_layout_revision.py",
}
SOURCE_LEVEL_METADATA = {
    "learned-blueprint.json",
    "questions.jsonl",
    "questions.auto.jsonl",
    "question-review-queue.jsonl",
    "official-question-review-queue.jsonl",
    "official-item-statistics.jsonl",
    "source-registry.jsonl",
    "source-index.jsonl",
    "official-source-registry.jsonl",
    "official-download-catalog.jsonl",
    "official-statistics-catalog.jsonl",
    "official-statistics-registry.jsonl",
    "visual-annotation-queue.csv",
    "visual-source-index.jsonl",
    "layout-review-queue.jsonl",
    "recent-math-form-analysis.json",
    "mock-dataset-audit.json",
}
PRIVATE_REPORTS = {
    "gsat-calibration-audit-2026-09-04.md",
    "english-social-corpus-audit-2026-09-05.md",
    "gsat-writing-source-ecology-audit-2026-09-05.md",
}

# Reviewed reusable tools only. New batch/question generators must not enter a
# distribution merely because their filename is absent from a legacy denylist.
DISTRIBUTABLE_SCRIPTS = set('''
analyze_current_chinese_natural_form.py analyze_gsat_official_patterns.py
analyze_historical_content.py analyze_mock_bundle.py analyze_mock_exam_dataset.py
analyze_pdf_visuals.py analyze_recent_math_form.py analyze_stimulus_ecology.py
analyze_writing_source_corpus.py audit_corpus_overlap.py audit_item_originality.py
audit_source_novelty.py audit_exam_pack.py audit_generated_suite.py
build_gsat_difficulty_profiles.py build_layout_review_queue.py
build_official_question_queue.py build_paper_profiles.py build_pdf_contact_sheets.py
build_question_candidates.py build_visual_queue.py download_ceec_gsat_statistics.py
download_ceec_gsat.py exam_data.py import_ceec_gsat_difficulty.py ingest_gsat_bundle.py
pack_verification.py pdf_provenance.py
qa_math_current_form.py safe_rendering.py
render_exam.py render_gsat_internal_review_pdf.py render_gsat_internal_review.py
render_gsat_official_pdf.py render_gsat_official.py render_pdf.py render_visual.py
gsat_115_templates.py render_gsat_template_assets.py
summarize_four_band_reference.py validate_attribution.py
validate_chinese_natural_scope.py validate_current_form_density.py
validate_english_difficulty_design.py
validate_english_layout_contract.py validate_english_vocabulary_scope.py
validate_fixed_page_html.py validate_inspiration_pool.py
validate_llm_originality_contract.py validate_math_curriculum.py
validate_math_difficulty_design.py validate_paper_difficulty_balance.py
validate_reference_page_density.py validate_rendered_paper.py
validate_social_item_design.py validate_source_grounding.py
validate_svg_text_geometry.py validate_visual_item_contract.py
validate_writing_source_grounding.py
validate_exam_release.py validate_exam_pack_contract.py
'''.split())


def should_include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if not rel.parts or rel.parts[0] in EXCLUDED_TOP_LEVEL or rel.parts[0].startswith("drive-download"):
        return False
    if rel.name == "PACKAGE_MANIFEST.json" or rel.name == ".env" or rel.name.startswith(".env."):
        return False
    if any(part == "__pycache__" for part in rel.parts):
        return False
    if any(part in {".secrets", "secrets"} for part in rel.parts):
        return False
    if path.suffix.lower() in {".key", ".p12", ".pfx"} or path.name.lower().endswith((".private.pem", "-private.pem")):
        return False
    if path.suffix.lower() == ".pem" and b"PRIVATE KEY-----" in path.read_bytes():
        return False
    if path.suffix.lower() in {".pyc", ".pyo"}:
        return False
    if rel.parts[0] == "docs" and rel.name in PRIVATE_REPORTS:
        return False
    if len(rel.parts) == 2 and rel.parts[0] == "scripts" and rel.name in REJECTED_GENERATOR_SCRIPTS:
        return False
    if rel.parts[0] == 'scripts' and (len(rel.parts) != 2 or rel.name not in DISTRIBUTABLE_SCRIPTS):
        return False
    if rel.parts[0] == "exam_packs" and rel.name in SOURCE_LEVEL_METADATA:
        return False
    if rel.parts[0] == "exam_packs" and "bundle-analyses" in rel.parts:
        return False

    for index, part in enumerate(rel.parts[:-1]):
        if part in PRIVATE_INTAKE_DIRS:
            return index == len(rel.parts) - 2 and rel.name in KEEP_IN_PRIVATE_DIRS
    return True


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_publication_open(root: Path) -> None:
    state = json.loads((root / 'SOFTWARE_RELEASE_STATUS.json').read_text(encoding='utf-8'))
    resolution = state.get('resolution') or {}
    if (state.get('status') != 'ready' or not resolution.get('reference')
            or resolution.get('kind') not in {'vendor-decision', 'reviewed-code-fix'}):
        raise ValueError('Software distribution is suspended pending incident resolution; file scans alone cannot reopen it')


def write_deterministic(zf: ZipFile, arcname: str, data: bytes) -> None:
    info = ZipInfo(arcname, date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, data)


def packaged_data(path: Path) -> bytes:
    """Strip source-level provenance from distributable Paper Profiles."""
    if path.name != "papers.jsonl" or "exam_packs" not in path.parts:
        return path.read_bytes()
    profiles = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    public_profiles = []
    for profile in profiles:
        if profile.get("source_kind") != "official_past_exam":
            continue
        identity = {
            "exam": profile.get("exam"),
            "year": profile.get("year"),
            "subject": profile.get("subject"),
            "section": profile.get("section"),
            "sections": profile.get("sections"),
        }
        public_id = hashlib.sha256(
            json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:12]
        cleaned = dict(profile)
        # A distribution without its private reference PDFs cannot inherit a
        # local verified claim. Keep aggregate records for discovery/review.
        cleaned['structure_status'] = 'needs_review'
        cleaned['evidence'] = dict(profile.get('evidence') or {})
        cleaned['evidence'].pop('structure_review', None)
        cleaned['evidence']['confidence'] = min(cleaned['evidence'].get('confidence', 0), 0.8)
        cleaned['evidence']['notes'] = 'Reference-only distribution; original sources withheld. Reconcile local PDFs and obtain a new page/slot review before full-paper use.'
        cleaned["paper_id"] = f"official-profile-{profile.get('year')}-{public_id}"
        cleaned["source_files"] = [{
            "sha256": "0" * 64,
            "relative_path": "official-source-withheld.pdf",
            "role": "question",
            "page_count": (profile.get("layout") or {}).get("target_page_count"),
        }]
        public_profiles.append(cleaned)
    return "".join(
        json.dumps(profile, ensure_ascii=False) + "\n" for profile in public_profiles
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="0.6.0-preview.3")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--public-release", action="store_true", help="Also require confirmed licensing declarations; does not publish anything")
    parser.add_argument('--source-url', help='Actual stable public HTTPS download URL; required for public-release checks')
    args = parser.parse_args()

    if args.public_release:
        try:
            require_publication_open(ROOT)
            from scan_skill_release import validate_source_url
            validate_source_url(args.source_url)
        except (OSError, ValueError) as exc:
            print(json.dumps({'error': str(exc), 'status': 'publication-blocked'}, ensure_ascii=False))
            return 2

    attribution = validate_attribution(ROOT, public_release=args.public_release)
    if attribution["status"] != "pass":
        print(json.dumps({"error": "Attribution check failed", "details": attribution}, ensure_ascii=False, indent=2))
        return 2

    output = args.output or ROOT / "dist" / f"taiwan-exam-generator-skill-v{args.version}.zip"
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(
        path for path in ROOT.rglob("*") if path.is_file() and should_include(path)
    )
    entries = []
    archive_root = "taiwan-exam-generator"

    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            data = packaged_data(path)
            rel = path.relative_to(ROOT).as_posix()
            write_deterministic(zf, f"{archive_root}/{rel}", data)
            entries.append({"path": rel, "bytes": len(data), "sha256": sha256(data)})

        manifest = {
            "name": "taiwan-exam-generator",
            "version": args.version,
            "schema_version": 1,
            "distribution_status": "release-candidate-not-published" if args.public_release else "internal-review",
            "origin": attribution["origin"],
            "attribution_check": {"status": "pass", "scope": attribution["scope"], "notice_sha256": attribution["notice_sha256"], "warnings": attribution["warnings"]},
            "exam_acceptance": "not-established-by-packager",
            "contains_original_exam_files": False,
            "file_count": len(entries),
            "files": entries,
        }
        write_deterministic(
            zf,
            f"{archive_root}/PACKAGE_MANIFEST.json",
            (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )

    if args.public_release:
        from scan_skill_release import scan_release
        report = scan_release(output, source_url=args.source_url)
        output.with_suffix('.security.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if report['status'] != 'pass':
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2
    print(json.dumps({"archive": str(output), **manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
