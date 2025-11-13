# Plugin System Architecture

This document explains the architecture of FairDM's plugin system for framework contributors. It covers the internal implementation, registration mechanisms, and design patterns used throughout the system.

## Overview

The FairDM plugin system provides a declarative way to extend portal functionality through modular, reusable views that integrate seamlessly into the core framework. The system emphasizes explicit configuration over implicit behavior and uses modern Django patterns.

## Core Components

### 1. Plugin Registry (`fairdm/plugins.py`)

The `GlobalPluginRegistry` is the central component that manages plugin registration and discovery:

```python
class GlobalPluginRegistry:
    """Central registry for all plugins in the FairDM system."""
    
    def __init__(self):
        self._plugins = defaultdict(lambda: defaultdict(list))
    
    def register(self, model_string, category="explore"):
        """Register a plugin for a specific model and category."""
        def decorator(plugin_class):
            self._plugins[model_string][category].append(plugin_class)
            return plugin_class
        return decorator
```

**Key Design Decisions:**

- **Model strings**: Uses dotted strings like `'dataset.Dataset'` instead of actual model classes to avoid circular imports
- **Category-based organization**: Plugins are grouped into `explore`, `actions`, and `management` categories
- **Lazy loading**: Registry uses `defaultdict` for efficient plugin storage and retrieval

### 2. Plugin Categories

Three module-level constants define plugin categories:

```python
EXPLORE = "explore"      # Analytical and exploratory views
ACTIONS = "actions"      # Operations that perform actions  
MANAGEMENT = "management"  # Form-based management views
```

These constants provide:
- **Type safety**: Prevents typos in category names
- **Discoverability**: IDE autocomplete for available categories
- **Consistency**: Ensures uniform category naming across the codebase

### 3. MenuLink System

The `MenuLink` class provides explicit menu configuration:

```python
@dataclass
class MenuLink:
    name: str
    icon: str = ""
    check: Union[bool, Callable] = True
    
    def has_permission(self, request, obj=None):
        """Check if the user has permission to see this menu item."""
        if callable(self.check):
            return self.check(request, obj)
        return self.check
```

**Design Benefits:**

- **Explicit configuration**: Forces developers to be explicit about menu appearance
- **Permission integration**: Built-in support for permission checks
- **Immutable configuration**: Uses `@dataclass(frozen=True)` to prevent runtime modification

### 4. Base Plugin Classes

The plugin hierarchy provides specialized base classes:

```python
class BasePlugin(View):
    """Base class for all plugins with common functionality."""
    menu_item: Optional[MenuLink] = None
    title: str = ""
    path: str = ""
    
    @property
    def base_object(self):
        """Access to the object this plugin is attached to."""
        return getattr(self, '_base_object', None)

class Explore(BasePlugin, TemplateView):
    """Base class for exploratory/analytical plugins."""
    pass

class Action(BasePlugin):
    """Base class for action-oriented plugins."""
    pass

class Management(BasePlugin, FormView):
    """Base class for form-based management plugins."""
    pass
```

## Registration Flow

### 1. Plugin Discovery

The framework automatically discovers plugins through Django's app loading mechanism:

```python
def autodiscover():
    """Automatically discover and import plugins from all installed apps."""
    for app_config in apps.get_app_configs():
        try:
            import_module(f"{app_config.name}.plugins")
        except ImportError:
            pass  # App doesn't have plugins.py
```

### 2. Registration Process

When a plugin is registered:

1. **Decorator execution**: `@plugin.register()` is called during module import
2. **Registry storage**: Plugin class is stored in the registry by model string and category
3. **Validation**: Basic validation ensures required attributes are present
4. **URL generation**: Plugin URLs are generated based on class names and paths

### 3. Runtime Resolution

During view resolution:

1. **Model resolution**: Model strings are resolved to actual model classes
2. **Plugin retrieval**: Plugins are retrieved by model class and category
3. **Permission checking**: Menu items are filtered by user permissions
4. **Context injection**: Base objects are injected into plugin context

## Integration Points

### 1. URL Routing

Plugins integrate with Django's URL system through automatic route generation:

```python
def get_plugin_urls(model_class):
    """Generate URL patterns for all plugins of a model."""
    patterns = []
    for category, plugins in registry.get_plugins(model_class).items():
        for plugin_class in plugins:
            path = plugin_class.get_path()
            name = plugin_class.get_url_name()
            patterns.append(path(path, plugin_class.as_view(), name=name))
    return patterns
```

