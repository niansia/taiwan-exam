# Exam Pack verification and end-to-end acceptance

Read before full papers, multi-form tests, quality complaints or Skill acceptance.
Subject references remain controlling. Checks verify evidence consistency, not
whether an LLM truly read a document or a reviewer was genuinely independent.

## Preserve the requested product

Before writing, record the original request, exam, subject/section, curriculum,
controlling year, number of independent forms, exclusions, answer profile and
output format in a separate `run-contract.json`. 國綜 and 國寫 are different
deliverables; do not add excluded 國寫 or combine them into a new 150-point paper.

- **Software smoke:** fixtures test file creation/rendering, not educational
  quality. Legacy question builders cannot supply new papers or acceptance tests.
- **Editorial full-paper test:** freshly written items, authenticated material,
  independent solutions, source/layout comparison and cross-form review.
- **Pilot calibration:** representative examinees and actual measured P/D;
  separate from expert-estimated difficulty, never generated metadata.

Switching `generation_mode` to custom-practice, adding “內部預覽”, or producing
enough PDFs does not satisfy a full-paper request. “直接完成” does not authorize
lowering the requested product. Continue feasible source analysis and repairs;
if evidence remains insufficient, disclose exact gaps and obtain explicit user
acceptance before substituting exploratory exercises. Do not repeatedly generate
failed drafts to fill a quota.

## Verify exam_packs before using it

`exam_packs` is a data store, not an authority because filenames say verified.
Inventory supplied material; inspect manifest, subject/regime, papers.jsonl,
writer blueprint, difficulty profiles, curriculum specification and layout profiles.
Run `python scripts/audit_exam_pack.py --output <audit.json>` and `exam_data.py status`.
The first checks EXISTING verified claims: no verified profiles with
`pass-claims-only` is NOT readiness. `--revoke-unsupported` is a maintenance
operation that demotes unsupported claims without deleting source materials.

Open actual selected source PDFs, verify hashes/exam/year/section and page counts.
Resolve disagreements using original pages, not hardcoded recipes. Use 111–115
as primary form evidence; older material is content-only. Keep coverage counts
for inventoried, text-extracted/OCRed, semantically reviewed and unreviewed files.
Visually inspect scans/screenshots. An inventory is not proof all questions were read.

### Paper Profile

For every scored unit record exact number (or unnumbered part), section order,
actual response type, option count, points, scoring rule, response format and
source page. Reconcile numbered questions separately from scored subparts. Record
actual types inside mixed sections: `mixed_group` is NOT a response type.
Copy and review exact section instructions, duration and answer-sheet rules.
Never infer single-choice from “選擇題”; 115 自然 explicitly includes single AND
multiple choice. Unknown mixes stay unknown until item-level review.
Once a Natural Science profile is selected and item-level reviewed, the rendered
candidate must expose that distinction: Questions 1–36 total 72 points, the
first-part instruction says they contain both types and every multiple-choice
stem prints its independently checked `（應選 n 項）` cue. The cover must include
the actual single- and multiple-choice scoring rules; metadata or an answer-key
type column cannot repair an incomplete candidate booklet.

`evidence.structure_review` must contain:

- `profile_sha256`: `pack_verification.profile_digest(profile)`;
- actual `reviewer`, ISO `reviewed_at`, `method: page-by-page`, `unresolved`;
- `pages`: records of source_sha256, physical PDF page (1-based), and specific
  observations, not copied pass strings;
- `slots`: every scored unit with unique id, number (null if unnumbered),
  section_id, actual type, score, option_count for choices, source_sha256 and page.

Only set verified after completing the review and resolving findings. A recipe,
confidence 1.0, matching total or `official_document` label never establishes
verification. Profile digests exclude evidence/status fields; changed structure
or sources invalidates review. Stage parser rebuilds before replacing reviewed
profiles; preserve reviewed local data unless its underlying source changed.

### Layout Profile, separately

Store under the subject's `blueprints/layout-profiles/`. Match exam, curriculum,
regime and 國綜/國寫 section. Select one same-subject controlling reference and
record differences across years/publishers, not universal identical typography.

