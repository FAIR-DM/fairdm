# Quickstart: Plugin System

**Feature**: 008-plugin-system  
**Audience**: Portal developers building on FairDM

---

## 1. Create Your First Plugin (2 minutes)

Create a file `plugins.py` in your app:

```python
# myapp/plugins.py
from django.views.generic import TemplateView
from fairdm import plugins
from fairdm.contrib.plugins import Plugin, is_instance_of
from fairdm.core.models import Sample
from myapp.models import RockSample

@plugins.register(Sample)  # Register on base model
class AnalysisPlugin(Plugin, TemplateView):
    """Display analysis data for a rock sample."""
    check = is_instance_of(RockSample)  # Only show for RockSample instances
    menu = {
        "label": "Analysis",
        "icon": "chart-bar",
        "order": 10,
    }
```

Create a template at `templates/plugins/analysis-plugin.html`:

```django
{% extends "plugins/base.html" %}

{% block content %}
  <h2>Analysis for {{ object.name }}</h2>
  <p>Sample type: {{ object.rock_type }}</p>
{% endblock %}
```

Navigate to any `RockSample` detail page — you'll see an "Analysis" tab.

**Note**: The `check = is_instance_of(RockSample)` line ensures this plugin only appears for `RockSample` instances, not other Sample types. Setting `menu = None` would make this plugin accessible only via direct URL (no tab).

---

## 2. Plugin with a Form

```python
from django.views.generic import UpdateView
from fairdm import plugins
from fairdm.contrib.plugins import Plugin, is_instance_of
from fairdm.core.models import Sample
from myapp.models import RockSample
from myapp.forms import RockSampleForm

@plugins.register(Sample)  # Base model
class EditRockPlugin(Plugin, UpdateView):
    check = is_instance_of(RockSample)
    form_class = RockSampleForm
    permission = "myapp.change_rocksample"
    menu = {
        "label": "Edit",
        "icon": "pencil",
        "order": 50,
    }
```

The framework automatically provides:
- The model instance as `self.object`
- Permission checking (both model-level and object-level)
- A 403 response for unauthorized users
- Tab hidden for users without permission

---

## 3. Plugin Without a Tab (Direct URL Only)

```python
@plugins.register(Sample)
class DeleteRockPlugin(Plugin, DeleteView):
    check = is_instance_of(RockSample)
    permission = "myapp.delete_rocksample"
    success_url = "/"
    menu = None  # No tab, only accessible via direct URL
```

URL: `/samples/<uuid>/delete-rock-plugin/`

---

## 4. Custom URL Path

```python
@plugins.register(Sample)
class DownloadPlugin(Plugin, TemplateView):
    check = is_instance_of(RockSample)
    url_path = "download"  # Overrides default "download-plugin"
    menu = {
        "label": "Download",
        "icon": "download",
        "order": 30,
    }
```

URL: `/samples/<uuid>/download/`

---

## 5. Plugin for Multiple Models

```python
from fairdm.core.models import Project, Dataset, Sample, Measurement

@plugins.register(Project, Dataset, Sample, Measurement)
class ActivityPlugin(Plugin, TemplateView):
    menu = {
        "label": "Activity",
        "icon": "activity",
        "order": 40,
    }
```

This plugin appears on detail pages for all four model types.

**Note**: No `check` filter means it appears on all instances of these base models.

---

## 6. PluginGroup — Multi-View Feature

For complex features that need multiple views (e.g., view + edit + delete):

```python
from django.views.generic import DetailView, UpdateView, DeleteView
from fairdm import plugins
from fairdm.contrib.plugins import Plugin, PluginGroup, is_instance_of
from fairdm.core.models import Sample
from myapp.models import RockSample
from myapp.forms import GeospatialForm

# Individual plugins (no menu attributes — the group provides the tab)
class GeospatialView(Plugin, DetailView):
    template_name = "plugins/geospatial/view.html"

class GeospatialEdit(Plugin, UpdateView):
    form_class = GeospatialForm
    permission = "myapp.change_rocksample"

class GeospatialDelete(Plugin, DeleteView):
    permission = "myapp.delete_rocksample"
    success_url = "/"

# Register the group on base model
@plugins.register(Sample)
class GeospatialGroup(PluginGroup):
    check = is_instance_of(RockSample)  # Only for RockSample
    plugins = [GeospatialView, GeospatialEdit, GeospatialDelete]
    url_prefix = "geospatial"
    menu = {
        "label": "Geospatial",
        "icon": "map",
        "order": 15,
    }
```

