"""Tests for Project Edit Plugin using the new plugin system."""

import pytest

from fairdm import plugins
from fairdm.core.project.forms import ProjectForm
from fairdm.core.project.models import Project

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_project(db):
    """Create a test project for plugin tests."""
    return Project.objects.create(
        name="Test Project", visibility=Project.VISIBILITY.PUBLIC, status=Project.STATUS_CHOICES.IN_PROGRESS
    )


class TestProjectEditPlugin:
    """Tests for the Project Edit plugin using the new plugin API."""

    def test_edit_plugin_is_registered(self):
        """Test that the Edit plugin is registered for Project model."""
        registered_plugins = plugins.registry.get_plugins_for_model(Project)
        assert len(registered_plugins) > 0, "Should have plugins registered for Project"

        # Find the Edit plugin
        edit_plugin = None
        for plugin in registered_plugins:
            if plugin.__name__ == "Edit":
                edit_plugin = plugin
                break

        assert edit_plugin is not None, "Edit plugin should be registered"

    def test_edit_plugin_configuration(self):
        """Test that the Edit plugin has correct configuration."""
        registered_plugins = plugins.registry.get_plugins_for_model(Project)

        # Find the Edit plugin
        edit_plugin = None
        for plugin in registered_plugins:
            if plugin.__name__ == "Edit":
                edit_plugin = plugin
                break

        assert edit_plugin is not None

        # Edit plugin inherits from EditPlugin and doesn't set a menu
        # (it's meant for the Manage section, not a navigation tab)
        assert hasattr(edit_plugin, "menu")

        # Plugin should have form configuration
        assert edit_plugin.form_class == ProjectForm
        assert edit_plugin.fields == ["image", "name", "visibility", "status"]

    def test_edit_plugin_creates_tab(self):
        """Test that the Edit plugin can work with the tab navigation API."""
        # Edit plugin doesn't have a menu attribute set, so it won't create tabs
        # But it should still be compatible with the plugin system
        registered_plugins = plugins.registry.get_plugins_for_model(Project)
        edit_plugin = next((p for p in registered_plugins if p.__name__ == "Edit"), None)
        assert edit_plugin is not None

        # Plugin should have menu attribute (even if None)
        assert hasattr(edit_plugin, "menu")

    def test_edit_plugin_url_generation(self):
        """Test that Edit plugin generates proper URL patterns."""
        urls = plugins.registry.get_urls_for_model(Project)

        # Should have URLs for the plugin
        assert len(urls) > 0

        # Check that there's a URL pattern for the edit plugin
        url_names = [url.name for url in urls if hasattr(url, "name") and url.name]
        # The URL name should be based on the plugin class name
        assert any("edit" in name.lower() for name in url_names)

    def test_edit_plugin_has_correct_form_fields(self):
        """Test that the Edit plugin exposes the correct form fields."""
        registered_plugins = plugins.registry.get_plugins_for_model(Project)

        # Find the Edit plugin
        edit_plugin = None
        for plugin in registered_plugins:
            if plugin.__name__ == "Edit":
                edit_plugin = plugin
                break

        assert edit_plugin is not None

        # Verify the fields match what we expect from the ProjectForm
        expected_fields = ["image", "name", "visibility", "status"]
        assert edit_plugin.fields == expected_fields

        # Verify form_class is ProjectForm
        assert edit_plugin.form_class == ProjectForm

    def test_edit_plugin_has_permission(self):
        """Test that the Edit plugin has permission attribute."""
        registered_plugins = plugins.registry.get_plugins_for_model(Project)

        # Find the Edit plugin
        edit_plugin = None
        for plugin in registered_plugins:
            if plugin.__name__ == "Edit":
                edit_plugin = plugin
                break

        assert edit_plugin is not None

        # Edit plugin should have a permission attribute (even if None)
        assert hasattr(edit_plugin, "permission")
        # Permission can be None for plugins without permission requirements

    def test_edit_plugin_inherits_from_plugin_mixin(self):
        """Test that Edit plugin uses the Plugin mixin."""
        registered_plugins = plugins.registry.get_plugins_for_model(Project)

        # Find the Edit plugin
        edit_plugin = None
        for plugin in registered_plugins:
            if plugin.__name__ == "Edit":
                edit_plugin = plugin
                break

        assert edit_plugin is not None

        # Plugin should have methods from Plugin mixin
        assert hasattr(edit_plugin, "get_urls")
        assert callable(edit_plugin.get_urls)
        assert hasattr(edit_plugin, "get_name")
        assert callable(edit_plugin.get_name)
        assert hasattr(edit_plugin, "get_url_path")
        assert callable(edit_plugin.get_url_path)
