# Contract: Tab Rendering

## `registry.get_tabs_for_model(model, request, obj)`

### Signature
```python
def get_tabs_for_model(
    model: type[Model],
    request: HttpRequest,
    obj: Model | None = None,
) -> list[Tab]
```

### Preconditions
- `model` must be a Django Model class
- `request` must be a valid Django `HttpRequest` with `request.user` available
- `obj` is the model instance (used for object-level permission checks); may be `None` for model-level only

### Postconditions
- Returns a list of `Tab` dataclass instances
- Only includes plugins/groups that:
  1. Have a truthy `menu` attribute (dict with at least `"label"` key)
  2. Pass the visibility check (if `check` is set)
  3. Pass the permission check for the current user and object
- Sorted by `menu["order"]` (ascending, stable sort, default 0)
- Each `Tab` has a fully resolved URL (using `reverse()`)

### Tab Dataclass

```python
@dataclass
class Tab:
    label: str       # From Menu.label (or plugin name)
    icon: str        # From Menu.icon
    url: str         # Fully resolved URL
    order: int       # From Menu.order
    is_active: bool  # True if current request URL matches this tab's URL
```

### Tab Source Mapping

| Plugin Type | Tab Label | Tab URL |
|-------------|-----------|---------|
| `Plugin` with `menu` dict | `menu["label"]` | `reverse("{model}:{plugin_name}", kwargs=...)` |
| `PluginGroup` with `menu` dict | `menu["label"]` | URL of `PluginGroup.get_default_plugin()` |
| `Plugin` with `menu = None` | (no tab) | — |

### Active Tab Detection

`is_active` is set to `True` when:
- For a simple Plugin: `request.path == tab.url`
- For a PluginGroup: `request.path` starts with the group's URL prefix

---

## Template Integration

### Template Tag

```django
{% load plugin_tags %}

{% get_plugin_tabs model=object request=request as tabs %}
{% for tab in tabs %}
  <a href="{{ tab.url }}" 
     class="nav-link {% if tab.is_active %}active{% endif %}">
    {% if tab.icon %}<i class="{{ tab.icon }}"></i>{% endif %}
    {{ tab.label }}
  </a>
{% endfor %}
```

### Context Processor (Alternative)

A context processor may inject tabs automatically for all plugin views:

```python
def plugin_tabs(request):
    # Only active on plugin views (where `model` and `object` are available)
    return {"plugin_tabs": tabs}
```

### Bootstrap 5 Tab Rendering

The framework provides a Cotton component (`templates/cotton/plugin/tabs.html`):

```django
<c-plugin-tabs :tabs="plugin_tabs" />
```

Which renders:
```html
<ul class="nav nav-tabs">
  <li class="nav-item">
    <a class="nav-link active" href="/samples/abc/overview/">
      <i class="bi bi-eye"></i> Overview
    </a>
  </li>
  <li class="nav-item">
    <a class="nav-link" href="/samples/abc/analysis/">
      <i class="bi bi-chart-bar"></i> Analysis
    </a>
  </li>
  <!-- ... -->
</ul>
```

---

## Ordering Guarantees

1. Tabs are sorted by `menu["order"]` (ascending)
2. For equal `menu["order"]` values: registration order is preserved (stable sort)
3. Default `order` is `0` if not specified in menu dict
4. Recommended convention:
   - 0-9: Core plugins (Overview)
   - 10-29: Primary data plugins
   - 30-49: Secondary plugins
   - 50+: Administrative/management plugins

---

## Permission Filtering

Tabs for plugins the user cannot access are **excluded entirely** (not rendered as disabled):

```python
# Pseudocode
tabs = []
for plugin_or_group in registry.get_plugins_for_model(model):
    if not plugin_or_group.menu:  # Falsey check
        continue
    # Visibility check (model type filtering)
    if plugin_or_group.check and not plugin_or_group.check(request, obj):
        continue
    # Permission check
    if not plugin_or_group.has_permission(request, obj):
        continue
    tabs.append(Tab(
        label=plugin_or_group.menu["label"],
        icon=plugin_or_group.menu.get("icon", ""),
        order=plugin_or_group.menu.get("order", 0),
        ...
    ))
tabs.sort(key=lambda t: t.order)
```

For PluginGroups:
- If group-level `permission` fails → entire group tab hidden
- Individual plugin permissions within the group only affect direct URL access, not tab visibility
