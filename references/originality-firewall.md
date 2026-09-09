# Originality firewall

Read this reference before generating or revising any item from a corpus of official papers, mock exams, screenshots, or publisher material.

## Core rule

Historical items teach the system **coverage and editorial behavior**, not reusable question skeletons. A generated item fails originality when a source item can be recovered by changing numbers, symbols, proper nouns, surface context, sentence order, or drawing style while preserving the same information flow and solution graph.

The LLM is responsible for inventing every candidate's disciplinary object, information mechanism, reasoning structure, representation, and distractor model at generation time. The skill supplies boundaries and rejection tests, not a bank of reusable skeletons, fixed domain mappings, or predetermined figure recipes.

This applies to **every scored item**, with no exemption for short or text-only questions. Single choice, multiple selection, fill-in, constructed response, and every subpart of a mixed group must each pass the same firewall.

Originality is independent from correctness and form fidelity. A paper may match the official syllabus, difficulty curve, typography, section structure, and response geometry while every actual problem remains new.

Examples suggested by a user or observed in a source are possibility proofs, not permanent mappings. Never encode rules such as “permutations and combinations use neural networks,” “trigonometry uses surveying,” or “probability uses medical tests.” Curriculum units and narrative/visual domains must remain independently selectable.

## Two-pass blind pipeline

Keep source analysis and item generation separate.

### Pass A: source abstraction

The analyzer may export only aggregate or de-identified pattern fields:

- curriculum unit, subunit, and concept coverage;
- section, response type, score, target position, and difficulty vector;
- cognitive operations and representation changes, expressed generically;
- stimulus family and the functional role of text, table, graph, or diagram;
- visual information density and function, never the source figure's topology as a generation template;
- stem/option length bands, option geometry, page footprint, and distractor misconception families;
- source-year distribution and compatible regime.

Do not pass source stems, options, numeric tuples, equations in source order, named entities, figure coordinates, node/edge lists, or cropped source images into the writing pass. Screenshots supplied to demonstrate layout may calibrate typography and placement only unless the user explicitly places their content in scope.

### Pass B: blind construction

The writer receives the Item Spec and aggregate blueprint only. It first invents a new mathematical or disciplinary object and a new solution graph, solves it, and only then writes the setting and representation. Never start by paraphrasing a retrieved item.

Before selecting a context, propose several mutually dissimilar information mechanisms from different domains, including a context-free mathematical construction when suitable. Reject repeated unit-to-domain pairings, repeated visual topology, and recent-paper motif saturation. Choose by curriculum fit, authentic data relations, readability, and novelty—not by a hard-coded example list.

For a generated item, record at least these novelty dimensions:

1. information mechanism or mathematical object;
2. task/unknown and required inference chain;
3. representation semantics or visual topology;
4. distractor-generating misconceptions;
5. narrative or source domain, when a context is used.

At least the first three must be independently new. Changing only the fifth dimension is a context skin and fails.

## Structural skin-swap test

Compare the candidate with its nearest official, mock, and already-generated neighbors. Reject it if any of the following is true:

- one-to-one replacement of numbers, variables, labels, or nouns reconstructs a source;
- the ordered givens, key equation sequence, case split, recurrence, probability tree, or optimization constraints are materially the same;
- the intended shortcut and the main distractor paths are the same;
- a diagram preserves the source's shape chain, node/edge topology, angle/length placement, panel relationship, or visual reveal;
- the candidate differs mainly in prose length, story wrapper, rotation, reflection, scale, or drawing style;
- a solver who memorized the source can answer without performing the candidate's purported new reasoning.

When uncertain, replace the underlying object and solution graph; do not merely rewrite the wording.

## Type-specific originality gates

### Text-only items

A text-only item may be concise and purely mathematical, but it must still begin from a newly invented object or relation. Reject canonical drill shells whose only variation is a coefficient set, named object, or requested final quantity. Lack of a figure is never an originality exemption.

### Fill-in items

Copy the official machine-marking geometry only; never copy the content skeleton. The candidate must contain an appropriate reasoning decision, representation change, case distinction, or constraint reconciliation for its target slot. Reject a bare recalled formula, one direct substitution, or a familiar equation with replaced constants unless the selected empirical slot explicitly calls for a basic entry item.

### Multiple-selection items

Each option must test a distinct inference or misconception about the candidate's new object. Reject five independent true/false textbook statements assembled around a familiar definition. Option interaction and evidence use must be planned before wording.

### Mixed and constructed-response groups

The shared stimulus must define one original system, dataset, document, experiment, or mathematical object. Subparts should reveal or reuse intermediate structure without leaking later answers, and the group must include genuine integration, transfer, evaluation, or justification. Reject a paragraph that merely binds several otherwise independent routine exercises.

Audit every subpart separately and the group architecture as a whole.

## Visual originality

Build every answer-bearing visual from a new semantic specification produced after the new item logic is fixed. Reference figures may supply only measurable form features such as print width, label size, grayscale contrast, caption placement, or the fact that the figure sits beside a fill rail.

Before release, compare candidate and source visuals by:

- entity types and counts;
- node degree sequence and edge direction;
- polygon/curve sequence and repeated-shape topology;
- location of unknowns, givens, annotations, and crossings;
- role of each visual lookup in the solution.

If these align closely with one source, regenerate the semantic construction rather than cosmetically redrawing it.

## Required audit record

Each candidate needs an originality record containing:

- corpus and years searched;
- nearest source IDs or `none found`;
- lexical-screen result;
- structural-screen result;
- visual-topology result when applicable;
- novelty dimensions actually changed;
- skin-swap test result;
- reviewer decision and reason.

Automated text similarity is only a triage screen. It cannot approve an item by itself. A structural comparison of solution and representation is mandatory, and any unresolved similarity blocks release.

For an all-data recheck, use `evidence-backed-editorial-audit.md` and the full-corpus
screen there; the legacy targeted screen omits older official years and generated
history. Include internal cross-group reuse and formula/solution-path neighbors,
not just word matches. Never inherit the writer's `pass` field as reviewer evidence.
