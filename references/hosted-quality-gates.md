# Hosted quality: actual content and measured work

Required with hosted-run-evidence.md. These helpers detect specific defects;
they cannot turn fabricated reviews into real visual or academic acceptance.

## Layout before claims

Do not overlay fill-in circles after laying out the page. Use
`hosted_item_layout.reserve_rail(content_boxes, x=..., slots=..., bottom_limit=...)`
with actual renderer bounds of stem, math, options AND figure. The rail starts
below their lowest bottom with at least 6 pt clearance. None requires moving or
reflowing the item. Draw with draw_rail and advance to next_y. Never shrink text
or clip diagrams to recover space. Special answer patterns need equivalent
measured flow blocks; draw_rail only provides plain numbered circles.

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

The report starts pending. Open EVERY crop at readable resolution (2 pixels/pt),
inspect stem, options, rail, equations and every diagram label, then add status
pass and concrete observations to each part. Keep crops unchanged. Repeat for
solutions; register each report as pdfs.ROLE.item_review. The checker rerenders
crops from final bytes and verifies geometry, coverage and freshness. A contact
sheet is not item review. Renderer boxes can omit content: compare crops to the
authored content AND whole pages. The narrow rail detector cannot discover all
clipped/outlined objects, and supplied geometry is not independently inferred.

## Measured density, not a prose waiver

For large-bottom-void-review, issue_dispositions must include reference_pdf
(path/sha256), reference_page (one-based), page_role (cover/formula/body/solutions),
and decision/reason. Choose a comparable same-subject page from the embedded
official 111–115 source map; verify/download once and retain it in the run.
The checker verifies its hash against that map and remeasures both PDF pages.
Candidate bottom void cannot exceed reference by over 10 percentage points.
This conservative review threshold is project policy, not an official exam rule.
Editorial review must verify role compatibility: never compare an interior page
to a sparse cover/formula page. A self-created reference or scratch-space reason
cannot waive failure. Reflow and inspect new bytes when it fails.

## Independent difficulty before final rendering

For math run hosted_blind_review.py exam.json blind-packet.json. It retains visible
questions, options, visuals and solutions, excluding author labels and item_spec.
Supply actual referenced visuals and compatible 111–115 anchors to a separate
reviewer context without prior judgments. Request shortest valid routes, necessary
decisions, shortcut searches, provisional difficulty/time and specific year/item
comparisons. Correctness alone does not fulfil difficulty QA. Seek linear-combination
shortcuts, small-n enumeration and unused conditions; long solutions do not prove
required solving effort.

The difficulty report adds blind_packet (path/sha256), real author_context and
reviewer_context identifiers. Each item adds shortest_route, decisive_steps,
shortcut_search, anchor_comparison, expected_minutes, difficulty_band
(very_easy/easy/medium/hard/very_hard), unresolved (empty after resolution).
The checker reconstructs the packet, rejects same-context reviews, and blocks
author time over 1.5 times the independent estimate or two-band overestimation.
Revise items or adopt the defensible estimate, then rerun the existing whole-paper
balance audit using it; never inflate estimates to reach 80–92 minutes. These
twenty-item papers also need the independent estimates to meet the existing
80–92 minute target and three-decision coverage of at least 50 points. These
thresholds are review policy, not student psychometrics. Fields cannot authenticate
reviewer identity: never invent a second context. If none is available, preserve
pending work for review in a fresh context.

Four required math visuals is a coverage floor, NOT four fixed picture types.
Derive information relationships first, then choose representations. Do not reuse
a permanent geometry/function/probability menu or merely rotate constants. Compare
accessible prior papers' mechanisms, shortcuts and visual topology.

## Required timing and earlier rejection

Start hosted_run_timing.py generation-timing.json PAPER_ID phase reference_preflight
before loading references. At transitions use phase with authoring, solving,
difficulty_qa, render_repair or visual_qa; finish closes the final interval.
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
