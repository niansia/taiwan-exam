# Reusable body components and early visual QA

Use with hosted-pdf-production.md and hosted-quality-gates.md for all seven
subjects. Fixed cover/header/footer/formula PDFs remain unchanged original
layers. The reusable components below create ONLY the new body inside that
subject's mapped frame. They do not establish subject structure or difficulty.

## Reuse layout, never questions

Start with `templates/hosted-subject-layouts.json` and load ONLY the requested
subject's `questions` and `solutions` JSON files. The default web extractor
selects that pair and excludes the other six subjects' layout examples.

| Subject | Distinct body examples |
|---|---|
| 國綜 | language knowledge, separately styled reading/cross-text stimulus, short-answer table, evidence and partial-credit explanations |
| 英文 | vocabulary, inline cloze gaps, one ten-option completion bank, four discourse gaps/five options, reading, mixed response, translation and composition; separate explanatory/rubric formats |
| 數學A | five-option single/multiple choice, integer/fraction rails, figure–text and constructed response, mathematical verification and scoring |
| 數學B | its own single/multiple choice and rails, data/condition table and constructed response, interpretation and mathematical verification |
| 自然 | five-option single/multiple choice, required-selection count, experimental/observational table and figure, mixed responses with scientific reasoning/units |
| 社會 | history/geography/civics sources, four-option choice, map/image and comparison table, cross-source explanation and scoring |
| 國寫 | common two-task heading, 一／二 materials, first-task 80-character/4-point and 400-character/21-point subparts, second-task 25-point prompt; separate examples and analytic scoring |

The preview files illustrate these structures with placeholders, not full papers
or fixed topic/figure quotas. Preserve each subject's own profile. Do not assign
math rails to other subjects, reuse the English composition rubric for 國寫,
or copy the preview's sparse page density and abbreviated passages.
Downloadable previews are at
https://niansia.github.io/taiwan-exam/layout-examples/2026.09.13.7/index.html .
They are optional visual references, never a new download/preflight requirement.

`templates/hosted-body-blocks.json` is a **layout-reference-only** gallery.
Its text, numbers, option counts, scores and block order are placeholders, not
an exam specification. The gray SVG is not a reusable question diagram.
Never turn these into questions by changing constants. Create the new paper's
content in its own run, with original stems, solutions, distractors and visuals.
Keep the originality/history audit. A figure's topology is content, not layout.

Use `scripts/hosted_body_templates.py` instead of writing a fresh PDF compositor
for ordinary blocks: section heading plus boxed directions; choice/multiple
options; integer/fraction fill rails; shared stimulus; constructed response with
printed score; and solution steps. The subject profile still controls actual
directions, labels, item/option counts, sequence, scores and response forms.
English cloze/discourse use the subject's inline passage/bank components. 國寫
and English composition prompts belong in the question booklet; separate
student answer-sheet grids must not be inserted as a generic ruled workbook.
A supported common block does
not mean the gallery itself is a valid full paper for any subject.

```text
python scripts/hosted_body_templates.py run/questions-blocks.json --output run/questions-body-v1.pdf --layout run/questions-layout-v1.json --font /path/to/verified-body-font.ttf
```

Run separately for authored solutions. The renderer outputs transparent body
pages, NOT deliverable exam PDFs. Feed both bodies into compose_hosted_pdf.py
with the actual subject, year and verified fixed assets. For viewing only the
placeholder gallery, supply `--proof`; never use that flag for a production run.

`passage` blocks contain `paragraphs`, an optional `heading`, `language: en`
for Latin passage typography, and optional `bank`/`columns` for one shared option
bank. `{{gap:11}}` produces a visibly underlined inline gap. A `table` block
contains `headers` and rectangular `rows`, with optional introductory `text`.
Use `keep_with_next: true` where a stimulus/table must stay with the next task;
oversized groups need explicit continuation instead of clipping or shrinking.
Use `label` for real subpart labels such as （一） rather than inventing extra
Arabic-numbered items. Labels do not determine the scored-item contract.

`--reading-font` can supply a separately verified reading-material font for
國綜/國寫. Main body and reading roles must retain the selected subject's visual
hierarchy. Some DFKai versions collapse Chinese advances in the HTML renderer;
the helper rejects this pattern. Use a compatible tested font, not a smaller
font or a claim that successful export proves text is readable.

