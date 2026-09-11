#!/usr/bin/env python3
"""Validate GSAT English lexical scope against the CEEC 111-onward list.

The validator deliberately separates list membership from item quality.  It
checks the former from the official PDF and requires explicit lexical-design
metadata for vocabulary items so that a paper cannot pass merely by using easy
words.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ENTRY_RE = re.compile(
    r"^(.+?)\s+((?:\(?[A-Za-z]+\.\)?/?)+)\s+([1-6])$"
)
TOKEN_RE = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*")
SKIP_LINES = {"高中英文參考詞彙表", "依字母排序", "附錄"}
READING_LABELS = ("閱讀測驗", "reading")
VOCAB_LABELS = ("詞彙題", "vocabulary")
VALID_COMPETITION_TYPES = {
    "near_synonym", "collocation", "polysemy", "argument_structure",
    "register", "semantic_prosody", "word_family_or_form", "discourse_relation",
}


def answer_positions_balanced(counts: Counter[str], labels: set[str] | None = None) -> bool:
    labels = labels or {"A", "B", "C", "D"}
    values = [counts[label] for label in sorted(labels)]
    return set(counts) == labels and max(values) - min(values) <= 1
STRONG_PLAUSIBILITY = {"high", "medium"}

# The CEEC PDF is a headword list, not a complete surface-form lexicon.  Keep
# elementary function words and high-frequency irregular forms from becoming
# false scope failures, while still checking content words against a CEEC
# headword (or an explicit gloss/proper-noun allowance in the item spec).
BASIC_FUNCTION_FORMS = {
    "a", "an", "the", "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve", "twenty", "thirty", "hundred",
    "be", "am", "is", "are", "was", "were", "been", "being", "cannot", "ones",
    "do", "does", "did", "done", "have", "has", "had",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
}

IRREGULAR_HEADWORDS = {
    "began": "begin", "felt": "feel", "gave": "give", "gone": "go",
    "held": "hold", "kept": "keep", "led": "lead", "stood": "stand",
    "forgot": "forget", "wrote": "write", "truly": "true",
    "became": "become", "broken": "break", "came": "come", "chosen": "choose",
    "drawn": "draw", "fell": "fall", "grew": "grow", "heard": "hear",
    "hid": "hide", "known": "know", "made": "make", "taken": "take", "sent": "send",
    "using": "use", "reader's": "read",
    "understood": "understand", "written": "write", "children": "child",
}


def _load_pymupdf() -> Any:
    try:
        import pymupdf  # type: ignore
        return pymupdf
    except ImportError:
        try:
            import fitz  # type: ignore
            return fitz
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise SystemExit("需要 PyMuPDF 才能讀取大考中心參考詞彙表 PDF。") from exc


def _expand_word_expression(expression: str) -> set[str]:
    """Expand CEEC slash/parenthesis notation into lookup forms."""
    expression = expression.strip().replace("’", "'")
    variants: set[str] = set()
    for part in expression.split("/"):
        part = part.strip()
        if not part:
            continue
        match = re.fullmatch(r"([A-Za-z][A-Za-z'-]*?)\(([A-Za-z]+)\)", part)
        if match:
            base, inner = match.groups()
            variants.add(base.lower())
            if inner in {"s", "ment"}:
                variants.add((base + inner).lower())
            else:
                variants.add(inner.lower())
            continue

        # Pronoun and irregular-form entries use a parenthesized comma list.
        outside = re.sub(r"\([^)]*\)", "", part).strip()
        variants.update(token.lower() for token in TOKEN_RE.findall(outside))
        for inner in re.findall(r"\(([^)]*)\)", part):
            variants.update(token.lower() for token in TOKEN_RE.findall(inner))
    return variants


def parse_reference_pdf(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Parse the alphabetic section of the official CEEC vocabulary PDF."""
    pdf = _load_pymupdf().open(path)
    rows: list[tuple[str, str, int]] = []
    pending = ""
    # The alphabetic list begins on printed page 53 / physical page 65 and the
    # appendix begins on physical page 116 in the verified 111-onward edition.
    for page_index in range(64, len(pdf)):
        page_text = pdf[page_index].get_text("text")
        if page_index > 64 and "附錄" in page_text:
            break
        for raw_line in page_text.splitlines():
            line = " ".join(raw_line.split())
            if not line or line in SKIP_LINES or re.fullmatch(r"[A-Z]", line):
                continue
            if line.isdigit() and not (pending and line in {"1", "2", "3", "4", "5", "6"}):
                continue
            candidate = f"{pending} {line}".strip() if pending else line
            match = ENTRY_RE.fullmatch(candidate)
            if match:
                expression, pos, level = match.groups()
                rows.append((expression, pos, int(level)))
                pending = ""
            else:
                # Wrapped entries are at most three short lines.  A fresh line
                # ending in a level but still not matching signals extraction
                # damage; keep it out rather than silently inventing a record.
                pending = candidate if len(candidate) < 180 else ""

    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for expression, pos, level in rows:
        record = {"entry": expression, "pos": pos, "level": level}
        for form in _expand_word_expression(expression):
            if record not in index[form]:
                index[form].append(record)
    if not 5000 <= len(rows) <= 7000:
        raise ValueError(f"參考詞彙表解析筆數異常：{len(rows)}")
    return dict(index)


