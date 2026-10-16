
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
