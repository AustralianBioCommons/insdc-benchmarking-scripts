# Contributing Guide

## Development Setup

```bash
# Clone repo
git clone https://github.com/yourorg/insdc-benchmarking-scripts
cd insdc-benchmarking-scripts

# Install with dev dependencies
poetry install

# Install pre-commit hooks (optional)
pre-commit install
```

## Adding New Protocols

1. Create new file: `scripts/benchmark_PROTOCOL.py`
2. Follow the pattern from `benchmark_http.py`
3. Import utilities from `scripts/utils/`
4. Add tests in `tests/test_PROTOCOL.py`
5. Update documentation

## Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=scripts

# Specific test file
poetry run pytest tests/test_config.py -v
```

## Code Style

We use:
- **black** for formatting
- **ruff** for linting

```bash
# Format code
poetry run black scripts/ tests/

# Lint
poetry run ruff check scripts/ tests/
```

## Pull Request Process

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-protocol`)
3. Make changes
4. Run tests (`poetry run pytest`)
5. Format code (`poetry run black .`)
6. Commit changes
7. Push to fork
8. Open Pull Request

## Questions?

Open an issue or contact the maintainers.
