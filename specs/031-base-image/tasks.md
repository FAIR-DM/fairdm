# Tasks: publish a FairDM base image that portals build their containers on

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Tests first**: the entrypoint's behaviour is tested in the suite before the script is written,
and each test is seen to fail first. What only a built image shows is checked by
`docker/smoke-test.sh`, which is run locally against the built image before the story is handed
back. Wording and appearance get no tests.

**Format**: `[ID] [Story] Description`.

**Story order**: US1, US2, US3, US5, US4, each from the previous story's accepted commit.

## Phase 1: US-1, a portal developer builds their portal's production image on FairDM's images (P1)

- [ ] T001 [US1] `tests/test_docker/test_entrypoint.py`, `TestWebStart`: with stand-in `python`
  and `gunicorn` on `PATH`, `entrypoint.sh web` runs `migrate --noinput`, `collectstatic
  --noinput` in that order, then `gunicorn config.wsgi:application`. With no
  argument it does the same. `WSGI_APP` changes the application gunicorn is given. A failing
  `migrate` exits non-zero and gunicorn never runs (AS 1.2, AS 1.6, FR-005). Add
  `tests/test_docker/` to `non-mirror-paths` in `pyproject.toml`.
- [ ] T002 [US1] Same module, `TestWorkerAndPassThrough`: `entrypoint.sh worker` runs `celery
  --app config worker` and none of the web steps, `CELERY_APP` changes the app, extra arguments
  reach Celery, and any other command runs as given with its arguments and exit status (AS 1.5,
  FR-007).
- [ ] T003 [US1] `docker/entrypoint.sh` per plan P2, without the start-steps loop, to green.
- [ ] T004 [US1] `docker/Dockerfile` per plan P1, both targets. Build both locally.
- [ ] T005 [US1] `docker/portal.Dockerfile` per plan P3. Remove `COMPRESS_ENABLED` and
  `COMPRESS_OFFLINE` from `config/settings.py` (plan P3). Build FairDM's demo with it on the local
  images.
- [ ] T006 [US1] `docker/smoke-test.sh` per plan P7, every check except the start step,
  including the image-contents checks. Run it
  against the demo image and a local PostGIS until it passes (AS 1.1 to 1.7, FR-001 to FR-007,
  FR-009, SC-001, SC-005).
- [ ] T019 [US1] Remove django-compressor and django-libsass per plan P10, and the `compress`
  step from the entrypoint, its tests, the smoke test, the guide and `CONTEXT.md` (FR-005,
  FR-020). The suite stays green. Then finish T006 against the demo image.
- [ ] T007 [US1] Documentation: rewrite `docs/portal-development/production.md` per plan P8 for
  everything US1 delivers, including the example by `literalinclude`, the environment variables
  the smoke test needed, and the worker. `CONTEXT.md` terms. Changelog entry (FR-018).

## Phase 2: US-2, a portal developer adds their own steps to the start sequence (P2)

- [ ] T008 [US2] `tests/test_docker/test_entrypoint.py`, `TestStartSteps`: executable files in
  `FAIRDM_START_DIR` run after `collectstatic` and before gunicorn, in name order. A failing step exits
  non-zero and gunicorn never runs. A file that is not executable is skipped and named on stderr.
  An empty or missing directory runs the default sequence alone (AS 2.1, AS 2.2, AS 2.3, FR-008).
- [ ] T009 [US2] The start-steps loop in `docker/entrypoint.sh`, to green.
- [ ] T010 [US2] `docker/smoke-test.sh`: mount a step into `/docker-entrypoint.d/` that records
  that the `django_migrations` table exists, and check it ran before the server answered.
- [ ] T011 [US2] Documentation: start steps in the deployment guide.

## Phase 3: US-3, a developer runs a local development environment on the development image (P2)

- [ ] T012 [US3] `docker-compose.yml` per plan P4. Delete `compose/django/Dockerfile`. Run
  `docker compose up` and check the home page answers, an edited source file reloads the server,
  and the worker starts (AS 3.1, AS 3.2, FR-010, FR-011).
- [ ] T013 [US3] Documentation: the contributor pages and `AGENTS.md` per plan P8, and a portal's
  own compose file on the development image in the deployment guide (AS 3.3).

## Phase 4: US-5, a FairDM contributor learns at review that their change breaks the images (P2)

- [ ] T014 [US5] `test-suite.yml` per plan P5: the suite runs in the development image built
  from the branch. The job name stays (AS 5.1, FR-016).
- [ ] T015 [US5] `.github/workflows/image.yml` per plan P6, steps 1 to 3, with no publishing yet:
  build both targets and the demo, run the smoke test (AS 5.2, AS 5.3, FR-016, FR-017, SC-004).
- [ ] T016 [US5] Show that a broken image fails: on a scratch branch that is never pushed, remove
  `gdal-bin` from the Dockerfile and run the smoke test and one test in the development image.
  Both fail. Record the commands and output as the evidence.

## Phase 5: US-4, a portal developer moves FairDM and its images to a new release together (P2)

- [ ] T017 [US4] `docker/publish.sh` and `image.yml` step 4 per plan P6, amd64 only. Evidence,
  against a local registry (`registry:2` on localhost): a first run pushes both tags; a second run
  leaves both digests unchanged; with only `<version>` present, a run pushes `<version>-dev` and
  leaves `<version>` unchanged; with the registry unreachable, the script exits non-zero and
  pushes nothing (AS 4.2, AS 4.3, FR-012 to FR-015). SC-003 and AS 4.1 are shown on the first
  release after the merge.
- [ ] T018 [US4] Documentation: image versions against FairDM versions, and what a portal pinned
  to a commit between releases uses (FR-019).
- [ ] T024 [US4] Image releases of their own per plan P11: `docker/next-version.sh` test-first,
  `image-release.yml`, `image.yml` without publishing, `FAIRDM_IMAGE_VERSION`, and the docs
  (FR-012, FR-013, FR-014, FR-019).

