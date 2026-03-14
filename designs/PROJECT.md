# Formalizer — Project Design

Orchestrate end-to-end reproduction of fillable PDF forms as self-contained Typst packages. Distributed as a PyPI package with both a Python API and an opinionated CLI.

## Goal

Given a fillable PDF, produce a portable Typst package that a user can edit to fill the form and compile to a near-perfect PDF replica.

## Architecture

| Layer | Component | Output |
|---|---|---|
| **Input** | User-supplied fillable PDF | — |
| **Extraction** | PyMuPDF | `FIELDS.json`, `page1.png`, `page2.png`, … |
| **Codegen** | formalizer orchestrator | `FIELDS.json`, `pageN.png`, `lib.typ`, `copied-form.typ` |
| **Output** | Self-contained Typst package | User edits and compiles with `typst compile` |

## formalizer-engine

The Typst rendering engine lives in-tree (monorepo). At codegen time, its `lib.typ` is **copied** into the generated package so the output is fully self-contained — no Typst registry access or network required.

Engine-specific tests and examples are colocated under the engine directory:

```
formalizer-engine/
  lib.typ
  tests/       # Typst-based engine tests
  example/     # example schema + backgrounds for manual testing
```

Orchestrator tests (extraction, codegen) live separately at the repo root under `tests/` and use `pytest`.

## Workflow

### 1. User Inputs

**CLI:**
```sh
# Package name defaults to output directory basename ("my-form")
formalizer --pdf form.pdf --out ./my-form

# Override the package name
formalizer --pdf form.pdf --out ./my-form --name custom-name
```

**API:**
```python
from formalizer import generate

# Package name defaults to output directory basename ("my-form")
generate(pdf="form.pdf", out="./my-form")

# Override the package name
generate(pdf="form.pdf", out="./my-form", name="custom-name")
```

Key parameters:
- `pdf` — fillable PDF to replicate
- `out` — destination directory for the generated package (files are written directly here, no subdirectory is created); errors if it already exists (pass `-f` / `force=True` to delete and overwrite)
- `name` — *(optional)* override the package name in `typst.toml` (defaults to `--out` basename, slugified)

### 2. Extraction Phase

PyMuPDF reads the PDF and produces:

- `FIELDS.json` — field schema (names, types, bounding boxes, options); see [FIELD_SCHEMA.md](FIELD_SCHEMA.md)
- `page1.png`, `page2.png`, … — rasterized page backgrounds at 250 dpi

### 3. Codegen Phase

The orchestrator copies a template project skeleton and injects dynamic content (field definitions, dummy values, metadata) to produce a self-contained Typst package in `--out`:

```
<out>/
  typst.toml      # package manifest
  lib.typ         # rendering engine (copied from formalizer-engine)
  FIELDS.json     # extracted field schema
  page1.png       # page backgrounds
  form.typ        # generated API wrapper (do not edit)
  example.typ     # generated template pre-filled with dummy data
```

The `typst.toml` `name` field is derived from the `--out` basename (slugified) unless `--name` is provided.

`form.typ` defines a typed `form()` function (one named parameter per field). `example.typ` calls it with realistic dummy values and is the user's starting point. See [FORMALIZER_ENGINE.md](FORMALIZER_ENGINE.md) for details.

At the end of codegen, the CLI automatically compiles `example.typ` into `out/example.pdf` (gitignored) so the user can immediately preview the result.

### 4. Fill Phase (user)

The user edits `example.typ` (or copies it), replaces the dummy values with real ones, then compiles:

```sh
typst compile example.typ out/filled-form.pdf
```

## Distribution

Formalizer is published to PyPI as `formalizer`. Install with:

```sh
pip install formalizer
# or
uv add formalizer
```

The package exposes:
- `formalizer` — CLI entry point
- `formalizer` Python module — public API for programmatic use

## Tooling

| Tool | Role |
|---|---|
| `uv` | Python package manager; manages dependencies and builds the PyPI package |
| `pytest` | Test runner for extraction and codegen logic |
| `typst` CLI | Compiles the generated package to PDF |

## References

- [FIELDS_SCHEMA.md](./FIELDS_SCHEMA.md) — `FIELDS.json` schema contract between extraction and rendering
- [FORMALIZER_ENGINE.md](./FORMALIZER_ENGINE.md) — rendering engine API and generated package structure
