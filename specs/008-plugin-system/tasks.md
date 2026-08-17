# Tasks — 008 The plugin system

**Written greenfield.** This list describes building the plugin system from nothing, to the current
standard, without reference to what the repository contains. It is reconciled against the codebase
afterwards; tasks the code already satisfies are marked with a citation and a passing test, and
everything else is work.

Nothing from the previous `tasks.md` is carried over.

Convention: every task states the requirement it serves and the test that proves it. A task is not
complete without both.

---

## Phase 1 — Foundation

- **T001** Create the `fairdm.contrib.plugins` app: `apps.py` with an `AppConfig`, `__init__.py`
  exporting the public surface, registered in the settings app list.
- **T002** Create the test package mirroring the source tree —
  `tests/test_contrib/test_plugins/{__init__,conftest}.py` — per Article X.
- **T003** Write factories for every core record a plugin can attach to (project, dataset, sample,
  contributor, location), one factory per model, in the project's factory module.
- **T004** Write `conftest.py` fixtures: a request factory, an anonymous user, an authenticated user
  with no permissions, a user with a model-level permission, a user with an object-level permission
  only, and one record of each core type.
- **T005** Write a fixture that registers throwaway plugins against a throwaway model and tears the
  registry down afterwards, so tests never depend on the plugins the framework ships.

## Phase 2 — US1: Register a view and get a working page

- **T006** `Plugin` base class: a `View` subclass carrying `name`, `url_path`, `permission`,
  `check`, `extra_views`, `registered_model` and `plugin_class`, all with defaults. *(FR-001)*
- **T007** `get_name()` — returns `name`, else the slugified class name. Test both. *(FR-002)*
- **T008** Delete the hand-rolled `slugify` and derive the name with
  `django.utils.text.camel_case_to_spaces` composed with `django.utils.text.slugify`. The bespoke
  version mangles acronyms — `URLTestPlugin` becomes `u-r-l-test-plugin` — and a current test
  asserts that as correct; correct the assertion with the code. *(FR-002)*
- **T009** `get_url_path()` — returns `url_path`, else the slugified class name; `None` means no
  segment of its own. Test all three. *(FR-002, FR-003)*
- **T010** `PluginRegistry` with a `register(*models, **options)` decorator returning the class
  unchanged, storing per model. Test that the decorated class is unchanged and is retrievable.
  *(FR-001)*
- **T011** `get_plugins_for_model()` returning registrations for a model, empty for an unregistered
  one. *(FR-001)*
- **T012** `get_urls_for_model()` returning one flat pattern per view, named `<plugin>`. *(FR-002)*
- **T013** Mount plugin URLs beneath each record's detail address in that record's URL
  configuration, under the record's namespace. *(FR-002, FR-005)*
- **T014** Test that a registered plugin is reversible by name through the record's namespace.
  *(FR-005)*
- **T015** **End-to-end**: request a registered plugin's address for a real record through the test
  client and assert 200. *(US1 sc.1)*
- **T016** Test that a plugin declaring `url_path` is served at that segment, not the derived one.
  *(FR-003, US1 sc.3)*
- **T017** Bind the model per mount via `as_view(registered_model=model)`; declare both initkwargs
  as class attributes so `as_view` accepts them. *(FR-004)*
- **T018** Test that one plugin registered against two models serves each independently — assert
  each mount resolves its own record type, and that the class attribute is untouched. *(FR-004,
  US1 sc.4)*

## Phase 3 — US2: Reach the record without disturbing the view

- **T019** Compose the existing related-object mixin rather than reimplementing record access; it
  already supplies a `base_object` `cached_property` over `get_object_or_404`, a configurable lookup
  kwarg, and `non_polymorphic_object`, which the template tags read first and which the polymorphic
  records need. Generalise its lookup to the declared map. *(FR-006)*
- **T020** Test `base_object` resolves for a polymorphic record accessed as its base type, and that
  `non_polymorphic_object` is present. *(FR-006)*
- **T021** Test `base_object` is in the template context and is the core record. *(FR-007)*
- **T022** Do **not** assign `self.object`. Test that a plugin over a `CreateView` still sees
  `self.object is None` in its own `get()`, and that a plugin over a `DetailView` keeps its own
  resolution. *(FR-008, US2 sc.1)*
- **T023** Test that a plugin over a stock `UpdateView` keeps its own `form_class`, `get_object`
  and `form_valid`. *(FR-008, SC-006)*
- **T024** Test a request naming a record that does not exist returns 404 through the URLconf, not
  an exception — the composed mixin's `get_object_or_404` supplies this. *(FR-009, US2 sc.3)*
- **T025** Model-level addressing: a model declares its URL route and an explicit kwarg-to-field map,
  defaulting to the `uuid` form. Not per-registration — two plugins on one model cannot disagree
  about how their shared record is found. *(FR-006)*
- **T025a** Reverse uses the declared map. The current helper hardcodes a `uuid` kwarg, and the
  navigation package filters kwargs and then swallows the failure, so a record without one renders
  an **empty menu rather than an error**. Test that a location plugin's entry renders a working
  href. *(FR-005, FR-006)*
