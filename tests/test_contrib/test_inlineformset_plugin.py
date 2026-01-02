"""
Test the InlineFormSetPlugin template resolution.
"""

import pytest

from fairdm import plugins
from fairdm.contrib.contributors.models import Contributor


@pytest.mark.django_db
class TestInlineFormSetPluginTemplateResolution:
    """Tests for InlineFormSetPlugin template resolution order."""

    def test_identifiers_plugin_template_resolution_order(self, rf):
        """Test that Identifiers plugin uses correct template resolution order."""
        from fairdm.factories.contributors import PersonFactory

        person = PersonFactory()

        # Get the Identifiers plugin class
        view_class = plugins.registry.get_view_for_model(Contributor)
        identifiers_plugin = None
        for plugin in view_class.plugins:
            if plugin.__name__ == "Identifiers":
                identifiers_plugin = plugin
                break

        assert identifiers_plugin is not None

        # Create a request and instantiate the plugin view
        request = rf.get(f"/contributor/{person.uuid}/management/identifiers/")

        # Instantiate the view
        view = identifiers_plugin()
        view.request = request
        view.base_model = Contributor
        view.base_object = person
        view.kwargs = {"uuid": str(person.uuid)}

        # Get the template names
        template_names = view.get_template_names()

        # Expected order:
        # 1. contributor/plugins/identifiers.html
        # 2. fairdm/plugins/identifiers.html
        # 3. fairdm/plugins/formset.html (generic formset template)
        # 4. fairdm/plugin.html (fallback)
        expected_templates = [
            "contributor/plugins/identifiers.html",
            "fairdm/plugins/identifiers.html",
            "fairdm/plugins/formset.html",
            "fairdm/plugin.html",
        ]

        assert template_names == expected_templates

    def test_affiliations_plugin_template_resolution_order(self, rf):
        """Test that Affiliations plugin uses correct template resolution order."""
        from fairdm.contrib.contributors.models import Person
        from fairdm.factories.contributors import PersonFactory

        person = PersonFactory()

        # Get the Affiliations plugin class
        view_class = plugins.registry.get_view_for_model(Person)
        affiliations_plugin = None
        for plugin in view_class.plugins:
            if plugin.__name__ == "Affiliations":
                affiliations_plugin = plugin
                break

        assert affiliations_plugin is not None

        # Create a request and instantiate the plugin view
        request = rf.get(f"/person/{person.uuid}/management/affiliations/")

        # Instantiate the view
        view = affiliations_plugin()
        view.request = request
        view.base_model = Person
        view.base_object = person
        view.kwargs = {"uuid": str(person.uuid)}

        # Get the template names
        template_names = view.get_template_names()

        # Expected order:
        # 1. person/plugins/affiliations.html
        # 2. fairdm/plugins/affiliations.html
        # 3. fairdm/plugins/formset.html (generic formset template)
        # 4. fairdm/plugin.html (fallback)
        expected_templates = [
            "person/plugins/affiliations.html",
            "fairdm/plugins/affiliations.html",
            "fairdm/plugins/formset.html",
            "fairdm/plugin.html",
        ]

        assert template_names == expected_templates
