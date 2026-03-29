"""Tests for the extraction module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from formalizer.extract import extract


class TestExtract:
    """Extraction from a fillable PDF → FIELDS.json + page SVGs."""

    def test_fields_json_created(self, sample_pdf: Path, tmp_path: Path):
        schema = extract(sample_pdf, tmp_path)
        assert (tmp_path / "FIELDS.json").exists()
        loaded = json.loads((tmp_path / "FIELDS.json").read_text())
        assert loaded == schema

    def test_pages_key(self, sample_pdf: Path, tmp_path: Path):
        schema = extract(sample_pdf, tmp_path)
        assert "pages" in schema
        assert len(schema["pages"]) >= 1
        page = schema["pages"][0]
        assert "width" in page and "height" in page
        assert page["width"] > 0 and page["height"] > 0

    def test_fields_key(self, sample_pdf: Path, tmp_path: Path):
        schema = extract(sample_pdf, tmp_path)
        assert "fields" in schema
        assert len(schema["fields"]) >= 1

    def test_field_structure(self, sample_pdf: Path, tmp_path: Path):
        schema = extract(sample_pdf, tmp_path)
        for f in schema["fields"]:
            assert "name" in f
            assert "type" in f
            assert "bbox" in f
            assert "page" in f
            assert "options" in f
            assert len(f["bbox"]) == 4
            assert f["page"] >= 1

    def test_field_types_normalized(self, sample_pdf: Path, tmp_path: Path):
        """PyMuPDF types like 'CheckBox' should be normalized to 'checkbox'."""
        schema = extract(sample_pdf, tmp_path)
        valid_types = {"text", "checkbox", "radio", "combobox", "listbox"}
        for f in schema["fields"]:
            assert f["type"] in valid_types, f"unexpected type: {f['type']}"

    def test_push_buttons_excluded(self, sample_pdf: Path, tmp_path: Path):
        """Push-button widgets should not appear in FIELDS.json."""
        schema = extract(sample_pdf, tmp_path)
        for f in schema["fields"]:
            assert f["type"] != "button", "push buttons should be excluded"

    def test_page_svgs_created(self, sample_pdf: Path, tmp_path: Path):
        schema = extract(sample_pdf, tmp_path)
        for i in range(len(schema["pages"])):
            svg = tmp_path / f"page{i + 1}.svg"
            assert svg.exists(), f"Missing: {svg.name}"
            assert svg.stat().st_size > 0

    def test_options_present_for_combobox(self, sample_pdf: Path, tmp_path: Path):
        schema = extract(sample_pdf, tmp_path)
        combo_fields = [f for f in schema["fields"] if f["type"] == "combobox"]
        for f in combo_fields:
            assert f["options"] is not None
            assert len(f["options"]) > 0
            for opt in f["options"]:
                assert len(opt) == 2  # [export_value, display_label]


class TestExtractMultiPage:
    """Multi-page PDF extraction."""

    def test_multi_page_svgs(self, af4141_pdf: Path, tmp_path: Path):
        schema = extract(af4141_pdf, tmp_path)
        assert len(schema["pages"]) == 2
        assert (tmp_path / "page1.svg").exists()
        assert (tmp_path / "page2.svg").exists()

    def test_fields_span_pages(self, af4141_pdf: Path, tmp_path: Path):
        schema = extract(af4141_pdf, tmp_path)
        pages_with_fields = {f["page"] for f in schema["fields"]}
        assert 1 in pages_with_fields
        assert 2 in pages_with_fields
