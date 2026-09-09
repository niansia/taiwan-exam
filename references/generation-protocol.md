# Generation protocol

Read this reference for individual questions, practice sets, or full mock exams.

For every full paper (including internal/stress tests), first follow
[exam-pack-execution-contract.md](exam-pack-execution-contract.md). The actual
exam_packs references and shared handoff gate control execution. No custom
batch content generator or generic renderer may replace this workflow.

## 1. Establish the contract

Resolve exam, subject, curriculum/regime, desired length, simulated exam date, editorial lock date, exclusions, difficulty target, answer profile, and output. For a full simulation, first select compatible verified Paper and Layout Profiles and preserve total numbered/scored items, every major section's count and order, type mix, scoring rules, total score, duration, exact instruction blocks, and page contract. For a custom practice set, state which full-exam constraints were intentionally relaxed.

## 2. Plan before writing

### Current-form evidence priority

For a current GSAT simulation, separate **form evidence** from **content evidence**:

- primary form corpus: official ROC 111–115 papers plus same-period publisher mocks;
- secondary content corpus: ROC 100–110 official papers and older compatible material.

The primary form corpus controls wording length, stimulus construction, representation load, option competition, reasoning depth, position difficulty, question-block height, option rows, and page density. The secondary corpus may supply curriculum scope and abstract item archetypes only. Do not average the two corpora, and do not let an older short/direct item lower the target for a current slot.

Use `exam_packs/學測/shared-data/historical-content-envelope.json` when it exists. It is the only old-corpus artifact allowed in the writing pass. Treat its recurring labels and response-type evidence as a diversity pool, never as item recipes; its explicit forbidden-use list overrides any tempting historical pattern.

A Paper Profile is a joint structure template, not a menu of independent averages. Never combine one paper's total count with another paper's section recipe. If an exact requested year lacks a verified profile, inspect and reconcile its source or report the precise blocker. Do not silently downgrade a requested complete exam to a generic reference paper.

Create an Item Spec for every question. Learn correlations from multiple compatible administrations and encode them in aggregate pattern clusters. Then sample a new coherent paper plan inside that multi-year envelope. Do not pass a complete historical item record or one year's unit sequence to the writer. The plan may combine or rebalance aggregate clusters to meet the request but must log the change.

Each Item Spec should include:

- item id and section;
- unit, subunit, concepts, and skills;
- question type, stimulus type, and group structure;
- score, target position, and expected time;
- full difficulty vector;
- curriculum constraint and exclusions;
- originality constraint and optional misconception targets;
- a Visual Spec when the item uses any answer-bearing or contextual image;
- aggregate pattern-cluster ids only, never individual source-question ids or source wording;
- `current_form_cluster_id` derived from multiple compatible 111–115 administrations and, when used, a separate aggregate historical-content cluster;
- target stem/option length band, representation count, minimum reasoning operations, distractor misconception ids, question-block height band, and explicit option-row layout.

For GSAT, add the official slot target: P center/range, D floor, metric type, compatible years, and whether the value comes from an exact position or section fallback. A target is not an achieved statistic. Constructed-response slots need their rubric/distribution calibration instead of an invented P.

Before writing competence items, build a dated inspiration pool. Record source authority, publication date, access date, editorial lock date, simulated exam date, lead time, source family, factual stability, curriculum bridge, rights status, and originality potential. Validate it with `scripts/validate_inspiration_pool.py`. If the historical source-timing ecology is insufficient, describe the paper as a dated internal simulation rather than claiming its source timing was learned from official papers.

Keep corpus coverage and inspiration coverage separate. A source-file registry proves inventory coverage; it does not prove OCR, semantic annotation, item-level source tracing, or difficulty calibration. A generation report must state the counts in each coverage tier and may claim only the lowest verified tier relevant to the claim.

## 3. Generate original items

