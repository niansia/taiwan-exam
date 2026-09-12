# Transforming current sources into original exam material

Use this reference when an item or writing prompt begins from a current event, article, official dataset, scientific mission, product update, or emerging field.
For Math A/B, also apply math-current-events-and-sourcing.md: default 2–4 recent
model-dependent items, a 365-day event/publication window, and internal-only
source records. The printed attribution rules below for 國寫 do not apply to math.

## Freeze the editorial world

Across subjects, include candidates from the previous year's events/results in
bounded source discovery where they support the subject's curriculum and task.
Do not replace literary quality, historical reasoning or disciplinary depth with
recency alone. A source described as recent needs an event/result date and a
publication date within 365 days of the editorial lock; refreshed pages alone
do not qualify. Subject profiles control selection, with the specific 2–4-item
default and mathematical modelling gate defined for Math A/B in the reference above.

Set `editorial_lock_at` before discovery. A source must have been publicly available by that date, and every volatile fact must be frozen in a source record with its publication or update date and access date. The simulated paper may not quietly incorporate later information. A recent event whose facts are still changing can be used only when the printed material supplies a complete snapshot and the question does not depend on predicting the unresolved outcome.

For every local corpus, distinguish four coverage levels:

1. inventoried: file name, hash, role, and subject are known;
2. visually scanned: page and image/layout signals are known;
3. text accessible: OCR or a reliable text layer is available;
4. semantically annotated: concepts, stimulus role, reasoning, source provenance, and difficulty evidence were reviewed.

Never describe levels 1–2 as “the questions were learned.” Report incomplete OCR or semantic coverage numerically.

## Build the source record

Use `templates/inspiration-source-record.json`. Record the canonical URL, publisher, title, publication/update/access dates, source family, authority class, rights basis, a short factual snapshot, volatile claims, and what was paraphrased or synthesized. Separate:

- `verified_facts`: facts preserved from the source;
- `invented_modelling_values`: values created solely to make a closed school-level model;
- `source_affordances`: relationships or representations that could genuinely change a task;
- `forbidden_surface_hooks`: names or headlines that would only decorate a routine exercise.

## Transform, do not reskin

Apply this sequence:

1. **Factual nucleus** — state the smallest verified fact or relationship worth preserving.
2. **Information affordance** — identify what the source uniquely makes possible: a detector mosaic with gaps, a staged event timeline, a changing capacity, an abstention policy, a route network, or a measured series.
3. **Curriculum bridges** — propose at least three different syllabus-valid bridges. They must not all use the same equation or solution graph.
4. **Candidate competition** — compare at least three mutually dissimilar mechanisms, including one without the topical name. Reject candidates that require trivia or that merely insert the same numbers into a familiar shell.
5. **Instructional closure** — define every external rule in plain language. The student must need no news or professional knowledge beyond the stimulus.
6. **Independent mathematical object** — create new values, constraints, diagram topology, distractor paths, and a solution graph. Mark invented data as simplified or simulated in the printed text whenever readers might mistake it for a reported fact.

## Two release tests

### Proper-noun substitution

Replace every topical proper noun with a neutral label to separate fame from
evidence. Anonymization alone is not a failure: a source-derived relation, evidence
structure, representation or decision must remain essential. Then remove that
relation and identify the changed/undecidable inference. See
`evidence-backed-editorial-audit.md` for the task-level review ledger.

### Source-removal counterfactual

Remove the source-derived paragraph, table, or figure. The item fails if the same operations and answer remain available. A passing competence item forces the student to extract or qualify source evidence before crossing to the curriculum concept.

Passing these tests does not by itself prove difficulty. Calibrate reading, modelling, algebra, and representation load separately against the target slot.

## Whole-paper ecology

Do not turn one fashionable topic into a theme paper. Use multiple unrelated source families and domains, and retain context-free items where the form corpus supports them. The exact share is learned from compatible current-form evidence or declared as an internal editorial target; it is never a universal constant.

User examples are prompts for breadth, not prescriptions. A telescope may support geometry in one run and data modelling in another, or may be rejected entirely. A language model may support probability, logarithms, matrices, or an argumentative writing problem only when the supplied information makes that bridge natural.

## 國寫 material construction

Create a fact-and-viewpoint ledger before prose. For each printable passage, declare its rhetorical job and record a paragraph-level source map. Combine or contrast evidence from more than one note when useful, but never fabricate a quotation, person, institution, event, product comparison or narrative case. Keep the student paper self-contained and print a concise adapted-source note that identifies the publisher and work; retain URLs and claim mappings in the internal registry.

For the knowledge/argument task, require a definable claim, material integration, a tension or counterexample, and a bounded writing decision. For the affective/literary task, let current material open an image, relation, or temporal tension; do not turn it into a second policy essay. Both materials must be newly assembled and paraphrased from traceable sources and must not reproduce a source article's wording, sequence, or signature metaphor. The LLM creates the comparison, title and question; it does not create the stimulus evidence.

Source authority is role-dependent. Government, legal and research sources are strong defaults for verifiable analytical material, but they are not the default for the affective task. For that task, actively search contemporary Chinese essays, new poetry, picture-book prose, literary nonfiction, cultural criticism, interviews, field notes or nature writing, and preserve enough of the source's concrete carrier and reflective turn to support expressive writing without copying its language. Foreign-language literature is an occasional translated-literature route, not the default: require a traceable published Chinese translation and print the established Chinese author/work form.

The printed source note is part of the passage, not editorial furniture. Put `（改寫自……）`, `（節錄自……）`, or the appropriate equivalent immediately after the passage's final sentence in the same paragraph. Do not isolate it with blank lines. Do not label the passages `材料一：` or `材料二：`; use `甲` and `乙` only where the selected official profile needs cross-reference labels.

For both writing tasks, run the blind autonomous source discovery and source-selection tournament in `current-gsat-writing-form.md` before drafting. Automatic search output is a candidate pool, not a finished prompt. Record at least three candidates per task, the concrete carrier and semantic hinge of each, and a short rejection reason for every candidate not selected. Past-exam content is unavailable during this phase. Never compensate for a weak source by adding a fabricated or generic narrative paragraph, a composite case, or an artificial continuation page. `invented_modelling_values` must be empty for 國寫.
