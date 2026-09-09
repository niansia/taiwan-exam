#!/usr/bin/env python3
"""Validate a dated, source-traceable inspiration pool."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


REQUIRED = {
    "source_id",
    "canonical_url",
    "publisher",
    "title",
    "published_at",
    "accessed_at",
    "editorial_lock_at",
    "simulated_exam_at",
    "source_family",
    "authority_class",
    "rights_status",
    "factual_stability",
    "verified_facts",
    "invented_modelling_values",
    "source_affordances",
    "forbidden_surface_hooks",
    "curriculum_bridge_candidates",
    "paraphrase_strategy",
    "fact_check_status",
}


def iso(value: object, field: str, source_id: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{source_id}: {field} 必須是 YYYY-MM-DD") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pool", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.pool.read_text(encoding="utf-8-sig"))
    records = payload.get("sources") if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not records:
        raise SystemExit("來源池必須是非空陣列，或含 sources 陣列的物件")
    errors: list[str] = []
    ids: set[str] = set()
    domains: set[str] = set()
    families: set[str] = set()
    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            errors.append(f"第 {index} 筆不是物件")
            continue
        source_id = str(record.get("source_id") or f"#{index}")
        missing = sorted(REQUIRED - record.keys())
        if missing:
            errors.append(f"{source_id}: 缺少 {', '.join(missing)}")
            continue
        if source_id in ids:
            errors.append(f"{source_id}: source_id 重複")
        ids.add(source_id)
        parsed = urlparse(str(record["canonical_url"]))
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append(f"{source_id}: canonical_url 必須是完整 HTTPS 網址")
        domains.add(parsed.netloc.lower())
        families.add(str(record["source_family"]))
        try:
            published = iso(record["published_at"], "published_at", source_id)
            accessed = iso(record["accessed_at"], "accessed_at", source_id)
            lock = iso(record["editorial_lock_at"], "editorial_lock_at", source_id)
            exam = iso(record["simulated_exam_at"], "simulated_exam_at", source_id)
            if published > lock:
                errors.append(f"{source_id}: published_at 晚於 editorial_lock_at")
            if accessed > lock:
                errors.append(f"{source_id}: accessed_at 晚於 editorial_lock_at")
            if lock > exam:
                errors.append(f"{source_id}: editorial_lock_at 晚於 simulated_exam_at")
        except ValueError as exc:
            errors.append(str(exc))
        for field in ("verified_facts", "source_affordances", "curriculum_bridge_candidates"):
            value = record.get(field)
            if not isinstance(value, list) or not value:
                errors.append(f"{source_id}: {field} 必須是非空陣列")
        if len(record.get("curriculum_bridge_candidates") or []) < 3:
            errors.append(f"{source_id}: curriculum_bridge_candidates 至少三個")
        if record.get("fact_check_status") != "verified":
            errors.append(f"{source_id}: fact_check_status 尚未 verified")
    report = {
        "status": "pass" if not errors else "fail",
        "source_count": len(records),
        "domain_count": len(domains),
        "source_family_count": len(families),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
