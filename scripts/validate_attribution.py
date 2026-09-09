#!/usr/bin/env python3
"""Transparent local provenance checks; not DRM, legal advice or exam acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

UPSTREAM_ID = "taiwan-exam-generator"
UPSTREAM_NAME = "Taiwan Exam"


def validate(root: Path, *, public_release: bool = False) -> dict:
    root = root.resolve()
    errors, warnings = [], []
    record = None
    notice = ""
    for name in ("ORIGIN.json", "NOTICE", "AGENTS.md", "SKILL.md", "references/attribution-and-forks.md"):
        if not (root / name).is_file():
            errors.append(f"Missing distribution file: {name}")
    try:
        record = json.loads((root / "ORIGIN.json").read_text(encoding="utf-8-sig"))
        if not isinstance(record, dict) or record.get("schema_version") != 1:
            raise ValueError("Unsupported ORIGIN schema")
        upstream, distribution, licensing = (record[key] for key in ("upstream", "distribution", "licensing"))
        if not all(isinstance(value, dict) for value in (upstream, distribution, licensing)):
            raise ValueError("Origin sections must be objects")
        if upstream.get("project_id") != UPSTREAM_ID or upstream.get("name") != UPSTREAM_NAME:
            errors.append("Upstream identity was removed/replaced; edit distribution.name for a rebrand")
        name = distribution.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append("distribution.name must be a nonempty string")
        derivative = distribution.get("is_derivative")
        if not isinstance(derivative, bool):
            errors.append("distribution.is_derivative must be a boolean")
        if name != UPSTREAM_NAME and derivative is not True:
            errors.append("A renamed distribution must identify itself as a derivative")
        changes = distribution.get("changes")
        valid_changes = isinstance(changes, list) and all(isinstance(x, str) and x.strip() for x in changes)
        if not valid_changes or (derivative is True and not changes):
            errors.append("Derivative changes must be recorded as nonempty descriptions")
        notice = (root / "NOTICE").read_text(encoding="utf-8-sig")
        for line in (f"Upstream project: {UPSTREAM_NAME}", f"Upstream project ID: {UPSTREAM_ID}"):
            if line not in notice.splitlines():
                errors.append("NOTICE does not retain the upstream attribution: " + line)
        if licensing.get("status") != "owner-confirmed":
            (errors if public_release else warnings).append("Final license is pending owner confirmation")
        if public_release:
            if not isinstance(licensing.get("spdx_id"), str) or not licensing["spdx_id"].strip():
                errors.append("Owner-confirmed license identifier is missing")
            holders = licensing.get("copyright_holders")
            if not isinstance(holders, list) or not holders or not all(isinstance(x, str) and x.strip() for x in holders):
                errors.append("Owner-confirmed rights-holder notice is missing")
            relative = licensing.get("license_file")
            license_path = (root / relative).resolve() if isinstance(relative, str) and relative else root
            if root not in license_path.parents or not license_path.is_file():
                errors.append("Declared license must be a file within the distribution")
            elif not license_path.read_text(encoding="utf-8-sig").strip():
                errors.append("Declared license text is empty")
            url = upstream.get("repository_url")
            parsed = urlparse(url) if isinstance(url, str) else None
            if not parsed or parsed.scheme != "https" or not parsed.netloc or parsed.path in ("", "/"):
                errors.append("Confirmed upstream repository URL is missing")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"Cannot validate origin: {exc}")
    return {"status": "fail" if errors else "pass", "scope": "attribution-declarations-only",
            "public_release_requested": public_release, "errors": errors, "warnings": warnings,
            "origin": record, "notice_sha256": hashlib.sha256(notice.encode("utf-8")).hexdigest() if notice else None,
            "legal_or_exam_approval": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--public-release", action="store_true")
    args = parser.parse_args(argv)
    result = validate(args.root, public_release=args.public_release)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
