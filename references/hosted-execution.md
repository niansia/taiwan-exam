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
VERSIONED_REFS with unchanged file bytes. The references, schemas, layout
templates and exam-pack data travel inside two `resources/bundles/*.json`
members (the uploader allows at most 200 files); the reader expands them and
verifies every restored file against its own manifest digest, so VERSIONED_REFS
holds ordinary files and no helper or reading step ever opens a bundle. Run subsequent helpers from
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

Every PDF helper needs PyMuPDF. If the runtime lacks it, or a helper fails with
`ModuleNotFoundError: pymupdf`, run `python scripts/ensure_pymupdf.py` (the
preflight runs the same step itself). It first uses any wheel already on disk,
then downloads the pinned PyMuPDF wheel from this project's GitHub Release
(SHA-256 verified, one bounded HTTPS request, no proxy or policy change) and
installs it with `pip --no-index`. The equivalent one-line command, when pip can
reach github.com, is `python -m pip install "https://github.com/niansia/taiwan-exam/releases/download/wheels-pymupdf-1.26.0/pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl"`.
Only when the helper reports `missing-wheel`, which
means the runtime blocks that download too, ask the user once, in these words:
download the wheel
`pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` from the README troubleshooting entry
（「AI 說執行環境缺少 PyMuPDF」）and upload it to this chat. Then run
`python scripts/ensure_pymupdf.py --wheel UPLOADED_FILE` and continue the same
paper from the saved state. Do not ask for an allow-list, an internal index or
admin action, and never compose pages with another PDF library. Only
`install-failed` after the upload is a blocker: stop, keep saved work and report
its JSON.

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

The preflight result lists `authoring_requirements`: every field a saved item
must already carry (curriculum codes, difficulty design, originality record,
innovation audit, source binding and grounding for any printed material,
current-context records) and the subject's form rules. Read them before the
first batch: a 3-hour hosted run learned each one from a later whole-paper gate
and rebuilt the paper every time (52 minutes for source binding alone). Every
message a batch save returns under `subject_gate_pending`, `design_fields_pending`
or `absolute_claim_options` is a final-check failure; when any is present the
save reports `items-saved-fix-before-next-batch`, and the next batch waits until
`--replace` clears it. Items of one shared stimulus may set
`item_spec.inherits_audit_from` to the group's first item: the saver copies its
originality record, innovation audit, source binding and grounding; difficulty
design, curriculum codes and the answer stay per item. A stem that quotes 「…」
from 甲／乙／丙／上文 must quote the material as printed; the saver rejects a
quotation the material does not contain.

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

Work one batch at a time: draft two to four items (up to six when every item is
text-only, since those need no proof), draw only their figures, save
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

Proof what can print wrongly, not everything. The saved-batch result lists
`proof_recommended` (the first batch, and any item with a figure, inline formula
image, sub/superscript or markup, answer blank or gap, response table, fill rail,
or a long shared stimulus) with the reason, and `proof_optional` (plain-text
items, which print through the same paragraph path as every earlier proof).
Proof the recommended items now. Text-only items need no proof and no final
crop of their own: the final build marks their crops `review_via: page`, and
they pass when the page image they sit on receives a passed review; the
checker recomputes the triage from the exam and verifies the page. Every page
is still opened, so every item is still read. A measured 自然 paper spent
90 minutes on 50 batch proofs whose text-only crops found no defect.

The same result names other things that are cheapest to fix while the item is
fresh: `absolute_claim_options` (options containing 必定／只／無關／皆 and
similar; ask once whether any condition makes the option true), `layout_risks`
(a figure that will print taller than 40% of the body and force a page break;
lower `width_percent`, redraw wider, or place it side-right now), and
`plan_hint` once about twenty items are saved.

Subparts print in `subpart_id` order, so ids that share one printed number must
start with their printed ordinal (`1-plot`, `2-calculation`, or `a`, `b`); a
bare name such as `plot`/`calculation` is refused because alphabetical order
would print (2) before (1). `emit_item_skeleton.py` already prefixes the
ordinal for profile slot names.

