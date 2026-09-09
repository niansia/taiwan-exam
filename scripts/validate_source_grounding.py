#!/usr/bin/env python3
"""Validate source grounding for current GSAT 國綜/自然 drafts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


FORBIDDEN_PRINT_LABELS = re.compile(r"自擬|本卷自擬|數值為自擬|模型生成文章")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exam", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--novelty-report", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam.read_text(encoding="utf-8-sig"))
    registry = json.loads(args.registry.read_text(encoding="utf-8-sig"))
    sources = {str(x.get("source_id")): x for x in registry.get("sources") or []}
    subject = (exam.get("metadata") or {}).get("paper_subject") or (exam.get("metadata") or {}).get("subject")
    errors: list[str] = []
    mapped_groups: set[str] = set()

    if args.novelty_report:
        novelty = json.loads(args.novelty_report.read_text(encoding="utf-8-sig"))
        if novelty.get("status") != "pass":
            errors.append("source novelty report is not pass")

    for q in exam.get("questions") or []:
        number = q.get("number")
        printed = "\n".join(str(x or "") for x in (q.get("group_stimulus"), q.get("prompt")))
        if FORBIDDEN_PRINT_LABELS.search(printed):
            errors.append(f"Q{number}: forbidden invented-source label in student text")
        spec = q.get("item_spec") or {}
        literacy = spec.get("literacy") or {}
        source_ids = [str(x) for x in literacy.get("source_ids") or []]
        stimulus = str(q.get("group_stimulus") or "")
        if stimulus:
            if not source_ids:
                errors.append(f"Q{number}: stimulus has no source_ids")
            missing = [x for x in source_ids if x not in sources]
            if missing:
                errors.append(f"Q{number}: unknown source_ids {missing}")
            grounding = spec.get("source_grounding") or {}
            if grounding.get("status") != "verified":
                errors.append(f"Q{number}: source_grounding.status must be verified")
            if not grounding.get("proposition_map"):
                errors.append(f"Q{number}: missing proposition_map")
            if subject == "國綜" and grounding.get("material_mode") not in {"licensed_quote", "public_domain_quote", "attributed_adaptation"}:
                errors.append(f"Q{number}: invalid 國綜 material_mode")
            if subject == "自然" and grounding.get("data_mode") not in {"published_exact", "derived_from_published"}:
                errors.append(f"Q{number}: natural-science data must be published or transparently derived")
            mapped_groups.add(stimulus)
        elif source_ids:
            errors.append(f"Q{number}: source_ids present without a source-bearing stimulus")

    report = {
        "status": "pass" if not errors else "fail",
        "subject": subject,
        "question_count": len(exam.get("questions") or []),
        "source_count": len(sources),
        "source_grounded_group_count": len(mapped_groups),
        "errors": errors,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
