import json
import sys
from pathlib import Path

import fitz
import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pdf_provenance import mark_pdf, page_fingerprints, publish_pdf, verify_pdf
from package_skill import ROOT, should_include


def example(path):
    with fitz.open() as doc:
        for i in range(2):
            page = doc.new_page()
            page.insert_text((40, 80), f"Question {i + 1}: x + 2 = 5", fontsize=11)
            page.draw_rect(fitz.Rect(40, 110, 190, 155), color=(0, 0, 0), width=0.7)
        doc.set_metadata({"title": "An existing title", "author": "An existing author"})
        doc.save(path)
    return path


def test_mark_is_pixel_identical_and_preserves_metadata(tmp_path):
    source = example(tmp_path / "source.pdf")
    before = source.read_bytes()
    result = mark_pdf(source, tmp_path / "marked.pdf")
    assert source.read_bytes() == before
    assert result["pages_unchanged"] == 2
    assert page_fingerprints(source) == page_fingerprints(Path(result["pdf"]))
    reader = PdfReader(result["pdf"])
    assert reader.metadata.title == "An existing title"
    assert reader.metadata.author == "An existing author"
    checked = verify_pdf(Path(result["pdf"]), Path(result["manifest"]))
    assert checked["identity"] == "unsigned-not-authenticated"
    assert checked["exam_quality"] == "not-assessed"


def test_refuses_overwrite_and_inplace(tmp_path):
    source = example(tmp_path / "source.pdf")
    with pytest.raises(ValueError):
        mark_pdf(source, source)
    with pytest.raises(FileExistsError):
        mark_pdf(source, example(tmp_path / "existing.pdf"))


def test_tamper_fails_and_each_export_has_new_id(tmp_path):
    source = example(tmp_path / "source.pdf")
    first = mark_pdf(source, tmp_path / "first.pdf")
    second = mark_pdf(source, tmp_path / "second.pdf")
    assert first["document_id"] != second["document_id"]
    with Path(first["pdf"]).open("ab") as target:
        target.write(b"\n%modified\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_pdf(Path(first["pdf"]), Path(first["manifest"]))


def test_optional_signing_requires_independently_trusted_key(tmp_path):
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    source = example(tmp_path / "source.pdf")
    key = Ed25519PrivateKey.generate()  # Ephemeral test-only key; never a production key.
    private, public = tmp_path / "test-private.pem", tmp_path / "test-public.pem"
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    public.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    result = mark_pdf(source, tmp_path / "signed.pdf", signing_key=private)
    pdf, manifest = Path(result["pdf"]), Path(result["manifest"])
    with pytest.raises(ValueError, match="independent trusted channel"):
        verify_pdf(pdf, manifest)
    assert verify_pdf(pdf, manifest, trusted_public_key=public)["identity"].startswith("signature-verified")
    data = json.loads(manifest.read_text())
    data["signature"] = None
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="signature missing"):
        verify_pdf(pdf, manifest, trusted_public_key=public)


def test_packager_excludes_known_secret_locations_and_suffixes():
    for name in [".secrets/key.txt", "secrets/key.txt", "assets/publisher-private.pem", "assets/sign.key", "assets/sign.pfx"]:
        assert not should_include(ROOT / name)


def test_publish_optout_and_default(tmp_path):
    source = example(tmp_path / "source.pdf")
    output = tmp_path / "export.pdf"
    publish_pdf(source, output)
    manifest = output.with_suffix(".provenance.json")
    assert json.loads(manifest.read_text())["payload"]["filename"] == output.name
    assert verify_pdf(output, manifest)["integrity"] == "pass"
    with pytest.raises(FileExistsError, match="stale"):
        publish_pdf(source, output, provenance=False)
    plain = tmp_path / "plain.pdf"
    publish_pdf(source, plain, provenance=False)
    assert plain.read_bytes() == source.read_bytes()


def test_rejects_encrypted_or_signature_fields(tmp_path):
    source = example(tmp_path / "source.pdf")
    encrypted = tmp_path / "encrypted.pdf"
    writer = PdfWriter(clone_from=source)
    writer.encrypt("test-password")
    writer.write(encrypted)
    with pytest.raises(ValueError, match="Encrypted"):
        mark_pdf(encrypted, tmp_path / "no.pdf")
    signed = tmp_path / "signature-field.pdf"
    writer = PdfWriter(clone_from=source)
    field = DictionaryObject({NameObject("/FT"): NameObject("/Sig"), NameObject("/T"): TextStringObject("signature")})
    writer.root_object[NameObject("/AcroForm")] = DictionaryObject({NameObject("/Fields"): ArrayObject([writer._add_object(field)])})
    writer.write(signed)
    with pytest.raises(ValueError, match="signature fields"):
        mark_pdf(signed, tmp_path / "no.pdf")
