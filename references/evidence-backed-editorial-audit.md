# Evidence-backed originality, literacy and student-facing notes

Read for a repeat audit, a complaint about recycled content or weak literacy, or
before releasing a current-source paper. This supplements the originality
firewall; it does not supply question seeds.

## Audit coverage and actual decisions

Run `scripts/audit_corpus_overlap.py EXAM_JSON... --output REPORT_JSON` in the
analysis pass. It inventories every supplied `drive-download*` directory and
organized Exam Pack, hashes duplicate files, searches every PDF text page without
a year/question cutoff, and compares surviving `output/**/*exam.json` history.
It separates item text from shared stimuli and flags disjoint groups reusing the
same material. It does not perform OCR or recognize graph topology.

Report physical files, unique PDFs, extracted-text pages, low-text pages, failed
files, non-PDF inputs and generated-history coverage. A cover can legitimately
have little text; inspect low-text pages before calling them scans. Reconcile
image-only inputs with trusted OCR or visual review. Existing semantic metadata
can assist review but cannot substitute for the underlying item. If any remain
unreviewed, the whole-corpus result is **incomplete**, not “no duplication”.

The older `audit_item_originality.py` is only a targeted 111–115/registered-mock
screen. Neither script can approve originality. Empty neighbors, automatic
`pass` labels, candidate names ending `-a/-b/-c`, and the writer's declarations
are not evidence of independent alternatives or review.

Review each flagged neighbor using actual givens, unknown, decisive constraints,
intermediate results, wrong paths and visual function. Also inspect low-lexical
neighbors by mathematical mechanism or rhetorical task. Record exact file/hash,
page/item, compared features, decision and reason. Distinguish:

- same syllabus concept or standard theorem: not itself a duplicate;
- same source but genuinely distinct, integrated subparts in one group: expected;
- independent groups repeating the same evidence or inference: redundancy;
- number/name/output swaps preserving the substantive solution: structural reuse;
- a maintained revision of the same paper: version history, not a second source.

Do not count an item with five subparts as five independent source discoveries.
Do not change only a failed item's story. Replace its task mechanism when reuse
is confirmed; preserve unrelated PDFs unless revision is in the user's scope.

## Literacy and freshness are separate axes

Use a task-level editorial ledger, not one label copied across a whole group:

- **basic / direct retrieval**: legitimate when the slot allows it, but not counted
  as integrated literacy merely because the stem names a current event;
- **evidence application**: a specific sentence, table cell or visual feature is
  needed and must be linked to a curriculum concept;
- **integration / evaluation**: reconcile constraints or sources, choose a model,
  infer a limitation, compare explanations or justify a bounded decision.

For each claimed literacy item record the exact evidence span/location, the
inference it enables, the curriculum bridge and a concrete counterfactual: what
becomes undecidable or changes if that evidence relation is removed? Review the
actual student text. “Uses material” and repeated generic operation lists fail.
Check the wrong options too: if three are absurd without reading the evidence,
the item does not deliver its intended evidential demand.

Anonymizing a proper noun is allowed: real information can remain useful after a
name is removed. It is the **source-derived relationship**, not the famous name,
that must affect the reasoning. A policy default and its exception can be
essential without naming the agency. An agency name prefixed to arbitrary mean
and variance values is not an evidence relationship.

Keep context-free mathematics, authentic everyday sources, and enduring literary
or historical material. Literacy does not require news, long wording or advanced
terminology. Freshness does not establish difficulty or discrimination.

## Responding to “more recent examples”

Freeze the editorial date; actively search for newly published articles,
data releases or substantive updates before selecting replacements. Review
0–12-month and 13–24-month candidates separately, alongside evergreen sources.
These are internal discovery windows, not asserted CEEC proportions. Record
publication, event, data-period, substantive-update and access dates separately;
unknown month/day stays unknown. An access date or website refresh cannot make
an old event current. A portal URL is not a source for an invented archive item.

Build a paper-level **planned versus verified** table: unique source objects,
dated recent groups, literacy items and points by the three levels above, subject
domains, section placement and estimated solving time. Mark unsupported source
dates and unreviewed reasoning separately; do not include them in verified totals.
Count connected source objects once, even if they have multiple URLs or are reused
in several groups. Cite a local snapshot/claim map where available and distinguish
web verification from an archived snapshot.

When the user requests a modest increase, propose a positive increase from the
audited baseline in genuinely source-dependent groups, with the amount justified
by the paper's section, reading-load and time budget. Do not merely raise a
metadata quota or force all subjects into one current-affairs percentage.
Social Studies should distribute these across parts and disciplinary lenses;
English should diversify passage genres and argument structures; mathematics
must retain pure mathematics and must not acquire a physics/technology theme.
No named example becomes a fixed topic-to-unit mapping.

For a repeat release, compare the new verified counts with the failed baseline.
If source ecology is incompletely annotated, report the increase as an internal
editorial target, not a historically measured GSAT match.

## Student booklet versus internal provenance

All subjects require a full internal source/rights/claim ledger. The existence of
that ledger does not authorize printing it in the student booklet.

For each visible source note or explanatory addition, record `display_reason`
and a same-subject, same-regime, same-item-role reference page when form-based.
Keep it only when the selected official form calls for it, it is necessary for
answerability/source criticism, or rights require it. Otherwise keep it internal.
Remove gratuitous URLs, access dates, search/review narration, agency credibility
preambles and “source supplement” blocks from student output. Do not automatically
append an adaptation note to every math, English or Social Studies group.

Preserve authorship, era, perspective, units, definitions or essential data dates
when removing them changes interpretation. Keep the established inline literary
attribution for 國寫 when the official form requires it. An annotation being
nonessential to solving does not override that form or required attribution.
If photo licensing requires visible credit but the chosen form does not allow it,
select a suitable replacement; never silently drop legally required attribution.

Do not erase a warning to make fictitious evidence appear real. If a source note
reveals an invented passage or dataset inconsistent with the requested full mock,
replace or source the underlying content. Then compare the final visible notes,
paragraph endings and page flow with official references, not just the JSON.
