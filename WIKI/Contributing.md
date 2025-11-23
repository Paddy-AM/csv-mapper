# Contributing

Thanks for your interest in contributing to csv-mapper! We welcome bug fixes, features, documentation improvements, and tests.

How to contribute
1. Fork the repository
2. Create a feature branch: git checkout -b feature/your-topic
3. Run tests and linters locally (see Development page)
4. Open a pull request against the `main` branch with a clear description of the change

Coding style
- Follow PEP 8 for Python code
- Use meaningful commit messages
- Keep PRs small and focused

Tests
- Tests are pytest-based. Place tests under `tests/`.
- Run tests:
```bash
pip install -r requirements-dev.txt
pytest
```

Review process
- PRs will be reviewed by maintainers. Expect comments and requested changes.
- Add tests for new features and bug fixes.

Reporting issues
- Please open an issue with a reproducible example, sample input, and expected output.

Local development tips
- Use a virtual environment
- Install dev dependencies: pip install -r requirements-dev.txt