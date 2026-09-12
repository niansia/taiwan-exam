# Replacement candidate review, 2026-09-12

Status: local checks passed; normal browser acceptance pending. This document
does not clear the public distribution hold or assert vendor confirmation.

The replacement incorporates reviewed source-installation path/collision and
atomic-write fixes, stricter source/profile evidence checks, scored-slot planning
and validation, unnumbered response rendering, source-bound calibration additions,
packaging boundaries, and explicit Traditional Chinese font fallbacks after
a Linux PDF text-extraction regression was reproduced in CI. Removed legacy helpers remain removed. There is no
encoding, obfuscation or compression change intended to evade detection.

Candidate: `taiwan-exam-generator-v0.7.1.zip`, 308 files.
SHA-256: `18e9a07760ac544f98e58945b3b44e18153e0f038a7864a83f3816e829ccfec8`.
Intended stable asset URL:
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
