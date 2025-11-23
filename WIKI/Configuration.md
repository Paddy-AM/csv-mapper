# Configuration / Mapping Files

csv-mapper uses declarative mapping files (YAML or JSON) to describe how CSV columns map to output structure and types.

Basic structure (YAML)
```yaml
mappings:
  - source: "<csv_column_name>"
    target: "<output_field_name>"
    type: "<int|float|str|bool|date|...>"   # optional
    default: "<value>"                      # optional
    required: true|false                    # optional
    transform: "<transform_name>"           # optional, builtin or custom
```

Examples

Simple rename and type coercion
```yaml
mappings:
  - source: "price"
    target: "price_usd"
    type: float
  - source: "in_stock"
    target: "inStock"
    type: bool
```

Nested objects
```yaml
mappings:
  - source: "street"
    target: "address.street"
  - source: "city"
    target: "address.city"
```

Lists and splitting
```yaml
mappings:
  - source: "tags"
    target: "tags"
    transform: "split_comma"  # built-in transform that splits on commas
```

Custom transforms
- Custom transforms can be registered via the Python API (see API Reference).
- Example: register a function that parses custom date formats or normalizes phone numbers.

Validation and required fields
- Set `required: true` to raise an error if the source column is missing or empty.
- Use `default` for fallback values when a column is blank.

File formats
- YAML recommended for readability
- JSON supported (same structure)