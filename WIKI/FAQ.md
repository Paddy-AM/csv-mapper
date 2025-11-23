# FAQ

Q: My mapping fails with "missing column" even though the CSV has the header.
A: Confirm delimiter and encoding. Use --delimiter to match the CSV or pass the correct encoding. Also ensure header names exactly match `source` fields (case-sensitive by default).

Q: How do I handle empty values?
A: Use `default` in the mapping config, or use a transform that handles empty strings.

Q: Can I map the same CSV column to multiple output fields?
A: Yes — repeat the mapping entry with the same `source` but different `target`.

Q: Is there support for streaming/large CSVs?
A: Yes — the Python API returns an iterable/generator so you can stream transformations without loading everything in memory.

Q: How to add a custom transform?
A: Register the transform via `register_transform("name", callable)` and reference it in the mapping using `transform: "name"`.