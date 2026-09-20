# One hosted execution route

Use this route for a complete paper in ChatGPT, Claude or Gemini with file/code
tools. It governs hosted scheduling and evidence serialization. Local repository
maintenance, source-corpus rebuilding, installation and release-package audits
are separate operations; do not run them during ordinary hosted generation.
The subject's curriculum, structure, originality and quality requirements remain
binding. Run the route as one continuous job: keep working in the same response
from preflight to the delivered PDFs, and do not end it to report the preflight,
the body font, a checkpoint, a finished batch or what remains. A provider limit
can still end a response early; the saved run then resumes when the user replies
繼續.

Formal question and solution PDFs come only from these helpers composing onto
the original fixed template bytes, and only after `check_hosted_run.py` passes.
Never let LaTeX, HTML, Word or drawing tools recreate a cover, running
header/footer, answer-marking example or formula page; a "mock" disclaimer does
not make an imitation acceptable. When a helper or template is unavailable,
stop before drafting or delivery, keep saved work and name the missing part to
the user. State the final check result when delivering the two PDFs.

## Load once and begin the paper

When a native Skill already exposes its scripts and references, use
`python scripts/read_web_knowledge.py --source-dir NATIVE_SKILL_DIR --subject
SUBJECT --output-dir VERSIONED_REFS --reading-plan`. Its package manifest is
checked before the selected runtime files are copied. ZIP filenames are portable
ASCII names; `runtime_path` in the manifest restores original canonical paths in
VERSIONED_REFS with unchanged file bytes. Run subsequent helpers from
VERSIONED_REFS, not the installed ZIP directory. This one local copy is scoped to
the selected subject; it requires no aggregate Markdown, reinstallation or
repository download. Reuse that reference directory on continuation. Its result
lists this subject's two `layout_previews` (placeholder layout only). Do not ask
native-Skill users to attach previews; the renderer already applies their
conventions, so open one only for a specific layout question. Its
`reading/preflight.md` view embeds this same document: having read it here,
skip those chunks and run the preflight.

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
repeating already recorded work on unchanged inputs. It also does not require
rereading references already read in this conversation: open a phase's reading
only the first time you enter it. If files have expired,
recover the actual saved artifacts or report the missing files precisely.

Before drafting, confirm file creation, Python/PDF operations and readable image
inspection in the actual runtime. The preflight starts the run clock
(`generation-timing.json` in the run directory, phase `reference_preflight`);
later phases are recorded as described under the checkpoint command below. Do
not start a separate logger or reconstruct times later. Run:

```text
python scripts/prepare_hosted_run.py --subject SUBJECT --run-dir run --paper-id PAPER_ID [--font FONT] [--resource-pdf UPLOADED_RESOURCE_PDF]
```

Pass `--font` for an installed or user-supplied Traditional Chinese serif font
(for example Noto Serif CJK TC). Without one, or when it lacks a glyph of the
cover and header fields, the helper uses PyMuPDF's built-in CJK font (Droid Sans
Fallback, sans-serif) and records `body_font`; `proof` and `build` default to it.
Do not stop to ask for a font or try to install system packages. Keep going, and
say in the delivery message that the body is sans-serif and that a serif font
file can be supplied next time.

The native Skill bundles every subject's verified template components, and the
helper uses them without network access; omit `--resource-pdf` there. From the
knowledge file, pass the uploaded resource PDF; without it the helper attempts
bounded retrieval. If acquisition fails, follow its `next_action`: stop and ask
for `taiwan-exam-template-resources.pdf`, never a redrawn substitute.
The resource PDF's embedded original attachments are the templates;
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

Work one batch at a time: draft two to four items, draw only their figures, save
them, then proof and review them before drafting the next batch. Only `exam.json`
carries the paper between phases and turns. Two hosted runs spent every command
of their turn designing, verifying and illustrating a whole paper that existed
only in the reply, and finished with nothing saved; the batch loop below turns
the same work into finished items. Save editable content, diagrams, candidate
decisions and review progress every two to four items, before starting more
figures or a long tool call:

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
their actual display/answer label. The helper refuses a batch whose printed
fields would print wrongly and lists every such issue at once: LaTeX commands
(`\frac`, `\cdot`, ...), `$` math delimiters (a currency `$` before a digit is
allowed), unbalanced `<sup>`/`<sub>`/`<i>`/`<b>`, `{{asset:NAME}}` tokens missing
from `inline_assets`, asset files that are absent or differ from their
sha256, an inline image taller than one 18 pt line, and a raster figure below
twice its printed width (vector art prints at three times its size, so save
figures as SVG or a one-page PDF). Fix them in the batch and save again; otherwise they surface only after
rendering and page review. A saved result also lists `design_fields_pending`:
the final check's difficulty-design messages for the items just saved. Complete
them with `--replace` while solving and reviewing that batch, before writing the
gate reviews; they are not printed, so page and crop reviews stay valid. Check scope, answerability, shortest routes, distractors and
score sums early. After each saved batch, project both body specs and render
only that batch's items and solutions:

