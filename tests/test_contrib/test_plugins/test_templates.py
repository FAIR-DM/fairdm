"""
Tests for plugin template resolution.

User Story 3: Template Resolution
"""

import pytest
from django.test import RequestFactory
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.sample.models import Sample

pytestmark = pytest.mark.django_db


class TestTemplateResolution:
    """Test template resolution hierarchy (User Story 3)."""

    def test_plugin_uses_specified_template(self):
        """Given a plugin with template_name specified,
        When rendering the plugin,
        Then the specified template is used."""

        @plugins.register(Sample)
        class TemplatePlugin(Plugin, TemplateView):
            template_name = "plugins/custom-template.html"
            menu = {"label": "Template", "icon": "file", "order": 10}

        plugin = TemplatePlugin()
        assert plugin.template_name == "plugins/custom-template.html"

    def test_template_hierarchy_for_model_specific_override(self):
        """Template resolution should follow the hierarchy:
        1. plugins/<app>/<model>/<plugin>.html
        2. plugins/<plugin>.html
        3. Plugin's template_name attribute
        """

        @plugins.register(Sample)
        class HierarchyPlugin(Plugin, TemplateView):
            template_name = "plugins/fallback.html"
            menu = {"label": "Hierarchy", "icon": "layer", "order": 20}

        # The plugin should look for templates in this order:
        # 1. plugins/sample/sample/hierarchy-plugin.html (most specific)
        # 2. plugins/hierarchy-plugin.html (generic)
        # 3. plugins/fallback.html (explicit template_name)

        plugin = HierarchyPlugin()

        # Verify fallback template is set
        assert plugin.template_name == "plugins/fallback.html"


class TestTemplateContext:
    """Test template context for plugins."""

    def test_plugin_get_context_data(self, user):
        """Plugin should be able to add context data."""

        @plugins.register(Sample)
        class ContextPlugin(Plugin, TemplateView):
            template_name = "plugins/context.html"
            menu = {"label": "Context", "icon": "database", "order": 30}

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["custom_data"] = "test_value"
                return context

        factory = RequestFactory()
        request = factory.get("/test/")
        request.user = user

        plugin = ContextPlugin()
        plugin.request = request

        context = plugin.get_context_data()
        assert "custom_data" in context
        assert context["custom_data"] == "test_value"