def _morphological_candidates(token: str) -> Iterable[str]:
    token = token.lower().replace("’", "'")
    yield token
    if token in IRREGULAR_HEADWORDS:
        yield IRREGULAR_HEADWORDS[token]
    if token.endswith("'s"):
        yield token[:-2]
    if token.endswith("ies") and len(token) > 4:
        yield token[:-3] + "y"
    if token.endswith("es") and len(token) > 4:
        yield token[:-2]
        yield token[:-1]
    if token.endswith("s") and len(token) > 3:
        yield token[:-1]
        if token.endswith("ers") and len(token) > 5:
            yield token[:-3]
    if token.endswith("ied") and len(token) > 4:
        yield token[:-3] + "y"
    if token.endswith("ed") and len(token) > 4:
        yield token[:-2]
        yield token[:-1]
        if len(token) > 5 and token[-3] == token[-4]:
            yield token[:-3]
    if token.endswith("ing") and len(token) > 5:
        stem = token[:-3]
        yield stem
        yield stem + "e"
        if len(stem) > 2 and stem[-1] == stem[-2]:
            yield stem[:-1]
    for suffix in ("ly", "ness", "less"):
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            yield token[: -len(suffix)]
            if suffix == "ly" and token.endswith("ily"):
                yield token[:-3] + "y"
    for suffix in ("er", "or"):
        if token.endswith(suffix) and len(token) > len(suffix) + 3:
            yield token[: -len(suffix)]
            if token.endswith("ier"):
                yield token[:-3] + "y"
    if token.endswith("est") and len(token) > 5:
        yield token[:-3]
        yield token[:-2]
        if token.endswith("iest"):
            yield token[:-4] + "y"
        if len(token) > 6 and token[-4] == token[-5]:
            yield token[:-4]
    if token.endswith("er") and len(token) > 4:
        yield token[:-2]
        yield token[:-1]
        if token.endswith("ier"):
            yield token[:-3] + "y"
        if len(token) > 5 and token[-3] == token[-4]:
            yield token[:-3]
    for prefix in ("re", "un", "in", "im", "ir", "il", "non"):
        if token.startswith(prefix) and len(token) > len(prefix) + 3:
            yield token[len(prefix) :]


def resolve_token(token: str, index: dict[str, list[dict[str, Any]]]) -> tuple[str | None, list[dict[str, Any]]]:
    for candidate in dict.fromkeys(_morphological_candidates(token)):
        if candidate in index:
            return candidate, index[candidate]
    return None, []