```text
python scripts/run_hosted_workflow.py specs --state run/run-state.json --question-output run/questions-blocks.json --solution-output run/solutions-blocks.json --hints run/layout-hints.json
python scripts/run_hosted_workflow.py proof --state run/run-state.json --question-spec run/questions-blocks.json --solution-spec run/solutions-blocks.json --items q1,q2,q3 --output run/proof-01
```

Where the runtime allows, chain `append_items.py`, `specs` and `proof` with `&&`
in one tool call, so each batch costs one command before its crops are opened.

`specs` copies printed text only from exam.json and applies the same saved-item
conventions as the maintained official-form renderers, for every subject:
section titles/instructions; prompts; options printed as `(A)`/`(1)`;
`option_layout` columns; a fill rail at `{{answer}}` or the first `______`, sized
by `answer_format`; `visual_asset` printed once per shared file, `visual_layout:
side-right`, `inline_assets`; one `第 X 至 Y 題為題組` label per group of different
numbers; `group_stimulus` and `group_stimulus_page_splits`; English `[[n]]` gaps,
`*italic*`, `stimulus_layout`, a lettered option bank printed once and cloze
option rows aligned after their passage; Natural Science `（應選n項）` generated
from `required_selection_count` (never typed in the prompt); Social Studies
`response_format_table`; `continuation_pages`; answer reasoning/explanations.
An item with `suppress_question_display` is `covers`ed by the block that prints
it (its group's material or the same-number item), so shared text is never faked
as extra rows. Score wording already in a prompt (including a whole question's
total across subparts) is not printed twice. Unicode sub/superscripts such as
H₂O, SO₄²⁻ or x⁴ become real sub/superscripts, because most CJK fonts lack those
glyphs. `specs` applies the same printed-text checks with the item named: use
real symbols or a verified formula asset. Long material, prompts and solutions continue on the next page at
paragraph or step boundaries instead of leaving a large blank bottom. `--hints`
is optional; it holds layout choices and explicit blocks for structures the item
fields cannot express. Never edit a generated spec: stale or hand-edited
generated specs are refused. Open every proof crop at readable scale while the
item is fresh. The result gives absolute image paths, each batch's `record_as`
keys and an `observations_template`; fill a copy with what you actually saw and
record it in one `record-review --proof PROOF_DIR` call. Fix
superscripts, fractions, radicals and figure/text arrangement before authoring
more items. A final crop may later reuse such an actual review only under the
unchanged-item rule below; final pages always need their own review.
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

After all content, answers and difficulty reviews are complete, freeze the
saved exam with `run_hosted_workflow.py lock-content --state <latest-state>`.
Early batch proofs still happen during authoring. During full pagination,
change layout hints and regenerate specs; a necessary content correction needs
renewed dependent reviews and `lock-content --reason "actual correction"`.
The lock preserves its previous version and never supplies editorial approval.
The build's `page-plan.json` reports actual measured heights, kept blocks, page
item IDs and remaining bottom space. Inspect these and `reflow_before_review`
before opening a long review queue. Rendering has a separate-process,
20-second per-operation stall guard; it reports the block to repair rather
than retrying exact-fit indefinitely. No guard bypasses a quality check.

Read `reading/layout.md`. Use `hosted_body_templates.py` components and the
selected subject's question/solution layout pair. Generate the current run's
body specifications from the saved exam with `specs` (layout hints for special
structures); never retype item text or rewrite a PDF engine for ordinary
blocks. Preserve original fixed PDF layers as immutable backgrounds, including
the subject-specific formula page for Math A/B. Body flow must reserve complete
answer rails, equations, figures and shared stimuli before painting later items.
A figure wider than its text column prints at the column width and is listed in
the layout's `scaled_assets`. When a last page would hold only a line or two,
the renderer first retries with closer block spacing (`gap_scale`); font size
and line height never change. Composition embeds one copy of the body font;
`finalize` then drops the glyphs no page draws from the delivered copies.

After content review and both body specifications exist, the maintained pipeline
renders both bodies, composes both fixed-template PDFs and prepares their actual
page/item review together:

```text
python scripts/run_hosted_workflow.py build --state run/run-state.json --question-spec run/questions-blocks.json --solution-spec run/solutions-blocks.json --year 116 --output run/build-v1
```

The result's `review_queue` lists exactly the page and crop images still pending
in the returned review state, as absolute paths. Open each at readable scale;
thumbnails/contact sheets only navigate. One `review_batches` entry is one
viewing call of up to six images: a build groups a pending page with its pending
crops, and a proof keeps each item's question and solution crops together. Each
image carries its `record_as` key. `observations_template` is a skeleton of
exactly those keys, all `pending`: fill a copy with your actual findings. When the runtime
shows several separate images at native resolution in one call, open one batch
per call rather than one image per call; never stitch or downscale images to
save calls. Inspect formula geometry, labels, response rails,
collisions, whole-page density, missing material, answer separation and grayscale
readability, then record the actual findings in one call:

```text
python scripts/run_hosted_workflow.py record-review --state run/build-v1-review-run-state.json --observations run/review-notes-v1.json
```

The notes map `question`/`solution` to `pages` (page number) and `items` (item
id, or `id#n` for a continuation part), each with `status` (pass, fail or
pending) and concrete `observations`. The helper checks that the reviewed images
are unchanged, writes the findings, refreshes registered hashes and lists what
remains. It never supplies a status or an observation. A machine report cannot
replace this visual work. `needs_full_resolution_review` and its reasons identify
pages needing priority magnification; those rasters are prepared at higher
resolution. Every page and required crop still needs review. A false flag does
not prove visual quality; zoom any uncertain page regardless of the heuristic.

For each `large-bottom-void-review` the build attaches `density_evidence`: the
page role and the comparable same-role embedded official measurements.
`reflow_before_review` lists pages that no comparable measurement can justify;
reflow those before spending review time on them. For a genuinely comparable
page, record `{"decision": "justified", "reason": "...", "embedded_reference": N}`
under that page's `issue_dispositions`; the helper copies the measurement's
identity and the final checker remeasures both. Prose cannot waive a collision
or an unjustified terminal void.

Repair the saved item (`append_items.py --replace --state LATEST_REVIEW_STATE`)
or the layout hints, rerun `specs` with that state, and build to a new output
path from it. Reflow pages that `reflow_before_review` names in the same repair,
so one rebuild resolves every known defect. A crop keeps
an actual earlier review, from a proof or an earlier build of this paper, only when
the item's authored record is unchanged (review metadata excluded; a shared
stimulus binds its whole group), fonts and painting helpers are unchanged, and the
new crop is pixel-identical or prints the same glyphs, rules and images within
0.02 pt, the float placement noise left by reflow. A recorded non-pass finding
on an equivalent rendering blocks reuse. A page keeps its review only with
identical pixels, mechanical issues and item content. Everything else starts
pending. Say that retained reviews were retained, not freshly inspected; changed
content still requires its dependent editorial review.

