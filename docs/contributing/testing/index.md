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

## Checking the images

Every pull request runs the `Image` workflow. It builds the runtime image, the development image and
the demo portal on top of them, then runs `docker/smoke-test.sh` against all three. A change to
`docker/`, to the system libraries FairDM needs, or to the code that starts the portal can fail it,
even when every test passes. Releases are published by the same workflow, but only on a release tag.

To run the same check on your machine, build the three images, start PostGIS and Redis on a network
of their own, and run the script on that network:

```bash
docker build -f docker/Dockerfile --target runtime -t fairdm-base:local .
docker build -f docker/Dockerfile --target development -t fairdm-base:local-dev .
docker build -f docker/portal.Dockerfile --build-arg FAIRDM_IMAGE=fairdm-base \
    --build-arg FAIRDM_VERSION=local -t fairdm-demo:local .

docker network create fairdm-smoke
docker run -d --name fairdm-smoke-db --network fairdm-smoke -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=fairdm postgis/postgis:17-3.5
docker run -d --name fairdm-smoke-redis --network fairdm-smoke redis:7
SMOKE_NETWORK=fairdm-smoke SMOKE_DB_HOST=fairdm-smoke-db \
    SMOKE_REDIS_URL=redis://fairdm-smoke-redis:6379/0 \
    docker/smoke-test.sh fairdm-base:local fairdm-base:local-dev fairdm-demo:local
```

The script prints one line per check and stops at the first failure. It needs an empty database, so
remove and recreate `fairdm-smoke-db` before running it again. Remove the containers and the
network when you are done:

```bash
docker rm -f fairdm-smoke-db fairdm-smoke-redis
docker network rm fairdm-smoke
```
