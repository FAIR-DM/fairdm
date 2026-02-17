# FairDM Demo Application

This is the reference implementation and demo portal for the FairDM framework. It demonstrates best practices for building research data portals using FairDM's plugin system, model configuration, and UI components.

## Purpose

The demo app serves multiple purposes:

1. **Reference Implementation**: Executable documentation showing how to use FairDM features
2. **Testing Ground**: Provides models and data for framework testing
3. **Learning Resource**: Examples of plugin patterns, model configuration, and UI composition
4. **Quick Start Template**: Starting point for new portal projects

---

## Plugin System Examples

The demo app showcases the FairDM plugin system with working examples. See [`fairdm_demo/plugins.py`](plugins.py) for complete implementations.

### Basic Plugin Registration

```python
from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.plugins import BaseOverviewPlugin, BaseEditPlugin

@plugins.register(Sample)
class SampleOverview(BaseOverviewPlugin):
    """Basic overview inheriting standard behavior."""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["measurements"] = self.object.measurements.all()
        return context
```

### Form-Based Edit Plugin

```python
@plugins.register(Sample)
class SampleEdit(BaseEditPlugin):
    """Edit form with custom permissions."""
    
    form_class = SampleForm
    menu = {"label": "Edit", "icon": "pencil", "order": 10}
    permission = "fairdm_demo.change_sample"
```

### Polymorphic Visibility (Conditional Plugins)

```python
@plugins.register(Sample)
class LocationDetailsPlugin(Plugin, TemplateView):
    """Only appears for samples with locations."""
    
    menu = {"label": "Location Details", "icon": "geo-alt", "order": 50}
    
    @staticmethod
    def check(request, obj):
        """Custom visibility check."""
        return obj and hasattr(obj, "location") and obj.location is not None
```

### Plugin with Static Assets

The demo includes examples of plugins with CSS and JavaScript:

```python
@plugins.register(Sample)
class ChartPlugin(Plugin, TemplateView):
    menu = {"label": "Charts", "icon": "chart", "order": 40}
    
    class Media:
        css = {"all": ("demo/charts.css",)}
        js = (
            "https://cdn.jsdelivr.net/npm/chart.js",
            "demo/charts.js",
        )
```

---

## Model Configuration

The demo app demonstrates custom Sample and Measurement types:

### Custom Sample Model

See [`fairdm_demo/models/sample.py`](models/sample.py):

```python
class DemoSample(Sample):
    """Example Sample subclass with custom fields."""
    
    char_field = models.CharField(max_length=100)
    text_field = models.TextField()
    date_field = models.DateField()
    # ... more field examples
```

### Custom Measurement Model

See [`fairdm_demo/models/measurement.py`](models/measurement.py):

```python
class DemoMeasurement(Measurement):
    """Example Measurement subclass."""
    
    value = models.FloatField()
    unit = models.CharField(max_length=50)
    # ... more field examples
```

---

## Registry Configuration

The demo shows how to configure model display using the registry system.

See [`fairdm_demo/options.py`](options.py):

```python
from fairdm.core.registry import registry

@registry.register(DemoSample)
class DemoSampleOptions:
    list_fields = ["name", "char_field", "date_field"]
    detail_fields = ["name", "char_field", "text_field", "date_field"]
    filter_fields = ["char_field", "date_field"]
```

---

## Running the Demo

### 1. Create Migrations

```bash
poetry run python manage.py makemigrations fairdm_demo
```

### 2. Apply Migrations

```bash
poetry run python manage.py migrate
```

### 3. Create Sample Data

```bash
poetry run python manage.py shell

from fairdm_demo.factories import DemoSampleFactory, DemoMeasurementFactory

# Create 10 demo samples
samples = DemoSampleFactory.create_batch(10)

# Create 5 measurements per sample
for sample in samples:
    DemoMeasurementFactory.create_batch(5, sample=sample)
```

### 4. Run Development Server

```bash
poetry run python manage.py runserver
```

### 5. Navigate to Demo Content

- **Projects**: http://localhost:8000/projects/
- **Datasets**: http://localhost:8000/datasets/
- **Samples**: http://localhost:8000/samples/
- **Measurements**: http://localhost:8000/measurements/

---

## Project Structure

