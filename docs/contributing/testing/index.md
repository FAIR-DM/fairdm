# Running the tests

What gets a test, how tests are written and structured, and the coverage floors are set out in the
[testing standard](../standards/testing.md). This page covers running the suite.

## Requirements

The suite runs against PostgreSQL with PostGIS, configured from the same `POSTGRES_*` variables as
a development portal (`stack.development.env`). The dev container's `postgres` service provides one.
Install the development dependencies with:

```bash
uv sync
```

## Running

```bash
uv run pytest                                    # everything: tests/ and demo/tests/
uv run pytest tests/test_core/test_project/      # one area
uv run pytest tests/test_core/test_project/test_models.py::TestProjectModel   # one class
```

Tests mirror the source tree, so the tests for `fairdm/core/project/models.py` are in
`tests/test_core/test_project/test_models.py`. The reference application's own tests are in
`demo/tests/`.

The default options in `pyproject.toml` run the suite in parallel, one worker per core, with each
class or module kept on one worker. Add `-n0` to run serially, which is easier to read when
debugging a single test.

## The test database

The suite builds its database straight from the models (`--no-migrations`) and keeps it between
runs (`--reuse-db`). After changing a model, add `--create-db` once to rebuild it.

`tests/test_smoke.py` is the exception: it runs the real migrations, so a model change without a
migration fails there.

## Coverage

```bash
uv run pytest --cov --cov-report=term-missing
uv run pytest --cov --cov-report=html            # report in htmlcov/
```
