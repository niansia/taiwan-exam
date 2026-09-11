# Current GSAT mathematics difficulty and discrimination design

Use this reference for every current-form Math A or Math B item. It converts official position-level P/D evidence into a pre-pilot construction gate. It does not claim that an unpiloted item has achieved an official P or D.

## Separate four questions

For each item, keep these judgments separate:

1. **Target severity** — the official position/section P target and observed range.
2. **Solution demand** — the irreducible mathematical decisions a proficient student must make.
3. **Discrimination design** — the point at which a partially prepared student is likely to take a plausible wrong path while a proficient student can recover.
4. **Achieved statistics** — P and D observed only after a representative administration.

An answer key with three written lines does not prove three reasoning decisions. Expanding arithmetic, repeating one transformation, or applying the same determinant/recurrence rule several times counts as one decision unless a new model, representation, condition, case, or consistency check must be chosen.

## Required `difficulty_design` record

Every scored item must record:

- `target_basis`, `target_p_center`, `target_p_range`, `target_d_floor`, and `metric_type`; objective values must agree with the selected official profile;
- `minimum_linked_decisions` and `linked_decisions`, where every entry names a distinct choice or inference and the evidence that triggers it;
- `representation_changes` and `constraint_checks` as non-negative integers;
- `misconception_paths`, each with a distinct mathematical error and its predicted wrong conclusion;
- `discrimination_design.level` (`low`, `medium`, or `high`), the tempting lower-performing move, and the proficient move that resolves it;
- `shortcut_audit`, including the shortcuts attempted, `collapse_found: false`, and `reviewer_decision: pass-no-collapse`;
- `burden_audit` confirming that arithmetic volume, prose length, and outside knowledge are not the primary difficulty source;
- `time_audit` giving a realistic hand-calculation route, expected minutes, and explicit confirmation that neither a calculator nor exhaustive enumeration is required;
- an expert-estimated difficulty band and confidence, explicitly marked provisional until pilot testing.

Use `templates/math-difficulty-design-record.json` as the field contract. The placeholder is not evidence of a pass.

## Anti-collapse thresholds

Use the selected official position target. Before pilot data, the following are construction minima, not psychometric conversions:

| Target P center | Minimum linked decisions | Additional gate |
|---:|---:|---|
| `>= 0.65` | 2 | At least one representation choice, condition check, or plausible misconception |
| `0.40–0.64` | 2 | Normally 3 when the slot is past the first two positions of its section |
| `0.20–0.39` | 3 | At least one representation change, case distinction, or non-obvious constraint reconciliation |
| `< 0.20` | 4 | At least two distinct bottlenecks; one shortcut must appear viable before being rejected |

For selected-response items, evaluating five statements by the same mechanical test is not five linked decisions. For fill-in items, producing several digits is not additional reasoning. For mixed groups, reuse of an earlier result counts as one link only when the later subpart must reinterpret, test, or extend it.

The first item after a section reset may be accessible, but it must not default to reading one value and substituting once. Later fill-in slots require special scrutiny because an apparently compact answer rail can hide an underpowered textbook exercise.

### Math B feedback floor

For every complete Math B paper, apply this stricter feedback-informed floor without changing the official position targets:

- every item labelled `簡單` or `中` must still contain at least three genuine linked decisions; accessibility should come from a discoverable route, not from a one-line substitution;
- the first three fill-in items must each combine at least three linked decisions with a total of at least two representation changes and constraint checks;
- `shortcut_audit.direct_formula_substitution_only` must be `false` for every item;
- `difficulty_design.innovation_audit` must record `formula_or_definition_recall_only: false`, `skin_swap_changes_solution_graph: true`, a concrete nearest-neighbour structural difference, and `reviewer_decision: pass-nonroutine`;
- a latitude/longitude conversion by itself fails. The coordinates must feed a spherical distance, route comparison, or navigation constraint that still needs at least three operations.

