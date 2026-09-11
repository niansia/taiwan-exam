# GSAT source corpus data release

Release tag: `source-corpus-2026.09.11`

This data release contains subject-scoped ZIP archives of the reference PDFs and
answer materials used by the local Taiwan Exam calibration workflow. The
ordinary Git tree remains lightweight; `exam_packs/學測/source-pack-manifest.json`
binds every archive and member file by SHA-256.

Use `python scripts/bootstrap_exam_sources.py --subject <科目>` to download only
the selected subject plus shared material. The bootstrapper rejects unexpected
paths, verifies the archive before extraction, verifies every installed file and
does not delete existing source data.

The archives contain reference documents and images only; they are not a Skill
installer or executable software release. Project code and documentation remain
under the repository's MIT License. Examination papers, passages, photographs,
publisher materials and fonts retain their respective source notices and rights;
their presence in this reference corpus is not a claim that the project's MIT
License applies to them or that Taiwan Exam is an official examination authority
release.

The source corpus is calibration evidence, not a reusable question bank. Generated
papers must still satisfy the curriculum, originality, independent-solving,
layout and release gates in `SKILL.md`.