- **T026** `get_breadcrumbs()` resolving the record's list address and the record's own address by
  reverse, not by literal. Test both hrefs resolve. *(FR-010, US2 sc.4)*
- **T027** Give `Plugin` a `page_title` default so a plugin that sets none does not raise while
  building its trail. *(FR-010)*
- **T028** Custom context: test a plugin adding its own keys keeps both its own and the system's.
  *(FR-036, US2 sc.5)*
- **T029** Declared assets: collect a plugin's stylesheets and scripts into the context and render
  them. Test the rendered response contains them. *(FR-035, US2 sc.6)*

## Phase 4 — US3: Visibility and reachability are one set

- **T030** `access.py` with `can_open(view_class, request, obj)`. *(FR-019, FR-020)*
- **T031** Read the predicate with `inspect.getattr_static`. Test that a plain function, a lambda,
  a `staticmethod` and an inherited attribute all receive `(request, obj)` identically. *(FR-017)*
- **T031a** Refuse a `check` that is neither callable nor a bool. `getattr_static` returns a
  `classmethod` object unchanged; it is **not callable but is truthy**, so a `callable()` guard falls
  through and publishes the page. Test that a `classmethod` predicate is refused at registration
  rather than silently permitting everyone. *(FR-017, FR-033)*
- **T032** Permission resolution as `has_perm(p) or has_perm(p, obj)`. Test a user with only a
  model-level permission and a user with only an object-level one — **both must pass**. *(FR-018,
  FR-021)*
- **T033** Memoise permission results on the request by `(permission, model label, pk)` — not
  `id(obj)`, which CPython reuses after collection, and the decision is reachable from template loops
  over temporary objects. **Export the helper**, because the real per-page cost is author predicates
  calling the permission check themselves, which an internal memo never sees. *(FR-021)*
- **T034** Subclass `PermissionRequiredMixin` and override `has_permission()` only. It already
  defines the permission normaliser, the predicate and the `dispatch` that delegates to
  `handle_no_permission`; the only difference this feature needs is the second, object-level call.
  *(FR-018)*
- **T035** Test an anonymous visitor is redirected to login and an authenticated one gets 403.
  *(FR-018)*
- **T036** The registry passes the navigation package an adapter closure calling `can_open`, never
  the author's function. *(FR-020)*
- **T037** Test that both the navigation path and the dispatch path reach the same function object,
  so they cannot diverge. *(FR-020)*
- **T038** The adapter catches predicate exceptions and hides the entry. Test that a predicate which
  raises does not break the page. *(FR-019)*
- **T039** **End-to-end**: a plugin whose predicate excludes the user shows no entry *and* refuses a
  direct request. Assert both in one test. *(FR-019, US3 sc.1–2)*
- **T040** **End-to-end**: a plugin whose permission the user lacks shows no entry. *(US3 sc.3)*
- **T041** Test a plugin narrowed to one subtype of a polymorphic record is neither listed nor
  reachable for another subtype. *(US3 sc.4)*
- **T042** Test a plugin with neither predicate nor permission is listed and reachable for any user.
  *(US3 sc.5)*
- **T043** Pin query counts with `django_assert_num_queries` on a record page carrying several
  plugins, for an anonymous user, a denied user and a granted user. *(SC-008)*

## Phase 5 — US4: A registration that cannot work is refused

- **T044** `checks.py` with a validation entry point called from the decorator. *(FR-034)*
- **T045** Refuse a registration naming no model, or naming a non-model. *(FR-027, US4 sc.3–4)*
- **T046** Refuse a duplicate plugin name on one model, naming both plugins and the model.
  *(FR-028, US4 sc.1)*
- **T047** Allow the same name on different models. *(FR-032, US4 sc.7)*
- **T048** Refuse a duplicate path segment on one model. *(FR-029, US4 sc.2)*
- **T049** Refuse a segment that cannot appear in a route by constructing it with `path()` inside a
  `try` and re-raising with the plugin named, rather than parsing converters by hand — `path()`
  already raises on an unknown converter. *(FR-030, FR-033, US4 sc.5)*
- **T049a** Refuse a duplicate **generated URL name** on one model. Segments and plugin names are not
  enough: a plugin `a` with a child `b` and a separate plugin `a-b` produce the same reverse name
  from different paths, and Django keeps the last one silently. *(FR-029, FR-031)*
- **T050** Test every refusal names the plugin, the model and the problem. *(FR-033)*
- **T051** Test refusal happens at registration, not at first request — assert the import itself
  raises. *(FR-034)*

## Phase 6 — US5: One plugin, several related views

- **T052** `extra_views` class attribute and `get_extra_views()` classmethod; nothing else reads the
  attribute. *(FR-022)*
- **T053** Mount each additional view beneath the parent's path, flat, named
  `<plugin>-<child>`. *(FR-023)*