### 2. Menu Generation

The menu system dynamically builds navigation based on registered plugins:

```python
def get_menu_items(request, obj, category):
    """Get menu items for an object and category."""
    items = []
    for plugin_class in registry.get_plugins(obj.__class__)[category]:
        if plugin_class.menu_item and plugin_class.menu_item.has_permission(request, obj):
            items.append(plugin_class.menu_item)
    return items
```

### 3. Template Integration

Plugins integrate with FairDM's template system through component wrappers:

```html
<!-- Plugin content is automatically wrapped -->
<c-plugin data-category="{{ category }}" data-plugin="{{ plugin_name }}">
    <!-- Plugin template content -->
</c-plugin>
```

## Migration from Legacy System

The current system replaced a more complex legacy approach:

### Legacy Issues Addressed

1. **Complex inheritance**: Old system used multiple inheritance hierarchies
2. **Implicit registration**: Plugins were registered through metaclass magic
3. **Dict-based menus**: Menu configuration was done through dictionaries
4. **Backward compatibility burden**: Multiple registration patterns caused confusion

### Migration Strategy

1. **Clean break**: No backward compatibility - complete rewrite
2. **Explicit patterns**: All configuration must be explicit
3. **Modern Django**: Uses current Django best practices
4. **Type safety**: Better IDE support through type hints

## Testing Patterns

### Plugin Testing

Test plugins using Django's test framework:

```python
class TestMyPlugin(TestCase):
    def setUp(self):
        self.dataset = DatasetFactory()
        self.plugin = MyPlugin()
        self.plugin._base_object = self.dataset
    
    def test_plugin_context(self):
        context = self.plugin.get_context_data()
        self.assertIn('stats', context)
```

### Registry Testing

Test the registry system:

```python
def test_plugin_registration():
    registry = GlobalPluginRegistry()
    
    @registry.register('test.Model', category='explore')
    class TestPlugin(BasePlugin):
        pass
    
    plugins = registry.get_plugins('test.Model')
    assert TestPlugin in plugins['explore']
```

## Performance Considerations

### 1. Lazy Loading

- Plugin modules are only imported when first accessed
- Registry uses efficient data structures (`defaultdict`)
- Model resolution is cached after first lookup

### 2. Memory Usage

- Plugin classes are singletons (one instance per class)
- Registry stores class references, not instances
- Menu items are generated on-demand

### 3. Database Queries

- Plugins should implement proper queryset optimization
- Use `select_related` and `prefetch_related` in plugin views
- Consider caching for expensive operations

## Extension Points

### 1. Custom Base Classes

Create custom base classes for specialized plugin types:

```python
class VisualizationPlugin(BasePlugin, TemplateView):
    """Base class for data visualization plugins."""
    
    def get_chart_data(self):
        """Override to provide chart data."""
        raise NotImplementedError
```

### 2. Plugin Middleware

Add middleware for plugin-specific processing:

```python
class PluginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Plugin-specific processing
        response = self.get_response(request)
        return response
```

### 3. Signal Integration

Use Django signals for plugin lifecycle events:

```python
plugin_loaded = Signal()
plugin_rendered = Signal()

# In plugin base class
def dispatch(self, request, *args, **kwargs):
    plugin_loaded.send(sender=self.__class__, plugin=self, request=request)
    return super().dispatch(request, *args, **kwargs)
```

## Best Practices for Contributors

### 1. Plugin Development

- Always inherit from appropriate base classes (`Explore`, `Action`, `Management`)
- Use explicit `MenuLink` configuration
- Implement proper permission checking
- Follow Django view patterns

### 2. Registry Usage

- Use model strings, not model classes in decorators
- Prefer constants (`plugins.EXPLORE`) over string literals
- Keep plugin modules focused (one concern per module)

### 3. Testing

- Test plugin registration separately from plugin functionality
- Use factories for test data creation
- Mock external dependencies in plugin tests
- Test permission scenarios

### 4. Documentation

- Document plugin purposes and usage patterns
- Provide examples for common use cases
- Document any special requirements or dependencies
- Keep documentation synchronized with code changes

This architecture provides a robust, extensible foundation for FairDM's plugin system while maintaining simplicity and following Django best practices.