# Plan — 008 The plugin system

Derived from `spec.md` and `research.md`, and revised after design review. The findings that changed
it are noted inline as **[review]**.

## Shape

`fairdm/contrib/plugins/` becomes six modules:

| Module | Holds |
|---|---|
| `base.py` | `Plugin` — declaration surface, URL generation, record access, context |
| `access.py` | `can_open()`, the permission helper and its request memo, and the predicate helpers moved from `visibility.py` |
| `checks.py` | registration-time validation. **New** — rebuilt, not restored. |
| `registry.py` | model → plugin map, addressing, URL aggregation, navigation construction |
| `menus.py` | the renderer only; the per-model navigation objects move into the registry |
| `utils.py` | reverse |

`visibility.py` folds into `access.py`. `slugify` is deleted — see below.

## The declaration surface

```python
@plugins.register(Sample, label=_("Analysis"), icon="chart", order=50)
class Analysis(Plugin, FairDMTemplateView):
    url_path = "analysis"
    permission = "sample.view_sample"
    check = staticmethod(is_instance_of(RockSample))
    extra_views = [AnalysisEdit]
```

- `menu` as a class attribute is deleted (FR-016). Label, icon and position come from the decorator.
  Declining an entry is `menu=False` (FR-012).
- `extra_views` is the declaration; `get_extra_views()` is the only thing that reads it.
- An additional view is an ordinary `Plugin` subclass.
- `url_path` may carry a route converter, `"<int:pk>/edit"`.

**[review] Use Django's own slugify.** `django.utils.text.camel_case_to_spaces` composed with
`django.utils.text.slugify` replaces the four hand-rolled regexes in `utils.py`. The bespoke version
mangles acronyms — `URLTestPlugin` becomes `u-r-l-test-plugin`, and a current test asserts that as
correct. Django's pair gives `url-test-plugin`. The assertion is corrected with the code.

## Record addressing

**[review] This is a model-level declaration, not a per-registration one, and the example in the
previous draft was a no-op** — `registry.register` is the plugin decorator, so calling it with a
model and no class returns a decorator and registers nothing.

Addressing belongs to the model because two plugins on one model cannot disagree about how their
shared record is found:

```python
registry.declare_addressing(
    Point,
    route="<str:lon>/<str:lat>",
    lookup={"lon": "x", "lat": "y"},      # url kwarg -> model field, explicit both ways
)
```

The default, applied to every core record that does not declare otherwise, is
`route="<str:uuid>"`, `lookup={"uuid": "uuid"}`.

The map is explicit in both directions because **reverse is the harder half and the previous draft
ignored it.** `utils.reverse` hardcodes `kwargs.update({"uuid": model.uuid})` and `base.html` passes
`uuid=object.uuid`. Both give `NoReverseMatch` for a record with no `uuid`, and the navigation
package filters kwargs and then swallows the failure, so a location menu would render **empty rather
than erroring** — the silent mode this feature exists to end. So:

- `utils.reverse` builds its kwargs from the model's declared map.
- The navigation entry resolves its kwargs from the record, not from a hardcoded `uuid=`.
- A test asserts a location plugin's entry renders with a working href, not merely that the page is
  200.

## Reaching the record

**[review] Compose `RelatedObjectMixin`, do not reimplement it.** `fairdm/views/mixins.py:30-68`
already supplies a `base_object` `cached_property` built on `get_object_or_404` — which is FR-009
for free — a configurable lookup kwarg, and a context carrying `base_object`, `base_model`,
`non_polymorphic_object` and the record under its model name. `non_polymorphic_object` is
load-bearing: `plugin_tags.py:31` reads it first, and `Sample` and `Contributor` are both
polymorphic. Generalise its lookup to the declared map and use it.

**The context contract, stated explicitly [review]:**

- `base_object` is the core record the plugin hangs from. Always present.
- `object` remains the *view's own* object, whatever the view class decides that is. For a plugin
  over a `DetailView` of the record, they are the same. For a `CreateView` child, `object` is `None`
  and `base_object` is the record.
- `self.object` is never assigned by the plugin system (FR-008).

Four live consumers read `object` as the core record today and are migrated with the change:
`base.html`, `plugin_tags.py`, the contributor overview template, and
`contributors/plugins/shared.py` — which also calls `get_plugin_url`, a method defined nowhere in
the tree. A test asserts the navigation entries' **contents**, not merely a 200, because a missing
context key renders as empty, the reverse fails, and the entry is hidden — so a page with no
navigation at all still returns 200.

## Visibility and access

One function, two callers:

```python
def can_open(view_class, request, obj) -> bool
```

- **[review] It consults the owning plugin's predicate, not just the view's own.** An additional
  view inherits `Plugin.check = True`, so reading the predicate off the view class would leave a
  child of a restricted plugin reachable while its parent is refused. The previous draft called that
  acceptable; it is not — the predicate belongs to the plugin and the child belongs to the plugin,
  so FR-019 and SC-003 both fail. `plugin_class` is already bound per mount and is what `can_open`
  reads.
- The predicate is read with `inspect.getattr_static`, so a plain function, a lambda, a
  `staticmethod` and an inherited attribute all behave identically.