Measure paper/margins/body frame; fonts and FINAL point sizes by question,
passage, Latin/formula, option, heading and label roles; line/baseline spacing;
cover; full instruction/scoring blocks; headers/footers and physical/printed
page numbers; section starts; option geometry; formula/marking rails; figures
and appropriate answer spaces. One generic six-subject style is not acceptable.

`evidence.layout_review` has the same hash/reviewer/date/method/pages/unresolved
fields, covering EVERY reference page including cover/final. `page_geometry`,
`typography`, `question_styles`, `pagination`, `cover`, `running_elements`, and
`instructions.blocks` must hold actual measured/transcribed data.
Selection reruns `pack_verification`; a verified string alone does not pass.
Portable packs without original PDFs remain needs-review/reference-only until
local sources are supplied and verified; zero hashes are not trusted evidence.

Source/appearance review is an analysis/QA pass. Export aggregate difficulty,
length, reasoning and layout envelopes to the writer, never historical stems,
solutions, numerical tuples or one year's unit order. Missing writer blueprints
must be derived from approved abstractions, not fabricated fingerprints.
Reusable profiles belong in exam_packs/references, not disposable output/tmp.

## Actual demands, authenticity and multi-form independence

Plan four-band count AND score balance from each subject's evidence. Solve the
shortest route, name actual bottlenecks and plausible wrong paths. Never assign
bands by modulo, random seed, shared cycle or only the requested quota. A direct
formula item may be an entry item, not a hard slot. Check section resets and
realistic total time, counting shared reading once.

Source ids must resolve to a frozen registry. Claim maps connect printed facts,
phrases and data transformations to actual sources. A current year/name is not
literacy: removing the source-derived relationship must change the reasoning.
Do not invent codes, candidate alternatives, data or no-shortcut review evidence.
國綜 requires authenticated excerpts, not invented prose with a real author's
name. Follow subject-specific source/rights rules; keep unnecessary provenance
and bibliographies out of student pages.

For 國綜, the blueprint and `curriculum_semantics` review must also reconcile
core-classical points to 20–25% of the whole-paper score, with confirmed work-list
membership, actual text dependency and no duplicate/group-wide overcounting.
Check every independently answered short-response subpart against the 40-character
and 4-point ceilings, including a within-limit full-credit sample and a realistic
rubric. Apply the detailed rules in `current-gsat-chinese-natural-form.md`;
larger official major-question totals do not authorize one long response.
This editorial check is separate from automated curriculum-code validation and
does not change 國寫 limits or historical Paper Profiles.

Across forms independently vary mechanisms, source selection, evidence roles,
solution dependencies, representations and distractors. Rotating a fixed pool,
replacing numbers or shuffling options is not multiple original papers. Run
`audit_generated_suite.py` across ALL intended forms; review within/across-form
findings and low-lexical structural neighbors. A generic repeated question label
may be legitimate with different evidence; zero lexical flags is not approval.
Keep hash-bound suite inventory, actual pairwise adjudications and coverage gaps.

## Independent answers and useful explanations

Use the requested answer profile and compatible publisher explanation samples.
An official short answer key supplies key format, not a student-friendly model.
No fixed line count is required: depth follows the question, not padding.

Solve from student wording without seeing the author's key first; compare after
solving. Use another route/calculation for high-risk or ambiguous items. Explain
every distractor and true multiple-select option; give equivalents, units,
tolerance and partial-credit rubrics. “Matches the passage” or “use the formula”
repeated across questions is not a full explanation. Remap all answer/explanation
references after option reordering; check student PDFs separately for leakage.

Each answer's `independent_review` contains `question_sha256` from content_hash(q),
`answer_sha256` from canonical digest(answer excluding independent_review),
reviewer, reviewed_at, answer_visible_during_solve=false, actual solution,
shortest_route, difficulty_rationale, option_verdicts keyed by every label,
derived_answer matching the reconciled published final_answer, rubric_review
for constructed responses, and unresolved=[] only when resolved. For equivalent
mathematical forms, preserve the raw independently derived result in solution
and explain the equivalence before recording the reconciled key. English cloze,
text completion and discourse items also require actual completed_text after
reinsertion, checking grammar, reference and discourse flow rather than a generic
“context selects this word” statement. Empty or duplicate option labels/text fail;
mathematically equivalent or semantically overlapping options still need review.
These are auditable work notes, not proof of human review or measured difficulty.