**Generated URLs**:
- `/samples/<uuid>/geospatial/geospatial-view/` — View (tab links here)
- `/samples/<uuid>/geospatial/geospatial-edit/` — Edit (permission-gated)
- `/samples/<uuid>/geospatial/geospatial-delete/` — Delete (permission-gated)

**Note**: The group's `check` filter means the entire Geospatial tab (and all its URLs) only appear for RockSample instances.

---

## 7. Template Customization

Templates are resolved in this order:

1. `{app_label}/{model_name}/plugins/{plugin_name}.html` — Model-specific
2. `{base_model}/plugins/{plugin_name}.html` — Parent model fallback
3. `plugins/{plugin_name}.html` — Generic
4. Explicit `template_name` on the class
5. `plugins/base.html` — Framework fallback

To customize for a specific model, create:
```
templates/
  geology/
    rocksample/
      plugins/
        analysis-plugin.html    ← Used for RockSample
  sample/
    plugins/
      analysis-plugin.html      ← Used for other Sample types
  plugins/
    analysis-plugin.html        ← Used for all models
```

### Cotton Components

The framework provides Cotton components for rendering plugin UI elements. All plugin-related components are namespaced under `c-plugin-*`:

```django
{# Render tab navigation #}
<c-plugin-tabs :tabs="plugin_tabs" />

{# Optional: Plugin base wrapper #}
<c-plugin-base>
  <!-- Your plugin content -->
</c-plugin-base>
```

**File Structure**:
```
templates/
  cotton/
    plugin/
      tabs.html       → <c-plugin-tabs />
      base.html       → <c-plugin-base />
```

---

## 8. Reusable Plugins (for Package Authors)

Create a distributable plugin:

```python
# my_package/plugins.py
from fairdm.contrib.plugins import Plugin

class KeywordPlugin(Plugin, UpdateView):
    """Reusable keyword management plugin."""
    form_class = None  # Override in consumer code
    menu = {
        "label": "Keywords",
        "icon": "tags",
        "order": 50,
    }
```

Portal developers use it:

```python
# myapp/plugins.py
from my_package.plugins import KeywordPlugin
from fairdm import plugins
from fairdm.contrib.plugins import is_instance_of
from fairdm.core.models import Sample
from myapp.models import RockSample
from myapp.forms import RockKeywordForm

@plugins.register(Sample)  # Base model
class RockKeywords(KeywordPlugin):
    check = is_instance_of(RockSample)
    form_class = RockKeywordForm
```

---

## Quick Reference

### Helper Functions

```python
from fairdm.contrib.plugins import is_instance_of

# Single model type filter
check = is_instance_of(RockSample)

# Multiple model types
check = is_instance_of(RockSample, WaterSample)

# Custom check function
def my_check(request, obj):
    if obj is None:
        return True  # Allow model-level access
    return obj.status == 'published' and isinstance(obj, RockSample)

check = my_check

# Lambda for simple checks
check = lambda request, obj: isinstance(obj, RockSample)
```

### Quick Reference Table

| Feature | How |
|---------|-----|
| Register a plugin | `from fairdm import plugins` then `@plugins.register(BaseModel)` |
| Filter by model type | Set `check = is_instance_of(RockSample)` |
| Show as tab | Set `menu = {"label": "...", "icon": "...", "order": 0}` |
| Hide tab | Set `menu = None` |
| Custom URL | Set `url_path = "..."` |
| Permission gate | Set `permission = "app.perm"` |
| Custom template | Set `template_name = "..."` |
| Static assets | Add inner `Media` class |
| Group plugins | Use `PluginGroup` |
| Access instance | `self.object` / `{{ object }}` |
