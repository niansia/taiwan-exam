#!/usr/bin/env python3
"""Validate current GSAT 國綜/自然 structure and official-scope anchors."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
CONTENT_CODE = re.compile(r"\b[A-Z][A-Za-z]{2}-Vc-\d\b")
PERFORMANCE_CODE = re.compile(r"\b[a-z]{2}-Ⅴc-\d\b")
CHINESE_CODES = {f"A{i}" for i in range(1, 7)} | {f"B{i}" for i in range(1, 6)}


def pdf_text(path: Path) -> str:
    doc = pymupdf.open(path)
    return "\n".join(page.get_text("text") or "" for page in doc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("exam", type=Path)
    parser.add_argument("--science-spec", type=Path, default=ROOT / "tmp" / "pdfs" / "gsat-science-spec.pdf")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam.read_text(encoding="utf-8-sig"))
    subject = (exam.get("metadata") or {}).get("paper_subject")
    questions = exam.get("questions") or []
    errors: list[str] = []
    warnings: list[str] = []

    if subject not in {'國綜', '自然'}:
        errors.append(f"unsupported paper_subject {subject!r}")
    else:
        # Scope and full-paper structure are separate. Never hardcode one
        # generated paper's section ids/counts as all ROC 111-115 structures.
        warnings.append('Exact section/type/score structure must pass validate_exam_release.py against the selected source-reviewed profile.')

    used_codes = Counter()
    domain_counts = Counter()
    if subject == "國綜":
        if any("國寫" in str(q) for q in questions):
            errors.append("國綜 paper contains 國寫 material")
        for q in questions:
            codes = (q.get("item_spec") or {}).get("curriculum_codes") or []
            if not codes:
                errors.append(f"Q{q.get('number')}: no curriculum code")
            bad = [c for c in codes if c not in CHINESE_CODES]
            if bad:
                errors.append(f"Q{q.get('number')}: invalid 國綜 scope codes {bad}")
            used_codes.update(codes)
        if not any(code.startswith("A") for code in used_codes):
            errors.append("國綜 has no language-knowledge A objective")
        for code in ("B1", "B2", "B3", "B4", "B5"):
            if not used_codes[code]:
                errors.append(f"國綜 missing {code}")
    elif subject == "自然":
        source = pdf_text(args.science_spec)
        valid_content = set(CONTENT_CODE.findall(source))
        valid_performance = set(PERFORMANCE_CODE.findall(source))
        for q in questions:
            spec = q.get("item_spec") or {}
            codes = spec.get("curriculum_codes") or []
            if not codes:
                errors.append(f"Q{q.get('number')}: no curriculum code")
                continue
            for code in codes:
                if code not in valid_content and code not in valid_performance:
                    errors.append(f"Q{q.get('number')}: code not in official specification: {code}")
                used_codes[code] += 1
            domain = str(spec.get("domain") or "")
            domain = domain.replace("地球科學", "地科")
            head = next((name for name in ("物理", "化學", "生物", "地科") if name in domain), None)
            if head:
                domain_counts[head] += 1
            else:
                errors.append(f"Q{q.get('number')}: natural-science domain is not classifiable")
        for domain in ("物理", "化學", "生物", "地科"):
            if domain_counts[domain] < 8:
                errors.append(f"{domain} coverage below 8 items: {domain_counts[domain]}")
        inquiry = sum(any(PERFORMANCE_CODE.fullmatch(c) for c in ((q.get("item_spec") or {}).get("curriculum_codes") or [])) for q in questions)
        if inquiry < 14:
            errors.append(f"inquiry/practice coverage below 14 items: {inquiry}")
        if not any(q.get("type") == "constructed_response" for q in questions):
            errors.append("natural mixed part has no constructed response")
    else:
        inquiry = 0

    report = {
        "status": "pass" if not errors else "fail", "subject": subject,
        "question_count": len(questions), "total_score": sum(float(q.get("score") or 0) for q in questions),
        "domain_counts": dict(domain_counts), "curriculum_code_counts": dict(sorted(used_codes.items())),
        "inquiry_item_count": inquiry if subject == "自然" else None,
        "errors": errors, "warnings": warnings,
        "scope_source": str(args.science_spec) if subject == "自然" else "CEEC 國文考科考試說明 A1-A6/B1-B5",
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
