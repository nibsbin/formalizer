"""Tests for the generate() public API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from formalizer import generate


class TestGenerate:
    """End-to-end generate() tests."""

    def test_produces_complete_package(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "my-form"
        generate(pdf=sample_pdf, out=out)
        assert (out / "FIELDS.json").exists()
        assert (out / "lib.typ").exists()
        assert (out / "typst.toml").exists()
        assert (out / "form.typ").exists()
        assert (out / "example.typ").exists()
        assert (out / "page1.png").exists()

    def test_default_name_from_out_basename(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "My Form"
        generate(pdf=sample_pdf, out=out)
        toml = (out / "typst.toml").read_text()
        assert 'name = "my-form"' in toml

    def test_custom_name(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "output"
        generate(pdf=sample_pdf, out=out, name="custom-pkg")
        toml = (out / "typst.toml").read_text()
        assert 'name = "custom-pkg"' in toml

    def test_error_if_out_exists(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "existing"
        out.mkdir()
        with pytest.raises(FileExistsError):
            generate(pdf=sample_pdf, out=out)

    def test_force_overwrites(self, sample_pdf: Path, tmp_path: Path):
        out = tmp_path / "existing"
        out.mkdir()
        (out / "stale.txt").write_text("old")
        generate(pdf=sample_pdf, out=out, force=True)
        assert not (out / "stale.txt").exists()
        assert (out / "FIELDS.json").exists()

    def test_missing_pdf_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            generate(pdf="nonexistent.pdf", out=tmp_path / "out")

    def test_multi_page_pdf(self, af4141_pdf: Path, tmp_path: Path):
        out = tmp_path / "af4141"
        generate(pdf=af4141_pdf, out=out)
        schema = json.loads((out / "FIELDS.json").read_text())
        assert len(schema["pages"]) == 2
        assert (out / "page1.png").exists()
        assert (out / "page2.png").exists()