Apply the blind two-pass procedure in [originality-firewall.md](originality-firewall.md) and candidate competition in [llm-original-item-generation.md](llm-original-item-generation.md). The source-analysis pass exports only abstract multi-year pattern fields; the item-writing pass must not receive source stems, numeric tuples, equations in source order, individual source-question ids, or source-figure topology.

Write from the Item Spec, not from the source question text. Invent the information mechanism and solution graph before inventing the story. Generate several mutually dissimilar domain/mechanism candidates and select one by curriculum fit, authentic information use, readability, and novelty. A user example is never a fixed unit-to-context mapping. Change the underlying reasoning construction and representation semantics as well as the visible context. Use plausible distractors tied to named misconceptions. Avoid difficulty created only by ugly arithmetic, obscure trivia, excessive prose, or content outside the selected curriculum.

Figures, tables, and shared passages must be self-contained, labeled, and referenced consistently. For every visual item follow [visual-generation.md](visual-generation.md): match visual reasoning load as well as prose difficulty, render exact data deterministically, and validate the final rendered asset. Generated external-reading material must be original or clearly licensed.

Originality is item-type invariant. Run the firewall for text-only, selected-response, fill-in, and every mixed/constructed subpart. For fill-ins, reproduce only official response geometry, not canonical exercise shells. For mixed groups, validate both each subpart and the shared reasoning architecture; a common paragraph over independent routine questions is a failure.

For competence-oriented items, also follow [stimulus-generation.md](stimulus-generation.md). A long preamble alone is not evidence of competence orientation. Record the evidence span, curriculum bridge, reasoning operations, source provenance, and result of the stimulus-removal test.

For dated or real-world material, also follow [current-source-transformation.md](current-source-transformation.md). Reject topical name-dropping, preserve a frozen fact snapshot, distinguish verified facts from invented modelling values, and require at least one source-derived relation to alter the solution graph. Do not set a permanent rule such as “combinatorics uses neural networks”; candidate domains must be resampled for each build.

## 4. Solve independently

Do not reuse the generation rationale as proof of correctness. Solve again from the student's view. For high-risk items, verify by another method. Record the final answer, essential reasoning, accepted equivalents or tolerance, and common wrong paths.

Use only printed conditions and frozen visual evidence; no hidden generator
constants. Substitute every English gap answer into its full context, test each
option, and record actual derivations/scoring points rather than generic claims.
After any content or answer change, invalidate the old review and repeat it.

## 5. Validate

Question-level checks:

- in curriculum and matches Item Spec;
- complete prompt and sufficient data;
- exactly one answer for single-answer formats;
- plausible, non-overlapping options;
- valid units, formulas, diagrams, and references;
- no near-copy of a historical or already-generated item.
- lexical similarity is screened, and the mandatory structural skin-swap test covers ordered givens, solution graph, distractor paths, and visual topology;
- every scored item has an originality record, including text-only and fill-in items; every mixed group also has a group-level originality record;
- current-form evidence comes from 111–115, while any pre-111 evidence is tagged content/archetype-only;
- the intended solution actually reaches the planned reasoning and representation counts;
- every wrong option is reproduced by a documented plausible wrong path, not a random nearby number;
- option-row layout is explicit and survives rendering without compressed text or accidental wrapping.

Exam-level checks:

- item count, total score, sections, unit/type/difficulty distributions;
- difficulty curve and expected-time budget;
- answer-option balance without forcing a conspicuous pattern;
- no accidental concept repetition or answer leakage;
- traceability fields and calibration label present.
- official P/D target coverage for compatible objective slots and separate constructed-response calibration;
- competence/basic score share, source-family coverage, source-date/lead-time coverage, and stimulus-removal results;
- verified layout profile, exact instruction transcription, target page count, and page-level visual comparison for formal papers.

Replace failed items, then rerun exam-level checks. Never repair layout by changing mathematical or semantic content.

## 6. Answers

Keep answers out of the student paper. Supported profiles may include `official-short`, `teacher-detailed`, `student-friendly`, and `machine-check`. A subject profile overrides a generic profile when present.
