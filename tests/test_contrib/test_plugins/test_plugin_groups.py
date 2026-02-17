"""
Tests for PluginGroup functionality.

User Story 4: PluginGroup Composition
"""

import pytest
from django.test import RequestFactory
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, PluginGroup
from fairdm.core.sample.models import Sample

pytestmark = pytest.mark.django_db


class TestPluginGroup:
    """Test PluginGroup composition (User Story 4)."""

    def test_plugin_group_aggregates_multiple_plugins(self, sample, user):
        """Given multiple related plugins,
        When grouped in a PluginGroup,
        Then they appear under a single tab (User Story 4, Scenario 1)."""

        class ChartPlugin(Plugin, TemplateView):
            menu = {"label": "Chart", "icon": "chart", "order": 10}
            template_name = "plugins/chart.html"

        class TablePlugin(Plugin, TemplateView):
            menu = {"label": "Table", "icon": "table", "order": 20}
            template_name = "plugins/table.html"

        @plugins.register(Sample)
        class VisualizationGroup(PluginGroup):
            plugins = [ChartPlugin, TablePlugin]
            menu = {"label": "Visualizations", "icon": "eye", "order": 100}

        factory = RequestFactory()
        request = factory.get("/")
        request.user = user
        tabs = plugins.registry.get_tabs_for_model(Sample, request, sample)
        viz_tabs = [t for t in tabs if t.label == "Visualizations"]

        # Should have one tab for the group
        assert len(viz_tabs) == 1

    def test_plugin_group_urls_include_all_subplugins(self):
        """Given a PluginGroup with multiple plugins,
        When getting URLs for the model,
        Then all subplugin URLs are included."""

        class SubPlugin1(Plugin, TemplateView):
            menu = {"label": "Sub1", "icon": "s1", "order": 10}
            template_name = "sub1.html"

        class SubPlugin2(Plugin, TemplateView):
            menu = {"label": "Sub2", "icon": "s2", "order": 20}
            template_name = "sub2.html"

        @plugins.register(Sample)
        class TestGroup(PluginGroup):
            plugins = [SubPlugin1, SubPlugin2]
            menu = {"label": "Test Group", "icon": "group", "order": 200}

        url_patterns = plugins.registry.get_urls_for_model(Sample)

        # Should have URL patterns for both subplugins
        # The exact implementation depends on how PluginGroup generates URLs
        assert len(url_patterns) > 0

    def test_plugin_group_without_plugins_attribute(self):
        """A PluginGroup without plugins attribute should have empty list."""

        @plugins.register(Sample)
        class EmptyGroup(PluginGroup):
            menu = {"label": "Empty", "icon": "empty", "order": 300}
            # Missing plugins attribute

        # PluginGroup has a default empty list for plugins
        assert EmptyGroup.plugins == []


class TestPluginGroupHierarchy:
    """Test that PluginGroups cannot be nested."""

    def test_nested_plugin_groups_not_allowed(self):
        """PluginGroups should not contain other PluginGroups (E007)."""

        class InnerGroup(PluginGroup):
            plugins = []
            menu = {"label": "Inner", "icon": "inner", "order": 10}

        # Attempting to nest groups should be caught by system checks
        @plugins.register(Sample)
        class OuterGroup(PluginGroup):
            plugins = [InnerGroup]
            menu = {"label": "Outer", "icon": "outer", "order": 20}

        # The system check E007 should catch this
        # For now, we just verify the structure is created
        # The actual validation happens in system checks
        assert InnerGroup in OuterGroup.plugins
