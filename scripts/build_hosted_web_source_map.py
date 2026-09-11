#!/usr/bin/env python3
"""Build the compact ROC 111-115 CEEC source map used by hosted-web agents."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "exam_packs" / "學測" / "metadata"
CATALOG = METADATA / "official-download-catalog.jsonl"
REGISTRY = METADATA / "official-source-registry.jsonl"
OUTPUT = METADATA / "official-current-web-sources.json"
OFFICIAL_LISTING_URL = "https://www.ceec.edu.tw/xmfile?xsmsid=0J052424829869345634"
YEARS = (115, 114, 113, 112, 111)
SUBJECTS = (
    ("國綜", "國文", "國綜"),
    ("國寫", "國文", "國寫"),
    ("英文", "英文", "英文"),
    ("數學A", "數學A", None),
    ("數學B", "數學B", None),
    ("社會", "社會", None),
    ("自然", "自然", None),
)
ROLES = ("question", "answer", "scoring_rule")


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root: Path = ROOT) -> dict:
    metadata = root / "exam_packs" / "學測" / "metadata"
    catalog_path = metadata / CATALOG.name
    registry_path = metadata / REGISTRY.name
    catalog = read_jsonl(catalog_path)
    registry_by_url = {row["source_url"]: row for row in read_jsonl(registry_path)}
    selected = [
        row for row in catalog
        if row.get("selected") is True
        and row.get("extension") == ".pdf"
        and row.get("roc_year") in YEARS
        and row.get("role") in ROLES
    ]

    subject_records = []
    document_count = 0
    question_count = 0
    for output_subject, catalog_subject, section in SUBJECTS:
        years = []
        for roc_year in YEARS:
            documents = {}
            for role in ROLES:
                matches = [
                    row for row in selected
                    if row.get("roc_year") == roc_year
                    and row.get("subject") == catalog_subject
                    and row.get("section") == section
                    and row.get("role") == role
                ]
                if not matches and output_subject == "國寫" and role == "answer":
                    continue
                if len(matches) != 1:
                    raise ValueError(
                        f"Expected one {roc_year} {output_subject} {role} PDF; found {len(matches)}"
                    )
                catalog_row = matches[0]
                source = registry_by_url.get(catalog_row["url"])
                if not source or source.get("download_status") != "downloaded":
                    raise ValueError(f"Downloaded source evidence missing: {catalog_row['url']}")
                local_source = root / source["destination_relative_path"]
                if (
                    not local_source.is_file()
                    or local_source.stat().st_size != source["size_bytes"]
                    or sha256_file(local_source) != source["sha256"]
                ):
                    raise ValueError(f"Local source failed hash verification: {local_source}")
                documents[role] = {
                    "label": catalog_row["label"],
                    "title": catalog_row["file_title"],
                    "url": catalog_row["url"],
                    "bytes": source["size_bytes"],
                    "sha256": source["sha256"],
                    "pages": source["pdf_pages"],
                    "text_layer_status": source["text_layer_status"],
                    "local_path": source["destination_relative_path"],
                }
                document_count += 1
                question_count += role == "question"
            years.append({"roc_year": roc_year, "calendar_year": roc_year + 1911, "documents": documents})
        subject_records.append({
            "subject": output_subject,
            "catalog_subject": catalog_subject,
            "section": section,
            "years": years,
        })

    if question_count != 35 or document_count != 100:
        raise ValueError(
            f"Current-form source map must contain 35 question PDFs and 100 documents; "
            f"found {question_count} and {document_count}"
        )
    return {
        "schema_version": 1,
        "exam": "學測",
        "regime": "111學年度起",
        "authority": "財團法人大學入學考試中心",
        "official_listing_url": OFFICIAL_LISTING_URL,
        "roc_years": list(YEARS),
        "question_pdf_count": question_count,
        "document_count": document_count,
        "catalog_sha256": sha256_file(catalog_path),
        "registry_sha256": sha256_file(registry_path),
        "subjects": subject_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = build()
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({
        "output": str(output),
        "subjects": len(payload["subjects"]),
        "question_pdf_count": payload["question_pdf_count"],
        "document_count": payload["document_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
