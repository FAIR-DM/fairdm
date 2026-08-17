# Plan — 008 The plugin system

Derived from `spec.md` and `research.md`. The three questions the specification left open are
answered in the research; this is how the answers are built.

## Shape

`fairdm/contrib/plugins/` becomes six modules:

| Module | Holds |
|---|---|
| `base.py` | `Plugin` — declaration surface, URL generation, record access, context |
| `access.py` | `can_open()` and the request-scoped permission memo. **New.** |
| `checks.py` | registration-time validation. **New** — rebuilt, not restored. |
| `registry.py` | model → plugin map, URL aggregation, navigation entry construction |
| `menus.py` | the per-model navigation objects and the renderer |
| `utils.py` | slugify, reverse |

`visibility.py` folds into `access.py`; it holds one helper and belongs beside the function that
calls it.

## The declaration surface

```python
@plugins.register(Sample, label=_("Analysis"), icon="chart", order=50)
class Analysis(Plugin, FairDMTemplateView):
    url_path = "analysis"                  # optional; defaults to the slugified class name
    permission = "sample.view_sample"      # optional
    check = staticmethod(is_instance_of(RockSample))   # optional
    extra_views = [AnalysisEdit]           # optional
```

Rules that follow from the specification and the research:

- `menu` as a class attribute is deleted. Label, icon and position come from the decorator (FR-013,
  FR-016). Declining an entry is `@plugins.register(Sample, menu=False)` (FR-012).
- `extra_views` is the declaration; `get_extra_views()` is the only thing that reads it, matching
  this repo's D2/D9 and admin's `inlines`/`get_inlines` pair.
- An additional view is an ordinary `Plugin` subclass, so FR-025 holds by construction.
- `url_path` may carry a route converter, `"<int:pk>/edit"`, so an additional view can address its
  own target.

## URL generation

`Plugin.get_urls(model)` returns flat patterns, one per view:

```
<mount>/<record-lookup>/<parent-path>/            name="<plugin>"
<mount>/<record-lookup>/<parent-path>/<child>/    name="<plugin>-<child>"
```

No `include()`, no nested namespace. This removes the empty-resolver problem rather than guarding
it, and matches admin, DRF and neapolitan, none of which nest.

**Binding is per mount, never on the class.** Every view is mounted with
`view_class.as_view(registered_model=model, plugin_class=parent)`. That deletes `registry.py:129`
and fixes three things at once: additional views that currently have no model and 500 on every
request, and a plugin registered against two models serving the wrong record on one of them (D12).

`as_view` refuses initkwargs that are not already class attributes, so `registered_model` and
`plugin_class` are declared on `Plugin` with `None` defaults.

## Record addressing

Today `uuid` is hardcoded in `slug_field`/`slug_url_kwarg`, in `get_base_object`, and in
`utils.reverse`. `Point` has no `uuid` field, so location cannot be wired until that assumption
becomes a property of the registration.

The registration declares the record's URL fragment and lookup, defaulting to the `uuid` form every
core record uses:

```python
registry.register(Point, lookup="<str:lon>/<str:lat>", lookup_fields=("x", "y"))
```

`get_base_object()` resolves the record from whatever the fragment captured. The plugin system stops
containing the string `uuid`.

The record is exposed as `base_object`, a `cached_property`, matching `RelatedObjectMixin`
(`fairdm/views/mixins.py:44`), and goes into the context under that name. **`self.object` is no
longer assigned** — that is FR-008, and it is what currently breaks a `CreateView` whose own `get()`
sets `self.object = None`.

## Visibility and access

One function, two callers:

```python
def can_open(view_class, request, obj) -> bool
```

- Reads the predicate with `inspect.getattr_static`, so descriptor binding never happens and a
  plain function, a lambda and a `staticmethod` all behave identically. This is what permanently
  removes the two-call-conventions defect.
