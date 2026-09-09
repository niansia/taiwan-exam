#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = ROOT / "templates" / "current-gsat-math-scope.json"


def compact_text(question: dict) -> str:
    pieces = [str(question.get("prompt", "")), str(question.get("group_stimulus", ""))]
    pieces.extend(str(option.get("text", "")) for option in question.get("options", []))
    spec = question.get("item_spec", {})
    record = spec.get("originality_record", {})
    pieces.extend(str(x) for x in record.get("curriculum_reduction", {}).get("mapped_operations", []))
    return " ".join(pieces)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a generated GSAT Math A/B paper against the current curriculum gate.")
    parser.add_argument("paper", type=Path)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    args = parser.parse_args()

    paper = json.loads(args.paper.read_text(encoding="utf-8"))
    scope = json.loads(args.scope.read_text(encoding="utf-8"))
    subject = str(paper.get("metadata", {}).get("subject", ""))
    if subject not in {"數學A", "數學B"}:
        print(f"ERROR unsupported subject: {subject}")
        return 2

    suffix = "math_a_codes" if subject == "數學A" else "math_b_codes"
    allowed = set(scope["common_codes"]) | set(scope[suffix])
    errors: list[str] = []
    bridges: list[str] = []
    context_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    for question in paper.get("questions", []):
        qid = str(question.get("id", "?"))
        spec = question.get("item_spec", {})
        codes = spec.get("scope_codes", [])
        status = spec.get("scope_status")
        if not codes:
            errors.append(f"{qid}: missing scope_codes")
        unknown = sorted(set(codes) - allowed)
        if unknown:
            errors.append(f"{qid}: out-of-subject codes {unknown}")
        if status not in {"direct", "defined-bridge"}:
            errors.append(f"{qid}: scope_status must be direct or defined-bridge")
        elif status == "defined-bridge":
            bridges.append(qid)

        context_class = spec.get("context_class")
        topic_family = spec.get("topic_family")
        if context_class not in {"pure-math", "neutral-application", "dated-source"}:
            errors.append(f"{qid}: invalid or missing context_class")
        else:
            context_counts[context_class] += 1
        if not topic_family:
            errors.append(f"{qid}: missing topic_family")
        else:
            topic_counts[str(topic_family)] += 1

        text = compact_text(question)
        for pattern in scope["always_forbidden_patterns"]:
            if re.search(re.escape(pattern), text, flags=re.IGNORECASE):
                errors.append(f"{qid}: forbidden GSAT concept/term {pattern!r}")
        if subject == "數學B":
            lowered = text.lower()
            for operation in scope["math_b_forbidden_operations"]:
                if operation.lower() in lowered:
                    errors.append(f"{qid}: Math B operation outside the A/B boundary {operation!r}")

    item_count = len(paper.get("questions", []))
    if item_count == 20:
        if not 5 <= context_counts["dated-source"] <= 8:
            errors.append(f"paper: dated-source count {context_counts['dated-source']} is outside the internal 5-8 ecology band")
        if context_counts["pure-math"] < 4:
            errors.append(f"paper: only {context_counts['pure-math']} pure-math items; require at least 4")
        if context_counts["neutral-application"] < 4:
            errors.append(f"paper: only {context_counts['neutral-application']} neutral-application items; require at least 4")
        dominant = [(name, count) for name, count in topic_counts.items() if count > 4]
        if dominant:
            errors.append(f"paper: a topical family exceeds 20% of scored items: {dominant}")
        if topic_counts["combinatorics"] < 1:
            errors.append("paper: no explicit combinatorics item")
        if subject == "數學A":
            cubic_items = [
                question
                for question in paper.get("questions", [])
                if "F-10-2" in (question.get("item_spec", {}).get("scope_codes", []))
            ]
            if not 1 <= len(cubic_items) <= 2:
                errors.append(
                    f"paper: Math A requires 1-2 cubic-function items carrying F-10-2; found {len(cubic_items)}"
                )
            if len(cubic_items) == 2:
                mechanisms = [
                    str(
                        question.get("item_spec", {})
                        .get("originality_record", {})
                        .get("selected_mechanism", "")
                    )
                    for question in cubic_items
                ]
                if not all(mechanisms) or len(set(mechanisms)) != 2:
                    errors.append("paper: two F-10-2 items must use distinct recorded mechanism families")

    if errors:
        print("CURRICULUM CHECK: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "CURRICULUM CHECK: PASS "
        f"({item_count} items; ecology={dict(context_counts)}; "
        f"defined-bridge human review: {', '.join(bridges) or 'none'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
