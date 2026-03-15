# Formalizer — convert fillable PDFs into Typst packages

Hey all, wanted to share a small tool I've been working on: **Formalizer**.

The short version: you point it at a fillable PDF, it spits out a self-contained Typst package. You edit one `.typ` file, run `typst compile`, and get a filled PDF back — no Acrobat, no PDF reader quirks, no AcroForm headaches.

## How it works

1. PyMuPDF reads the PDF's field schema and rasterizes each page to a PNG background at 250 DPI.
2. A code generator produces a typed Typst API wrapper (`form.typ`) and a ready-to-edit template (`example.typ`) pre-filled with human-readable dummy values.
3. The rendering engine overlays text, checkboxes, radio buttons, comboboxes, and listboxes at exact pixel coordinates on top of those backgrounds.

The generated package is completely self-contained — no network or registry access needed after generation.

```sh
formalizer --pdf myform.pdf --out ./myform-pkg
# edit out/example.typ
typst compile out/example.typ filled.pdf
```

Or from Python:

```python
from formalizer import generate
generate(pdf="myform.pdf", out="./myform-pkg")
```

## Why Typst?

PDF form filling has always been fragile. AcroForms break across readers, flatten poorly, and are a nightmare to version-control. Typst gives you a declarative, diff-friendly source file that compiles deterministically. The result is a PDF that looks identical to the original.

## Real-world use

It's early — radio button support is still rough around the edges and accessibility tagging isn't there yet — but it's already working well in production on an Air Force form (AF4141). Two pages, mix of text fields, checkboxes, and combos, compiles cleanly and matches the original layout.

## Links

- Repo: https://github.com/tongue-to-quill/formalizer (Apache 2.0)

Happy to answer questions or hear about other PDF-heavy workflows where this might help.