- **T054** Test each additional view resolves and is served. *(US5 sc.1)*
- **T055** Bind `registered_model` and `plugin_class` on additional views exactly as on the parent.
  Test an additional view reaches the record. *(FR-025, US5 sc.4)*
- **T056** Test exactly one navigation entry appears for a plugin with additional views, and none
  for the children. *(FR-024, US5 sc.2)*
- **T057** An additional view declares its own permission, enforced at its own dispatch. Test a user
  refused the child while the parent stays reachable. *(FR-026, US5 sc.3)*
- **T058** Support a route converter in an additional view's segment, so it can address its own
  target. Test `<int:pk>/edit`. *(FR-023)*
- **T059** Refuse colliding segments among additional views, and between a child and the parent's
  own root. *(FR-031, US4 sc.6)*
- **T060** Refuse an additional view that is not a `Plugin`, and refuse recursion. *(FR-031)*

## Phase 7 — US6: Control the navigation entry, or decline it

- **T061** Build a navigation entry per registration from the decorator's `label`, `icon` and
  `order`. *(FR-011, FR-013)*
- **T062** Test the entry appears by default for a registered plugin. *(FR-011, US1 sc.2)*
- **T063** `menu=False` declines the entry; the plugin stays reachable. Test both halves. *(FR-012,
  US6 sc.1)*
- **T064** Honour `order`: entries render in position order, not registration order. Test with
  positions deliberately out of registration sequence. *(FR-014, US6 sc.2)*
- **T065** Test a declared label and icon are used. *(FR-013, US6 sc.3)*
- **T066** Default the label to a name derived from the view class and the icon to the framework
  default. *(FR-015, US6 sc.4)*
- **T067** A plugin must not be able to configure its entry through a class attribute. Test that
  such an attribute has no effect. *(FR-016)*
- **T068** Pass the record to predicates from the template that renders the navigation. *(FR-017)*

## Phase 8 — Wiring, removals, documentation

- **T069** Mount plugin URLs for every core record that serves a detail page. *(SC-007)*
- **T070** Wire the location record, declaring its coordinate lookup. *(SC-007)*
- **T071** Remove registrations against records that have no detail page of their own. *(SC-007)*
- **T072** Remove plugin templates that nothing selects, and any template extending a base that does
  not exist.
- **T073** Remove registrations that are syntactically broken at import.
- **T074** Write the plugin author's guide: registration, the URL a plugin gets, reaching the
  record, the predicate and permission contract with the guarantee stated plainly, additional views,
  declining an entry, and what a refused registration looks like. *(SC-001, SC-002)*
- **T075** Remove documentation describing the container, its error codes, and the interface that
  predates the current one.
- **T076** Correct the roadmap item whose motivating example this work falsifies.
- **T077** **End-to-end**: an addon-style package registers a plugin against a core model it does not
  own, and it is served. *(SC-002)*
- **T078** Full suite, lint, type checks and build green.

## Phase 9 — Added after design review

- **T079** `can_open` consults the **owning plugin's** predicate, not only the view's own. An
  additional view inherits the permissive default, so reading the predicate off the view class alone
  leaves a child of a restricted plugin reachable while its parent is refused and unlisted. The mount
  already binds the owning plugin; nothing read it. Test the child case directly. *(FR-019, SC-003)*
- **T080** The registry owns the per-model navigation object and creates it on first registration.
  They are currently five hand-written objects found by a string convention, one of which registers
  under a different name than its variable, and a record with none makes the registry append to
  `None`. *(FR-011)*
- **T081** State and test the context contract: `base_object` is the core record, `object` stays the
  view's own object, and the plugin system never assigns `self.object`. *(FR-007, FR-008)*
- **T082** Migrate the four consumers that read `object` as the core record today — the base
  template, the template tags, the contributor overview template, and the contributor plugin module,
  which also calls a method defined nowhere in the tree. *(FR-008)*
- **T083** Navigation tests assert entry **contents**, not merely a 200 response. A missing context
  key renders empty, the reverse fails, and the entry is hidden — so a page with no navigation at all
  still returns 200. *(FR-011, FR-013)*
- **T084** Give every surviving shipped registration explicit `label`, `icon` and `order` kwargs.
  Removing the class-attribute fallback otherwise leaves around ten of them rendering a slugified
  class name and the default icon. *(FR-013, FR-015)*
- **T085** Remove the `menu` class attribute from the shipped plugins that declare one. *(FR-016)*
- **T086** Replace, do not merely delete, the templates that live plugins serve. Four extend a base
  template that does not exist; deleting them leaves those plugins with no template at all. *(SC-001)*
- **T087** Remove the template lookup chain in the generic plugin module. It is the chain the
  decisions record orders removed, and it reads an attribute no class defines. *(FR-008)*
- **T088** Fold the predicate helpers into the access module and delete the separate module.
- **T089** A system check reports a registration against a model with no mounted attachment point.
  This cannot be caught in the decorator, because no URL configuration exists when it runs — so it is
  a weaker guarantee than the rest, and recorded as such. It is also the failure that let five
  registrations sit inert. *(FR-027)*
