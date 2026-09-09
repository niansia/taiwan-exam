# Defender download detection: open investigation

Distribution is suspended. This record is NOT a false-positive verdict.
Maintainer sign-in to the Microsoft developer submission portal is complete.
The form now has a newly built, hardened review candidate selected for upload.
The original quarantined ZIP remains unavailable; the new candidate is not a
replacement for historical sample evidence. Final submission is pending; no
case number has been obtained. A prepared form is not a submitted case. Do not restore quarantined
files or reconstruct a blocked archive to bypass protection for this workflow.

## Confirmed evidence

Repository: https://github.com/niansia/taiwan-exam
Product: taiwan-exam-generator, educational item authoring and layout tools.
Detection: `Trojan:Script/Wacatac.H!ml`, threat ID `2147814524`.

- preview.2 ZIP SHA-256:
  `935f091d1f16a8334a4e259adca99354f632237ba9b3422ad529513cb3078798`.
  Detections identified `scripts/paginate_chinese_natural.js` and
  `scripts/render_chinese_natural_proof.py`, retired from preview.3.
- preview.3 ZIP SHA-256:
  `d7e6836d7ca965ba9b3a9d5f5434de09a8577f6e5bac1754113c5e0b11173a8e`.
  Size: 549431 bytes. ZIP and extracted-member Defender custom scans passed at
  2026-09-09 13:57:09 UTC. ClamAV 1.5.3 reported zero infected files in
  [CI run 34360739045](https://github.com/niansia/taiwan-exam/actions/runs/34360739045).
- At 2026-09-09 14:02:49 UTC, Defender event 1116 identified a download as Internet
  origin, type `FastPath`, source `Downloads and attachments`. Engine
  `1.1.26080.3`, signatures `1.459.126.0` (same as the earlier passing custom
  scan). It named two other files present in preview.3:

| Member | SHA-256 from the published manifest |
| --- | --- |
| scripts/qa_gsat_internal_layout.js | 935e21a8cc376d6fb65f821c3ab5e6f228cd40e5e6167304ec0b72626a57a31f |
| scripts/validate_svg_text_geometry.py | 0371e5bb12b9e0e29a4537ac8e228be734c7cdd63b57e52131a689909a7c8452 |

The downloaded copy was blocked before an independent hash could be obtained;
the archive hash above belongs to the published candidate. Event 1117 recorded
quarantine/no further action required, with error `0x80508023` (item no longer
found). The latest threat record was inactive and did not record execution.
This is not a whole-device clean bill of health.

## Review scope and uncertainty

The newly named files were reviewed as text, not executed. One uses Playwright
to measure local HTML overflow; the other constructs local HTML from SVG and
uses Chromium to measure text/stroke geometry. No obvious credential collection,
persistence or exfiltration was found in those files. This limited review does
NOT establish that the entire distribution or dependencies are safe. Loading
arbitrary SVG/HTML into a browser also needs an active-content/resource audit.
The exact detection rule is unknown; do not assert that browser automation is
the trigger or that this is a confirmed false positive.

## Hardened candidate: local passes, browser acceptance incomplete

A substantive rendering security revision is documented in
[the focused security review](rendering-security-review.md). It rejects active
HTML/SVG content and external resources, isolates browser profiles and removes
redundant legacy helpers without removing the maintained exam quality gates.

Internal candidate `0.6.0-security-review.1` is 547937 bytes, with 234 manifested
files and SHA-256
`1c13cd4163be21be6e102e50f0defa08de8ea4de27df72084330156003136d89`.
This candidate predates subsequent source-hash reporting and empty-directory
regression fixes in commit `c466b33`; it is not an archive of that entire commit.

At 2026-09-09 14:45:32 UTC, this exact candidate passed Defender custom scans of
the ZIP and extracted members and `IAttachmentExecute.Save` (HRESULT 0).
Engine: `1.1.26080.3`; intelligence: `1.459.126.0`; real-time protection enabled.
The attachment check used the previous public raw download source URL, not the
later draft-release asset URL. An earlier checker failure was a PowerShell
module-path compatibility error before attachment scanning, not a new detection.

A normal Chrome download from a maintainer-only draft release subsequently
ended at `ERR_BLOCKED_BY_CLIENT`. No downloaded artifact was available to hash.
That client block is not evidence of a new Defender detection; its cause is
unresolved. It was not bypassed. Neither the local passes nor a different URL
constitutes browser acceptance. Public installation downloads remain suspended.

## Microsoft analysis request (prepared, NOT submitted)

Please investigate this public educational software package, especially the
discrepancy between custom scans and download/attachment FastPath detection with
the same Defender engine and intelligence versions. Please determine whether
the identified files are malicious or misclassified, and provide a submission
ID, final determination and applicable intelligence update. We withdrew the ZIP
without disabling protection, adding exclusions, restoring quarantined code or
repackaging to avoid detection. The prepared form explicitly identifies the new
candidate hash, historical preview.3 detection, local passing checks and the
separate Chrome client block. It requests assessment rather than asserting a
confirmed false positive. Public substantive fix revision: `c466b33`.
Only public project code and these sanitized facts are in scope for submission;
private exam corpora, account data and raw device logs are not.

## Reopening criteria

The end-user archive allowlist now excludes the maintainer-only packager,
source exporter and Defender scanner. The source exporter separately preserves
these tools and CI. Regression tests exercise this boundary using benign
fixtures, not the withdrawn production archive. This packaging correction is
not a determination of the detection trigger and does not resolve the incident.

Do not interpret an Actions success while suspended as a fresh malware scan:
the suspension branch checks that the install ZIP is absent and skips scans.
The preview.3 passing reports are historical and precede its confirmed block.
URL reputation, filename reuse and heuristic sensitivity to scanner commands
remain unverified hypotheses. Versioned artifacts can improve traceability
after clearance, but a new filename/URL cannot substitute for incident resolution.

Resolve the incident through vendor determination or a documented substantive
code fix with security review. Scan the exact candidate, validate its manifest,
test Windows Attachment Services `Save` with the actual source URL, and verify a
normal browser download with protection enabled. The attachment test uses its
own client identity: it is additional coverage, not proof that every browser
check was reproduced. Retain hash-bound evidence. Do not remove required exam
quality validators solely because their filenames appear in a detection.

References: [Microsoft cloud protection](https://learn.microsoft.com/en-us/defender-endpoint/cloud-protection-microsoft-antivirus-sample-submission),
[Attachment Services Save](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-iattachmentexecute-save),
[Microsoft submission portal](https://www.microsoft.com/en-us/wdsi/filesubmission).
