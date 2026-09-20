# Reusable body components and early visual QA

Use the single hosted-execution.md route for all seven
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
https://niansia.github.io/taiwan-exam/layout-examples/2026.09.14.1/index.html .
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

That low-level command is for a focused renderer repair. For batch item proofs
use `run_hosted_workflow.py proof`, whose crops use the fixed-page transform and
can carry an actual review forward. `run_hosted_workflow.py specs` writes both
specifications from the saved exam plus optional layout hints, so item text is
not typed a second time. For the two candidate booklets use
`run_hosted_workflow.py build` from hosted-execution.md: it runs both body
layouts, fixed composition and pending review preparation in one call. Do not
also repeat all low-level commands on the same inputs. The
body renderer alone outputs transparent pages, NOT deliverable exam PDFs. For viewing only the
placeholder gallery, supply `--proof`; never use that flag for a production run.

`passage` blocks contain `paragraphs`, an optional `heading`, `language: en`
for Latin passage typography, and optional `bank`/`columns` for one shared option
bank. `{{gap:11}}` produces a visibly underlined inline gap. A `table` block
contains `headers` and rectangular `rows`, with optional introductory `text`.
Use `keep_with_next: true` where a stimulus/table must stay with the next task;
oversized groups need explicit continuation instead of clipping or shrinking.
Use `label` for real subpart labels such as （一） rather than inventing extra
Arabic-numbered items; an unnumbered task (中譯英, 作文) may use a label without
`number`. Labels do not determine the scored-item contract. `passage` and
`stimulus` blocks may print one `group_label` (`group_label_style: underline`
for English, bold otherwise); a prose passage may set `indent: true` for justified
first-line indentation. `language: en` on an item block prints its English text
in the English face. `score_in_text: true` (with `printed_score` for a whole
question's total) declares score wording the authored text already prints; the
renderer verifies the wording instead of appending a second score. `covers` lists
other item IDs printed inside a block, such as suppressed cloze/completion gaps
or a subpart without its own printed text; the final item-crop coverage counts
them, so no filler rows are needed. `split: paragraphs` lets a long stimulus,
passage, constructed prompt or solution continue on the next page at paragraph
or step boundaries: the label, heading and group label stay on the first piece;
options, bank, score and figure stay on the last. `run_hosted_workflow.py specs`
sets these fields from the saved exam.

`--reading-font` can supply a separately verified reading-material font for
國綜/國寫. Main body and reading roles must retain the selected subject's visual
hierarchy. Some DFKai versions collapse Chinese advances in the HTML renderer;
the helper rejects this pattern. Use a compatible tested font, not a smaller
font or a claim that successful export proves text is readable.

Text is plain Unicode; `{ "rich": "…<sup>…</sup>…" }` permits only simple inline
typography, not arbitrary CSS. Complex math and new diagrams may be supplied as
hash-bound assets inside the current run: `assets.NAME` has `path`, `sha256`,
`width_pt`; `figure: NAME` and `figure_position: right|below` reserve figure space.
`{{asset:NAME}}` places a checked inline asset in stems, options, solution steps,
passages, headings and table cells. Save new artwork as SVG or a single-page PDF:
both are converted to an image at three times their printed width, so lines and
labels stay sharp, and this never rasterizes fixed templates. A raster figure
needs at least twice, preferably three times, its printed width in pixels.
Multi-page body assets must be split explicitly. The body prints 11 pt text on an
18 pt line, so an inline asset taller than that overlaps the line above: keep
inline formulas within one line and move anything taller into a measured display
block. `append_items.py` reports both sizes when a batch is saved.
The renderer does not author or validate equations. Check notation and graph
labels at readable resolution. It rejects overflow; never shrink fonts to fit.
The common base is 11 pt with measured line flow; validate its suitability
against the selected subject's role-specific typography before production.

A fill block places exactly one `{{answer}}` in the semantic answer location.
`rows: [3]` means three integer positions; `[1,2]` means one numerator and two
denominator positions. IDs are centered inside circles, with ruled rows, and
the complete rail height participates in paragraph flow. Do not split the stem,
rail and suffix into three table columns. Keep the rail at `{{answer}}`, with
the adjoining equation/unit/condition on the same readable line or at the end
of the stem; short prefixes such as `λ =` stay with it on wrapping. A fill item
with a figure uses below placement so a top-aligned side table cannot displace
its rail. Check actual baseline alignment, not only non-intersection. This is no permission to change
the independently verified answer encoding. Radicals, signs and other patterns
need their own checked response asset; do not force them into plain digits.

Each complete block is measured before painting; a section stays with its next
block. The measured PDF block is reused at full scale, including during gap
balancing; production placement does not repeat HTML exact-fit. The workflow
runs body rendering in a separate process with a 20-second progress timeout per
block operation, reporting the item ID and available/measured height on a stall.
A full-page measurement failure needs an explicit split/repair; moving an
oversized block to yet another empty page cannot fix it. Existing whole-block
pagination moves items that exceed only the current page's remaining space.
No timeout path shrinks text, drops content or certifies a partial PDF.
Each build saves `page-plan.json` from the actual measurements, with question
IDs, block heights, keep-with-next decisions and bottom safety distance. It is
a repair aid produced during layout, not a claim that density or QA passed.
A block that does not fit fills the rest of the page with its leading
paragraphs when it allows `split: paragraphs`; otherwise it moves whole, and a
block taller than a page needs explicit continuation blocks with the same item
ID. Nothing is truncated. Consecutive blocks of one owner on the same page form
one crop, so shared material and its item, or continued paragraphs, are reviewed
together. Shared stimulus parts use one owner ID and must also be considered
when reviewing all dependent items. Real image/text
bounds and the compositor's outside-body check supplement the HTML measurement.
They are not a general proof of collision-free layout or sufficient page density.

## Reserve review time before the last minutes

For a web conversation observed to stop around 25 minutes, plan to reach final
layout by about minute 17 and reserve about 8 minutes for page/item inspection,
repairs and the final checker. This is a scheduling budget, not a platform limit
claim or guaranteed runtime. Keep the existing inclusive phase clock. Do not
wait until all items are written to discover a broken equation/rail renderer or
a figure that crowds its stem: after every saved batch run `run_hosted_workflow.py
specs` and `proof` for that batch, review its item and solution crops at once,
then solve and review difficulty in the same small batch. Crop review done here
is not repeated for unchanged items in the final booklets; page review is.
Complete all content reviews before the first full build, then run
`run_hosted_workflow.py lock-content --state <latest-state>`. Keep necessary
early batch proofs; do not delay discovering a broken figure until the end.
Change layout hints during pagination. If content really needs correction,
renew its dependent reviews and re-lock with `--reason`; the previous lock is
retained. The lock records change control, never editorial approval.
If the provider does end a response before delivery, these checkpoints are
where the next turn resumes: reviewed authoring batches first, then one final
build, page review and finalize. Never end the response at a checkpoint yourself.

Reuse the tested renderer, verified assets and calibration. Do not repeatedly
load every subject, download originals during final QA, or rewrite the PDF
engine. If the provider ends the response during authoring, the next turn
continues the SAME paper's unfinished reviews. Do not reduce difficulty, omit real checks,
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
The returned `review_queue` names every pending page and crop image; the index
lists pending images first and retained ones last. Open the actual page AND item
images only for pending entries after a repair; unchanged pages still have
their actual, hash-bound prior reviews. Always pass the latest returned
`state` (also exposed as `continue_from_state`) to the next checkpoint/build,
not the initial preflight state. Finalize still checks both complete booklets.
Open the actual page AND item
images, not just thumbnails. Record observed defects and repairs with
`run_hosted_workflow.py record-review`, which writes the reviewer's findings and
refreshes report digests; no helper supplies passing prose. After hand-editing a
report instead, refresh only report digests and run the final checker:

```text
python scripts/prepare_hosted_review.py --refresh-state run/qa-v1-run-state.json
python scripts/check_hosted_run.py run/qa-v1-run-state.json --output run/final-check.json
```

Finish the actual timing intervals and save their digest as required by the
existing timing workflow before the checker. Refreshing review hashes does
not close timing, approve content or resolve a failed gate.

For a repaired version, pass the prior reviewed state and NEW output names.
The helper retains an actual previous passing crop review, from an item proof or
an earlier build of this paper, only when the item's authored record is
unchanged (review metadata excluded; a shared stimulus binds its group), the font
and painting helpers are unchanged, and the new crop is pixel-identical or prints
the same glyphs, rules and images within 0.02 pt. Composition scales the body to
the 594.96 pt fixed pages, so a reflowed but unchanged block rarely keeps exact
pixels; the primitive comparison separates that placement noise from any printed
change. A recorded non-pass finding on an equivalent rendering blocks reuse. A
page review is retained only for identical page pixels, issue lists and item
content; a page without item content needs identical pixels and printed section
text. Changed parts start pending. State honestly that unchanged visual reviews
were retained; do not claim they were freshly inspected. Every final PDF still
receives fresh mechanical checks, fixed-layer verification, crops and the final
checker. This cache belongs to the same paper, never to a newly generated exam.
