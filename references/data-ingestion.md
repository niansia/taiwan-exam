# Data ingestion

Read this reference when the user adds past papers, mock exams, answer keys, scoring notes, or formatting examples.

## Keep originals private

Put source files under the matching subject's `歷屆試題/` or `模擬考/`. These folders are git-ignored. Run `index-sources` to create `metadata/source-index.jsonl` with file paths, sizes, modification times, and SHA-256 fingerprints.

For a downloaded multi-subject mock bundle, first run `scripts/ingest_gsat_bundle.py SOURCE --probe-pdfs` as a dry run. Use `--copy` to ingest while preserving the supplied folder; use the destructive `--execute` move mode only when the user explicitly requests moving the originals. The registry merge is hash-idempotent. If a folder is organized by subject rather than by bundle, the ingester may resolve the year/series against an already indexed bundle; otherwise pass `--bundle`, `--publisher`, and `--scope` explicitly.

For CEEC GSAT papers, `scripts/download_ceec_gsat.py --min-roc-year 100` catalogs the official page and downloads only PDF questions, answer keys, and non-choice scoring principles. It writes `metadata/official-source-registry.jsonl`; preserve `source_kind: official_past_exam` and never merge old-regime mathematics with current Math A/B calibration.

Do not move, rename, OCR, or publish the user's originals unless requested. An index is not permission to redistribute the file.

## Create one metadata record per item

Use `templates/question-metadata.csv` or write JSON Lines that conform to `schemas/question.schema.json`. A useful record captures:

- identity: exam, year, subject, curriculum, source kind, question id, question number, and section;
- content: unit, subunit, concepts, skills, and curriculum codes when known;
- form: question type, score, stimulus type, group id, diagram requirement, and expected time;
- difficulty vector: overall plus concept, calculation, reasoning, reading, novelty, and distractor dimensions on a 1-5 scale;
- evidence: answer rate, option response rates, discrimination, or reviewer confidence when available;
- rights and provenance: source file fingerprint, source URL, and whether source text can be published.

Do not infer empirical answer rate or discrimination from prose. Leave unknown fields null or absent.

Keep `requires_diagram` as `null` until the source question page has been checked. False means the item was reviewed and does not require a visual; it must not be used as a default for unreviewed material.

## Labeling quality

Use the curriculum version that governed the specific year. Do not merge pre-108 and 108-curriculum records without the `curriculum` field. For composite subjects, use `section` and `domain` (for example 社會/歷史 or 自然/物理) rather than inventing new exam subjects.

Difficulty is multidimensional. A question can be calculation-light but reasoning-heavy. Base labels on evidence when possible and store `difficulty_basis` as `empirical`, `expert_review`, or `estimated`.

After import, run `validate`, inspect all reported errors, then run `build-blueprints`. The builder aggregates only valid records and records a fingerprint so generated work is traceable to the exact metadata state.

Run `scripts/analyze_mock_bundle.py --bundle "BUNDLE NAME"` after paper profiles, visual signals, and question candidates exist. Its report contains aggregate text-load, source-cue, visual, structure, unit, and difficulty coverage only. Do not expose that bundle-specific report to the item-writing pass, and do not reinterpret mentioned calendar years as publication dates.
## Paper structure before item metadata

Every complete source paper needs a Paper Profile conforming to `schemas/paper-profile.schema.json`. Record the whole-paper question count, scored-item count, duration, total score, and each major section's title, order, question range, type mix, count, score rule, and subtotal. These values form a joint structure and must reconcile before the paper can calibrate full simulations.

Run `python scripts/build_paper_profiles.py` after ingesting a GSAT bundle. Text-layer parsing produces candidates; scan-only files remain `pending_ocr`. Review against the actual paper and change `structure_status` to `verified` only after every count and subtotal is checked. Do not fill missing values from memory or from another publisher's paper.

When solution files contain explicit unit/objective and difficulty labels, `python scripts/build_question_candidates.py` writes reviewable `questions.auto.jsonl`. Use `--promote` only after inspecting samples and reconciling the linked Paper Profiles. The extractor never invents a difficulty for subjects whose solution format omits it.
