#!/usr/bin/env python3
"""Screen proposed 國綜/自然 sources against the supplied PDF corpus.

Input is a source-registry JSON with a `sources` array.  Each source supplies
`source_id`, `subject`, `title`, and optional `aliases` /
`distinctive_phrases`.  Output contains hit counts and file paths, never the
matching question text.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
PUNCT = re.compile(r"[\W_]+", re.UNICODE)


def norm(value: str) -> str:
    return PUNCT.sub("", unicodedata.normalize("NFKC", value)).lower()


def corpus_paths(subject: str) -> list[Path]:
    base = ROOT / "exam_packs" / "學測" / "subjects" / subject
    return sorted({p for folder in (base / "歷屆試題", base / "模擬考") if folder.exists() for p in folder.rglob("*.pdf")})


def extract(path: Path) -> str:
    try:
        doc = pymupdf.open(path)
        return norm("\n".join(page.get_text("text") or "" for page in doc))
    except Exception:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    registry = json.loads(args.registry.read_text(encoding="utf-8-sig"))
    sources = registry.get("sources") or []
    subject_map = {"國綜": "國文", "國文": "國文", "自然": "自然"}
    corpora: dict[str, list[tuple[Path, str]]] = {}
    reports: list[dict[str, Any]] = []
    errors: list[str] = []

    for source in sources:
        source_id = str(source.get("source_id") or "")
        subject = subject_map.get(str(source.get("subject") or ""))
        if not source_id or not subject:
            errors.append(f"invalid source identity: {source_id or '<missing>'}")
            continue
        if subject not in corpora:
            corpora[subject] = [(path, extract(path)) for path in corpus_paths(subject)]
        probes = [source.get("title") or "", *(source.get("aliases") or []), *(source.get("distinctive_phrases") or [])]
        probes = [str(p) for p in probes if len(norm(str(p))) >= 4]
        hits = []
        for probe in probes:
            needle = norm(probe)
            files = [str(path.relative_to(ROOT)) for path, text in corpora[subject] if needle and needle in text]
            if files:
                hits.append({"probe_kind": "title_alias_or_phrase", "probe_length": len(needle), "file_count": len(files), "files": files[:25]})
        decision = "pass-lexical-triage" if not hits else "reject-or-manual-alias-review"
        if hits:
            errors.append(f"{source_id}: supplied corpus hit")
        reports.append({"source_id": source_id, "subject": subject, "probe_count": len(probes), "decision": decision, "hits": hits})

    output = {
        "status": "pass" if not errors else "fail",
        "registry": str(args.registry),
        "corpus_file_counts": {subject: len(rows) for subject, rows in corpora.items()},
        "sources": reports,
        "errors": errors,
        "warning": "Exact normalized matching is a triage gate; aliases, translations, excerpt identity, and semantic reuse still require editorial review.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
