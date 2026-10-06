
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

## 2026-10-06T22:14:33Z · Implementer US3 · T010

Did: Added TestRemove (parametrized over navigation, action and card) and TestRemoveRefusals to tests/test_contrib/test_plugins/test_registration.py. They cover no mount/pattern/entry/action/card after removal, removal by class and by name, still mounted on another record type, same result whichever of remove/register came first, get_plugins_for_model unchanged, and the refusals for an unregistered target and for the overview of a project and a sample.
Verified: `uv run pytest tests/test_contrib/test_plugins/test_registration.py -q -n0 -k TestRemove` -> 26 failed, all with AttributeError on registry.remove (the right reason, the method does not exist yet). pre-commit run --all-files passed.
Next: T011, the page tests through the client.
Watch: the registry fixtures (isolate_registry, PluginSandbox) save and restore removals once the registry has somewhere to keep them, so that edit lands with T012.

## 2026-10-06T22:16:24Z · Implementer US3 · T011

Did: Added tests/test_templates/test_overview_removed_plugins.py. For every plugin FairDM registers on a record type with an overview (read from the registry when the tests are collected, minus the overview itself), it removes the plugin through the sandbox, opens the overview as a visitor and as a manager, and asserts a 200, no link to the former address and no anchor with an empty or None address. It also asserts the former address answers 404 like an unknown one, that the name does not reverse, that reverse(default="") and both plugin_url tags give an empty string, that a dataset's and a sample's Contributors pages are served without a link to the record above (each first shown to carry that link before the removal), and that a removed plugin's credits are still stored.
Verified: with a temporary is_overview stub that I removed again, `uv run pytest tests/test_templates/test_overview_removed_plugins.py -q -n0` -> 31 failed, 7 errors, every one on `fairdm.plugins` having no `remove` (the right reason). pre-commit run --all-files passed.
Next: T012, the implementation.
Watch: Point has a registration but no overview page to open, so it is not in the parametrized list.

## 2026-10-06T22:21:12Z · Implementer US3 · T012

Did: registry.remove and its export as plugins.remove (registration.py, __init__.py); removals kept per record type and judged in resolve() by checks.validate_removals, which refuses a name not registered for the record type and the overview (checks.is_overview), with its own wording; validate_all also resolves a record type that has only a removal; both registry fixtures (isolate_registry, PluginSandbox) save and restore removals; plugins.reverse takes default=; both plugin_url tags give an empty string for a name that does not resolve; the People card's link, the Contributors pages' two links to the record above (and the button and link in contribution_list.html), the sample Manage menu, the project Manage entry, stats tiles and record cards on project, person and organization pages now draw a link only when it has an address. Corrected two of my own T010 tests: the card case asserted a pattern at the card's own name, and a wording assertion on "registered against" contradicted the refusal text.
Verified: `uv run pytest tests/test_contrib/test_plugins/test_registration.py tests/test_templates/test_overview_removed_plugins.py -q -n0` green (T010 and T011 now pass); `uv run pytest tests/test_templates tests/test_contrib/test_plugins tests/test_contrib/test_contributors tests/test_core -q -n auto --dist loadscope` -> 4111 passed, 13 skipped. pre-commit run --all-files clean.
Next: T013, the documentation.
Watch: project/plugins/overview.html and the dataset, sample and measurement ones beside it extend a template that does not exist, and cotton/contributor/card/contribution.html is referenced by nothing; none edited, all listed in the report.

## 2026-10-06T22:22:08Z · Implementer US3 · T013

Did: Added "Removing a plugin" to docs/portal-development/create_a_plugin.md (remove by class or name, what happens to the address, name, entry, stored data and get_plugins_for_model, and that the overview cannot be removed); two removal refusals under "When a registration is wrong"; a note under "The address" that a link to another plugin asks with reverse(..., default="") and {% plugin_url %}; resolve() described as one mount per registration not removed; replaced the sentence saying an additional view inherits its plugin's check with the rule the page's own example shows. Added a short section to overview-pages.md on pages served without a removed plugin's link.
Verified: ran the page's example against the branch (import Keywords, plugins.remove by class and by name, validate_all, resolve no longer lists keywords, get_plugins_for_model still does). pre-commit run --all-files clean. The docs build runs in the full verify below.
Next: full verify and the completion report.
Watch: the page says nothing about replacing the overview, because replacement is not built yet.

## 2026-10-06T22:47:08Z · Implementer US4 · T014

