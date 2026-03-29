"""Test that SVG backgrounds produce smaller output PDFs than the PNG baseline.

Measured sizes when formalizing samples/af4141-fillable.pdf:
  Before last commit (PNG at 250 DPI): example.pdf ~ 259,353 bytes
  After  last commit (SVG vector):     example.pdf ~ 137,403 bytes
  Reduction: ~47%
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest


# PNG-era baseline measured from the commit before fe346c4
_PNG_BASELINE_BYTES = 259_353
# Allow 20% headroom above the SVG result for font/typst-version variance
_SVG_SIZE_THRESHOLD = int(_PNG_BASELINE_BYTES * 0.80)  # 207,482 bytes


@pytest.fixture()
def requires_typst():
    if not shutil.which("typst"):
        pytest.skip("typst not installed")


class TestPDFSizeAfterSVGSwitch:
    """Verify the SVG-background change meaningfully reduces output PDF size."""

    def test_af4141_pdf_smaller_than_png_baseline(
        self, af4141_pdf: Path, tmp_path: Path, requires_typst: None
    ):
        out = tmp_path / "af4141-svg"
        result = subprocess.run(
            [
                sys.executable, "-m", "formalizer.cli",
                "--pdf", str(af4141_pdf),
                "--out", str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

        pdf = out / "out" / "example.pdf"
        assert pdf.exists(), "example.pdf was not produced"

        size = pdf.stat().st_size
        assert size < _SVG_SIZE_THRESHOLD, (
            f"example.pdf is {size:,} bytes, expected < {_SVG_SIZE_THRESHOLD:,} bytes "
            f"(PNG baseline was {_PNG_BASELINE_BYTES:,} bytes). "
            "SVG backgrounds may not be in effect."
        )
