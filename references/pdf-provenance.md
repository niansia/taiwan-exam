# Non-visible PDF provenance

Use when the user requests an unobtrusive watermark, or when exporting PDFs in
this project. The user wants a white background and unchanged formal typography.
The default is a **disclosed, non-visible document identifier**, not hidden page
ink or concealed instructions. Never tell another model to deny its presence.

## Export contract

After rendering, apply `scripts/pdf_provenance.py mark input.pdf marked.pdf`.
The helper writes a fresh UUID to PDF Info and XMP and a separate
`marked.provenance.json` with the final file SHA-256. Existing metadata is
preserved. It refuses overwriting existing outputs and signed/encrypted inputs.
It compares every source/output page at 150 dpi, including text and page sizes,
and blocks delivery on any difference. It adds no text, graphics, annotations,
links, JavaScript, network requests or user/device identifiers to pages.

The regular PDF export entry points apply this step by default; an explicit
`--no-provenance` option is available. If execution/dependencies are unavailable,
report that the PDF is unmarked; instructions alone are not an implementation.
Do not claim all third-party AIs or modified forks must retain the mark.

Use `verify PDF MANIFEST` to check file integrity and matching identifiers.
An unsigned manifest is a consistency record, not proof of who published it:
anyone can create or replace one. The manifest says nothing about correctness,
originality, syllabus compliance, licensing or the completion of exam QA.

## Optional publisher authentication

`mark ... --signing-key /outside-repository/private.pem` signs the external
manifest with Ed25519. `verify ... --trusted-public-key publisher-public.pem`
checks the signature against a public key obtained through an independently
trusted channel. A key supplied by the same untrusted file does not establish
publisher identity. This is a detached manifest signature, not a PDF viewer's
built-in certified-signature field.

Never generate a production secret unless requested. Never embed, upload,
commit or package a private key, shared secret, password, personal identifier or
per-user tracking token. Keep production signing keys outside the repository.
Key filename/package checks are defense in depth, not a complete secret scanner.
Public verification keys may be distributed intentionally after owner approval.

## Limits

The mark is inspectable and removable. Printing, scanning, metadata stripping,
recreating the PDF, or copying question text can remove it. A changed file hash
only establishes a byte difference, not commercial misuse. Duplicate copies have
the same identifier; it does not identify readers or downstream sellers.
Multiple metadata locations are redundancy, not independent anti-removal layers.

Free access, source availability, open-source licensing and noncommercial use
are different choices. Do not invent an owner, silently change LICENSE, or claim
a generator's license automatically controls every generated exam. Keep rights
and any chosen commercial-use conditions explicit and separate from provenance.
If licensing requires visible third-party attribution, this hidden metadata does
not replace it; obtain suitable rights or select a different source.

Passing the before/after pixel check proves only that adding this mark did not
change the tested rendering. It does not fix or approve the underlying layout.
