#!/usr/bin/env python3
"""Validate GSAT English lexical scope against the CEEC 高中英文參考詞彙表.

The list ships with the Skill as
exam_packs/學測/shared-data/ceec-english-vocabulary-list.json (parsed from
https://www.ceec.edu.tw/SourceUse/ce37/4.pdf, 6,474 headwords in six levels), so the
check runs when a hosted batch is saved, not only at the local release gate.

Calibration on the official 111-115 booklets (2026-09-23), answers of the ten
詞彙題 per year by level: 1:1, 2:7, 3:11, 4:20, 5:6, 6:2, unresolved 2 of 50
(113 randomly and 115 consumption are level 6; 112 supposedly and 113 compulsory
are not headwords). Distractors include 3-6 level-6 words a year. Items 1-34
(詞彙, 綜合測驗, 文意選填, 篇章結構) carry 1.9-3.1% tokens outside the list and
2.2-5.4% level-6 tokens once proper nouns, contractions, hyphenated compounds and
inflected forms are excluded; the reading passages 4.5-7.3% and 2.1-4.5%. The
former rules (no off-list or level-6 token outside reading, every target at most
level 5, 70% of targets at levels 1-4) rejected every official year and are
replaced by the rates below.

The validator still separates list membership from item quality: vocabulary
items must carry explicit lexical-design metadata so a paper cannot pass merely
by using easy words.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = ROOT / "exam_packs" / "學測" / "shared-data" / "ceec-english-vocabulary-list.json"
NONREADING_OFF_LIST_RATE_MAX = 0.05     # official 1.9-3.1%
NONREADING_LEVEL_6_RATE_MAX = 0.07      # official 2.2-5.4%
READING_OFF_LIST_RATE_MAX = 0.10        # official 4.5-7.3% (warning)
VOCAB_TARGET_LEVEL_6_MAX = 1            # official 0, 0, 1, 0, 1
VOCAB_TARGET_OFF_LIST_MAX = 1           # official 0, 1, 1, 0, 0
VOCAB_TARGETS_LEVEL_1_4_MIN = 6         # official 8, 9, 8, 8, 7 of 10
VOCAB_TARGETS_LEVEL_5_6_MIN = 1         # official 2, 1, 1, 2, 3 of 10
BANK_OFF_LIST_MAX = 1                   # 文意選填 (A)-(J): official 1, 1, 2, 0, 0 unresolved (risky, absorption, fateful)
BANK_LEVEL_4_PLUS_MIN = 2               # official 4, 4, 2, 4, 3 words at level 4-6
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
# Irregular forms, comparatives, compounds of pronouns and transparent derivations
# met in the official 111-115 booklets; each maps to the CEEC headword it is read from.
IRREGULAR_HEADWORDS.update({
    "brought": "bring",
    "seen": "see",
    "men": "man",
    "teeth": "tooth",
    "lost": "lose",
    "said": "say",
    "paid": "pay",
    "built": "build",
    "met": "meet",
    "rung": "ring",
    "sprang": "spring",
    "shown": "show",
    "given": "give",
    "goes": "go",
    "going": "go",
    "dying": "die",
    "doing": "do",
    "got": "get",
    "fallen": "fall",
    "meant": "mean",
    "died": "die",
    "women": "woman",
    "children": "child",
    "feet": "foot",
    "taken": "take",
    "made": "make",
    "done": "do",
    "known": "know",
    "written": "write",
    "thought": "think",
    "bought": "buy",
    "caught": "catch",
    "taught": "teach",
    "fought": "fight",
    "sought": "seek",
    "left": "leave",
    "felt": "feel",
    "kept": "keep",
    "slept": "sleep",
    "held": "hold",
    "told": "tell",
    "sold": "sell",
    "stood": "stand",
    "understood": "understand",
    "found": "find",
    "heard": "hear",
    "led": "lead",
    "ran": "run",
    "began": "begin",
    "begun": "begin",
    "sang": "sing",
    "sung": "sing",
    "drank": "drink",
    "drunk": "drink",
    "swam": "swim",
    "grew": "grow",
    "grown": "grow",
    "knew": "know",
    "threw": "throw",
    "thrown": "throw",
    "flew": "fly",
    "flown": "fly",
    "drew": "draw",
    "drawn": "draw",
    "wore": "wear",
    "worn": "wear",
    "tore": "tear",
    "torn": "tear",
    "chose": "choose",
    "chosen": "choose",
    "spoke": "speak",
    "spoken": "speak",
    "broke": "break",
    "broken": "break",
    "woke": "wake",
    "rose": "rise",
    "risen": "rise",
    "drove": "drive",
    "driven": "drive",
    "wrote": "write",
    "rode": "ride",
    "ridden": "ride",
    "hid": "hide",
    "hidden": "hide",
    "bit": "bite",
    "bitten": "bite",
    "fed": "feed",
    "bled": "bleed",
    "sat": "sit",
    "shot": "shoot",
    "struck": "strike",
    "stuck": "stick",
    "swung": "swing",
    "hung": "hang",
    "dug": "dig",
    "won": "win",
    "spun": "spin",
    "forgot": "forget",
    "forgotten": "forget",
    "became": "become",
    "came": "come",
    "gave": "give",
    "saw": "see",
    "went": "go",
    "ate": "eat",
    "eaten": "eat",
    "fell": "fall",
    "laid": "lay",
    "lain": "lie",
    "lit": "light",
    "sent": "send",
    "spent": "spend",
    "lent": "lend",
    "bent": "bend",
    "dealt": "deal",
    "dreamt": "dream",
    "burnt": "burn",
    "learnt": "learn",
    "shook": "shake",
    "shaken": "shake",
    "froze": "freeze",
    "frozen": "freeze",
    "stole": "steal",
    "stolen": "steal",
    "beaten": "beat",
    "forgave": "forgive",
    "forgiven": "forgive",
    "arose": "arise",
    "arisen": "arise",
    "awoke": "awake",
    "bore": "bear",
    "borne": "bear",
    "born": "bear",
    "bound": "bind",
    "bred": "breed",
    "clung": "cling",
    "crept": "creep",
    "fled": "flee",
    "flung": "fling",
    "forbade": "forbid",
    "forbidden": "forbid",
    "knelt": "kneel",
    "leapt": "leap",
    "mistook": "mistake",
    "mistaken": "mistake",
    "overcame": "overcome",
    "shrank": "shrink",
    "shrunk": "shrink",
    "slid": "slide",
    "sank": "sink",
    "sunk": "sink",
    "spat": "spit",
    "sprung": "spring",
    "stung": "sting",
    "strove": "strive",
    "swept": "sweep",
    "swore": "swear",
    "sworn": "swear",
    "undertook": "undertake",
    "undertaken": "undertake",
    "withdrew": "withdraw",
    "withdrawn": "withdraw",
    "wept": "weep",
    "woven": "weave",
    "wove": "weave",
    "mice": "mouse",
    "geese": "goose",
    "oxen": "ox",
    "people": "person",
    "best": "good",
    "better": "good",
    "worse": "bad",
    "worst": "bad",
    "less": "little",
    "least": "little",
    "more": "much",
    "most": "much",
    "farther": "far",
    "further": "far",
    "farthest": "far",
    "furthest": "far",
    "everything": "every",
    "everywhere": "every",
    "everyone": "every",
    "everybody": "every",
    "himself": "him",
    "herself": "her",
    "themselves": "them",
    "myself": "my",
    "yourself": "your",
    "itself": "it",
    "ourselves": "our",
    "nobody": "no",
    "nothing": "no",
    "nowhere": "no",
    "somebody": "some",
    "someone": "some",
    "something": "some",
    "somewhere": "some",
    "anybody": "any",
    "anyone": "any",
    "anything": "any",
    "anywhere": "any",
    "truly": "true",
    "using": "use",
    "gone": "go",
    "lying": "lie",
    "tying": "tie",
    "paying": "pay",
    "says": "say",
    "has": "have",
    "does": "do",
    "cannot": "can",
    "online": "line",
    "probably": "probable",
    "surprisingly": "surprising",
    "specifically": "specific",
    "understandably": "understand",
    "periodically": "periodic",
    "harmonically": "harmonic",
    "legitimately": "legitimate",
    "relevantly": "relevant",
    "persistently": "persistent",
    "genetically": "genetic",
    "literally": "literal",
    "alternatively": "alternative",
    "ultimately": "ultimate",
    "undoubtedly": "doubt",
    "supposedly": "suppose",
    "randomly": "random",
    "verbally": "verbal",
    "initially": "initial",
    "potentially": "potential",
    "eventually": "eventual",
    "originally": "original",
    "generally": "general",
    "usually": "usual",
    "finally": "final",
    "especially": "especial",
    "particularly": "particular",
    "recently": "recent",
    "immediately": "immediate",
    "actually": "actual",
    "totally": "total",
    "hardly": "hard",
    "nearly": "near",
    "mostly": "most",
    "entirely": "entire",
    "happiness": "happy",
    "friendliness": "friendly",
    "cleanliness": "clean",
    "timeliness": "timely",
    "responsiveness": "responsive",
    "weightlessness": "weight",
    "stupidity": "stupid",
    "consistency": "consistent",
    "affordable": "afford",
    "adjustable": "adjust",
    "manageable": "manage",
    "trustworthy": "trust",
    "hurtful": "hurt",
    "heartwarming": "heart",
    "smelly": "smell",
    "puffy": "puff",
    "bumpy": "bump",
    "risky": "risk",
    "fateful": "fate",
    "soulful": "soul",
    "forceful": "force",
    "eligibly": "eligible",
    "misguided": "guide",
    "unbiased": "bias",
    "outdated": "date",
    "reopened": "open",
    "redistributed": "distribute",
    "redistributing": "distribute",
    "disrupted": "disrupt",
    "outermost": "outer",
    "northeastern": "northeast",
    "hilltop": "hill",
    "treetops": "tree",
    "headaches": "headache",
    "shoppers": "shopper",
    "bookshop": "bookshop",
    "bookshops": "bookshop",
    "smartphones": "smartphone",
    "newcomers": "newcomer",
    "nappers": "nap",
    "passersby": "passerby",
    "shelves": "shelf",
    "icons": "icon",
    "delicacies": "delicacy",
    "shootings": "shooting",
    "manifestations": "manifestation",
    "eyesores": "eyesore",
    "lifelike": "life",
    "masterful": "master",
    "festive": "festival",
    "filmmaking": "film",
    "imagery": "image",
    "keywords": "keyword",
    "absorption": "absorb",
    "provision": "provide",
    "precedence": "precede",
    "shrinkage": "shrink",
    "contentment": "content",
    "cognition": "cognitive",
    "accompaniment": "accompany",
    "restoration": "restore",
    "photosynthesis": "photosynthesis",
    "dementia": "dementia",
    "pandemic": "pandemic",
    "liability": "liable",
    "siblings": "sibling",
    "nausea": "nausea",
    "syndrome": "syndrome",
    "devastating": "devastate",
    "agonizing": "agony",
    "deceased": "decease",
    "evoked": "evoke",
    "intermix": "mix",
    "jigsaw": "jigsaw",
    "lactose": "lactose",
    "hydrated": "hydrate",
    "hydration": "hydrate",
    "ideology": "ideology",
    "swollen": "swell",
    "perceptual": "perceive",
    "blackout": "black",
    "campfire": "camp",
    "snooze": "snooze",
    "poop": "poop",
    "tendon": "tendon",
    "checklist": "check",
    "cutback": "cut",
    "counterproductive": "productive",
    "compulsory": "compulsory",
    "deformation": "deform",
    "disintegrating": "disintegrate",
    "pressurization": "pressure",
    "acrobatic": "acrobat",
    "aesthetics": "aesthetic",
    "antiquarian": "antique",
    "altars": "altar",
    "bonfire": "bonfire",
    "eggplants": "eggplant",
    "horseback": "horse",
    "kimonos": "kimono",
    "midair": "air",
    "rams": "ram",
    "breakage": "break",
    "microgravity": "gravity",
    "fiberglass": "fiber",
    "coronations": "coronation",
    "minimalist": "minimal",
    "acoustic": "acoustic",
    "claustrophobic": "claustrophobic",
    "cued": "cue",
    "dizziness": "dizzy",
    "intricate": "intricate",
    "seasonal": "season",
    "brightening": "bright",
    "culinary": "culinary",
    "individualism": "individual",
    "unsmiling": "smile",
    "underlying": "underlie"
})


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


def build_index(rows: Iterable[tuple[str, str, int]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for expression, pos, level in rows:
        record = {"entry": expression, "pos": pos, "level": int(level)}
        for form in _expand_word_expression(expression):
            if record not in index[form]:
                index[form].append(record)
    return dict(index)


def load_reference(path: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """The shipped JSON list (default) or the official PDF."""
    path = Path(path) if path else DEFAULT_REFERENCE
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = [(str(r[0]), str(r[1]), int(r[2])) for r in data.get("rows") or []]
        if not 5000 <= len(rows) <= 7000:
            raise ValueError(f"參考詞彙表解析筆數異常：{len(rows)}")
        return build_index(rows)
    return parse_reference_pdf(path)


def _audit_skip(token: str) -> bool:
    """Proper nouns, contractions, hyphenated compounds and one- or two-letter tokens are not scope evidence."""
    return token[0].isupper() or "'" in token or "-" in token or len(token) <= 2


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
    off_list: dict[str, list[dict[str, Any]]] = {"reading": [], "nonreading": []}
    counted: Counter[str] = Counter()
    level_6: dict[str, list[str]] = {"reading": [], "nonreading": []}
    bank_words: list[str] = []
    vocab_level_6_targets: list[str] = []
    vocab_off_list_targets: list[str] = []

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

        kind = "reading" if is_reading else "nonreading"
        if "文意選填" in section_title and isinstance(question.get("group_stimulus"), str) and not bank_words:
            bank_words = [word.strip() for _, word in re.findall(r"\(([A-J])\)\s*([A-Za-z][A-Za-z' -]*?)(?=\s*\(|\n|$)",
                                                                   question["group_stimulus"].replace("’", "'"), flags=re.M)]
        for text in _question_texts(question):
            for token in _text_tokens(text):
                audited_tokens += 1
                lowered = token.lower().replace("’", "'")
                if lowered in BASIC_FUNCTION_FORMS or lowered in allowed or _audit_skip(token):
                    continue
                counted[kind] += 1
                resolved, records = resolve_token(lowered, index)
                if not resolved:
                    off_list[kind].append({"question_id": qid, "section": section_title, "token": token})
                    continue
                level = min(record["level"] for record in records)
                token_levels[level] += 1
                if level == 6:
                    level_6[kind].append(token)

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
                vocab_off_list_targets.append(str(target_word))
                warnings.append({"code": "vocabulary_target_off_list", "question_id": qid, "token": target_word})
            else:
                level = min(record["level"] for record in records)
                vocab_target_levels[level] += 1
                if level == 6:
                    vocab_level_6_targets.append(str(target_word))
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

    # Scope rates measured on the official 111-115 booklets (see module docstring).
    for kind, rate_max, code in (("nonreading", NONREADING_OFF_LIST_RATE_MAX, "nonreading_off_list_rate_too_high"),
                                 ("reading", READING_OFF_LIST_RATE_MAX, "reading_off_list_rate_high")):
        warnings.extend({"code": "off_list_token", **finding} for finding in off_list[kind])
        if counted[kind] >= 40:
            rate = len(off_list[kind]) / counted[kind]
            if rate > rate_max:
                (errors if kind == "nonreading" else warnings).append({
                    "code": code, "rate": round(rate, 4), "maximum": rate_max, "tokens": sorted({f["token"] for f in off_list[kind]}),
                    "detail": "官方 111-115 第1-34題表外詞 1.9-3.1%、閱讀 4.5-7.3%（專有名詞、縮寫、連字號複合詞不計）；"
                              "表外詞須在 item_spec.lexical_scope.allowed_proper_nouns／glossed_terms 說明或改用詞彙表用字。",
                })
    if counted["nonreading"] >= 40 and len(level_6["nonreading"]) / counted["nonreading"] > NONREADING_LEVEL_6_RATE_MAX:
        errors.append({"code": "unjustified_level_6_nonreading", "rate": round(len(level_6["nonreading"]) / counted["nonreading"], 4),
                       "maximum": NONREADING_LEVEL_6_RATE_MAX, "tokens": sorted(set(level_6["nonreading"])),
                       "detail": "官方 111-115 第1-34題第六級詞 2.2-5.4%；第六級只能零星出現。"})
    if counted["nonreading"] < 40 and level_6["nonreading"] and counted["nonreading"] and len(level_6["nonreading"]) / counted["nonreading"] > NONREADING_LEVEL_6_RATE_MAX:
        errors.append({"code": "unjustified_level_6_nonreading", "tokens": sorted(set(level_6["nonreading"]))})
    if bank_words:
        bank_levels = []
        for word in bank_words:
            levels = []
            for token in TOKEN_RE.findall(word):
                resolved, records = resolve_token(token, index)
                levels.append(min(r["level"] for r in records) if resolved else None)
            bank_levels.append((word, max((l for l in levels if l is not None), default=None) if all(l is not None for l in levels) else None))
        unresolved = [w for w, l in bank_levels if l is None]
        if len(unresolved) > BANK_OFF_LIST_MAX:
            errors.append({"code": "completion_bank_off_list", "words": unresolved, "maximum": BANK_OFF_LIST_MAX,
                           "detail": "文意選填十個選項須為參考詞彙表用字（官方 111-115 每年至多 1-2 個非表內字）。"})
        if len(bank_levels) >= 8 and sum(1 for _, l in bank_levels if l and l >= 4) < BANK_LEVEL_4_PLUS_MIN:
            errors.append({"code": "completion_bank_too_easy", "levels": [l for _, l in bank_levels], "minimum_level_4_plus": BANK_LEVEL_4_PLUS_MIN,
                           "detail": "官方 111-115 文意選填選項每年有 2-4 個第四級以上用字。"})
    if len(vocab_level_6_targets) > VOCAB_TARGET_LEVEL_6_MAX:
        errors.append({"code": "vocabulary_target_level_6_more_than_one", "tokens": vocab_level_6_targets,
                       "detail": "官方 111-115 每卷至多一個第六級標的詞（113 randomly、115 consumption）。"})
    if len(vocab_off_list_targets) > VOCAB_TARGET_OFF_LIST_MAX:
        errors.append({"code": "vocabulary_target_off_list_more_than_one", "tokens": vocab_off_list_targets})
    if vocabulary_question_count == 10:
        easy = sum(count for level, count in vocab_target_levels.items() if level <= 4)
        demanding = sum(count for level, count in vocab_target_levels.items() if level >= 5)
        if easy < VOCAB_TARGETS_LEVEL_1_4_MIN:
            errors.append({"code": "vocabulary_target_level_mix_too_high", "found_level_1_4": easy, "minimum": VOCAB_TARGETS_LEVEL_1_4_MIN,
                           "detail": "官方 111-115 十題標的詞第一至四級為 8、9、8、8、7 題。"})
        if demanding < VOCAB_TARGETS_LEVEL_5_6_MIN:
            errors.append({"code": "vocabulary_target_level_mix_too_low", "found_level_5_6": demanding, "minimum": VOCAB_TARGETS_LEVEL_5_6_MIN,
                           "detail": "官方 111-115 每卷有 1-3 個第五、六級標的詞（potentially、quest、blurring、vacancy、assaulted…）。"})
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
    parser.add_argument("reference", type=Path, nargs="?", help="CEEC list JSON (default: the shipped list) or the official PDF")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    exam = json.loads(args.exam_json.read_text(encoding="utf-8-sig"))
    reference = args.reference if args.reference and args.reference.is_file() else DEFAULT_REFERENCE
    index = load_reference(reference)
    report = validate_exam(exam, index)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