```
fairdm_demo/
├── README.md              ← This file
├── apps.py               ← App configuration
├── models.py             ← Polymorphic Sample/Measurement models
├── plugins.py            ← Example plugin implementations
├── options.py            ← Registry configuration
├── factories.py          ← Test data factories
├── forms.py              ← Form definitions
├── tables.py             ← django-tables2 table definitions
├── filters.py            ← django-filter filterset definitions
├── tests/                ← Test suite
├── templates/            ← Demo-specific templates
│   └── fairdm_demo/
│       └── plugins/      ← Plugin templates
└── static/               ← Demo-specific static assets
    └── fairdm_demo/
        ├── css/
        └── js/
```

---

## Key Learning Examples

### 1. Plugin Inheritance Patterns

The demo shows three inheritance approaches:

- **Framework Base Classes**: Inherit from `BaseOverviewPlugin`, `BaseEditPlugin`, `BaseDeletePlugin`
- **Custom Base Classes**: Create reusable bases in your package
- **Direct Implementation**: Combine `Plugin` + Django CBV directly

See [`plugins.py`](plugins.py) for side-by-side examples.

### 2. Reusable Plugin Components

The demo demonstrates creating base plugins that portal developers can inherit:

```python
# Base class (reusable)
class GeologyAnalysisPlugin(Plugin, TemplateView):
    menu = {"label": "Geology", "order": 30}
    template_name = "geology/analysis.html"
    
    def analyze_geology(self, sample):
        """Override in subclasses."""
        return {}

# Portal-specific customization (inherits from base)
@plugins.register(Sample)
class CustomGeologyPlugin(GeologyAnalysisPlugin):
    def analyze_geology(self, sample):
        return {"custom_metric": sample.calculate_metric()}
```

### 3. Form-Based Plugins

Examples of plugins using Django's UpdateView, DeleteView, FormView:

- **Edit plugins**: Update object fields with crispy forms
- **Delete plugins**: Confirmation and cascade behavior
- **Wizard plugins**: Multi-step form workflows

### 4. List View Plugins

Show related objects in plugin tabs:

```python
@plugins.register(Project)
class ProjectDatasets(Plugin, DatasetListView):
    menu = {"label": "Datasets", "icon": "dataset", "order": 20}
    
    def get_queryset(self):
        return self.object.datasets.all()
```

### 5. Permission-Based Plugins

Examples of:
- Model-level permissions (`permission = "app.change_model"`)
- Object-level permissions (django-guardian integration)
- Custom permission logic (`has_permission()` override)

---

## Testing

Run demo app tests:

```bash
# All tests
poetry run pytest fairdm_demo/tests/

# Specific test module
poetry run pytest fairdm_demo/tests/test_plugins.py

# With coverage
poetry run pytest fairdm_demo/tests/ --cov=fairdm_demo
```

---

## Using Demo Code in Your Portal

The demo app code is designed to be copied and adapted:

1. **Copy plugin patterns** from `plugins.py` to your app
2. **Adapt model examples** from `models.py` to your domain
3. **Reuse factory patterns** from `factories.py` for test data
4. **Reference templates** in `templates/fairdm_demo/plugins/`

### Example: Adapting a Plugin

From demo:
```python
@plugins.register(Sample)
class LocationDetailsPlugin(Plugin, TemplateView):
    check = lambda r,o: o and hasattr(o, "location") and o.location
    menu = {"label": "Location", "order": 50}
```

To your portal:
```python
@plugins.register(MySample)
class MyLocationPlugin(Plugin, TemplateView):
    check = lambda r,o: o and o.has_geolocation()
    menu = {"label": "Geolocation", "order": 50}
    template_name = "myplugins/location.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["map_data"] = self.object.get_map_coordinates()
        return context
```

---

## Contributing to Demo

The demo app is living documentation. When adding framework features:

1. **Add working examples** demonstrating the feature
2. **Include docstrings** explaining the purpose and pattern
3. **Link to documentation** with references to relevant guides
4. **Write tests** validating the example works correctly

See [Contributing Guide](../docs/contributing/index.md) for details.

---

## Further Reading

- [Plugin System Documentation](../docs/portal-development/create_a_plugin.md)
- [Framework Architecture](../specs/008-plugin-system/plan.md)
- [Quick Start Examples](../specs/008-plugin-system/quickstart.md)
- [API Reference](../docs/api/plugins.md)
