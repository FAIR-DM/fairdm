# Contract: URL Generation

## `Plugin.get_urls()` Classmethod

### Signature
```python
@classmethod
def get_urls(cls) -> list[URLPattern]
```

### Preconditions
- Plugin class must have `name` set (explicitly or auto-derived)
- Plugin class must be mixed with a Django CBV that supports `as_view()`

### Postconditions
- Returns a list containing exactly one `URLPattern` for simple plugins
- The pattern's route is `{url_path}/` where `url_path` defaults to the slugified `name`
- The pattern's `name` kwarg is set to the plugin's `name` (used for URL reversal)
- The view callable is `cls.as_view()` (standard Django CBV pattern)

### URL Pattern Format
```
{url_path}/  →  cls.as_view()  name={name}

# Examples:
"analysis/"   →  AnalysisPlugin.as_view()   name="analysis"
"download/"   →  DownloadPlugin.as_view()   name="download"
```

### Custom URL Path
```python
class MyPlugin(Plugin, TemplateView):
    url_path = "my-custom-path"
    # Produces: "my-custom-path/" → MyPlugin.as_view() name="my-plugin"
```

### Overriding for Multi-URL Plugins
Plugins may override `get_urls()` to return multiple patterns:
```python
@classmethod
def get_urls(cls):
    return [
        path(f"{cls.get_url_path()}/", cls.as_view(), name=cls.get_name()),
        path(f"{cls.get_url_path()}/export/", cls.export_view, name=f"{cls.get_name()}-export"),
    ]
```

---

## `PluginGroup.get_urls()` Classmethod

### Signature
```python
@classmethod
def get_urls(cls) -> list[URLPattern]
```

### Preconditions
- `cls.plugins` must be a non-empty list of Plugin subclasses
- `cls.url_prefix` must be set (explicitly or auto-derived)

### Postconditions
- Returns URL patterns for ALL wrapped plugins, each prefixed with `{url_prefix}/`
- Pattern format: `{url_prefix}/{plugin_url_path}/` for each wrapped plugin
- URL names are preserved from individual plugins

### URL Pattern Format
```
{url_prefix}/{plugin_url_path}/  →  PluginClass.as_view()  name={plugin_name}

# Example for PluginGroup with url_prefix="metadata":
"metadata/metadata-view/"   →  MetadataView.as_view()   name="metadata-view"
"metadata/metadata-edit/"   →  MetadataEdit.as_view()    name="metadata-edit"
"metadata/metadata-delete/" →  MetadataDelete.as_view()  name="metadata-delete"
```

---

## `registry.get_urls_for_model(model)` 

### Signature
```python
def get_urls_for_model(model: type[Model]) -> list[URLPattern]
```

### Preconditions
- `model` must be a Django Model class

### Postconditions
- Returns aggregated URL patterns from all plugins/groups registered for the model
- Calls `get_urls()` on each registered plugin/group and concatenates results
- For polymorphic models: includes URLs from parent-registered plugins
- All patterns are suitable for `include()` in Django URL configuration

### Integration Pattern
```python
# In model's urls.py
from fairdm.contrib.plugins import registry

urlpatterns = [
    path("samples/<str:uuid>/", include((
        registry.get_urls_for_model(Sample), "sample"
    ))),
]
```

### URL Namespace
All plugin URLs are namespaced under the model name. Reversal uses:
```python
reverse("sample:analysis")                  # Simple plugin
reverse("sample:metadata-view")             # Plugin in a group
reverse("sample:analysis", kwargs={"uuid": sample.uuid})
```

---

## Name Derivation Rules

### Plugin Name
1. If `name` attribute is explicitly set → use that value
2. Otherwise → slugify the class name: `AnalysisPlugin` → `"analysis-plugin"`

### Plugin URL Path
1. If `url_path` attribute is explicitly set → use that value
2. Otherwise → use `name` value

### PluginGroup URL Prefix
1. If `url_prefix` attribute is explicitly set → use that value
2. Otherwise → slugify the class name: `MetadataGroup` → `"metadata-group"`

### Slugification Rules
- Convert CamelCase to kebab-case: `MyPlugin` → `"my-plugin"`
- Lowercase all characters
- Replace consecutive hyphens with single hyphen
- Strip leading/trailing hyphens
