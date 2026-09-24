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
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


PROVISIONAL_FLOORS = {
    "數學A": {"count": 4, "sections": 3, "kinds": 2},
    "數學B": {"count": 4, "sections": 3, "kinds": 2},
    # Official 111-115 booklets label 21-36 (自然) and 8-17 (社會) distinct figures/tables
    # and mention photographs 3-7 times a year (社會); a paper at the old floor of 6-8
    # visuals looked like a text worksheet. Floors sit below the weakest official year.
    # 自然 111-115: 16-28 labelled 圖 and 4-12 表 a year, almost all drawn graphs, apparatus and
    # tables; real photographs are 0-2 a year (115: a mitosis micrograph panel and a rock).
    "自然": {"count": 16, "sections": 2, "kinds": 4, "domains": 4, "sourced_photos": 1},
    # 社會 111-115 measured (2026-09-24): 2-4 photographs or archival images a year (112 poster,
    # land deed, aerial photo; 113 temple photos, statuette; 114 cave photo, two cartoons; 115
    # murals, satellite image, aerial panel, Bamiyan) beside 7-13 charts, maps and tables, and
    # 18-45 items that cite a 圖/表/照片. A four-photo floor sat above two official years and
    # made hosted runs stall on downloads while text-only items multiplied.
    "社會": {"count": 10, "sections": 2, "kinds": 4, "domains": 3, "sourced_photos": 2, "visual_items": 18},
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
    "source_traceable",
}
# `rights_verified` is the earlier name of `source_traceable`; either records the check.
CHECK_ALIASES = {"rights_verified": "source_traceable"}
REQUIRED_ROLES = {"evidence", "required_for_solution"}
# A source found on the web is usable when it is traceable (maintainer decision 2026-09-24):
# the record keeps where it came from, not a license verdict. `web_sourced` says exactly that.
ALLOWED_RIGHTS = {"original", "licensed", "public_domain", "user_authorized", "web_sourced"}
EXTERNAL_MODES = {"licensed_source", "web_source", "photo_library"}
PHOTOGRAPHIC_KINDS = {"photo", "archival_image", "satellite_image", "aerial_photo", "artifact_photo"}
FIGURE_REFERENCE = re.compile(r"(?:圖|表|照片)\s*\d+")
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


# Figure and table labels print in Chinese outside 英文 (maintainer decision 2026-09-25): a
# hosted 自然 paper headed a table 「sample／sulfate／carbonate」 and labelled figures
# 「electrolyte」「reaction progress」 where the booklets print 樣品、硫酸根、電解液、反應進程.
# A word is four or more letters in lower case after its first (so symbols, units such as
# mol and kWh, formulas such as NaHCO3 and acronyms such as DNA, NOAA and LED stay allowed).
ENGLISH_LABEL_EXEMPT_SUBJECTS = {"英文"}
ENGLISH_WORD = re.compile(r"(?<![A-Za-z])[A-Za-z][a-z]{3,}(?![A-Za-z])")
LATIN_LABEL_ALLOWED = {
    "mmol", "kmol", "kcal", "mbar", "torr", "alpha", "beta", "gamma", "delta", "theta", "lambda",
    "sigma", "omega", "sinh", "cosh", "tanh",
}
SVG_TEXT_TAGS = {"text", "tspan", "textPath"}
# semantic_data fields that print (axis names, legends, table headers and cells), not style
# settings such as {"style": "dashed"}.
PRINTED_KEY = re.compile(r"label|title|header|caption|name|text|legend|row|column|cell|categor|annotation|axis|tick|unit",
                         re.I)


def _label_strings(value: Any, printed: bool = False) -> list[str]:
    if isinstance(value, str):
        return [value] if printed else []
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in _label_strings(v, printed or bool(PRINTED_KEY.search(str(k))))]
    if isinstance(value, list):
        return [s for v in value for s in _label_strings(v, printed)]
    return []