- **[review] A `classmethod` predicate is refused at registration.** `getattr_static` returns the
  `classmethod` object, which is not callable but *is* truthy, so a `callable()` guard falls through
  to `bool(check)` and publishes the page. A `check` that is neither callable nor a bool is a
  registration error.
- Permission is `has_perm(p) or has_perm(p, obj)` — two calls, per the amended D13.
- **[review] Subclass `PermissionRequiredMixin`**, which already defines
  `get_permission_required`, `has_permission` and the `dispatch` that delegates to
  `handle_no_permission`. Only `has_permission` is overridden.
- **[review] The memo is keyed `(permission, obj._meta.label, obj.pk)`**, not `id(obj)`, which
  CPython reuses after collection — and `can_open` is reachable from template loops over temporary
  objects. The memoised helper is **exported**, because the real per-page cost is author predicates
  calling `has_perm` themselves, which the internal memo would never see.

The registry hands the navigation package an adapter closure that calls `can_open`, catching author
exceptions and hiding the entry. `base.html` passes the record so predicates receive it.

The entry's condition is the parent view's own condition, following admin: a link renders if and
only if its destination is openable.

## Navigation objects

**[review] The registry owns the per-model `Menu` and creates it on first registration.** Today they
are five hand-written objects looked up by the string `f"{model.__name__}Menu"` — and one of them
registers under a different name than its Python variable. `Point` has none, so wiring location would
raise `AttributeError` on an unguarded `append`. `menus.py` keeps only the renderer.

## Validation

In the decorator, raising, so a portal cannot start carrying a bad registration (FR-034). Each
failure names the plugin, the model and the problem (FR-033).

- No model, or an argument that is not a model (FR-027).
- Duplicate plugin name on one model; the same name on different models is fine (FR-028, FR-032).
- Duplicate path segment on one model (FR-029).
- **[review] Duplicate generated URL name on one model.** Segments and plugin names are not enough:
  plugin `a` with child `b` and a separate plugin `a-b` produce the same reverse name from different
  paths, and Django keeps the last one silently.
- **[review] A segment is validated by constructing it with `path()` inside a `try`** and re-raising
  with the plugin named, rather than parsing converters by hand — `path()` already raises on an
  unknown converter (FR-030).
- A `check` that is neither callable nor a bool.
- Among additional views: not a `Plugin`, duplicate segments, a segment equal to the parent's own
  root, or recursion (FR-031).

**[review] Registration against a model with no attachment point cannot be caught in the decorator**,
because no URL configuration has been built when it runs. It is a Django system check instead, which
fires on `manage.py check` and in CI. That is a weaker guarantee than the rest and is recorded as
such — but it is the failure that let five measurement plugins sit inert, so it is worth having.

## Order of work

1. **Access and permissions** — `access.py`, the mixin, the adapter closure, the exported memo. The
   live 500 on sample pages is fixed here, so it goes first.
2. **Record access and addressing** — compose `RelatedObjectMixin`, model-level addressing, reverse,
   the context contract and its four consumers.
3. **URL generation** — flat patterns, additional views, converters in segments.
4. **Validation** — `checks.py`, including the generated-name check and the system check.
5. **Navigation** — registry-owned menus, decorator-driven label/icon/order, `menu=False`, delete the
   `menu` attribute from the shipped plugins and give each one explicit decorator kwargs.
6. **Wiring and removals** — wire location, delete the measurement registrations, replace the plugin
   templates that extend a base which does not exist, remove the broken import/export registrations,
   correct R18, rewrite the documentation.

## What gets deleted

`visibility.py` (folded), the bespoke `slugify`, the `menu` class attribute on ten plugins, the
guardian branch in `has_permission`, the `subviews` include-and-namespace, the class mutation in
`registry.py`, the five measurement registrations, the template lookup chain in
`contrib/generic/plugins.py` (which is the chain D9 orders removed and reads an attribute no class
defines), the four broken registrations in `contrib/import_export/views.py`, and the container
sections of the plugin documentation.

## Testing

Mirrors the source tree per Article X, factories per model, fixtures in `conftest.py`.

Three rules the current suite breaks and this one must not:

- **At least one test per story requests a real record page through the URLconf.** The live 500
  survived 70 passing tests because every one of them tests a unit.
- **Navigation tests assert entry contents**, never just a 200. A page with no navigation returns
  200.
- **Query counts are pinned** with `django_assert_num_queries` for anonymous, denied and granted
  users. The figures in the research are derived from source and must not be trusted until asserted.

## Risks

- **Reverse names change**, `<plugin>:<child>` to `<plugin>-<child>`. One plugin in the tree uses
  additional views and its reverse call is already broken, so the real cost is a documentation note.
- **Ten shipped registrations lose their label and icon** when the `page_title`/`page_icon` fallback
  goes, unless each is given explicit decorator kwargs. Mechanical, but visible on every record page.
- **Addressing touches every wired model's URL configuration.** A mistake takes out a record type;
  covered by the per-story end-to-end tests.
- **Deleting the orphaned templates is not delete-only.** Four templates that live plugins actually
  serve extend `fairdm/plugin.html`, which does not exist; they need replacements, not removal.
