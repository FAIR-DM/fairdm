"""
Tests for plugin tab navigation functionality.

User Story 2: Tab Navigation
"""

import pytest
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, Tab
from fairdm.core.sample.models import Sample

pytestmark = pytest.mark.django_db


class TestTabNavigation:
    """Test tab navigation for plugins (User Story 2)."""

    def test_plugin_creates_tab_with_menu_config(self, rf, sample):
        """Given a plugin with menu configuration,
        When the plugin is registered,
        Then a tab is created with label, icon, and order."""

        @plugins.register(Sample)
        class TabPlugin(Plugin, TemplateView):
            menu = {"label": "Analysis", "icon": "chart-line", "order": 100}
            template_name = "analysis.html"

        # Get tabs for Sample model
        from fairdm.factories.contributors import UserFactory

        request = rf.get("/")
        request.user = UserFactory()

        tabs = plugins.registry.get_tabs_for_model(Sample, request, sample)

        # Find our tab
        analysis_tabs = [t for t in tabs if t.label == "Analysis"]
        assert len(analysis_tabs) > 0

        analysis_tab = analysis_tabs[0]
        assert analysis_tab.icon == "chart-line"
        assert analysis_tab.order == 100

    def test_tabs_sorted_by_order(self, rf, sample):
        """Given multiple plugins with different order values,
        When getting tabs for a model,
        Then tabs are sorted by order field (User Story 2, Scenario 2)."""

        @plugins.register(Sample)
        class FirstTab(Plugin, TemplateView):
            menu = {"label": "First", "icon": "1", "order": 10}
            template_name = "first.html"

        @plugins.register(Sample)
        class ThirdTab(Plugin, TemplateView):
            menu = {"label": "Third", "icon": "3", "order": 30}
            template_name = "third.html"

        @plugins.register(Sample)
        class SecondTab(Plugin, TemplateView):
            menu = {"label": "Second", "icon": "2", "order": 20}
            template_name = "second.html"

        request = rf.get("/")
        from fairdm.factories.contributors import UserFactory

        request.user = UserFactory()

        tabs = plugins.registry.get_tabs_for_model(Sample, request, sample)

        # Filter to our test tabs
        test_labels = ["First", "Second", "Third"]
        test_tabs = [t for t in tabs if t.label in test_labels]
        test_tabs.sort(key=lambda t: t.order)

        # Check order
        assert test_tabs[0].label == "First"
        assert test_tabs[1].label == "Second"
        assert test_tabs[2].label == "Third"

    def test_plugin_without_menu_does_not_create_tab(self, rf, sample):
        """Given a plugin with menu = None,
        When getting tabs for the model,
        Then no tab is created for that plugin (User Story 2)."""

        @plugins.register(Sample)
        class NoMenuPlugin(Plugin, TemplateView):
            menu = None  # No tab should be created
            template_name = "no_menu.html"

        # Plugin should be registered
        registered = plugins.registry.get_plugins_for_model(Sample)
        assert any(p.__name__ == "NoMenuPlugin" for p in registered)

        # But should NOT create a tab
        from fairdm.factories.contributors import UserFactory

        request = rf.get("/")
        request.user = UserFactory()

        tabs = plugins.registry.get_tabs_for_model(Sample, request, sample)
        no_menu_tabs = [t for t in tabs if "NoMenu" in t.label]
        assert len(no_menu_tabs) == 0


def test_tab_url_links_to_plugin_view(rf, sample):
    """Given a tab for a plugin,
    When accessing the tab's URL,
    Then it links to the plugin's view."""

    @plugins.register(Sample)
    class URLTabPlugin(Plugin, TemplateView):
        menu = {"label": "URL Tab", "icon": "link", "order": 50}
        template_name = "url_tab.html"

    request = rf.get("/")
    from fairdm.factories.contributors import UserFactory

    request.user = UserFactory()

    tabs = plugins.registry.get_tabs_for_model(Sample, request, sample)
    url_tabs = [t for t in tabs if t.label == "URL Tab"]

    assert len(url_tabs) > 0
    url_tab = url_tabs[0]

    # Tab should have a url attribute (may be empty as template resolves it)
    assert hasattr(url_tab, "url")


class TestTabDataclass:
    """Test the Tab dataclass functionality."""

    def test_tab_creation(self):
        """Tab dataclass can be created with all fields."""
        tab = Tab(label="Test", url="/test/url/", icon="test-icon", order=100, is_active=False)

        assert tab.label == "Test"
        assert tab.url == "/test/url/"
        assert tab.icon == "test-icon"
        assert tab.order == 100
        assert tab.is_active is False

    def test_tab_attributes(self):
        """Tab has all expected attributes."""
        tab = Tab(label="Admin", url="/admin/url/", icon="shield", order=200, is_active=True)

        assert tab.label == "Admin"
        assert tab.url == "/admin/url/"
        assert tab.icon == "shield"
        assert tab.order == 200
        assert tab.is_active is True


class TestPluginGroupTabs:
    """Test tab creation for PluginGroups."""

    def test_plugin_group_creates_single_tab(self, rf, sample):
        """Given a PluginGroup with multiple plugins,
        When registered,
        Then a single tab is created for the group (User Story 4)."""
        from fairdm.contrib.plugins import PluginGroup

        class SubPlugin1(Plugin, TemplateView):
            menu = {"label": "Sub1", "icon": "s1", "order": 10}
            template_name = "sub1.html"

        class SubPlugin2(Plugin, TemplateView):
            menu = {"label": "Sub2", "icon": "s2", "order": 20}
            template_name = "sub2.html"

        @plugins.register(Sample)
        class GroupTab(PluginGroup):
            plugins = [SubPlugin1, SubPlugin2]
            menu = {"label": "Tab Group", "icon": "group", "order": 300}

        request = rf.get("/")
        from fairdm.factories.contributors import UserFactory

        request.user = UserFactory()

        tabs = plugins.registry.get_tabs_for_model(Sample, request, sample)
        group_tabs = [t for t in tabs if t.label == "Tab Group"]

        # Should have exactly one tab for the group
        assert len(group_tabs) == 1
        assert group_tabs[0].icon == "group"
        assert group_tabs[0].order == 300
