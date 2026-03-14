// Formalizer Engine – rendering engine
// Renders pixel-perfect PDF form replicas from a PyMuPDF-extracted schema.

/// Render a single field's content overlay.
///
/// - field-type (str): normalised lowercase type
/// - value: user-supplied value for this field (or none)
/// - width (length): field width
/// - height (length): field height
/// - field (dictionary): raw field entry from the schema
#let render-field(field-type, value, width, height, field) = {
  if field-type == "text" {
    if value != none and str(value) != "" {
      box(
        width: width,
        height: height,
        clip: true,
        align(left + horizon, text(size: height * 0.6, str(value)))
      )
    }
  } else if field-type == "checkbox" {
    if value == true {
      box(
        width: width,
        height: height,
        align(center + horizon, text(size: height * 0.8, "✓"))
      )
    }
  } else if field-type == "radio" {
    // value is true when this specific button is the selected one
    // (resolved at group level before calling this helper)
    if value == true {
      let dot-r = calc.min(width, height) * 0.3
      box(
        width: width,
        height: height,
        align(center + horizon, circle(radius: dot-r, fill: black))
      )
    }
  } else if field-type == "combobox" or field-type == "listbox" {
    let display = if value != none { str(value) } else { "" }
    // Resolve export value → display label when options are present
    if field.at("options", default: none) != none and value != none {
      for opt in field.options {
        if str(opt.at(0)) == str(value) {
          display = str(opt.at(1))
        }
      }
    }
    if display != "" {
      box(
        width: width,
        height: height,
        clip: true,
        align(left + horizon, text(size: height * 0.6, display))
      )
    }
  }
}

/// Build a lookup that maps each radio-group name to an array of field
/// entries belonging to that group, preserving schema order.
#let build-radio-groups(fields) = {
  let groups = (:)
  for f in fields {
    let ft = lower(f.type)
    if ft == "radio" {
      let name = f.name
      if name in groups {
        groups.at(name).push(f)
      } else {
        groups.insert(name, (f,))
      }
    }
  }
  groups
}

/// Determine whether a single radio button should appear selected.
///
/// Strategy:
///  1. If the field carries an `export_value` key, match against it.
///  2. Otherwise fall back to matching the 0-based index within the group
///     (stringified) against the supplied value.
#let radio-button-selected(field, group-value, index-in-group) = {
  if group-value == none { return false }
  let ev = field.at("export_value", default: none)
  if ev != none {
    return str(ev) == str(group-value)
  }
  // Fallback: match against the stringified index
  str(index-in-group) == str(group-value)
}

/// Main entry point.
///
/// - schema (dictionary): result of `json("FIELDS.json")`
/// - backgrounds (array): list of image paths / bytes, one per page
/// - values (dictionary): field name → value; omit to render blank
#let render-form(schema: none, backgrounds: (), values: (:)) = {
  assert(schema != none, message: "render-form: `schema` is required")
  assert(backgrounds.len() > 0, message: "render-form: `backgrounds` is required")
  let pages = schema.pages
  let fields = schema.fields

  // Pre-compute radio groups for selection logic
  let radio-groups = build-radio-groups(fields)
  // Track how many radio buttons we have seen per group so far
  let radio-counters = (:)

  for (i, page-info) in pages.enumerate() {
    let page-num = i + 1
    let page-fields = fields.filter(f => f.page == page-num)

    let bg = backgrounds.at(i)
    let pw = page-info.width * 1pt
    let ph = page-info.height * 1pt

    page(
      width: pw,
      height: ph,
      margin: 0pt,
    )[
      // Background image (the original PDF page rasterised as PNG)
      #place(top + left, image(bg, width: pw, height: ph, fit: "stretch"))

      // Field overlays
      #for field in page-fields.filter(f => ("text", "checkbox", "radio", "combobox", "listbox").contains(lower(f.type))) {
        let x  = field.bbox.at(0) * 1pt
        let y  = field.bbox.at(1) * 1pt
        let w  = (field.bbox.at(2) - field.bbox.at(0)) * 1pt
        let h  = (field.bbox.at(3) - field.bbox.at(1)) * 1pt

        let field-type = lower(field.type)
        let val = values.at(field.name, default: none)

        // --- Radio: resolve group-level value to per-button boolean ---
        if field-type == "radio" {
          let group-name = field.name
          let idx = radio-counters.at(group-name, default: 0)
          radio-counters.insert(group-name, idx + 1)
          val = radio-button-selected(field, val, idx)
        }

        place(
          top + left,
          dx: x,
          dy: y,
          render-field(field-type, val, w, h, field),
        )

        // Zero-width fence to break PDF viewer text-selection grouping
        place(top + left, dx: x, dy: y, text(size: 0.001pt, "\u{FEFF}"))
      }
    ]
  }
}
