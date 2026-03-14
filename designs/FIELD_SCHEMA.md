# FIELDS.json Schema Spec

Contract between the orchestration layer (PyMuPDF extraction) and the Typst formalizer package.

## Top-level

```json
{
  "pages":  [ <Page>, ... ],
  "fields": [ <Field>, ... ]
}
```

## Page

```json
{ "width": 792.0, "height": 612.0 }
```

| Field | Type | Description |
|---|---|---|
| `width` | `float` | Page width in points |
| `height` | `float` | Page height in points |

## Field

```json
{
  "name":    "field_name",
  "type":    "text",
  "bbox":    [x0, y0, x1, y1],
  "page":    1,
  "options": null
}
```

| Field | Type | Description |
|---|---|---|
| `name` | `string` | Unique field identifier (from PDF AcroForm) |
| `type` | `string` | See field types below |
| `bbox` | `[float, float, float, float]` | `[x0, y0, x1, y1]` in points, top-left origin |
| `page` | `int` | 1-indexed page number |
| `options` | `[[string, string], ...]` \| `null` | `[export_value, display_label]` pairs; `combobox` and `listbox` only |
| `export_value` | `string` \| omitted | For `radio` fields: the export value of this specific button. When present, selection is matched by comparing this value against the group value. When absent, the 0-based index within the group (stringified) is used. |

## Field Types

| Type | Description | `options` |
|---|---|---|
| `text` | Single or multiline text input | `null` |
| `checkbox` | Boolean toggle | `null` |
| `radio` | One-of-many selection (one `Field` entry per button); may carry `export_value` | `null` |
| `combobox` | Dropdown with fixed options | required |
| `listbox` | Scrollable list with fixed options | required |

## Coordinates

- Origin: **top-left** of the page
- Unit: **points** (1/72 inch), matching PyMuPDF's native output
- `bbox` order: `x0` (left), `y0` (top), `x1` (right), `y1` (bottom)
- Field width = `x1 - x0`, height = `y1 - y0`
- No coordinate conversion needed for Typst (same origin and unit)

## Values

When a consumer provides values to fill the form, the expected type per field type:

| Field type | Value type | Blank default |
|---|---|---|
| `text` | `string` | `""` |
| `checkbox` | `bool` | `false` |
| `radio` | `string` (export value of selected button) | `none` |
| `combobox` | `string` (export value) | first option |
| `listbox` | `string` (export value) | first option |
