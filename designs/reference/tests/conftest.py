"""Shared fixtures for typst-formalizer tests."""

import json
import os
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

import pytest

# Root of the typst-formalizer package (one level up from tests/)
PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def _make_png(width: int, height: int, color: tuple[int, int, int] = (255, 255, 255)) -> bytes:
    """Create a minimal valid PNG image in memory."""

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        body = chunk_type + data
        crc = zlib.crc32(body) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + body + struct.pack(">I", crc)

    raw_rows = b""
    for _ in range(height):
        raw_rows += b"\x00" + bytes(color) * width

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw_rows))
        + _chunk(b"IEND", b"")
    )


@pytest.fixture()
def tmp_dir(tmp_path: Path):
    """Return a temporary directory that already contains lib.typ."""
    lib_src = PACKAGE_ROOT / "lib.typ"
    (tmp_path / "lib.typ").write_text(lib_src.read_text())
    return tmp_path


def compile_typst(work_dir: Path, typ_file: str) -> Path:
    """Compile a .typ file inside *work_dir* and return the PDF path.

    Raises ``AssertionError`` with the compiler stderr on failure.
    """
    pdf = work_dir / typ_file.replace(".typ", ".pdf")
    result = subprocess.run(
        ["typst", "compile", typ_file, str(pdf.name)],
        cwd=work_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"typst compile failed:\n{result.stderr}"
    assert pdf.exists(), f"Expected PDF not found: {pdf}"
    return pdf


def write_schema(dest: Path, pages: list[dict], fields: list[dict]) -> Path:
    """Write a FIELDS.json file and return its path."""
    schema_path = dest / "FIELDS.json"
    schema_path.write_text(json.dumps({"pages": pages, "fields": fields}))
    return schema_path


def write_bg(dest: Path, name: str, width: int, height: int) -> Path:
    """Write a blank background PNG and return its path."""
    bg_path = dest / name
    bg_path.write_bytes(_make_png(width, height))
    return bg_path
