# Research — 008 The plugin system

Three questions were left open by `decisions.md`: how a plugin declares additional views, how the
predicate and the per-view permissions combine into one decision, and how location plugins mount.
This records the answers and the prior art behind them.

It also records a live defect found while answering the second question. That came first.

---

## 0. Sample detail pages return 500 on `main` today

Four of the five plugins registered against `Sample` declare
`check = check_has_edit_permission`, whose signature is `(request, instance, **kwargs)`
(`fairdm/core/sample/plugins.py:19`). The navigation package calls a check as
`check(request, **kwargs)` (`flex_menu/menu.py:363`), so `instance` is never supplied.

Verified by requesting a real page:

```
GET /samples/<uuid>/  ->  TypeError: check_has_edit_permission() missing 1 required
                          positional argument: 'instance'
                          flex_menu/menu.py:363, in MenuItem.check
```

There is no `try` around that call in `MenuItem.check`, `MenuItem.process` or `process_menu`, so it
propagates out of template rendering. Every sample page renders this menu, so every sample page
fails.

Blast radius across the four models whose plugins are routed:

| Model | Plugins | Checks that raise |
|---|---|---|
| Project | 4 | 0 |
| Dataset | 3 | 0 |
| **Sample** | **5** | **4** — Edit, Descriptions, Keywords, KeyDates |
| Contributor | 5 | 0 |

Measurement carries the same mixin and is not routed, so it does not add to this.

Nothing in the test suite requests a record detail page, which is why 70 passing plugin tests sit
alongside it. That absence is itself a finding: the suite tests the plugin system's units and never
its output.

---

## 1. How a plugin declares additional view classes

### What exists

`Plugin.subviews` is a class attribute (`base.py:47`); `get_urls` (`base.py:78-102`) mounts each
child under a nested namespace. One production use, `contributors/plugins/shared.py:84`. Weaknesses,
all confirmed by reading and by building the live URLconf:

- The `include()` is emitted unconditionally, so every plugin installs an empty resolver whose
  namespace equals its own pattern name — the plugin is simultaneously a route and a container.
- **Children are never bound to a model.** `registry.py:129` sets `registered_model` on the parent
  class only, so every child has `registered_model = None`.
- **Consequently every child is a 500.** `base.py:189` evaluates `self.registered_model.DoesNotExist`
  when building its except tuple, so `None.DoesNotExist` raises `AttributeError`. The sole
  production use of `subviews` cannot serve a request.
- Nothing validates a child is a `Plugin`; a plain class registers silently and fails later at
  URLconf build, inside a traceback.
- No collision detection among children, or between children and the parent.
- A child cannot carry a lookup for its own target: `ContributionUpdate` routes to
  `/project/<uuid>/contributors/edit/` with no contribution identifier anywhere.
- `base.py:197-198` assigns the core record to `self.object`, which a `CreateView` sets to `None` in
  its own `get()`. The record and the view's own object share one attribute name, which is what
  FR-008 forbids.

The class-attribute mutation at `registry.py:129` is the same defect as D12; multi-model
registration and unbound children are one bug.

### Prior art

| | Django admin | DRF `ViewSet` | neapolitan `CRUDView` |
|---|---|---|---|
| Composed sub-units | class attr `inlines` + hook `get_inlines()` (`options.py:664`, `:410`) | `@action` on methods | `Role` enum |
| Child URL segment | literal with converter, `<path:object_id>/change/` (`options.py:741`) | `url_path`, defaults to method name | built from a converter (`views.py:65-79`) |
| Child URL name | flat, `{app}_{model}_{action}` (`options.py:725`) | flat (`routers.py:111`) | flat (`views.py:85`) |
| Nested namespace | **no** | **no** | **no** |
| Binding parent context | per-instance construction (`options.py:683`, `:701`) | `as_view(**initkwargs)` → `cls(**initkwargs)` | same |
| Per-child permission | per-action `has_*_permission`, failing units dropped (`options.py:703-708`) | `get_permissions()` or `@action(permission_classes=)` | none |
| Collision detection | none | none | none |

Three things follow. Nobody uses a nested namespace — all three flatten the child's name under the
parent's prefix. Everybody binds parent context onto the *instance*, never onto the class. And
nobody validates that a unit's children collide, so FR-031 has no prior art and has to be built.

### What this repo already settled

`specs/002-fairdm-registry/decisions.md` D2 and D9 settle both halves and are not in tension:
declaration is a class attribute, resolution is a single method, and nothing reads the attribute
directly. That is exactly admin's `inlines` + `get_inlines()` pair, where `get_inline_instances`
iterates the hook and never touches the attribute. Sam's "class method" is the resolution half.

