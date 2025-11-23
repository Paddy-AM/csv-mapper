# Quick Start

This page contains minimal examples to get you going.

CLI: Convert CSV to JSON using a mapping file
```bash
csv-mapper convert --mapping mapping.yaml input.csv > output.json
```

Python API: basic usage
```python
from csv_mapper import Mapper

mapper = Mapper.from_file("mapping.yaml")
with open("input.csv", "r", newline="") as fh:
    results = mapper.transform_csv(fh)
# results is a list of dicts (or generator depending on config)
```

Example mapping (YAML)
```yaml
mappings:
  - source: "first_name"
    target: "firstName"
  - source: "last_name"
    target: "lastName"
  - source: "age"
    target: "age"
    type: int
```

See Configuration for more mapping examples (nested objects, default values, custom transforms).