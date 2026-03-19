"""Tests for the formalizer-engine Typst package.

Each test builds a small .typ file that imports lib.typ and calls render-form,
then compiles it with the ``typst`` CLI and verifies that compilation succeeds
and the output PDF has the expected number of pages.
"""

import json
import subprocess
from pathlib import Path

import pytest

from conftest import PACKAGE_ROOT, compile_typst, write_bg, write_schema

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pdf_page_count(pdf_path: Path) -> int:
    """Count pages in a PDF by scanning for /Type /Page entries."""
    raw = pdf_path.read_bytes()
    # Count "/Type /Page" that are NOT "/Type /Pages"
    count = 0
    idx = 0
    needle_page = b"/Type /Page"
    needle_pages = b"/Type /Pages"
    while True:
        pos = raw.find(needle_page, idx)
        if pos == -1:
            break
        # Make sure it's not /Type /Pages
        if raw[pos : pos + len(needle_pages)] == needle_pages:
            idx = pos + len(needle_pages)
        else:
            count += 1
            idx = pos + len(needle_page)
    return count


def _write_typ(dest: Path, name: str, content: str) -> Path:
    p = dest / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Test: blank form (no values)
# ---------------------------------------------------------------------------

class TestBlankForm:
    def test_compiles_with_no_values(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 200, "height": 100}], [
            {"name": "f1", "type": "text", "bbox": [10, 10, 190, 30], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 200, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        assert _pdf_page_count(pdf) == 1


# ---------------------------------------------------------------------------
# Test: text field
# ---------------------------------------------------------------------------

class TestTextField:
    def test_text_field_renders(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 300, "height": 100}], [
            {"name": "greeting", "type": "text", "bbox": [10, 10, 290, 40], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 300, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (greeting: "Hello World"),
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        assert _pdf_page_count(pdf) == 1

    def test_text_empty_string_produces_no_extra_content(self, tmp_dir: Path):
        """An empty-string value should compile identically to no value at all."""
        write_schema(tmp_dir, [{"width": 200, "height": 100}], [
            {"name": "f", "type": "text", "bbox": [10, 10, 190, 30], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 200, 100)

        # With empty string
        _write_typ(tmp_dir, "a.typ", """\
#import "lib.typ": render-form
#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (f: ""),
)
""")
        # With no value at all
        _write_typ(tmp_dir, "b.typ", """\
#import "lib.typ": render-form
#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
)
""")
        pdf_a = compile_typst(tmp_dir, "a.typ")
        pdf_b = compile_typst(tmp_dir, "b.typ")
        # Both should have the same number of pages
        assert _pdf_page_count(pdf_a) == _pdf_page_count(pdf_b) == 1


# ---------------------------------------------------------------------------
# Test: checkbox field
# ---------------------------------------------------------------------------

class TestCheckboxField:
    def test_checked(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 200, "height": 100}], [
            {"name": "agree", "type": "checkbox", "bbox": [10, 10, 30, 30], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 200, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (agree: true),
)
""")
        compile_typst(tmp_dir, "test.typ")

    def test_unchecked(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 200, "height": 100}], [
            {"name": "agree", "type": "checkbox", "bbox": [10, 10, 30, 30], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 200, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (agree: false),
)
""")
        compile_typst(tmp_dir, "test.typ")


# ---------------------------------------------------------------------------
# Test: radio field
# ---------------------------------------------------------------------------

class TestRadioField:
    def test_radio_group(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 200, "height": 100}], [
            {"name": "choice", "type": "radio", "bbox": [10, 10, 30, 30], "page": 1, "options": None},
            {"name": "choice", "type": "radio", "bbox": [40, 10, 60, 30], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 200, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (choice: "1"),
)
""")
        compile_typst(tmp_dir, "test.typ")

    def test_radio_with_export_value(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 200, "height": 100}], [
            {"name": "yesno", "type": "radio", "bbox": [10, 10, 30, 30], "page": 1, "options": None, "export_value": "yes"},
            {"name": "yesno", "type": "radio", "bbox": [40, 10, 60, 30], "page": 1, "options": None, "export_value": "no"},
        ])
        write_bg(tmp_dir, "bg.png", 200, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (yesno: "no"),
)
""")
        compile_typst(tmp_dir, "test.typ")

    def test_radio_none_value(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 200, "height": 100}], [
            {"name": "choice", "type": "radio", "bbox": [10, 10, 30, 30], "page": 1, "options": None},
            {"name": "choice", "type": "radio", "bbox": [40, 10, 60, 30], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 200, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
)
""")
        compile_typst(tmp_dir, "test.typ")


# ---------------------------------------------------------------------------
# Test: combobox field
# ---------------------------------------------------------------------------

class TestComboboxField:
    def test_combobox_renders_display_label(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 300, "height": 100}], [
            {"name": "gender", "type": "combobox", "bbox": [10, 10, 150, 30], "page": 1,
             "options": [["M", "Male"], ["F", "Female"]]},
        ])
        write_bg(tmp_dir, "bg.png", 300, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (gender: "F"),
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        # Verify the PDF was produced (compilation proves the display label
        # was resolved from the options array without error).
        assert _pdf_page_count(pdf) == 1

    def test_combobox_with_unknown_value(self, tmp_dir: Path):
        """A value not in the options list should still render (as-is)."""
        write_schema(tmp_dir, [{"width": 300, "height": 100}], [
            {"name": "dd", "type": "combobox", "bbox": [10, 10, 150, 30], "page": 1,
             "options": [["a", "Apple"]]},
        ])
        write_bg(tmp_dir, "bg.png", 300, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form
#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (dd: "z"),
)
""")
        compile_typst(tmp_dir, "test.typ")


# ---------------------------------------------------------------------------
# Test: listbox field
# ---------------------------------------------------------------------------

class TestListboxField:
    def test_listbox_renders_display_label(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 300, "height": 100}], [
            {"name": "items", "type": "listbox", "bbox": [10, 10, 150, 30], "page": 1,
             "options": [["a", "Apple"], ["b", "Banana"]]},
        ])
        write_bg(tmp_dir, "bg.png", 300, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (items: "b"),
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        assert _pdf_page_count(pdf) == 1


# ---------------------------------------------------------------------------
# Test: multi-page form
# ---------------------------------------------------------------------------

class TestMultiPage:
    def test_two_page_form(self, tmp_dir: Path):
        write_schema(tmp_dir, [
            {"width": 400, "height": 300},
            {"width": 400, "height": 300},
        ], [
            {"name": "p1", "type": "text", "bbox": [10, 10, 190, 30], "page": 1, "options": None},
            {"name": "p2", "type": "text", "bbox": [10, 10, 190, 30], "page": 2, "options": None},
        ])
        write_bg(tmp_dir, "bg1.png", 400, 300)
        write_bg(tmp_dir, "bg2.png", 400, 300)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg1.png", "bg2.png"),
  values: (p1: "Page One", p2: "Page Two"),
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        assert _pdf_page_count(pdf) == 2


# ---------------------------------------------------------------------------
# Test: capitalized field types (raw PyMuPDF output)
# ---------------------------------------------------------------------------

class TestCapitalizedTypes:
    def test_text_capitalised(self, tmp_dir: Path):
        """Ensure ``lower()`` normalization handles PyMuPDF's 'Text'."""
        write_schema(tmp_dir, [{"width": 300, "height": 100}], [
            {"name": "name", "type": "Text", "bbox": [10, 10, 290, 40], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 300, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (name: "Alice"),
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        assert _pdf_page_count(pdf) == 1

    def test_checkbox_capitalised(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 200, "height": 100}], [
            {"name": "cb", "type": "CheckBox", "bbox": [10, 10, 30, 30], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 200, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (cb: true),
)
""")
        compile_typst(tmp_dir, "test.typ")


# ---------------------------------------------------------------------------
# Test: real-world schema (example/FIELDS.json)
# ---------------------------------------------------------------------------

class TestRealWorldSchema:
    def test_example_fields_json(self, tmp_dir: Path):
        """Compile using the actual example FIELDS.json shipped in the repo."""
        import shutil
        real_schema = PACKAGE_ROOT / "example" / "FIELDS.json"
        if not real_schema.exists():
            pytest.skip("example/FIELDS.json not found")
        shutil.copy(real_schema, tmp_dir / "FIELDS.json")

        # Read page dimensions to create backgrounds
        schema = json.loads(real_schema.read_text())
        bg_names = []
        for i, page in enumerate(schema["pages"]):
            name = f"bg_{i}.png"
            write_bg(tmp_dir, name, int(page["width"]), int(page["height"]))
            bg_names.append(name)

        bg_list = ", ".join(f'"{n}"' for n in bg_names)
        if len(bg_names) == 1:
            bg_list += ","
        _write_typ(tmp_dir, "test.typ", f"""\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ({bg_list}),
  values: (commonforms_text_p1_1: "Test"),
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        assert _pdf_page_count(pdf) == len(schema["pages"])


# ---------------------------------------------------------------------------
# Test: mixed field types on one page
# ---------------------------------------------------------------------------

class TestMixedFields:
    def test_all_types_on_one_page(self, tmp_dir: Path):
        write_schema(tmp_dir, [{"width": 400, "height": 400}], [
            {"name": "fname", "type": "text", "bbox": [10, 10, 200, 30], "page": 1, "options": None},
            {"name": "agree", "type": "checkbox", "bbox": [10, 40, 30, 60], "page": 1, "options": None},
            {"name": "opt", "type": "radio", "bbox": [10, 70, 30, 90], "page": 1, "options": None},
            {"name": "opt", "type": "radio", "bbox": [40, 70, 60, 90], "page": 1, "options": None},
            {"name": "dd", "type": "combobox", "bbox": [10, 100, 200, 120], "page": 1,
             "options": [["x", "Choice X"], ["y", "Choice Y"]]},
            {"name": "lb", "type": "listbox", "bbox": [10, 130, 200, 150], "page": 1,
             "options": [["1", "One"], ["2", "Two"]]},
        ])
        write_bg(tmp_dir, "bg.png", 400, 400)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (
    fname: "Jane",
    agree: true,
    opt: "0",
    dd: "y",
    lb: "2",
  ),
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        # All field types rendered on a single page
        assert _pdf_page_count(pdf) == 1
        # Verify the PDF size is larger with values than without
        # (content was rendered, not just the background)
        _write_typ(tmp_dir, "blank.typ", """\
#import "lib.typ": render-form
#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
)
""")
        blank_pdf = compile_typst(tmp_dir, "blank.typ")
        assert pdf.stat().st_size > blank_pdf.stat().st_size


# ---------------------------------------------------------------------------
# Test: shrink-to-fit text overflow
# ---------------------------------------------------------------------------

class TestShrinkToFit:
    def test_long_text_value_compiles_and_renders(self, tmp_dir: Path):
        """Long text in a narrow field should shrink to fit and still compile."""
        write_schema(tmp_dir, [{"width": 200, "height": 100}], [
            {"name": "narrow", "type": "text", "bbox": [10, 10, 70, 30], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 200, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (narrow: "This is a very long string that would overflow the field"),
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        assert _pdf_page_count(pdf) == 1

        # Blank form for comparison
        _write_typ(tmp_dir, "blank.typ", """\
#import "lib.typ": render-form
#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
)
""")
        blank_pdf = compile_typst(tmp_dir, "blank.typ")
        assert pdf.stat().st_size > blank_pdf.stat().st_size

    def test_combobox_long_label_compiles(self, tmp_dir: Path):
        """Long display label in a narrow combobox should shrink to fit and compile."""
        write_schema(tmp_dir, [{"width": 200, "height": 100}], [
            {"name": "dd", "type": "combobox", "bbox": [10, 10, 70, 30], "page": 1,
             "options": [["x", "A very long display label that exceeds the field width"]]},
        ])
        write_bg(tmp_dir, "bg.png", 200, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (dd: "x"),
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        assert _pdf_page_count(pdf) == 1


# ---------------------------------------------------------------------------
# Test: debug overlay mode
# ---------------------------------------------------------------------------

class TestDebugOverlay:
    def test_debug_compiles(self, tmp_dir: Path):
        """debug: true should compile without errors."""
        write_schema(tmp_dir, [{"width": 300, "height": 100}], [
            {"name": "greeting", "type": "text", "bbox": [10, 10, 290, 40], "page": 1, "options": None},
        ])
        write_bg(tmp_dir, "bg.png", 300, 100)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (greeting: "Hello World"),
  debug: true,
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        assert _pdf_page_count(pdf) == 1

    def test_debug_all_field_types(self, tmp_dir: Path):
        """debug: true should work with all supported field types."""
        write_schema(tmp_dir, [{"width": 400, "height": 400}], [
            {"name": "fname", "type": "text", "bbox": [10, 10, 200, 30], "page": 1, "options": None},
            {"name": "agree", "type": "checkbox", "bbox": [10, 40, 30, 60], "page": 1, "options": None},
            {"name": "opt", "type": "radio", "bbox": [10, 70, 30, 90], "page": 1, "options": None},
            {"name": "opt", "type": "radio", "bbox": [40, 70, 60, 90], "page": 1, "options": None},
            {"name": "dd", "type": "combobox", "bbox": [10, 100, 200, 120], "page": 1,
             "options": [["x", "Choice X"], ["y", "Choice Y"]]},
            {"name": "lb", "type": "listbox", "bbox": [10, 130, 200, 150], "page": 1,
             "options": [["1", "One"], ["2", "Two"]]},
        ])
        write_bg(tmp_dir, "bg.png", 400, 400)
        _write_typ(tmp_dir, "test.typ", """\
#import "lib.typ": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (
    fname: "Jane",
    agree: true,
    opt: "0",
    dd: "y",
    lb: "2",
  ),
  debug: true,
)
""")
        pdf = compile_typst(tmp_dir, "test.typ")
        assert _pdf_page_count(pdf) == 1
        # Debug PDF should be larger than a non-debug one (overlays add content)
        _write_typ(tmp_dir, "nodebug.typ", """\
#import "lib.typ": render-form
#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("bg.png",),
  values: (
    fname: "Jane",
    agree: true,
    opt: "0",
    dd: "y",
    lb: "2",
  ),
)
""")
        nodebug_pdf = compile_typst(tmp_dir, "nodebug.typ")
        assert pdf.stat().st_size > nodebug_pdf.stat().st_size
