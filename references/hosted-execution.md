# One hosted execution route

Use this route for a complete paper in ChatGPT, Claude or Gemini with file/code
tools. It governs hosted scheduling and evidence serialization. Local repository
maintenance, source-corpus rebuilding, installation and release-package audits
are separate operations; do not run them during ordinary hosted generation.
The subject's curriculum, structure, originality and quality requirements remain
binding. This route does not promise completion inside a provider's turn limit.

## Load once and begin the paper

When a native Skill already exposes its scripts and references, use
`python scripts/read_web_knowledge.py --source-dir NATIVE_SKILL_DIR --subject
SUBJECT --output-dir VERSIONED_REFS --reading-plan`. Its package manifest is
checked before the selected runtime files are copied. ZIP filenames are portable
ASCII names; `runtime_path` in the manifest restores original canonical paths in
VERSIONED_REFS with unchanged file bytes. Run subsequent helpers from
VERSIONED_REFS, not the installed ZIP directory. This one local copy is scoped to
the selected subject; it requires no aggregate Markdown, reinstallation or
repository download. Reuse that reference directory on continuation.

Otherwise extract the uploaded knowledge file once with `read_web_knowledge.py KNOWLEDGE
--subject SUBJECT --output-dir VERSIONED_REFS --reading-plan`. Read this
`reading/preflight.md` index now, then its numbered chunks in order. Each chunk
is at most 12,000 characters: open separately, never concatenate all chunks into
one truncated output. Read the authoring, review and layout indexes/chunks when
their work begins, retaining previous observations. The index names canonical
Markdown already embedded in full; do not reopen the same reference. JSON records
remain on disk with exact pointers; do not dump them into context. The full hash-checked
canonical files remain on disk for helpers. Do not print executable code, full
source maps, unrelated subjects or legacy curriculum statistics into the chat.
Do not recursively read the local execution manual merely because an older
reference links to it. For hosted runs this document is its execution route;
read a linked subject rule when it changes the actual item being authored.

Use one run directory and paper ID. Reuse a surviving same-paper checkpoint;
verify its file hashes and continue the first unfinished action. A new user turn
does not require reinstalling, restarting preflight, rewriting the paper or
repeating already recorded work on unchanged inputs. If files have expired,
recover the actual saved artifacts or report the missing files precisely.

Before drafting, confirm file creation, Python/PDF operations and readable image
inspection in the actual runtime. Use an already tested body font. Start the
inclusive `hosted_run_timing.py` logger with `reference_preflight`; record actual
transitions rather than reconstructing times later. Then run:

```text
python scripts/prepare_hosted_run.py --subject SUBJECT --run-dir run --paper-id PAPER_ID --font FONT --resource-pdf UPLOADED_RESOURCE_PDF
```

If no resource PDF was supplied, omit that option and use the helper's bounded
acquisition. The resource PDF's embedded original attachments are the templates;
its visible information page and the subject preview PDFs are not templates.
Open the small preflight proof images once to verify actual glyphs/field fit.
After `ready-for-authoring`, use the saved original subject components and
calibration. No separate manual four-file rehash, repeated smoke test or original
official PDF download is required. The final gate independently checks the final
bytes. A verified offline calibration is valid without pretending its original
official PDFs were viewed. Future simulation years may use the current verified
regime until an actual structure change requires different evidence.

Choose a real independent reviewer if available. Otherwise ordinary hosted work
uses `single-context` and an answer-free second solving pass. Do not invent a
second identity or stop solely because a subagent is unavailable. An explicit
user request for independent review still requires a real separate reviewer.
Inspect optional layout preview PDFs once, only for the selected subject pair.

## Author once, with small saved batches

Read `reading/authoring.md` before creating content. Use the selected paper
profile's actual scored slots, response forms, printed directions, score and
duration. The generated paper uses `schemas/exam.schema.json`: questions contain
`id`, `number`, `section_id`, `type`, `prompt`, options and item specifications;
answers use `schemas/answer.schema.json`. `schemas/question.schema.json` describes
historical corpus metadata, not this generated question object. Do not populate
both incompatible representations. Keep source registries and review records
outside student-facing text where the subject requires internal-only provenance.