Record the paper-level declaration in `metadata.math_b_difficulty_floor` with `easy_medium_minimum_linked_decisions: 3`, `first_three_fill_ins_nonroutine: true`, and `audit_status: pass`. These fields are review evidence, not permission to relabel a routine item; the human audit must verify that the printed question actually realizes the record.

## Failure patterns

Reject an item for a medium/hard slot when its complete solution can be reduced to one familiar routine, even if the prose or notation is elaborate. Typical failures include:

- solve one exposed 2-by-2 linear system and apply a requested arithmetic expression;
- infer one area multiplier and raise it to a stated power with no further decision;
- combine an already signposted formula and discard an obviously invalid root;
- copy values from a table into a formula named in the stem;
- make difficulty by unwieldy fractions, large numbers, or long scene-setting text.

These are failure examples, not forbidden topics. The same syllabus content can be used when the new object genuinely requires selecting a representation, reconciling constraints, handling a case, or checking global consistency.

## Unit-coverage depth

Do not mark a major unit as covered merely because one easy tagged item appears. Compare the sampled paper with the multi-year aggregate coverage envelope and inspect both frequency and depth. A recurring major unit that is omitted, or represented only by direct substitution, needs a documented blueprint reason.

For functions and graphs, distinguish coefficient manipulation from structural understanding. For this Skill's complete 20-item Math A product contract, include one or two `F-10-2` cubic-function items: never zero, never more than two. If there are two, they must use different objects and reasoning mechanisms. Give meaningful opportunity to reason about graph symmetry, translation, intersections, factor/remainder information, sign, or global/local behavior. A user screenshot or past item only establishes the desired reasoning density; never reuse its polynomial, assertions, or solution graph.

For this Skill's complete 20-item Math A product contract, also include at least one `D-10-3` counting/combinatorics item. At least one such item must carry `medium` or `high` discrimination, contain three genuinely linked decisions, and require a case distinction, inclusion-exclusion, complementary count, symmetry argument with a nontrivial exception, or reconciliation of two constraints. A direct factorial/product calculation, one fixed slot pattern followed by division by two, or exhaustive listing does not satisfy the paper-level depth requirement even if it is correct. The intended short route must remain feasible by hand.

## Feedback-informed tightening

Treat timed external review as pilot evidence about the generated paper, not as permission to overwrite official P/D records. When several reviewers place a paper around official Math A or slightly below it and clearly below a target mock-exam level, tighten the next paper modestly:

- preserve section-entry resets and the official time budget;
- strengthen three to five underpowered slots by adding one real decision, representation change, or constraint reconciliation;
- prefer revising the easiest late multiple-selection, sole combinatorics item, and late fill-in slots before touching the opening item;
- keep every hard item on a discoverable short route and keep the complete hand-solving estimate within 80–92 minutes;
- do not manufacture severity through longer prose, unpleasant arithmetic, rare terminology, or more cases than can reasonably be checked in time.

Record the feedback statement, affected slots, structural change, and anticipated direction of change separately from official targets. The next paper remains `expert-estimated` until representative timed pilot results exist. Preserve only the successful design principle of a praised item—such as one shared object supporting distinct option-level inferences—not its recurrence, values, context, propositions, or solution graph.

## Discrimination design

A designed discriminator must be mathematically diagnostic rather than tricky wording. Record:

- what incomplete understanding is likely to do;
- why that move remains locally plausible;
- what evidence or invariant a proficient solver notices;
- which option, partial result, or rubric boundary reveals the difference.

For single choice, normally derive at least three wrong options from named paths. For multiple selection, propositions must probe distinct consequences of one shared object rather than five disconnected facts. For fill-in and constructed response, record at least two plausible intermediate failures even when they are not printed as options.

### Math A: unpredictable answer counts and occasional close options

These are Math A authoring rules, not claimed CEEC answer-count frequencies or
proof of a measured increase in difficulty. Do not automatically apply them to
other subjects or change the selected paper's marking rules.