- Author-facing predicate signature is `check(request, obj) -> bool`.
- Permission is `has_perm(p) or has_perm(p, obj)` — two calls, per the amended D13, because
  `ModelBackend` contributes nothing once an object is passed.
- Memoised per request by `(permission, id(obj))`. Without it a record page with several plugins
  costs 60–90 extra queries.

`dispatch` calls it. The registry hands the navigation package an adapter closure that calls it,
so the package's `check(request, **kwargs)` contract is untouched and the author never sees it. The
closure catches author exceptions and hides the entry, because an uncaught predicate exception is
currently a 500 during template rendering.

**The entry's condition is the parent view's own condition**, following admin: a link renders if and
only if its destination is openable. Additional views carry no entry, so they enforce at their own
dispatch alone.

`base.html` gains `object=object` beside the existing `uuid=object.uuid`, so predicates receive the
record. Extra kwargs are filtered before URL reversal, so this is safe.

Access failure goes through `AccessMixin.handle_no_permission`, so an anonymous visitor is redirected
to login instead of being given the 403 the current unconditional raise produces.

## Validation

In the decorator, where the class body has already executed. Each failure names the plugin, the
model and the problem (FR-033), and raises, so a portal cannot start carrying one (FR-034).

- No model, or an argument that is not a model (FR-027).
- Duplicate plugin name on one model; the same name on different models is fine (FR-028, FR-032).
- Duplicate path segment on one model (FR-029).
- A segment that cannot appear in a route (FR-030), accepting `<converter:name>` and checking the
  converter against `django.urls.converters.get_converters()`.
- Among additional views: not a `Plugin`, duplicate segments, a segment equal to the parent's own
  root, or recursion (FR-031).

## Order of work

1. **Access and permissions** — `access.py`, the mixin, the adapter closure. This is where the live
   500 on sample pages is fixed, so it goes first.
2. **Binding and record access** — per-mount `as_view`, `base_object`, stop assigning `self.object`,
   registration-declared lookup.
3. **URL generation** — flat patterns, additional views, converters in segments.
4. **Validation** — `checks.py`.
5. **Navigation** — decorator-driven label/icon/order, `menu=False`, delete the `menu` attribute.
6. **Wiring and removals** — wire location, delete the measurement registrations, delete the six
   unreachable overview templates, correct R18, rewrite the plugin documentation.

## What gets deleted

`visibility.py` (folded), the `menu` class attribute on ten plugins, the guardian branch in
`has_permission`, the `subviews` include-and-namespace, `registry.py:129`, the five measurement
registrations, six `*/plugins/overview.html` files that extend a template which does not exist, the
four broken `@plugins.register` uses in `contrib/import_export/views.py`, and the `PluginGroup`
sections of `docs/portal-development/create_a_plugin.md`.

## Testing

Mirrors the source tree per Article X: `tests/test_contrib/test_plugins/test_{base,access,checks,
registry,menus,urls}.py`, factories per model, fixtures in `conftest.py`.

Two rules the current suite breaks and this one must not:

- **At least one test requests a real record page through the URLconf.** The live 500 survived 70
  passing tests because every one of them tests a unit. Each user story gets an end-to-end test.
- **Query counts are pinned** with `django_assert_num_queries` on a record page for an anonymous
  user, a denied user and a granted user. The costs in the research are derived from source, not
  measured, and must not be trusted until asserted.

## Risks

- **The reverse-name change is a break.** `project:contribution-list:contribution-create` becomes
  `project:contribution-list-contribution-create`. Only one plugin in the tree uses additional views,
  and its reverse call is already broken, so the real cost is a documentation note.
- **Registration-declared lookup touches every wired model's URL configuration.** Four models, each
  one line, but a mistake takes out a whole record type. Covered by the end-to-end tests above.
- **The permission memo is keyed on `id(obj)`.** Safe within a request because the record is one
  instance, and the memo lives on the request. It must not be promoted to a longer-lived cache.
