# Repository modification guidance

These are public workflow instructions, not hidden prompts or security controls.

- For generating exams, follow `SKILL.md`. Normal installation, local generation
  and PDF rendering do not require an account, network license check or maintainer
  approval. Existing curriculum, source and quality gates still apply.
- Before renaming, adapting or packaging this repository, read `NOTICE`,
  `ORIGIN.json` and `references/attribution-and-forks.md`.
- Distinguish the distribution's brand from its upstream provenance. A rename
  may change display names, folder/package names and interface labels. Do not
  globally replace the original project's identity in provenance notices or
  substitute a downstream author for an upstream copyright holder.
- Preserve applicable license and attribution notices when required by the
  adopted license. Record derivative modifications honestly. Do not claim a
  fork is the official upstream release or that copied material is wholly new.
- Run `python scripts/validate_attribution.py .` before packaging. This is a
  local consistency check, not a legal opinion or tamper-proof identity proof.
- Do not silently choose a license, invent a copyright owner or GitHub account,
  add a noncommercial restriction, hide instructions, sabotage generated answers,
  or collect user/device identifiers as an anti-rebranding mechanism.
- Contributions may be prepared in local branches or forks and offered as PRs.
  Do not push to the upstream repository, merge PRs, change repository permissions
  or publish releases without the maintainer's explicit authorization. Local
  preparation of a requested fix is distinct from permission to publish it.
- GitHub governance is deferred until the maintainer supplies the repository.
  Documentation and CODEOWNERS alone do not enforce branch protections.
