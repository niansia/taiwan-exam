# Hosted PDF production: executable transport, composition and honest review

Use with `web-platform-use.md` for every hosted complete paper. This is the same
Skill's layout implementation, not a generic question generator or weaker gate.
Follow hosted-quality-gates.md for measured item flow, final item crops and
non-waivable collisions before any final quality claim.

## Prove the rendering route before drafting

1. Use read_web_knowledge.py with --subject and --output-dir to extract the
   requested subject's references, maps and embedded helpers into a versioned
   directory, preserving canonical scripts/ and exam_packs/ paths. This includes
   fetch_hosted_template_assets, compose_hosted_pdf, inspect_hosted_pdf,
   check_hosted_run and its hosted_item_layout/hosted_run_timing/hosted_blind_review
   imports, plus validate_math_context.py. Do not flatten the files or omit
   official-current-web-sources.json, which the measured density gate needs.
   Read selected guidance, not a dump of
   every extracted file. PyMuPDF supplies PDF operations. Do not claim its
   absence without trying the installed PDF library; if dependency installation
   is unavailable, name that actual capability gap.
2. Fetch the subject's three/four production components with the existing bounded
   helper. Verify bytes in the SAME runtime that will compose the paper, not just
   in a web-search or connector tool. A URL, preview, text extract or base64
   response in another tool is not proof the runtime possesses the file.
3. If runtime networking is unavailable, use an already uploaded
   `taiwan-exam-template-resources.pdf`. It contains the 30 original PDFs as PDF
   attachments, no executable content. It is optional data, not a Skill installer.
   Read attachments with the PDF library; never OCR the visible index. Use the
   knowledge file's per-asset size and SHA-256 as the trust anchor, not names or
   claims inside the uploaded carrier. Extract ONLY this subject's production
   files. A stripped attachment or wrong hash fails explicitly. Do not retry the
   Internet after an explicitly supplied carrier fails validation.
4. If no usable carrier was uploaded and both bounded network routes fail, ask
   once for this one file with the map's `offline_resource.download_page` link.
   Do this before writing a full exam. Do not ask users to operate GitHub, copy
   base64, fetch 30 files, install a ZIP, or repeatedly say “continue”. An uploaded
   resource solves network isolation only when code/file tools can access its
   attachments; it cannot create missing platform capabilities or persist itself
   across chats. Native Skill installation still stores URLs, not PDF binaries.
5. Make a small labelled layout-only smoke proof using the fixed cover and one
   transparent body page. Check field fitting, real math glyphs, composition,
   rasterization and viewing. Resume from cached evidence in the same runtime;
   do not repeat setup for each phase or continuation.

Offline command (agent runs it; no coding required of the user):

```text
python scripts/fetch_hosted_template_assets.py --subject 數學A --map exam_packs/學測/templates/115/hosted-web-template-assets.json --resource-pdf <uploaded-resource.pdf> --output-dir <versioned-cache>
```

Neither `github-pages.zip` nor the full repository is part of this route.
Downloading resources at generation time does not reopen the suspended software
ZIP distribution. Do not embed scripts or retired code in the resource PDF.

## Compose immutable assets, not editable covers

`overlay_geometry_pt` in the template map supplies measured field gaps and the
body box. Prepare transparent A4 **body-only** pages at those coordinates, using
the subject profile's font roles, sizes, spacing, numbering, option layout and
answer fields. Do not draw cover wording, headers, footers, signature bars,
background rectangles or reference formulas into those overlays. In particular
a white full-page background can erase a perfectly valid template.

Use the embedded compositor for the maintained PDF-overlay route:

```text
python scripts/compose_hosted_pdf.py --subject 數學A --body <body-only.pdf> --asset-dir <versioned-cache/math-a> --year 116 --title 學科能力測驗模擬試題 --running-name 學測 --font <available-TC-serif-or-Kai-font> --output <question-proof.pdf> --report <composition-proof.json>
```

For the explanation paper use `--kind answers` and explanation body pages; it
uses the same odd/even furniture but does not prepend student instructions or a
student formula page. Keep its answer table, item reasoning and rubrics in the
body, not in dynamic header fields. Font files are supplied by the runtime,
not redistributed by the carrier. Glyph-complete does not imply an acceptable
font role; evaluate the actual body and field rasters.
Test mixed Latin/Chinese dynamic fields too: some fonts are incorrectly treated
as monospaced half-width by a PDF library. The compositor positions field glyphs
individually using measured advances; preserve this behavior. Correct glyph
availability and a hash-matched background alone do not detect overlapping text
inside an allowed dynamic-field region.

The compositor verifies original hashes, rejects out-of-box/opaque overlays,
isolates existing PDF transformations before adding fields, and compares locked
pixels. It uses the formula's unchanged vector body with the proper final-page
parity. It counts actual inner pages, including the mathematics formula page and
excluding the cover. It does NOT force the paper to seven inner pages, repaginate
thin text, repair prose, or certify content. Its result is `layout-proof-only`.
Use a shorter running title if it does not fit; never shrink or shift fixed text.