Draw each figure with its own small script and run
`python scripts/normalize_figure_asset.py FIG.svg` (or `.pdf`) before recording
its sha256: it strips the export timestamp, random document ID and salted
element ids, so an unchanged figure redrawn later keeps its hash and its item,
reviews and content lock stay valid. Regenerating a whole batch of figures with
one script changes every hash and costs a `--replace`, re-lock and rebuild for
figures that did not change.

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
before opening a long review queue. Do not pay for a full build to learn only
the pagination: `run_hosted_workflow.py plan` runs the same renderer on the same
specs in seconds, writes `page-plan.json` with each page's `bottom_void_ratio`
and lists `bottom_void_attention` pages, but composes no booklet, rasterizes
nothing and creates no review state. Run it once about twenty items in (the
batch result says when) to learn the paper's rhythm and catch tall figures or
over-long groups early, and again after each layout-hint repair; run one full
build only when the plan is acceptable. A measured 自然 run spent 16 of 17
builds (about 25 minutes) on pagination that a plan would have shown.

### Mandatory order and iteration budgets

Three measured runs of 2026-09-22 (國綜 33 checkpoints with 9 plans and 6 proof
rounds; 社會 2 h 04 with 20 proofs, 7 plans and 3 builds; 自然 2 h 26 with 24
plans, 11 builds and 18 proofs) lost most of their time re-reading unchanged
content. The order below is not advice; the tools enforce the parts they can.

1. **Author** in saved batches; read each batch's gate messages while the items
   are fresh. Fix every structural message before the next batch, never at the end.
   Once the figures of a batch exist, run `check-figures --state <state>`: it opens
   every referenced figure and reports missing or renamed files, HTML saved under
   an image name, unreadable artwork, printed-size defects, colour-only pixels,
   glyphs CJK-only fonts lack and labels sitting on strokes, before any PDF exists.
   A measured 自然 run paid one full redraw–plan–build–review round per such defect.
2. **Solve and review content** (`checkpoint --phase solving`, `difficulty_qa`).
   Fix stale option references here: after any option reorder, rewrite the
   explanation; the gate rejects an explanation citing a label the item no longer
   prints. Every `checkpoint` result now carries `evidence_ready` and
   `evidence_attention`: which gate reports are missing, stale (with the items
   changed since that review) or structurally incomplete, in the final checker's
   own terms. Read it; `finalize` must never be the first place a stale report is
   discovered.
3. **Lock** (`lock-content`). `build` refuses to run without `content-lock.json`.
   A booklet built before the lock is discarded the moment an item changes, and
   every one of its page reviews with it. If content must change after reviews
   exist, run `refresh-evidence --state <state>`: it re-registers the mechanical
   records and writes `<gate>.draft.json` for every stale report, keeping the rows
   of items whose authored record is unchanged, leaving changed or new items and
   the paper-level status `pending`, and regenerating the difficulty blind packet.
   Complete the pending rows from an actual review, save the file as `<gate>.json`,
   checkpoint, then re-lock with `--reason`. The checker never reads a draft and no
   draft is a pass.
