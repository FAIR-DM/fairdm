"""
Integration tests for the plugin system.

Tests the complete plugin workflow from registration to rendering.
"""

import pytest
from django.test import RequestFactory
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, PluginGroup
from fairdm.core.plugins import BaseEditPlugin, BaseOverviewPlugin
from fairdm.core.sample.models import Sample

pytestmark = pytest.mark.django_db


class TestPluginIntegration:
    """Integration tests for complete plugin workflows."""

    def test_plugin_registration_to_url_generation(self, sample, user):
        """Test complete flow from registration to URL generation."""

        @plugins.register(Sample)
        class IntegrationPlugin(Plugin, TemplateView):
            menu = {"label": "Integration", "icon": "integrate", "order": 10}
            template_name = "plugins/integration.html"

        # 1. Plugin should be registered
        registered = plugins.registry.get_plugins_for_model(Sample)
        assert any(p.__name__ == "IntegrationPlugin" for p in registered)

        # 2. Tab should be created
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user
        tabs = plugins.registry.get_tabs_for_model(Sample, request, sample)
        integration_tab = next((t for t in tabs if t.label == "Integration"), None)
        assert integration_tab is not None

        # 3. URLs should be generated
        urls = plugins.registry.get_urls_for_model(Sample)
        assert len(urls) > 0

    def test_plugin_group_integration(self, sample, user):
        """Test PluginGroup integration workflow."""

        class SubPlugin1(Plugin, TemplateView):
            menu = {"label": "Sub 1", "icon": "s1", "order": 10}
            template_name = "sub1.html"

        class SubPlugin2(Plugin, TemplateView):
            menu = {"label": "Sub 2", "icon": "s2", "order": 20}
            template_name = "sub2.html"

        @plugins.register(Sample)
        class GroupIntegration(PluginGroup):
            plugins = [SubPlugin1, SubPlugin2]
            menu = {"label": "Group", "icon": "group", "order": 100}

        # 1. Group should be registered
        registered = plugins.registry.get_plugins_for_model(Sample)
        assert any(p.__name__ == "GroupIntegration" for p in registered)

        # 2. Single tab for the group
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user
        tabs = plugins.registry.get_tabs_for_model(Sample, request, sample)
        group_tabs = [t for t in tabs if t.label == "Group"]
        assert len(group_tabs) == 1

        # 3. URLs for all subplugins
        urls = plugins.registry.get_urls_for_model(Sample)
        assert len(urls) > 0

    def test_multiple_models_integration(self, sample, dataset, user):
        """Test plugin registered for multiple models."""
        from fairdm.core.dataset.models import Dataset

        @plugins.register(Sample, Dataset)
        class MultiModelIntegration(Plugin, TemplateView):
            menu = {"label": "Multi", "icon": "multi", "order": 50}
            template_name = "multi.html"

        # Should be registered for both models
        sample_plugins = plugins.registry.get_plugins_for_model(Sample)
        dataset_plugins = plugins.registry.get_plugins_for_model(Dataset)

        assert any(p.__name__ == "MultiModelIntegration" for p in sample_plugins)
        assert any(p.__name__ == "MultiModelIntegration" for p in dataset_plugins)

        # Should have tabs for both models
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user
        sample_tabs = plugins.registry.get_tabs_for_model(Sample, request, sample)
        dataset_tabs = plugins.registry.get_tabs_for_model(Dataset, request, dataset)

        assert any(t.label == "Multi" for t in sample_tabs)
        assert any(t.label == "Multi" for t in dataset_tabs)


class TestBaseClassIntegration:
    """Integration tests for reusable base classes."""

    def test_base_overview_plugin_integration(self, sample, user):
        """Test BaseOverviewPlugin integration."""

        @plugins.register(Sample)
        class Overview(BaseOverviewPlugin):
            menu = {"label": "Overview", "icon": "info", "order": 1}

        # Should be registered
        registered = plugins.registry.get_plugins_for_model(Sample)
        assert any(p.__name__ == "Overview" for p in registered)

        # Should create tab
        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/overview/")
        request.user = user
        tabs = plugins.registry.get_tabs_for_model(Sample, request, sample)
        overview_tab = next((t for t in tabs if t.label == "Overview"), None)
        assert overview_tab is not None

        # Should provide context
        plugin = Overview()
        plugin.request = request
        plugin.kwargs = {"pk": sample.pk}

        context = plugin.get_context_data()
        assert "object" in context

    def test_base_edit_plugin_integration(self, sample, admin_user):
        """Test BaseEditPlugin integration."""

        @plugins.register(Sample)
        class Edit(BaseEditPlugin):
            menu = {"label": "Edit", "icon": "edit", "order": 10}
            permission = "sample.change_sample"
            fields = ["name", "description"]

        # Should be registered
        registered = plugins.registry.get_plugins_for_model(Sample)
        assert any(p.__name__ == "Edit" for p in registered)

        # Should have permission attribute
        assert hasattr(Edit, "permission")
        assert Edit.permission == "sample.change_sample"

        # Should have fields
        assert Edit.fields == ["name", "description"]


class TestPluginURLResolution:
    """Test URL resolution and routing."""

    def test_plugin_url_resolution(self, sample):
        """Test that plugin URLs can be resolved."""

        @plugins.register(Sample)
        class URLResolution(Plugin, TemplateView):
            menu = {"label": "URL Test", "icon": "url", "order": 30}
            template_name = "url_test.html"

        # Get URLs for Sample
        urls = plugins.registry.get_urls_for_model(Sample)

        # Should have at least one URL
        assert len(urls) > 0

        # URLs should have names
        url_names = [p.name for p in urls if hasattr(p, "name") and p.name]
        assert len(url_names) > 0


class TestPermissionIntegration:
    """Test permission integration in the full workflow."""

    def test_permission_enforcement_integration(self, sample, user, admin_user):
        """Test permission enforcement through the stack."""

        @plugins.register(Sample)
        class PermissionIntegration(Plugin, TemplateView):
            permission = "sample.change_sample"
            menu = {"label": "Secure", "icon": "lock", "order": 40}
            template_name = "secure.html"

        # Plugin should have permission attribute
        assert hasattr(PermissionIntegration, "permission")
        assert PermissionIntegration.permission == "sample.change_sample"

        # Regular user should not have permission (model-level check)
        assert not user.has_perm("sample.change_sample")

        # Admin should have permission
        assert admin_user.has_perm("sample.change_sample")
