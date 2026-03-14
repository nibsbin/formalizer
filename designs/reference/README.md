# formalizer-engine

A Typst package that renders pixel-perfect PDF form replicas from a PyMuPDF-extracted schema. Overlay filled-in field values onto rasterized page backgrounds — no AcroForm interaction required.

## How it works

The system has four layers:

| Layer | Responsibility |
|---|---|
| **Orchestration** (separate project) | PyMuPDF → `FIELDS.json`, PDF → page PNGs, codegen of `copied-form.typ` |
| **This package** | Rendering engine: schema + values dict → overlaid form |
| **Generated `copied-form.typ`** | Named-parameter function wrapping the package |
| **End user** | Calls `#form(first_name: "John", agree_terms: true)` |

The orchestration layer (not part of this package) uses PyMuPDF to:
1. Extract field geometry into `FIELDS.json`
2. Rasterize each PDF page to a PNG background
3. Codegen a `copied-form.typ` wrapper with named parameters

The end user then fills in the form by editing `copied-form.typ`.

## Installation

Import from the Typst preview registry:

```typst
#import "@preview/formalizer:0.1.0": render-form
```

Or copy `lib.typ` alongside your project and import directly:

```typst
#import "lib.typ": render-form
```

## Usage

### Direct API

```typst
#import "@preview/formalizer:0.1.0": render-form

#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("page1.png", "page2.png"),
  values: (
    first_name:  "John",
    agree_terms: true,
    choice:      "yes",
    gender:      "M",
    items:       "a",
  ),
)
```

Omit `values` to render a blank form:

```typst
#render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("page1.png",),
)
```

### Via generated `copied-form.typ`

The orchestration layer codegens `copied-form.typ` once from `FIELDS.json`. End users edit it to fill the form:

```typst
// copied-form.typ (generated, then edited by the end user)
#import "@preview/formalizer:0.1.0": render-form

#let form(
  first_name:  "",      // text
  agree_terms: false,   // checkbox
  choice:      none,    // radio
  gender:      "Male",  // combobox [Male, Female]
  items:       "Aaa",   // listbox [Aaa, Bbb]
) = render-form(
  schema: json("FIELDS.json"),
  backgrounds: ("page1.png",),
  values: (first_name: first_name, agree_terms: agree_terms, choice: choice, gender: gender, items: items),
)
```

```typst
// main.typ (end user)
#import "copied-form.typ": form

#form(first_name: "John", agree_terms: true)
```

## API Reference

### `render-form`

```typst
#let render-form(schema:, backgrounds:, values: (:)) = { ... }
```

| Parameter | Type | Description |
|---|---|---|
| `schema` | `dictionary` | Parsed `FIELDS.json` — result of `json("FIELDS.json")` |
| `backgrounds` | `array` | List of PNG image paths, one per page, in page order |
| `values` | `dictionary` | Field name → value pairs; omit to render blank |

Renders one Typst `page` per entry in `schema.pages`. Each page has zero margin, uses the corresponding background PNG stretched to fill, and places field content overlays at the exact coordinates from the schema.

## Field Types

| Type | Value type | Blank default | Rendering |
|---|---|---|---|
| `text` | `string` | `""` | Left-aligned text, vertically centered, clipped to bbox |
| `checkbox` | `bool` | `false` | ✓ centered in bbox when `true` |
| `radio` | `string` (export value) | `none` | Filled circle centered in bbox for the selected button |
| `combobox` | `string` (export value) | first option | Display label resolved from `options`, left-aligned |
| `listbox` | `string` (export value) | first option | Display label resolved from `options`, left-aligned |

Field type strings are matched case-insensitively, so both schema-spec (`"text"`) and raw PyMuPDF output (`"Text"`) are supported.

## Schema (`FIELDS.json`)

See [`designs/FIELDS_SCHEMA.md`](designs/FIELDS_SCHEMA.md) for the full spec. In brief:

```json
{
  "pages": [
    { "width": 792.0, "height": 612.0 }
  ],
  "fields": [
    {
      "name":    "first_name",
      "type":    "text",
      "bbox":    [378.0, 46.0, 533.0, 84.0],
      "page":    1,
      "options": null
    },
    {
      "name":    "gender",
      "type":    "combobox",
      "bbox":    [100.0, 200.0, 250.0, 220.0],
      "page":    1,
      "options": [["M", "Male"], ["F", "Female"]]
    }
  ]
}
```

- `bbox` is `[x0, y0, x1, y1]` in points (1/72 inch), top-left origin — the same coordinate system as Typst, so no conversion is needed.
- `options` contains `[export_value, display_label]` pairs for `combobox` and `listbox` fields.

See [`example/FIELDS.json`](example/FIELDS.json) for a real-world example extracted from a multi-page PDF.

## Running tests

Tests require [uv](https://docs.astral.sh/uv/) and the [typst CLI](https://github.com/typst/typst/releases).

```sh
cd tests
uv run pytest -v
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
