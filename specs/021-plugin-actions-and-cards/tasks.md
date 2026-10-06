# Tasks: Plugins contribute page actions and overview cards, and can be removed or replaced

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md)

**Tests first**: in every story the test tasks come first and are seen to fail before the code
that makes them pass is written. Registry rules are tested directly on a registry the test fills.
Page behaviour is tested by registering a plugin the way an addon would and opening the real
overview through the Django test client, once for each kind of visitor the scenario names. Wording,
layout and styling get no tests.

**Existing behaviour**: every existing test in `tests/test_contrib/test_plugins/` and the record
types' own `test_plugins.py` keeps passing unchanged. A change to one of them is a sign that SC-009
has been broken, and is not made.

**Format**: `[ID] [Story] Description`.

**Story order**: US1, US2, US3, US4, each from the previous story's accepted commit.

## Phase 1: US-1, an addon adds an action any visitor can take (P1)

This story also lays the ground the others stand on: the declared place, the method that works out
what a record type serves, and the validation at startup.

- [ ] T001 [US1] `tests/test_contrib/test_plugins/test_places.py`, new. `TestPlaceOption`: no
  `place` gives a navigation mount (FR-002); `"action"` and `Place.ACTION` are both accepted; an
  unknown place is refused when registered; a `column` on something that is not a card is refused
  when registered. `TestResolve`: one mount per registration, carrying the plugin's name, segment,
  label, icon and order; `menu=False` gives a mount that is served and not listed; resolving twice
  gives the same list. `TestPageActions`: `get_page_actions` returns action mounts only, in `order`
  and then name, and the same list when the same plugins are registered in the opposite order
  (scenario 5, FR-011). `TestRecordTypeOffersPlaces`: an action registered against `Point` is
  refused by `validate_all`, naming the plugin and the record type (FR-005); the same registration
  against `Sample` is accepted.
- [ ] T002 [US1] `tests/test_contrib/test_plugins/test_registration.py`, added to.
  `TestNavigationUnchanged`: with an action registered beside pages, the navigation menu lists the
  pages and not the action (scenario 2, FR-008), and the URL patterns include the action under its
  own name (FR-007). `tests/test_apps.py`, added to: `FairDMConfig.ready()` validates the
  registry, shown by a declaration that cannot work raising from it.
- [ ] T003 [US1] `tests/test_templates/test_overview_page_actions.py`, new, through the test
  client. For each of project, dataset, sample, measurement, person and organization: an action
  registered for that record type is offered on its overview with the plugin's address for that
  record (scenarios 1 and 10). On one record type: a visitor who is not signed in is offered an
  unrestricted action (7); an action whose predicate excludes the visitor is not in the response
  and its address is refused (3); the same for a permission the visitor lacks (4); with no action,
  and with every action hidden, the dropdown's hook is absent from the response (6, FR-012); a
  predicate that raises hides the action, the page is served and the failure is logged; a person
  with rights over the record gets both the Manage menu and the dropdown, and the action is not
  inside the Manage menu (8); an action registered against contributors and narrowed to people
  with `is_instance_of` is absent from an organization's overview and refused at its address (9);
  an action registered with `menu=False` is served at its address and not offered. The dropdown is
  found by a `data-` hook on the component, never by its label. First, one fixture in
  `tests/conftest.py`: it saves the registry, lets the test declare plugins, rebuilds every record
  type's URL patterns and clears the URL caches, and restores the registry and the URL
  configuration afterwards. Every page test in this feature uses it.
- [ ] T004 [US1] Implement to make T001 to T003 pass (plan D1 registrations, D2, D3 steps 1, 6 and
  7, D4, D5):
  - `fairdm/contrib/plugins/places.py`: `Place`, `Column`, `OverviewPlaces` with `page_actions`
  - `registration.py`: `Mount`, `resolve`, `get_page_actions`, `validate_all`; `get_urls_for_model`
    and the navigation built from mounts
  - `base.py`: `Plugin.get_urls` takes `name` and `url_path`
  - `checks.py`: the registration-time checks for `place` and `column`
  - `fairdm/apps.py`: `validate_all()` after the `plugins` modules are imported
  - `fairdm/core/plugins.py`: `OverviewPlugin` carries `OverviewPlaces`
  - `fairdm/templates/cotton/plugins/actions.html` and the `overview.page_actions` block in
    `overview/page.html`, with the block added to the template's own block list
  - `__init__.py`: export `Place`
- [ ] T005 [US1] Documentation: in `docs/portal-development/create_a_plugin.md`, "Where a plugin
  appears" and "A page action" with a working example, and the new refusals under "When a
  registration is wrong". `docs/portal-development/overview-pages.md` gains the
  `overview.page_actions` block. `CONTEXT.md` gains "page action" and "Manage menu".

