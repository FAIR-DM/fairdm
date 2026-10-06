
## 2026-10-06T21:23:29Z · Planner · plan

Did: wrote research.md, plan.md, tasks.md (17 tasks over 4 stories) and the ledger, on the branch brought up to date with origin/main at dafb8efb.
Verified: the application starts and answers from this branch after uv sync and migrate.
Next: design review, one reviewer with three lenses.
Watch: US-1 carries the groundwork every later story builds on, so it is the largest of the four.

## 2026-10-06T21:36:55Z · Implementer US1 · T001

Did: wrote tests/test_contrib/test_plugins/test_places.py (place option, resolve, page actions, record types that offer places).
Verified: uv run pytest tests/test_contrib/test_plugins/test_places.py -q -n0 fails at collection, ModuleNotFoundError fairdm.contrib.plugins.places, which is the missing feature. pre-commit passes.
Next: T002 tests for the navigation and startup validation.
Watch: Place has no card member yet; a column is refused whatever the place.

## 2026-10-06T21:37:27Z · Implementer US1 · T002

Did: added TestNavigationUnchanged to test_registration.py and TestPluginRegistryValidatedAtStartup to tests/test_apps.py.
Verified: uv run pytest on both classes -q -n0: 2 failed (action listed in navigation; ready() does not refuse an action against Point), 3 passed. The passing action-served-under-its-own-name test guards FR-007 while the patterns are rebuilt from mounts; it passed before the change because an unrecognised place is ignored today.
Next: T003 page tests and the registry-and-URL fixture.
Watch: ready() is called a second time in-process by these tests; it is safe to repeat.

## 2026-10-06T21:40:07Z · Implementer US1 · T003

Did: added the PluginSandbox fixture (plugin_sandbox) to tests/conftest.py, tests/test_conftest.py proving a declared plugin and its address are gone after close, and tests/test_templates/test_overview_page_actions.py (six record types, visitors, predicate, permission, subtype narrowing, empty and hidden, raising predicate, order, apart from the Manage menu).
Verified: uv run pytest tests/test_conftest.py -q -n0: 2 passed. uv run pytest tests/test_templates/test_overview_page_actions.py -q -n0: 13 failed, 3 passed; the failures are the dropdown listing nothing where an action is expected. pre-commit passes.
Next: T004 implementation.
Watch: the sandbox imports the six URL modules, the core include module and the root URL configuration again, so a portal with record types mounted elsewhere is not covered.

## 2026-10-06T21:43:27Z · Implementer US1 · T004

Did: added fairdm/contrib/plugins/places.py (Place, OverviewPlaces with page_actions), Mount, resolve, get_page_actions and validate_all on the registry, validate_options, validate_mounts and validate_places_offered in checks.py, name and url_path on Plugin.get_urls, validate_all from FairDMConfig.ready, OverviewPlaces on OverviewPlugin, the c-plugins.actions component and the overview.page_actions block; export Place. Corrected my T001 tests so registries that hold an action also hold an overview, and added two tests of get_urls.
Verified: uv run pytest tests/test_contrib/test_plugins tests/test_templates tests/test_core/test_project tests/test_core/test_dataset tests/test_apps.py tests/test_conftest.py -q -n auto --dist loadscope: 1195 passed. Probe: making the dropdown list every action regardless of access fails four page tests. pre-commit passes.
Next: T005 documentation, then the full verify.
Watch: the full suite has not run yet.

## 2026-10-06T21:44:24Z · Implementer US1 · T005

Did: documented the places in docs/portal-development/create_a_plugin.md (Where a plugin appears, A page action, the new refusals), the overview.page_actions block in overview-pages.md, and page action and Manage menu in CONTEXT.md.
Verified: ran the two documented examples (a dataset action for signed-in visitors and a contributors action narrowed to people) in a throwaway test through the test client; both were offered and opened. The throwaway test was not kept.
Next: full verify, then the report.
Watch: docs build is part of the full verify.

## 2026-10-06T21:57:19Z · Implementer US2 · T006

Did: wrote tests/test_contrib/test_plugins/test_cards.py (TestCardRegistration, TestCardMounts, TestRenderCard) and added the Point and accepted-card cases to TestRecordTypeOffersPlaces in test_places.py. Test cards draw a template added under tests/registry_models/templates/plugin_cards/.
Verified: collection fails with ModuleNotFoundError for fairdm.contrib.plugins.cards, which is the expected red; nothing implemented yet.
Next: T007 page tests, then the implementation.
Watch: a card registered as a page or an action is refused at registration (added beyond the task list because a navigation entry for a card has no address to reverse).

## 2026-10-06T21:57:19Z · Implementer US2 · T007

Did: wrote tests/test_templates/test_overview_cards.py through the plugin_sandbox fixture: each record type, who sees a card, further views of a card (predicate, permission, private project), where a card is drawn, failures, nothing to show, assets, and no cards.
Verified: collection fails on the missing Card module, the expected red.
Next: T008 implementation.
Watch: position is checked by siblings inside the column and the data-contributed-card hook the template loop will emit, since the wide column has no hook of its own.

## 2026-10-06T22:02:39Z · Implementer US2 · T008

Did: added fairdm/contrib/plugins/cards.py (Card with render_card, get_media, admits and a get_urls that drops the card's own pattern), Place.CARD and Column and the card drawing in OverviewPlaces (access check, try around the drawing with the failure logged, media merged only for cards that were drawn), Mount.column, get_cards, the card rules in validate_options, the owning card's decision in Plugin.has_permission, the overview.contributed_main and overview.contributed_side blocks, and Card and Column in the exports. No story 1 test needed to change: the one that asserts a column on a non-card is refused still holds.
Verified: uv run pytest tests/test_contrib/test_plugins tests/test_templates tests/test_core/test_project tests/test_core/test_dataset tests/test_apps.py tests/test_conftest.py -q -n auto --dist loadscope: 1253 passed. uv run pytest tests/test_contrib/test_contributors tests/test_core/test_sample tests/test_core/test_measurement: 2683 passed, 13 skipped. pre-commit run --all-files passes. Probes, each failing the named tests and then reverted: dropping Card.admits from has_permission (3 failures), dropping the overview check in admits (1), dropping the card's own decision (2), dropping the access check when drawing (6), never merging media (1), putting the side block before the column (1), removing the try around drawing (2), drawing wide cards in the side column (2).
Next: T009 documentation, then the full verify.
Watch: decisions D12 to D14.

## 2026-10-06T22:03:32Z · Implementer US2 · T009

Did: documented the card in docs/portal-development/create_a_plugin.md (the place table, An overview card with the column, a further view and assets, who sees a card, the further-view rule, the new refusals under When a registration is wrong, Mount.column and get_cards), the two contributed blocks in overview-pages.md, and overview card plus the exports in CONTEXT.md.
Verified: ran the documented example (a dataset card in the wide column for signed-in visitors with a further view and assets) in a throwaway test through the test client: hidden and refused to a visitor who is not signed in, drawn with a working link to its further view for one who is, assets present, no address at the card's own name. The throwaway test and its templates were not kept.
Next: full verify, then the report.
Watch: the docs build is part of the full verify.