Use `run_hosted_workflow.py checkpoint --run-dir run --phase authoring` after
preflight to create/register the run state. `append_items.py` already checkpoints
each batch; do not duplicate that call just to register the same hash. For a repair,
supply `--state RETURNED_REVIEW_STATE`
so the latest surviving reviews are retained. `--review-bundle FILE` can fan out
one JSON object of actual named gate reports without generating observations.
Measure solving and difficulty review when those activities actually happen:
switch with `checkpoint --phase solving` and `checkpoint --phase difficulty_qa`
(add `--state` after a build). `build` records `render_repair` and `visual_qa`,
`proof` records `visual_qa`, and `finalize` closes the clock; the final check
needs all six phases.

After real reviews are complete, finalize once; this closes the active clock:

```text
python scripts/run_hosted_workflow.py finalize --state RETURNED_REVIEW_STATE --output run/final-check.json
```

This refreshes artifact digests and runs `check_hosted_run.py`; it does not author
passing reviews. Fix the reported failure, not unrelated phases. Delivery needs
both separate downloadable final PDFs and current complete evidence. On
`evidence-complete` the report's `delivery` lists the files to hand over: copies
of the checked booklets without unused font data, kept only when every page
renders the same pixels and text (typically about 1 MB instead of 20–40 MB). Disclose
the actual review mode. `evidence-complete` means recorded evidence is complete
and current, not official certification or empirical psychometric validation.

## Time and continuation

Before a response ends, close active work with
`run_hosted_workflow.py clock --state <latest-state> --operation pause`.
On continuation use `--operation resume`; during long reading, solving or
inspection use `--operation touch` at least every five minutes. These are
explicit agent steps, not automatic platform callbacks. Abrupt interruptions
are detected on the next clock call: time beyond the last activity plus ten
minutes is labelled **estimated waiting**. It may include unrecorded thought.
Keep total wall time, estimated activity, recorded tool duration and explicit/
estimated waits separate. Legacy logs cannot supply exact active time.
Always continue repairs from the latest returned review state, so unchanged
hash-bound page/item reviews survive; inspect the pending `review_batches`.

Time phases by primary activity: `reference_preflight`, `authoring`, `solving`,
`difficulty_qa`, `render_repair`, `visual_qa`. Batch independent calculations and
file operations inside one tool invocation where supported; changing phase must
not require a user reply. Never end the response to give a progress update; where
the platform shows interim notes without ending the response, keep each to a line
and never display a whole manifest or internal record. The only messages that end
the response before delivery name a blocker the user must resolve. Save before
long work and after each reviewed batch.
Reserve final review time early. If a provider interrupts, continue the same
paper from saved work and unresolved checks; do not regenerate successful phases.
The 20-minute benchmark is measured, not an acceptance deadline. Finish required
QA even if the target is missed; never fake completion or lower difficulty to
fit a clock. A provider limit cannot be removed by this Skill, and surviving
temporary files must be verified on continuation.
