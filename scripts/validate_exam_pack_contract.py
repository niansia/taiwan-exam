"""Renderer handoff adapter to the single validate_exam_release content gate.

No parallel evidence schema, content generator, or independent pass flags.
"""
from __future__ import annotations
import argparse
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def is_complete_paper(exam: dict) -> bool:
    m = exam.get("metadata") or {}
    return bool(m.get("generation_mode") == "full-paper" or m.get("paper_profile_id")
                or m.get("expected_question_count") or m.get("run_contract"))


def require_handoff(exam: dict, base: Path | None = None, contract_override: Path | None = None) -> None:
    if not is_complete_paper(exam) and contract_override is None:
        return  # Isolated renderer fixtures/custom practice are not full exams.
    pointer = (exam.get("metadata") or {}).get("run_contract")
    if not pointer and contract_override is None:
        raise ValueError("Exam Pack handoff blocked: missing metadata.run_contract; inspect exam_packs and preserve the full-paper request.")
    contract = contract_override.resolve() if contract_override is not None else ((base or Path.cwd()) / pointer).resolve()
    if pointer and contract_override is not None and ((base or Path.cwd()) / pointer).resolve() != contract:
        raise ValueError("Exam Pack handoff blocked: CLI and metadata run contracts disagree")
    if not contract.is_file():
        raise ValueError("Exam Pack handoff blocked: run contract is unavailable")
    from validate_exam_release import validate
    # Keep the snapshot beside the input so existing validators resolve relative
    # visual assets correctly. This unique temporary file never replaces input.
    # Contract dependencies remain relative to the external contract itself.
    path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json",
                                         prefix=".exam-content-handoff-", dir=base or Path.cwd(), delete=False) as stream:
            path = Path(stream.name)
            json.dump(exam, stream, ensure_ascii=False)
        result = validate(path, contract, stage="content")
    finally:
        if path is not None:
            path.unlink(missing_ok=True)
    if result["status"] != "pass-content-evidence":
        raise ValueError("Exam Pack handoff blocked: " + "; ".join(result["errors"][:12]))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("exam", type=Path)
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    from validate_exam_release import validate
    try:
        result = validate(a.exam.resolve(), a.contract.resolve(), stage="content")
    except Exception as exc:
        result = {"status": "fail", "errors": [str(exc)]}
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return int(result["status"] == "fail")


if __name__ == "__main__":
    raise SystemExit(main())
