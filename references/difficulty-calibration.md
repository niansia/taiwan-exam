# Difficulty calibration

Use this reference before analyzing difficulty, planning a full paper, or describing an output as GSAT-like.

## Evidence hierarchy

Difficulty is a measured outcome, not an adjective. Keep every source population separate and use this authority order:

1. CEEC official item P and D for official past papers;
2. representative local pilot-test item statistics for generated items;
3. publisher mock-exam item statistics from a documented examinee population;
4. structured expert review using the full difficulty vector;
5. model estimate, which is exploratory only.

Never convert publisher labels such as easy, medium, or hard into CEEC-equivalent P values. Whole-paper five-standard or score-distribution files may describe paper severity, but they cannot be assigned to individual items.

## P and D

For an official single-choice item, P is the answer rate. For an officially marked multiple-selection item, P is the score rate. D is the official discrimination value. Preserve `metric_type` and never compare answer rate and score rate without naming the distinction.

The local five bands are only compact descriptions:

- very easy: P at least 0.80;
- easy: 0.65 to less than 0.80;
- medium: 0.40 to less than 0.65;
- hard: 0.20 to less than 0.40;
- very hard: below 0.20.

These cut points are not CEEC labels. Planning must retain the continuous P target, interquartile range, D floor, metric type, year, section, and question position.

## Regime separation

For GSAT, analyze ROC years 100–106, 107–110, and 111 onward separately. The 111 reform introduced Math A/B and current mixed/constructed-response structures. Old mathematics is historical evidence only and must not set a Math A or Math B full-paper curve.

Use at least three compatible administrations for a position target. Prefer the latest five compatible years for the current regime. Do not pool question number 10 across years when it belongs to different sections or item types.

If the user names a compatible multi-year subset, use that subset instead of silently averaging it back into every available current year. Record the selected years, measured item count, mean/median P, section/position curves, and annual exceptions in the paper metadata. A subset still needs at least three administrations for a formal position target; otherwise treat it as a sensitivity comparison rather than a calibration curve.

For current GSAT generation, ROC 111–115 is not merely one regime among several: it is the exclusive primary corpus for the produced paper's difficulty form. Use its joint distribution of position, item type, P/D, reasoning depth, representation load, reading load, and distractor strength. ROC 100–110 may identify curriculum topics and historical reasoning archetypes, but must have zero weight in the current position curve, wording-load target, literacy share, or option-competition target.

## Full-paper target curve

A full-paper blueprint must provide a target for every scored slot:

- exact major section and item type;
- question-number or normalized within-section position;
- target P center and observed interquartile range where official P exists;
- D floor or review trigger;
- expected time and score weight;
- full difficulty vector: concept depth, reasoning steps, representation load, computation load, language load, novelty, distractor plausibility, and time pressure;
- calibration basis and confidence.
- a compatible 111–115 aggregate current-form cluster id derived from multiple administrations, and an explicit statement that older evidence, if present, is aggregate content-only.

Use section curves, not a single overall mean. Preserve recurring easy entry items, ramps, local resets at the beginning of a new section, and annual exceptions. For Math A/B, the current evidence supports a broad easy-to-hard tendency within opening sections, not a requirement that every adjacent question be harder.

## Target versus achieved difficulty

### Four-band paper planning for every subject

For user-facing paper plans use **簡單／中／中偏難／難** consistently. Never initialize an entire paper to「中」and leave that placeholder in the final answer key, or conceal the column instead of fixing the underlying design. Preserve the original continuous statistics and five-band archive; the four labels are an additional editorial display, not CEEC terminology.

For a transparent historical comparison only, the four-bin display is P ≥ 0.65, 0.50 ≤ P < 0.65, 0.40 ≤ P < 0.50, and P < 0.40. Keep answer-rate and score-rate strata separate. This display does not assign an achieved P to a generated item and does not erase differences in marking rules.

For each full paper, declare an integer target by item count and by scored points, its subject-specific 111–115 basis, and any justified deviation. All four levels should appear in a full paper unless a documented user request explicitly specifies a restricted practice set. Do not import Math A's percentage distribution or linked-decision numeric thresholds unchanged into language, science or social studies. Transfer its method: irreducible decisions, plausible wrong paths, shortcut tests, section-level demand and feasible solving time.

- 簡單: a clear concept or direct evidence link with a short accessible route.
- 中: connect conditions or textual evidence to a concept; at least one meaningful distinction or check.
- 中偏難: reconcile multiple evidence/condition sets, change representation, or reject a locally plausible incomplete interpretation.
- 難: interdependent in-syllabus decisions with at least two distinct bottlenecks; for reading, a close competing interpretation must survive one passage segment but fail against another. An unfamiliar word, longer paragraph or more arithmetic is not sufficient.

Every scored item records an expert-estimated band, confidence, actual linked decisions, plausible misconception, short solution route and expected minutes. Harder items whose full route collapses to direct extraction/substitution must be substantively redesigned, not relabelled to fill a quota. Count a shared reading stimulus's reading time once, then add marginal question time. Maintain accessible entries/resets and distribute difficult opportunities across sections/domains rather than stacking every hard item at the end.

