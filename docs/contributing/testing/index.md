# Running the tests

What gets a test, how tests are written and structured, and the coverage floors are set out in the
[testing standard](../standards/testing.md). This page covers running the suite.

## Requirements

The suite runs against PostgreSQL with PostGIS, configured from the same `POSTGRES_*` variables as
a development portal (`stack.development.env`), and needs the GDAL, GEOS and PROJ libraries that
GeoDjango loads. The development image has them, and the `Test suite` workflow runs the suite in
that image, built from the branch, against a PostGIS service container.

To run the suite the same way on your machine, start the databases and run `pytest` in the
development image. Docker is all it needs:

```bash
docker compose up -d postgres redis
docker compose run --rm --no-deps django sh -c "uv sync --locked && pytest"
```

To run it on your own machine instead, install GDAL, GEOS and PROJ (see
[Before you start](../before_you_start.md)), start the databases with
`docker compose up postgres redis`, and install the development dependencies with:

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
migration fails there. It creates two empty databases on the same server for this and drops them
afterwards, so the database user needs the right to create databases.

## Coverage

```bash
uv run pytest --cov --cov-report=term-missing
uv run pytest --cov --cov-report=html            # report in htmlcov/
```