Did: Added TestReplace, TestReplaceKeepsOnlyWhatIsStated, TestReplaceTheNavigation, TestReplaceFurtherViews, TestReplaceAReplacement, TestReplaceTheOverview, TestReplaceRefusals, TestReplacesNamesAPlugin and two small place classes to tests/test_contrib/test_plugins/test_registration.py. They cover the mount carrying the replacement's class under the target's name and segment (by class and by name, for a page, an action and a card), carry-over of label, icon, order, column and a declined entry unless stated, the replaced class contributing no patterns, the replacement's views named under the target's, a replacement with the target's own segment accepted in either order, chains, the overview and its removal, and every refusal.
Verified: uv run pytest tests/test_contrib/test_plugins/test_registration.py -q -n0 -k Replace -> 58 failed, 26 passed before any implementation, each failing on the replacement being ignored or refused at registration (the right reason). The passing ones are checks of behaviour that already held, such as a Card registered with no place being refused.
Next: T015, the page tests through the client.
Watch: the registry tests build navigation in detached menus, as TestRemove does.

## 2026-10-06T22:47:08Z · Implementer US4 · T015

Did: Added tests/test_templates/test_overview_replaced_plugins.py. Through the client it checks that the target's address serves the replacement and its name reverses there while the replacement's own name does not, that the replaced class's views are not served unless the replacement declares them, that the original is still served on another record type, that the navigation has one entry in the target's position (or the position the replacement states), both directions of the access decision for check and permission, a replaced page action and a replaced card each drawn once as the replacement, and a replacement for each record type's overview still showing a registered action and card.
Verified: uv run pytest tests/test_templates/test_overview_replaced_plugins.py -q -n0 before the implementation: failures only, each the replacement not being served, its registration being refused, or the replaced overview not being removable.
Next: T016, the implementation.
Watch: the shipped Keywords page of a sample does not open at all (ImproperlyConfigured, no queryset), so the examples use Descriptions.

## 2026-10-06T22:47:08Z · Implementer US4 · T016

Did: registration.py gets Candidate (a registration with the options it was made with), Mount.replaced_by and PluginRegistry.collapse, and resolve() now runs removals, replacement checks, collapse, the clash check on the final mounts and the places check in that order. checks.py gets Claim (name, segment and URL names of one plugin or one mount), validate_replacements, validate_place_kept and a check that replaces is a plugin class or a name; validate_against_existing leaves a registration that states replaces out of the segment and URL-name comparison on both sides; the overview refusal in validate_removals applies only to a registration that states no replaces.
Verified: uv run pytest tests/test_contrib/test_plugins tests/test_templates tests/test_core/test_project/test_plugins.py -q -n auto --dist loadscope -> 710 passed. Probes: with the replaces skip taken out of validate_against_existing 9 tests fail; with the overview rule put back 3 fail. pre-commit run --all-files clean.
Next: T017, the documentation.
Watch: url_names_for is gone, replaced by Claim.url_names, so a mount's URL names use its served name.

## 2026-10-06T22:47:09Z · Implementer US4 · T017

Did: Added Replacing a plugin to docs/portal-development/create_a_plugin.md (the example, what carries over and what does not, the order not mattering, a replacement built on a plugin that sets name, the overview, chains and removing a link, two addons replacing one plugin) and the replacement refusals under When a registration is wrong; resolve() described as one mount per plugin served; the overview note in Removing a plugin and in overview-pages.md now say it can be replaced.
Verified: ran the page's examples against the branch in a throwaway test (replace Descriptions, a chain of two, replace the dataset overview, remove the last link) and it passed; I deleted the test. pre-commit run --all-files clean.
Next: the full verify and the completion report.
Watch: no changelog entry, none exists for the earlier stories either.

## 2026-10-06T23:22:31Z · Converge · converge

Did: brought the branch up to date with origin/main; wrote ADRs 0026 and 0027 and gave every decision its verdict; renamed the three names this feature added with a leading underscore; read the requirements against the tests.
Verified: lint, types, the whole suite, build, structure and documentation checks pass on the whole feature; no test that existed on main was changed.
Next: code review.
Watch: three older tests that create many people fail now and then (#440). A sample's Keywords page does not open (#441). Neither is caused by this feature.

## 2026-10-06T23:34:25Z · Implementer FIX-1 · T018

Did: Page actions whose address needs more than the record are left out and logged; an order that is not a whole number is refused at registration; the two sandbox tests close in a finally; the docstrings of can_open and Plugin.plugin_class state the real rule; CHANGELOG.md and CONTEXT.md carry the feature.
Verified: new tests failed first (NoReverseMatch on the overview, DID NOT RAISE for order), then `uv run pytest tests/test_conftest.py tests/test_contrib/test_plugins tests/test_templates/test_overview_page_actions.py -q -n0` gave 358 passed; `uv run pre-commit run --all-files` passed.
Next: T019 cards.
Watch: none.
