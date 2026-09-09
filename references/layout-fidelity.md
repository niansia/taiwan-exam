# Formal layout fidelity

Use this reference whenever the output is described as a formal GSAT/CAP paper, official-like paper, or print-ready simulation.

## Separate structure from appearance

A Paper Profile proves question count, score, timing, sections, item types, and order. A Layout Profile separately proves the visual and instructional form. Passing one gate does not imply passing the other.

A verified Layout Profile must record, from an official paper in the same exam, subject, and regime:

- cover title hierarchy, organization line, subject label, and year-label pattern;
- exact instruction blocks and their order, including time, writing instruments, correction rules, answer-sheet rules, and scoring explanations;
- paper size, page count target, printable area, margins, columns, baseline/font family and measured size ranges;
- section-heading wording and hierarchy, question-number and option format, score labels, stimulus boxes, tables, figures, and answer-space rules;
- running header/footer, page-number wording, total-page wording, signature reminder, and booklet/answer-sheet references;
- subject-specific first-page and final-page behavior;
- reference file hash, page-level measurements, review status, and visual-diff tolerance.

For current GSAT output, measure the layout distribution from ROC 111–115. Older papers may clarify a historical element but cannot set the current font, density, cover, instruction, option, or page-flow target. Publisher mocks from the same period may be used to learn robust variation, but official papers remain authoritative for the final shell.

For every selected-response item, store an explicit option layout rather than deriving it at render time. At minimum support one horizontal row, four-per-row, three-plus-two, two-column continuation, and fully stacked options. Mathematical expressions must be measured by rendered width, and the chosen arrangement must match a recent reference pattern for the same item type. Equal-width five-column grids are forbidden when they compress or concatenate options visually.

For mathematics fill-in items, blank underlines are not an acceptable substitute for the official marking contract. Store and render the exact number of answer rows, their sequential ids (for example `15-1`, `15-2`), and their integer/decimal/fraction/sign arrangement. A fraction must place numerator rows above the bar and denominator rows below it. Validate that the displayed slots agree with every accepted answer, including signs and leading-zero rules.

Place the machine-marked rail at the exact semantic blank in the item sentence; never center all rails by renderer default. A rail may wrap to a new line through normal text flow or occupy the left column beside a right-hand figure. For the measured 115 mathematics profile, use the DFKai `○` position glyph at approximately 25.98 pt and Times New Roman row identifiers at approximately 10.02 pt, then verify apparent circle diameter and line lengths on the rasterized page.

A section heading and its instruction box appear once, at the first item of that section. A page break inside the section must not reprint them.

For current GSAT 國寫, source attribution is inline paragraph-ending text. The closing full-width parenthesis follows the material's final sentence and wraps only through ordinary typesetting; it must not become a centered line, standalone paragraph, footnote block, or bibliography card. Multi-text prompts use small `甲`/`乙` identifiers when needed, never worksheet-like headings such as `材料一：` and `材料二：`. Include these nodes in the same overflow and orphan checks as the material paragraph so a source line cannot be pushed into an isolated bottom-page fragment.

Instructions must be transcribed from the chosen official reference and reviewed. Do not fabricate a shorter generic list while claiming formal equivalence.

Visible source notes require a same-role official-form basis, an answerability
need, or a rights obligation. Follow `evidence-backed-editorial-audit.md` for the
student/internal split. Do not print the source registry, access dates or editorial
supplements by default; do not delete an essential author/date or literary source
note merely because other subjects omit credits.

## Render gate

`layout_fidelity_status` has three meanings:

- `verified`: an exact subject/regime template has been measured and visually compared with the official reference;
- `reference-only`: official pages exist, but measurements or transcriptions are incomplete;
- `generic`: stable readable house style only.

A full paper may be rendered as a formal simulation only with `verified`. `reference-only` can produce a proof for review; `generic` must be labelled a practice preview. Missing status is treated as generic.

## Verification loop

Render to PDF, rasterize every page, and compare side by side with the reference. Check cover, instruction wording, page count, section starts, question density, orphaned stems/options, table and figure scaling, equations, page headers/footers, answer space, and grayscale legibility.

Before PDF export, measure every fixed page container in the rendered browser DOM. Reject the build on horizontal or vertical overflow, or when the bounding box of a direct child, question, stimulus, option block, answer rail, table, figure, or figure image crosses its containing rectangle. Apply the same containment test to bordered instruction boxes, response examples, tables, and other elements whose border carries semantic meaning; staying inside the physical page is not enough when text crosses its own box. `break-inside: avoid` is not sufficient: an indivisible question can itself be taller than the remaining page or even taller than the page frame. Fix wrapping, container sizing, page assignment, side-by-side placement, or figure size, then rerun the measurement.

After export, rasterize every page at review resolution. A contact sheet is only a navigation aid; inspect each page at readable scale, with extra attention to the last visible row of every figure and the area immediately above the footer. Do not mark the paper visually reviewed when only page count, text extraction, font inventory, or average density was checked.

Page count is a constraint, but never alter question content, score, or wording merely to force pagination. Fix typography, spacing, and breaks inside the verified tolerance. A paper with correct questions but generic layout fails formal-layout validation.
