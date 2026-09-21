# Current GSAT reading load and reasoning depth: 國綜, 國寫, 英文, 社會, 自然

Mathematics A and B already carry a pre-writing construction gate in
[math-difficulty-design.md](math-difficulty-design.md), and reviewer testing
accepts those two papers. The other five current-form subjects had no
equivalent, and generated papers collapsed in three specific ways that this
reference now blocks:

1. items solvable by one formula substitution or one definition lookup;
2. papers printing roughly half the reading material of an official booklet;
3. 自然 第貳部分 題組 that stay inside one discipline.

Read this before writing any 國綜, 國寫, 英文, 社會 or 自然 item. It is a
construction floor, not a writing target, and never a licence to pad. Its
companion [current-form-topicality.md](current-form-topicality.md) fixes the
other measured gap of the same review: how many recent, Taiwan-anchored and
hazard contexts an official paper carries.

## Measured envelope, ROC 111–115

`exam_packs/學測/shared-data/current-form-literacy-envelope.json` is produced by
`scripts/analyze_current_form_literacy.py` from the supplied official booklets.
`substantive_compact_chars` strips repeated page furniture (running header,
footer, signature banner), so it is **lower** than the whole-PDF `compact_chars`
in `current-chinese-natural-density.json`. The two are not interchangeable.

| Subject | Pages | Substantive chars (min–max) | Shared-stimulus 題組 per paper |
|---|---:|---:|---:|
| 國綜 | 12 | 11,926 – 12,871 | 9 – 10 |
| 國寫 | 3 – 4 | 1,528 – 1,908 | two 大題, each with its own packet |
| 英文 | 12 | 18,142 – 19,230 (3,321 – 3,550 English words) | 7 – 8 |
| 社會 | 18 – 20 | 13,446 – 15,269 | 14 – 19 |
| 自然 | 19 – 20 | 13,517 – 15,243 | 9 – 12 |

Two measurement limits are disclosed rather than hidden. Where an official group
prints its table or figure *after* the item numbers, the extracted stimulus
length is near zero (a few 15-character rows in the 國綜 series); read those as
"not separately measurable", not as a 15-character stimulus. And the English
section bands below count every English word printed in a section, directions,
stems and options included, so they are section budgets, not passage lengths.

## Whole-paper substantive floor

Before rendering, measure the authored exam's printed student-facing text and
compare it with the weakest official year. Compare like with like: the gate
reads the exam record, which holds unique group stimuli, item prompts, option
text and printed tables — not the cover page and not the section 說明 blocks,
which the Layout Profile prints. The envelope records that basis separately as
`item_content_compact_chars`. The floor is 0.85 of the weakest year on it:

| Subject | Weakest official year (item content) | Release floor |
|---|---:|---:|
| 國綜 | 10,727 chars | 9,117 chars |
| 國寫 | 1,109 chars | 942 chars |
| 英文 | 3,004 English words | 2,553 English words |
| 社會 | 12,709 chars | 10,802 chars |
| 自然 | 12,573 chars | 10,687 chars |

Using the whole-booklet figure here would be a miscalibration, not a stricter
gate: for 國寫 the cover and directions are the difference between 1,528 and
1,109 characters, so a floor drawn from the larger number would have rejected a
paper shaped exactly like ROC 111.

Do not count directions boilerplate, answer ruling, decorative labels, figure
bounding boxes, or repeated page furniture. A paper below its floor is rejected
and repaired by restoring genuine source material and complete item blocks;
never by enlarging type, inflating figures, widening answer space, or appending
`來源補充`.

This gate runs on the authored exam data **before** layout, so a thin paper is
caught before a full booklet is composed. It does not replace the post-render
PDF comparison in `validate_current_form_density.py`.

## Shared stimulus is the form, not an option

The single largest structural cause of a thin, easy paper is writing every item
as a standalone one- or two-sentence scenario. Official papers do not do this.
Most scored items sit in 題組 that share one substantial stimulus, **including
inside 第壹部分**, where a generated paper is most likely to omit them.

| Subject | 第壹部分 題組 | Items they carry | 第貳部分 題組 |
|---|---:|---:|---:|
| 自然 | 3 – 6 | 6 – 12 | exactly 6 |
| 社會 | 5 – 10 | 13 – 24 | 8 – 11 |
| 國綜 | 7 – 9 | 19 – 21 | 1 – 2 |
| 英文 | 7 | 36 | 1 |

Release floors: 自然 needs at least **3 第壹部分 題組 carrying at least 6 items**
and exactly **6 第貳部分 題組**; 社會 needs at least **5 第壹部分 題組** and at least
**7 第貳部分 題組**; 國綜 needs at least **8 題組** in total. A group exists when two
or more scored items genuinely depend on the same printed material. Numbering
two unrelated items consecutively under one header is not a 題組.

### Stimulus length floors

Judge the group stimulus — the material printed between the group header and
its first numbered item — not the item stems.

| Subject / part | Official per-year median | Floor: median | Floor: short groups |
|---|---:|---:|---|
| 自然 第貳部分 | 188 – 365 | ≥ 175 chars | at most 2 groups under 120 chars |
| 自然 第壹部分 | 100 – 198 | ≥ 90 chars | — |
| 社會 (all groups) | 203 – 271 | ≥ 170 chars | at most 30% under 110 chars |
| 國綜 第壹部分 | 365 – 572 | ≥ 300 chars | — |

Each floor sits below the weakest official year, so no official paper would be
rejected by it. ROC 113 自然 is the binding case at median 188 with two groups
under 120 characters; that is the shape the floor permits, not a target.

## Per-item reasoning floor

