"""
Tests for custom URL configuration in plugins.

User Story 6: Custom URL Patterns
"""

from django.urls import path
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.sample.models import Sample


class TestCustomURLs:
    """Test custom URL patterns (User Story 6)."""

    def test_plugin_with_custom_url_path(self):
        """Given a plugin with a custom url_path,
        When generating URLs,
        Then the custom path is used (User Story 6, Scenario 1)."""

        @plugins.register(Sample)
        class CustomURLPlugin(Plugin, TemplateView):
            url_path = "custom/analysis"
            menu = {"label": "Custom", "icon": "custom", "order": 10}
            template_name = "custom.html"

        # Verify custom URL path is set
        assert CustomURLPlugin.get_url_path() == "custom/analysis"

    def test_plugin_with_get_urls_override(self):
        """Given a plugin with overridden get_urls classmethod,
        When generating URL patterns,
        Then custom URL patterns are used (User Story 6, Scenario 2)."""

        @plugins.register(Sample)
        class MultiURLPlugin(Plugin, TemplateView):
            menu = {"label": "Multi", "icon": "multi", "order": 20}
            template_name = "multi.html"

            @classmethod
            def get_urls(cls):
                return [
                    path("main/", cls.as_view(), name=f"{cls.get_name()}-main"),
                    path("export/", cls.as_view(), name=f"{cls.get_name()}-export"),
                ]

        # Get URLs
        url_patterns = MultiURLPlugin.get_urls()

        # Should have two URL patterns
        assert len(url_patterns) == 2

        # Check URL names
        url_names = [p.name for p in url_patterns]
        assert f"{MultiURLPlugin.get_name()}-main" in url_names
        assert f"{MultiURLPlugin.get_name()}-export" in url_names


class TestDefaultURLGeneration:
    """Test default URL generation for plugins."""

    def test_default_url_path_from_class_name(self):
        """Without custom url_path, URL path is derived from class name."""

        @plugins.register(Sample)
        class DefaultURLPlugin(Plugin, TemplateView):
            menu = {"label": "Default", "icon": "default", "order": 30}
            template_name = "default.html"

        # Default slug should be kebab-case of class name
        # Note: "DefaultURLPlugin" → "default-u-r-l-plugin" (each capital gets hyphen)
        expected_path = "default-u-r-l-plugin"
        assert DefaultURLPlugin.get_url_path() == expected_path

    def test_default_url_name_from_class_name(self):
        """Without custom URL names, name is derived from class name."""

        @plugins.register(Sample)
        class NamedPlugin(Plugin, TemplateView):
            menu = {"label": "Named", "icon": "name", "order": 40}
            template_name = "named.html"

        # Default name should be kebab-case of class name
        expected_name = "named-plugin"
        assert NamedPlugin.get_name() == expected_name


class TestURLParameters:
    """Test URL patterns with parameters."""

    def test_plugin_url_includes_pk_parameter(self):
        """Plugin URLs are simple paths that get included under parent pk route."""

        @plugins.register(Sample)
        class ParamPlugin(Plugin, TemplateView):
            menu = {"label": "Param", "icon": "param", "order": 50}
            template_name = "param.html"

        # Default get_urls should return simple path (pk handled by parent route)
        url_patterns = ParamPlugin.get_urls()

        # Should have at least one URL pattern
        assert len(url_patterns) > 0

        # First pattern should be simple (no pk - that's in parent routing)
        first_pattern = url_patterns[0]
        pattern_str = str(first_pattern.pattern)

        # Should just be the plugin path
        assert pattern_str == "param-plugin/"
