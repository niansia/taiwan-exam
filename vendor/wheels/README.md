# Bundled PyMuPDF wheel

`build_hosted_skill.py` copies the PyMuPDF wheel in this folder into the hosted
ZIP as `resources/wheels/`, so a hosted runtime without PyMuPDF and without
package-index access can still install it offline (`scripts/ensure_pymupdf.py`).
The wheel is fetched, not versioned; download it before a release build:

```bash
python -m pip download PyMuPDF==1.26.0 --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.11 --no-deps -d vendor/wheels
```

Expected file: `pymupdf-1.26.0-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl`
(24,052,460 bytes, SHA-256
`a3f6a45fcf8177763a2629a2ab2cad326e8950a0d120b174b56369365355a2a7`). It is an
abi3 wheel for CPython 3.9 and later on x86_64 Linux, has no dependencies, and is
distributed under PyMuPDF's AGPL-3.0 licence by Artifex; the packager records its
hash in `PACKAGE_MANIFEST.json`. Without a wheel here the build still succeeds
but records `bundled_wheels.count = 0`; pass `--require-wheels` for a release.
