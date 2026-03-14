import json
import fitz  # pymupdf

PDF = "af4141-fillable.pdf"

doc = fitz.open(PDF)

pages = [{"width": page.rect.width, "height": page.rect.height} for page in doc]

fields = []
for page in doc:
    for widget in page.widgets():
        fields.append({
            "name": widget.field_name,
            "type": widget.field_type_string,
            "bbox": list(widget.rect),
            "page": page.number + 1,
            "label": widget.field_label,
            "value": widget.field_value,
            "flags": widget.field_flags,
            "options": widget.choice_values,  # non-empty for select/radio
            "max_len": widget.text_maxlen,
        })

output = {"pages": pages, "fields": fields}
print(json.dumps(output, indent=2))
