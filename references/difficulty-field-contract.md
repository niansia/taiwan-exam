# Difficulty fields: author once, validate the actual content

Run `python scripts/emit_item_skeleton.py --subject 數學A --number 14` for the
current scored slot and pending fields. Use its `question` in `exam.questions`
and its `answer` in `exam.answers`; keep `requirements` outside the student text.
It copies exact current structure and Math A/B profile targets. It does not
write question content, estimate actual difficulty, solve, or pass any review.
Null/pending is intentional. Complete each field from actual authored work.
The emitted draft is not yet a valid completed exam.
For 國寫’s first printed question, select `--subpart 1` or `--subpart 2`;
the helper does not merge its distinct 4-point and 21-point tasks.
For unnumbered English tasks use `--slot-id translation-1`, `translation-2` or
`composition`; their actual printed labels remain separate from Arabic numbering.

`schemas/difficulty-design.schema.json` describes
`question.item_spec.difficulty_design`. Its root accepts pending draft fields;
the `completedMathDesign` definition rejects unset mandatory math fields.
The executable difficulty and hosted gates still decide whether evidence is
complete. A schema pass alone never certifies difficulty or originality.

| Field | Required meaning / exact values |
|---|---|
| `band` | `簡單`, `中`, `中偏難`, `難`. Match `item_spec.difficulty.label` and `answer.difficulty_label`. |
| `expert_estimate.difficulty_band` | `very_easy`, `easy`, `medium`, `hard`, `very_hard`. Map to `簡單`, `簡單`, `中`, `中偏難`, `難`. |
| `metric_type` | `answer_rate`, `score_rate`, `constructed_response`. Multi-select uses score rate; do not invent an achieved rate. |
| `target_p_center`, `target_p_range`, `target_d_floor` | Copy the skeleton’s exact same-number official profile values. Constructed-response targets may be null. |
| `target_basis` | `official-profile` when a numeric reference exists; otherwise `constructed-response-expert` or `official-rubric-expert`. |
| `minimum_linked_decisions` | Skeleton imports the validator’s exact minimum. Math B easy/medium needs at least 3; its first three fill-ins also require 3 and at least 2 representation/constraint operations. |
| `linked_decisions` | Array of distinct objects: `id`, `description`, `kind`, `trigger_evidence`. Arithmetic lines are not separate necessary decisions. |
| `misconception_paths` | Distinct objects: `id`, `error`, `predicted_outcome`; at least 3 for choice items, 2 otherwise. |
| `discrimination_design.level` | `low`, `medium`, `high`; provide actual `lower_group_move` and `proficient_move`. Match `expert_estimate.discrimination_level`. |
| `shortcut_status` | `reviewed-no-direct-collapse` only after actual shortcut review; required for `中偏難`/`難`. |
| `shortcut_audit` | At least 2 attempted shortcuts; actual non-collapse records `collapse_found=false`, `direct_formula_substitution_only=false`, `reviewer_decision=pass-no-collapse`. |
| `innovation_audit` | Actual evidence: recall-only false, solution-graph change true, structural nearest-neighbor difference, `reviewer_decision=pass-nonroutine`. Never fill these by default. |
| `burden_audit` | All three false only after checking arithmetic volume, prose length and outside knowledge are not the primary difficulty. |
| `expected_minutes` | Positive estimate; math item ≤10. Keep question, design, and `time_audit.expected_minutes` equal. Supply the actual short route and hand-solving feasibility. |
| `expert_estimate.confidence` | Number in [0,1]. Completed estimate status stays `provisional-until-representative-pilot`; it is not student-tested P/D. |

All subjects need the actual `basis`, `confidence`, `short_route`, `misconception`,
`linked_decisions`, `bottleneck`, `expected_minutes` and final `content_sha256`
for the four-band gate. Math-specific nested audits are not generic targets for
English, science, social studies or Chinese. Follow those subjects’ own rules.

Set `content_sha256` only after the current item content and its assets are
saved. Use `validate_paper_difficulty_balance.content_hash(question)` directly;
do not invent a shorter hash recipe. It covers the exact keys `prompt`,
`group_stimulus`, `options`, `visual_asset`, plus non-null `continuation_pages`,
`group_stimulus_page_splits`, `response_format_table`. The function canonicalizes
these values; hashing the entire question or only the prompt gives a different
result. A content change requires rechecking affected judgments before rebinding.

Review reports are separate from author design metadata. The hosted difficulty
report needs actual shortest-route, shortcut, anchor and answer-recheck findings,
the real review mode and context. Reuse a real finding across required records;
never prefill pass, independent identities, achieved difficulty or observations.
