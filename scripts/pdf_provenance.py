#!/usr/bin/env python3
"""Non-visible PDF provenance. Not DRM, secret instructions, or a copyright claim."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

NS = "urn:taiwan-exam:provenance:1"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
SCHEMA = "taiwan-exam/pdf-provenance/1"
INFO_ID = "/TaiwanExamDocumentID"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def page_fingerprints(path: Path) -> list[dict]:
    """Compare actual page pixels AND extracted text; never paint on the page."""
    import fitz

    rows = []
    with fitz.open(path) as document:
        for page in document:
            pix = page.get_pixmap(matrix=fitz.Matrix(150 / 72, 150 / 72), alpha=False)
            rows.append({"size": list(page.rect), "pixels_sha256": digest(pix.samples),
                         "text_sha256": digest(page.get_text().encode("utf-8"))})
    return rows


def _xmp(reader: PdfReader, record: dict) -> bytes:
    metadata = reader.trailer["/Root"].get("/Metadata")
    if metadata:
        # Preserve pre-existing XMP properties; malformed XML is not silently discarded.
        root = ET.fromstring(metadata.get_object().get_data())
        rdf = root if root.tag == f"{{{RDF}}}RDF" else root.find(f".//{{{RDF}}}RDF")
        if rdf is None:
            raise ValueError("Existing XMP has no RDF container; refusing to discard it")
    else:
        root = ET.Element("{adobe:ns:meta/}xmpmeta")
        rdf = ET.SubElement(root, f"{{{RDF}}}RDF")
    # Do not stack contradictory records when maintaining a previously marked proof.
    for description in list(rdf):
        for element in list(description):
            if element.tag.startswith(f"{{{NS}}}"):
                description.remove(element)
        for key in list(description.attrib):
            if key.startswith(f"{{{NS}}}"):
                del description.attrib[key]
    description = ET.SubElement(rdf, f"{{{RDF}}}Description", {f"{{{RDF}}}about": ""})
    for key, value in record.items():
        ET.SubElement(description, f"{{{NS}}}{key}").text = str(value)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def mark_pdf(source: Path, output: Path, *, manifest: Path | None = None,
             signing_key: Path | None = None) -> dict:
    """Write a new copy; refuse overwrite, encryption and signed input. No network."""
    source, output = source.resolve(), output.resolve()
    manifest = (manifest or output.with_suffix(".provenance.json")).resolve()
    if len({source, output, manifest}) != 3:
        raise ValueError("Input, output and manifest must be distinct paths")
    if output.exists() or manifest.exists():
        raise FileExistsError("Output or manifest exists; choose new paths (no implicit overwrite)")
    reader = PdfReader(source)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF is not supported")
    if any(field.get("/FT") == "/Sig" for field in (reader.get_fields() or {}).values()):
        raise ValueError("PDF has signature fields; refusing to invalidate existing signatures")
    record = {"schema": SCHEMA, "document_id": str(uuid.uuid4()),
              "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "source_sha256": digest(source.read_bytes())}
    writer = PdfWriter(clone_from=reader)
    writer.add_metadata({INFO_ID: record["document_id"]})
    stream = DecodedStreamObject()
    stream.set_data(_xmp(reader, record))
    stream.update({NameObject("/Type"): NameObject("/Metadata"), NameObject("/Subtype"): NameObject("/XML")})
    writer.root_object[NameObject("/Metadata")] = writer._add_object(stream)
    before = page_fingerprints(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pdf-provenance-") as work:
        candidate = Path(work) / "marked.pdf"
        writer.write(candidate)
        writer.close()
        if page_fingerprints(candidate) != before:
            raise ValueError("Pixel/text/page geometry changed; marked PDF was NOT released")
        payload = {**record, "filename": output.name, "pdf_sha256": digest(candidate.read_bytes()),
                   "page_count": len(before), "visual_check": "identical-at-150-dpi",
                   "pages": before, "claim": "Document provenance only; not exam QA, ownership or license enforcement"}
        envelope = {"payload": payload, "signature": None}
        if signing_key:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            key = serialization.load_pem_private_key(signing_key.read_bytes(), password=None)
            if not isinstance(key, Ed25519PrivateKey):
                raise ValueError("Use an Ed25519 private PEM key stored outside the repository")
            public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            envelope["signature"] = {"algorithm": "Ed25519", "key_id": digest(public),
                                     "value": base64.b64encode(key.sign(canonical(payload))).decode("ascii")}
        # Exclusive creation protects existing user files even if another process races us.
        created_output = False
        try:
            with output.open("xb") as target:
                created_output = True
                target.write(candidate.read_bytes())
            with manifest.open("x", encoding="utf-8") as target:
                target.write(json.dumps(envelope, ensure_ascii=False, indent=2) + "\n")
        except Exception:
            if created_output:
                output.unlink()  # Only the new file created by this invocation.
            raise
    return {"pdf": str(output), "manifest": str(manifest), "document_id": record["document_id"],
            "pages_unchanged": len(before), "signed": bool(envelope["signature"])}


def verify_pdf(pdf: Path, manifest: Path, *, trusted_public_key: Path | None = None) -> dict:
    envelope = json.loads(manifest.read_text(encoding="utf-8"))
    payload, signature = envelope["payload"], envelope.get("signature")
    if payload.get("schema") != SCHEMA or digest(pdf.read_bytes()) != payload["pdf_sha256"]:
        raise ValueError("Unknown schema or PDF hash mismatch")
    reader = PdfReader(pdf)
    record = ET.fromstring(reader.trailer["/Root"]["/Metadata"].get_data())
    xmp_id = record.find(f".//{{{NS}}}document_id")
    if xmp_id is None or xmp_id.text != payload["document_id"] or reader.metadata.get(INFO_ID) != payload["document_id"]:
        raise ValueError("PDF Info, XMP and manifest identifiers disagree")
    if len(reader.pages) != payload["page_count"]:
        raise ValueError("Page count mismatch")
    identity = "unsigned-not-authenticated"
    if trusted_public_key:
        if not signature or signature.get("algorithm") != "Ed25519":
            raise ValueError("Expected signed provenance; signature missing or unsupported")
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        key = serialization.load_pem_public_key(trusted_public_key.read_bytes())
        if not isinstance(key, Ed25519PublicKey):
            raise ValueError("Expected a trusted Ed25519 public key")
        raw = key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        if digest(raw) != signature["key_id"]:
            raise ValueError("Signing key does not match the independently trusted public key")
        key.verify(base64.b64decode(signature["value"], validate=True), canonical(payload))
        identity = "signature-verified-against-supplied-trusted-key"
    elif signature:
        raise ValueError("Signed manifest requires --trusted-public-key from an independent trusted channel")
    return {"integrity": "pass", "identity": identity, "document_id": payload["document_id"],
            "exam_quality": "not-assessed"}


def publish_pdf(source: Path, output: Path, *, provenance: bool = True) -> None:
    """Final renderer step. Renderer callers retain their existing overwrite policy."""
    output = output.resolve()
    manifest = output.with_suffix(".provenance.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not provenance:
        if manifest.exists():
            raise FileExistsError("An existing provenance manifest would become stale; choose a new output name")
        shutil.copyfile(source, output)
        return
    with tempfile.TemporaryDirectory(prefix="pdf-publish-") as work:
        marked = Path(work) / output.name
        mark_pdf(source, marked)
        marked_manifest = marked.with_suffix(".provenance.json")
        # Publish only after all before/after checks pass, leaving original PDFs
        # untouched if marking or verification fails.
        verify_pdf(marked, marked_manifest)
        shutil.copyfile(marked, output)
        shutil.copyfile(marked_manifest, manifest)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    mark = commands.add_parser("mark")
    mark.add_argument("input", type=Path)
    mark.add_argument("output", type=Path)
    mark.add_argument("--manifest", type=Path)
    mark.add_argument("--signing-key", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("input", type=Path)
    verify.add_argument("manifest", type=Path)
    verify.add_argument("--trusted-public-key", type=Path)
    args = parser.parse_args(argv)
    try:
        result = (mark_pdf(args.input, args.output, manifest=args.manifest, signing_key=args.signing_key)
                  if args.command == "mark" else verify_pdf(args.input, args.manifest, trusted_public_key=args.trusted_public_key))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Provenance check failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