### Recommendation

`extra_views` as a class attribute plus `get_extra_views()` as the single classmethod that reads it.
An additional view is an ordinary `Plugin` subclass, so FR-025 holds by construction rather than by
forwarding — which is the forwarding the container was removed to avoid.

- **Flat patterns, no `include()`, no nested namespace.** Parent at `name=<plugin>`, each child at
  `name=<plugin>-<child>`. Removes the empty-resolver problem outright rather than guarding it.
  Cost: reverse names become `project:contribution-list-edit`, not `…:contribution-list:edit`.
- **Segments may carry converters** — `url_path = "<int:pk>/edit"`. Django's `path()` accepts it,
  and it is how both admin and neapolitan express the same need. This is what makes a child able to
  address its own target.
- **Bind per mount:** `view_class.as_view(registered_model=model)`, applied identically to parent and
  children. Deletes `registry.py:129` and fixes the unbound children and D12 together.
- **Expose the record as `base_object`**, matching `fairdm/views/mixins.py:44`, and stop assigning
  `self.object`.
- **Validate in the decorator**, where the class body has already executed: child is a `Plugin`,
  no duplicate segments, no empty or parent-colliding segment, converters checked against
  `django.urls.converters.get_converters()`, and no recursion.

Rejected: DRF's `@action`, because it makes a child a method rather than a view class, which
US2 and SC-006 forbid. Keeping `get_urls()` as the override point, because arbitrary returned
patterns cannot be validated at registration — both DRF and neapolitan take that bargain and both
ship with no collision detection.

---

## 2. How the predicate and the permissions become one decision

### What the navigation package requires

`check(request, **kwargs) -> bool`, called at `flex_menu/menu.py:363` with the caller's kwargs
forwarded. Today `fairdm/templates/base.html:31` passes `uuid=object.uuid`, so **the record itself
never reaches a predicate.** Extra kwargs are safe: `resolve_url` filters them against the URL
pattern before reversing (`menu.py:485-498`), so passing `object=object` alongside is supported.

Two behaviours to design around. An exception in a check is not caught anywhere and becomes a 500 —
that is finding 0. And a processed menu item keeps only a fixed set of attributes
(`menu.py:428-458`), so anything a check needs must live in its closure.

### Why nothing an author can write works today

`base.py:180` reads `self.check`, which triggers descriptor binding and calls
`fn(plugin_instance, request)`. `registry.py:157` passes the unbound attribute, and the package calls
`fn(request, uuid=…)`.

| declared as | dispatch calls | navigation calls |
|---|---|---|
| plain function | `f(plugin, request)` | `f(request, uuid=…)` |
| `staticmethod` | `f(request)` | `f(request, uuid=…)` |

`staticmethod` dodges the binding and still cannot satisfy both, because dispatch passes one
positional and no kwargs. Every predicate in the tree is broken in at least one path, and
`is_instance_of` — the one helper the package exports — refuses every request when used.

### The object-level permission trap

`request.user.has_perm(perm, obj)` **does not include model-level permissions**:
`ModelBackend._get_permissions` returns `set()` as soon as `obj is not None`
(`django/contrib/auth/backends.py:104-111`). All the remaining configured backends are guardian
subclasses that consult object rows only. So the single call D13 describes would refuse a user who
holds the permission globally with no object row — a regression against today's behaviour.

Guardian's own mixin does it in two parts (`guardian/utils.py:183-192`), and that is the shape to
copy: `user.has_perm(p) or user.has_perm(p, obj)`.

**D13 is amended accordingly.**

### Query cost

Derived from source, not measured. A denied object-level check on a Sample costs roughly 8–11
queries, because `_user_has_perm` only short-circuits on a grant and
`ObjectPermissionBackend.has_perm` builds a fresh checker every call (`guardian/backends.py:113`).
Sample has five registered plugins; at eight the menu alone would add 60–90 queries per page.

The mitigation is cheap: the record is the same instance for every plugin on the page, so memoise on
the request by `(permission, id(obj))`. A record page uses two or three distinct permission strings,
so the checks collapse to two or three real evaluations. These numbers must be pinned with
`django_assert_num_queries` during implementation rather than trusted.

### How admin keeps two consumers consistent

This is the load-bearing prior art. `ModelAdmin.get_model_perms` returns the result of the same
`has_*_permission` methods the pages enforce (`options.py:776-787`), and `AdminSite._build_app_dict`
renders a link only when the predicate of the page it points at passes
(`sites.py:508-521`). **A link is shown if and only if its destination is openable.** Admin never
asks a broader question to decide whether to render a narrower link.

