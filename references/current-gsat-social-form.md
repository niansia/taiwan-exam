# Current GSAT social-studies form and evidence design

Read this reference for current-form GSAT social-studies analysis, generation, or rendering. Scope is controlled jointly by the CEEC social-studies examination specification and the selected official Paper Profile.

## Structure is annual, not frozen

The verified current-regime profiles show real variation:

| ROC year | Objective items / score | Mixed or constructed items / score | Total numbered items |
|---:|---:|---:|---:|
| 111 | 46 / 92 | 21 / 52 | 67 |
| 112 | 45 / 90 | 21 / 54 | 66 |
| 113 | 35 / 70 | 29 / 74 | 64 |
| 114 | 42 / 84 | 22 / 60 | 64 |
| 115 | 38 / 76 | 27 / 68 | 65 |

Every profile is 110 minutes and 144 points. Select one verified year before writing. Do not average these counts or declare 65 items universal. For the observed 115 paper, the official feature report further groups the objective section into five groups and the latter section into eleven mixed groups; reproduce that only when using the 115 profile.

## Three disciplinary lenses

History, geography, and civics remain identifiable even inside cross-disciplinary groups. Every item records one primary domain, any secondary domains, curriculum codes, evidence operations, and score. The controlling CEEC specification limits assessed knowledge to the Grade 10–11 required history, geography, and civics learning-content codes; an extension topic may provide a situation, but it may not silently introduce an out-of-scope rule. Use the chosen profile and current multi-year envelope to balance score; a convenient 25%–42% per-domain band is a review warning, not a replacement for annual evidence.

- **History:** chronology and continuity/change, contextualization, source provenance, comparison of accounts, historical causation, and judgment about evidence fitness.
- **Geography:** location and scale, map/remote-image reading, spatial pattern, human–environment systems, data interpretation, regional comparison, and policy implications.
- **Civics:** rights and institutions, law and procedure, media/public opinion, markets and externalities, distribution/fairness, competing values, and warranted policy judgment.
- **Cross-disciplinary:** one shared object must genuinely require more than one lens. Merely placing a historical date beside a map does not make an integrated item.

## Current issues without current-affairs trivia

Typhoons, AI labor, public health, elections, platform governance, migration, energy, war, disasters, conservation, trade, or any other current issue may inspire a group. They are examples, never mandatory topic-to-unit mappings.

A current source may advance only if:

1. it predates the simulated editorial lock and has a stable URL/date;
2. factual claims are checked against a primary source, dataset, law, judgment, research release, or archive; news alone is not the factual authority;
3. all facts needed to solve are printed in the stimulus;
4. the question requires a disciplinary operation, not recognition of the event;
5. a source-derived relation changes the reasoning when removed; merely anonymizing a famous name is allowed and is not a failure;
6. political and contested claims are attributed, balanced where the task requires it, and separated from facts.

Keep both basic anchors and competence-oriented groups. A paper made entirely of long topical passages is as distorted as a paper made entirely of recall questions.

For a full current-form internal paper, recent evidence must be distributed rather than quarantined in the final mixed section. Before release, require several independently sourced current-context clusters across the objective and mixed parts, spread across geography, civics, and historically grounded change/evidence where appropriate. The existing current-issue-forward planning target is seven recent-source clusters and 24 scored items depending on them. These numbers were an internal editorial choice, not a numerical user requirement or measured CEEC quota. At least two current clusters should occur in the objective part; review topic saturation. Count only source-verified, task-reviewed items using `evidence-backed-editorial-audit.md`. Repeated stimuli, unsupported dates and metadata-only competence labels do not count. Anonymized names are allowed; decorative source relationships are not.

Current clusters should make students perform operations such as reconstructing a hazard–exposure–vulnerability chain, correcting a denominator, comparing policy defaults and exceptions, identifying scale mismatch, weighing rights or incentives, relating current change to historical evidence, or testing what a source cannot establish. Plausible distractors must fail on one of these operations; three absurd alternatives do not create literacy. “More current” never means asking who, when, or where as news trivia: all event-specific facts needed for the answer must appear in the material, while the assessed operation remains within a required-course code.

## Source and task ecology

Build source candidates from multiple families: historical primary and secondary sources, archives, maps, aerial/satellite images, photographs, artifacts, statistical charts, open data, laws/judgments, policy documents, research, news used with a primary source, literature, and authentic life documents. Avoid repeating the same newspaper-summary-plus-definition pattern.

For every competence item, record:

- `orientation: competence`, primary/secondary domain, and curriculum codes;
- `source_family`, `source_ids`, dates, rights and fact-check status;
- exact `evidence_targets` and `reasoning_operations`;
- `stimulus_required: true`, `stimulus_removal_test: fail_without_stimulus`, and `external_knowledge_required: false`;
- current-context items: `editorial_lock_date`, `published_at`, and `proper_noun_substitution_test: mechanism_changes`;
- a rubric evidence unit for every constructed response.

Run:

```text
python scripts/validate_social_item_design.py EXAM_JSON --report REPORT_JSON
```

The validator checks metadata and evidence contracts. It does not replace solving the item, legal/date verification, or human review for contested interpretations.

## Distractors and constructed responses

Social-studies distractors should be reasonable claims defeated by a specific flaw: wrong time/space, reversed causality, overgeneralization, evidence-source mismatch, category confusion, legal hierarchy error, denominator error, or an unsupported value judgment. Avoid three absurd choices around one textbook phrase.

Constructed responses must state the evidence units and permissible equivalents before prose is written. The prompt should bound length and response form exactly as the selected official profile does. Score evidence selection, interpretation, comparison, or justification; do not reward generic opinion unsupported by the supplied material.

## Visual evidence and grayscale photographs

Maps, tables, charts, timelines, document fragments, aerial images, artifacts, and real photographs are central evidence forms. Real photos may be used only with traceable rights and provenance. Convert to grayscale only after identifying the answer-bearing features.

Keep photograph credit, license, crop, and transformation records in the internal provenance ledger. Do not print a photo-source credit in the student question booklet unless the selected official profile explicitly places one there. This does not remove the obligation to print a textual material/source attribution when that attribution is part of the selected profile.

Every visual item must pass the color-independence and evidence-survival tests in [visual-generation.md](visual-generation.md). A question about color is invalid after monochrome conversion unless the decisive categories are redundantly encoded by labels, shape, pattern, position, or measured value. Do not repair a failed image by relying on the answer explanation.

## Layout contract

Current official papers use a cover plus densely composed one-column A4 body pages, running page/total-page and subject/year headers, a centered signature reminder, and bottom page number. The 115 paper has nineteen numbered body pages plus the cover. The part heading and bordered instruction line appear once at the part start, not after every page break.

Options are normally stacked beneath the stem. Figures sit close to the exact paragraph or question that invokes them and use sequential labels (`圖`, `表`, `照片`) with captions. Mixed groups may include bordered answer-format tables that describe what belongs on the separate answer sheet; reproduce their cell sizes, word limits, and checkboxes only when present in the selected profile. Never add generic ruled lines to every constructed item.

Pagination must protect maps, captions, legends, question continuations, and response-format tables from clipping or separation. Rasterize every page in grayscale and inspect at target print size before release.

Run `scripts/validate_reference_page_density.py` against the selected official paper after PDF export. Overflow-free but half-empty pages fail. First restore authentic evidence and item length; then distribute the remaining small amount of white space between complete items. Do not push all unused space below the last item, stretch a single gap unnaturally, repeat headings, enlarge type, or add content-free filler merely to reach a percentage.
