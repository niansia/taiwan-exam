# Rendering

Local PDF and geometry tools accept static, self-contained exam documents only.
Keep image assets within the exam JSON directory; scripts, event handlers,
external URLs and unsupported SVG features are rejected. Do not disable the
input checks or Content Security Policy to make a figure render. Correct the
figure without changing its answer-bearing information and recheck its layout.
See [rendering-security-review.md](rendering-security-review.md).

Read this reference when producing a formal paper, answer booklet, HTML, or PDF.

For PDF exports, also read [pdf-provenance.md](pdf-provenance.md). The export
helpers add non-visible provenance by default and verify that every rendered page
is unchanged by marking. This check must not be confused with layout acceptance.

The model should first produce `exam.json` conforming to `schemas/exam.schema.json`. Read [layout-fidelity.md](layout-fidelity.md). Do not improvise a different visual structure on every run.

The bundled CSS is a generic practice renderer. It is not evidence of official fidelity. For `generation_mode: full-paper`, `metadata.layout_profile` must name a verified subject/regime profile and `metadata.layout_fidelity_status` must be `verified`; otherwise rendering must stop rather than present a generic page as a formal paper.

Use `scripts/render_exam.py` / `scripts/render_pdf.py` only for custom practice
that is not a complete-paper simulation. They reject full-paper/profile-bearing
data even when a metadata flag claims verified layout. For full GSAT review
proofs use the maintained subject components `render_gsat_internal_review.py`
or `render_gsat_official.py` and their PDF wrappers after the shared Exam Pack
handoff passes. Do not create another batch renderer. These components control:

- paper size, margins, typography, headers, footers, and page breaks;
- exam title, subject, duration, score, candidate fields, and instructions;
- question numbering, scoring labels, option alignment, section hierarchy, and group stimuli;
- separation of student paper and answer key.

For measured Math A/B v4, use `render_gsat_internal_review.py` and its PDF
wrapper, not the generic official-named component. Both student and teacher
documents must consist of actual fixed `.sheet` pages. Before rendering answers,
plan `metadata.answer_page_groups` as ordered lists of question ids: each answer
appears exactly once, each group occupies one detail page. Set
`metadata.answer_expected_page_count` to the approved quick-key plus detail-page
count. Adjust this plan if real measurements fail, then review the revised plan
before printing again. Do not leave the details in unmeasured flowing HTML behind
one fixed cover. The maintained wrapper checks containment for v4 answers too.
Rendered explanations come from `reasoning` and `explanation_blocks`; put actual
partial-credit rules and distractor explanations in these printable fields.

For static MathML, write both arguments explicitly: `\frac{1}{2}` and
`\binom{6}{3}`, never bare `\frac12` or `\binom63`. The converter may tokenize
bare digits together and consume the following equality sign. The maintained
renderer rejects that ambiguous form. Delimit exponents and subscripts in both
questions AND answers; `u=2^x` or `M_min` in ordinary prose is rejected rather
than silently printed as source notation. Inspect the resulting fraction or
binomial numerators and denominators, not just the existence of a MathML node.

Do not use text substitutions to insert spacing inside `msub`, `msup`, or
`msubsup`: these require exactly two, two, and three children. Function spacing
belongs in an enclosing expression row. A smaller `2` sitting on the ordinary
baseline is NOT a correctly rendered log base or squared trigonometric function.
Inspect those positions at readable scale and check their vertical placement;
the presence of an `msub`/`msup` tag alone is not proof of correct output.
After a shared formula-rendering fix, re-render and review all affected papers,
including the formula sheet and teacher explanations. Withdraw stale visual
passes and preserve the observed defect and its correction in the review record.

Keep instruction placement faithful to the selected reference: for the measured
115 mathematics booklet, the cover carries full scoring rules, while the first
three boxed section notes give only item ranges and points. Print the separate
85-point Part I heading, and place odd/even numbered body-page footers at the
left/right outer edges. Mixed-item type and points belong at the prompt end.
Do not replicate full cover scoring rules inside each section to fill space.

Question images are referenced through `questions[].visual_asset`. Paths are resolved relative to `exam.json` and embedded as data URIs, so the resulting HTML remains self-contained and PDF rendering does not lose local images. See [visual-generation.md](visual-generation.md) for the required visual checks.

Open the HTML in a modern browser and print to PDF with background graphics enabled. For fixed-page internal proofs, run `python scripts/validate_fixed_page_html.py <paper.html>` before export; confirm the selected wrapper actually runs this check rather than assuming all PDF tools do. The final delivery gate reruns containment on the student and answer HTML. Horizontal overflow, vertical overflow, or an element crossing either the page content rectangle or a bordered semantic container blocks acceptance. Before delivery, rasterize and compare every page to the official reference. Inspect cover and instruction wording, page boundaries, box containment, density, section starts, headers/footers, clipped content, tables, figures, equations, font fallback, answer spaces, and unintended answer leakage. Inspect full-size page rasters rather than relying only on a contact sheet.

When rendering is unavailable, use stable Markdown headings and numbered options, but label it as a chat preview rather than a formal paper.
