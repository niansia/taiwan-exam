---
name: taiwan-exam-generator
description: Generate, solve, validate, and format original Taiwan GSAT (學測) or CAP (會考) practice questions from local historical-question metadata and learned blueprints. Use for Taiwan exam item analysis, question writing, mock-exam assembly, answer profiles, and formal print layouts; not for reproducing past questions verbatim.
---

# Taiwan Exam Generator

Use the repository as the source of truth. The model writes new questions; the Exam Pack, metadata, learned blueprint, and validators decide what is in scope and how the paper is composed.

This skill is an editorial constraint and validation system, not a rewriting template library. For every run, the LLM must newly invent the disciplinary object, information mechanism, solution graph, representation, context, and distractor logic. Historical material supplies aggregate boundaries only.

Do not use or package any hard-coded paper builder as a content source, including a newly written one. A renderer or validator may be reused; new questions belong in this run's structured exam data, not in a reusable Python/JavaScript question bank. Never implement five forms by rotating stems, swapping constants, reusing passage frames, cycling difficulty labels, or fixing answer patterns. Writing a new batch generator is not an alternative way to follow this Skill.

## Mandatory execution contract

For **every complete paper**, including internal tests, smoke tests and stress tests, first read [references/exam-pack-execution-contract.md](references/exam-pack-execution-contract.md). Resolve the actual `exam_packs/<exam>/subjects/<subject>/` records and reference pages before writing. A profile id, a file inventory or a `verified` string is not evidence that its contents were inspected. Keep the reference/measurement pass separate from the original item-writing pass.

Complete-paper tests must use the same content and subject-layout checks as ordinary generation. Missing empirical pilot statistics may be disclosed; missing correct answers, curriculum boundaries, sources, official response modes or a usable layout may not be excused by calling the result a preview. Never silently change a full-paper request into generic practice. If a prerequisite is missing, produce a precise gap report and repair the evidence/template first; do not fabricate evidence or output a substitute batch.

Use the existing subject renderers and the single `scripts/validate_exam_release.py` content/delivery gate. `scripts/validate_exam_pack_contract.py` is only its renderer handoff adapter, not a second validation policy. Set `metadata.run_contract` to the external run-contract.json path relative to exam.json; see the execution contract for the maintained evidence format. A generic renderer cannot render a complete paper merely because metadata claims a verified layout. Renderer output is a **review proof**, not an accepted exam; PDF page inspection and final acceptance are separate. No helper script or export/marking test can self-certify educational quality.

Distinguish a **new paper** from a **user-requested correction of an existing paper**. In correction mode, inspect the supplied exam and audit findings, preserve unaffected items, replace confirmed failed mechanisms, and retain revision provenance. This is not a new-original-paper claim. The new-build inheritance prohibition below applies to new papers, not maintenance. After corrections, rerun whole-paper checks; metadata marking, packaging, or fixing one defect never clears unrelated failed acceptance checks.

## Route the request

For first use in a fresh installation or a new chat environment, read
[references/first-use.md](references/first-use.md). Handle ordinary-language
requests without requiring the user to operate repository commands. Installing
this folder does not install runtimes or certify reference data; inspect actual
capabilities and repair feasible prerequisites without weakening the full-paper
gates or claiming that a file upload is persistent skill installation.
For one-time installation requests, follow [INSTALL.md](INSTALL.md). On later
exam requests use the existing enabled Skill; do not reinstall or redownload it
as a routine prerequisite. Reuse accessible, still-valid reference evidence;
missing subject calibration is not a reason to reinstall the Skill.

For full papers, multi-form tests and Skill quality/acceptance work, first read
[references/pack-and-release-verification.md](references/pack-and-release-verification.md).
Verify actual `exam_packs` source PDFs, scored-slot structure and separate layout
evidence before trusting any `verified` flag. Preserve the requested product in
an external run contract; never substitute a generic smoke suite for independent
exam generation. `validate_exam_release.py` content AND delivery gates are
mandatory for formal full-paper claims. Reconcile/demote unsupported profiles;
do not repair them with confident labels. Diagnostic PDFs and provenance checks
are not exam acceptance.

For adapting, rebranding or packaging the Skill itself, read `NOTICE`,
`ORIGIN.json` and [references/attribution-and-forks.md](references/attribution-and-forks.md).
Keep current branding distinct from upstream attribution. These public guidance
and packaging checks do not add an account/approval step to ordinary exam use.