## Phase 2: US-2, an addon adds a card to the overview (P1)

- [ ] T006 [US2] `tests/test_contrib/test_plugins/test_cards.py`, new. `TestCardRegistration`: a
  class that cannot be drawn is refused as a card when registered; a card with no `column` resolves
  to the side column (scenario 6, FR-019); `"wide"` is accepted; a card's name clashing with
  another plugin's on the record type is refused; `menu=False` on a card is refused.
  `TestCardMounts`: `get_cards` returns card mounts only, in `order` then name, the same whichever
  order they were registered in (7, FR-020); a card contributes no URL pattern at its own name and
  one per further view beneath it; a card has no navigation entry and is not among the page actions
  (2, FR-016). `TestRenderCard`: `render_card` draws the template with the record and the request.
  `TestRecordTypeOffersPlaces`, added to in `test_places.py`: a card registered against `Point` is
  refused by `validate_all`.
- [ ] T007 [US2] `tests/test_templates/test_overview_cards.py`, new, through the test client. For
  each of the six record types: a registered card's content is in the overview and was drawn with
  that record (scenarios 1 and 11). On one record type: a card whose predicate excludes the viewer,
  and one whose permission they lack, leave nothing in the response (3, FR-017); a further view
  owned by a hidden card is refused, both when the predicate hides the card and when only its
  permission does (4, FR-018), and is served to a viewer the card admits; a further view of a card
  that states no predicate, on a private project, is refused to a stranger and served to someone
  who can open the project; a side card follows the
  page's own side cards and a wide card follows the wide column's own content, checked by position
  in the response against a hook the page already has (5, FR-020); two cards in one column come out
  in `order` (7); a card that raises is left out, the page answers 200, the other card is still
  drawn and the failure is logged (9, FR-022); a card narrowed to one sample type is not drawn on
  another (10); a card with nothing to show is still drawn (FR-024); a card's stylesheet and script
  are in the response when it is drawn and absent when it is hidden (12, FR-023); with no cards the
  response has no contributed-card markup (8, FR-021).
- [ ] T008 [US2] Implement to make T006 and T007 pass (plan D6, the card parts of D3 and D4):
  - `fairdm/contrib/plugins/cards.py`: `Card` with `render_card`
  - `registration.py`: `get_cards`; card mounts contribute only their further views' patterns
  - `checks.py`: the registration-time checks for a card
  - `base.py`: `has_permission` requires the owning card's decision for a card's further views
  - `places.py`: `OverviewPlaces` supplies `overview_cards` and merges drawn cards' media into
    `plugin_media`
  - `overview/page.html`: the `overview.contributed_main` and `overview.contributed_side` blocks
  - `__init__.py`: export `Card` and `Column`
- [ ] T009 [US2] Documentation: "An overview card" in `create_a_plugin.md` with a working example
  covering the column, a further view and assets; the two new blocks in `overview-pages.md`;
  "overview card" in `CONTEXT.md`; the card refusals under "When a registration is wrong".

## Phase 3: US-3, a portal or an addon takes a registered plugin away (P2)

- [ ] T010 [US3] `tests/test_contrib/test_plugins/test_registration.py`, added to. `TestRemove`: a removed
  plugin has no mount, so no URL pattern for itself or its further views, no navigation entry, no
  action and no card, for a plugin in each of the three places (scenarios 1 and 5, FR-025, FR-026);
  the removal is accepted by class and by name; removed from one record type, it is still mounted
  on another (4, FR-027); the result is the same whether `remove` is called before or after
  `register` (6, FR-028); `get_plugins_for_model` still returns the registration, so nothing is
  deleted from what was declared. `TestRemoveRefusals`: a removal naming a plugin not registered
  against that record type is refused by `validate_all`, naming the removal and the record type
  (7, FR-029); a removal of a record type's overview is refused and the message says it can be
  replaced, for a project, whose overview is at the record's own address, and for a sample, whose
  overview is at `overview/` (9, FR-030). The registry fixtures, the one in
  `tests/test_contrib/test_plugins/conftest.py` and the one in `tests/conftest.py`, save and
  restore removals.
- [ ] T011 [US3] `tests/test_templates/test_overview_removed_plugins.py`, new, through the test
  client. A removed plugin's former address
  answers 404, as does an address that never existed (2); its name does not reverse (3);
  `plugins.reverse(..., default="")` and `{% plugin_url %}` give an empty string for it. For every
  plugin FairDM registers that can be removed, on every record type it is registered against: with
  it removed, that record type's overview answers 200 for a visitor and for someone who can manage
  the record, carries no link to the former address, and has no anchor whose address is empty or
  `None` (8, FR-032, SC-006). The list of plugins is read from the registry, so a plugin added
  later is covered without editing the test. With `contribution-list` removed from projects, a
  dataset's Contributors page answers 200 for a manager and for a visitor and links to no project
  Contributors page; the same for a sample's page with it removed from datasets. A removed plugin's stored rows are still there (10, FR-031).
