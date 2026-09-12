# Current-form GSAT mathematics profile (111–115)

Use this profile for Math A and Math B whenever the requested form is a current GSAT or a current commercial mock. It records evidence from the official 111–115 corpus, with 114–115 PDFs used for direct typography inspection. Older papers may contribute content domains and item archetypes, but must not override current surface form.

Keep a separate **context-texture** audit from the curriculum-unit audit. A paper can contain enough pure-math records yet still read like a physics or engineering paper if astronomy, energy, waves, motion, sensing, or similar settings cluster together. Unless requested otherwise, science/engineering external settings should occupy no more than one quarter of the scored items, must not dominate consecutive sections, and must be balanced by pure mathematics, everyday/civic contexts, data, arts/humanities, and neutral diagrams. Spatial geometry is not automatically a physics context; judge the printed wording, not only the syllabus code.

## Typography and formula contract

- Main Chinese item text: `PMingLiU` / `MingLiU` (新細明體), nominal 11 pt.
- On a hosted web surface where those proprietary families are unavailable,
  follow `web-platform-use.md`: keep the original template PDF for locked text
  and use a metric-compatible Traditional-Chinese serif/Kai substitute for new
  body text, validated by final-size rasters. Do not fail solely on the internal
  font name.
- Latin letters, numerals, and mathematical text: Times New Roman, nominal 11 pt.
- Instruction rules: `DFKai-SB` / 標楷體, commonly 12 pt. Do not collapse these
  with all section headings: the page-measured 115 Math A controlling profile
  uses approximately 13.02 pt bold PMingLiU for section headings. Use the selected
  profile's role measurements, not a universal 12 pt heading assumption.
- In the 115 cover specimen, the organization and year lines are approximately 19.98 pt DFKai, the subject title approximately 25.98 pt DFKai/Times, the signature warning 18 pt DFKai, and the notice heading approximately 16.02 pt. Treat these as profile measurements rather than visual guesses.
- Do not substitute Noto Serif TC for a mathematics paper when the Windows fonts above are available. Its glyph width, punctuation position, and apparent density are visibly different.
- Never use Unicode presentation glyphs such as `₂` or `ⁿ` as the final formula representation. They carry font-specific miniature metrics and often look much smaller than the official notation. Store formula structure semantically and render subscripts/superscripts at the measured script ratio and baseline offset.
- A renderer must check body text, inline formulas, display formulas, fractions, radicals, matrices, subscripts, superscripts, vectors, and cases separately. Matching the Chinese font does not imply that mathematical composition is correct.
- The target is not merely the same nominal point size. Match apparent density, full-width Chinese punctuation, line spacing, formula axis, script baseline, and spacing around operators.
- For the measured v4 Math A implementation, use the existing
  `render_gsat_internal_review.py` components and PDF wrapper after the content
  gate. Store math between `\(…\)` or `\[…\]`; the pinned `latex2mathml`
  dependency produces static, screened MathML. It does not execute a TeX engine.
  Check full-size fraction numerators/denominators as well as deliberately smaller
  scripts. Times New Roman is the primary Latin face; MathML may need Cambria Math
  for mathematical glyphs. Report and inspect that fallback, not byte-identical
  font fidelity. Never switch to the generic 9.4 pt renderer to make content fit.
- In `gsat-math-a-115-measured-v1`, body pitch is 20 pt, the content frame is
  241 mm high, and the footer baseline is approximately 797.22 pt from page top.
  Budget section rules, stimulus blocks, actual formula heights and item margins
  within this frame. The final formula page is supplied by the maintained v4
  component; it is not a blank extra-content page.
- Cover examples must remain completely inside the bordered instruction box at final print metrics. Allow explanatory prose to wrap inside its remaining column; do not force a long sentence into one unbreakable flex row or visually shrink the entire example to hide overflow.

## Avoid repeat mathematics proof repairs

For timed runs also follow [fast-full-paper-workflow.md](fast-full-paper-workflow.md).
The following rules concern the maintained mathematics renderer, not a faster
question-writing substitute:

- Keep reproducible formula/line-breaking fixes in the mathematics component,
  not only in one paper's exported HTML. Measured v4 inline MathML reserves 4px
  of vertical glyph clearance on each side; prompts/stimuli use strict Chinese
  line breaking with normal word wrapping. This clearance prevents formula
  ink from exceeding its inline box; it is not extra response space or a way
  to satisfy page-density checks. Main type size and measured line pitch stay
  unchanged. Display formulas retain block behavior.
- Measured teacher explanations bind each inline formula only to its immediate
  closing punctuation. Do not wrap a whole sentence, several formulas, a display
  equation or an entire solution in `nowrap`. Overwide mathematics must still
  fail containment; split the expression at a mathematically valid boundary
  without changing the stated conditions or shrinking the type.
- Use explicit delimiters and braced fractions/binomials when first authoring
  both questions and explanations. Check component behavior once when renderer,
  browser or fonts change, before spending time on a new full-paper layout.
  `python -m pytest tests/test_measured_math_renderer.py -q` exercises these
  components when working in the source checkout; it is not paper acceptance
  and is not an installation prerequisite for end users.
