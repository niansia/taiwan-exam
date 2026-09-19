# Hosted quality: actual content and measured work

Required with hosted-run-evidence.md. These helpers detect specific defects;
they cannot turn fabricated reviews into real visual or academic acceptance.

## Layout before claims

Use the measured components and batch-review procedure in
hosted-body-workflow.md. Do not overlay fill circles onto a completed page.
A row identifier belongs inside its circle, with the correct integer/fraction
rules and an answer position connected to the stem. Inline placement or a
measured line wrap must reserve the full rail height. The low-level
hosted_item_layout.reserve_rail / draw_rail helpers provide a line-wrap fallback:
start below the actual union of stem, equations and figures, at the semantic
blank's left edge, with at least 6 pt clearance; advance to next_y. They are not
permission to center a detached second blank on the page. Special response
patterns require equivalent measured components and actual visual inspection.
The native circle/label format detector rejects recognizable misplaced IDs or
missing row rules; raster rails, unusual outlines and other response forms
still require readable crop review. Never shrink text or clip figures to fit.

Keep measured non-overlapping blocks for every item. Inline equations belong
inside their stem block; figures, display formulas and rails get separate blocks.
Before composition run hosted_item_layout.geometry_errors to check cross-item
figure/stem intersections and rail gaps. compose_hosted_pdf additionally rejects
native rail labels intersecting text or outlined math. The final inspector and
checker repeat this on saved bytes. answer-rail-content-collision cannot be waived.

After composition offset measured body page numbers for the cover. Write
layout.json with pdf_sha256 and parts: each has id, page (one-based), bbox
[x0,y0,x1,y1] in PDF points, components [{role,bbox}]. Long items/solutions have
multiple parts with the same id. Include continuations, shared stimulus and full
figures. Cover/formula pages get whole-page review, not fictional question IDs.

```text
python scripts/hosted_item_layout.py --pdf question.pdf --layout layout.json --output item-crops --report question-items.json
```

The report starts pending (or retains a qualifying actual review of an unchanged
item under hosted-body-workflow.md). Open EVERY new or changed crop at readable
resolution (2 pixels/pt), inspect stem, options, rail, equations and every diagram
label, then record status and concrete observations for each part
(`run_hosted_workflow.py record-review` writes them). Keep crops unchanged. Repeat for
solutions; register each report as pdfs.ROLE.item_review. The checker rerenders
crops from final bytes and verifies geometry, coverage and freshness. Every item
must own a reviewed part or be listed in the `covers` of the part that prints it
(a suppressed gap in its passage, a subpart inside its question); reviewing that
crop means checking every covered item's printed content too. A contact
sheet is not item review. Renderer boxes can omit content: compare crops to the
authored content AND whole pages. The narrow rail detector cannot discover all
clipped/outlined objects, and supplied geometry is not independently inferred.

## Measured density, not a prose waiver

For large-bottom-void-review, the default offline issue disposition contains
`kind: embedded-page-metric`, `source_sha256`, `reference_page` (one-based),
`page_role` (cover/formula/body/solutions), and decision/reason. Select a comparable
page from the subject's preflight `calibration.json.page_metrics`. These numeric
measurements were built from byte/hash-verified official sources at release time;
no original question text or source PDF is included. The checker reconstructs the
capsule from canonical files, validates source identity and measurement algorithm,
requires the actual candidate role to match, and remeasures the candidate PDF.
Scoring-rule pages are rubric references, not full worked solutions: their use
still needs a concrete editorial explanation of compatible density and content.
Alternatively retain an already available same-subject official 111–115 PDF and
use `reference_pdf: {path, sha256}`, reference_page, page_role and decision/reason.
This legacy route verifies its source hash and remeasures both PDFs. Choose the
route at preflight, never start downloading originals during final QA.
Candidate bottom void cannot exceed reference by over 10 percentage points.
This conservative review threshold is project policy, not an official exam rule.
The build precomputes each flagged page's `density_evidence`: its role and up to
three same-role embedded measurements within that limit, or
`exceeds-all-embedded-references` when none qualifies (reflow first). Selecting
one with `embedded_reference` in record-review copies its identity; the reviewer
still confirms the page is genuinely comparable and writes the reason.
Editorial review must verify role compatibility: never compare an interior page
to a sparse cover/formula page. A self-created reference or scratch-space reason
cannot waive failure. Reflow and inspect new bytes when it fails.