1. Map the requested exam and subject to an existing folder under `exam_packs/`.
2. For generation, read that pack's `manifest.json`, the subject's `metadata/papers.jsonl`, `blueprints/writer-blueprint.json`, and compatible aggregate difficulty/layout profiles when they exist. Never read `metadata/questions.jsonl`, review queues, or `blueprints/learned-blueprint.json` during the writing pass. Those source-level files belong only to ingestion and analysis.
3. If the user is adding or analyzing source material, read [references/data-ingestion.md](references/data-ingestion.md).
4. For GSAT analysis or generation, read [references/gsat-subject-patterns.md](references/gsat-subject-patterns.md).
   Resolve the subject's controlling CEEC examination specification through [references/official-gsat-specifications.md](references/official-gsat-specifications.md). A third-party summary or overview image is never sufficient for detailed scope.
5. If the user asks about difficulty, questions, or a full mock exam, read [references/difficulty-calibration.md](references/difficulty-calibration.md) and [references/generation-protocol.md](references/generation-protocol.md). For current GSAT Math A/B generation, also read [references/math-difficulty-design.md](references/math-difficulty-design.md); its anti-collapse and discrimination-design gates are release-blocking.
   Every subject's full paper also needs a declared 簡單／中／中偏難／難 count-and-score distribution and `scripts/validate_paper_difficulty_balance.py` review. The levels must describe actual item demands, never an all-中 default, hidden column, or quota-only relabelling. Use each subject's own 111–115 evidence; transfer Math A's design-and-shortcut-review method, not its percentage mix.
6. Before generating from any official, mock, screenshot, or publisher corpus, read [references/originality-firewall.md](references/originality-firewall.md) and [references/llm-original-item-generation.md](references/llm-original-item-generation.md). Blind source separation, LLM candidate competition, and the structural skin-swap audit are release-blocking requirements.
7. For current-form GSAT mathematics, also read [references/current-gsat-math-form.md](references/current-gsat-math-form.md) and [references/current-gsat-math-scope.md](references/current-gsat-math-scope.md); their typography, formula, stem-rhetoric, visual-placement, option-geometry, machine-marking, curriculum-code, and boundary rules are hard constraints.
   When present, also read `exam_packs/學測/shared-data/current-math-form-writer-profile.json`; it is an aggregate-only form envelope. Treat common-range mock statistics as shared-unit/form evidence, never as a Math A or Math B full-paper distribution.
   For current-form GSAT English, read [references/current-gsat-english-form.md](references/current-gsat-english-form.md). Its section sequence, vocabulary envelope, option-competition rules, passage lengths, source transformation, response formats, and page geometry are hard constraints. The vocabulary section must be written from contextual distinctions among plausible alternatives, not from one obvious word surrounded by wrong-part-of-speech fillers.
   For the verified 115 English profile, render cloze, text completion, and discourse gaps inline inside the passage; print their option blocks once in the official order, never as repeated worksheet-style blank rows. Part I is 62 points. Section-start underlines, heading placement, and page transitions require a section-by-section visual comparison before release.
   For current-form GSAT Social Studies, read [references/current-gsat-social-form.md](references/current-gsat-social-form.md). Its discipline balance, source ecology, evidence operations, cross-disciplinary grouping, constructed-response contract, and page geometry are hard constraints. Current events may supply evidence and a real decision problem, but may not replace history, geography, or civics reasoning.
   For current-form GSAT 國綜 or 自然, read [references/current-gsat-chinese-natural-form.md](references/current-gsat-chinese-natural-form.md). Its ROC 111–115 item-length and page-density envelopes, source-novelty rule, and no-unattributed-passage rule are hard constraints. 國綜 does not permit model-authored literary, classical, expository, or practical-text passages. 自然 may define a school-level model or ask students to transform source data, but every printed empirical datum and real-world claim must be traceable to a frozen source or a transparent calculation from it.
   For current-form GSAT writing, read [references/current-gsat-writing-form.md](references/current-gsat-writing-form.md) and [references/gsat-writing-source-ecology.md](references/gsat-writing-source-ecology.md). During the writing pass, do not read past question text, year-by-year topic summaries, or prior generated writing prompts. The LLM must discover new articles independently, then design a new material sequence, rhetorical tension, task decision, and title from those sources. Every printable event, case, datum, attributed viewpoint, and concrete anecdote must map to an identified source; the LLM may paraphrase, translate, juxtapose, and ask a new question, but it may not invent a supposedly real or generic case to complete the material. For the second task, search contemporary Chinese essays, new poetry, picture-book prose and other Chinese literary writing first. A foreign work may advance only through a traceable published Chinese translation; do not expose a raw English web bibliography as the normal student-facing source line.
