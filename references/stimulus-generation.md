# Competence-oriented stimulus generation

Use this reference for GSAT/CAP items built from articles, current events, public data, documents, experiments, maps, charts, or realistic situations.

## The item contract

A competence-oriented item must contain all three links:

1. **Evidence extraction**: the student must locate, compare, transform, or qualify information in the stimulus.
2. **Curriculum bridge**: the student must connect that evidence to named subject knowledge or a curriculum skill.
3. **Reasoned outcome**: the answer must require an inference, model, evaluation, explanation, or decision that can be checked.

Do not count scene-setting prose as competence orientation. Run a stimulus-removal test: remove the passage, event, table, or figure. If the same answer can still be obtained by recalling a definition or substituting numbers already repeated in the prompt, the stimulus is decorative. Rewrite the item or classify it as a basic item.

Cross-domain novelty is welcome but must be instructionally closed. The stimulus may borrow a mechanism from a profession, technology, university field, public issue, or everyday object, yet it must define that mechanism in ordinary language. Do not require the field's jargon or prior facts. The assessed bridge and all solution operations must remain inside the selected school curriculum. A user-provided example demonstrates a possible direction; it never becomes a mandatory or recurring unit-to-context mapping.

## Source routes

Prefer primary, auditable sources: government open data, official statistics, legislation and judgments, research institutions, peer-reviewed papers, museum/archive records, and first-party technical documents. News can identify a topic but should not be the sole factual authority when a primary source exists.

For time-sensitive material, record `accessed_at`, `published_at`, and a stable URL or dataset identifier. Fact-check claims before generation. Do not make a student need outside knowledge of the news event; the final stimulus must be self-contained.

Do not copy an article passage merely to make a reading block. Synthesize facts, change the rhetorical construction, and write an original self-contained stimulus. Preserve quantitative values only when they are needed and verified. Record whether the source is public domain, open-licensed, user-authorized, or used only as factual research.

Run a source-relation test in addition to the stimulus-removal test. Names may be anonymized without failure. Remove the actual source-derived quantitative relationship, constraint or evidence structure instead: if the same reasoning remains available, the source is decoration. Review the concrete counterfactual using `evidence-backed-editorial-audit.md`, not a copied pass label.

For 國寫, an article-like material block must have a rhetorical design, not just length. Assign each supplied passage one job—define a problem, narrate a documented case, complicate a claim, introduce counterevidence, or shift perspective. Compose the printable passages anew from a sourced fact ledger or from licensed text; never imitate the sequence and cadence of one source article. Every concrete case and factual assertion needs paragraph-level provenance. Do not create a fictional or composite anecdote to bridge sources, even when it is labelled as a simulated case. The task must reward selecting, relating, qualifying, or challenging the supplied material rather than repeating it.

## Temporal source ecology

Treat the source date as calibration evidence. For every historical competence-oriented item, record the exam administration date and each stimulus source's publication date. Derive `lead_time_days` from those dates; never guess it from the year label alone.

For a current GSAT simulation, learn stimulus form and source ecology primarily from ROC 111–115 official papers and mocks: passage/data length, source-family mix, number of linked questions, evidence density, lead-time band, curriculum bridge, and the operations actually required. ROC 100–110 may suggest a topic or evidence archetype, but it cannot determine the present literacy share or turn a current evidence-driven item into a short recall question.

Blueprints should learn joint patterns rather than independent averages:

- subject, section, and item position;
- source family (news, government statistics, research, law/judgment, archive, literature, life document, experiment, or synthetic scenario);
- publication-to-exam lead-time band;
- current-event, recent-context, or evergreen status;
- passage length, visual density, cross-domain breadth, reasoning operations, and difficulty;
- basic-item versus competence-oriented score share.

When generating on a new date, first build a dated inspiration pool that matches those joint patterns. Exclude events newer than the minimum observed editorial lead time unless the user explicitly requests rapid-response practice. Do not use information published after the simulated exam date. Prefer topics that remain answerable from the supplied stimulus even after the news cycle has passed.

The inspiration pool is not the paper. Rank candidates for source authority, factual stability, curriculum bridge, self-containedness, originality potential, rights safety, and difficulty fit. Only promoted candidates may become Item Specs.

## Required Item Spec fields

For every competence-oriented item, add:

- `stimulus_kind` and `stimulus_role`;
- `evidence_targets`: the exact rows, sentences, labels, or observations needed;
- `curriculum_bridge`: the subject concepts applied to that evidence;
- `reasoning_operations`: for example compare, calculate, causal-qualify, source-critique, model, transfer, or justify;
- `source_ids` linked to the paper source registry;
- `source_family`, `published_at`, `exam_date`, `lead_time_days`, and `freshness_class`;
- `stimulus_required: true`;
- `stimulus_removal_test: fail_without_stimulus`;
- `fact_check_status` and `rights_status`.

## Subject patterns

- **國文**: compare viewpoints, infer rhetorical purpose, evaluate evidence, connect classical and modern texts, or compose from supplied material.
- **英文**: integrate passage, chart, notice, or correspondence; test discourse, inference, synthesis, translation, and purposeful writing.
- **數學A/B**: define variables from a real dataset, select or critique a model, calculate from evidence, interpret residuals/uncertainty, and state model limits.
- **社會**: combine historical sources, spatial data, policy documents, statistics, and competing civic values; distinguish description from causation and evaluate provenance.
- **自然**: use observations, experimental design, graphs, mechanisms, uncertainty, and cross-domain evidence; require data-to-model or model-to-data translation.

## Paper-level gate

Keep an intentional balance of basic and competence-oriented items. For a full paper, report counts and scores for both. Do not force every item to have a long context; basic items remain valid. However, every item claimed as competence-oriented must pass the stimulus-removal test, and major mixed-question sections must be driven by shared evidence rather than repeated independent stems.

Also report stimulus-source coverage and temporal coverage. If publication dates are unknown for most historical stimuli, label the source-ecology model `insufficient-data`; do not claim that the LLM has learned the exam's current-event timing pattern.
