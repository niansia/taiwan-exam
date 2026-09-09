# Visual question generation

Read this reference whenever a source item or generated item contains a graph, diagram, map, table, photograph, experimental setup, document image, or other visual evidence.

## Treat the visual as part of the item specification

Set `requires_diagram: true` and attach a `visual` object conforming to `schemas/visual-spec.schema.json`. Do not calibrate visual difficulty from file size, pixel count, or visual clutter alone. Record:

- visual kind, subtype, layout, and whether it supplies context, evidence, or information required for the solution;
- information density, entity and label counts, number of data series, distractor salience, and visual reasoning steps;
- whether values must be exact or to scale, whether color is essential, target print width, and minimum raster resolution;
- semantic source data, rights status, generation method, safe alternative text, and mandatory validation checks.

Match difficulty using the joint pattern of text and visual demands. A similar-looking picture is not difficulty-matched if the student must perform a different number of searches, comparisons, transformations, or text–figure integrations.

Classify answer-bearing visuals by function before choosing a drawing style:

- `abstract-mathematical`: coordinate grids, function graphs, geometric constructions, networks, and finite patterns;
- `contextual-evidence`: maps, instrument panels, schedules, measured charts, document fragments, and process diagrams;
- `hybrid-scene-diagram`: a recognizable real or invented scene whose silhouettes, spatial relations, paths, fields of view, zones, or labels carry exact mathematical evidence.

A strong paper may use all three. Do not satisfy the visual quota with four near-identical abstract geometry drawings. For a current-form internal mathematics paper with at least four required visuals, include more than one functional class and normally include at least one `contextual-evidence` or `hybrid-scene-diagram`, unless the sampled form cluster explicitly calls for an abstract-only set.

For current GSAT mathematics, learn visual frequency and placement from ROC 111–115 official papers and same-period mocks, then distribute answer-bearing visuals across applicable single-choice, multiple-choice, fill-in, and mixed sections. Do not place the paper's only diagram in the final mixed group. Until item-level visual annotation is complete, an internal full-paper review candidate needs at least four required visuals or graphical representations across at least three sections; this is a provisional product floor, not a claimed CEEC statistic.

## Choose the generation route

Use a deterministic renderer when a pixel can change the answer:

- coordinate or function graphs;
- geometry diagrams and measurement relationships;
- bar, line, scatter, and other data charts;
- data tables and timelines;
- circuits, chemical structures, scaled maps, and precisely labeled scientific diagrams.

For maps, record the subtype: reference, projection, choropleth, cartogram, thematic, route, or topographic contour. Build answer-bearing maps from authorized geodata and a deterministic renderer; do not ask an image model to invent boundaries, values, contours, or scale.

Create semantic data first, solve from that data, then render it. `scripts/render_visual.py` provides grayscale-safe SVG for coordinate graphs, bar/line charts, and point/segment geometry. Extend the renderer rather than asking an image model to guess exact values.

For a hybrid scene diagram, separate a non-answer-bearing illustration layer from an exact overlay layer. The background may establish the telescope, launch tower, building, transit station, camera, laboratory, or daily-life setting; the deterministic overlay must carry every ray, path, boundary, tick, angle, scale, state, or label used in the solution. Record both layers in the Visual Spec and verify the composite in grayscale. A recognizable silhouette is allowed, but copying a source photograph's composition or a historical question's topology is not.

When a reference figure is present, treat it as layout or visual-function evidence only. Do not reuse its shape chain, node/edge topology, angle/length placement, panel reveal, or unknown location as the candidate's semantic data. Construct the new item's solution graph first, create a new Visual Spec from that graph, and run the visual-topology audit in [originality-firewall.md](originality-firewall.md). Rotation, reflection, scaling, relabeling, or changing drawing style does not make a copied topology original.

Use an image model for visual context whose fine geometry is not itself the numerical answer, such as a natural scene, an apparatus viewed as a whole, a biological context illustration, or an original documentary-style image. Use the scientific-educational or infographic-diagram style as appropriate. Keep critical equations, tick values, answer-bearing labels, and small text out of the image-model prompt; add them deterministically afterward.

