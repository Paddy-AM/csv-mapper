# CLI Reference

Main command: `csv-mapper`

Convert
```bash
csv-mapper convert --mapping <mapping-file> [options] <input-csv>
```

Options
- --mapping, -m <file>   Mapping file (YAML or JSON)
- --delimiter, -d <char> CSV delimiter (default: ,)
- --encoding <enc>       Input file encoding (default: utf-8)
- --output <file>        Output path (defaults to stdout)
- --format <json|ndjson> Output format (default: json)
- --preview N            Show first N mapped rows only

Examples
- Convert CSV to JSON:
  csv-mapper convert -m mapping.yaml input.csv > out.json
- Output newline-delimited JSON:
  csv-mapper convert -m mapping.yaml --format ndjson data.csv > out.ndjson

Help
```bash
csv-mapper --help
csv-mapper convert --help
```