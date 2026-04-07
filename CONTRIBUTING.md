# Contributing to Formalizer

Thanks for your interest in contributing! Here's everything you need to get started.

## Prerequisites

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/) (package manager)
- [Typst CLI](https://github.com/typst/typst/releases) — optional, but needed to run the full test suite

## Setup

```sh
# Clone the repo
git clone https://github.com/nibsbin/formalizer.git
cd formalizer

# Create a venv and install in editable mode
uv sync
```

## Running Tests

```sh
uv run pytest tests/ -v
```

> **Note:** Tests that invoke the `typst` CLI (`test_cli`, `test_codegen_compiles`) are skipped automatically if `typst` is not on `PATH`.

## Project Layout

```
src/formalizer/       # Python package (extract → codegen → CLI)
formalizer-engine/    # Typst rendering engine (lib.typ)
tests/                # pytest suite
```

## Submitting Changes

1. Fork the repo and create a feature branch from `main`.
2. Make your changes and add/update tests where relevant.
3. Ensure `uv run pytest tests/ -v` passes.
4. Open a pull request with a clear description of what and why.

## Release

Releases are pushed to pypi visa publish.yml workflow. Use the following commands locally to trigger:

```bash
uv version --bump patch
git tag v*.*.*
git push origin v0.2.2
```

## License

By contributing you agree that your contributions will be licensed under the [Apache 2.0](LICENSE) license.
