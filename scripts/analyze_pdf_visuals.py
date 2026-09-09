#!/usr/bin/env python3
"""Build a copyright-safe visual-signal index for ingested PDF sources."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader
    from pypdf.generic import ContentStream
except ImportError as exc:  # pragma: no cover
    raise SystemExit("需要 pypdf；請使用工作區內含 pypdf 的 Python 執行環境。") from exc


ROOT = Path(__file__).resolve().parents[1]
VECTOR_OPERATORS = {b"m", b"l", b"re", b"c", b"v", b"y", b"S", b"s", b"f", b"f*", b"B", b"B*", b"sh"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def xobject_counts(page: Any) -> tuple[int, int]:
    images = 0
    forms = 0
    try:
        resources = page.get("/Resources") or {}
        xobjects = resources.get("/XObject") or {}
        xobjects = xobjects.get_object() if hasattr(xobjects, "get_object") else xobjects
        for value in xobjects.values():
            obj = value.get_object()
            subtype = obj.get("/Subtype")
            if subtype == "/Image":
                images += 1
            elif subtype == "/Form":
                forms += 1
    except Exception:
        pass
    return images, forms


def vector_operation_count(reader: PdfReader, page: Any) -> int:
    try:
        contents = page.get_contents()
        if contents is None:
            return 0
        stream = ContentStream(contents, reader)
        return sum(1 for _, operator in stream.operations if operator in VECTOR_OPERATORS)
    except Exception:
        return 0


def inspect_pdf(path: Path) -> dict[str, Any]:
    reader = PdfReader(path, strict=False)
    pages_with_raster: list[int] = []
    pages_with_vector_signal: list[int] = []
    raster_objects = 0
    form_objects = 0
    vector_operations = 0
    for page_number, page in enumerate(reader.pages, 1):
        images, forms = xobject_counts(page)
        vectors = vector_operation_count(reader, page)
        raster_objects += images
        form_objects += forms
        vector_operations += vectors
        if images:
            pages_with_raster.append(page_number)
        # A threshold reduces false positives from borders, underlines, and crop marks.
        if vectors >= 18 or (forms >= 2 and vectors >= 6):
            pages_with_vector_signal.append(page_number)
    raster = bool(pages_with_raster)
    vector = bool(pages_with_vector_signal)
    signal = "mixed" if raster and vector else "raster" if raster else "vector" if vector else "none_detected"
    return {
        "page_count": len(reader.pages),
        "raster_object_count": raster_objects,
        "form_object_count": form_objects,
        "vector_operation_count": vector_operations,
        "pages_with_raster": pages_with_raster,
        "pages_with_vector_signal": pages_with_vector_signal,
        "visual_signal": signal,
        "analysis_status": "ok",
        "analysis_error": None,
    }


def inspect_pdf_isolated(path: Path, timeout_seconds: int) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--inspect-one", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        check=False,
    )
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or f"exit {completed.returncode}").strip()
        raise RuntimeError(details[:300])
    return json.loads(completed.stdout)


def analyze(root: Path, timeout_seconds: int) -> int:
    metadata = root / "exam_packs" / "學測" / "metadata"
    records: list[dict[str, Any]] = []
    for name in ("source-registry.jsonl", "official-source-registry.jsonl"):
        path = metadata / name
        if path.is_file():
            records.extend(read_jsonl(path))
    if not records:
        print(f"找不到來源索引：{metadata}", file=sys.stderr)
        return 2
    # Visual calibration is question-facing. Answer keys and scoring rubrics add
    # substantial PDF cost without describing the visuals a student must read.
    pdf_records = [
        record for record in records
        if record.get("extension", "").lower() == ".pdf"
        and record.get("role") in {"question", "question_and_solution"}
    ]
    index_path = metadata / "visual-source-index.jsonl"
    existing = {item["sha256"]: item for item in read_jsonl(index_path)} if index_path.is_file() else {}
    output: list[dict[str, Any]] = []
    for index, record in enumerate(pdf_records, 1):
        path = root / record["destination_relative_path"]
        base = {
            "sha256": record["sha256"],
            "exam": record["exam"],
            "year": record["year"],
            "subject": record["subject"],
            "section": record.get("section"),
            "role": record["role"],
            "publisher": record["publisher"],
            "bundle": record["bundle"],
            "destination_relative_path": record["destination_relative_path"],
        }
        try:
            if record["sha256"] in existing:
                base.update({key: value for key, value in existing[record["sha256"]].items() if key not in base})
            else:
                base.update(inspect_pdf_isolated(path, timeout_seconds))
        except subprocess.TimeoutExpired:
            base.update({
                "page_count": record.get("pdf_pages"),
                "raster_object_count": None,
                "form_object_count": None,
                "vector_operation_count": None,
                "pages_with_raster": [],
                "pages_with_vector_signal": [],
                "visual_signal": "unknown",
                "analysis_status": "timeout",
                "analysis_error": f"單檔分析超過 {timeout_seconds} 秒",
            })
        except Exception as exc:
            base.update({
                "page_count": record.get("pdf_pages"),
                "raster_object_count": None,
                "form_object_count": None,
                "vector_operation_count": None,
                "pages_with_raster": [],
                "pages_with_vector_signal": [],
                "visual_signal": "unknown",
                "analysis_status": "failed",
                "analysis_error": f"{type(exc).__name__}: {exc}"[:300],
            })
        output.append(base)
        if index % 10 == 0 or index == len(pdf_records):
            index_path.write_text(
                "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in output), encoding="utf-8"
            )
        if index % 25 == 0 or index == len(pdf_records):
            print(f"已分析 {index}/{len(pdf_records)} 份 PDF", flush=True)

    index_path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in output), encoding="utf-8")
    by_subject: dict[str, Counter[str]] = defaultdict(Counter)
    by_role: dict[str, Counter[str]] = defaultdict(Counter)
    by_publisher: dict[str, Counter[str]] = defaultdict(Counter)
    for item in output:
        signal = item["visual_signal"]
        by_subject[str(item["subject"])][signal] += 1
        by_role[str(item["role"])][signal] += 1
        by_publisher[str(item["publisher"])][signal] += 1
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "PDF resource and drawing-operator heuristic; it identifies candidate pages, not semantic visual types.",
        "pdf_count": len(output),
        "successful": sum(item["analysis_status"] == "ok" for item in output),
        "failed": sum(item["analysis_status"] != "ok" for item in output),
        "visual_signal_counts": dict(Counter(item["visual_signal"] for item in output)),
        "by_subject": {key: dict(value) for key, value in sorted(by_subject.items())},
        "by_role": {key: dict(value) for key, value in sorted(by_role.items())},
        "by_publisher": {key: dict(value) for key, value in sorted(by_publisher.items())},
        "candidate_page_count": sum(
            len(set(item["pages_with_raster"]) | set(item["pages_with_vector_signal"])) for item in output
        ),
    }
    (metadata / "visual-source-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"已建立 {index_path.relative_to(root)} 與 visual-source-report.json")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="分析學測 PDF 的視覺訊號")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--timeout-seconds", type=int, default=15)
    parser.add_argument("--inspect-one", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.inspect_one:
        try:
            print(json.dumps(inspect_pdf(args.inspect_one.resolve()), ensure_ascii=False))
            return 0
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return 2
    return analyze(args.root.resolve(), args.timeout_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