8. For every competence-oriented item or group stimulus, read [references/stimulus-generation.md](references/stimulus-generation.md).
   For corpus rechecks, current-example/literacy complaints, source-note cleanup, or release review, also read [references/evidence-backed-editorial-audit.md](references/evidence-backed-editorial-audit.md). Report coverage gaps; author-declared pass flags never substitute for a comparison. Keep full provenance internal and print only notes justified by the official form, answerability, or rights.
   If the stimulus is drawn from a dated article, event, dataset, research release, or technical update, also read [references/current-source-transformation.md](references/current-source-transformation.md). A recognizable topic name is not evidence of literacy or originality. When users request real/current-event literacy, anonymous hypothetical cases do not fulfill that request: source actual dated evidence first, then require its specific relations to enter the curriculum reasoning. Keep event, publication and page-update dates distinct; never backfill invented observations under a real institution's name.
9. If the user wants a printable paper, HTML, or PDF, also read [references/layout-fidelity.md](references/layout-fidelity.md) and [references/rendering.md](references/rendering.md).
10. If any source or generated item uses a figure, graph, map, table, photograph, or visual evidence, read [references/visual-generation.md](references/visual-generation.md).
11. For PDF export or watermark requests, read [references/pdf-provenance.md](references/pdf-provenance.md). Use non-visible metadata provenance without changing page pixels. Disclose its presence and limits; never hide instructions or promise unremovable marks. Provenance verification is separate from exam acceptance.

Official subject folders are:

- 學測: 國文、英文、數學A、數學B、社會、自然. 國綜 and 國寫 share the 國文 data folder but are separate examinations/booklets with separate timing, numbering, scoring and layout contracts. Do not merge them into one 180-minute/150-point paper. If both are requested, produce two separately validated booklets. English translation/composition, by contrast, remain inside the English booklet.
- 會考: 國文、英語、數學、社會、自然、寫作測驗. Treat reading and listening as sections of 英語.

The auxiliary `數學（舊制）` folder is historical-only. Do not merge pre-111 GSAT mathematics into Math A or Math B. The auxiliary `數學（共同範圍模考）` folder holds current-regime mock exams that cover only the common books and are not labeled A or B; use their item patterns only for shared units, never as the full-paper distribution of Math A or Math B. When a blueprint contains more than one curriculum, require an explicit curriculum and never sample across regimes.

For a current GSAT paper, use ROC years 111–115 as the primary form corpus. Official 111–115 papers and same-period publisher mocks determine the current item-writing mode: stem and option length, stimulus density, representation changes, literacy construction, reasoning depth, distractor competition, local difficulty curve, item-block height, option-row arrangement, and page density. ROC years 100–110 may expand the curriculum-content and historical item-archetype pool, but they must not set current wording, layout, literacy, or difficulty distributions. This priority is mandatory even when older files are more extractable.

When `exam_packs/學測/shared-data/historical-content-envelope.json` exists, the writing pass may read it only to broaden curriculum coverage and abstract archetype diversity. Its forbidden-use list is binding. Do not read bundle-specific reports or source-level records to obtain the same information.

Do not silently substitute a neighboring subject, curriculum regime, or exam system.

## Calibration gate

Run `python scripts/exam_data.py status` before claiming that output is calibrated. A subject and curriculum are data-calibrated only when metadata validates and `calibration_by_curriculum` is `ready` in the learned blueprint. For GSAT this requires, separately, official semantic anchors, official objective-item P/D curves, full difficulty vectors, competence/source annotations, constructed-response calibration, and a verified formal Layout Profile.

- If calibrated data exists, use its observed joint patterns for unit, item type, score, position, and difficulty.
- If only an official structure or objective-item curve exists, it may support an analysis or content plan, but not a complete-paper generation claim. Label partial diagnostics explicitly.
- If neither exists, do not invent an "official-like" distribution. Explain what data is missing, or proceed only if the user explicitly accepts an exploratory uncalibrated draft.
- Never treat a sample file or a single year as a ten-year trend.

## Full-paper structure gate

