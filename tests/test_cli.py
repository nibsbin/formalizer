"""Tests for the CLI entry point."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from formalizer.cli import main


class TestCLI:
    def test_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "formalizer.cli", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--pdf" in result.stdout
        assert "--out" in result.stdout

    def test_missing_pdf_exits_nonzero(self, tmp_path: Path):
        result = subprocess.run(
            [sys.executable, "-m", "formalizer.cli", "--pdf", "nope.pdf", "--out", str(tmp_path / "out")],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_basic_run(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "cli-test"
        result = subprocess.run(
            [sys.executable, "-m", "formalizer.cli", "--pdf", str(sample_pdf), "--out", str(out)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (out / "FIELDS.json").exists()
        assert (out / "form.typ").exists()

    def test_force_flag(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "cli-force"
        out.mkdir()
        result = subprocess.run(
            [sys.executable, "-m", "formalizer.cli",
             "--pdf", str(sample_pdf), "--out", str(out), "-f"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_name_flag(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "cli-name"
        result = subprocess.run(
            [sys.executable, "-m", "formalizer.cli",
             "--pdf", str(sample_pdf), "--out", str(out), "--name", "my-custom"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        toml = (out / "typst.toml").read_text()
        assert 'name = "my-custom"' in toml

    def test_main_callable(self, sample_pdf: Path, tmp_path: Path):
        """The main() function can be called directly with argv."""
        out = tmp_path / "direct"
        main(["--pdf", str(sample_pdf), "--out", str(out)])
        assert (out / "FIELDS.json").exists()

    def test_debug_pdf_produced(self, sample_pdf: Path, tmp_path: Path):
        """CLI should produce both example.pdf and debug.pdf."""
        out = tmp_path / "cli-debug"
        result = subprocess.run(
            [sys.executable, "-m", "formalizer.cli",
             "--pdf", str(sample_pdf), "--out", str(out)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (out / "example.pdf").exists()
        assert (out / "debug.pdf").exists()