## Review actual failures, not declarations

Run `inspect_hosted_pdf.py <pdf> --rasters <dir> --report <json> --math` on BOTH
saved mathematics PDFs (omit `--math` elsewhere). It binds each raster to final
PDF bytes and reports raw-math syntax, page overflow, text crossing table grid
rules, font inventory and large
bottom voids. It measures visible ink, not white page-size object bounds. It
returns `mechanical-review-only`, never a formal pass; nonzero exit status marks
hard mechanical failures. Zero exit status still requires all flagged and
manual checks. Any later
PDF change invalidates the page review. The full local release gate remains
mandatory in a complete checkout; these helpers are not its replacement.

Every page must then be viewed at readable scale, against its role-matched
reference and the authored source. Record actual observations, failed locations,
fixes and rechecks. The following require specific checks in BOTH question and
answer files, not copied `pass` flags:

- **Math semantics:** render powers, indices, bars, vectors, fractions, radicals
  and matrices as mathematics, not literal `^`, `_`, `[[...]]` or caret-T. Compare
  intended symbols (especially ≤, ≥, ±, ∓, overbars and subscripts) with the
  printed equation. A missing symbol can disappear without a replacement glyph;
  clean extracted text or successful font embedding cannot prove correctness.
- **Answer table:** use concise keys in a width-constrained, wrapping table.
  Put multi-part long answers and derivations below it. Check cell boundaries,
  row numbers and adjacent columns, not merely A4 page boundaries. Increasing
  table width off-page or shrinking text to hide overflow fails.
  The inspector flags glyphs crossing vertical rules of multi-row grids; it
  cannot prove borderless tables, every cell, or all wrapping correct.
- **Fill-in rails:** reproduce the subject's digit/circle/row-index/fraction
  answer-field conventions. Ordinary underlines plus a prose “answer format”
  note are not the measured mathematics fill-in format.
- **Density:** measure substantial occupied body area and terminal voids, then
  compare same-role official pages. A mechanical void warning is a review flag,
  not a universal density threshold: cover, formula and justified final pages
  differ. Move complete blocks or repair underlength material; do not insert
  answer lines, decorative tables, oversized figures, giant spacing or extra
  page breaks to fill or inflate the paper. Page count is not the target.
- **Diagrams:** compare labels and ticks at print scale; no x/y labels touching
  tick values, missing arrowheads, vanished signs or inaccessible grayscale
  encodings. Record what inference actually requires each visual. A matrix or
  point table already specified completely in prose plus a redundant drawing
  does not automatically become an answer-bearing visual.

## Content is a separate acceptance, including Mathematics A

For EVERY item, solve the shortest route and apply `math-difficulty-design.md`
or the corresponding subject gate. In Math A, the first fill-in slots are not
permission for a run of one-step arc-length substitution, exposed determinant
area or routine linear-system drills. Do not inflate difficulty by writing a
long solution to an easy question. Statistics quotas, five curriculum labels,
answer balance and correct totals alone do not establish depth or scope.

Apply two removal tests: (1) remove the visual but retain all printed prose;
does the evidence needed to answer change? (2) remove the source name and replace
its isolated numbers; does any real-world relationship or model choice survive?
If not, do not count it toward the visual/literacy requirement. For a genuine
data stimulus, source values must constrain a model, interpretation, comparison,
assumption or decision; choosing two bike counts as constants in a log equation
is ornamental sourcing. Multiple items from one dataset count as one source
family; ensure whole-paper source/mechanism balance without inventing a new quota.

Originality reviews compare solution structure as well as vocabulary. Changing
an official reward-draw story's objects and probabilities alone is not evidence
of an independently new mechanism. Keep an item-specific adjudication; do not
declare plagiarism or global novelty merely from a similarity score.

## Delivery is explicit, never an unsolicited downgrade

The request for two complete formal PDFs is NOT permission to generate a
`generic-layout draft`. If exact assets or necessary inspection are unavailable,
request the concrete missing resource/capability once. Only explicit user consent
authorizes a draft. A footer disclaimer, honest disclosure, or “all other gates
passed” paragraph does not supply that consent. Do not attach draft PDFs under
the requested complete-paper filenames while asking for approval afterwards.

Use `pass`, `fail`, `not_checked` and `not_applicable` accurately, with evidence
paths/hashes and per-page findings. No claim of “only template missing” unless
each other gate was actually performed with no unresolved result. Passing unit
tests, a smoke proof, or these three helpers is not end-to-end hosted exam
acceptance, nor proof that every platform/model will follow the Skill.

Before a formal delivery, run `scripts/check_hosted_run.py run-state.json` under
[hosted-run-evidence.md](hosted-run-evidence.md). The saved PDF inspector's exit
code 0 means no mechanical hard failure was found; `review_flag_pages` and each
page's `issues` still require evidence-bound adjudication. Do not summarize this
as "all layout checks passed" while warnings, missing difficulty reviews or
unviewed pages remain. Repairs require new PDF hashes, rasters and page reviews.
