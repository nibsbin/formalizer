"""Core orchestration: extraction → codegen → optional compile."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from formalizer.codegen import _slugify, codegen
from formalizer.extract import extract


def generate(
    pdf: str | Path,
    out: str | Path,
    *,
    name: str | None = None,
    force: bool = False,
) -> Path:
    """Generate a self-contained Typst package from a fillable PDF.

    Parameters
    ----------
    pdf:
        Path to the source fillable PDF.
    out:
        Destination directory.  Files are written directly here (no
        subdirectory is created).  Raises ``FileExistsError`` unless
        *force* is ``True``.
    name:
        Override the package name in ``typst.toml``.  Defaults to the
        *out* directory basename, slugified.
    force:
        When ``True``, delete *out* if it already exists.
    """
    pdf = Path(pdf)
    out = Path(out)

    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf}")

    if out.exists():
        if not force:
            raise FileExistsError(
                f"Output directory already exists: {out}  "
                "(pass force=True or -f to overwrite)"
            )
        shutil.rmtree(out)

    out.mkdir(parents=True, exist_ok=True)

    # Derive package name
    pkg_name = name if name else _slugify(out.resolve().name)

    # 1. Extraction
    schema = extract(pdf, out)

    # 2. Codegen
    codegen(schema, out, pkg_name)

    return out
