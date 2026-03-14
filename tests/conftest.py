"""Shared fixtures for orchestrator tests."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PDF = REPO_ROOT / "designs" / "reference" / "example" / "all_fields_sample.pdf"
AF4141_PDF = REPO_ROOT / "designs" / "reference" / "example" / "af4141-fillable.pdf"


@pytest.fixture()
def sample_pdf() -> Path:
    """Return the path to the small all-fields sample PDF."""
    if not SAMPLE_PDF.exists():
        pytest.skip("all_fields_sample.pdf not found in designs/reference/example/")
    return SAMPLE_PDF


@pytest.fixture()
def af4141_pdf() -> Path:
    """Return the path to the multi-page AF4141 PDF."""
    if not AF4141_PDF.exists():
        pytest.skip("af4141-fillable.pdf not found in designs/reference/example/")
    return AF4141_PDF
