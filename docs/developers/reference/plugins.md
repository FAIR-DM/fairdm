# Plugins

This page lists everything the plugin framework gives you: the registration decorator, the `Plugin` base class, the registry, the helper functions and the errors a refused registration raises. It does not show how to build a plugin, which is in [How to create a plugin](../how-to/create-a-plugin.md), or how access to a record is decided, which is in [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md).

A plugin is a Django view attached to a core record type. Registering it gives the view an address under the record, an entry in the record's tab navigation, and the record itself as `base_object`.

Import from `fairdm.plugins`, which re-exports `fairdm.contrib.plugins`:

```python
from fairdm import plugins
from fairdm.plugins import Plugin
```

## Record types that accept plugins

FairDM mounts the plugin addresses of five record types. A plugin registered against any other model is never reachable.

| Record type | Import | Address prefix | URL namespace |
|---|---|---|---|
| Project | `fairdm.core.project.models.Project` | `/projects/<uuid>/` | `project` |
| Dataset | `fairdm.core.dataset.models.Dataset` | `/datasets/<uuid>/` | `dataset` |
| Sample | `fairdm.core.sample.models.Sample` | `/samples/<uuid>/` | `sample` |
| Measurement | `fairdm.core.measurement.models.Measurement` | `/measurement/<uuid>/` | `measurement` |
| Contributor | `fairdm.contrib.contributors.models.Contributor` | `/contributor/<uuid>/` | `contributor` |