For a complete mock exam, select one compatible Paper Profile from `metadata/papers.jsonl` before planning individual items. It must specify total numbered/scored items and every major section's count, type mix, scoring rule, and order. Use a `verified` official profile for a formal GSAT claim. `auto_parsed`, `needs_review`, or `pending_ocr` records are evidence queues, not formal generation templates.

When compatible official and publisher-mock profiles both pass the gate, use `official_past_exam` for full-paper structure. Use mock exams as supplementary evidence for explanation style and item variation; never let a mock override a verified official structure for the same regime and year.

Do not average incompatible paper structures or infer a section recipe from loose per-question frequencies. If the user requests an exact year, use that year's verified profile. If only the official reference architecture exists, stop at analysis or planning and do not claim that a reference-paper count is fixed for every administration.

## Formal layout gate

A Paper Profile is not a Layout Profile. A formal paper must also select a subject/regime-compatible Layout Profile whose `fidelity_status` and instruction transcription are both `verified`. It must reproduce the official cover hierarchy, full作答注意事項, score explanations, section labels, page geometry, running headers/footers, page count behavior, answer-sheet references, and subject-specific answer spaces. A generic readable renderer may be called a preview only.

## Required generation sequence

1. Resolve exam, subject, curriculum, year/regime, full-paper or custom-practice mode, difficulty target, simulated exam date, exclusions, answer profile, and output format. Use pack defaults only when those defaults are present in data.
2. In full-paper mode, lock a verified Paper Profile and Layout Profile. Copy the official section counts, order, scores, duration, instructions, and page contract into the plan. Then create a new full-paper distribution inside the multi-year aggregate envelope; do not inherit a previous generated paper or copy one historical year's unit sequence. A visual item must include a Visual Spec; `requires_diagram: true` without one is invalid. Source analysis must end in an abstraction artifact; the item writer must not receive source stems, numeric tuples, equations in source order, source-question ids, or source-figure topology.
   For current GSAT generation, every Item Spec must cite a 111–115 aggregate form-pattern cluster built from multiple compatible administrations. A pre-111 record may influence only aggregate curriculum coverage and historical archetype diversity; it is never an item seed.
3. Attach the official difficulty target for every compatible objective slot and the separate official/pilot rubric calibration for every constructed-response slot. Preserve section resets, position curves, annual exceptions, and the distinction between target and achieved P. For current mathematics, add a `difficulty_design` record to every scored item before writing prose. It must name the irreducible linked decisions, representation changes or constraint checks, misconception paths, discrimination move, and the result of a shortcut-collapse audit. Counting algebra lines or naming several syllabus concepts is not evidence of difficulty.
   When timed reviewer feedback exists for an earlier generated paper, preserve it as a separate feedback-calibration record. Use it to adjust the next paper's actual reasoning architecture, not its official target labels. A complete Math A paper must include a non-routine `D-10-3` item meeting the counting-depth gate in `references/math-difficulty-design.md`; direct factorial multiplication or a single symmetry halving step cannot be the paper's sole combinatorics coverage.
4. Build a dated inspiration pool for competence items from sources available before the simulated editorial lock. Match source family and lead-time distributions; never use a current event merely because it feels topical. Validate the pool with `scripts/validate_inspiration_pool.py`. Record corpus coverage separately: a file being hashed, indexed, or visually scanned does not mean its questions were semantically read. When OCR or item annotation is incomplete, disclose the exact gap and do not claim the model has learned every supplied question.
   For 國綜 and 自然, screen every proposed source title, author-work pair, distinctive quoted phrase, dataset name, and canonical URL against the full supplied official/mock corpus before drafting. Run `scripts/audit_source_novelty.py source-registry.json output-report.json`. A zero lexical hit is only a triage pass: also review aliases, translations, alternate titles, excerpt boundaries, and whether the same source object appeared through another representation. Store the result in the source registry; do not expose source-paper wording to the writing pass.
