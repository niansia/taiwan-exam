# Software distribution security

This workflow is for maintainers publishing Skill code, not ordinary users
generating papers. It is separate from educational quality and attribution.

On 2026-09-09 Defender detected `Trojan:Script/Wacatac.H!ml` in preview.2's
legacy `paginate_chinese_natural.js` and `render_chinese_natural_proof.py`.
Vendor confirmation of a false positive has NOT been obtained. These unused
proof helpers are retired, not renamed, obfuscated or repackaged elsewhere.
Current subject renderers and their content/layout gates remain required.

Before publication:

1. Review code changes, dependencies, archive contents and callers of removed
   tools. Preserve source licenses; exclude private data and unneeded executables.
2. Run regression tests. A functional pass is not an antivirus pass.
3. Build with `package_skill.py --public-release` or `export_public_repo.py`.
   Public packaging now requires enabled Windows Defender with signatures no
   older than one day. It scans the actual ZIP AND extracted files, checks
   archive paths and manifest hashes, and fails closed on detections, scan
   errors, missing tools or changed bytes. Do not publish a failed candidate.
   Internal builds may skip this only as unpublished review artifacts.
4. Publish the exact scanned ZIP with its `downloads/security-scan.json` report.
   Check the downloaded bytes against the report's SHA-256 after publication.
   Any changed archive requires a new scan. Do not claim all engines, future
   definitions, browser reputation systems or platforms have approved it.
5. If protection flags a release, stop distributing that revision, investigate
   exact hashes and detections, and obtain vendor analysis if needed. Never
   instruct users to disable antivirus, add exclusions or restore quarantined
   code. Do not change encoding/compression merely to avoid detection. Do not
   submit user files to third-party services without appropriate authorization.

The scanner's `-DisableRemediation` is a custom-scan option, NOT disabled
protection: it scans archive contents, ignores file exclusions and records
detections without applying remediation. Real-time protection stays enabled.
Existing Defender cloud/sample policies are not changed. See the
[Microsoft command-line documentation](https://learn.microsoft.com/en-us/defender-endpoint/command-line-arguments-microsoft-defender-antivirus).

Git history can still contain the withdrawn revision. Its existence is not a
recommendation to restore/use it. The ordinary installation link must point to
the replacement; users should not have to operate scanner commands themselves.
