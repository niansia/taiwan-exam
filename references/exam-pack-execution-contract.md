# Full-paper execution contract

The single authoritative evidence format and content/delivery workflow is
[pack-and-release-verification.md](pack-and-release-verification.md). Read it in
full before writing, rendering or testing a complete paper. Do not introduce a
second contract schema or substitute a generic batch generator.

Use the actual exam_packs manifest, subject, paper records, writer/difficulty
profiles, curriculum specification, reference PDFs and separate Layout Profile.
Learn aggregate form/coverage in the analysis pass; never pass historical stems,
numeric tuples or figure topology to the new-item writer.

For a local complete paper, reference PDFs are a required data layer. Verify the
selected subject with `scripts/bootstrap_exam_sources.py --subject <科目>
--verify-only` before treating a Paper or Layout Profile as source-backed. If the
check is incomplete, install the selected source pack and rerun the check. The
ordinary Git tree, a packaged Skill and the hosted-web projection may intentionally
omit multi-gigabyte binaries; that packaging choice does not make the binaries
optional for a source-verified local run and never authorizes their deletion.

Additional implementation invariants from the failed stress test:

- New content belongs in this run's exam JSON, never in a reusable script's
  stem/option/answer pool. Loops may serialize or orchestrate independently
  reviewed papers; they may not create versions by rotating a fixed pool.
- Difficulty follows actual shortest routes, not modulo/seed/quota cycling.
  Real alternatives and rejected mechanisms must be documented substantively.
- Independent solving uses the complete printable conditions, not hidden code
  constants. After solving without the key, compare answers. For every English
  gap, record the completed sentence/paragraph and check grammar and coherence.
- Detailed multiple-choice solutions review every option; a sample composition
  is an actual written response, not advice describing a good response.
- 國綜 and 國寫 share storage but have separate booklets/time/scores. English
  translation and composition stay inside English. Inspect actual mixed-section
  response types; matching only total count/score is insufficient.
- Missing sources, correct answers or form evidence cannot be excused by
  labelling a requested full exam as an internal preview. Repair the prerequisite
  or report an exact blocker. Never manufacture pass records.
- Treat `歷屆試題/`, `模擬考/`, raw intake bundles and their registries as
  protected inputs. Output cleanup must resolve its targets and exclude these
  roots. Git-ignore and package-exclusion rules are distribution boundaries, not
  retention policies.

For HTML/PDF subject entry points add metadata.run_contract pointing to the same
external run-contract.json, relative to the exam JSON. The handoff adapter
scripts/validate_exam_pack_contract.py invokes the existing validate_exam_release
content gate; it contains no separate validator policy. The public CLI can also
use --contract explicitly (HTML and PDF subject wrappers support it); conflicting
CLI/metadata contracts are rejected. Generic rendering rejects profile-bearing/full-paper
data, even with a verified metadata flag.

A subject renderer produces a review proof only. Final delivery still requires
the same external contract's delivery gate, bound final files, all-page readable
raster inspection and source/semantic/originality review. Keep proofs outside
the accepted PDF area. Watermark/fixture tests do not establish exam acceptance.
