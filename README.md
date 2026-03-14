# formalizer

Convert a fillable PDF into a self-contained [Typst](https://typst.app) package that anyone can edit and compile to a pixel-perfect replica.

## How it works

1. **Extract** — PyMuPDF reads the PDF and outputs `FIELDS.json` (field schema) and `pageN.png` background images.
2. **Codegen** — The orchestrator writes a Typst package with a typed `form()` function and a pre-filled `example.typ`.
3. **Fill** — Edit `example.typ`, replace the dummy values with real ones, compile with `typst compile`.

```
<out>/
  typst.toml      # package manifest
  lib.typ         # rendering engine
  FIELDS.json     # extracted field schema
  page1.png       # rasterized page backgrounds
  form.typ        # generated API wrapper (do not edit)
  example.typ     # your starting point — edit this
```

## Requirements

- Python ≥ 3.10
- [typst CLI](https://github.com/typst/typst/releases) (for compiling the output package)

## Installation

```sh
pip install formalizer
# or
uv add formalizer
```

## Usage

### CLI

```sh
# Generate a package (name defaults to --out basename)
formalizer --pdf form.pdf --out ./my-form

# Override the package name
formalizer --pdf form.pdf --out ./my-form --name custom-name

# Overwrite an existing output directory
formalizer --pdf form.pdf --out ./my-form -f
```

After generation the CLI auto-compiles `example.typ` → `example.pdf` so you can immediately preview the result.

### Python API

```python
from formalizer import generate

# Minimal — name defaults to the out directory basename
generate(pdf="form.pdf", out="./my-form")

# With options
generate(pdf="form.pdf", out="./my-form", name="custom-name", force=True)
```

### Filling the form

Edit the generated `example.typ` and pass real values to `form()`:

```typst
#import "form.typ": form

#form(
  first_name:  "Jane Smith",
  agree_terms: true,
  gender:      "F",
)
```

Then compile:

```sh
typst compile example.typ filled-form.pdf
```

## Development

```sh
# Install in editable mode
pip install -e .

# Run tests
pip install pytest
pytest tests/ -v
```

Tests that invoke the `typst` CLI (`test_cli`, `test_codegen_compiles`) are skipped automatically if `typst` is not on `PATH`.

## License

Apache 2.0