def _text_tokens(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    return TOKEN_RE.findall(value.replace("’", "'"))


def _scope_for(question: dict[str, Any]) -> dict[str, Any]:
    item_spec = question.get("item_spec") if isinstance(question.get("item_spec"), dict) else {}
    scope = item_spec.get("lexical_scope") if isinstance(item_spec.get("lexical_scope"), dict) else {}
    return scope


def _question_texts(question: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for key in ("group_stimulus", "passage", "prompt", "stem", "intro"):
        if isinstance(question.get(key), str):
            texts.append(question[key])
    for option in question.get("options") or []:
        if isinstance(option, dict) and isinstance(option.get("text"), str):
            texts.append(option["text"])
        elif isinstance(option, str):
            texts.append(option)
    return texts


def validate_exam(exam: dict[str, Any], index: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    sections = {
        str(section.get("id")): str(section.get("title", ""))
        for section in exam.get("sections", [])
        if isinstance(section, dict)
    }
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    token_levels: Counter[int] = Counter()
    vocab_target_levels: Counter[int] = Counter()
    competition_types: Counter[str] = Counter()
    vocabulary_answer_positions: Counter[str] = Counter()
    competitive_vocab_items = 0
    audited_tokens = 0
    answers_by_id = {
        str(answer.get("question_id")): answer
        for answer in exam.get("answers", [])
        if isinstance(answer, dict) and answer.get("question_id") is not None
    }
    vocabulary_question_count = 0

    for question in exam.get("questions", []):
        if not isinstance(question, dict):
            continue
        qid = str(question.get("id") or question.get("number") or "unknown")
        section_title = sections.get(str(question.get("section_id")), str(question.get("section", "")))
        label = section_title.lower()
        is_reading = any(term.lower() in label for term in READING_LABELS)
        is_vocab = any(term.lower() in label for term in VOCAB_LABELS)
        scope = _scope_for(question)
        allowed = {
            str(word).lower().replace("’", "'")
            for key in ("allowed_proper_nouns", "defined_terms", "glossed_terms")
            for word in (scope.get(key) or [])
        }

        for text in _question_texts(question):
            for token in _text_tokens(text):
                audited_tokens += 1
                lowered = token.lower().replace("’", "'")
                if lowered in BASIC_FUNCTION_FORMS or len(lowered) == 1:
                    continue
                if lowered in allowed:
                    continue
                resolved, records = resolve_token(lowered, index)
                if not resolved:
                    finding = {"question_id": qid, "section": section_title, "token": token}
                    (warnings if is_reading else errors).append({"code": "off_list_token", **finding})
                    continue
                level = min(record["level"] for record in records)
                token_levels[level] += 1
                if not is_reading and level == 6 and lowered not in allowed:
                    errors.append({
                        "code": "unjustified_level_6_nonreading",
                        "question_id": qid,
                        "section": section_title,
                        "token": token,
                    })

        if not is_vocab:
            continue
        vocabulary_question_count += 1
        option_pos = scope.get("option_pos")
        target_word = scope.get("target_word")
        target_surface_form = scope.get("target_surface_form")
        target_pos = scope.get("target_pos")
        evidence = scope.get("disambiguating_evidence") or []
        confusion = scope.get("distractor_confusion_basis") or []
        options = [option for option in (question.get("options") or []) if isinstance(option, dict)]
        option_map = {str(option.get("label")): str(option.get("text") or "").strip() for option in options}
        if not isinstance(option_pos, list) or len(option_pos) != 4:
            errors.append({"code": "vocabulary_option_pos_missing", "question_id": qid})
        elif not target_pos or any(str(pos) != str(target_pos) for pos in option_pos):
            errors.append({"code": "vocabulary_options_not_same_pos", "question_id": qid})
        if not target_word:
            errors.append({"code": "vocabulary_target_word_missing", "question_id": qid})
        else:
            resolved, records = resolve_token(str(target_word), index)
            if not resolved:
                errors.append({"code": "vocabulary_target_off_list", "question_id": qid, "token": target_word})
            else:
                level = min(record["level"] for record in records)
                vocab_target_levels[level] += 1
                if level > 5:
                    errors.append({"code": "vocabulary_target_above_level_5", "question_id": qid, "token": target_word})
        answer = answers_by_id.get(qid) or {}
        answer_label = str(answer.get("final_answer") or "")
        selected_surface = option_map.get(answer_label, "")
        if answer_label:
            vocabulary_answer_positions[answer_label] += 1
        if not answer_label or not selected_surface:
            errors.append({"code": "vocabulary_answer_option_unresolved", "question_id": qid})
        if not target_surface_form:
            errors.append({"code": "vocabulary_target_surface_form_missing", "question_id": qid})
        elif selected_surface and str(target_surface_form).casefold().strip() != selected_surface.casefold():
            errors.append({
                "code": "vocabulary_target_surface_form_mismatch",
                "question_id": qid,
                "declared": target_surface_form,
                "printed": selected_surface,
            })
        if len(evidence) < 2:
            errors.append({"code": "vocabulary_evidence_too_thin", "question_id": qid})
        if len(confusion) != 3 or not all(isinstance(record, dict) for record in confusion):
            errors.append({"code": "vocabulary_distractor_logic_incomplete", "question_id": qid})
        else:
            wrong_labels = set(option_map) - {answer_label}
            recorded_labels: set[str] = set()
            strong_distractors = 0
            for record in confusion:
                label_value = str(record.get("option") or "")
                surface_value = str(record.get("surface_form") or "").strip()
                competition_type = str(record.get("competition_type") or "")
                recorded_labels.add(label_value)
                if label_value not in wrong_labels:
                    errors.append({"code": "vocabulary_distractor_record_wrong_label", "question_id": qid, "option": label_value})
                elif surface_value.casefold() != option_map[label_value].casefold():
                    errors.append({
                        "code": "vocabulary_distractor_surface_form_mismatch",
                        "question_id": qid,
                        "option": label_value,
                    })
                if competition_type not in VALID_COMPETITION_TYPES:
                    errors.append({
                        "code": "vocabulary_competition_type_invalid",
                        "question_id": qid,
                        "value": competition_type,
                    })
                else:
                    competition_types[competition_type] += 1
                if record.get("slot_feasible") is not True:
                    errors.append({"code": "vocabulary_distractor_not_slot_feasible", "question_id": qid, "option": label_value})
                if not str(record.get("initial_fit") or "").strip() or not str(record.get("defeating_evidence") or "").strip():
                    errors.append({"code": "vocabulary_distractor_evidence_incomplete", "question_id": qid, "option": label_value})
                if record.get("plausibility_after_local_read") in STRONG_PLAUSIBILITY and record.get("slot_feasible") is True:
                    strong_distractors += 1
            if recorded_labels != wrong_labels:
                errors.append({
                    "code": "vocabulary_distractor_records_do_not_cover_options",
                    "question_id": qid,
                    "expected": sorted(wrong_labels),
                    "found": sorted(recorded_labels),
                })
            if strong_distractors >= 2:
                competitive_vocab_items += 1

        explanation = answer.get("lexical_explanation") if isinstance(answer.get("lexical_explanation"), dict) else {}
        if not explanation:
            errors.append({"code": "vocabulary_lexical_explanation_missing", "question_id": qid})
        elif selected_surface:
            if str(explanation.get("selected_option_label") or "") != answer_label:
                errors.append({"code": "vocabulary_explanation_option_label_mismatch", "question_id": qid})
            if str(explanation.get("selected_surface_form") or "").casefold().strip() != selected_surface.casefold():
                errors.append({"code": "vocabulary_explanation_surface_form_mismatch", "question_id": qid})
            if len(explanation.get("evidence_cues") or []) < 2 or not str(explanation.get("context_fit") or "").strip():
                errors.append({"code": "vocabulary_explanation_evidence_incomplete", "question_id": qid})
        if selected_surface:
            rendered_reasoning = " ".join(str(value) for value in (answer.get("reasoning") or []))
            if not re.search(rf"(?<![A-Za-z]){re.escape(selected_surface)}(?![A-Za-z])", rendered_reasoning, flags=re.IGNORECASE):
                errors.append({
                    "code": "vocabulary_rendered_explanation_omits_selected_surface_form",
                    "question_id": qid,
                    "selected_surface_form": selected_surface,
                })

    vocab_count = sum(vocab_target_levels.values())
    if vocab_count and sum(count for level, count in vocab_target_levels.items() if level <= 4) / vocab_count < 0.7:
        errors.append({"code": "vocabulary_target_level_mix_too_high", "detail": "至少 70% 標的詞應為第一至四級。"})
    if vocabulary_question_count == 10:
        if not answer_positions_balanced(vocabulary_answer_positions):
            errors.append({
                "code": "vocabulary_answer_positions_unbalanced",
                "counts": dict(sorted(vocabulary_answer_positions.items())),
                "rule": "use A-D and keep max-min <= 1",
            })
        if competitive_vocab_items < 8:
            errors.append({
                "code": "vocabulary_competitive_items_too_few",
                "found": competitive_vocab_items,
                "minimum": 8,
            })
        if len(competition_types) < 5:
            errors.append({
                "code": "vocabulary_distractor_family_mix_too_narrow",
                "found": sorted(competition_types),
                "minimum_distinct_families": 5,
            })
        if competition_types.get("word_family_or_form", 0) < 1:
            errors.append({"code": "vocabulary_word_family_or_form_competition_missing"})
        if not ({"near_synonym", "polysemy"} & set(competition_types)):
            errors.append({"code": "vocabulary_semantic_near_miss_competition_missing"})
        if not ({"collocation", "argument_structure"} & set(competition_types)):
            errors.append({"code": "vocabulary_usage_competition_missing"})

    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "reference_entry_forms": len(index),
        "audited_token_count": audited_tokens,
        "token_level_counts": dict(sorted(token_levels.items())),
        "vocabulary_target_level_counts": dict(sorted(vocab_target_levels.items())),
        "vocabulary_question_count": vocabulary_question_count,
        "vocabulary_answer_position_counts": dict(sorted(vocabulary_answer_positions.items())),
        "competitive_vocabulary_item_count": competitive_vocab_items,
        "vocabulary_competition_type_counts": dict(sorted(competition_types.items())),
        "errors": errors,
        "warnings": warnings,
        "notes": [
            "非閱讀區的表外詞與未說明之第六級詞彙為硬錯誤。",
            "閱讀區表外詞為警告；仍須另做語境、註解與可推知性審查。",
            "通過詞表檢查不代表題目具有足夠鑑別度。",
            "詞彙題的正確印刷字形、答案標籤與會印入詳解的用字必須逐題一致；詳解不得悄悄換成另一個近義詞。",
            "完整卷的十題詞彙題必須展現多種有效混淆機制，且至少八題在局部閱讀後仍有兩個具誘因的錯項。",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exam_json", type=Path)
    parser.add_argument("reference_pdf", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam_json.read_text(encoding="utf-8-sig"))
    index = parse_reference_pdf(args.reference_pdf)
    report = validate_exam(exam, index)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
