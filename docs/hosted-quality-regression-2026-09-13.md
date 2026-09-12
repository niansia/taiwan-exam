# Hosted PDF quality regression and scope

User-supplied second Math A output exposed a failure of the prior hosted evidence
gate: page-review declarations and author difficulty metadata could be complete
while actual rails overlapped stems. This correction updates source and web
knowledge to **2026.09.13.1**. The immutable, separately scanned v0.7.1 ZIP is
unchanged and does not contain these later fixes.

## Reproduced evidence

- The supplied eight-page question PDF SHA-256 is
  `5c8bf8f9e12447ba4210a4f5331c08d1d92ed06dd2fc7f0e0b1ca811283ca0cd`.
  The new actual-PDF rail detector blocks physical pages 6 and 7, identifying
  labels 13-1, 14-1, 15-1, 15-2, 16-1 and 17-1. Native text AND vector-outline
  math matter: ordinary text extraction misses some printed equations.
- Local inspection of all eight pages, including raster production, took
  0.786 seconds in one run. The narrow detector scanned this PDF and the actual
  115 Math A official paper together in 0.369 seconds; the official paper had
  no rail findings. These timings are observations, not guaranteed latency.
  A further local scan of all 35 original 111–115 question PDFs across seven
  subjects also produced no rail findings. This checks a false-positive sample,
  not the detector's ability to find every possible layout defect.
- A separate reviewer received only the supplied question/solution PDFs and
  instructions to review questions 13–16, without author labels or prior reviews.
  Answers 120, 8, 12 and 5 were correct. Q14 can use equation combinations without
  solving all three unknowns; Q16 can inspect the first few terms instead of
  deriving general formulas. These are concrete shortcuts undermining difficulty
  inferred from solution length. The reviewer also found Q15's A vertex/label
  obscured by Q16. This was a bounded four-item review, not whole-paper acceptance
  or empirical student timing. The PDFs are not redistributed in this repository.

## Implemented changes

- Final-PDF rail collisions are hard failures, rechecked from bytes by the
  delivery checker even if an inspection JSON claims no issues.
- Reusable measured rail reservation and item block checks account for the full
  height of figures before placing following content. Overflow asks for reflow;
  the helper does not hide content or reduce font size.
- Both booklets require readable item crops in addition to whole-page review.
  Crop bytes are reproduced from the saved PDF; supplied item geometry is checked
  for intersections and rail clearance. Renderer omissions still require actual
  visual/editorial review; this is not universal PDF collision detection.
- Sparse-page waivers need a same-subject official PDF with a hash from the
  canonical source map and a measured comparison. Prose alone cannot pass.
  The reviewer must select a genuinely comparable page role.
- Mathematics uses a label-free review packet and separate reviewer context.
  Shortcuts and independent estimates control discrepancy checks; twenty-item
  papers must also meet existing time/decision floors using independent records.
  Context fields cannot authenticate reviewers or prove psychometric difficulty.
- Six measured wall-time phases are mandatory. An exceeded 20-minute benchmark
  reports target_met=false while QA continues; absent timing leaves work pending.
- Font bytes and invariant parity-template rasters are reused within composition.
  Every output page still undergoes locked-pixel verification. An eight-page warm
  synthetic Math A composition with Windows Kai font took 15.543 seconds before
  and 12.255 seconds after; all eight rendered pages were pixel-identical. This
  one local comparison does not explain the user's 25-minute hosted run.
- The hosted schema now explicitly permits metadata.paper_id and visual coverage
  uses the schema's section_id field.

## Validation boundaries

Regression tests cover native/outlined collision rejection, clean template assets,
tall-figure rail reservation, cross-item intersections, stale crops/evidence,
missing timing/review files, prose-only density waivers, label removal and
shortcut-driven difficulty failures. Existing composition tests verify all seven
subjects' fixed cover, header/footer parity and formula pixels.

No new complete twenty-item hosted exam has been accepted by these code tests.
The original 25m49s run has no complete measured phase log available here; its
largest bottleneck cannot be stated as a measured fact. Platform execution limits
remain outside the Skill's control. Update the installed web knowledge attachment;
a GitHub change does not automatically replace an account's existing Skill.

## Subsequent current-context policy update: 2026.09.13.2

The math policy now selects 2–4 recent model-dependent items in a default full
paper, checks event/publication dates against the editorial lock, and keeps
provenance in internal records instead of printing source-note rows or URLs.
The new gate is used by hosted/local release checks; PDF text inspection catches
printed notes even if they are absent from source metadata. Other subjects'
passage attribution remains unchanged. Date, leakage and nonroutine-review
regressions join the existing layout/release checks; these remain software
tests, not evidence that an entire new exam achieves originality or difficulty.