If the context can be communicated clearly with original vector silhouettes plus deterministic overlays, prefer that route for print fidelity. Image generation is optional, not a mandatory sign of richness. Whichever route is used, the visual must earn its space: remove it and rerun the stimulus-removal test. A decorative rocket, telescope, skyline, or person does not count toward the answer-bearing visual quota.

For multi-panel photo options, generate each panel from a separate semantic description, normalize crop and contrast, then assemble and label the grid programmatically. Difficulty comes from the intended semantic contrast among panels, not from poor image quality or ambiguous cropping.

Real photographs are allowed for English and social-studies stimuli when their provenance and rights permit reuse. Record the original URL or archive identifier, creator/agency when known, publication date, license or authorization, crop, and every tonal transformation. Do not treat "found on the web" as a rights status.

Before converting a photograph, map each answer-bearing feature to one or more channels: shape, position, boundary, count, texture, readable label, relative tone, or measured value. Then render the exact placed crop in grayscale at the intended physical size and run an evidence-survival review. A reviewer must be able to point to every required feature without seeing the color original. If the item asks about hue, color category, color-coded legend, vegetation color, warning-light color, or any other chromatic fact, either add redundant deterministic encoding (labels, patterns, shapes, or values) and rewrite the item around that encoding, or reject the visual. Merely increasing contrast does not make a color-dependent question valid.

For photographs sourced online, prefer a licensed original over a screenshot embedded in a news article. If a news page is the discovery route, trace the image to the photographer, agency, archive, museum, government, or open-license repository before use. A source photo may support factual observation, but cropping or monochrome conversion does not make it original or erase attribution requirements.

Attribution requirements are satisfied through the internal source/provenance record unless the controlling official layout profile explicitly prints a photo credit. Do not insert `照片：...`, a URL, license prose, or an image-rights note into the student booklet by default. Keep textual passage/material attributions separate: they follow that subject's official source-line convention and are not suppressed merely because a photograph shares the source.

Use `licensed_source` only when the source is authorized for that use and the record says so. Do not redraw or lightly alter a publisher's historical figure merely to evade similarity. Generate a new semantic construction and a new surface composition.

## Image-model prompt contract

Build the prompt from the Visual Spec and include:

1. the educational purpose and observable scene;
2. composition, viewpoint, number of entities, and required empty label zones;
3. monochrome or color constraints and intended A4 print size;
4. what must be visually unambiguous;
5. explicit exclusions: no answer cues, no watermark, no branding, no decorative text, and no unsupported scientific details.

Store the original prompt and generated asset beside the generated `exam.json`. Set `source_rights: original`. If the image contains details not present in the Visual Spec, either remove them or revalidate the question against the final image.

## Validation gate

Before accepting a visual item, check all requested entries in `validation_checks`:

- compare every label, quantity, object, relation, axis, legend, and scale with `semantic_data` and the prose;
- solve using the rendered visual, not only the underlying spec;
- verify that cropping, captions, filenames, metadata, and alt text do not reveal the answer;
- print or render at the target physical width; raster artwork should normally be at least 300 dpi at that width;
- inspect in grayscale, because formal papers and student printers may not preserve color;
- compare the color source and final grayscale crop with an explicit `answer_evidence_survives_grayscale: true` record; store the reviewer and final print-width evidence notes;
- reject any color-dependent item whose decisive distinction is not redundantly encoded by shape, pattern, label, position, or value;
- make different series distinguishable by shape, line style, fill, or direct labels, not color alone;
- confirm symbols and small labels remain legible after A4 pagination;
- keep alternative text observational and sufficient, but do not encode an inference or answer unavailable to sighted students.

If any answer-bearing visual detail cannot be verified, reject and regenerate the item. Never repair an incorrect visual by changing the answer key alone.

## Rendering

Put the final asset in the exam project and reference it with `questions[].visual_asset` in `exam.json`. `scripts/render_exam.py` and `scripts/render_pdf.py` embed PNG, JPEG, WEBP, GIF, or SVG files into the self-contained paper. Use SVG for exact line art and high-resolution raster files for image-model output.