Text is plain Unicode; `{ "rich": "…<sup>…</sup>…" }` permits only simple inline
typography, not arbitrary CSS. Complex math and new diagrams may be supplied as
hash-bound assets inside the current run: `assets.NAME` has `path`, `sha256`,
`width_pt`; `figure: NAME` and `figure_position: right|below` reserve figure space.
`{{asset:NAME}}` places a checked inline asset in the stem/solution; an inline
asset that collides with text must be moved into a measured display block.
The renderer does not author or validate equations. Check notation and graph
labels at readable resolution. It rejects overflow; never shrink fonts to fit.
The common base is 11 pt with measured line flow; validate its suitability
against the selected subject's role-specific typography before production.

A fill block places exactly one `{{answer}}` in the semantic answer location.
`rows: [3]` means three integer positions; `[1,2]` means one numerator and two
denominator positions. IDs are centered inside circles, with ruled rows, and
the complete rail height participates in flow. This is no permission to change
the independently verified answer encoding. Radicals, signs and other patterns
need their own checked response asset; do not force them into plain digits.

Each complete block is measured before painting; a section stays with its next
block. Very long items/solutions require explicit continuation blocks with the
same item ID; no automatic truncation. Shared stimulus parts use one owner ID
and must also be considered when reviewing all dependent items. Real image/text
bounds and the compositor's outside-body check supplement the HTML measurement.
They are not a general proof of collision-free layout or sufficient page density.

## Reserve review time before the last minutes

For a web conversation observed to stop around 25 minutes, plan to reach final
layout by about minute 17 and reserve about 8 minutes for page/item inspection,
repairs and the final checker. This is a scheduling budget, not a platform limit
claim or guaranteed runtime. Keep the existing inclusive phase clock. Do not
wait until all items are written to discover a broken equation/rail renderer:
render and inspect the first 2–4 newly authored items AND their solutions early,
then solve, review difficulty and check layout in small batches.

Reuse the tested renderer, verified assets and calibration. Do not repeatedly
load every subject, download originals during final QA, or rewrite the PDF
engine. If authoring consumes the reserve, persist the SAME paper and continue
its unfinished reviews next turn. Do not reduce difficulty, omit real checks,
invent passing observations or restart a new paper to meet the clock.

## One preparation command for both final booklets

Save exam.json and its current hash in run-state.json, then compose both PDFs.
Keep all artifacts inside that run. With renderer-produced body layouts:

```text
python scripts/prepare_hosted_review.py --state run/run-state.json --question run/questions-v1.pdf --question-body run/questions-body-v1.pdf --question-layout run/questions-layout-v1.json --solution run/solutions-v1.pdf --solution-body run/solutions-body-v1.pdf --solution-layout run/solutions-layout-v1.json --output run/qa-v1
```

This batches mechanical inspection, whole-page images, readable item crops and
pending review records. It checks body hashes and compares projected body crops
to the actual final PDF before rebinding page numbers. It writes a new
`run/qa-v1-run-state.json` beside the original state and `run/qa-v1/index.html`.
Open the actual page AND item images, not just thumbnails. Record observed
defects and repairs in the generated reports; no helper supplies passing prose.

After actual review, refresh only report digests and run the final checker:

```text
python scripts/prepare_hosted_review.py --refresh-state run/qa-v1-run-state.json
python scripts/check_hosted_run.py run/qa-v1-run-state.json --output run/final-check.json
```

Finish the actual timing intervals and save their digest as required by the
existing timing workflow before the checker. Refreshing review hashes does
not close timing, approve content or resolve a failed gate.

For a repaired version, pass the prior reviewed state and NEW output names.
The helper retains an actual previous passing review only when the exam hash,
page/item identity and exact newly rendered pixels match. Page issue lists must
also match. Changed parts start pending. State honestly that unchanged visual
reviews were retained; do not claim they were freshly inspected. Changing the
exam invalidates reuse. Every final PDF still receives fresh mechanical checks,
fixed-layer verification, crops and the final checker. This cache belongs to
the same paper, never to a newly generated exam.
