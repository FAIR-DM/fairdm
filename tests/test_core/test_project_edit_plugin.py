"""
Test the Edit plugin for the Project model.

NOTE: These tests are skipped pending plugin system redesign.
The plugin API has changed significantly (category attribute location, configuration structure).
"""

import pytest

# Skip entire module - plugin API has changed
pytestmark = pytest.mark.skip(reason="Plugin API changed - awaiting plugin system redesign completion")

from fairdm import plugins
from fairdm.core.project.forms import ProjectForm
from fairdm.core.project.models import Project
from fairdm.factories.core import ProjectFactory


@pytest.mark.django_db
class TestProjectEditPlugin:
    """Tests for the Project Edit plugin."""

    def test_edit_plugin_is_registered(self):
        """Test that the Edit plugin is registered for Project model."""
        view_class = plugins.registry.get_view_for_model(Project)
        assert view_class is not None

        # Find the Edit plugin
        edit_plugin = None
        for plugin in view_class.plugins:
            if plugin.__name__ == "Edit":
                edit_plugin = plugin
                break

        assert edit_plugin is not None, "Edit plugin should be registered"

    def test_edit_plugin_configuration(self):
        """Test that the Edit plugin has correct configuration."""
        view_class = plugins.registry.get_view_for_model(Project)

        # Find the Edit plugin
        edit_plugin = None
        for plugin in view_class.plugins:
            if plugin.__name__ == "Edit":
                edit_plugin = plugin
                break

        assert edit_plugin is not None
        assert edit_plugin.category == plugins.MANAGEMENT
        assert edit_plugin.form_class == ProjectForm
        assert edit_plugin.fields == ["image", "name", "visibility", "status"]
        assert edit_plugin.menu_item is not None
        assert edit_plugin.menu_item.name == "Edit"
        assert edit_plugin.about is not None

    def test_edit_plugin_in_management_menu(self):
        """Test that the Edit plugin appears in the management menu."""
        view_class = plugins.registry.get_view_for_model(Project)

        # Check that the management menu has items
        management_menu = view_class.menus.get("management")
        assert management_menu is not None

        # Check if Edit menu item is present
        menu_items = [item.name for item in management_menu.children]
        assert "Edit" in menu_items

    def test_edit_plugin_url_generation(self):
        """Test that Edit plugin generates proper URL patterns."""
        view_class = plugins.registry.get_view_for_model(Project)
        urls = view_class.get_urls()

        # Should have URLs for the plugin
        assert len(urls) > 0

        # Check that there's a URL pattern for the edit plugin
        url_names = [url.name for url in urls if url.name]
        # The URL name should be based on the plugin class name
        assert any("edit" in name.lower() for name in url_names)

    def test_edit_plugin_has_correct_form_fields(self):
        """Test that the Edit plugin exposes the correct form fields."""
        view_class = plugins.registry.get_view_for_model(Project)

        # Find the Edit plugin
        edit_plugin = None
        for plugin in view_class.plugins:
            if plugin.__name__ == "Edit":
                edit_plugin = plugin
                break

        assert edit_plugin is not None

        # Verify the fields match what we expect from the ProjectForm
        expected_fields = ["image", "name", "visibility", "status"]
        assert edit_plugin.fields == expected_fields

        # Verify form_class is ProjectForm
        assert edit_plugin.form_class == ProjectForm

    def test_edit_button_in_overview_template(self, client):
        """Test that the edit button appears in the project overview page."""
        # Create a project
        project = ProjectFactory()

        # Get the overview page (note: plugins are accessed via their specific URLs)
        url = f"/project/{project.uuid}/overview/"
        response = client.get(url)

        # Check that the page loads successfully
        assert response.status_code == 200

        # Check that the edit button/link is present in the response
        # The template uses plugin_url 'edit' which should generate a link to the edit plugin
        edit_url = f"/project/{project.uuid}/management/edit/"
        assert edit_url.encode() in response.content or b"edit" in response.content

    def test_edit_plugin_template_resolution_order(self, rf):
        """Test that EditPlugin uses correct template resolution order."""
        project = ProjectFactory()

        # Get the Edit plugin class
        view_class = plugins.registry.get_view_for_model(Project)
        edit_plugin = None
        for plugin in view_class.plugins:
            if plugin.__name__ == "Edit":
                edit_plugin = plugin
                break

        assert edit_plugin is not None

        # Create a request and instantiate the plugin view
        request = rf.get(f"/project/{project.uuid}/management/edit/")

        # Instantiate the view
        view = edit_plugin()
        view.request = request
        view.base_model = Project
        view.base_object = project
        view.kwargs = {"uuid": str(project.uuid)}

        # Get the template names
        template_names = view.get_template_names()

        # Expected order:
        # 1. project/plugins/edit.html
        # 2. fairdm/plugins/edit.html
        # 3. fairdm/plugins/form.html (generic form template)
        # 4. fairdm/plugin.html (fallback)
        expected_templates = [
            "project/plugins/edit.html",
            "fairdm/plugins/edit.html",
            "fairdm/plugins/form.html",
            "fairdm/plugin.html",
        ]

        assert template_names == expected_templates