5. Write original questions that satisfy each item spec. Test the intended concepts, not superficial number changes. Require a new information mechanism, solution graph, and representation semantics before drafting the surface context. Generate at least three mutually dissimilar mechanism candidates for every scored item; do not bind a curriculum unit to a user example or recurring domain. Render answer-bearing diagrams from new semantic data; use image generation only for non-exact visual context and follow the visual-generation reference.
   `Original` describes the assessment design, not the authorship of the reading material. Do not invent a passage, poem, diary, archival record, interview, public notice, research result, or allegedly real dataset and then print it as source material. Select a traceable published source that has passed the corpus-novelty screen; quote only when rights permit, otherwise make an accurate attributed adaptation with an audit map back to source propositions. Do not print labels such as `自擬`, `本卷自擬`, or `數值為自擬` in a student paper. If a task genuinely requires simulated data, it may be used only when the user explicitly allows it and the paper is labelled as a custom exercise rather than a source-grounded full mock.
   For competence-oriented items, the stimulus must be required evidence rather than decoration. Apply the stimulus-removal test from `references/stimulus-generation.md`; if the item remains answerable with the same reasoning after removing the stimulus, rewrite it or label it a basic item.
   Also apply the source-relation test: anonymizing names is allowed, but removing the source-derived relation, representation, constraint, or decision must change the reasoning. A topical name alone is ornamental. See `references/evidence-backed-editorial-audit.md`; current material must supply a mathematical or rhetorical affordance, not prestige vocabulary.
   Apply bounded novelty: unfamiliar professional, technological, daily-life, or university-adjacent mechanisms are allowed only when every external rule is defined in the item, no outside domain knowledge is required, and the complete solution reduces to named concepts in the selected curriculum. Novel context must not inflate difficulty beyond the slot target.
   Do not hard-code a topic-to-unit association. Spaceflight, language models, telescopes, public bicycles, energy systems, or any user example are candidates only. For each slot, compare at least three mutually dissimilar information mechanisms, including a non-topical alternative, and select by evidence necessity, curriculum fit, solution quality, and target difficulty.
   Apply the originality firewall to every scored item without exception: text-only, single-choice, multiple-selection, fill-in, constructed response, and every mixed-group subpart. For fill-ins, only the official marking rail may be reused. For mixed groups, the shared object and the dependency among subparts must also be newly invented.
   A photograph must be original, public-domain, licensed, or explicitly user-authorized and must carry an auditable provenance record. When it will print in grayscale, freeze the exact crop and tonal conversion before item review. Every answer-bearing feature must remain distinguishable at final print size without hue. A color-dependent prompt is rejected unless the same distinction is redundantly encoded by labels, patterns, shapes, positions, or printed values. Never ask students to identify a color from a grayscale reproduction.
