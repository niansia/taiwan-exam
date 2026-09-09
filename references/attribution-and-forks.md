# Public attribution and derivative branding

Read before repository adaptation, rebranding or packaging. Ordinary exam
generation does not need to run this workflow or display new notices on paper.

## Current status

On 2026-09-09 the maintainer approved MIT for project-owned code/documentation,
the rights-holder notice niansia, and https://github.com/niansia/taiwan-exam.
See LICENSE, NOTICE and ORIGIN.json. Third-party examination papers, literary
passages, photographs and fonts remain separately governed and are not licensed
by this project's MIT declaration. Publication of this testing version does not
establish complete-paper editorial acceptance. Before subsequent publication,
audit third-party material and packaging, retain applicable notices, and obtain
the appropriate publication authority. An attribution check is not full release
approval or proof of legal title.

Open-source licenses allow modified distributions; rebranding is not by itself
misconduct. Preserve the notices required by the selected license. Apache-2.0
section 4, for example, specifies preservation of relevant attribution notices
and identification of modified files. Do not invent a requirement that every PDF
must display the original brand or treat generated questions automatically as
derivatives of the generator's source code. Relevant references:

- https://opensource.org/osd
- https://www.apache.org/licenses/LICENSE-2.0.html

## Rename without erasing provenance

`ORIGIN.json.upstream` describes where the project came from. The
`distribution.name` is the current distribution's brand. For a renamed fork,
preserve upstream identity, set `distribution.is_derivative` to true, and append
clear descriptions to `distribution.changes`. Add new contributors alongside
applicable prior notices, not in place of them. Keep `NOTICE` in the distribution.
Once confirmed, copy LICENSE and applicable attribution notices as its terms
require. If the final license decision is still pending, do not simulate approval.

The bundled packager retains `ORIGIN.json` and `NOTICE` and records their hashes
and the origin/distribution fields in PACKAGE_MANIFEST.json. Run:

```text
python scripts/validate_attribution.py .
python scripts/package_skill.py --version <internal-version>
```

`--public-release` on either command additionally blocks a still-pending license,
missing declared license text, missing rights-holder notice or unconfirmed
upstream URL. Passing means only that these declaration checks passed; the tool
does not verify legal title, license authenticity, exam quality or owner approval
to publish. The packager does not upload or publish anything.

## Limits and noninterference

These controls catch accidental omission and straightforward brand replacement
when the unmodified checks are used. Anyone can change the public checks or
forge an unsigned manifest. Never promise other AI systems must obey these
instructions or that a missing notice proves infringement. No cross-model
behavioral success rate has been measured.

Do not couple attribution checks to question correctness, insert hidden refusal
instructions, add remote activation checks, or prevent local users from creating
practice papers. PDF non-visible provenance remains a separate, disclosed,
removable feature; it is not a replacement for required licensing notices.