4. **Plan** at most three times (`plan`, then `plan --compare <previous plan dir>`
   which reports each page's `bottom_void_delta` and the page-count change).
   If the third plan is still not acceptable, stop adjusting hints by eye: shrink
   the figure or split the block once, based on the measured heights.
5. **Build** at most twice. The second build exists to fix defects the first
   review found, not to try another layout hint.
6. **Review once.** Every result carries `iteration_budget` (`count`, `budget`,
   `over_budget`). Exceeding a budget is not blocked, but the note names the
   cause to fix once; report the overrun in the delivery notes.

Proof rounds follow the same rule: proof `proof_recommended` items once after
they are written, then trust the retained reviews. Text-only items are reviewed on
their page (`review_via: page`), not as crops. A page keeps its review when its
**body** pixels and item content are unchanged even if the running header's page
count changed (`共 22 頁` → `共 21 頁`), so a shorter final booklet does not
re-open every page.

### Renderer rules worth knowing before the first plan

- Options print as their own full-width block under the numbered stem, never
  inside the stem's table cell: a hosted run's MuPDF shrank such a nested
  table to the stem's width and wrapped every 國綜 option at 40% of the page.
  The column count follows the longest option (國綜: four options of at most 16
  characters print two abreast, anything longer or a five-option item one per
  line). The inspector's `narrow-wrap-column` hard failure and the final
  checker catch any body whose wrapped lines leave a quarter of the width
  unused with nothing beside them, however the body was produced.
- Mathematics digits, Latin letters and √ print in the Latin face automatically;
  `x_{i+1}` or `a^{2}` in saved text is refused at save time (write `<sub>`/`<sup>`),
  a mathematics choice item is refused without its five options, a figure taller
  than 60% of the body is refused until resized, and a key that differs from the
  planned position in `paper-plan.json` is listed as `answer_position_drift`.
- Typography is fixed for all seven subjects (國綜、國寫、英文、數學A、數學B、社會、自然), as in the official booklets: CJK in the
  pinned Traditional Chinese serif (明體-style Noto Serif TC, downloaded by the
  preflight; a supplied font is used only when that download fails, the built-in
  sans-serif is the last resort) and digits, Latin letters and √ in the Times-like
  Latin face. Authors never choose fonts.
- Leading is measured per subject: 國綜, 國寫 and 英文 print 11 pt on a 1.5 line
  (16–17 pt option pitch, 19–20 pt between items, as the official booklets),
  社會 and 自然 on 1.6, mathematics on 1.65 for scripts. A 國綜 paper that runs
  far past the official 12 pages is a layout defect, not extra content.
- Every composed booklet carries the creator stamp `taiwan-exam-generator/
  compose_hosted_pdf`; `check_hosted_run.py` refuses a PDF without it, so a
  body typeset by any other tool cannot be delivered.
- The preflight downloads a Traditional Chinese serif body font (Noto Serif TC
  Regular, OFL 1.1, pinned digest) from this project's GitHub Release when the
  runtime has none, and only then falls back to the built-in sans-serif; the
  font record says which happened.
- A task label longer than three characters (`中譯英`, `英文作文`, `第一段`)
  leads the text; only plain numbers and `(1)`-style subparts sit in the number
  column. Give each subpart its own `number_display`/`answer_label`; `specs`
  refuses a spec that would print the same label twice.
- MuPDF prints U+2060, U+FEFF, U+200B and U+00AD as visible gaps and U+3000
  (full-width space) inside a number column breaks the line. `text_issues`
  rejects them at authoring time; do not paste text from a PDF or a web page
  without normalising it.
- Figures: one asset per figure, referenced by content hash; a redrawn figure
  changes the hash and re-opens only its own crop. Figures wider than the text
  column are scaled to the column and listed in `scaled_assets`, so plan the
  figure at column width from the start.

### Environment traps the hosted runtimes have shown

- Image downloads are usually blocked or silently return an HTML error page.
  Use bundled assets or draw the figure from verified data; never keep a
  0-byte or text/html "image".
- The runtime may lose `tmp/` between turns; `finalize` recomputes digests
  from disk, so a missing artifact fails the final check honestly. Rebuild from
  the saved state instead of hand-editing the state file.
- A gate report older than the exam hash it names is stale; the checker rejects
  it. `checkpoint` reports it under `evidence_attention` and `refresh-evidence`
  drafts the replacement; never edit the hash inside an existing report.
- Fifty scripts referenced by the references were missing from ZIPs before
  2026.09.22.2; if a documented command is absent in an older ZIP, report it as
  a packaging defect and continue with the documented hosted-equivalent check.

```text
python scripts/run_hosted_workflow.py plan --state run/run-state.json --question-spec run/questions-blocks.json --solution-spec run/solutions-blocks.json --output run/plan-01
``` Rendering has a separate-process,
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

Page density has one fixed rule, shared by `plan`, the inspector and the final
checker (`hosted_density.py`): a body page may leave at most 32% of the
printable body blank (英文 42%, where official section breaks reach 40%), the
last body page at most 60%; the cover and the mathematics formula page are
fixed layers and are never measured. `plan` lists pages over their limit under
`bottom_void_attention` with the limit that applies, the inspector flags them
as `large-bottom-void-review`, and `finalize` fails them; no disposition,
reference PDF or prose waives a page over the limit. `density_evidence` still
attaches the comparable embedded official measurements, as reference only.
`reflow_before_review` lists the pages to fix before spending review time. The
renderer paginates for these limits: after the greedy pass it re-flows the same
content evenly across the same number of pages when any page would exceed its
limit, so an over-limit page in a plan means a figure or block is too tall for
its position, not a threshold to argue about.

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
named `{考試}_{科目}_{paper_id}_題本.pdf` and
`{考試}_{科目}_{paper_id}_詳解.pdf` under `delivery/`. Use the returned paths
as the actual downloadable attachments, preserving the same paper ID on resume.
All subjects follow the naming rule in `SKILL.md`; build-folder English filenames
remain internal evidence paths. If the user explicitly requests other names,
copy the finalized bytes to those names and link those files.
These are copies
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
