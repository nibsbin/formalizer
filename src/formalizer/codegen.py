"""Generate a self-contained Typst package from an extracted field schema."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

# Resolve the in-tree engine lib.typ
_ENGINE_LIB = Path(__file__).resolve().parent.parent.parent / "formalizer-engine" / "lib.typ"


def _slugify(text: str) -> str:
    """Convert *text* to a Typst-safe package name slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "package"


def _typst_default(field_type: str, options: list | None) -> str:
    """Return a Typst literal for the default value of a field type."""
    if field_type == "text":
        return '""'
    if field_type == "checkbox":
        return "false"
    if field_type == "radio":
        return "none"
    if field_type in ("combobox", "listbox"):
        if options:
            return _quote(options[0][0])
        return '""'
    return '""'


def _typst_dummy(field_type: str, field_name: str, options: list | None) -> str | None:
    """Return a Typst literal for a realistic dummy value, or ``None`` to omit."""
    if field_type == "text":
        return _quote(field_name)
    if field_type == "checkbox":
        return "true"
    if field_type == "radio":
        return None  # radio defaults to none — omit from example
    if field_type in ("combobox", "listbox"):
        if options:
            return _quote(options[0][0])
        return None
    return None


def _quote(value: str) -> str:
    """Wrap *value* in Typst double-quotes, escaping internal quotes."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _typst_ident(name: str) -> str:
    """Sanitise a field name into a valid Typst identifier."""
    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if name and name[0].isdigit():
        name = "_" + name
    return name or "_field"


def _options_comment(options: list | None) -> str:
    """Build a short ``[A, B]`` comment suffix for combobox/listbox fields."""
    if not options:
        return ""
    labels = [opt[1] for opt in options[:4]]
    suffix = ", ".join(labels)
    if len(options) > 4:
        suffix += ", …"
    return f" [{suffix}]"


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def codegen(schema: dict, out: Path, name: str) -> None:
    """Generate a Typst package in *out* from *schema*.

    *name* is the package name written into ``typst.toml``.
    """
    # --- lib.typ (copy engine) ---
    engine_lib = _ENGINE_LIB
    if not engine_lib.exists():
        raise FileNotFoundError(
            f"Engine lib.typ not found at {engine_lib}.  "
            "Ensure formalizer-engine/ is present in the repository root."
        )
    shutil.copy2(engine_lib, out / "lib.typ")

    # --- typst.toml ---
    (out / "typst.toml").write_text(
        f'[package]\nname = "{name}"\nversion = "0.1.0"\n'
        f'entrypoint = "lib.typ"\nauthors = []\nlicense = "Apache-2.0"\n'
        f'description = "Generated form package"\n'
    )

    # --- Deduplicate fields (radio groups share names) ---
    seen: dict[str, dict] = {}
    for f in schema["fields"]:
        if f["name"] not in seen:
            seen[f["name"]] = f

    # Build background list
    num_pages = len(schema["pages"])
    bg_names = [f'"page{i + 1}.png"' for i in range(num_pages)]
    bg_list = ", ".join(bg_names)

    # --- form.typ ---
    params: list[str] = []
    values_entries: list[str] = []
    for field_name, f in seen.items():
        ident = _typst_ident(field_name)
        ftype = f["type"].lower()
        default = _typst_default(ftype, f.get("options"))
        comment = f"// {ftype}{_options_comment(f.get('options'))}"
        params.append(f"  {ident}: {default},  {comment}")
        values_entries.append(f"    {ident}: {ident}")

    params_block = "\n".join(params)
    values_block = ",\n".join(values_entries)

    form_typ = (
        '// form.typ (generated — do not edit)\n'
        '#import "lib.typ": render-form\n\n'
        f"#let form(\n{params_block}\n) = render-form(\n"
        f'  schema: json("FIELDS.json"),\n'
        f"  backgrounds: ({bg_list},),\n"
        f"  values: (\n{values_block},\n  ),\n)\n"
    )
    (out / "form.typ").write_text(form_typ)

    # --- example.typ ---
    example_args: list[str] = []
    for field_name, f in seen.items():
        ident = _typst_ident(field_name)
        ftype = f["type"].lower()
        dummy = _typst_dummy(ftype, field_name, f.get("options"))
        if dummy is not None:
            example_args.append(f"  {ident}: {dummy}")

    args_block = ",\n".join(example_args)

    example_typ = (
        "// example.typ (edit this file to fill the form)\n"
        '#import "form.typ": form\n\n'
    )
    if args_block:
        example_typ += f"#form(\n{args_block},\n)\n"
    else:
        example_typ += "#form()\n"

    (out / "example.typ").write_text(example_typ)
