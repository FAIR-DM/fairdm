
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
