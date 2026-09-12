#!/usr/bin/env python3
"""Download, verify and safely install GSAT source packs from GitHub Releases."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "exam_packs" / "學測" / "source-pack-manifest.json"
SUBJECT_PACKS = {
    "國文": {"chinese", "shared"},
    "國綜": {"chinese", "shared"},
    "國寫": {"chinese", "shared"},
    "英文": {"english", "shared"},
    "數學A": {"math-a", "math-common", "shared"},
    "數A": {"math-a", "math-common", "shared"},
    "數學B": {"math-b", "math-common", "shared"},
    "數B": {"math-b", "math-common", "shared"},
    "社會": {"social", "shared"},
    "自然": {"science", "shared"},
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def allowed_member(relative: PurePosixPath) -> bool:
    parts = relative.parts
    if len(parts) < 5 or parts[:2] != ("exam_packs", "學測"):
        return False
    if parts[2] == "subjects":
        return len(parts) >= 6 and parts[4] in {"歷屆試題", "模擬考"}
    return parts[2] == "shared-data" and parts[3] == "模擬考"


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".download-", suffix=".part", dir=target.parent)
    part = Path(name)
    request = Request(url, headers={"User-Agent": "TaiwanExamSkill/source-bootstrap"})
    try:
        with os.fdopen(fd, "wb") as output, urlopen(request, timeout=120) as response:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        part.replace(target)
    finally:
        part.unlink(missing_ok=True)


def validate_member_path(name: str) -> PurePosixPath:
    relative = PurePosixPath(name)
    if (relative.is_absolute() or ".." in relative.parts or "\\" in name
            or relative.as_posix() != name or not allowed_member(relative)
            or any(any(c in part for c in ':*?"<>|') or part.endswith((' ', '.')) for part in relative.parts)):
        raise ValueError(f"Unsafe or unexpected archive member: {name}")
    return relative


def install_pack(pack: dict, cache: Path, *, verify_only: bool) -> tuple[int, int]:
    # Validate the manifest before reading any path, including verify-only runs.
    # A source pack may add missing inputs; it must never replace private inputs.
    expected_files = {item["path"]: item for item in pack["files"]}
    if len(expected_files) != len(pack["files"]):
        raise ValueError("Duplicate source paths in manifest")
    if len({name.casefold() for name in expected_files}) != len(expected_files):
        raise ValueError("Source paths collide on case-insensitive filesystems")
    asset = pack["asset"]
    if not isinstance(asset, str) or not asset or Path(asset).name != asset or any(c in asset for c in '/\\:') or asset in {'.', '..'}:
        raise ValueError("Unsafe source archive filename")
    missing_or_invalid = []
    conflicts = []
    for relative, record in expected_files.items():
        path = validate_member_path(relative)
        target = ROOT / Path(*path.parts)
        if ROOT.resolve() not in target.resolve().parents:
            raise ValueError(f"Source target escaped the Skill root: {relative}")
        if target.is_symlink():
            raise ValueError(f"Source target must not be a symbolic link: {relative}")
        if not target.is_file() or target.stat().st_size != record["bytes"] or sha256_file(target) != record["sha256"]:
            missing_or_invalid.append(relative)
            if target.exists():
                conflicts.append(relative)
    if not missing_or_invalid:
        return len(expected_files), 0
    if verify_only:
        return len(expected_files) - len(missing_or_invalid), len(missing_or_invalid)
    if conflicts:
        raise ValueError("Conflicting local sources preserved; resolve these files before installation: " + "; ".join(conflicts))

    archive = cache / pack["asset"]
    if not archive.is_file() or archive.stat().st_size != pack["archive_bytes"] or sha256_file(archive) != pack["archive_sha256"]:
        if archive.exists():
            archive.unlink()
        print(f"Downloading {pack['id']}: {pack['download_url']}", flush=True)
        download(pack["download_url"], archive)
    if archive.stat().st_size != pack["archive_bytes"] or sha256_file(archive) != pack["archive_sha256"]:
        raise ValueError(f"Archive verification failed: {archive}")

    with ZipFile(archive) as zipped:
        entries = [info for info in zipped.infolist() if not info.is_dir()]
        members = {info.filename: info for info in entries}
        if len(entries) != len(members):
            raise ValueError(f"Duplicate archive members: {archive.name}")
        if set(members) != set(expected_files):
            raise ValueError(f"Archive manifest mismatch: {archive.name}")
        for name, info in members.items():
            relative = validate_member_path(name)
            record = expected_files[name]
            if stat.S_ISLNK(info.external_attr >> 16) or info.file_size != record["bytes"]:
                raise ValueError(f"Invalid archive member type or size: {name}")
            target = (ROOT / Path(*relative.parts)).resolve()
            if ROOT.resolve() not in target.parents:
                raise ValueError(f"Extraction target escaped the Skill root: {target}")
            if target.is_file() and target.stat().st_size == record["bytes"] and sha256_file(target) == record["sha256"]:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            # Unique staging avoids clobbering another run or a user's .part file.
            fd, temp_name = tempfile.mkstemp(prefix=".source-", suffix=".part", dir=target.parent)
            part = Path(temp_name)
            try:
                with os.fdopen(fd, "wb") as output, zipped.open(info) as source:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                if part.stat().st_size != record["bytes"] or sha256_file(part) != record["sha256"]:
                    raise ValueError(f"Extracted file verification failed: {relative}")
                try:
                    # Atomic create-if-absent: a file created concurrently wins.
                    os.link(part, target)
                except FileExistsError:
                    if not target.is_file() or sha256_file(target) != record["sha256"]:
                        raise ValueError(f"Conflicting local source preserved: {relative}")
            finally:
                part.unlink(missing_ok=True)

    invalid = []
    for relative, record in expected_files.items():
        target = ROOT / Path(*PurePosixPath(relative).parts)
        if not target.is_file() or target.stat().st_size != record["bytes"] or sha256_file(target) != record["sha256"]:
            invalid.append(relative)
    if invalid:
        raise ValueError(f"Pack remains incomplete after installation: {pack['id']} ({len(invalid)} files)")
    return len(expected_files), 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", action="append", choices=sorted(SUBJECT_PACKS), help="Prepare only the requested subject; may be repeated")
    parser.add_argument("--all", action="store_true", help="Prepare every source pack")
    parser.add_argument("--verify-only", action="store_true", help="Check local files without downloading or changing them")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--cache", type=Path, default=ROOT / "downloads" / "source-packs")
    args = parser.parse_args(argv)
    if not args.all and not args.subject:
        parser.error("choose --subject <科目> or --all")
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        available = {pack["id"]: pack for pack in manifest["packs"]}
        if len(available) != len(manifest['packs']) or not available:
            raise ValueError('Source manifest has duplicate pack ids or no packs')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'invalid-manifest', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    selected = set(available) if args.all else set().union(*(SUBJECT_PACKS[item] for item in args.subject))
    unknown = selected - set(available)
    if unknown:
        print(f"Manifest does not contain source packs: {sorted(unknown)}", file=sys.stderr)
        return 2
    failures = 0
    for pack_id in sorted(selected):
        try:
            valid, invalid = install_pack(available[pack_id], args.cache.resolve(), verify_only=args.verify_only)
            print(json.dumps({"pack": pack_id, "valid_files": valid, "missing_or_invalid": invalid}, ensure_ascii=False))
            failures += invalid
        except (OSError, ValueError, KeyError, TypeError, BadZipFile) as exc:
            print(json.dumps({"pack": pack_id, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
            return 2
    print(json.dumps({"status": "pass" if failures == 0 else "incomplete", "selected_packs": sorted(selected), "missing_or_invalid": failures}, ensure_ascii=False))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