- For a five-option multiple-selection item, randomize the intended number of
  correct options over **1, 2, 3, 4, or 5** during fresh item planning. One correct
  option and all five correct are both legitimate possibilities. Do not default
  to two/three correct options, reuse a previous paper's answer-count sequence,
  cycle through counts, or attach a count to a question number or difficulty
  band. Do not require every possible count to appear in every paper; that would
  itself create an exploitable pattern. Review the whole paper's actual counts
  and label sets for conspicuous fixed patterns.
- Randomness belongs to the authoring plan, **never to mathematical truth or
  grading**. Construct five substantive claims about the new shared object,
  independently prove or disprove each, and derive the final key from those
  results. If the planned count cannot be realized coherently, revise the
  claims or resample the plan and solve again; never flip an answer-key label
  merely to match a sampled count. Zero correct options is not permitted.
- Keep the standard student instruction that at least one option is correct;
  do not reveal the count for an individual item. Do not add an extra
  "all of the above" option: an all-correct item means all five actual
  mathematical statements are true. All five still need distinct, nontrivial
  evaluation. With four/five true statements, misconception paths may describe
  incorrectly rejecting true statements; they do not require inventing three
  false printed options. Retain every option's proof/counterexample in the
  existing `independent_review.option_verdicts` and printable explanation.
- Occasionally use a close-numerical-option design in **one or two suitable
  selected-response items**, not throughout the paper and not as a compulsory
  quota for every paper. It may make coarse estimation insufficient, but a
  correct in-syllabus exact or sufficiently precise route must distinguish the
  options within the normal hand-solving budget. Preserve legitimate efficient
  reasoning; do not try to defeat every shortcut by increasing arithmetic load.
- A nearby distractor must be reproduced by a specific plausible error, such
  as an endpoint inclusion error, missed exceptional case, wrong rounding stage,
  or omitted constraint. Record that derivation in the existing
  `difficulty_design.misconception_paths`; do not create a distractor merely by
  adding a small numerical offset to the correct answer. Check units, requested
  precision, rounding/tolerance and mathematical equivalence so close values
  remain unambiguously distinguishable under the printed conditions. Never
  require precision absent from the source data or a diagram's scale.
- Neither unfamiliar answer counts nor small gaps between options count as an
  extra linked decision by themselves. Preserve the four-band distribution,
  anti-collapse audit, scope and time budget. Any increased difficulty or
  discrimination remains an expert hypothesis until a representative pilot.

## Paper-level target

For an internal 20-item current-form mathematics paper targeting roughly medium discrimination:

- at least 75 scored points must be designed at `medium` or `high` discrimination;
- no three consecutive scored items may all be labelled `low`;
- every major section must contain at least one `high` item unless the selected official position profile gives a documented exception;
- section-entry resets remain, but late single-choice, late multiple-selection, and fill-in positions must preserve their official demand rather than being flattened toward the paper mean;
- the six Math A single-choice positions may contain one accessible entry item, but positions 2–6 must not collectively collapse into exposed one-formula substitutions. In a feedback-tightened paper, at least four of the six single-choice items should require three genuine linked decisions, and at least two should require a representation change or reconciliation of two constraints. This remains subordinate to the official position profile and the 80–92 minute hand-solving budget;
- at least half the score must require three or more linked decisions, or an equivalent mixed-response dependency verified by human review.
- the sum of item-level expected hand-solving times should normally be 80–92 minutes for a 100-minute paper, leaving time to reread, transfer answers, and check work;
- every hard item must have an identifiable short route. Reject a candidate whose only viable solution is long case-by-case enumeration, repeated decimal approximation, or excessive arithmetic.

Do not force artificial hardness to satisfy these totals. If the only available candidate meets the count through prose load, arithmetic burden, obscure terminology, or outside knowledge, reject and regenerate the slot.

## Required validation

Run:

```text
python scripts/validate_math_difficulty_design.py generated-exam.json
```

The script checks record completeness, official target alignment, anti-collapse minima, misconception coverage, time feasibility, and paper-level discrimination architecture. Human review must still verify that the listed decisions are genuinely irreducible, the short route is realistic for hand work, and the shortcut audit was performed honestly.
