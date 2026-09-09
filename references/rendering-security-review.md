# Local rendering hardening (2026-09-09)

This is a focused code review and regression record, NOT a Microsoft
false-positive verdict or a whole-project security certification.

## Confirmed code issues and changes

- Image embedding previously resolved arbitrary paths supplied in exam JSON.
  It now confines images to the exam directory after path resolution, rejects
  network paths and checks image bytes against the declared format. Keep exam
  images in that directory; do not weaken the boundary when an image is missing.
- Browser inputs previously lacked a static-content/resource boundary. New
  `safe_rendering.py` rejects input scripts, event handlers, external resources,
  active SVG elements, entities and processing instructions. It adds a
  restrictive Content Security Policy: no default resource access, only embedded
  images and inline layout CSS; only an exact installed measurement script may
  run via a script hash. Chromium's sandbox is NOT disabled. A dedicated fresh
  profile avoids sharing the user's browsing session; it is not a complete
  network/OS sandbox and browser background networking is only reduced.
- The SVG geometry validator was reimplemented, not recovered from quarantine.
  It measures label overlap, viewport containment and transformed stroked edges,
  uses a measurement budget, fails on empty/malformed input and binds results
  to source hashes. It rejects unsupported SVG features rather than silently
  dropping answer-bearing content. Stroke sampling and bounding boxes are
  conservative; markers, clipping and visual semantics still need final review.
- The redundant `qa_gsat_internal_layout.js` helper is retired. Its page-overflow
  role is covered by the maintained `validate_fixed_page_html.py`, whose normal
  content/frame checks remain mandatory. The SVG validator remains included.
- The maintenance attachment checker previously lost its detailed failure
  cause. A benign README control reproduced `Get-FileHash` not found at the
  hash-input stage. Python inherited PowerShell 7 module paths into Windows
  PowerShell. The launcher now removes only `PSModulePath` from the child's
  environment, case-insensitively, so Windows PowerShell builds its own default.
  No persistent environment, registry or antivirus setting is changed.
  See [Microsoft's documented Python launch case](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_psmodulepath?view=powershell-7.6).

## Verification and limitations

Behavioral regressions cover active/external SVG and HTML rejection, escaped CSS,
path escape, mislabeled images, forged layout reports, fresh browser profiles,
generated SVG compatibility, empty-input failure, and trusted probe execution.
Real Chromium tests cover clear labels, crossing strokes, overlapping labels,
out-of-frame labels and transformed edges. A real PDF test preserves Chinese
text. These are software fixtures, not full-paper educational acceptance.

The internal review ZIP `1c13cd4163be21be6e102e50f0defa08de8ea4de27df72084330156003136d89`
passed Defender archive/member checks and Attachment Services Save at
2026-09-09 14:45:32 UTC (engine 1.1.26080.3, intelligence 1.459.126.0).
The earlier attachment check failed before scanning because of the launcher
defect, not a newly confirmed malware detection. This hash belongs to an
internal review candidate, not the eventual public release. Any later changed
package needs new hash-bound scans and an actual browser download check.

The original preview.2/preview.3 detections remain historical facts. Their exact
Defender trigger has not been established. Do not characterize the hardening
or module-path fix as proof of the original detection cause, promise immunity
to future antivirus updates, restore quarantined files, or remove protection.
