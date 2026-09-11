#!/usr/bin/env python3
"""Build deterministic, subject-scoped GSAT source archives and a manifest.

This packages reference material only. It does not generate exam questions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "exam_packs" / "學測"
ALLOWED_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
FIXED_TIME = (2026, 1, 1, 0, 0, 0)
PACKS = {
    "chinese": PACK / "subjects" / "國文",
    "english": PACK / "subjects" / "英文",
    "math-a": PACK / "subjects" / "數學A",
    "math-b": PACK / "subjects" / "數學B",
    "math-common": PACK / "subjects" / "數學（共同範圍模考）",
    "math-legacy": PACK / "subjects" / "數學（舊制）",
    "social": PACK / "subjects" / "社會",
    "science": PACK / "subjects" / "自然",
    "shared": PACK / "shared-data",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files(pack_id: str, source_root: Path) -> list[Path]:
    files = []
    for path in source_root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(source_root)
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        if pack_id == "shared":
            if "模擬考" not in relative.parts:
                continue
        elif not ({"歷屆試題", "模擬考"} & set(relative.parts)):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix())


def write_file(zipped: ZipFile, path: Path, arcname: str) -> None:
    info = ZipInfo(arcname, date_time=FIXED_TIME)
    info.compress_type = ZIP_STORED
    info.external_attr = 0o644 << 16
    with path.open("rb") as source, zipped.open(info, "w") as target:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            target.write(chunk)


def build(output: Path, tag: str, repository: str) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "release_tag": tag,
        "repository": repository,
        "content_policy": "reference-papers-and-answer-materials",
        "allowed_suffixes": sorted(ALLOWED_SUFFIXES),
        "packs": [],
    }
    for pack_id, source_root in PACKS.items():
        files = source_files(pack_id, source_root)
        if not files:
            raise ValueError(f"Source pack is empty: {pack_id} ({source_root})")
        asset = f"taiwan-exam-gsat-sources-{pack_id}-{tag}.zip"
        archive = output / asset
        entries = []
        with ZipFile(archive, "w", compression=ZIP_STORED, allowZip64=True) as zipped:
            for path in files:
                relative = path.relative_to(ROOT).as_posix()
                write_file(zipped, path, relative)
                entries.append({
                    "path": relative,
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                })
        archive_bytes = archive.stat().st_size
        if archive_bytes >= 2 * 1024**3:
            raise ValueError(f"Release asset reaches GitHub's 2 GiB limit: {asset}")
        manifest["packs"].append({
            "id": pack_id,
            "asset": asset,
            "download_url": f"https://github.com/{repository}/releases/download/{tag}/{asset}",
            "archive_bytes": archive_bytes,
            "archive_sha256": sha256_file(archive),
            "file_count": len(entries),
            "source_bytes": sum(item["bytes"] for item in entries),
            "files": entries,
        })
        print(json.dumps({"pack": pack_id, "asset": asset, "files": len(entries), "bytes": archive_bytes}, ensure_ascii=False), flush=True)
    manifest_path = ROOT / "exam_packs" / "學測" / "source-pack-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {"manifest": str(manifest_path), "assets": len(manifest["packs"]), "output": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "source-packs")
    parser.add_argument("--tag", default="source-corpus-2026.09.11")
    parser.add_argument("--repository", default="niansia/taiwan-exam")
    args = parser.parse_args()
    try:
        result = build(args.output.resolve(), args.tag, args.repository)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "pass", **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