Write new objects, information relationships, solution paths and distractors.
Do not reuse preview questions, stored generated papers, constant-swapping
builders, fixed unit-to-context menus or a permanent set of figure types.
Consider at least three structurally different mechanism candidates per slot.
Record concise mechanism sketches and selection reasons, not three complete
unused question/solution/PDF sets. Fully develop the selected candidate only;
the originality record and accessible-history comparison must describe real
work. Shared stimulus and mixed-group dependencies need their own review.

Use actual current-source verification when the selected item depends on recent
facts; a verified template never verifies those facts. Freeze sources, dates,
rights and claim transformations once. Reuse that registry within the paper.
Do not repeatedly search for historical templates, helper source or already
verified facts. Preserve subject-specific source ecology and literacy demands;
a topical name or decorative image is not an answer-bearing relationship.

Before writing stems, create a structural plan with
`check_paper_plan.py --skeleton --subject SUBJECT --paper-id PAPER_ID --year 116 --report run/paper-plan.json`.
Complete the actual band, time, answer-position and visual choices in its `items`,
four-band totals and answer distributions. Run
`check_paper_plan.py run/paper-plan.json --report run/plan-check.json` once before
expensive authoring. It checks scored slots, scores, five-strand partition where
applicable, four-band points/counts, answer counts, visual floors and total time.
These are planning checks, never a reason to distort the eventual correct key.
The plan is separate from student content and review evidence. Scored subparts
have separate slot IDs even when their printed question number is shared.

Use `emit_item_skeleton.py --subject SUBJECT --number N` for the exact slot and
Math A/B profile targets/minimum decisions. Its null/pending fields need actual
content and review; no pass is prefilled. Read `difficulty-field-contract.md`
for enums and content-hash rules instead of reverse-engineering validator code.
For shared numbered subparts use `--subpart`; unnumbered tasks use `--slot-id`.

Save editable content, diagrams, candidate decisions and review progress every
two to four items, before starting more figures or a long tool call:

```text
python scripts/append_items.py --run-dir run --plan run/paper-plan.json --batch run/batch-01.json
```

The batch contains actual `questions` and matching `answers` with solution
reasoning. The helper atomically creates/updates `exam.json`, then registers its
current checkpoint. On a surviving run, retrying the identical batch safely
reconciles an interrupted write without duplicating items. Later batches do not
require `--plan`; deliberate replacements require `--replace`. Preserve existing
review reports: changed content invalidates their old hashes and returns to
pending. Numbered subparts require distinct `subpart_id`; unnumbered tasks retain
their actual display/answer label. Check scope, answerability, shortest routes, distractors and
score sums early. Inspect the first authored items and their solutions with the
maintained body renderer before producing twenty items with broken typography.
Complex formulas need actual readable verification; plain HTML success does not
prove superscripts, fractions or radicals are correct. Use deterministic assets
for exact diagrams and data. Do not shrink text or pad content to meet a page
count. Preserve the actual subject's instruction and response geometry.

For Math A/B the current project profile requires easy score **below 10**,
medium-hard plus hard score **at least 70**, and hard score **at least 30**.
Retain the reviewed 80–92 minute hand-solving target, at least 50 points with
three necessary decisions, and the subject-specific stricter Math B rules.
Routine-only work cannot be labelled hard and remains capped at 25 points.
Use at least four distinct answer-bearing visuals across at least three sections
and more than one role; these are not four fixed diagram recipes. Source credits
remain internal unless the actual subject/rights requirements demand otherwise.
Do not transfer Math A/B difficulty percentages, time or rails to other subjects.
Other subjects keep their own form, calibration, sources and difficulty rules.

## One real review can support several checks

Read `reading/review.md` and review each completed batch before final layout.
For a single context, create the answer-free packet with `hosted_blind_review.py`;
derive answers from printable conditions and actual visuals, then compare the
saved key. Adjudicate every option, ambiguity, domain restriction and rubric.
Search for shorter routes and scaffolding supplied by earlier items. Estimate
necessary decisions and time against the saved compatible calibration, then
reconcile the paper's difficulty balance. Numerical/symbolic verification or
another derivation supplements high-risk items; it does not establish difficulty.