## Capability-aware difficulty review before final rendering

Choose the mode before authoring. Prefer `independent-context` when a real
separate reviewer is available. With only one context, automatically choose
`single-context`; this is an accepted ordinary delivery route, not a reason to
halt or require the user to open another chat. If the user explicitly requires
independent review, preserve `require_independent_review: true` in the run plan
and arrange a real separate reviewer instead of silently substituting self-review.
The Python helper cannot discover a model's available tools or create a reviewer.

For all seven subjects run:

```text
python scripts/hosted_blind_review.py exam.json review-packet.json --review-mode single-context
```

Use `--review-mode independent-context` for an actual separate reviewer. Both
packets retain visible ordered questions, continuations, options, response tables
and visuals, excluding author difficulty labels and item_spec. The independent
packet also retains solutions. The single-context packet excludes all answers:
first derive answers/interpretations and shortest routes from those questions,
then compare with the saved answer paper and adjudicate discrepancies. Check all
options, domain restrictions, alternate readings and constructed-response rubrics.
Use numerical/symbolic checks or a different derivation for high-risk items where
practical. Removing answers from a file does not erase conversation memory or
make the same model blind. Record actual findings, not a second fictional identity.

Supply actual referenced visuals and compatible 111–115 calibration. In a real
separate context, withhold prior author judgments. Request shortest valid routes, necessary
decisions, shortcut searches, provisional difficulty/time and concrete comparisons
against the available calibration. Default offline route: give the reviewer the
subject's preflight `calibration.json` and record each item's
`anchor: {kind: embedded-calibration, key: ...}`. For objective Math A/B items the
key is `slot:N` for the actual question number; other objective subjects use
`objective`. Constructed responses and 國寫 use `constructed-response`, with
explicit rubric/task-demand comparison to aggregate patterns (and the embedded
writing rubric for 國寫). Never borrow 國綜 objective P/D for 國寫. Preserve the
objective profile's `full_paper_status: insufficient-data`: its statistics do
not cover all constructed responses or establish empirical difficulty of new
papers. The checker verifies the whole saved capsule against canonical content;
author-written readiness flags are insufficient. `anchor_comparison` must say
what historical aggregate/rubric feature supports or challenges the estimate,
including shortest-route differences and limitations; numbers alone cannot pass
academic review. Aggregate review is not a claim of viewing individual originals.

If a compatible original PDF is already available, a stronger item-to-item route
remains supported: `anchor: {reference_pdf: {path, sha256}, page, item}` where
page is one-based and item identifies the compared official question/task.
The checker verifies the actual source bytes against the embedded same-subject
111–115 map and checks the page exists. The reviewer must actually read that
page: this check cannot judge whether the comparison is truthful or well chosen.
Correctness alone does not fulfil difficulty QA. Seek linear-combination
shortcuts, small-n enumeration and unused conditions; long solutions do not prove
required solving effort.

The difficulty report adds `review_mode` and the legacy-named `blind_packet`
(path/sha256; also used for the answer-free single-context packet), plus real
author_context and reviewer_context identifiers. For `single-context` they must
be the SAME actual context; add `independent_review: false` and `review_reason`
describing the available capability. Every item additionally has `answer_recheck`:
the actual new solving/evidence route, comparison with its saved answer and any
resolved correction. Do not copy the original explanation as a supposed recheck.
For `independent-context` the actual contexts must differ. Legacy reports without
review_mode retain that stronger meaning, so changing only IDs cannot bypass it.
Each item adds shortest_route, decisive_steps,
shortcut_search, anchor_comparison, expected_minutes, difficulty_band
(very_easy/easy/medium/hard/very_hard), unresolved (empty after resolution).
The checker reconstructs the mode-specific packet and blocks false independence,
missing per-item rechecks, author time over 1.5 times the reviewed estimate or
two-band overestimation in BOTH modes. It checks evidence, not whether a model
actually performed the claimed reasoning.
Revise items or adopt the defensible estimate, then rerun the existing whole-paper
balance audit using it; never inflate estimates to reach 80–92 minutes. These
twenty-item papers also need the reviewed estimates to meet the existing
80–92 minute target and three-decision coverage of at least 50 points. These
thresholds are review policy, not student psychometrics.

