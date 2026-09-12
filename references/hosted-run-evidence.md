# Recoverable hosted work and evidence-complete delivery

Use for every hosted full paper, including a single paper with no requested time
target. This is the recorded implementation of web-platform-use's hosted gate,
not a substitute for local validate_exam_release or a new academic standard.
Apply [hosted-quality-gates.md](hosted-quality-gates.md) alongside this format:
actual PDF collisions, item crops, blind difficulty and timing are mandatory.

## Work that survives interruption

Create one run directory and paper_id before writing. Save exam.json, original
editable visual assets, candidate decisions and independent solution records in
small batches (normally two to four items), updating run-state.json each time.
Review each item's shortest solution, provisional difficulty, comparison with
recent accessible mechanisms, and visual-removal test before proceeding. Preserve
failed items and reasons separately; only selected items enter the paper.

Record turn_started_at, measured elapsed time, known runtime limits if exposed,
and next_action. A user's reported approximately 25-minute interruption is an
observation, not a universal provider guarantee. When a limit is known, reserve
at least five minutes for saving and remaining review; begin checkpoint handoff
before that reserve is consumed. Without a visible limit, save periodically and
before every long operation rather than assuming unlimited time. These are
scheduling margins, not claims that five minutes is enough to inspect any paper.

Do not spend the remaining budget drafting more content while difficulty and
layout checks accumulate. Finish missing content review before rendering. If
the remaining work cannot fit, save and expose a continuation record with exact
next actions; do not claim the paper complete or attach unchecked PDFs as formal
deliverables. Continue autonomously in the same active turn when possible; no
per-phase approval is required. If the platform ends the turn, a later "continue"
resumes the same run after verifying saved files. A changed item revokes its
dependent reviews; a changed PDF revokes its page reviews. Missing temporary
files require the saved recovery material, not a claim that they persist forever.

When interruption risk is known, keep an accessible recovery copy of exam.json,
run-state.json and review/visual files; an optional data-only recovery bundle may
contain those run files, never the Skill executable tree. It is a work checkpoint,
not a third completed exam or a request to install again. A JSON index alone
cannot recover missing referenced files. Show a short progress/next-action note.

## Evidence format and checker

Run from the run directory. All paths below are relative to it, including raster
paths emitted by `inspect_hosted_pdf.py --rasters rasters/...`. No external paths
or symlinks out of the directory are accepted. Hash each file after saving it.
Do not invent successful review observations or manufacture reviewer identities.

`run-state.json` has schema_version 1, paper_id, current_phase, next_action,
exam (`path`, `sha256`), timing (`path`, `sha256`), template_asset_dir, checks, and pdfs.
template_asset_dir is a relative directory INSIDE this run containing the selected
subject's verified `cover-blank.pdf`, `inner-odd-blank.pdf`, `inner-even-blank.pdf`
and, for Math A/B, `formula-blank.pdf`. Keep these assets in recovery material.
The gate verifies their size/SHA against the canonical map, then independently
compares both FINAL PDFs with those assets. It checks every page's locked pixels,
reachable original PDF content streams, actual page counters and math formula body.
An unused attachment, screenshot, retyped lookalike or `template_composition: pass`
cannot stand in for that comparison. Template checks do not inspect body pedagogy. exam.json uses the existing exam schema:
metadata.paper_id, metadata.subject, questions with unique id and section_id, and
the full authored answers and item specifications. Its hash binds each review.

`checks` maps each of these names to an artifact (`path`, `sha256`):

- answers: every item independently solved, options adjudicated and key compared;
- difficulty: shortest routes, genuine decisions, provisional bands and collapse
  findings per item; execute the embedded validate_math_difficulty_design.py for
  mathematics using the extracted subject difficulty profile;
- originality: concrete structural differences per item, candidate selection and
  recent-paper comparison; carry comparison_scope (`available-history` or
  `no-history-available`) and history (hash-bound artifact records). Available
  history must really be supplied. No-history never means globally original;
- visuals: every item reviewed, including explicit not_applicable findings for
  nonvisual items. Required visuals have required_for_answer true, visual_id and
  visual_role, and observations explaining the visual-removal result. Reused
  group visuals count once. The existing math floor remains four distinct
  answer-bearing visuals across three sections and more than one role;
- structure_scope, difficulty_balance, source_grounding, template_composition,
  answer_separation: whole-paper findings and actual supporting evidence.

Every review JSON contains exam_sha256, status and nonempty observations.
The first four also have items: one record per actual question id, with id,
status and observations. Only visuals may use not_applicable with a reason.
Use the embedded validate_paper_difficulty_balance.py for its structural audit;
The final checker also executes it directly; its output alone does not prove achieved difficulty. Reference actual reports
in the observations and retain them in the recovery copy.

`pdfs.question` and `pdfs.solution` each contain file, inspection, item_review and visual_review
artifact records plus exam_sha256. Inspection is the unchanged output of
inspect_hosted_pdf.py on that final PDF. The visual_review JSON contains
pdf_sha256 and pages, one for EVERY actual page: page, raster_sha256, status,
observations, and issue_dispositions. Each unresolved inspector issue blocks
completion. A legitimate role-specific warning can be adjudicated with
`{"decision":"justified","reason":"actual page/reference observation"}`.
Bottom-void findings additionally require the actual verified official reference
PDF and numeric comparison specified in hosted-quality-gates.md. Prose alone
cannot waive them. Hard collision findings can never be waived by a reason.
Repairing a warning means regenerating and inspecting new bytes, not writing
"fixed" against the obsolete raster. Hard mechanical failures always block.

Execute `python scripts/check_hosted_run.py run-state.json` using the extracted
helper location as appropriate. Nonzero exit lists missing/stale checks and
unresolved page findings. `evidence-complete` certifies completeness/freshness
of recorded evidence only; it cannot independently certify truthful reviews,
mathematical correctness, difficulty, global novelty or fidelity to an unseen
source. Formal completion still requires actual editorial judgment under Skill.

## Avoid repeated mechanisms

Before each new paper, read accessible prior-run originality reports and compare
mechanism_family, representation/visual topology, unknown, constraint interaction,
solution graph and distractor logic. Keep these concise records as a cumulative
series history, including rejected saturated motifs. Identical curriculum units
are normal; renamed objects or changed constants do not reset the mechanism.
Do not embed prior stems or a permanent unit-to-figure menu as authoring templates.
A user screenshot diagnoses a failure; it is not a mandatory future question.
