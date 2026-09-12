# Timed full-paper workflow

Read this reference when a user asks for faster generation, a timed benchmark, or a target such as one complete paper within 20 minutes. Speed is measured under the same complete-paper contract as ordinary generation. This workflow changes scheduling and cache use; it never lowers educational, originality, source, rights, layout, or review gates.

## What the time means

Treat 20 minutes as a per-paper **warm-run performance target**, not a universal guarantee or an acceptance rule. Record whether the run is:

- `cold`: required profiles, reference measurements, fonts, renderer dependencies, or source snapshots still need discovery or repair;
- `warm`: the exact subject/regime Paper Profile, Layout Profile, blueprint fingerprint, renderer, validators, and reusable source-rights records have already passed compatibility checks;
- `revision`: a user-requested correction of an identified paper, which is not a new-original-paper benchmark.

The timed generation clock starts only after a fresh run contract has been created and compatible immutable inputs have been loaded. Report prerequisite/readiness time separately. Stop the clock only after the student PDF, answer material, required validation reports, provenance record, and hash-bound all-page review record exist. A PDF export alone is not completion.

Never claim a warm-run number as a cold-start number. Never exclude failed candidate writing, repair passes, source verification, rendering, or page inspection from the timed total. If a process is retried, the retry remains inside the clock.

## Safe reuse and forbidden reuse

Cache immutable analysis that is independent of the new questions:

- Exam Pack audit and profile compatibility results, bound to file hashes;
- official-paper measurements, layout profiles, curriculum code tables, vocabulary-list extraction, and renderer/font capability checks;
- licensed/public-domain source originals, rights records, and frozen factual snapshots that remain valid at the editorial lock date;
- validator environments and deterministic rendering assets that contain no question content.

Invalidate a cache entry when any bound hash, profile id, editorial-lock condition, rights term, dependency version, or renderer measurement changes. Record the cache keys and hit/miss state in the timing report.

Never cache or reuse generated stems, passages, option sets, numeric tuples, solution graphs, distractor paths, visual topology, prompt metaphors, or a previous paper's section sequence as a shortcut. Do not write a reusable question bank, hard-coded paper builder, or batch content generator. New scored content stays in the current run's `exam.json` and must pass the originality firewall.

This prohibition concerns inheritance by a **new paper**, not resuming the same
identified run after interruption. Persist the phase/artifact evidence described
in `web-platform-use.md`; revalidate hashes, then continue from the first unfinished
phase. Do not discard solved items or redownload verified assets on every user
“continue”. In hosted mode, use that reference's bounded-loading and transport
workflow rather than reconstructing the whole repository or all subjects.

## Fast path, one paper at a time

1. **Readiness gate** — validate the selected pack, subject, Paper Profile, Layout Profile, blueprint fingerprint, scope references, renderer, and required private inputs. Fail early with an exact gap report rather than starting an impossible benchmark.
2. **Fresh contract and blueprint** — freeze the simulated exam date and editorial lock, create the external run contract, and lock the subject distribution, source ecology, visual/photo plan, difficulty vector, answer pattern, and page roles. Natural Science and Social Studies photo counts use a minimum of two with no upper bound; plan more when independent answer-bearing observations improve the paper.
3. **Source tournament** — query or load several unrelated, rights-safe candidates together, freeze facts and provenance, then close source wording before original writing. 國寫 still requires its task-specific source tournament and paragraph-level map.
4. **Slot writing** — write candidates from abstract slot specifications. Candidate competition, independent solution, scope mapping, misconception design, and visual-removal tests remain mandatory. Parallelize only independent read-only analysis, rendering, hashing, or validation work that cannot leak one candidate's surface into another.
5. **Incremental rejection** — run cheap structural, count, score, scope-code, answer-distribution, rights-record, and schema checks before expensive rendering. Replace failed slots and re-solve affected groups; do not defer known defects to final pagination.
6. **Single controlled render loop** — render the validated content with the maintained subject component, run containment and density checks, then make only form-preserving pagination repairs. Content changes revoke affected solution, source-removal, and originality approvals.
7. **Final gate** — render the final student and answer PDFs, apply document provenance, rasterize every page, inspect every page at readable scale, and bind reviews to final hashes. Run the shared content/delivery gate and record unresolved limitations.

## Timing report

Save `generation-timing.json` beside the paper. It must contain:

- `schema_version`, `paper_id`, `subject`, `run_kind`, `target_minutes`, `started_at`, `completed_at`, and `elapsed_seconds`;
- `clock_start_definition` and `clock_stop_definition` using the boundaries above;
- `prerequisite_seconds` reported separately;
- ordered phase records for planning, source work, writing/solving, validation/repair, rendering, and final all-page review;
- cache keys with bound hashes and hit/miss status;
- candidate/rejection counts, render attempts, final PDF hashes, gate-report paths, and `target_met`;
- `quality_gates_waived: []`. Any nonempty value makes the timing run invalid as a complete-paper benchmark;
- bottlenecks and a truthful note when the target was missed.

Phase time may overlap when independent processes run concurrently, so the sum of phase durations may exceed wall-clock time. `elapsed_seconds` is the wall clock and controls `target_met`. Use a timezone-aware clock and never manually round a near miss downward.

## Interpretation

A single pass shows feasibility for that subject, machine, cache state, source conditions, and selected profile only. It is not proof that every future paper or every subject will meet 20 minutes. Report a six-subject result subject by subject. If one paper exceeds the target, keep the valid output, identify the measured bottleneck, and optimize only reusable analysis or scheduling on the next run. Do not reduce photograph provenance, discipline balance, passage length, candidate competition, answer verification, or page review to manufacture a faster number.
