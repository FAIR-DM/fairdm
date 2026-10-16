
## 2026-10-16T10:37:46Z · Forge · PLAN

Research, plan and tasks written against v0.1.0. Five stories, eighteen tasks. Next: design review.

## 2026-10-16T10:57:52Z · Implementer US1 · T001-T003

Did: wrote the entrypoint tests first (TestWebStart, TestWorkerAndPassThrough) and saw all 11 fail because docker/entrypoint.sh did not exist, then wrote the entrypoint. Fixed my stand-in so a failure is matched on the full command line.
Verified: uv run pytest -n0 tests/test_docker/ -> 11 passed. Removing `set -e` fails the three failing-step tests.
Next: T004 Dockerfile.
Watch: none.

## 2026-10-16T11:26:38Z · Implementer US1 · T004-T007

Did: built docker/Dockerfile (both targets), docker/portal.Dockerfile, docker/smoke-test.sh; removed the two COMPRESS lines from config/settings.py; rewrote production.md; added CONTEXT.md terms and a changelog entry.
Verified: both targets and the demo image build with docker.exe. Smoke test against the demo image stops at the web start: `python manage.py compress` fails with OfflineGenerationError because no template in the demo uses {% compress %}. Against a throwaway image that adds one such template, all 12 checks pass. forge verify: conformance, docs, lint, typecheck, test, build all passed.
Next: Forge to decide what the start sequence does about compress; T006 stays open until the smoke test passes on the demo image.
Watch: T006 not marked done.

## 2026-10-16T15:53:10Z · Implementer US1 · T019

Did: removed django-compressor and django-libsass (dependencies, compressor app, finder, COMPRESS_* settings, the production compress step, spectacular.html load, theme README snippet), dropped the compress step from the entrypoint, its tests, the smoke test message, the guide, CONTEXT.md; changelog Removed entry; uv.lock regenerated with only removals.
Verified: entrypoint tests red (2 failed) before the change, 10 passed after; ruff check and format clean on touched files; manage.py check clean; uv lock --check ok.
Next: T006, build images and run the smoke test.
Watch: the local uv writes lock revision 3; restored revision 5 by hand so the lock diff is removals only.

## 2026-10-16T15:58:34Z · Implementer US1 · T006

Did: rebuilt fairdm-base:local, fairdm-base:local-dev and fairdm-demo:local from docker/ on the branch; started postgis/postgis:17-3.5 and redis:7 on a user-defined network; ran docker/smoke-test.sh.
Verified: smoke test exit 0, 10 checks plus "all checks passed": libpq present, uv present, neither base image contains FairDM, dev image has gcc and git, database reachable, portal migrated+collected and answered 200 on 8000, server not root, GDAL/GEOS load with no library path, PORT=8123 answers, worker starts Celery without the web sequence, unreachable database exits 1 and the server never starts. The remaining containers and the network were removed afterwards.
Next: full verify, then the report.
Watch: the portal Dockerfile build prints two InvalidDefaultArgInFrom warnings because FAIRDM_VERSION has no default by design.

## 2026-10-16T16:13:29Z · Implementer US2 · T008-T009

Did: wrote TestStartSteps first (7 tests), saw 4 fail because no step ran, then added the start-steps loop to docker/entrypoint.sh.
Verified: uv run pytest -n0 tests/test_docker/ -> 17 passed; ruff check and format clean on tests/test_docker.
Next: T010 smoke-test check for a mounted step.
Watch: none.

## 2026-10-16T16:33:37Z · Implementer US2 · T010-T011

Did: added a start step to docker/smoke-test.sh, copied into the web container with docker create, cp and start, that asserts django_migrations exists and logs a line; the script compares that line's position in the container log with gunicorn's 'Listening at'. Wrote the Add your own start steps section of production.md and a changelog sentence.
Verified: smoke test on a fresh PostGIS, exit 0, 13 checks. Probe: moved the start-steps loop before migrate in the entrypoint, rebuilt, smoke test failed on the step's assertion; restored. Built a throwaway image with the guide's example step (COPY --chmod=755): it ran and the server started; a 644 file was skipped with the documented stderr line.
Next: US3 compose.
Watch: a bind mount of a WSL path under Docker Desktop arrives empty, so the script copies the step in instead. One earlier run exited before answering with a WSL accept4 error in the output; the next three runs were green.

## 2026-10-16T16:48:20Z · Implementer US3 · T012-T013

Did: docker-compose.yml builds docker/Dockerfile target development, mounts the checkout and a venv volume, and runs uv sync then migrate and runserver, or the Celery worker, through the entrypoint's pass-through. Deleted compose/django/Dockerfile. Updated AGENTS.md, before_you_start.md, testing/index.md, production.md (a portal's own compose file) and the changelog.
Verified: docker.exe compose -p fairdm031 up -d --build: GET / 200 from this shell; touching fairdm/__init__.py logs '/app/fairdm/__init__.py changed, reloading.'; the worker logs 'celery@... ready.'; torn down with down -v --rmi local. The first attempt failed because both services synced into the venv volume at once, so the worker now waits for a healthy django (D13). Ran the suite the way the contributor page says: pytest -n0 tests/test_core/test_project -> 346 passed. Ran the guide's portal compose file against fairdm-base:local-dev: GET / 200 and the worker ready.
Next: full verify and the report.
Watch: a project name other than fairdm was used for the run (-p fairdm031) so the existing fairdm_postgres volume was untouched. docker.exe only translates the relative .:/app mount; an absolute WSL path mounts an empty directory.

## 2026-10-16T17:10:01Z · Implementer US5 · T014

Did: test-suite.yml now builds the development target from the branch (buildx, load, gha cache scoped "development"), caches ~/.cache/uv on uv.lock, and runs `uv sync --locked`, the Django pin and its version check, and pytest with coverage in one `docker run --network host --user root` with the checkout mounted at /app. The GDAL, setup-uv, host sync and host pytest steps are gone. Job name, matrix, caller job id and the Codecov step are unchanged.
Verified: check-jsonschema (vendor.github-workflows) exit 0; actionlint 1.7.12 exit 0; the workflow's run step executed locally with docker.exe against a postgis container (network fs031-ci, bind mount via wslpath -w): Django 5.2.17 printed by the version check, `pytest --cov=fairdm --cov-report=xml tests/test_smoke.py tests/test_docker` 21 passed, exit 0, coverage.xml written into the checkout. `uv pip install` needed `--python /opt/venv/bin/python`: UV_PROJECT_ENVIRONMENT does not apply to the pip interface.
Next: T015 image.yml.
Watch: the full suite was not run in the image here; CI is the first full run. coverage.xml is written by root in the checkout, which the Codecov step reads.
