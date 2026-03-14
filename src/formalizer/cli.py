"""Command-line interface for formalizer."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="formalizer",
        description="Generate a self-contained Typst package from a fillable PDF.",
    )
    parser.add_argument(
        "--pdf",
        required=True,
        help="path to the fillable PDF to replicate",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="destination directory for the generated package",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="override the package name in typst.toml (default: --out basename, slugified)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="delete and overwrite --out if it already exists",
    )

    args = parser.parse_args(argv)

    from formalizer import generate

    try:
        out = generate(pdf=args.pdf, out=args.out, name=args.name, force=args.force)
    except (FileNotFoundError, FileExistsError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Auto-compile example.typ → example.pdf and debug.typ → debug.pdf
    out_dir = out / "out"
    example_typ = out_dir / "example.typ"
    compile_ok = True
    if example_typ.exists():
        result = subprocess.run(
            ["typst", "compile", "--root", str(out), str(example_typ), str(out_dir / "example.pdf")],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            compile_ok = False
            print(f"✓ Package generated in {out}")
            print(f"  ⚠ typst compile example.typ failed: {result.stderr.strip()}", file=sys.stderr)

    debug_typ = out_dir / "debug.typ"
    if debug_typ.exists():
        result = subprocess.run(
            ["typst", "compile", "--root", str(out), str(debug_typ), str(out_dir / "debug.pdf")],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            compile_ok = False
            print(f"  ⚠ typst compile debug.typ failed: {result.stderr.strip()}", file=sys.stderr)

    if compile_ok:
        print(f"✓ Package generated in {out}")
        print(f"  Preview: {out_dir / 'example.pdf'}")
        print(f"  Debug:   {out_dir / 'debug.pdf'}")
    elif example_typ.exists() or debug_typ.exists():
        pass  # error already printed above
    else:
        print(f"✓ Package generated in {out}")


if __name__ == "__main__":
    main()
