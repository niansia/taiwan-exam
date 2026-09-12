#!/usr/bin/env python3
"""Extract hash-checked reference sections, not questions, from Web Knowledge.

No network, installation, question generation or PDF rendering occurs here.
Without --output-dir, list the selected paths and sizes without dumping content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


SUBJECT_REFERENCES = {
    "數學A": {"current-gsat-math-form.md", "current-gsat-math-scope.md", "math-difficulty-design.md"},
    "數學B": {"current-gsat-math-form.md", "current-gsat-math-scope.md", "math-difficulty-design.md"},
    "英文": {"current-gsat-english-form.md"},
    "社會": {"current-gsat-social-form.md", "social-required-content-codes.json"},
    "自然": {"current-gsat-chinese-natural-form.md"},
    "國綜": {"current-gsat-chinese-natural-form.md"},
    "國寫": {"current-gsat-writing-form.md", "gsat-writing-111-115-selection-calibration.md",
             "gsat-writing-source-ecology.md"},
}
SUBJECT_ONLY = set().union(*SUBJECT_REFERENCES.values())


def relevant(path: str, subject: str) -> bool:
    """Initial read route, not a claim that every transitive dependency is loaded."""
    if subject not in SUBJECT_REFERENCES:
        raise ValueError(f"Unknown GSAT subject: {subject}")
    if path.startswith("references/"):
        return Path(path).name not in SUBJECT_ONLY or Path(path).name in SUBJECT_REFERENCES[subject]
    if path.startswith("exam_packs/"):
        if not path.startswith("exam_packs/學測/") or path.endswith("source-pack-manifest.json"):
            return False
        if "/subjects/" in path:
            folder = "國文" if subject in {"國綜", "國寫"} else subject
            return path.startswith(f"exam_packs/學測/subjects/{folder}/")
    return True


def sections(knowledge: str) -> dict[str, tuple[dict, bytes]]:
    start = knowledge.index("## Source manifest\n")
    manifest_text = knowledge[start:].split("```json\n", 1)[1].split("\n```", 1)[0]
    manifest = json.loads(manifest_text)
    records = {row["path"]: row for row in manifest}
    if len(records) != len(manifest):
        raise ValueError("Duplicate manifest path")
    found = {}
    for match in re.finditer(r'^<canonical-source path="([^"]+)">\n(.*?)^</canonical-source>$',
                             knowledge, re.MULTILINE | re.DOTALL):
        path, payload = match.groups()
        parts = PurePosixPath(path).parts
        if not parts or path.startswith("/") or ".." in parts or "\\" in path or ":" in path:
            raise ValueError("Unsafe canonical path")
        if path in found or path not in records:
            raise ValueError(f"Duplicate or unlisted section: {path}")
        found[path] = (records[path], payload.encode("utf-8"))
    if found.keys() != records.keys():
        raise ValueError("Missing canonical sections")
    return found


def extract(knowledge_path: Path, *, subject: str | None = None,
            paths: list[str] | None = None, output_dir: Path | None = None) -> dict:
    source = knowledge_path.read_text(encoding="utf-8-sig")
    entries = sections(source)
    chosen = sorted(paths or [p for p in entries if subject is None or relevant(p, subject)])
    verified = []
    for path in chosen:
        record, data = entries[path]
        # Original source hashes can differ under CRLF/BOM. Only the explicitly
        # recorded portable payload hash verifies the normalized embedded bytes.
        if (len(data) != record["embedded_bytes"]
                or hashlib.sha256(data).hexdigest() != record["embedded_sha256"]):
            raise ValueError(f"Embedded checksum mismatch: {path}")
        verified.append((path, data))
    if output_dir is not None:
        root = output_dir.resolve()
        for path, data in verified:
            destination = (root / path).resolve()
            if not destination.is_relative_to(root):
                raise ValueError(f"Destination outside workspace: {path}")
            if destination.exists() and destination.read_bytes() != data:
                raise ValueError(f"Preserve existing different file; use a versioned reference directory: {path}")
        for path, data in verified:
            destination = root / path
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
    return {"subject": subject, "section_count": len(verified),
            "selected_bytes": sum(len(data) for _, data in verified),
            "knowledge_bytes": knowledge_path.stat().st_size,
            "files": [{"path": p, "bytes": len(data)} for p, data in verified]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("knowledge", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--subject", choices=sorted(SUBJECT_REFERENCES))
    group.add_argument("--path", action="append", dest="paths")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(extract(args.knowledge, subject=args.subject, paths=args.paths,
                             output_dir=args.output_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
