"""Shared test settings: the preflight never downloads or picks up installed body fonts during tests."""
import pytest


@pytest.fixture(autouse=True)
def _no_font_download(monkeypatch):
    monkeypatch.setenv("TAIWAN_EXAM_NO_FONT_DOWNLOAD", "1")
    # Tests never pick up the machine's installed 新細明體／標楷體 either.
    monkeypatch.setenv("TAIWAN_EXAM_NO_LOCAL_FONT", "1")
