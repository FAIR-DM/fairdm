(views-module)=
# Views Module Overview

## Introduction

The `fairdm.views` module serves as the central hub for all view-related functionality in the FairDM framework. This module consolidates view mixins, concrete view classes, and utilities that provide consistent behavior across the framework's user interface.

The views module follows Django's class-based view (CBV) architecture and provides both mixins for composability and ready-to-use concrete view classes that implement common patterns used throughout FairDM applications.

## Architecture Overview

The views module is organized into three main categories:

1. **View Mixins** - Reusable components that provide specific functionality
2. **Concrete View Classes** - Ready-to-use views that combine mixins with Django's generic views
3. **Utilities** - Helper classes and functions for dynamic view generation

## View Mixins

### FairDMBaseMixin

The foundational mixin that provides common functionality for all FairDM views.

```python
from fairdm.views import FairDMBaseMixin

class MyCustomView(FairDMBaseMixin, TemplateView):
    page_title = "My Custom Page"
    about = ["Information about this page"]
```

**Key Features:**
- Integrates with FairDM's layout system (`BaseLayout`)
- Provides message framework integration (`MessageMixin`)
- Handles metadata for SEO (`MetadataMixin`)
- Manages page context including titles, actions, and help content
- Controls user edit permissions

**Attributes:**
- `about` - Optional descriptive text or list of text for the page
- `actions` - List of template components displayed with the page title
- `learn_more` - Optional link to documentation or user guides
- `page_title` - Title displayed on the page

**Methods:**
- `get_context_data()` - Adds common context variables
- `user_can_edit()` - Determines if the current user has edit permissions
- `get_page_title()` - Returns the page title for the view

### FairDMFormViewMixin

Provides enhanced form handling capabilities for form-based views.

```python
from fairdm.views import FairDMFormViewMixin

class MyFormView(FairDMFormViewMixin, FormView):
    template_name = "my_form.html"
```

**Key Features:**
- Integrates with FairDM's form layout system (`FormLayout`)
- Handles success URL redirection with `next` parameter support
- Provides consistent form styling and behavior

### FairDMModelFormMixin

Advanced mixin for model-based forms with dynamic form class generation.

```python
from fairdm.views import FairDMModelFormMixin

class MyModelFormView(FairDMModelFormMixin, CreateView):
    model = MyModel
    fields = ["name", "description"]
```

**Key Features:**
- Dynamic form class generation using `modelform_factory`
- Integration with FairDM's registry system for registered models
- Automatic form class resolution from model configurations
- Login required for POST requests (via decorator)
- Add-another popup support for related object creation

**Attributes:**
- `model` - The Django model for the form
- `form_class` - Optional custom form class
- `fields` - Fields to include in the generated form

### RelatedObjectMixin

Specialized mixin for views that need to fetch and display related objects, commonly used in plugins.

```python
from fairdm.views import RelatedObjectMixin

class SampleListView(RelatedObjectMixin, ListView):
    base_model = Dataset
    
    def get_queryset(self):
        return self.base_object.samples.all()
```

**Key Features:**
- Fetches related objects based on URL parameters
- Handles polymorphic models automatically
- Adds related object context to templates
- Caches related object for performance

**Attributes:**
- `base_model` - The model class of the related object
- `base_object_url_kwarg` - URL parameter name (defaults to "uuid")

## Concrete View Classes

The module provides ready-to-use view classes that combine the mixins with Django's generic views:

### FairDMTemplateView
Basic template view with FairDM styling and context.

### FairDMListView
Enhanced list view with filtering, pagination, and FairDM integration.

**Key Features:**
- Built-in filtering using `django-filter`
- Pagination (20 items per page by default)
- Automatic filterset generation for registered models
- Permission-based filtering
- Search functionality

### FairDMDetailView
Detail view for displaying individual objects with consistent styling.

**Key Features:**
- Automatic image context for models with image fields
- Meta description generation
- Consistent detail page layout

### FairDMCreateView
Create view with automatic permission assignment and activity logging.

**Key Features:**
- Automatic model permission assignment to the creating user
- Activity stream integration for object creation tracking
- Consistent form layout and styling

### FairDMUpdateView
Update view with permission checking and consistent styling.

### FairDMDeleteView
Delete view with proper permission checking and user confirmation.

## Advanced Features

### CRUDView (Experimental)

The `CRUDView` class provides dynamic CRUD view generation based on a model configuration.

```python
from fairdm.views import CRUDView

class MyModelCRUDView(CRUDView):
    model = MyModel
    base_url = "mymodel"
    
    # Generates URLs for list, create, detail, update, delete
    urlpatterns = MyModelCRUDView.get_urls()
```

**Features:**
- Automatic URL pattern generation
- Dynamic view class creation
- Permission checking integration
- Customizable view classes for different actions

## Usage Patterns

### Basic View Implementation

```python
from fairdm.views import FairDMListView

class MyModelListView(FairDMListView):
    model = MyModel
    page_title = "My Models"
    template_name = "myapp/mymodel_list.html"
```

### Custom Form View

```python
from fairdm.views import FairDMModelFormMixin
from django.views.generic import CreateView

class CustomCreateView(FairDMModelFormMixin, CreateView):
    model = MyModel
    fields = ["name", "description", "category"]
    page_title = "Create New Item"
    
    def get_success_url(self):
        return reverse("mymodel:detail", kwargs={"pk": self.object.pk})
```

### Plugin View with Related Object

```python
from fairdm.views import RelatedObjectMixin, FairDMListView

class DatasetSampleListView(RelatedObjectMixin, FairDMListView):
    base_model = Dataset
    template_name = "samples/dataset_sample_list.html"
    
    def get_queryset(self):
        return self.base_object.samples.all()
```

## Integration with Other Framework Components

### Registry System
The views integrate seamlessly with FairDM's registry system to automatically generate forms, filters, and serializers for registered models.

### Layout System
All view mixins integrate with FairDM's layout system (`fairdm.layouts`) to provide consistent styling using Bootstrap 5 components.

### Permission System
Views include integration with `django-guardian` for object-level permissions and automatic permission assignment.

### Activity Streams
Create and update views automatically log activities using `django-activity-stream`.

## Best Practices

1. **Always use FairDM mixins** when creating custom views to maintain consistency
2. **Leverage the registry system** for automatic form and filter generation
3. **Use RelatedObjectMixin** for plugin views that need parent object context
4. **Set appropriate page titles and help text** using the mixin attributes
5. **Follow Django CBV patterns** when extending or customizing views

## Migration from Legacy Code

If you're updating code that previously imported from `fairdm.utils.view_mixins`, update your imports:

```python
# Old import (deprecated)
from fairdm.utils.view_mixins import FairDMBaseMixin

# New import
from fairdm.views import FairDMBaseMixin
```

All view mixins have been consolidated into the `fairdm.views` module for better organization and discoverability.