- [ ] T012 [US3] Implement to make T010 and T011 pass (plan D1 removals, D3 step 2, D7):
  - `registration.py`: `remove`, and the removal step of `resolve`
  - `__init__.py`: export `remove`
  - `utils.py`: `reverse` takes `default`
  - `templatetags/plugin_tags.py`: `plugin_url` gives an empty string for a name that does not
    resolve
  - `templatetags/plugin_tags.py` and the older tag in `fairdm/templatetags/fairdm.py` alike
  - `fairdm/core/plugins.py`, `contributors/plugins/shared.py` (both links to the record above)
    and every shipped template that draws an entry leading to a plugin, whether its address comes
    from `plugins.reverse`, `safe_reverse` or `{% plugin_url %}`: the entry is left out when there
    is no address. Plan D7 lists them. A template nothing includes is left alone
- [ ] T013 [US3] Documentation: "Removing a plugin" in `create_a_plugin.md` with a working example,
  saying what happens to the address and that the overview cannot be removed; the removal refusals
  under "When a registration is wrong"; a note in the section on linking that a link to another
  plugin should allow for its removal.

## Phase 4: US-4, an addon swaps a shipped plugin for its own (P2)

- [ ] T014 [US4] `tests/test_contrib/test_plugins/test_registration.py`, added to. `TestReplace`: the
  mount carries the replacement's class under the target's name and segment (scenarios 1 and 2,
  FR-034); stating nothing, it keeps the target's label, icon and order, and a card its column (3,
  FR-036); stating one of them, it uses that and keeps the rest (4); the replaced class contributes
  no patterns, and the replacement's further views are named under the target's name (6, FR-038);
  replaced on one record type, the original is mounted on another (7); the result is the same
  whichever of the two is registered first, for a replacement that keeps its target's own segment
  (8, FR-039); a replacement of a page registered with `menu=False` is not listed either; a replacement of a replacement is served at
  the first plugin's address (FR-042); the target given by class and by name. `TestReplaceRefusals`,
  each by `validate_all` and each naming what the specification says: two replacements for one
  plugin (9); those two with one removed starts, and the other stands, for a page and for a record type's
  overview (10, FR-040); a target not
  registered against the record type, and a target that is removed (11, FR-041, naming the
  replacement and the removal); a replacement in a different place from its target (12, FR-035); a
  cycle; a replacement whose further views would clash with another mount's URL names.
- [ ] T015 [US4] `tests/test_templates/test_overview_replaced_plugins.py`, new, through the test
  client. The target's address serves the replacement and the target's name reverses to it (1, 2,
  SC-005); the navigation has one entry in the target's position (3); the access decision is the
  replacement's own: a visitor the target admitted and the replacement excludes is refused, and the
  reverse is admitted (5, FR-037); a replaced page action and a replaced card are each offered or
  drawn once, as the replacement; a replacement for a record's overview built on the shipped
  overview still shows a registered page action and a registered card (13).
- [ ] T016 [US4] Implement to make T014 and T015 pass (plan D3 steps 3 to 6, D8):
  - `registration.py`: the replacement steps of `resolve`
  - `checks.py`: a registration with `replaces` is left out of the segment and URL-name
    comparison made at registration, on both sides of it
- [ ] T017 [US4] Documentation: "Replacing a plugin" in `create_a_plugin.md` with a working
  example, covering what carries over, what does not, replacing the overview, and how a portal
  settles two addons replacing the same plugin, and that a replacement built on a plugin which sets
  `name` must set its own; the replacement refusals under "When a registration
  is wrong".

## Phase 5: fixes from the code review

- [ ] T018 [US1] Page actions and registration checks. An action whose address does not resolve
  from the record alone is left out of the dropdown and logged, and the overview is served. An
  `order` that is not a whole number is refused when the registration is made. The two tests of the sandbox fixture close it in a `finally`. The docstrings of
  `can_open` and `Plugin` say a further view is decided by its own rule. `CHANGELOG.md` has the
  feature's entries, and `CONTEXT.md` lists `remove` among the plugin system's exports.
- [ ] T019 [US2] Cards. A card with no segment of its own (`url_path = None`) is refused when
  registered. A further view of a card answers 404 when the record's overview refuses the viewer,
  so it does not confirm that a private record exists.
- [ ] T020 [US3] Removals. `plugins.remove` given something that is neither a plugin class nor a
  name, or a record type that is not a model, is refused with a named error.