- Set the actual student page assignments, option geometry, marking rails and
  teacher `answer_page_groups` before the first PDF. Diagnose all failed blocks
  from the same DOM report together instead of changing one margin and printing
  the entire paper after every small adjustment. Repair within the selected
  profile, then rerun containment; density and full-page inspection still apply.
- Write candidate decisions and second-solve notes once, then serialize those
  actual findings into the required schema. Do not ask the model to rewrite
  identical evidence at each handoff, and never auto-invent review verdicts.
  Freeze the content after scope, answer and originality reconciliation, before
  final PDF/page-review hashes are bound. Later content edits invalidate the
  relevant reviews and require whole-paper rechecking.
- Keep diagnostics in files and return a compact list of failed page/question
  ids, measurements and causes to the model. Do not repeatedly echo a complete
  MathML document or the entire successful DOM tree into the conversation.
  Full evidence must remain available; a short display is not a reduced check.
- Do not remove the shared content handoff or final delivery rerun to save a
  small amount of runtime. Measure first: distinguish machine validation/export
  seconds from model writing, review, tool round trips and repair time. An
  unchanged-paper rendering regression does not establish a 20-minute newly
  authored-paper result. After renderer changes regenerate affected proofs;
  preserve prior delivered files, withdraw stale candidate review claims, and
  compare every page before making a new acceptance claim.

## Stem rhetoric contract

A current-form literacy item normally has three functional moves:

1. **Material setup** — introduce a phenomenon, procedure, record, diagram, or short source passage and establish why the information exists.
2. **Operational definitions and constraints** — define symbols, measurement rules, assumptions, exceptional cases, or the relation among representations.
3. **Task** — ask for an inference, model judgement, computation, or selection that can only be made after integrating the material and constraints.

Length alone is not literacy. Add a sentence only when it supplies information that the solver must interpret, translate, compare, or test. Delete any context that can be removed without changing the solution path.

For the current primary corpus, the compact detected character distribution of selected-response items is roughly P25 164, median 205, P75 269. The detector includes options and may occasionally capture adjacent print, so this is a calibration band, not a per-item quota. Nevertheless, a full paper whose selected-response median is far below 160 compact characters is presumptively too terse and must be reviewed.

Avoid these weak forms:

- a one-sentence textbook exercise with a decorative proper noun;
- a paragraph that merely delays stating the same equation;
- explicit instructions that reveal the intended formula or algorithm;
- every item using the same “某公司／某同學” narrative shell;
- all givens compressed into symbol-heavy engineering prose.

## Difficulty contract

Apply the full record and release thresholds in [math-difficulty-design.md](math-difficulty-design.md). The points below describe the visible paper behavior; they do not replace the anti-collapse audit.

