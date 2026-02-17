"""Plugin mixin base class for extending model detail views."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from django.core.exceptions import PermissionDenied
from django.urls import path
from django.views.generic.base import View

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.db.models import Model
    from django.http import HttpRequest, HttpResponse
    from django.urls import URLPattern


class Plugin(View):
    """Mixin class that adds plugin behavior to Django class-based views.

    Plugins extend model detail views with custom functionality. Each Plugin
    is paired with a Django CBV (e.g., TemplateView, UpdateView, DeleteView).

    Attributes:
        name: Unique identifier per model (auto-derived from class name if not set)
        url_path: URL path segment (auto-derived from name if not set)
        template_name: Explicit template path override (uses resolution if empty)
        permission: Required permission string (e.g., "myapp.change_sample")
        check: Visibility check callable (request, obj) -> bool
        model: Set by registry during registration (base model only)
        menu: Tab configuration dict with keys:
            - label (str, required): Display text
            - icon (str, optional): Icon identifier
            - order (int, optional, default 0): Sort position
            If None/falsey, no tab is created.

    Basic Example:
        ```python
        from fairdm.plugins import Plugin, register_plugin
        from django.views.generic import TemplateView


        @register_plugin(Sample)
        class AnalysisPlugin(Plugin, TemplateView):
            menu = {
                "label": "Analysis",
                "icon": "chart-bar",
                "order": 10,
            }

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["analysis_data"] = self.object.get_analysis()
                return context
        ```

    Inheritance Patterns:

        **1. Reusable Base Classes**
        Create base plugin classes in your package that can be inherited by portal developers:

        ```python
        # In fairdm/core/plugins.py (framework base classes)
        from fairdm.plugins import Plugin
        from django.views.generic import TemplateView, UpdateView


        class BaseOverviewPlugin(Plugin, TemplateView):
            menu = {"label": "Overview", "icon": "eye", "order": 0}

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["activities"] = get_activities(self.object)
                return context


        class BaseEditPlugin(Plugin, UpdateView):
            menu = {"label": "Edit", "icon": "pencil", "order": 100}

            def get_success_url(self):
                return self.object.get_absolute_url()
        ```

        **2. Portal Developer Customization**
        Portal developers inherit from base classes and add domain-specific behavior:

        ```python
        # In portal_app/plugins.py (portal-specific implementations)
        from fairdm.core.plugins import BaseOverviewPlugin, BaseEditPlugin
        from fairdm.plugins import register_plugin
        from .models import Sample
        from .forms import SampleForm


        @register_plugin(Sample)
        class SampleOverview(BaseOverviewPlugin):
            # Inherit menu, template_name, base behavior
            # Add custom context
            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["measurements"] = self.object.measurements.all()
                return context


        @register_plugin(Sample)
        class SampleEdit(BaseEditPlugin):
            form_class = SampleForm
            permission = "samples.change_sample"
        ```

        **3. Polymorphic Visibility**
        Use the `check` attribute to show plugins only for specific subtypes:

        ```python
        from fairdm.plugins import is_instance_of


        @register_plugin(Sample)
        class RockAnalysisPlugin(Plugin, TemplateView):
            check = is_instance_of(RockSample)
            menu = {"label": "Geochemistry", "order": 20}
            # Only visible for RockSample instances, not WaterSample
        ```

        **4. Multi-Package Plugin Distribution**
        Base plugins can be defined in one package and extended in another:

        ```python
        # In fairdm_geology package
        class GeologyAnalysisPlugin(Plugin, TemplateView):
            menu = {"label": "Geology", "order": 30}
            template_name = "geology/analysis.html"


        # In portal_project (inherits from fairdm_geology)
        from fairdm_geology.plugins import GeologyAnalysisPlugin
        from fairdm.plugins import register_plugin


        @register_plugin(Sample)
        class CustomGeologyPlugin(GeologyAnalysisPlugin):
            # Inherits template, menu, behavior
            # Can override specific methods
            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["custom_data"] = self.object.local_custom_analysis()
                return context
        ```

        **5. Method Override Checklist**
        Common methods to override when inheriting:
        - `get_context_data()`: Add custom template variables
        - `get_template_names()`: Customize template resolution
        - `has_permission()`: Add custom permission logic
        - `get_breadcrumbs()`: Customize navigation breadcrumbs
        - `get_queryset()`: For list-based views (FormSetView, etc.)
        - `get_success_url()`: For form-based views (UpdateView, DeleteView)

        **6. Class Attributes to Set**
        When creating plugins, consider setting:
        - `menu`: Tab configuration (required for tab visibility)
        - `permission`: Django permission string for access control
        - `template_name`: Explicit template path (or rely on resolution)
        - `url_path`: Custom URL segment (or auto-generated from name)
        - `check`: Visibility check function for polymorphic filtering

        **7. Static Assets with Django Media Class**
        Plugins can include CSS and JavaScript assets using Django's Media class:

        ```python
        from fairdm.plugins import Plugin, register_plugin
        from django.views.generic import TemplateView


        @register_plugin(Sample)
        class ChartPlugin(Plugin, TemplateView):
            menu = {"label": "Charts", "icon": "chart", "order": 40}

            class Media:
                css = {
                    "all": ("plugins/chart/chart.css",),
                }
                js = (
                    "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js",
                    "plugins/chart/chart-init.js",
                )

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["chart_data"] = self.object.get_chart_data()
                return context
        ```

        The Media class assets are automatically included in the template context as `plugin_media`.
        Include them in your template:

        ```html
        {% extends "plugins/base.html" %}

        {% block extra_head %}
            {{ plugin_media.css }}
        {% endblock %}

        {% block content %}
            <canvas id="myChart"></canvas>
        {% endblock %}

        {% block extra_js %}
            {{ plugin_media.js }}
        {% endblock %}
        ```

        **Media Class Options:**
        - `css`: Dict mapping media types to tuples of CSS file paths
          - Keys: "all", "screen", "print", etc.
          - Values: Tuples of file paths (relative to STATIC_ROOT or absolute URLs)
        - `js`: Tuple of JavaScript file paths (order matters for dependencies)

        **Best Practices:**
        - Place plugin-specific assets in `static/plugins/{plugin_name}/`
        - Use CDN URLs for large third-party libraries (Chart.js, D3.js, etc.)
        - Minify assets for production
        - Use Django's collectstatic command to gather assets
        - Consider using webpack or vite for complex asset pipelines

        **Example with Multiple CSS Media Queries:**
        ```python
        class Media:
            css = {
                "all": ("plugins/base.css",),
                "screen": ("plugins/screen.css",),
                "print": ("plugins/print.css",),
            }
            js = (
                "plugins/vendor/jquery.min.js",  # Load first (dependency)
                "plugins/main.js",  # Load after jQuery
            )
        ```

    See Also:
        - PluginGroup: For grouping multiple plugins under shared namespace
        - register_plugin: Decorator for plugin registration
        - is_instance_of: Helper for polymorphic visibility checks
    """

    # Class attributes (can be overridden by subclasses)
    name: ClassVar[str | None] = None
    url_path: ClassVar[str | None] = None
    template_name: str = ""
    permission: ClassVar[str | None] = None
    check: ClassVar[Callable[[HttpRequest, Model | None], bool] | None] = None
    model: ClassVar[type[Model] | None] = None
    menu: ClassVar[dict[str, Any] | None] = None

    @classmethod
    def get_name(cls) -> str:
        """Get the plugin name (slugified class name if not set).

        Returns:
            Plugin name used for URL naming and identification
        """
        if cls.name:
            return cls.name
        from .utils import slugify

        return slugify(cls.__name__)

    @classmethod
    def get_url_path(cls) -> str:
        """Get the URL path segment.

        Returns:
            URL path segment (e.g., "analysis" or "download")
        """
        if cls.url_path:
            return cls.url_path
        return cls.get_name()

    @classmethod
    def get_urls(cls) -> list[URLPattern]:
        """Generate URL pattern(s) for this plugin.

        Returns:
            List containing one URLPattern for simple plugins.
            Subclasses may override to return multiple patterns.
        """
        return [
            path(f"{cls.get_url_path()}/", cls.as_view(), name=cls.get_name()),
        ]

    def get_object(self) -> Model:
        """Fetch model instance from URL kwargs.

        Returns:
            Model instance based on URL kwargs (typically 'pk' or 'uuid')

        Raises:
            Model.DoesNotExist: If instance not found
        """
        if not self.model:
            msg = f"Plugin {self.__class__.__name__} has no associated model"
            raise ValueError(msg)

        pk = self.kwargs.get("pk") or self.kwargs.get("uuid")
        if not pk:
            msg = "Plugin URL must include 'pk' or 'uuid' kwarg"
            raise ValueError(msg)

        return self.model.objects.get(pk=pk)

    def get_template_names(self) -> list[str]:
        """Hierarchical template resolution.

        Returns template paths in order of precedence:
        1. Explicit template_name if set
        2. plugins/{model_name}/{plugin_name}.html (model-specific)
        3. plugins/{parent_model_name}/{plugin_name}.html (for polymorphic models)
        4. plugins/{plugin_name}.html (plugin default)
        5. plugins/base.html (framework fallback)

        Returns:
            List of template paths to try in order
        """
        templates = []

        # 1. Explicit template_name
        if self.template_name:
            templates.append(self.template_name)

        plugin_name = self.get_name()

        # 2. Model-specific template
        if self.model:
            model_name = self.model._meta.model_name
            templates.append(f"plugins/{model_name}/{plugin_name}.html")

            # 3. Parent model template (for polymorphic models)
            # Check if model has a polymorphic parent
            if hasattr(self.model, "_meta") and hasattr(self.model._meta, "get_parent_list"):
                for parent in self.model._meta.get_parent_list():
                    parent_name = parent._meta.model_name
                    templates.append(f"plugins/{parent_name}/{plugin_name}.html")

        # 4. Plugin default template
        templates.append(f"plugins/{plugin_name}.html")

        # 5. Framework fallback
        templates.append("plugins/base.html")

        return templates

    def has_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Two-tier permission check.

        Checks both model-level and object-level permissions.

        Args:
            request: HTTP request
            obj: Model instance (optional, for object-level checks)

        Returns:
            True if user has permission
        """
        # No permission requirement
        if not self.permission:
            return True

        # Model-level permission check
        if not request.user.has_perm(self.permission):
            return False

        # Object-level permission check (if guardian is available)
        if obj:
            try:
                from guardian.shortcuts import get_objects_for_user

                # Check if user has object-level permission
                queryset = get_objects_for_user(request.user, self.permission, klass=obj.__class__)
                return queryset.filter(pk=obj.pk).exists()
            except ImportError:
                # Guardian not available, rely on model-level check
                pass

        return True

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Permission-gated dispatch.

        Checks permissions before allowing access to the view.

        Args:
            request: HTTP request
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            HTTP response

        Raises:
            PermissionDenied: If user lacks required permissions
        """
        # Get object for permission checking
        try:
            obj = self.get_object()
        except (ValueError, self.model.DoesNotExist):  # type: ignore[union-attr]
            obj = None

        # Check permissions
        if not self.has_permission(request, obj):
            raise PermissionDenied

        # Store object for use in view methods
        if obj:
            self.object = obj  # type: ignore[attr-defined]

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add plugin-specific context data.

        Adds:
        - object: Model instance
        - tabs: List of Tab objects for this model
        - breadcrumbs: Breadcrumb navigation chain
        - plugin_media: Static assets for this plugin

        Args:
            **kwargs: Additional context

        Returns:
            Context dictionary
        """
        context = super().get_context_data(**kwargs)  # type: ignore[misc]

        # Add object if not already present
        if not context.get("object"):
            try:
                context["object"] = self.get_object()
            except (ValueError, Exception):
                context["object"] = None

        # Add breadcrumbs
        context["breadcrumbs"] = self.get_breadcrumbs()

        # Add tabs with active tab detection
        if self.model and hasattr(self, "request"):
            from .registry import registry

            tabs = registry.get_tabs_for_model(self.model, self.request, context.get("object"))  # type: ignore[attr-defined]

            # Mark current tab as active
            for tab in tabs:
                # Tab is active if its URL name matches the current plugin
                # Note: For PluginGroups, we'd need to check against the group's default plugin
                if hasattr(self, "request"):
                    # Check if current URL matches this tab's plugin
                    # This is a simple comparison - could be enhanced with URL resolution
                    tab.is_active = (tab.label == self.menu.get("label")) if self.menu else False

            context["tabs"] = tabs
        else:
            context["tabs"] = []

        # Add plugin media
        if hasattr(self, "Media"):
            from django.forms.widgets import Media

            context["plugin_media"] = Media(self.Media)
        else:
            context["plugin_media"] = None

        return context

    def get_breadcrumbs(self) -> list[dict[str, Any]]:
        """Auto-generate breadcrumb navigation chain.

        Returns:
            List of breadcrumb dicts with 'text' and optionally 'href' keys
        """
        breadcrumbs = []

        # Add model list view breadcrumb
        if self.model:
            model_name = self.model._meta.verbose_name_plural
            # TODO: Reverse model list URL
            breadcrumbs.append({"text": model_name, "href": "/"})

        # Add object breadcrumb
        try:
            obj = self.get_object()
            obj_str = str(obj)
            # Truncate long object names
            if len(obj_str) > 50:
                obj_str = obj_str[:47] + "..."
            # TODO: Reverse object detail URL
            breadcrumbs.append({"text": obj_str, "href": "#"})
        except (ValueError, Exception):  # noqa: S110
            pass

        # Add current page breadcrumb
        if self.menu:
            page_title = self.menu.get("label", self.get_name())
            breadcrumbs.append({"text": page_title})

        return breadcrumbs
