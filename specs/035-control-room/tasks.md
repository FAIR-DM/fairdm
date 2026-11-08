# Tasks: an operations control room in the administration interface

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[decisions.md](decisions.md)

**Tests first**: in every group the test tasks come first, and each is seen to fail before the code
that makes it pass is written. Wording and appearance get no tests.

**How tests run**: through the shared development container,
`~/.openclaw/devserver/fairdm-shared-test.sh <worktree> <command>`, which queues runs one at a time.

**Format**: `[ID] [Story] Description`.

**Order**: US1, then US2 from US1's verified commit.

## Phase 1: User Story 1, a superuser checks the portal's services (P1)

### Group 1

- [ ] T001 [US1] Add `dj-control-room[redis,cache,celery,urls,signals]>=1.8.1,<2` to
  `[project].dependencies` in `pyproject.toml`, add the seven distribution names
  (`dj-control-room`, `dj-control-room-base`, `dj-redis-panel`, `dj-cache-panel`,
  `dj-celery-panel`, `dj-urls-panel`, `dj-signals-panel`) to the deptry ignore list for packages
  named only in settings strings, and update `uv.lock`. No test: deptry and the suite cover it.
- [ ] T002 [US1] `tests/test_conf/test_settings/test_control_room.py`: with the production
  baseline (`DJANGO_ENV=qa`), `INSTALLED_APPS` holds `dj_control_room_base`, `dj_redis_panel`,
  `dj_cache_panel`, `dj_celery_panel` and `dj_control_room`, with the hub after the three panels
  and none of `dj_urls_panel`, `dj_signals_panel`. Each of `DJ_CONTROL_ROOM_SETTINGS`,
  `DJ_CONTROL_ROOM_BASE_SETTINGS`, `DJ_REDIS_PANEL_SETTINGS`, `DJ_CACHE_PANEL_SETTINGS`,
  `DJ_CELERY_PANEL_SETTINGS`, `DJ_URLS_PANEL_SETTINGS` and `DJ_SIGNALS_PANEL_SETTINGS` has
  `REQUIRE_SUPERUSER` true (FR-004). The Redis panel's one instance has the cache's `LOCATION` as
  its URL and no `features` key (FR-014). `DJ_URLS_PANEL_SETTINGS["ENABLE_TESTING"]` is false
  (FR-013). No dict sets `MCP_ENABLED` true (FR-007). Use the `isolated_env` and
  `settings_module` fixtures the other modules in that directory use.
- [ ] T003 [US1] `fairdm/conf/settings/control_room.py`, as plan.md "Settings" describes, with a
  module docstring in the style of its siblings, and add it to `settings_modules` in
  `fairdm/conf/setup.py` after `settings/celery.py`. T002 goes green.
- [ ] T004 [US1] `tests/test_contrib/test_admin/test_control_room.py`: on the dashboard
  (`dj_control_room:index`) and the index route of each of the Redis, cache and Celery panels, a
  superuser gets 200 (US1 AS 2); a staff account that is not a superuser gets 403 (AS 4); a holder
  of each rights-carrying portal role gets 403 (AS 5, reconcile roles as
  `test_sites.py` does); an anonymous visitor is redirected to the admin sign-in (AS 6). The admin
  index offers a superuser a link to the dashboard (AS 1) and offers the staff account and the
  role holders no link to the dashboard or any panel (AS 7). The agent interface address answers
  404 (AS 10). With `DJ_REDIS_PANEL_SETTINGS` pointing at a closed local port, the Redis and cache
  panel pages answer 200 for a superuser (AS 8), and the Celery panel answers 200 with no worker
  (AS 9). On a Redis key page the response offers no edit, delete or expiry form (AS 12): assert on
  the form actions or field names the package renders, not on text. Read each package's
  `urls.py` for the route names. Mark the Redis-backed tests so they skip cleanly when no Redis is
  reachable only if the shared container has none; it does (`REDIS_URL` is set there), so prefer
  real Redis.
- [ ] T005 [US1] `fairdm/contrib/admin/urls.py`: the panel routes as plan.md "Routes" describes.
  T004 goes green. Add a test to T004's module that, under `override_settings(ADMIN_URL=
  "manage/")` with the URL conf reloaded, the dashboard reverses under `manage/` and answers 200
  (AS 3).
- [ ] T006 [US1] Add to T002's module: a portal settings module that assigns its own
  `DJ_REDIS_PANEL_SETTINGS` after `fairdm.setup()` keeps its own value (AS 13, FR-008), and one
  that removes the five control-room apps from `INSTALLED_APPS` still loads. Add to T004's module:
  with the five apps removed (`modify_settings` and a reloaded URL conf), the admin index answers
  200 and the dashboard address answers 404 (AS 14, FR-009).
- [ ] T007 [US1] Documentation (FR-012):
  `docs/administrators/how-to/check-the-portals-services-in-the-control-room.md` and
  `docs/developers/how-to/change-who-can-open-the-control-room.md`, each linked from its section's
  `index.md`; one entry per new setting in `docs/developers/reference/settings.md` under a new
  "Operations dashboard" section; a line for Django Control Room in
  `docs/explanation/the-technology-stack.md`; a `CHANGELOG.md` entry under `[Unreleased]`. The
  developers' page says that a superuser whose staff flag is cleared is refused (research finding
  2), how to widen or narrow access with `REQUIRE_SUPERUSER` and `ALLOWED_GROUPS` per panel, how to
  turn on Redis editing per instance, how to remove the dashboard, and what turning on the agent
  interface exposes. Run every code example against the branch.

## Phase 2: User Story 2, a developer inspects routes and signals (P2)

### Group 2

- [ ] T008 [US2] Add to `tests/test_conf/test_development.py`: with `DJANGO_ENV=development`,
  `INSTALLED_APPS` holds `dj_urls_panel` and `dj_signals_panel`, both before `dj_control_room`
  (FR-010). With `DJANGO_ENV=qa` it holds neither (FR-011).
- [ ] T009 [US2] `fairdm/conf/development.py`: insert the two apps before `dj_control_room`. T008
  goes green.
- [ ] T010 [US2] Add to `tests/test_contrib/test_admin/test_control_room.py`: under the suite's
  development settings a superuser gets 200 on the URL panel's and the signal panel's index routes
  and a staff account that is not a superuser gets 403 (US2 AS 1, AS 3). With the two apps removed
  and the URL conf reloaded, both addresses answer 404 and the dashboard offers no link that opens
  either (AS 2).
- [ ] T011 [US2] Documentation: a section in
  `docs/developers/how-to/change-who-can-open-the-control-room.md` on the development-only panels,
  and that the URL panel's request testing is off and why.
