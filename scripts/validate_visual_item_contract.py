#!/usr/bin/env python3
"""Validate answer-bearing visual coverage, specifications, assets, and placement.

The floors below are conservative internal full-paper release floors.  They are
not presented as CEEC item-count statistics; a selected, fully annotated paper
profile may declare a stricter subject/year envelope in metadata.visual_contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


PROVISIONAL_FLOORS = {
    "數學A": {"count": 4, "sections": 3, "kinds": 2},
    "數學B": {"count": 4, "sections": 3, "kinds": 2},
    "自然": {"count": 8, "sections": 2, "kinds": 4, "domains": 4, "sourced_photos": 2},
    "社會": {"count": 6, "sections": 2, "kinds": 3, "domains": 3, "sourced_photos": 2},
    "英文": {"count": 3, "sections": 2, "kinds": 2, "sourced_photos": 1},
}

REQUIRED_CHECKS = {
    "semantic_consistency",
    "label_consistency",
    "answer_not_leaked",
    "grayscale_legibility",
    "grayscale_evidence_survival",
    "color_independence",
    "print_legibility",
    "accessibility_text_safe",
    "rights_verified",
}
REQUIRED_ROLES = {"evidence", "required_for_solution"}
ALLOWED_RIGHTS = {"original", "licensed", "public_domain", "user_authorized"}
REQUIRED_SPEC_FIELDS = {
    "kind", "role", "generation_mode", "information_density",
    "visual_reasoning_steps", "precision", "alt_text", "difficulty_basis",
    "validation_checks",
}
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
GRAPH_TOPOLOGY_KINDS = {
    "coordinate_graph", "bar_chart", "line_chart", "scatter_plot", "profile_diagram",
    "energy_profile", "spectrum",
}
RELATIONAL_TOPOLOGY_KINDS = {
    "map", "cross_section", "schematic", "pedigree", "gel", "flowchart",
    "measurement_diagram", "evidence_matrix", "evidence_network",
}


def _svg_primitives(path: Path) -> set[str]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return set()
    return {node.tag.rsplit("}", 1)[-1] for node in root.iter()}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _as_positive_int(value: Any, fallback: int) -> int:
    return value if isinstance(value, int) and value > 0 else fallback


def validate_exam(exam: dict[str, Any], asset_root: Path) -> dict[str, Any]:
    metadata = exam.get("metadata") or {}
    subject = metadata.get("paper_subject") or metadata.get("subject")
    full_paper = metadata.get("generation_mode") == "full-paper"
    configured = metadata.get("visual_contract") or {}
    floor = PROVISIONAL_FLOORS.get(str(subject), {})
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    sections: set[str] = set()
    kinds: Counter[str] = Counter()
    domains: set[str] = set()
    sourced_photos = 0

    for question in exam.get("questions") or []:
        asset = question.get("visual_asset")
        if not asset:
            continue
        number = question.get("number", "?")
        spec = asset.get("visual_spec") if isinstance(asset, dict) else None
        if not isinstance(spec, dict):
            errors.append(f"Q{number}: visual_asset lacks visual_spec")
            continue
        missing_fields = sorted(field for field in REQUIRED_SPEC_FIELDS if spec.get(field) in (None, ""))
        if missing_fields:
            errors.append(f"Q{number}: visual_spec fields missing: {', '.join(missing_fields)}")
        role = spec.get("role")
        if role not in REQUIRED_ROLES:
            errors.append(f"Q{number}: visual is decorative/context-only and cannot count")
            continue
        item_spec = question.get("item_spec") or {}
        if item_spec.get("requires_diagram") is not True:
            errors.append(f"Q{number}: answer-bearing visual requires item_spec.requires_diagram=true")
        if item_spec.get("stimulus_required") is not True or item_spec.get("stimulus_removal_test") != "fail_without_stimulus":
            errors.append(f"Q{number}: visual-removal test is missing or does not fail")
        if not spec.get("answer_bearing_features"):
            errors.append(f"Q{number}: answer-bearing features are not enumerated")
        if spec.get("color_dependency") is not False:
            errors.append(f"Q{number}: visual depends on color")
        if spec.get("answer_evidence_survives_grayscale") is not True:
            errors.append(f"Q{number}: grayscale evidence survival is not confirmed")
        review = spec.get("grayscale_review") or {}
        if review.get("status") != "pass" or not review.get("evidence_notes"):
            errors.append(f"Q{number}: final-size grayscale review has not passed")
        checks = set(spec.get("validation_checks") or [])
        missing_checks = sorted(REQUIRED_CHECKS - checks)
        if missing_checks:
            errors.append(f"Q{number}: visual checks missing: {', '.join(missing_checks)}")
        if spec.get("source_rights") not in ALLOWED_RIGHTS:
            errors.append(f"Q{number}: source rights are absent or unverified")
        if spec.get("generation_mode") == "licensed_source":
            for field in (
                "source_url", "source_creator", "license_or_authorization", "crop_description",
                "source_asset_path", "source_asset_sha256", "processing_steps",
            ):
                if not spec.get(field):
                    errors.append(f"Q{number}: licensed visual lacks {field}")
        path = asset_root / str(asset.get("path") or "")
        if not path.is_file():
            errors.append(f"Q{number}: visual asset is missing")
        elif asset.get("sha256") != _sha256(path):
            errors.append(f"Q{number}: visual asset hash is missing or stale")
        kind = str(spec.get("kind") or "missing")
        measured_natural = (
            str(subject) == "自然" and int(metadata.get("layout_contract_version") or 0) >= 5
        )
        if measured_natural and kind != "photo":
            representation = spec.get("representation_audit") or {}
            for field in ("topology_family", "rendered_primitives", "semantic_channels", "reviewer", "reviewed_at"):
                if not representation.get(field):
                    errors.append(f"Q{number}: representation_audit lacks {field}")
            if representation.get("declared_kind_matches_topology") is not True:
                errors.append(f"Q{number}: declared visual kind has not been matched to rendered topology")
            if representation.get("verbatim_prompt_redundancy") is not False:
                errors.append(f"Q{number}: figure duplicates prompt evidence or lacks a non-redundancy review")
            if representation.get("removal_changes_answerability") is not True:
                errors.append(f"Q{number}: removing the figure does not change answerability")
            if kind == "data_table":
                if not representation.get("table_justification"):
                    errors.append(f"Q{number}: data table lacks a cross-cell use justification")
                if len(representation.get("comparison_dimensions") or []) < 2:
                    errors.append(f"Q{number}: data table is a one-dimensional label list, not a genuine table")
            if path.suffix.lower() == ".svg" and path.is_file():
                primitives = _svg_primitives(path)
                nontext = primitives - {"svg", "g", "defs", "style", "title", "desc", "text", "tspan", "rect"}
                if kind in GRAPH_TOPOLOGY_KINDS and not ({"line", "polyline", "path"} & primitives):
                    errors.append(f"Q{number}: {kind} SVG has no plotted axis/line/path topology")
                if kind in RELATIONAL_TOPOLOGY_KINDS and len(nontext & {"line", "polyline", "path", "circle", "ellipse", "polygon"}) < 1:
                    errors.append(f"Q{number}: {kind} SVG is only a bordered label panel")
        if kind == "photo":
            if spec.get("generation_mode") != "licensed_source":
                errors.append(f"Q{number}: counted real photograph must use a traceable licensed_source record")
            elif path.suffix.lower() not in PHOTO_EXTENSIONS:
                errors.append(f"Q{number}: sourced photograph is not a raster image")
            else:
                sourced_photos += 1
            if asset.get("grayscale") is not True or spec.get("tonal_transform") not in {"grayscale", "bilevel"}:
                errors.append(f"Q{number}: sourced photograph is not a fixed monochrome asset")
            if not isinstance(spec.get("min_raster_dpi"), int) or spec["min_raster_dpi"] < 200:
                errors.append(f"Q{number}: sourced photograph must document at least 200 effective print dpi")
            source_path = asset_root / str(spec.get("source_asset_path") or "")
            if not source_path.is_file():
                errors.append(f"Q{number}: original source photograph is missing")
            elif spec.get("source_asset_sha256") != _sha256(source_path):
                errors.append(f"Q{number}: original source photograph hash is missing or stale")
        section = str(question.get("section_id") or "missing")
        domain = str(item_spec.get("domain") or question.get("domain") or "")
        kinds[kind] += 1
        sections.add(section)
        if domain:
            domains.add(domain)
        rows.append({"number": number, "section": section, "kind": kind, "domain": domain, "role": role})

    if full_paper and floor:
        minimum_count = _as_positive_int(configured.get("minimum_required_visuals"), floor["count"])
        minimum_sections = _as_positive_int(configured.get("minimum_sections"), floor["sections"])
        minimum_kinds = _as_positive_int(configured.get("minimum_kinds"), floor["kinds"])
        if len(rows) < minimum_count:
            errors.append(f"paper: {len(rows)} required visuals, minimum is {minimum_count}")
        if len(sections) < minimum_sections:
            errors.append(f"paper: visuals occur in {len(sections)} sections, minimum is {minimum_sections}")
        if len(kinds) < minimum_kinds:
            errors.append(f"paper: {len(kinds)} visual kinds, minimum is {minimum_kinds}")
        if floor.get("domains"):
            minimum_domains = _as_positive_int(configured.get("minimum_domains"), floor["domains"])
            if len(domains) < minimum_domains:
                errors.append(f"paper: visuals cover {len(domains)} subject domains, minimum is {minimum_domains}")
        if floor.get("sourced_photos"):
            minimum_photos = _as_positive_int(
                configured.get("minimum_sourced_photos"), floor["sourced_photos"]
            )
            if sourced_photos < minimum_photos:
                errors.append(
                    f"paper: {sourced_photos} traceable real-photo items, minimum is {minimum_photos}"
                )

    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "subject": subject,
        "required_visual_count": len(rows),
        "section_count": len(sections),
        "kind_counts": dict(kinds),
        "sourced_photo_count": sourced_photos,
        "sourced_photo_minimum": (
            _as_positive_int(configured.get("minimum_sourced_photos"), floor["sourced_photos"])
            if full_paper and floor.get("sourced_photos")
            else None
        ),
        "sourced_photo_upper_bound": None,
        "domains": sorted(domains),
        "items": rows,
        "errors": errors,
        "notes": [
            "Counts include only evidence/required-for-solution visuals with a completed visual-removal test.",
            "Default floors are conservative internal release floors, not claimed official item-count statistics.",
            "Photo floors count only traceable raster photographs/observation images, not generated photorealism or decorative pictures.",
            "The photo threshold is a minimum only. Natural Science and Social Studies have no photo-count upper bound; every additional photo must still be answer-bearing and pass all provenance, rights, grayscale, density, and timing checks.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exam_json", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam_json.read_text(encoding="utf-8-sig"))
    report = validate_exam(exam, args.exam_json.parent)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
