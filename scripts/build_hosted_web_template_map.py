#!/usr/bin/env python3
"""Build verified public locators for the fixed GSAT 115 layout assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from pypdf import PdfReader
import pymupdf


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "exam_packs" / "學測" / "templates" / "115"
OUTPUT = PACK / "hosted-web-template-assets.json"
RAW_ROOT = "https://raw.githubusercontent.com/niansia/taiwan-exam/main/"
VIEW_ROOT = "https://github.com/niansia/taiwan-exam/blob/main/"
TREE_ROOT = "https://github.com/niansia/taiwan-exam/tree/main/"


def public_url(relative: str, *, raw: bool) -> str:
    return (RAW_ROOT if raw else VIEW_ROOT) + quote(relative, safe="/")


def file_record(path: Path) -> dict:
    relative = path.relative_to(ROOT).as_posix()
    data = path.read_bytes()
    if not data.startswith(b"%PDF-"):
        raise ValueError(f"Template asset is not a PDF: {relative}")
    return {
        "component": path.stem,
        "repository_path": relative,
        "download_url": public_url(relative, raw=True),
        "view_url": public_url(relative, raw=False),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "pages": len(PdfReader(path).pages),
    }


def overlay_geometry(asset_dir: Path, profile: dict) -> dict:
    """Measure empty field gaps from the actual locked PDFs, not LLM guesses."""
    g = profile["page_geometry"]
    # The maintained inner-body CSS is top:30mm; bottom:17mm. Math A's
    # measured profile further narrows that box; do not enlarge it.
    top = g.get("content_top_pt", 30 * 72 / 25.4)
    bottom = min(280 * 72 / 25.4, top + g.get("content_frame_height_mm", 250) * 72 / 25.4)
    result = {"body": [g["body_left_pt"], top, g["body_right_pt"], bottom]}
    with pymupdf.open(asset_dir / "cover-blank.pdf") as doc:
        blocks = doc[0].get_text("blocks")
        brand, subject = blocks[0], blocks[1]
        result["cover_title"] = [g["body_left_pt"], brand[3] + 1, g["body_right_pt"], subject[1] - 1]
    for parity in ("odd", "even"):
        with pymupdf.open(asset_dir / f"inner-{parity}-blank.pdf") as doc:
            chars = [c for b in doc[0].get_text("rawdict")["blocks"] for l in b.get("lines", [])
                     for s in l["spans"] for c in s["chars"]]
            fields = {}
            for anchor, key in (("第", "current_page"), ("共", "total_pages")):
                first = next(c for c in chars if c["c"] == anchor)
                last = next(c for c in chars if c["c"] == "頁" and abs(c["bbox"][1] - first["bbox"][1]) < .1)
                fields[key] = [first["bbox"][2] + 1, first["bbox"][1] - 1,
                               last["bbox"][0] - 1, first["bbox"][3] + 1]
            dashes = sorted((c for c in chars if c["c"] == "-" and c["bbox"][1] > 750), key=lambda c: c["bbox"][0])
            if len(dashes) != 2:
                raise ValueError("Unexpected footer template")
            fields["footer"] = [dashes[0]["bbox"][2] + .2, dashes[0]["bbox"][1],
                                dashes[1]["bbox"][0] - .2, dashes[1]["bbox"][3]]
            fields["year_name"] = ([g["body_right_pt"] - 35 * 72 / 25.4, 40, g["body_right_pt"], 54]
                                   if parity == "odd" else [g["body_left_pt"], 40, g["body_left_pt"] + 31 * 72 / 25.4, 54])
            result[parity] = fields
    return result


def build() -> dict:
    manifest = json.loads((PACK / "template-pack.json").read_text(encoding="utf-8"))
    subjects = []
    total_assets = 0
    for subject, config in manifest["subjects"].items():
        asset_dir = PACK / config["asset_dir"]
        assets = [file_record(path) for path in sorted(asset_dir.glob("*.pdf"))]
        expected = {"blank-template", "cover-blank", "inner-even-blank", "inner-odd-blank"}
        if subject in {"數學A", "數學B"}:
            expected.add("formula-blank")
        if {row["component"] for row in assets} != expected:
            raise ValueError(f"Unexpected template components for {subject}")
        total_assets += len(assets)
        folder = "國文" if subject in {"國綜", "國寫"} else subject
        profile = json.loads((ROOT / "exam_packs" / "學測" / "subjects" / folder / "blueprints" /
                              "layout-profiles" / (config["layout_profile"] + ".json")).read_text(encoding="utf-8"))
        subjects.append({
            "subject": subject,
            "slug": config["slug"],
            "github_folder_url": TREE_ROOT + quote(asset_dir.relative_to(ROOT).as_posix(), safe="/"),
            "layout_profile": config["layout_profile"],
            "formula_variant": config.get("formula_variant"),
            "assets": assets,
            "overlay_geometry_pt": overlay_geometry(asset_dir, profile),
        })

    return {
        "schema_version": 1,
        "template_pack_id": manifest["template_pack_id"],
        "repository": "https://github.com/niansia/taiwan-exam",
        "github_template_folder": TREE_ROOT + quote(PACK.relative_to(ROOT).as_posix(), safe="/"),
        "asset_policy": "Formal output must use the verified component PDF bytes as immutable background layers; never OCR, retype, reflow, rasterize, or visually imitate their locked content. blank-template is a review packet, not a fixed-page exam skeleton.",
        "installation_contract": {
            "required_subject_count": 7,
            "required_download_url_count": 30,
            "store_all_download_url_records": True,
            "download_pdf_binaries_during_installation": False,
            "download_timing": "after installation, when generation starts for the requested subject",
        },
        "formal_composition": {
            "exact_binary_base_required": True,
            "template_retypesetting_allowed": False,
            "template_rasterization_allowed": False,
            "persistent_cache_required_for_skill_installation": False,
            "runtime_fetch_scope": "requested_subject_production_components_only",
            "runtime_asset_count": {
                "non_mathematics_subject": 3,
                "mathematics_a_or_b": 4,
            },
            "allowed_overlays": [
                "academic_year",
                "exam_name",
                "current_page",
                "total_pages",
                "newly_authored_body_within_the_inner_body_box",
            ],
            "missing_binary_behavior": "Before drafting, try bounded download or the uploaded data-only template resource PDF. If exact assets remain unavailable, request that one resource upload. Do not produce any generic-layout draft without explicit user consent; a disclaimer is not consent.",
        },
        "offline_resource": {
            "download_page": "https://niansia.github.io/taiwan-exam/download-web-knowledge.html#templates",
            "download_url": RAW_ROOT + "web/taiwan-exam-template-resources.pdf",
            "filename": "taiwan-exam-template-resources.pdf",
            "attachment_name_pattern": "{slug}--{component}.pdf",
            "trust_anchor": "Verify extracted attachment bytes against the per-file records below, not carrier metadata.",
            "usage": "Optional generation-time offline upload, not an installation prerequisite. Extract requested production components only. No code or ZIP attachments.",
        },
        "dynamic_fields": manifest["dynamic_fields"],
        "locked_fields": manifest["locked_fields"],
        "asset_count": total_assets,
        "subjects": subjects,
    }


def main() -> int:
    content = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    result = json.loads(content)
    print(json.dumps({
        "output": str(OUTPUT),
        "subjects": len(result["subjects"]),
        "asset_count": result["asset_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