- Early single-choice items may be accessible, but must still contain a plausible misconception or representation change; “read one value and substitute once” is not an adequate default.
- Difficulty should generally rise through the single-choice block, then reset locally at the start of a new response type. It need not be perfectly monotone.
- Medium items should normally require at least two linked decisions, such as identifying a model and then checking a constraint.
- Hard items should require three or more linked operations, a non-obvious representation change, case separation, global consistency, or rejection of a tempting shortcut.
- Treat operations as linked only when they require distinct choices or inferences. Several algebra lines, repeated matrix multiplication, or applying one area/ratio rule multiple times still count as one routine if no new decision is made.
- Multiple-choice distractors must correspond to distinct mathematical claims. Do not create options by superficial sign or arithmetic changes.
- For Math A, apply [the answer-count and close-option rules](math-difficulty-design.md#math-a-unpredictable-answer-counts-and-occasional-close-options): randomize the planned correct-option count across 1–5 without a fixed pattern; occasionally use one or two justified close-numerical-option items. Mathematical truth determines the final key, and closeness alone does not establish difficulty.
- A diagram is part of the reasoning when scale, incidence, trend, partition, ordering, or correspondence must be extracted from it. It must not be decorative clip art.

## Visual and placement contract

- Current-form visual questions must occur outside the final mixed section as well as inside it. For an internal pre-calibration gate, require at least four required visuals across at least three sections of a paper.
- Include more than one visual role across a paper: for example, geometry/partition, statistical chart, process/timeline, coordinate model, or tabular record.
- Each required visual needs a legibility check at final print size and a stimulus-removal check. If removing the visual leaves the same solution path, the item fails.
- Visuals must be deterministic and vector-first. Labels, ticks, angles, and line weights must remain readable in grayscale.

## Option geometry contract

- Five short options: one horizontal row when they fit at final print size.
- Five medium options: use the formal 3+2 grid.
- Four short options: one horizontal row when they fit.
- Long propositions or independent statements: stack vertically.
- The renderer must receive an explicit `option_layout`; automatic browser wrapping is not an accepted layout decision.

## Machine-marked answer rail contract

Selection/fill items are printed for optical-card response, not as open blank-answer exercises.

- Position the answer rail at the semantic blank inside the sentence. Do not center every rail as a separate block. It may remain at line end, wrap with the sentence, or sit in the left text column beside a right-hand figure.
- Integer: print the exact number of circled positions over a continuous answer line.
- Fraction: print numerator positions above a fraction bar and denominator positions below it, with a second answer line below the denominator row when the selected profile shows it.
- Sign, decimal, or special-symbol positions, when allowed, must be separately specified and printed.
- Position IDs are sequential in reading order: `(q-1)`, `(q-2)`, and so on. Do not invent numerator/denominator suffixes.
- The expected answer must fit exactly. Too many or too few positions is a release-blocking defect.
- In the 115 Math A selection/fill specimen, a position circle is the DFKai `○` glyph at approximately 25.98 pt (about 9.16 mm em-square) with a Times New Roman row identifier at approximately 10.02 pt. Use these measured values before substituting a generic CSS border circle.

## Section continuity contract

- Print a major section heading and its instruction rule only where that section begins.
- When the first objective section begins, print the overall part heading and the single-choice subsection heading on separate lines. Do not compress `第壹部分、選擇（填）題（占85分）` and `一、單選題（占35分）` into one run-in heading.
- When a section continues on the next page, continue directly with the next item. Do not repeat “一、單選題”, “二、多選題”, “三、選填題”, or their instruction box.
- When a section instruction already states a shared score such as “每題5分”, do not repeat “（5分）” beside every question. Keep item scores in the data for validation, but make per-item score labels opt-in and require direct evidence from the selected official form before enabling one.
- Count each major section heading in the rendered content pages. A count other than exactly one is a release-blocking error.

## Page-density and breathing-room contract

- Passing the overflow gate is necessary but not sufficient. Compare the occupied vertical band with a compatible current official page; a page with questions crowded at the top and a large unmotivated blank field below fails visual review even when no element is clipped.
- Give each question a deliberate lower breathing interval. Use fixed page assignment plus item-level minimum-height targets, or rebalance questions across pages, so the intervals are distributed among questions instead of accumulating only above the footer.
- Do not fill a page by enlarging one diagram or by changing item wording. Adjust page assignment, question minimum heights, and within-profile spacing. Preserve the footer clearance and keep answer-bearing figures at their validated print size.
- The final reference-formula heading is bold. Consecutive formula lines use the measured line rhythm without empty spacer paragraphs unless the selected official profile directly shows a group break.

## Mixed-section answer-space contract

- Current GSAT mathematics booklets send written mixed-response work to the separate answer sheet. Do not add workbook-style ruled answer lines beneath constructed-response prompts in the question booklet.
- Keep the question text, shared stimulus, figures, and any booklet response geometry evidenced by the selected official Layout Profile. Treat a generic `answer_space_lines` field on a Math A or Math B mixed-response item as a release-blocking defect unless the controlling official paper explicitly prints such lines.
- Removing ruled lines must not be compensated by enlarging a figure until it collides with the footer. Preserve the measured page density and leave deliberate white space when the official form does.

## Release checks

Reject the paper if any of the following is true:

- the current-form mathematics font stack is not used;
- any scored item lacks a passing `difficulty_design` record or the paper fails `scripts/validate_math_difficulty_design.py`;
- Unicode presentation subscripts/superscripts remain in the rendered paper;
- the selected-response text is globally terse or telegraphic;
- the visual placement floor is missed;
- a required visual is decorative or illegible;
- an option block wraps accidentally;
- a machine-marked response rail does not encode exact answer geometry;
- a response rail is globally centered instead of occupying the answer blank's semantic position;
- any major section heading is missing or repeated on a continuation page;
- the first-part and single-choice headings are collapsed onto one line;
- a shared score is redundantly printed beside individual questions without form evidence;
- a mathematics mixed-response prompt contains invented workbook-style answer lines;
- a question, stimulus, option block, answer rail, figure, or figure label crosses the printable content boundary or is clipped by a page footer;
- page whitespace is visibly accumulated as one large unmotivated field instead of distributed as question breathing room;
- the reference-formula heading is not bold or the formula list contains accidental empty spacer rows;
- cover instructions, marking examples, or table content cross their own border even if they remain inside the physical page;
- section counts, scoring, or total score differ from the selected official blueprint.

## Originality is orthogonal to form fidelity

The current-form corpus controls aggregate form: unit coverage, item-type behavior, reasoning load, stem/option length, diagram function, response geometry, and page density. It must not supply a single-item skeleton to the writer.

- Give the writer only aggregate slot specifications and abstract cognitive operations.
- Do not expose a source stem, numeric tuple, equation order, diagram topology, or answer/distractor set during construction.
- Invent and solve a new mathematical object before applying current-form rhetoric and layout.
- Compare the candidate's ordered givens, solution graph, distractor paths, and visual topology with its nearest official and mock neighbors.
- If number substitution, variable renaming, noun replacement, rotation, or cosmetic redrawing recovers a source item, reject it regardless of lexical similarity.

Follow [originality-firewall.md](originality-firewall.md) for the required audit record.