Math item reviews also contain `routine_only` (boolean), `uses_prior_results`
(list of earlier item IDs, empty when none), and `scaffolding_audit` explaining
the effect of earlier questions, options and supplied intermediate results.
Only decisions still necessary on the shortest in-booklet route count: substituting
three coordinates is one routine operation, not three modelling decisions.
Routine-only items cannot be hard/very_hard or count toward the 50-point
three-decision floor; their total is capped at 25 points under project policy.
Keep legitimate easy opening items and necessary scaffolds; replace enough
weak mechanisms to restore the intended curve, without inflating estimates or
adding irrelevant computation. Apply the same reasoning to Math B, preserving
its own scope and reference difficulty rather than copying Math A difficulty.

The reviewed five-band estimate maps to the four-band plan as very_easy/easy
→ 簡單, medium → 中, hard → 中偏難, very_hard → 難. Reconcile every item and its
answer label, then rebalance the actual plan. The checker reruns the structural
four-band validator for all subjects and the subject-profile math design validator
for Math A/B; citing those command names in an observation no longer substitutes
for execution. Math full papers must really have numbered items 1–20.

For 國綜/英文 review evidence inference and distractor elimination, not passage
length alone; for 自然/社會 review data interpretation, competing explanations and
constraint use, not recent-news terminology; for 國寫 review prompt demands,
source synthesis, reasoning and feasible writing time, not imposed wordiness.
Do not transfer the mathematics 80–92 minute target to other subjects.

These fields cannot authenticate reviewer identity: never invent a second context.
At delivery say which mode actually ran. For single-context use a concise note
such as「已完成單一工作階段的逐題解題與難度複核；未經第二個審閱者獨立審查。」
It may complete the ordinary Skill workflow after ALL checks pass, but must not
be described as independently reviewed, blind-reviewed or equivalent assurance.
If a review changes mode, redo the affected packet/review; never relabel unfinished
independent review as completed self-review. Missing content/visual evidence or
unresolved defects still remain pending in either mode.

Four required math visuals is a coverage floor, NOT four fixed picture types.
Apply math-current-events-and-sourcing.md for recent-event model design and
internal-only source records; topical arithmetic does not satisfy literacy.
Derive information relationships first, then choose representations. Do not reuse
a permanent geometry/function/probability menu or merely rotate constants. Compare
accessible prior papers' mechanisms, shortcuts and visual topology.

## Required timing and earlier rejection

prepare_hosted_run.py starts the run's generation-timing.json at
reference_preflight (hosted_run_timing.py generation-timing.json PAPER_ID phase
reference_preflight does the same by hand). Record authoring, solving and
difficulty_qa with `run_hosted_workflow.py checkpoint --phase`; build and proof
record render_repair and visual_qa, and finalize closes the final interval.
Use all six actual phases, repeat names for repairs, preserve the log in recovery
material, and register it as run-state.timing. Never reconstruct missing intervals
from memory. The checker requires positive, ordered, closed intervals for all
phases and computes total/per-phase times. Interruptions remain wall time.
Above 1200 seconds it reports target_met=false and continues QA; the benchmark
is not a delivery deadline. Missing timing is pending. Do not exclude template
acquisition or repairs to improve reported speed.

Review difficulty in small batches and repair body layout BEFORE fixed-template
composition. Cache verified immutable assets/source metrics. The compositor
reuses font bytes and parity-template reference rasters within one call while
checking every output page's locked pixels. Changed content/PDFs revoke dependent
reviews. If interrupted, save editable work, reviews, timing and exact next action.
Never call unfinished PDFs complete. Without a timing log, do not attribute an
entire 25-minute run to one phase or promise to remove the platform's timeout.
