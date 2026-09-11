#!/usr/bin/env python3
"""Build verified public locators for the fixed GSAT 115 layout assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from pypdf import PdfReader


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
        subjects.append({
            "subject": subject,
            "slug": config["slug"],
            "github_folder_url": TREE_ROOT + quote(asset_dir.relative_to(ROOT).as_posix(), safe="/"),
            "layout_profile": config["layout_profile"],
            "formula_variant": config.get("formula_variant"),
            "assets": assets,
        })

    return {
        "schema_version": 1,
        "template_pack_id": manifest["template_pack_id"],
        "repository": "https://github.com/niansia/taiwan-exam",
        "github_template_folder": TREE_ROOT + quote(PACK.relative_to(ROOT).as_posix(), safe="/"),
        "asset_policy": "Formal output must use the verified component PDF bytes as immutable background layers; never OCR, retype, reflow, rasterize, or visually imitate their locked content. blank-template is a review packet, not a fixed-page exam skeleton.",
        "formal_composition": {
            "exact_binary_base_required": True,
            "template_retypesetting_allowed": False,
            "template_rasterization_allowed": False,
            "allowed_overlays": [
                "academic_year",
                "exam_name",
                "current_page",
                "total_pages",
                "newly_authored_body_within_the_inner_body_box",
            ],
            "missing_binary_behavior": "Stop formal rendering, report fixed-template import unavailable, and offer draft-only output or request the exact mapped assets. Do not reconstruct a lookalike template.",
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
