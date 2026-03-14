"""Tests for the codegen module."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from formalizer.codegen import _slugify, _humanise_field_name, _unique_ident, _typst_ident, codegen


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
        assert (tmp_path / "debug.typ").exists()

    def test_form_typ_has_debug_param(self, tmp_path: Path):
        schema = _minimal_schema()
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        form = (tmp_path / "form.typ").read_text()
        assert "debug: false" in form
        assert "debug: debug" in form

    def test_debug_typ_has_debug_true(self, tmp_path: Path):
        schema = _minimal_schema()
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        debug = (tmp_path / "debug.typ").read_text()
        assert "debug: true" in debug
        assert '#import "form.typ": form' in debug

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

    def test_typst_toml_author_formalizer(self, tmp_path: Path):
        """Gap 5: generated typst.toml should use 'formalizer' as author."""
        schema = _minimal_schema()
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        toml = (tmp_path / "typst.toml").read_text()
        assert 'authors = ["formalizer"]' in toml
        assert 'description = "Fillable form package generated by formalizer"' in toml

    def test_radio_marked_experimental(self, tmp_path: Path):
        """Gap 7: radio fields should be marked as experimental in form.typ."""
        schema = _minimal_schema(fields=[
            {"name": "choice", "type": "radio", "bbox": [10, 10, 30, 30], "page": 1, "options": None},
            {"name": "choice", "type": "radio", "bbox": [40, 10, 60, 30], "page": 1, "options": None},
        ])
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        form = (tmp_path / "form.typ").read_text()
        assert "radio (experimental)" in form

    def test_ident_collision_dedup(self, tmp_path: Path):
        """Gap 6: fields that collide after sanitisation get unique idents."""
        schema = _minimal_schema(fields=[
            {"name": "first-name", "type": "text", "bbox": [0, 0, 100, 20], "page": 1, "options": None},
            {"name": "first.name", "type": "text", "bbox": [0, 30, 100, 50], "page": 1, "options": None},
        ])
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        form = (tmp_path / "form.typ").read_text()
        assert "first_name:" in form
        assert "first_name_2:" in form
        # The renamed field should have a comment
        assert 'renamed from "first.name"' in form

    def test_humanised_dummy_text(self, tmp_path: Path):
        """Gap 8: text dummy values should be humanised, not raw field names."""
        schema = _minimal_schema(fields=[
            {"name": "first_name", "type": "text", "bbox": [0, 0, 100, 20], "page": 1, "options": None},
        ])
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        example = (tmp_path / "example.typ").read_text()
        assert '"First Name"' in example

    def test_humanised_machine_name_fallback(self, tmp_path: Path):
        """Gap 8: machine-generated field names should produce humanised text."""
        schema = _minimal_schema(fields=[
            {"name": "commonforms_text_p1_1", "type": "text", "bbox": [0, 0, 100, 20], "page": 1, "options": None},
        ])
        (tmp_path / "FIELDS.json").write_text(json.dumps(schema))
        codegen(schema, tmp_path, "pkg")
        example = (tmp_path / "example.typ").read_text()
        # "commonforms_text_p1_1" → strip prefix → "text_p1_1" → strip page/index → "text" → title → "Text"
        assert '"Text"' in example


# ---------------------------------------------------------------------------
# Humanise field name
# ---------------------------------------------------------------------------

class TestHumaniseFieldName:
    def test_simple_underscore(self):
        assert _humanise_field_name("first_name") == "First Name"

    def test_camel_case(self):
        assert _humanise_field_name("firstName") == "First Name"

    def test_machine_prefix_stripped(self):
        result = _humanise_field_name("commonforms_text_p1_1")
        assert result == "Text"

    def test_trailing_digits_stripped(self):
        assert _humanise_field_name("field123") == "Field"

    def test_empty_fallback(self):
        assert _humanise_field_name("123") == "Sample Text"

    def test_hyphen_to_space(self):
        assert _humanise_field_name("last-name") == "Last Name"


# ---------------------------------------------------------------------------
# Unique ident
# ---------------------------------------------------------------------------

class TestUniqueIdent:
    def test_no_collision(self):
        seen: set[str] = set()
        assert _unique_ident("foo", seen) == "foo"
        assert "foo" in seen

    def test_collision_appends_suffix(self):
        seen: set[str] = set()
        assert _unique_ident("foo", seen) == "foo"
        assert _unique_ident("foo", seen) == "foo_2"
        assert _unique_ident("foo", seen) == "foo_3"

    def test_different_names_same_ident(self):
        """first-name and first.name both sanitise to first_name."""
        seen: set[str] = set()
        assert _unique_ident("first-name", seen) == "first_name"
        assert _unique_ident("first.name", seen) == "first_name_2"


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

    def test_generated_debug_compiles(self, tmp_path: Path):
        from formalizer.extract import extract

        pdf = Path(__file__).resolve().parent.parent / "designs" / "reference" / "example" / "all_fields_sample.pdf"
        if not pdf.exists():
            pytest.skip("sample PDF not found")

        schema = extract(pdf, tmp_path)
        codegen(schema, tmp_path, "test-pkg")

        result = subprocess.run(
            ["typst", "compile", "debug.typ", "debug.pdf"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"typst compile debug.typ failed:\n{result.stderr}"
        assert (tmp_path / "debug.pdf").exists()
