"""Extract field schema and page backgrounds from a fillable PDF using PyMuPDF."""

from __future__ import annotations

import json
from pathlib import Path

import fitz  # pymupdf

# Map PyMuPDF field_type_string → FIELDS_SCHEMA.md type
_TYPE_MAP: dict[str, str | None] = {
    "Text": "text",
    "CheckBox": "checkbox",
    "RadioButton": "radio",
    "ComboBox": "combobox",
    "ListBox": "listbox",
    "Button": None,  # push-buttons are skipped
}

_RENDER_DPI = 250


def extract(pdf: str | Path, out: Path) -> dict:
    """Read *pdf* and write ``FIELDS.json`` + page PNGs into *out*.

    Returns the parsed schema dict.
    """
    doc = fitz.open(str(pdf))

    pages: list[dict] = [
        {"width": page.rect.width, "height": page.rect.height} for page in doc
    ]

    fields: list[dict] = []
    for page in doc:
        for widget in page.widgets():
            raw_type = widget.field_type_string
            mapped = _TYPE_MAP.get(raw_type)
            if mapped is None:
                continue  # skip unsupported types (e.g. push buttons)

            raw_opts = widget.choice_values
            options = [list(pair) for pair in raw_opts] if raw_opts else None

            field: dict = {
                "name": widget.field_name,
                "type": mapped,
                "bbox": list(widget.rect),
                "page": page.number + 1,
                "options": options,
            }

            # Radio buttons: try to capture export value
            if mapped == "radio":
                states = widget.button_states()
                # button_states() returns a dict {"normal": [...], "down": [...]}
                # The "normal" list typically has the export value(s)
                if states:
                    normal = states.get("normal", [])
                    on_states = [s for s in normal if s != "Off"]
                    if on_states:
                        field["export_value"] = on_states[0]

            fields.append(field)

    schema = {"pages": pages, "fields": fields}

    # Write FIELDS.json
    (out / "FIELDS.json").write_text(json.dumps(schema, indent=2))

    # Rasterize each page as a PNG background
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=_RENDER_DPI)
        pix.save(str(out / f"page{i + 1}.png"))

    doc.close()
    return schema
