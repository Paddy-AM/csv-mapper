# API Reference

Objects and functions (summary)

Mapper
- Mapper.from_file(path: str) -> Mapper
  Load a mapping configuration from YAML/JSON file.

- Mapper.from_dict(cfg: dict) -> Mapper
  Create a mapper from a parsed config dictionary.

- Mapper.transform_row(row: dict) -> dict
  Transform a single CSV row (mapping/coercion/validation).

- Mapper.transform_csv(fh: TextIO) -> List[dict] | Generator[dict, None, None]
  Transform rows from a CSV file handle.

Transforms
- Built-in transforms:
  - split_comma: split a string on commas into a list
  - parse_date(format): parse dates with a given format
  - lower_case, upper_case, trim

Registering custom transforms
```python
from csv_mapper import Mapper, register_transform

def my_transform(value, **kwargs):
    # modify value
    return value

register_transform("my_transform", my_transform)
```

Errors and exceptions
- MappingError: base error for mapping-related failures
- ValidationError: raised when input fails required checks

Notes
- See the code docs for full signature details and additional helpers.