Every scored item keeps its subject contract — `natural_reasoning_contract`,
`social_reasoning_contract`, `english_difficulty_contract`, and now
`chinese_reasoning_contract` for 國綜, which had no per-item floor at all —
and also satisfies the following, which mirrors the anti-collapse rule
mathematics already applies.

An item fails if a proficient candidate can reach the key by:

- recalling one definition, name, date, law, or classification;
- substituting given numbers into one named formula once;
- reading one labelled value off one figure or table;
- applying the same mechanical test to five options with no change of model.

Counting written solution lines does not establish reasoning depth. A step
counts as a **linked operation** only when it requires a new decision: choosing
a model, changing representation, controlling a variable, reconciling a
constraint, comparing competing explanations, bounding an uncertainty, or
testing a limiting case. Repeating one operation with different numbers is one
operation.

| Declared band | Minimum linked operations |
|---|---:|
| 簡單 | 2, at least one of them non-mechanical |
| 中 | 3 |
| 中偏難 / 難 | 3, with at least two distinct bottlenecks |

`簡單` means a short, transparent evidence chain, not a recall prompt. An
accessible item earns its band through a discoverable route, never a one-line
substitution.

Every item also records why its printed material is required. Apply the
stimulus-removal test in [stimulus-generation.md](stimulus-generation.md) and
the source-relation test in
[evidence-backed-editorial-audit.md](evidence-backed-editorial-audit.md): if the
item survives deletion of the stimulus, or of the relation the stimulus
supplies, it is decorative and must be rewritten or relabelled.

## 自然: cross-disciplinary mixed groups

`exam_packs/學測/shared-data/natural-mixed-group-cross-discipline.json` records
the maintainer's reading of all thirty official 第貳部分 題組 in ROC 111–115.
CEEC's own 試題特色 tables declare exactly **two** 合科 題組 in every one of
those five papers (111: 37–42, 49–54; 112: 51–54, 55–60; 113: 40–43, 50–53;
114: 40–43, 50–54; 115: 40–43, 50–53). The maintainer's wider reading, which
also counts groups where a second discipline is load-bearing without being
co-credited, finds three to five (median 4, share 0.63).

At least **two of the six** 第貳部分 題組 must require concepts from two or more
of 物理／化學／生物／地科 to reach the scored answers. Two is the CEEC-declared
count in every official year, and the validator's test — a second discipline
that cannot be deleted without changing the solution — is the standard CEEC
uses to label a group 合科, so a floor of three would have rejected every
official paper under that definition. Declare each such group in
`metadata.natural_mixed_group_designs`, the record `validate_chinese_natural_scope.py`
already defines: `question_numbers`, `required_domains` (two or more), a concrete
`evidence_bridge`, plus `second_discipline_removable: false`. Only
cross-disciplinary groups are listed. The declaration alone never establishes the
crossing: at least one subpart in the group must record a different
`item_spec.domain`, or declare `item_spec.secondary_domains`.

A group is cross-disciplinary only when deleting the second discipline changes
the solution. Naming a second field, setting a biology question in a laboratory,
or mentioning climate in an earth-science stem does not qualify. The official
pattern is a shared physical object or measurement that forces the crossing:

- 115 野生菸草花蜜 — printed structural formulas of 苄丙酮 and 尼古丁 (化學) drive
  a pollination and reproductive-success argument (生物);
- 114 二氧化鈦光觸媒 — band-gap excitation (物理) produces the radicals that do
  the decomposition chemistry (化學);
- 113 捕蠅草捕器 — cell turgor (生物) is resolved through a mechanical closure
  mechanism (物理);
- 111 都卜勒血流儀 — wave frequency shift (物理) is the measurement instrument for
  a circulatory response (生物).

The 第壹部分 discipline-block rule in
[current-gsat-chinese-natural-form.md](current-gsat-chinese-natural-form.md)
still stops at question 36 and is unchanged; this floor applies to 第貳部分 only.

## Failure pattern: the measured counter-example

A generated ROC 116 自然 paper reviewed on 2026-09-21 failed every floor above.
The numbers are recorded here because they show what collapse looks like:

| Metric | Official 111–115 | That paper |
|---|---:|---:|
| Substantive chars | 13,517 – 15,243 | 7,853 (58% of the weakest year) |
| Whole-PDF compact chars | 13,909 – 15,970 | 8,248 (59%) |
| 第壹部分 題組 | 3 – 6 | 0 |
| 第貳部分 stimulus median | 188 – 365 | 77 |
| Groups under 120 chars | at most 2 of 6 | 6 of 6 |
| Cross-disciplinary mixed groups | 2 of 6 declared by CEEC; 3 – 5 in the wider reading | 0 of 6 |

Its items were internally correct. They were short, single-discipline, and
solvable by one substitution — a dilution calculation, a titration equivalence
point, a plate-speed subtraction, an `F = ma` on a uniform acceleration table.
Correct and in scope is not the same as calibrated.

## Validation

Run `scripts/validate_literacy_load.py` on the authored exam before layout:

```bash
python scripts/validate_literacy_load.py generated-exam.json --subject 自然 --report output/literacy-load.json
```

It checks the whole-paper substantive floor, group counts, group stimulus
lengths, and — for 自然 — the cross-disciplinary mixed-group floor. A structural
pass is not an editorial pass: a human reviewer must still confirm that the
declared linked operations, evidence bridges and cross-discipline dependencies
exist in the printed material.

Subject scope audits (`validate_chinese_natural_scope.py`,
`validate_social_item_design.py`, `validate_english_difficulty_design.py`) and
the post-render density comparison remain required and are not superseded.