A sample or measurement type that your portal defines shares the namespace of its base type. Register a plugin against `Sample` or `Measurement` and narrow it to your type with [`is_instance_of`](#is_instance_of).

## Registration

### `plugins.register`

```python
plugins.register(*models, label=None, icon="circle", order=0, menu=True)
```

A decorator factory. It registers the decorated class against each model in `models` and returns the class unchanged. A registration that cannot work raises [`PluginRegistrationError`](#pluginregistrationerror) when the module is imported.

| Keyword | Type | Default | What it does | Accepts |
|---|---|---|---|---|
| `label` | `str` or lazy string | The plugin name with hyphens replaced by spaces, in title case | The text of the navigation entry | Any string |
| `icon` | `str` | `"circle"` | The icon of the navigation entry | An icon name |
| `order` | `int` | `0` | The position of the entry among the record's entries. Lower comes first | Any integer |
| `menu` | `bool` | `True` | Whether the plugin gets a navigation entry | `False` leaves the entry out. The page stays reachable at its address |

Any other keyword is stored with the registration and has no effect.

FairDM imports the `plugins` module of every installed app at start-up, so a registration placed in `plugins.py` is found without any other step.

## The `Plugin` class

```python
from fairdm.contrib.plugins import Plugin
```

`Plugin` extends Django's `PermissionRequiredMixin` and `View`. List it before the view class you combine it with:

```python
class Analysis(Plugin, FairDMTemplateView): ...
```

### Attributes you set

| Attribute | Type | Default | What it does | Accepts |
|---|---|---|---|---|
| `name` | `str` or `None` | `None` | The plugin's identifier, unique for each record type. It forms the URL name | `None` uses the class name, slugified |
| `url_path` | `str` or `None` | `""` | The path segment of the plugin's address | `""` uses the name. `None` mounts the plugin at the record's own address with no segment. Any other string is used as given and may hold a route converter, such as `<int:pk>/edit` |
| `permission` | `str`, list of `str`, or `None` | `None` | The permission or permissions needed to open the page | A permission with its app label, such as `"sample.change_sample"`. With a list, every permission is needed. `None` asks for none |
| `check` | `bool` or callable | `True` | Decides whether the page opens and the entry appears | A bool, or a function `check(request, obj)` returning a bool. Write it as a plain function, a lambda or a `staticmethod`. A `classmethod` is refused |
| `extra_views` | list of `Plugin` subclasses | `[]` | Further views that belong to this plugin | Plugin classes with a non-empty `url_path` that declare no `extra_views` of their own |
| `page_title` | `str` | `""` | The page heading and the last entry of the breadcrumb trail | Any string |
| `slug_field` | `str` | `"uuid"` | The model field Django's single-object views look the record up by | A field name |
| `slug_url_kwarg` | `str` | `"uuid"` | The URL keyword that carries that value | A URL keyword |

An inner `Media` class, written as on a Django form, adds stylesheets and scripts to the page.

### Attributes set for you

| Attribute | What it holds |
|---|---|
| `registered_model` | The model the mount serves. A plugin registered against two models is mounted once for each, and each mount holds its own model |
| `plugin_class` | On an additional view's mount, the plugin that declares it. `None` on every class |
| `menu` | The navigation menu of the record type, bound to each mount |

### Methods and properties

| Name | Signature | Returns |
|---|---|---|
| `get_name` | `get_name()` (class method) | `name`, or the slugified class name |
| `get_url_path` | `get_url_path()` (class method) | The segment, or `None` when `url_path` is `None` |
| `get_extra_views` | `get_extra_views()` (class method) | A new list copied from `extra_views` |
| `get_urls` | `get_urls(menu_class=None, model=None)` (class method) | The URL patterns of the plugin and its additional views |
| `base_object` | Cached property | The core record the plugin hangs from, or `None` when it cannot be resolved. A record that does not exist raises a 404 |
| `get_base_object` | `get_base_object()` | The record named by the address. Reads through the model's `all_objects` manager when it has one, so a private record is found and the plugin's own `check` or `permission` decides |
| `has_permission` | `has_permission()` | The result of [`can_open`](#can_open) for this class, the request and the record |
| `get_breadcrumbs` | `get_breadcrumbs()` | The trail: the model's plural name (linked when a list page resolves), the record, then `page_title` |

`base_object` is separate from `self.object`, which stays whatever your view class makes it.

### Context

`Plugin.get_context_data` adds to the context of the view it is combined with:

| Key | What it holds |
|---|---|
| `base_object` | The core record |
| `object` | The view's own object, or `base_object` when the view has none |
| `breadcrumbs` | The trail from `get_breadcrumbs` |
| `plugin_menu` | The record type's navigation menu. FairDM's base template draws it as tabs |
| `plugin_media` | The `Media` built from the inner `Media` class, or `None` |

## Addresses and URL names

A plugin is mounted at `<record prefix>/<url_path>/`. An additional view is mounted at `<record prefix>/<plugin url_path>/<view url_path>/`.

URL names are flat, with no nested namespace:

| View | URL name |
|---|---|
| The plugin | `<name>` |
| An additional view | `<plugin name>-<view name>` |

The name of a view is its class name, slugified, unless it sets `name`. `Notes` becomes `notes` and `NoteEdit` becomes `note-edit`, so the additional view in `Notes.extra_views` is named `notes-note-edit`.

Names are unique for each record type, not across record types.

### Mounting a record type

A record type accepts plugins when a URL configuration mounts its patterns. FairDM does this for the five record types above. For another record type, include the patterns under the route the registry gives:

```python
from django.urls import include, path

from fairdm.plugins import registry

urlpatterns = [
    path(
        f"stations/{registry.route_for(Station)}/",
        include((registry.get_urls_for_model(Station), "station")),
    ),
]
```

The namespace is the lowercase model name. `get_urls_for_model` also builds the record type's navigation menu, so register the plugins before the URL configuration is imported.

## The registry

```python
from fairdm.plugins import registry
```

`registry` is an instance of `PluginRegistry`.

| Name | Signature | Returns |
|---|---|---|
| `register` | `register(*models, **kwargs)` | The decorator. This is `plugins.register` |
| `declare_addressing` | `declare_addressing(model, route, lookup)` | `None`. Declares how a record of `model` appears in an address. Raises `ValueError` when a name in `lookup` is not captured by `route` |
| `get_addressing` | `get_addressing(model)` | The `(route, lookup)` pair, or the defaults |
| `route_for` | `route_for(model)` | The route fragment a URL configuration mounts the record's plugins beneath |
| `lookup_for` | `lookup_for(model)` | The map from URL keyword to model field |
| `get_plugins_for_model` | `get_plugins_for_model(model)` | The registered `(plugin class, options)` pairs, empty when there are none |
| `get_urls_for_model` | `get_urls_for_model(model)` | The URL patterns of every plugin registered for `model`. Rebuilds the model's menu, so calling it twice adds no duplicate entries |
| `get_plugin_menu_for_model` | `get_plugin_menu_for_model(model)` | The record type's menu, named `<Model>Menu` |

The default addressing is the route `<str:uuid>` with the lookup `{"uuid": "uuid"}`. A record identified some other way declares it before its patterns are built:

```python
registry.declare_addressing(
    Station,
    route="<str:code>",
    lookup={"code": "code"},
)
```

A plugin then finds its record by `code`, and [`reverse`](#reverse) fills `code` in from the record.

## Helper functions

All are importable from `fairdm.plugins`.

### `is_instance_of`

```python
is_instance_of(*model_classes)
```

Returns a `check(request, obj)` predicate. It passes when `obj` is an instance of one of `model_classes`, and when `obj` is `None`.

### `has_perm`

```python
has_perm(request, permission, obj=None)
```

Returns `True` when the request's user holds `permission` for the whole portal or on `obj`. The answer is remembered for the rest of the request.

### `holds_level`

```python
holds_level(request, level, obj)
```

Returns `True` when the viewer holds `level` on a project, dataset, sample or measurement. `level` is `"view"`, `"edit"` or `"manage"`, standing for the `view_<model>`, `change_<model>` and `delete_<model>` permissions. Returns `False` when `obj` is `None` or is not one of those four, and for a visitor who is not signed in. Raises `ValueError` for any other level. The template tag of the same name is in [Template tags](template-tags.md). The levels are described in [Contribution levels and record access](contribution-levels-and-record-access.md).

### `can_open`

```python
can_open(view_class, request, obj=None)
```

Returns `True` when the view's `check` passes and every permission in its `permission` is held. Both the navigation entry and the page itself ask this one function. It reads only the `check` and `permission` of the class it is given. An additional view takes nothing from its plugin.

### `reverse`

```python
reverse(instance, view_name, *args, **kwargs)
```

Returns the URL of a plugin view for a record. The namespace is the record's `type_of` model when it has one, otherwise its own model, lowercased. Keywords named in the record type's addressing are filled in from the record.

```python
from fairdm.plugins import reverse

reverse(sample, "analysis")
```

### `slugify`

```python
slugify(text)
```

Returns the slug a class name becomes. `URLTestPlugin` becomes `url-test-plugin`.

## Mixins

Both are in `fairdm.contrib.plugins.mixins`. List them before `Plugin`.

| Mixin | What it does |
|---|---|
| `PrivateRecordNotFoundMixin` | Answers a refused request for a non-public record with a 404, so the address does not confirm the record exists. A refusal on a public record is the usual one. It reads `visibility` from the record, so it suits projects and datasets |
| `RecordOwnPageBackFallbackMixin` | On a deletion page, points **Back** at the record's own page rather than its list. List it before the delete view |

## `PluginRegistrationError`

`fairdm.contrib.plugins.checks.PluginRegistrationError` subclasses Django's `ImproperlyConfigured`. Its message reads `<plugin> registered against <model>: <problem>`.

A registration is refused when:

- no model is given, or a value is not a model class
- `check` is neither a bool nor a callable
- `url_path` is not a valid route
- another plugin on the record type has the same name
- another plugin on the record type has the same `url_path`
- the URL names the plugin generates collide with another plugin's
- an `extra_views` entry is not a `Plugin` subclass
- an `extra_views` entry is the plugin itself
- an `extra_views` entry declares `extra_views` of its own
- an `extra_views` entry has `url_path = None`
- two `extra_views` entries claim the same segment

## Subclassing

A plugin is an ordinary class. A package can ship a plugin without registering it, and a portal registers a subclass:

```python
@plugins.register(Sample, label=_("Citations"), icon="quote", order=520)
class Citations(CitationsPlugin):
    pass
```

## Related pages

- [How to create a plugin](../how-to/create-a-plugin.md)
- [How to restrict a plugin to some users](../how-to/restrict-a-plugin-to-some-users.md)
- [How to add pages to a plugin](../how-to/add-pages-to-a-plugin.md)
- [Overview plugins](overview-plugins.md) for the plugins that draw the record pages
- [Record editing pages](record-editing-pages.md) for the shared pages that edit and delete a record