Run `scripts/validate_paper_difficulty_balance.py` on every subject's completed paper. It checks four-band consistency, declared count and score targets, all-medium defaults, evidence fields and final content hashes. It is a structural audit, not a psychometric certificate: human re-solving must judge whether the written bottlenecks are genuine. Generated papers without representative pilots remain internal editorial tests, with the full-paper statistical calibration gap disclosed.

Use `python scripts/summarize_four_band_reference.py --output <report.json>` to reproduce the 111–115 display from the official statistics archive. Its pooled row is explicitly an unweighted objective-item count, not a full-paper score distribution; the answer-rate and score-rate strata must accompany that row. Record the chosen paper's actual scored-point balance separately. Do not overwrite an independently maintained subject paper merely to normalize its labels: pass the common gate to that paper's owner and review its item design before changing it.

Before administration, label difficulty `target` or `expert-estimated`. After a representative pilot, store achieved P, D, cohort description, sample size, administration conditions, and uncertainty. Do not claim that a generated item has an official-equivalent P merely because a model aimed at it.

When a pre-pilot independent solve exposes an overstated author estimate,
preserve both estimates and the actual shortest route. Either redesign the item
for a required hard slot, or explicitly revise the editorial whole-paper plan
if its accessible entries, discrimination opportunities and all four bands still
meet the subject evidence. Never keep an inflated adjective merely to preserve a
quota, silently count routine operations as new bottlenecks, or describe this
expert reassessment as measured P/D. A genuinely failed hard-slot requirement
still requires substantive replacement, not a more convenient label.

An item misses calibration when any of these holds:

- achieved P falls outside the accepted target interval;
- discrimination is below the subject/slot review threshold;
- the intended solution has fewer reasoning operations than the Item Spec;
- distractors do not correspond to plausible wrong paths;
- removing the stimulus preserves the same reasoning path for an item labelled competence-oriented;
- reading, representation, or computation load was silently reduced.
- a solution collapses to one direct substitution even though its 111–115 form pattern requires selecting a model, changing representation, or reconciling conditions;
- distractors cannot be generated by the named misconception paths;
- a difficult slot is made difficult mainly by long prose or unpleasant arithmetic rather than linked reasoning decisions.

Replace or revise failed items and run a new pilot; do not relabel them after seeing the results.

For current GSAT mathematics, a model must also pass [math-difficulty-design.md](math-difficulty-design.md) before rendering. In particular, an item cannot satisfy a hard position merely because its answer explanation has several algebra lines. Verify irreducible decisions and actively attempt shortcut collapse; if one familiar routine solves the item, regenerate it for that slot rather than upgrading its adjective.

## Bounded novelty

Novelty and difficulty are separate axes. A fresh setting, university-adjacent idea, workplace process, or unfamiliar diagram is allowed only when the item defines every external rule needed for the solution and the assessed knowledge remains inside the selected curriculum.

For each item, perform three checks:

- **prior-knowledge test**: a student who has never studied the external domain can still solve from the supplied evidence;
- **curriculum-reduction test**: after translating the setting, every required operation maps to named syllabus concepts and permitted tools;
- **difficulty-source test**: difficulty comes from selecting, connecting, and checking in-syllabus ideas—not hidden terminology, excessive decoding, arithmetic burden, or specialized facts.

Generate multiple candidates at the target slot, then compare them on the full difficulty vector. Reject both direct-substitution items that underuse the slot and novelty-heavy items whose language/representation load overwhelms the intended mathematics. Expert estimates remain provisional until a representative pilot supplies achieved P and D.

## Constructed response

Official objective-item P/D tables do not cover every constructed-response slot. Calibrate those slots from official rubric and score distributions, response examples, zero/full-credit rates when available, required evidence units, writing length, and expert double-scoring. Until those data are structured, a full-paper difficulty model remains incomplete even if objective-item curves are ready.

The objective-only `difficulty-profile.json` deliberately retains
`full_paper_status: insufficient-data`: that file alone cannot certify all paper
dimensions. Read the integrated `writer-blueprint.json` curriculum calibration
dimensions and the real source/rubric records as well. Do not flip the objective
profile's field to ready to suppress a warning. Missing constructed-response
rates remain null; actual rubric/evidence-unit review can support an editorial
paper, but is not a measured full-paper score distribution. Likewise, historical
source dates marked unverified do not establish a learned current-events lag.

## Hard gate

Never issue a complete GSAT mock paper when any required dimension is insufficient:

- verified official structure;
- official objective-item difficulty curve;
- constructed-response calibration;
- official semantic anchors;
- multidimensional difficulty annotations;
- literacy/stimulus annotations and provenance;
- verified layout profile for a formal-print claim.

`--allow-insufficient` is permitted only for custom exploratory practice and must never bypass the full-paper gate.
