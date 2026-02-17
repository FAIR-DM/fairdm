"""
Tests for plugin registration functionality.

User Story 1: Basic Plugin Registration and Display
"""

from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.sample.models import Sample


class TestBasicRegistration:
    """Test basic plugin registration (User Story 1, Scenario 1)."""

    def test_register_plugin_for_single_model(self):
        """Given a plugin class with @plugins.register decorator,
        When registered for a single model,
        Then the plugin is registered without errors."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            menu = {"label": "Test", "icon": "test", "order": 10}
            template_name = "test.html"

        # Verify registration
        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [p.__name__ for p in registered_plugins]
        assert "TestPlugin" in plugin_names

    def test_register_plugin_for_multiple_models(self):
        """Given a plugin registered for multiple model types,
        When visiting detail pages for any of those models,
        Then the plugin appears on all applicable detail pages (User Story 1, Scenario 3)."""
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import Project

        @plugins.register(Project, Dataset, Sample)
        class MultiModelPlugin(Plugin, TemplateView):
            menu = {"label": "Multi", "icon": "multi", "order": 20}
            template_name = "multi.html"

        # Verify registration on all models
        for model in [Project, Dataset, Sample]:
            registered_plugins = plugins.registry.get_plugins_for_model(model)
            plugin_names = [p.__name__ for p in registered_plugins]
            assert "MultiModelPlugin" in plugin_names

    def test_plugin_appears_in_url_patterns(self):
        """Given a registered plugin for a Sample model,
        When getting URLs for that model,
        Then the plugin's URL pattern is included."""

        @plugins.register(Sample)
        class URLTestPlugin(Plugin, TemplateView):
            menu = {"label": "URL Test", "icon": "url", "order": 30}
            template_name = "url_test.html"

        url_patterns = plugins.registry.get_urls_for_model(Sample)
        # Convert to list of URL pattern names
        url_names = []
        for pattern in url_patterns:
            if hasattr(pattern, "name") and pattern.name:
                url_names.append(pattern.name)

        # URL name should be slugified class name: "URLTestPlugin" → "u-r-l-test-plugin"
        assert any("u-r-l-test-plugin" in name for name in url_names)


class TestPluginDeregistration:
    """Test that plugins can be properly managed in registry."""

    def test_get_plugins_returns_list(self):
        """Registry should return a list of registered plugins."""
        plugins_list = plugins.registry.get_plugins_for_model(Sample)
        assert isinstance(plugins_list, list)

    def test_get_plugins_for_unregistered_model(self):
        """Getting plugins for a model with no plugins returns empty list."""
        from django.contrib.auth.models import User

        # User model should have no plugins registered
        plugins_list = plugins.registry.get_plugins_for_model(User)
        assert plugins_list == []


class TestPluginAttributes:
    """Test that plugin classes have required attributes and methods."""

    def test_plugin_has_get_urls_classmethod(self):
        """All plugins should have a get_urls classmethod."""

        @plugins.register(Sample)
        class AttributeTestPlugin(Plugin, TemplateView):
            menu = {"label": "Attr", "icon": "attr", "order": 40}
            template_name = "attr.html"

        assert hasattr(AttributeTestPlugin, "get_urls")
        assert callable(AttributeTestPlugin.get_urls)

    def test_plugin_has_get_name_classmethod(self):
        """All plugins should have a get_name classmethod."""

        @plugins.register(Sample)
        class NameTestPlugin(Plugin, TemplateView):
            menu = {"label": "Name", "icon": "name", "order": 50}
            template_name = "name.html"

        assert hasattr(NameTestPlugin, "get_name")
        assert callable(NameTestPlugin.get_name)
        assert NameTestPlugin.get_name() == "name-test-plugin"

    def test_plugin_has_get_url_path_classmethod(self):
        """All plugins should have a get_url_path classmethod."""

        @plugins.register(Sample)
        class PathTestPlugin(Plugin, TemplateView):
            menu = {"label": "Path", "icon": "path", "order": 60}
            template_name = "path.html"

        assert hasattr(PathTestPlugin, "get_url_path")
        assert callable(PathTestPlugin.get_url_path)
        assert PathTestPlugin.get_url_path() == "path-test-plugin"