def _asset_label_text(path: Path) -> list[str]:
    """Printed words of a vector asset: SVG text nodes or a PDF page's text (rasters are unreadable)."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".svg":
            root = ET.parse(path).getroot()
            return ["".join(node.itertext()) for node in root.iter() if node.tag.rsplit("}", 1)[-1] in SVG_TEXT_TAGS]
        if suffix == ".pdf":
            import pymupdf
            with pymupdf.open(path) as doc:
                return [page.get_text() for page in doc]
    except Exception:
        return []
    return []


def english_label_errors(number: Any, spec: dict[str, Any], path: Path, subject: Any) -> list[str]:
    if str(subject) in ENGLISH_LABEL_EXEMPT_SUBJECTS or str(spec.get("kind")) in PHOTOGRAPHIC_KINDS:
        return []
    texts = _label_strings(spec.get("semantic_data")) + (_asset_label_text(path) if path.is_file() else [])
    words = []
    for value in texts:
        for word in ENGLISH_WORD.findall(value):
            if word.lower() not in LATIN_LABEL_ALLOWED and word not in words:
                words.append(word)
    if not words:
        return []
    return [f"Q{number}: figure/table labels print English words ({'、'.join(words[:6])}); {subject} booklets label "
            "figures and tables in Chinese (樣品、時間、電解液、反應進程); keep only symbols, units, formulas and "
            "acronyms such as x, t (s), mol, NaCl, DNA in Latin letters"]


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
        errors.extend(english_label_errors(number, spec, asset_root / str(asset.get("path") or ""), subject))
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
        checks = {CHECK_ALIASES.get(c, c) for c in spec.get("validation_checks") or []}
        missing_checks = sorted(REQUIRED_CHECKS - checks)
        if missing_checks:
            errors.append(f"Q{number}: visual checks missing: {', '.join(missing_checks)}")
        if spec.get("source_rights") not in ALLOWED_RIGHTS:
            errors.append(f"Q{number}: source_rights must be one of {', '.join(sorted(ALLOWED_RIGHTS))} "
                          "(web_sourced: found online, traceable, no license claim needed)")
        if spec.get("generation_mode") in EXTERNAL_MODES:
            # Traceability, not a license: where it came from, who made or hosts it, when it
            # was fetched, the preserved original and what was done to it.
            for field in ("source_url", "crop_description", "source_asset_path", "source_asset_sha256", "processing_steps"):
                if not spec.get(field):
                    errors.append(f"Q{number}: sourced visual lacks {field}")
            if not (spec.get("source_creator") or spec.get("source_site")):
                errors.append(f"Q{number}: sourced visual lacks source_creator or source_site")
            if not (spec.get("source_retrieved_at") or spec.get("source_published_at")):
                errors.append(f"Q{number}: sourced visual lacks source_retrieved_at")
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
        if kind in PHOTOGRAPHIC_KINDS:
            if spec.get("generation_mode") not in EXTERNAL_MODES:
                errors.append(f"Q{number}: a real photograph or archival image needs a traceable source record "
                              "(generation_mode web_source, photo_library or licensed_source)")
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

    visual_items = sum(
        1 for q in exam.get("questions") or [] if isinstance(q, dict) and FIGURE_REFERENCE.search(" ".join(
            [str(q.get("group_stimulus") or ""), str(q.get("prompt") or "")]
            + [str(o.get("text") or "") for o in q.get("options") or [] if isinstance(o, dict)])))

    def minimum(key, fallback):
        # A paper may ask for more than the floor, never less: a hosted paper once lowered
        # its own photo floor in metadata.visual_contract.
        return max(_as_positive_int(configured.get(key), fallback), fallback)

    if full_paper and floor:
        minimum_count = minimum("minimum_required_visuals", floor["count"])
        minimum_sections = minimum("minimum_sections", floor["sections"])
        minimum_kinds = minimum("minimum_kinds", floor["kinds"])
        if len(rows) < minimum_count:
            errors.append(f"paper: {len(rows)} required visuals, minimum is {minimum_count}")
        if len(sections) < minimum_sections:
            errors.append(f"paper: visuals occur in {len(sections)} sections, minimum is {minimum_sections}")
        if len(kinds) < minimum_kinds:
            errors.append(f"paper: {len(kinds)} visual kinds, minimum is {minimum_kinds}")
        if floor.get("domains"):
            minimum_domains = minimum("minimum_domains", floor["domains"])
            if len(domains) < minimum_domains:
                errors.append(f"paper: visuals cover {len(domains)} subject domains, minimum is {minimum_domains}")
        if floor.get("sourced_photos"):
            minimum_photos = minimum("minimum_sourced_photos", floor["sourced_photos"])
            if sourced_photos < minimum_photos:
                errors.append(
                    f"paper: {sourced_photos} traceable real photographs or archival images, minimum is {minimum_photos}"
                )
        if floor.get("visual_items") and visual_items < floor["visual_items"]:
            errors.append(f"paper: {visual_items} items cite a 圖/表/照片 in their material, stem or options; "
                          f"official 社會 111-115 have 18-45, minimum is {floor['visual_items']}")

    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "subject": subject,
        "required_visual_count": len(rows),
        "section_count": len(sections),
        "kind_counts": dict(kinds),
        "sourced_photo_count": sourced_photos,
        "sourced_photo_minimum": (
            max(_as_positive_int(configured.get("minimum_sourced_photos"), floor["sourced_photos"]), floor["sourced_photos"])
            if full_paper and floor.get("sourced_photos")
            else None
        ),
        "figure_citing_item_count": visual_items,
        "sourced_photo_upper_bound": None,
        "domains": sorted(domains),
        "items": rows,
        "errors": errors,
        "notes": [
            "Counts include only evidence/required-for-solution visuals with a completed visual-removal test.",
            "Default floors are conservative internal release floors, not claimed official item-count statistics.",
            "Photo floors count traceable raster photographs, observation and archival images (web_source, photo_library or licensed_source), not generated photorealism or decorative pictures. A traceable web source needs no license claim.",
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
