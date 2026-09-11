# LLM-original item generation

Read this reference for every new question or full paper. It defines how the LLM creates content after corpus analysis has finished.

## What the corpus may control

The historical corpus may constrain only:

- curriculum coverage and exclusions;
- observed paper-level variation in unit share, section placement, and cross-unit integration;
- response types, scoring, duration, and formal layout;
- empirical position/difficulty targets and allowed reasoning/load bands;
- aggregate stem/option length, stimulus, visual-function, and page-footprint distributions;
- broad misconception and cognitive-operation families.

These are probability envelopes and editorial constraints, not a reusable recipe. Do not copy one year's unit vector, item order, or combination of topics. A new paper should be compatible with the observed multi-year distribution while remaining a new coherent draw.

## What the LLM must invent

For every scored item, the LLM newly creates:

- the disciplinary or mathematical object;
- the information mechanism and ordered givens;
- the solution graph and required decisions;
- the representation or visual semantics;
- the surface wording or self-contained context;
- the misconception model and distractor derivations;
- the relation to neighboring items and the paper-wide motif balance.

The skill must not contain a unit-to-domain lookup table, reusable item skeletons, canned diagrams, fixed contexts, or predetermined numeric constructions.

## Candidate competition

For each slot, generate at least three candidates before writing final prose. The candidates must use mutually dissimilar mechanisms, not three cosmetic contexts for the same equation. Include a context-free mathematical object when that is editorially appropriate.

For every candidate, record:

- `mechanism_family` and `domain_family`;
- new object and task/unknown;
- curriculum bridge and all required operations;
- planned representation and whether a visual is essential;
- target difficulty vector and likely difficulty sources;
- main misconception/distractor paths;
- reason it is structurally distinct from recent sources and other candidates.

Select the candidate with the best joint fit for curriculum, originality, target difficulty, reasonable reading load, authentic information use, and whole-paper diversity. Do not select novelty for novelty's sake.

## From object to wording

Use this order:

1. fix the new object, constraints, and unknown;
2. solve it independently and adjust values so the intended answer format is valid;
3. derive plausible wrong paths;
4. design a new Visual Spec when a visual is solution-bearing;
5. write the minimum self-contained context needed to expose the information mechanism;
6. tune wording and page footprint to the current form band without changing the solution graph;
7. run bounded-novelty, difficulty, stimulus, originality, and rendering gates.

Long wording is not automatically competence-oriented. Short wording is not automatically routine. The information mechanism and evidence use decide.

## Whole-paper originality

After selecting individual items, build a paper-level diversity matrix across:

- unit and cross-unit combination;
- mechanism family;
- domain/source family;
- representation and visual topology;
- cognitive-operation sequence;
- response type and answer form;
- misconception family.

Reject motif saturation, repeated story worlds, repeated graph/shape topology, repeated solution shortcuts, or a sequence that mirrors one historical paper. Re-sample failed slots while preserving the formal Paper Profile and empirical difficulty envelope.

## Subject-specific innovation audit

The common originality record proves that the item was constructed through the blind candidate process. It does not by itself prove that the selected construction is meaningfully new inside its subject. For every scored item in a current-form 國綜, 英文, 社會, or 自然 paper, also store `item_spec.subject_innovation_audit` with:

- `subject`, matching the paper subject;
- `mechanism_family`, naming the subject operation rather than the surface topic;
- `candidate_competition_linked: true`, confirming that the selected mechanism is one of the candidates in `originality_record` and was not invented after the audit;
- `routine_template_recoverable: false`, meaning that no official, mock, or prior generated item can be recovered by swapping names, numbers, excerpts, images, labels, or sentence order while retaining the scored reasoning;
- `surface_or_topic_novelty_only: false`, rejecting novelty claims based only on a current event, unusual noun, new source, photograph, grayscale conversion, or unfamiliar setting;
- `new_subject_mechanism`, stating what new language, discourse, evidence, model, experiment, institutional, spatial, temporal, or cross-representation relation the candidate makes students operate on;
- `evidence_or_reasoning_architecture`, listing the ordered evidence use and decisions that distinguish the item from a stock template;
- `nearest_neighbor_difference`, identifying the nearest structural neighbor found in the official/mock/prior-generated audit and explaining a concrete difference in givens, evidence dependency, operation order, distractor logic, response decision, or visual topology;
- `reviewer_decision: pass-subject-novelty`.

The relevant subject reference defines what counts as a real mechanism. Empty prose, `N/A`, `new topic`, `different context`, `passed`, copied generic text, or metadata contradicted by the printed item is a release failure. A validator checks presence and internal consistency; a human or model reviewer must still compare the actual item with its recorded neighbor and solve it.

Every complete paper in those four subjects also stores `metadata.subject_innovation_review` with the matching `subject`, `all_scored_items_reviewed: true`, passing `mechanism_saturation_review`, `representation_saturation_review`, and `section_or_domain_diversity_review`, plus `reviewer_decision: pass-subject-novelty`. These findings must describe actual paper-level evidence. The existing `paper_originality_matrix` remains required; this subject review narrows it to discipline-specific repetition and cannot replace it.

## Required provenance

Every Item Spec must contain an originality record with:

- `generated_by: llm-original-construction`;
- `source_visibility: aggregate-only`;
- candidate count and the mutually distinct mechanism families considered;
- selected mechanism/domain family;
- novelty dimensions;
- curriculum-reduction and prior-domain-knowledge checks;
- lexical, structural, and visual-topology audit results;
- final reviewer decision.

Every mixed group also needs a group-level record covering stimulus originality, subpart dependency, leakage, and integration. A paper cannot pass when any scored item or mixed group lacks this record.