6. Solve every question in a separate reasoning pass. For high-risk mathematics, science, ambiguous reading, or constructed response, use an independent second route or deterministic calculation where practical.
7. Validate scope twice: first map every mathematical operation to one or more official learning-content codes, then audit the actual wording and solution path for hidden out-of-scope terminology, theorems, or procedures. Run `scripts/validate_math_curriculum.py` for Math A/B and require human review of every `defined-bridge` item. Then validate answerability, unique answer where applicable, distractors, units, diagrams, answer distribution, duplicated concepts, total score, difficulty-vector match, stimulus necessity, and blueprint fit. Run lexical triage plus the mandatory structural skin-swap audit from `references/originality-firewall.md` against official, mock, and already-generated items. Also validate the paper-level diversity matrix from `references/llm-original-item-generation.md`. Replace only failed items and recheck the whole paper. Any build that inherits legacy generated question content is rejected in full.
   For 國綜 and 自然, validate every item against the controlling CEEC examination specification at the learning-performance/content-code level. The natural-science paper must visibly balance physics, chemistry, biology, earth science, and inquiry/practice across both major parts; naming a discipline in metadata is not a scope audit. Run `scripts/validate_chinese_natural_scope.py generated-exam.json --report output/scope-report.json`, then run `scripts/validate_source_grounding.py` with the frozen source registry and passing novelty report before rendering. A made-up, misspelled, or wrong-subject curriculum code is release-blocking even when the prose seems on topic.
   For source-bearing items, verify that printed facts agree with the frozen source snapshot, invented values are explicitly labelled as simplified or simulated, URLs and dates remain in the audit registry rather than cluttering the formal paper, and removing the source-derived relation changes the solution. For 國寫, verify that each supplied passage has a distinct rhetorical job, every material paragraph has a `material_source_map`, every printed case comes from an identified source, and no source record has invented modelling values. The second task must include an authored Chinese literary source, or a traceable published Chinese translation, suitable for affective expression rather than defaulting to institutional explainers or newly found English-language web essays. On the student page, source attribution stays in full-width parentheses at the end of the material paragraph; it is not a separate source block. Do not title the supplied passages `材料一：` or `材料二：`; use the official-style `甲`/`乙` markers only when multiple texts need labels. Run `scripts/validate_writing_source_grounding.py` and treat any failure as release-blocking.
   For mathematics, run `scripts/validate_math_difficulty_design.py` and reject any item whose planned difficulty collapses to direct substitution, one familiar formula, one routine linear-system solve, or repeated execution of the same operation. Treat model-estimated discrimination only as a design label until representative pilot data exist. Then validate explicit `option_layout` per item (`row-5`, `row-4`, `grid-3-2`, `grid-2`, or `stack`). Never infer the printed arrangement only from character count. Validate the rendered option baselines and inter-option whitespace against recent reference pages.
   Every mathematics fill-in item must declare a machine-marking `answer_format`: integer/decimal/fraction/sign form, exact numerator and denominator slot counts, and the sequential answer-row ids printed in the booklet. The renderer must show the same circle/rail/fraction geometry that the student will mark; a generic blank line is a hard failure.
   A current mathematics paper must also meet its learned answer-bearing visual quota across more than one section. Until item-level 111–115 visual annotation is complete, the internal review floor is four required visuals or structured graphical representations across at least three sections, including at least one item before the mixed-response section. Decorative pictures do not count.
   For English, run `scripts/validate_english_vocabulary_scope.py generated-exam.json <CEEC-reference-vocabulary.pdf> --report output/english-vocabulary-scope.json` and `scripts/validate_english_layout_contract.py generated-exam.json`. Treat an out-of-envelope non-reading word, a vocabulary target above level 5, missing part-of-speech competition, missing distractor-confusion evidence, or a failed section-display contract as release-blocking. Level 6 or off-list words in authentic reading material require local support or a documented reading-only exception; rarity may not be the intended source of difficulty.
   For Social Studies, run `scripts/validate_social_item_design.py generated-exam.json --report output/social-item-design.json`. Treat a missing curriculum code, unsupported current-event claim, ornamental proper noun, non-self-contained domain rule, or evidence-free competence label as release-blocking. Preserve identifiable history, geography, and civics coverage alongside cross-disciplinary groups instead of making the whole paper a collection of topical news passages.
   For a full current Social Studies paper, recent-source groups must be distributed across both the objective and mixed parts and must invoke real historical, geographic, or civic reasoning. Apply the provisional freshness floor in `references/current-gsat-social-form.md`; an event name, date, or fashionable technology used only as decoration does not count.
   For every answer-bearing photograph or raster figure, require `grayscale_evidence_survival` and `color_independence` in its Visual Spec and inspect the final rasterized page at print scale. Schema compliance alone is not a visual pass.
   Keep photo rights and credit in the internal provenance ledger. Do not print optional photo-source lines in the student booklet unless the selected official Layout Profile explicitly includes them; textual material/source lines remain subject to their own official-form rule. If a license requires visible attribution incompatible with the form, replace the source or obtain suitable permission; internal metadata never substitutes for required visible credit.
8. Keep student paper and answer material separate. Produce structured `exam.json`; for fixed-page proofs, render HTML and pass `scripts/validate_fixed_page_html.py` before PDF export. The gate must cover horizontal and vertical overflow plus containment inside bordered instruction boxes, tables, response examples, and the printable page frame. Then rasterize the PDF and inspect every page at readable scale before a formal claim. Page count, extracted-text density, font inventory, or a contact sheet alone cannot establish that nothing is clipped. For current Math A/B mixed-response items, do not print workbook-style answer lines in the question booklet unless the controlling official Layout Profile explicitly contains them.
   For 國綜 and 自然, also compare every rendered content page with the ROC 111–115 density envelope by running `scripts/validate_current_form_density.py`. In this project the explicit anti-blank-page floor is 78% of the printable body for every question page, including the final page; a low historical outlier may be reported but must not weaken the gate. Do not repair under-filled pages by shrinking the page count, enlarging type, or adding decorative filler; rebalance substantive source excerpts, item blocks, reference-supported answer space, exact figures, and page transitions while preserving readability. Do not auto-append `來源補充`, add answer-revealing commentary, inflate figures, or over-allocate response lines to pass this metric. Apply the role-specific typography and SVG text/stroke checks in `references/current-gsat-chinese-natural-form.md`; preserve failed full-form status when a corrected proof exposes inadequate substantive length. A matching total page count with half-empty pages is not layout fidelity.
   For current English and Social Studies, run `scripts/validate_reference_page_density.py` against the selected official paper after PDF export. Compare matching page roles, not only the total page count. A page that passes overflow checks but ends materially earlier than its official counterpart is still a release failure. Repair it by restoring authentic passage/item length, noncontinuous evidence, or measured item-block rhythm. Never create one large terminal void, and never disguise one by inflating type or adding irrelevant prose. Small distributed spacing between complete items is acceptable only after the substantive content-length contract is satisfied.

