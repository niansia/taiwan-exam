# Distribution reopening candidate review (v0.7.0; not released)

This record documents a substantive reviewed code-fix candidate. It did not
resolve the software-distribution hold because the required ordinary Chrome
download check remained blocked. It is not a Microsoft false-positive verdict,
a claim that the historical detections did not occur, or a guarantee against
future security engine decisions.

## Reviewed fix basis

The public release is based on the rendering hardening introduced in `c466b33`
and the public distribution cleanup through `ed29653`. The review established
the following material changes rather than a filename-only repackage:

- arbitrary image paths, external resources and active HTML/SVG content are
  rejected before rendering;
- browser measurement uses a fresh isolated profile, a restrictive content
  security policy and a fixed trusted probe without disabling the Chromium
  sandbox;
- the redundant legacy helpers named in the historical detections remain
  retired, while maintained content and layout validators remain present;
- the end-user allowlist excludes maintainer-only packagers, scanners,
  attachment checkers, security incident records, private intake, test output,
  old archives and unreviewed batch/question builders;
- the release ZIP has one deterministic Skill root, complete manifest coverage,
  safe archive paths and per-member SHA-256 records.

The focused review and its limitations remain in
`references/rendering-security-review.md`. These changes reduce the attack
surface and establish a substantive `reviewed-code-fix` candidate, but they do
not by themselves reopen distribution or identify the historical heuristic.

## Exact release gates

Any replacement archive is eligible for stable publication only when all of these
conditions pass for the unchanged bytes:

1. attribution validation and the complete software regression suite;
2. archive/member allowlist, path and manifest-hash inspection;
3. current, enabled Windows Defender scans of the exact ZIP and all extracted
   members;
4. Windows Attachment Services `IAttachmentExecute.Save`, bound to the
   replacement's actual stable public HTTPS asset URL;
5. an ordinary browser download of that same public URL with protection enabled,
   followed by SHA-256 comparison to the locally scanned archive;
6. an independent ClamAV scan in GitHub Actions after stable publication.

For the deleted v0.7.0 candidate, the attachment check was bound to
`https://github.com/niansia/taiwan-exam/releases/download/v0.7.0/taiwan-exam-generator.zip`
and the ZIP SHA-256 was
`89f898fa503bcb5a6e7e58ca0f8e81af6de4dd7b4cc2e9ae6560b6f0070d512d`.
With Defender intelligence `1.459.154.0`, the ZIP, extracted members and
Attachment Services `Save` passed on 2026-09-11. The candidate Web Knowledge
Markdown also passed a Defender custom scan. These passing file checks did not
override the browser requirement.

The candidate was uploaded temporarily as a GitHub prerelease. Opening its
public asset by clicking the GitHub release page again produced Chrome's
`ERR_BLOCKED_BY_CLIENT`; no completed browser download existed for hash
comparison. The prerelease and its `v0.7.0` tag were deleted immediately. A
blocked browser result is a failure, even though the file and attachment scans
passed. No stable ZIP, release tag, security report or browser-pass record was
retained as a live download.

## Historical files

The withdrawn preview.2 and preview.3 hashes remain listed in
`SOFTWARE_RELEASE_STATUS.json`. The maintainer-only draft release containing
`candidate.zip` and the failed v0.7.0 prerelease were deleted. Old archives must
not be restored, renamed or presented as verified replacement assets.
