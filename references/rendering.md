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

Question images are referenced through `questions[].visual_asset`. Paths are resolved relative to `exam.json` and embedded as data URIs, so the resulting HTML remains self-contained and PDF rendering does not lose local images. See [visual-generation.md](visual-generation.md) for the required visual checks.

Open the HTML in a modern browser and print to PDF with background graphics enabled. For fixed-page internal proofs, run `python scripts/validate_fixed_page_html.py <paper.html>` before export; confirm the selected wrapper actually runs this check rather than assuming all PDF tools do. The final delivery gate reruns containment on the student and answer HTML. Horizontal overflow, vertical overflow, or an element crossing either the page content rectangle or a bordered semantic container blocks acceptance. Before delivery, rasterize and compare every page to the official reference. Inspect cover and instruction wording, page boundaries, box containment, density, section starts, headers/footers, clipped content, tables, figures, equations, font fallback, answer spaces, and unintended answer leakage. Inspect full-size page rasters rather than relying only on a contact sheet.

When rendering is unavailable, use stable Markdown headings and numbered options, but label it as a chat preview rather than a formal paper.
