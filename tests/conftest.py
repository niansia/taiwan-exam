"""Shared test settings: the preflight never downloads the serif body font during tests."""
import pytest


@pytest.fixture(autouse=True)
def _no_font_download(monkeypatch):
    monkeypatch.setenv("TAIWAN_EXAM_NO_FONT_DOWNLOAD", "1")
