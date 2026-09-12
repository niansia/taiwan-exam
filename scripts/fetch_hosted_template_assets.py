#!/usr/bin/env python3
"""Fetch and verify one subject's fixed GSAT template PDF components.

This is a transport helper, not an exam or question generator. It downloads
only the production components required for the requested subject.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAP = ROOT / "exam_packs" / "學測" / "templates" / "115" / "hosted-web-template-assets.json"
MAP_URL = "https://raw.githubusercontent.com/niansia/taiwan-exam/main/exam_packs/%E5%AD%B8%E6%B8%AC/templates/115/hosted-web-template-assets.json"
API_ROOT = "https://api.github.com/repos/niansia/taiwan-exam/contents/"
PRODUCTION_COMPONENTS = {"cover-blank", "inner-odd-blank", "inner-even-blank", "formula-blank"}


def request_bytes(url: str, *, timeout: int, attempts: int) -> bytes:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": "taiwan-exam-template-fetcher/1"})
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"Unable to retrieve {url}: {last_error}")


def load_map(path: Path | None, *, timeout: int, attempts: int) -> dict:
    raw = path.read_bytes() if path and path.is_file() else request_bytes(MAP_URL, timeout=timeout, attempts=attempts)
    return json.loads(raw.decode("utf-8-sig"))


def api_url(repository_path: str) -> str:
    return API_ROOT + quote(repository_path, safe="/") + "?ref=main"


def fetch_record(record: dict, *, timeout: int, attempts: int, local_root: Path | None) -> tuple[bytes, str]:
    if local_root is not None:
        candidate = (local_root / record["repository_path"]).resolve()
        if not candidate.is_relative_to(local_root.resolve()):
            raise ValueError("Template path escapes local mirror")
        if candidate.is_file():
            return candidate.read_bytes(), "local-mirror"

    try:
        return request_bytes(record["download_url"], timeout=timeout, attempts=attempts), "raw-url"
    except RuntimeError:
        payload = json.loads(request_bytes(api_url(record["repository_path"]), timeout=timeout, attempts=attempts))
        if payload.get("encoding") != "base64" or not payload.get("content"):
            raise RuntimeError(f"GitHub contents response has no base64 payload for {record['repository_path']}")
        encoded = b"".join(payload["content"].encode("ascii").split())
        return base64.b64decode(encoded, validate=True), "github-contents-base64"


def verify(record: dict, data: bytes) -> None:
    if not data.startswith(b"%PDF-"):
        raise ValueError(f"Not a PDF: {record['repository_path']}")
    if len(data) != record["bytes"]:
        raise ValueError(f"Byte-count mismatch: {record['repository_path']}")
    digest = hashlib.sha256(data).hexdigest()
    if digest != record["sha256"]:
        raise ValueError(f"SHA-256 mismatch: {record['repository_path']}")


def read_resource_pdf(path: Path, subject_record: dict, records: list[dict]) -> dict[str, bytes]:
    """Read requested attachments only. Never execute embedded content or trust it by name."""
    import pymupdf
    result = {}
    with pymupdf.open(path) as doc:
        names = doc.embfile_names()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate resource attachment name")
        for record in records:
            name = f"{subject_record['slug']}--{record['component']}.pdf"
            if name not in names:
                raise ValueError(f"Missing PDF attachment {name}; the platform may have removed attachments")
            data = doc.embfile_get(name)
            verify(record, data)
            result[record["component"]] = data
    return result


def materialize(subject: str, output_dir: Path, *, map_path: Path | None, local_root: Path | None,
                timeout: int, attempts: int, resource_pdf: Path | None = None) -> dict:
    if timeout <= 0 or attempts not in (1, 2):
        raise ValueError("Use a positive timeout and one or two attempts per transport")
    if resource_pdf and (map_path is None or not map_path.is_file()):
        raise ValueError("Offline extraction requires the map from the uploaded knowledge file")
    started = time.monotonic()
    manifest = load_map(map_path, timeout=timeout, attempts=attempts)
    subject_record = next((row for row in manifest["subjects"] if row["subject"] == subject), None)
    if subject_record is None:
        raise ValueError(f"Unknown subject: {subject}")

    wanted = PRODUCTION_COMPONENTS - ({"formula-blank"} if subject not in {"數學A", "數學B"} else set())
    records = [row for row in subject_record["assets"] if row["component"] in wanted]
    if {row["component"] for row in records} != wanted or len(records) != len(wanted):
        raise ValueError(f"Incomplete production component map for {subject}")

    # Validate all requested attachments before writing anything. No network
    # fallback for an explicitly supplied corrupt carrier; report the mismatch.
    offline = read_resource_pdf(resource_pdf, subject_record, records) if resource_pdf else {}

    target = output_dir.resolve() / subject_record["slug"]
    if target.resolve().parent != output_dir.resolve():
        raise ValueError("Invalid subject slug")
    target.mkdir(parents=True, exist_ok=True)

    def acquire(record: dict) -> dict:
        destination = target / f"{record['component']}.pdf"
        if destination.is_file():
            data = destination.read_bytes()
            verify(record, data)
            transport = "verified-existing"
        else:
            if resource_pdf:
                data, transport = offline[record["component"]], "uploaded-resource-pdf"
            else:
                data, transport = fetch_record(record, timeout=timeout, attempts=attempts, local_root=local_root)
            verify(record, data)
            destination.write_bytes(data)
        return {
            "component": record["component"],
            "path": str(destination),
            "bytes": len(data),
            "sha256": record["sha256"],
            "transport": transport,
        }

    def attempt(record: dict) -> dict:
        try:
            return {"asset": acquire(record)}
        except (OSError, ValueError, RuntimeError) as exc:
            return {"error": {"component": record["component"], "message": str(exc)}}

    # Independent downloads overlap; a failed component does not discard the
    # verified successes. A later call checks cached bytes and retries only gaps.
    with ThreadPoolExecutor(max_workers=min(4, len(records))) as pool:
        results = list(pool.map(attempt, sorted(records, key=lambda row: row["component"])))
    written = [row["asset"] for row in results if "asset" in row]
    errors = [row["error"] for row in results if "error" in row]

    return {
        "status": "partial" if errors else "verified",
        "subject": subject,
        "expected": len(wanted),
        "verified": len(written),
        "assets": written,
        "errors": errors,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", required=True, choices=["國綜", "國寫", "英文", "數學A", "數學B", "社會", "自然"])
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--map", dest="map_path", type=Path, default=DEFAULT_MAP if DEFAULT_MAP.is_file() else None)
    parser.add_argument("--local-root", type=Path)
    parser.add_argument("--resource-pdf", type=Path, help="Uploaded data-only PDF carrier; requires PyMuPDF and a local --map")
    parser.add_argument("--timeout", type=int, default=15, help="Per socket-operation timeout, not an overall deadline")
    parser.add_argument("--attempts", type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    result = materialize(
        args.subject,
        args.output_dir,
        map_path=args.map_path,
        local_root=args.local_root,
        timeout=args.timeout,
        attempts=args.attempts,
        resource_pdf=args.resource_pdf,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
