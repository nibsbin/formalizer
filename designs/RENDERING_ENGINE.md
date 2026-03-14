# Rendering Engine Design Doc

The `typst-formalizer` rendering engine (`lib.typ`) that produces pixel-perfect PDF form replicas from a PyMuPDF-extracted schema. Consumed as a copied `lib.typ` inside each generated package (see [PROJECT.md](PROJECT.md)).

## Layers

| Layer | Responsibility |
|---|---|
| **Orchestration** (formalizer) | PyMuPDF → `FIELDS.json`, PDF → page PNGs, codegen of `form.typ` + `example.typ`, copy of `lib.typ` |
| **`lib.typ`** | Rendering engine: schema + values dict → overlaid form |
| **Generated `form.typ`** | Named-parameter `form()` function wrapping the engine — not user-edited |
| **Generated `example.typ`** | Calls `form()` with realistic dummy data — user's editable starting point |
| **End user** | Copies/adapts `example.typ`, runs `typst compile` |

## Package API

```typst
#let render-form(schema: none, backgrounds: (), values: (:)) = { ... }
```

- `schema` — result of `json("FIELDS.json")` (required named parameter)
- `backgrounds` — list of PNG paths, one per page (required named parameter)
- `values` — dict of field name → value (omit to render blank)

## Rendering

1. Group fields by page
2. Per page: `page(width, height, margin: 0pt)` → `place(top+left, image(bg, fit: "stretch"))` → `place(dx, dy)` per field
3. Coordinates: PyMuPDF bbox is top-left origin, same as Typst — multiply by `1pt`
4. Field widgets are transparent overlays (no chrome); PNG provides visual styling
5. A zero-width no-break space (`U+FEFF`) fence is placed at each field origin to prevent PDF viewer text-selection grouping across fields

## Generated Package Structure

```
<out>/
  typst.toml      # package manifest (name, version, entrypoint)
  lib.typ         # rendering engine (copied from typst-formalizer)
  FIELDS.json     # extracted field schema
  page1.png       # page backgrounds (one per page)
  form.typ        # generated: form() API — do not edit
  example.typ     # generated: pre-filled with dummy data — user's starting point
```

### `form.typ`

Generated from `FIELDS.json`. Defines the typed `form()` API. Users import from this but do not edit it directly.

```typst
#import "lib.typ": render-form

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

### `example.typ`

Generated with plausible dummy values for every field. This is what users copy and edit — it serves as both documentation of the API and a working template.

```typst
#import "form.typ": form

// Fill in your values below. Run: typst compile example.typ output.pdf
#form(
  first_name:  "Jane Smith",
  agree_terms: true,
  choice:      "option_b",
  gender:      "Female",
  items:       "Bbb",
)
```

## Schema

See [FIELD_SCHEMA.md](FIELD_SCHEMA.md) for the full spec.

## Testing

Use the `uv` project manager to bootstrap a Python pytest environment in `tests/`. Write mixed `.py` and `.typ` tests to robustly validate typst-formalizer package functionality.