### Recommendation

One module-level function, `can_open(view_class, request, obj)`, in a new `access.py`. Two callers:
dispatch, and a closure the registry hands to the navigation package. A regression test should assert
both paths reach the same function object, so FR-020 holds structurally rather than by convention.

- Read the predicate with `inspect.getattr_static`, which does not invoke the descriptor protocol.
  A plain function, a `staticmethod` and a lambda then all behave identically in both callers. This
  removes the binding asymmetry permanently instead of asking authors to remember `staticmethod`.
- Author-facing signature is `check(request, obj) -> bool`, matching the existing helper and
  answering FR-017's "per user and per record". Authors never see the package's kwargs contract.
- The registry passes an adapter closure, never the author's function, so the package's contract is
  untouched. The closure must swallow author exceptions and hide the entry, because the fail-safe
  direction for a visibility decision is "not shown" and the alternative is finding 0.
- Add `object=object` to `base.html:31` so predicates receive the record instead of re-fetching it.
- **The entry's condition is the parent view's own condition**, following admin. A plugin whose
  parent is permitted but whose children are not still shows one entry; the children are refused at
  their own dispatch and were never advertised.

  **Corrected after design review.** An earlier draft of this section said the inverse case — the
  parent refused, a child still reachable by address — was "correct under D7 because the child was
  never shown". That is wrong, and it defeats the guarantee the whole story exists for. An
  additional view inherits `Plugin.check = True`, so reading the predicate off the view class alone
  would leave `CurationEdit` served to a user who is refused `Curation` and shown no entry for it.
  The predicate belongs to the plugin, and a child belongs to the plugin, so `can_open` consults the
  owning plugin's predicate as well as the view's own permission. The mount already binds
  `plugin_class`; nothing was reading it.
- Replace `dispatch`/`has_permission` with a mixin over `AccessMixin`, so an anonymous visitor is
  redirected to login rather than given the 403 the current unconditional `PermissionDenied` sends.

Rejected: making `check` an ordinary bound method, because `configure_tab` runs at import time with
no request, so the item would close over a dead instance. Deriving the entry from the union or
intersection of the plugin's and its children's permissions — the union shows an entry linking to a
page the user cannot open, and the intersection hides one they can.

---

## 3. How location plugins mount

**`Point` has no `uuid` field.** It is identified by `unique_together = ("x", "y")`
(`fairdm/contrib/location/models.py:42`), and `PointDetailView.get_object` resolves it from `lon`
and `lat` kwargs (`fairdm/contrib/location/views.py:11`).

The plugin system assumes `uuid` in three places: `Plugin.slug_field`/`slug_url_kwarg`
(`base.py:48-49`), `get_base_object`, which tries `pk` then `uuid` and otherwise raises
(`base.py:104-126`), and `utils.reverse`, which hardcodes `kwargs.update({"uuid": model.uuid})`
(`utils.py:72-75`).

So this is not a mount-shape choice. Wiring location requires how a record is addressed to become a
property of the registration rather than a constant — which is what FR-006 asks for in general and
what SC-007 measures. `Point` has an implicit primary key, so a `pk`-keyed mount would work today,
but it would contradict the coordinate-keyed detail view the model already serves and leave the
hardcoded assumption in place for the next model that does not have a `uuid`.

Recommendation: the registration declares the URL fragment and lookup for its model, defaulting to
the `uuid` form every core record already uses. Location then declares the coordinate pair, and the
plugin system stops knowing the word `uuid`.

---

## Consequences for `decisions.md`

- **D13 is amended**: the single `has_perm(perm, obj)` call it describes drops model-level
  permissions. The correct expression is `has_perm(p) or has_perm(p, obj)`.
- D1's open question is answered: `extra_views` attribute plus `get_extra_views()` classmethod, flat
  patterns, per-mount binding.
- D7's open question is answered: one `can_open` function, two callers, entry condition equals the
  parent view's condition.
- D5's open question is answered, and is larger than recorded: addressing must become part of the
  registration.

## Follow-ons outside this feature

- `get_plugin_url` is called at `contributors/plugins/shared.py:39` and defined nowhere.
- The four `@plugins.register` uses in `contrib/import_export/views.py` are applied without calling
  the decorator factory, so each name is rebound to the inner decorator function. They are already
  broken at import, not merely on routing.
- `docs/portal-development/create_a_plugin.md` documents the removed container and its error codes,
  and its closing summary still teaches the pre-February interface.
