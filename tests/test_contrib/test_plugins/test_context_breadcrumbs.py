"""
Tests for plugin context and breadcrumb functionality.

User Story 7: Context and Breadcrumbs
"""

import pytest
from django.test import RequestFactory
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.sample.models import Sample

pytestmark = pytest.mark.django_db


class TestPluginContext:
    """Test plugin context data (User Story 7)."""

    def test_plugin_get_object_returns_instance(self, sample):
        """Given a plugin view,
        When get_object is called,
        Then it returns the model instance."""

        @plugins.register(Sample)
        class ObjectPlugin(Plugin, TemplateView):
            menu = {"label": "Object", "icon": "obj", "order": 10}
            template_name = "object.html"

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/object/")

        plugin = ObjectPlugin()
        plugin.request = request
        plugin.kwargs = {"pk": sample.pk}

        # Get object
        obj = plugin.get_object()
        assert obj == sample
        assert isinstance(obj, Sample)

    def test_plugin_context_object(self, sample, user):
        """Plugin context should contain the object."""

        @plugins.register(Sample)
        class ContextObjPlugin(Plugin, TemplateView):
            menu = {"label": "Context", "icon": "ctx", "order": 20}
            template_name = "context.html"

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/context/")
        request.user = user

        plugin = ContextObjPlugin()
        plugin.request = request
        plugin.kwargs = {"pk": sample.pk}

        context = plugin.get_context_data()

        # Should have object in context
        assert "object" in context
        assert context["object"] == sample


class TestPluginBreadcrumbs:
    """Test breadcrumb generation (User Story 7)."""

    def test_plugin_get_breadcrumbs(self, sample, user):
        """Given a plugin with get_breadcrumbs method,
        When called,
        Then it returns breadcrumb navigation (User Story 7, Scenario 2)."""

        @plugins.register(Sample)
        class BreadcrumbPlugin(Plugin, TemplateView):
            menu = {"label": "Breadcrumb", "icon": "bread", "order": 30}
            template_name = "breadcrumb.html"

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/breadcrumb/")
        request.user = user

        plugin = BreadcrumbPlugin()
        plugin.request = request
        plugin.kwargs = {"pk": sample.pk}

        breadcrumbs = plugin.get_breadcrumbs()

        # Should return a list
        assert isinstance(breadcrumbs, list)

        # Should have at least the current page
        assert len(breadcrumbs) > 0

    def test_breadcrumb_structure(self, sample, user):
        """Breadcrumbs should have proper structure with text and href."""

        @plugins.register(Sample)
        class StructuredBreadcrumb(Plugin, TemplateView):
            menu = {"label": "Structured", "icon": "struct", "order": 40}
            template_name = "structured.html"

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/structured/")
        request.user = user

        plugin = StructuredBreadcrumb()
        plugin.request = request
        plugin.kwargs = {"pk": sample.pk}

        breadcrumbs = plugin.get_breadcrumbs()

        # Each breadcrumb should be a dict with text and optionally href
        for crumb in breadcrumbs:
            assert isinstance(crumb, dict)
            assert "text" in crumb
            # href might be missing for the current page


class TestPluginContextData:
    """Test extended context data functionality."""

    def test_plugin_can_add_custom_context(self, sample, user):
        """Plugins can add custom data to the context."""

        @plugins.register(Sample)
        class CustomContextPlugin(Plugin, TemplateView):
            menu = {"label": "Custom Context", "icon": "custom", "order": 50}
            template_name = "custom_context.html"

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["custom_field"] = "custom_value"
                context["computed_data"] = self.compute_data()
                return context

            def compute_data(self):
                return {"result": 42}

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/custom-context/")
        request.user = user

        plugin = CustomContextPlugin()
        plugin.request = request
        plugin.kwargs = {"pk": sample.pk}

        context = plugin.get_context_data()

        # Should have custom fields
        assert "custom_field" in context
        assert context["custom_field"] == "custom_value"
        assert "computed_data" in context
        assert context["computed_data"]["result"] == 42