This same actual review may supply `answers`, `difficulty.answer_recheck` and
the answer's review fields. Store the result once and reference or mechanically
project the relevant findings into required artifacts. Do not solve the unchanged
item again just because two gate names request the same evidence. Do not replace
distinct judgments with one generic pass statement: correctness, difficulty,
originality, source grounding and visual necessity each need their actual finding.
The projection cannot supply invented review observations or reviewer identities.

Use the hosted evidence format in `hosted-run-evidence.md`; do not also assemble
the local run-contract/delivery JSON or local HTML proof package. Keep the required
item and whole-paper checks, current hashes, unresolved findings and actual
review mode. Run cheap content checks on batches and final balanced content;
once a relevant input changes rerun its dependent checks. Do not rerun an entire
completed chain because an unrelated metadata note changed without first
identifying which bindings and judgments it invalidates. Follow the checker’s
actual hash contract; never copy stale approvals onto changed content.

## One layout and review preparation pipeline

Read `reading/layout.md`. Use `hosted_body_templates.py` components and the
selected subject's question/solution layout pair. Put authored content in the
current run's body specifications; never rewrite a PDF engine for ordinary
blocks. Preserve original fixed PDF layers as immutable backgrounds, including
the subject-specific formula page for Math A/B. Body flow must reserve complete
answer rails, equations, figures and shared stimuli before painting later items.

After content review and both body specifications exist, the maintained pipeline
renders both bodies, composes both fixed-template PDFs and prepares their actual
page/item review together:

```text
python scripts/run_hosted_workflow.py build --state run/run-state.json --question-spec run/questions-blocks.json --solution-spec run/solutions-blocks.json --font FONT --year 116 --output run/build-v1
```

Use the returned review state and image index. Open every actual new or changed
page at readable scale and every new or changed item crop; thumbnails/contact
sheets only navigate these images. Record defects and concrete observations in
the generated pending reports. Inspect formula geometry, labels, response rails,
collisions, whole-page density, missing material, answer separation and grayscale
readability. A machine report cannot replace this visual work.
`needs_full_resolution_review` and its reasons identify pages needing priority
magnification; those rasters are prepared at higher resolution. Every page and
required crop still needs review. A false flag does not prove visual quality;
zoom any uncertain page regardless of the heuristic. Density findings
require compatible measured evidence; prose cannot waive a collision or a large
terminal void. Repair affected specifications and use a new build output path.
The helper may retain only qualifying actual reviews of unchanged same-paper
pixels; changed content still requires its dependent editorial review.

Use `run_hosted_workflow.py checkpoint --run-dir run --phase authoring` after
preflight to create/register the run state. `append_items.py` already checkpoints
each batch; do not duplicate that call just to register the same hash. For a repair,
supply `--state RETURNED_REVIEW_STATE`
so the latest surviving reviews are retained. `--review-bundle FILE` can fan out
one JSON object of actual named gate reports without generating observations.
Measure solving and difficulty review when those activities actually happen.

After real reviews are complete, finalize once; this closes the active clock:

```text
python scripts/run_hosted_workflow.py finalize --state RETURNED_REVIEW_STATE --output run/final-check.json
```

This refreshes artifact digests and runs `check_hosted_run.py`; it does not author
passing reviews. Fix the reported failure, not unrelated phases. Delivery needs
both separate downloadable final PDFs and current complete evidence. Disclose
the actual review mode. `evidence-complete` means recorded evidence is complete
and current, not official certification or empirical psychometric validation.

## Time and continuation

Time phases by primary activity: `reference_preflight`, `authoring`, `solving`,
`difficulty_qa`, `render_repair`, `visual_qa`. Batch independent calculations and
file operations inside one tool invocation where supported; changing phase must
not require a user reply. Use a short progress update instead of displaying every
manifest or internal record. Save before long work and after each reviewed batch.
Reserve final review time early. If a provider interrupts, continue the same
paper from saved work and unresolved checks; do not regenerate successful phases.
The 20-minute benchmark is measured, not an acceptance deadline. Finish required
QA even if the target is missed; never fake completion or lower difficulty to
fit a clock. A provider limit cannot be removed by this Skill, and surviving
temporary files must be verified on continuation.
