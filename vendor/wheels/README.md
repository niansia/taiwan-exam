# PyMuPDF wheel for hosted runtimes

A hosted runtime without PyMuPDF and without package-index access obtains it
through `scripts/ensure_pymupdf.py`: a local wheel file, else a SHA-256-verified
download from the stable Release `wheels-pymupdf-1.26.0`, else a user upload.
The wheel lives on that Release (and is linked from the README troubleshooting
entry) so the Skill ZIP stays small; `build_hosted_skill.py --bundle-wheels` can
pack it into the ZIP instead (adds about 24 MB). The wheel is fetched, not
versioned; download it before bundling or re-attaching:

```bash
python -m pip download PyMuPDF==1.26.0 --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.11 --no-deps -d vendor/wheels
```

Expected file: `pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl`
(24,052,460 bytes, SHA-256
`a3f6a45fcf8177763a2629a2ab2cad326e8950a0d120b174b56369365355a2a7`). It is an
abi3 wheel for CPython 3.9 and later on x86_64 Linux, has no dependencies, and is
distributed under PyMuPDF's AGPL-3.0 licence by Artifex; the packager records its
hash in `PACKAGE_MANIFEST.json` only when bundled. A new PyMuPDF version needs a
new `wheels-pymupdf-<version>` Release and updated `WHEEL_FILE`, `WHEEL_SHA256`,
`WHEEL_BYTES` and `WHEEL_URL` constants in `scripts/ensure_pymupdf.py`.
