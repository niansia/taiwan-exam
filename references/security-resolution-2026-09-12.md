# Replacement candidate review, 2026-09-12

Status: resolved through reviewed code fixes, exact-archive scans and maintainer
confirmation of normal browser downloads at both draft and stable public URLs.
The install-release hold is cleared for the unchanged v0.7.1 asset below.
The withdrawn older hashes remain withdrawn. This is not vendor confirmation
that the older detections were false positives.

The replacement incorporates reviewed source-installation path/collision and
atomic-write fixes, stricter source/profile evidence checks, scored-slot planning
and validation, unnumbered response rendering, source-bound calibration additions,
packaging boundaries, and explicit Traditional Chinese font fallbacks after
a Linux PDF text-extraction regression was reproduced in CI. Removed legacy helpers remain removed. There is no
encoding, obfuscation or compression change intended to evade detection.

Candidate: `taiwan-exam-generator-v0.7.1.zip`, 308 files.
SHA-256: `18e9a07760ac544f98e58945b3b44e18153e0f038a7864a83f3816e829ccfec8`.
Verified stable asset URL:
`https://github.com/niansia/taiwan-exam/releases/download/v0.7.1/taiwan-exam-generator-v0.7.1.zip`.
The exact archive, extracted members, package manifest and Attachment Services
Save check passed. Full hash-bound scan evidence is retained in
`maintenance/security-scan-2026-09-12.json`.

Defender engine 1.1.26080.3, product 4.18.26080.3, signatures 1.459.170.0,
signature age 0; antivirus and real-time protection enabled. Scan timestamp:
2026-09-12T11:38:03.454624+00:00. No security settings were changed.

As a control, a normal link click in the automated Chrome session on the existing
document-only `taiwan-exam-gsat-sources-math-legacy-source-corpus-2026.09.11.zip`
also reached ERR_BLOCKED_BY_CLIENT on GitHub's release-assets domain. This is not
evidence that the replacement software is infected, nor evidence that a normal
user download succeeds. The tool URL policy rejected opening chrome://downloads;
no alternate browser-control or policy bypass was attempted.

A passing local candidate can be held in a private GitHub draft for the
maintainer to download normally. Record acceptance of these exact bytes and this
URL before promoting it. A changed archive or URL requires new checks. No
browser result is inferred from a command-line download or an attachment API pass.

## Maintainer download evidence

On 2026-09-12 the maintainer reported that the bottom ZIP asset could be downloaded
safely and supplied a screenshot identifying the v0.7.1 draft. The downloaded
`taiwan-exam-generator-v0.7.1.zip` is 4,551,413 bytes and its locally verified
SHA-256 matches the candidate above. No local username or device identifier is
retained in this record. The tested draft URL was:
`https://github.com/niansia/taiwan-exam/releases/download/untagged-b63e4bbea22ef4a26cbe/taiwan-exam-generator-v0.7.1.zip`.

The exact asset was retained when GitHub published v0.7.1 as a prerelease; its
asset ID is 559168049. Publication changed its URL to the stable URL above.
Automated Chrome at the stable URL again returned ERR_BLOCKED_BY_CLIENT.
The maintainer subsequently confirmed on 2026-09-12, in response to the explicit
stable-URL download check, that all downloads were normal (「下載都正常」).
This separate user confirmation supplies the stable-URL browser acceptance;
the earlier draft result is not relabeled as a stable-URL browser result.

After publication, a separate HTTPS download from the stable public URL also
matched the recorded SHA-256. This verifies published bytes, not browser
acceptance. The stable-URL scan report is also published in
`downloads/security-scan.json` for the independent distribution CI check.

## Independent published-asset check

[Distribution security run 34692929316](https://github.com/niansia/taiwan-exam/actions/runs/34692929316)
downloaded the stable public URL, verified the manifest and exact hash against
the URL-bound Defender report, and passed both ClamAV scans. ClamAV 1.5.3 with
3,628,061 known-virus signatures reported zero infected files in the ZIP and in
all 309 extracted files (308 package files plus the manifest). Scans completed
at 2026-09-12 12:10:52 UTC. Logs are retained in that run's distribution-security
artifact. This checks this release and these signatures, not future definitions
or every antivirus product.
