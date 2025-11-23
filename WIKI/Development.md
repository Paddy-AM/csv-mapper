# Development

Setting up
```bash
git clone https://github.com/Paddy-AM/csv-mapper.git
cd csv-mapper
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run tests
```bash
pytest -q
```

Linting and formatting
- Black for formatting:
  black .
- Flake8 for linting:
  flake8 .

Type checking
- If present, use mypy:
  mypy src tests

Release process (suggested)
- Bump version in package metadata
- Update CHANGELOG
- Tag release and create GitHub release

Notes for maintainers
- Keep mapping config backwards-compatible where possible.
- Add examples to WIKI/Examples.md for major feature additions.