## Content gate → layout proof → delivery gate

Run contract required fields: user_request, requested_mode=full-paper, exam,
subject, curriculum. `section_map` maps generated section ids to reviewed profile
section ids. Include relevant source_registry, source_novelty_report and
vocabulary_reference paths, relative to the contract file.

```text
python scripts/validate_exam_release.py exam.json --contract run-contract.json --stage content --output content-gate.json
```

This resolves REAL pack profiles/sources/blueprint; checks slots, source links,
independent answers and reruns common/subject validators. Failure, exception or
missing dependency/evidence is not a skipped pass. Fix the underlying problem;
never fill fictitious review fields to clear the gate.

Then use the subject renderer. Generic rendering is custom practice only.
`render_gsat_official_pdf.py` needs --contract; --proof-only is a labelled internal
diagnostic. Other proof renderers remain diagnostic regardless of their names.
Content acceptance is not layout acceptance.

Measure final HTML/PDF and compare page roles and substantive lengths against
111–115 and the controlling profile. Inspect every raster at readable print
scale: missing ≤/≥/subscripts, formula signs, labels crossing strokes, duplicate
text, orphan options, fallback fonts, overflow, bottom voids and answer leakage.
Do not fix thin content with tiny fonts, inflated spacing/figures or irrelevant
sources/answer lines. Black-and-white figures must preserve all necessary
evidence; quantitative geometry/data must be exact, not image-generator guesses.

For delivery add student_pdf and answer_pdf objects with path, sha256,
expected_page_count (approved, not copied after rendering), review_path.
Review JSON binds exam_sha256, pdf_sha256, reviewer, reviewed_at, unresolved,
and pages. Each page needs page, raster_path, raster_sha256, specific reference_page,
observations and checks: font_glyphs, font_roles_sizes, formula_geometry,
overflow, whitespace, source_notes, figure_grayscale, headers_numbering,
content_legibility. Values: pass/fail/not-applicable, justified in observations.
Do not stamp records without actual viewing; contact sheets are navigation only.

Add editorial_reviews entries (path/sha256) for curriculum_semantics,
source_grounding, corpus_originality, literacy, layout_comparison and, when
suite_size>1, cross_form_originality. Each review file needs exam_sha256,
reviewer, status, observations, unresolved. Layout observations cite measured
overflow/density/font reports and hashes; source/novelty observations disclose
coverage. Cross-form reviews bind every suite file and adjudicate actual pairs.
For suite_size>1, contract.suite_exams lists every path/sha256; the cross-form
review stores suite_sha256=digest(suite_exams) and actual pairwise_findings.
Also provide student_html and answer_html (path/sha256) for the final fixed-page
HTML. Delivery reruns DOM containment and applicable subject density checks;
the measurements supplement, never replace, visual inspection.

```text
python scripts/validate_exam_release.py exam.json --contract run-contract.json --stage delivery --output delivery-gate.json
```

Every requested form must pass AND the suite review must be complete before
delivery as accepted. Changed JSON/figures/keys/PDFs invalidate prior review.
Keep failed reports; do not relabel them 最終檢查版. This is consistency checking,
not tamper-proof enforcement, proof of educational quality or publication.

## Maintenance acceptance

Test positive and negative paths: unsupported verified labels, changed sources,
wrong type/score/option mix, label-only hard questions, broken sources, repeated
templates, generic downgrades, stale reviews and missing pages. Correctly bound
synthetic fixtures may pass narrow checks but are not actual exam success.
Run repository tests and Skill frontmatter validation. Before packaging validate
attribution and exclude legacy question builders, private corpus/source-level
data. New reusable helpers require review before addition to package_skill.py's
explicit DISTRIBUTABLE_SCRIPTS list; an unknown script is not shipped by default.
Passing software tests is NOT multi-form exam acceptance without a fresh
editorial end-to-end generation run.
