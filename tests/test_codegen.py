"""Tests for the codegen module."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from formalizer.codegen import _slugify, codegen


# ---------------------------------------------------------------------------
# Slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert _slugify("my-form") == "my-form"

    def test_uppercase(self):
        assert _slugify("My Form") == "my-form"

    def test_special_chars(self):
        assert _slugify("hello_world!") == "hello-world"

    def test_leading_trailing_hyphens(self):
        assert _slugify("--foo--") == "foo"

    def test_empty(self):
        assert _slugify("") == "package"


# ---------------------------------------------------------------------------
# Codegen
# ---------------------------------------------------------------------------

def _minimal_schema(
    *,
    fields: list[dict] | None = None,
    pages: list[dict] | None = None,
) -> dict:
    return {
        "pages": pages or [{"width": 200, "height": 100}],
        "fields": fields or [
            {"name": "f1", "type": "text", "bbox": [10, 10, 190, 30], "page": 1, "options": None},
        ],
    }


class TestCodegen:
    def test_creates_expected_files(self, tmp_path: Path):
        schema = _minimal_schema()
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "test-pkg")
        assert (tmp_path / "lib.typ").exists()
        assert (tmp_path / "typst.toml").exists()
        assert (tmp_path / "form.typ").exists()
        assert (tmp_path / "example.typ").exists()

    def test_typst_toml_name(self, tmp_path: Path):
        schema = _minimal_schema()
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "custom-name")
        toml = (tmp_path / "typst.toml").read_text()
        assert 'name = "custom-name"' in toml

    def test_form_typ_imports_lib(self, tmp_path: Path):
        schema = _minimal_schema()
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        form = (tmp_path / "form.typ").read_text()
        assert '#import "lib.typ": render-form' in form

    def test_form_typ_has_field_params(self, tmp_path: Path):
        schema = _minimal_schema(fields=[
            {"name": "first_name", "type": "text", "bbox": [0, 0, 100, 20], "page": 1, "options": None},
            {"name": "agree", "type": "checkbox", "bbox": [0, 0, 20, 20], "page": 1, "options": None},
        ])
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        form = (tmp_path / "form.typ").read_text()
        assert "first_name:" in form
        assert "agree:" in form

    def test_radio_deduplicated(self, tmp_path: Path):
        """Multiple radio buttons with the same name → one parameter."""
        schema = _minimal_schema(fields=[
            {"name": "choice", "type": "radio", "bbox": [10, 10, 30, 30], "page": 1, "options": None},
            {"name": "choice", "type": "radio", "bbox": [40, 10, 60, 30], "page": 1, "options": None},
        ])
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        form = (tmp_path / "form.typ").read_text()
        assert form.count("choice:") == 2  # one in params, one in values dict

    def test_example_typ_imports_form(self, tmp_path: Path):
        schema = _minimal_schema()
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        example = (tmp_path / "example.typ").read_text()
        assert '#import "form.typ": form' in example

    def test_combobox_default_is_first_option(self, tmp_path: Path):
        schema = _minimal_schema(fields=[
            {"name": "dd", "type": "combobox", "bbox": [0, 0, 100, 20], "page": 1,
             "options": [["M", "Male"], ["F", "Female"]]},
        ])
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        form = (tmp_path / "form.typ").read_text()
        assert '"M"' in form  # default should be first option export value

    def test_multi_page_backgrounds(self, tmp_path: Path):
        schema = _minimal_schema(pages=[
            {"width": 300, "height": 200},
            {"width": 300, "height": 200},
        ])
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        form = (tmp_path / "form.typ").read_text()
        assert '"page1.png"' in form
        assert '"page2.png"' in form


class TestCodegenCompiles:
    """Verify the generated package compiles with typst."""

    def test_generated_package_compiles(self, tmp_path: Path):
        from formalizer.extract import extract

        pdf = Path(__file__).resolve().parent.parent / "designs" / "reference" / "example" / "all_fields_sample.pdf"
        if not pdf.exists():
            pytest.skip("sample PDF not found")

        schema = extract(pdf, tmp_path)
        codegen(schema, tmp_path, "test-pkg")

        result = subprocess.run(
            ["typst", "compile", "example.typ", "example.pdf"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"typst compile failed:\n{result.stderr}"
        assert (tmp_path / "example.pdf").exists()
