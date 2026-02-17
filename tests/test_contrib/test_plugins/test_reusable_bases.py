"""
Tests for reusable base plugin classes.

User Story 8: Reusable Base Classes
"""

import pytest
from django.test import RequestFactory

from fairdm import plugins
from fairdm.core.plugins import BaseDeletePlugin, BaseEditPlugin, BaseOverviewPlugin
from fairdm.core.sample.models import Sample

pytestmark = pytest.mark.django_db


class TestBaseOverviewPlugin:
    """Test BaseOverviewPlugin reusable base (User Story 8)."""

    def test_overview_plugin_inheritance(self):
        """Given BaseOverviewPlugin as a base,
        When creating a plugin,
        Then minimal configuration is needed (User Story 8, Scenario 1)."""

        @plugins.register(Sample)
        class SampleOverview(BaseOverviewPlugin):
            menu = {"label": "Overview", "icon": "info-circle", "order": 1}

        # Should have template_name from base class
        assert hasattr(SampleOverview, "template_name")

        # Should be properly registered
        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [p.__name__ for p in registered_plugins]
        assert "SampleOverview" in plugin_names

    def test_overview_plugin_provides_context(self, sample, user):
        """BaseOverviewPlugin should provide object context."""

        @plugins.register(Sample)
        class ContextOverview(BaseOverviewPlugin):
            menu = {"label": "Context Overview", "icon": "ctx", "order": 2}

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/context-overview/")
        request.user = user

        plugin = ContextOverview()
        plugin.request = request
        plugin.kwargs = {"pk": sample.pk}

        context = plugin.get_context_data()

        # Should have object in context
        assert "object" in context


class TestBaseEditPlugin:
    """Test BaseEditPlugin reusable base (User Story 8)."""

    def test_edit_plugin_inheritance(self):
        """BaseEditPlugin should provide edit form functionality."""

        @plugins.register(Sample)
        class SampleEdit(BaseEditPlugin):
            menu = {"label": "Edit", "icon": "edit", "order": 10}
            permission = "sample.change_sample"
            fields = ["name", "description"]

        # Should inherit from Plugin and UpdateView
        assert hasattr(SampleEdit, "get_object")
        assert hasattr(SampleEdit, "get_form_class")

        # Should be registered
        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [p.__name__ for p in registered_plugins]
        assert "SampleEdit" in plugin_names

    def test_edit_plugin_with_custom_form_class(self):
        """BaseEditPlugin can use a custom form class."""
        from django import forms

        class CustomSampleForm(forms.ModelForm):
            class Meta:
                model = Sample
                fields = ["name"]

        @plugins.register(Sample)
        class CustomFormEdit(BaseEditPlugin):
            form_class = CustomSampleForm
            menu = {"label": "Custom Edit", "icon": "edit", "order": 11}
            permission = "sample.change_sample"

        # Should use custom form class
        assert CustomFormEdit.form_class == CustomSampleForm


class TestBaseDeletePlugin:
    """Test BaseDeletePlugin reusable base (User Story 8)."""

    def test_delete_plugin_inheritance(self):
        """BaseDeletePlugin should provide delete functionality."""

        @plugins.register(Sample)
        class SampleDelete(BaseDeletePlugin):
            menu = {"label": "Delete", "icon": "trash", "order": 20}
            permission = "sample.delete_sample"

        # Should inherit from Plugin and DeleteView
        assert hasattr(SampleDelete, "get_object")
        assert hasattr(SampleDelete, "delete")

        # Should be registered
        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [p.__name__ for p in registered_plugins]
        assert "SampleDelete" in plugin_names

    def test_delete_plugin_requires_permission(self):
        """BaseDeletePlugin should enforce permissions."""

        @plugins.register(Sample)
        class RestrictedDelete(BaseDeletePlugin):
            menu = {"label": "Restricted Delete", "icon": "lock", "order": 21}
            permission = "sample.delete_sample"

        # Should have permission attribute
        assert RestrictedDelete.permission == "sample.delete_sample"


class TestInheritancePatterns:
    """Test proper inheritance patterns with base classes."""

    def test_multiple_plugins_from_same_base(self):
        """Multiple plugins can inherit from the same base class."""

        @plugins.register(Sample)
        class Overview1(BaseOverviewPlugin):
            menu = {"label": "Overview 1", "icon": "o1", "order": 100}

        @plugins.register(Sample)
        class Overview2(BaseOverviewPlugin):
            menu = {"label": "Overview 2", "icon": "o2", "order": 101}

        # Both should be registered
        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [p.__name__ for p in registered_plugins]

        assert "Overview1" in plugin_names
        assert "Overview2" in plugin_names

    def test_base_classes_do_not_require_plugin_mixin(self):
        """Base plugin classes already include Plugin mixin."""

        # These should work without explicit Plugin inheritance
        @plugins.register(Sample)
        class SimpleOverview(BaseOverviewPlugin):
            menu = {"label": "Simple", "icon": "simple", "order": 200}

        # Should have Plugin methods
        assert hasattr(SimpleOverview, "get_urls")
        assert hasattr(SimpleOverview, "get_name")
        assert hasattr(SimpleOverview, "get_url_path")