The output must say which pack, subject, curriculum/regime, blueprint fingerprint, and calibration level it used.

## Originality and private data

Historical files in `歷屆試題/` and `模擬考/` are user-owned working data. They are git-ignored by default.

- Learn abstractions: unit, concept, skill, stimulus class, item type, difficulty vector, score, position, visual function, and common misconception. Keep those abstractions in a separate artifact from source wording and figure topology.
- Do not copy, lightly paraphrase, translate, or merely swap numbers in a source item.
- Do not publish source passages, images, answer keys, or full historical questions unless the user confirms the necessary rights.
- If similarity is uncertain, change the information mechanism, solution graph, representation semantics, and surface context, then validate again. Surface changes alone never cure a structural match.

## Repository tools

Use the repository helpers when local execution is available (some require PDF/browser dependencies):

```text
python scripts/audit_exam_pack.py --output output/pack-audit.json
python scripts/validate_exam_release.py exam.json --contract run-contract.json --stage content --output output/content-gate.json
python scripts/validate_exam_release.py exam.json --contract run-contract.json --stage delivery --output output/delivery-gate.json
python scripts/audit_generated_suite.py form1.json form2.json --output output/suite-audit.json
python scripts/exam_data.py index-sources
python scripts/build_paper_profiles.py
python scripts/analyze_pdf_visuals.py
python scripts/build_visual_queue.py
python scripts/build_question_candidates.py --promote
python scripts/download_ceec_gsat_statistics.py --min-roc-year 100
python scripts/import_ceec_gsat_difficulty.py
python scripts/build_gsat_difficulty_profiles.py
python scripts/analyze_gsat_official_patterns.py
python scripts/analyze_mock_exam_dataset.py --intake <本次資料夾>
python scripts/analyze_mock_bundle.py --bundle "<正式套卷名稱>"
python scripts/analyze_historical_content.py
python scripts/build_layout_review_queue.py
python scripts/analyze_stimulus_ecology.py --exam 學測 --subject 社會 --output output/social-stimulus-ecology.json
python scripts/analyze_writing_source_corpus.py <資料夾...> --output output/writing-source-corpus.json
python scripts/validate_inspiration_pool.py output/current-inspiration-pool.json
python scripts/audit_item_originality.py generated-exam.json output/originality-audit.json
python scripts/validate_llm_originality_contract.py generated-exam.json
python scripts/validate_math_curriculum.py generated-exam.json
python scripts/validate_math_difficulty_design.py generated-exam.json
python scripts/validate_english_vocabulary_scope.py generated-exam.json <CEEC-reference-vocabulary.pdf> --report output/english-vocabulary-scope.json
python scripts/validate_social_item_design.py generated-exam.json --report output/social-item-design.json
python scripts/validate_chinese_natural_scope.py generated-exam.json --report output/chinese-natural-scope.json
python scripts/validate_source_grounding.py generated-exam.json source-registry.json --novelty-report source-novelty.json --report output/source-grounding.json
python scripts/validate_current_form_density.py generated-student.pdf --subject 國綜 --report output/form-density.json
python scripts/exam_data.py validate
python scripts/exam_data.py build-blueprints
python scripts/exam_data.py plan --exam 學測 --subject 數學A --count 10
python scripts/exam_data.py plan --exam 學測 --subject 數學A --full-paper --paper-year 2025
python scripts/render_visual.py templates/visual-spec.json output/example-graph.svg
python scripts/render_exam.py examples/synthetic-exam.json output/exam.html
python scripts/render_pdf.py examples/synthetic-exam.json output/exam.pdf
python scripts/validate_fixed_page_html.py output/paper.html
```

`render_pdf.py` uses a locally installed Chrome, Chromium, or Edge and preserves the CSS A4 page size. If no supported browser or local execution is available, deliver the print-ready HTML or follow the schemas manually. Never claim a validator ran when it did not.

Use `templates/llm-originality-record.json` for every scored item and `templates/paper-originality-matrix.json` for the paper-level and mixed-group records. These are audit forms only; their placeholder values are not evidence of a pass.
