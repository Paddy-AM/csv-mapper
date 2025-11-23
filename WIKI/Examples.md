# Examples

1) Mapping CSV to nested objects

mapping.yaml
```yaml
mappings:
  - source: "first_name"
    target: "name.first"
  - source: "last_name"
    target: "name.last"
  - source: "email"
    target: "contact.email"
```

Run (CLI)
```
csv-mapper convert -m mapping.yaml people.csv > people.json
```

2) Using Python for streaming large files
```python
from csv_mapper import Mapper

mapper = Mapper.from_file("mapping.yaml")
with open("large.csv") as fh, open("out.ndjson","w") as out:
    for obj in mapper.transform_csv(fh):
        out.write(json.dumps(obj) + "\n")
```
