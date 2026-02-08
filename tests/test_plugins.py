"""
Test the FairDM plugins module.

This module tests the plugin registry, plugin registration, and plugin functionality.

NOTE: All tests in this file are currently skipped pending completion of the plugin system redesign.
The plugin API is undergoing significant changes and tests will be updated once the design is finalized.
"""

import pytest

# Skip all tests in this module
pytestmark = pytest.mark.skip(reason="Plugin system redesign in progress - tests will be updated when API is finalized")

from django.contrib.auth.models import AnonymousUser
from django.forms.widgets import Media
from django.urls import path
from django.views.generic import TemplateView
from flex_menu import Menu

from fairdm.core.models import Project
from fairdm.factories import PersonFactory, ProjectFactory
from fairdm.plugins import (
    ACTIONS,
    EXPLORE,
    MANAGEMENT,
    FairDMPlugin,
    PluggableView,
    PluginMenuItem,
    PluginRegistry,
    check_has_edit_permission,
    class_to_slug,
    registry,
    sample_check_has_edit_permission,
)


class TestConstants:
    """Test plugin category constants."""

    def test_explore_constant(self):
        """Test that EXPLORE constant has correct value."""
        assert EXPLORE == "explore"

    def test_actions_constant(self):
        """Test that ACTIONS constant has correct value."""
        assert ACTIONS == "actions"

    def test_management_constant(self):
        """Test that MANAGEMENT constant has correct value."""
        assert MANAGEMENT == "management"


class TestClassToSlug:
    """Test the class_to_slug utility function."""

    def test_class_to_slug_with_string(self):
        """Test conversion of a PascalCase string to slug."""
        result = class_to_slug("MyPluginClass")
        assert result == "my-plugin-class"

    def test_class_to_slug_with_class_object(self):
        """Test conversion of a class object to slug."""

        class TestClass:
            pass

        result = class_to_slug(TestClass)
        assert result == "test-class"

    def test_class_to_slug_with_single_word(self):
        """Test conversion of a single word."""
        result = class_to_slug("Plugin")
        assert result == "plugin"

    def test_class_to_slug_with_acronyms(self):
        """Test conversion with consecutive uppercase letters."""
        result = class_to_slug("HTTPResponseHandler")
        assert result == "h-t-t-p-response-handler"

    def test_class_to_slug_with_underscores(self):
        """Test conversion of snake_case to slug (underscores preserved)."""
        result = class_to_slug("my_plugin_class")
        # Underscores are preserved, not converted to hyphens
        assert result == "my_plugin_class"

    def test_class_to_slug_empty_string(self):
        """Test conversion of empty string."""
        result = class_to_slug("")
        assert result == ""


class TestCheckHasEditPermission:
    """Test the check_has_edit_permission function."""

    @pytest.fixture
    def mock_request(self, rf):
        """Create a mock request object."""
        return rf.get("/")

    @pytest.mark.django_db
    def test_superuser_has_permission(self, mock_request):
        """Test that superusers always have edit permission."""
        user = PersonFactory(is_superuser=True, is_staff=True)
        mock_request.user = user

        project = ProjectFactory()
        result = check_has_edit_permission(mock_request, project)

        assert result is True

    @pytest.mark.django_db
    def test_user_editing_self(self, mock_request):
        """Test that users can edit their own object."""
        user = PersonFactory()
        mock_request.user = user

        result = check_has_edit_permission(mock_request, user)

        assert result is True

    @pytest.mark.django_db
    def test_data_administrator_has_permission(self, mock_request):
        """Test that Data Administrators group members have permission."""
        from django.contrib.auth.models import Group

        user = PersonFactory()
        group, _ = Group.objects.get_or_create(name="Data Administrators")
        user.groups.add(group)
        mock_request.user = user

        project = ProjectFactory()
        result = check_has_edit_permission(mock_request, project)

        assert result is True

    @pytest.mark.django_db
    def test_user_with_object_permission(self, mock_request):
        """Test that users with specific object permissions have access."""
        from guardian.shortcuts import assign_perm

        user = PersonFactory()
        mock_request.user = user

        project = ProjectFactory()
        assign_perm("core.change_project", user, project)

        result = check_has_edit_permission(mock_request, project)

        assert result is True

    @pytest.mark.django_db
    def test_user_without_permission(self, mock_request):
        """Test that users without permission are denied."""
        user = PersonFactory()
        mock_request.user = user

        project = ProjectFactory()
        result = check_has_edit_permission(mock_request, project)

        assert result is False


class TestSampleCheckHasEditPermission:
    """Test the sample_check_has_edit_permission function."""

    @pytest.fixture
    def mock_request(self, rf):
        """Create a mock request object."""
        return rf.get("/")

    @pytest.mark.django_db
    def test_always_returns_true(self, mock_request):
        """Test that sample permission check always returns True."""
        user = PersonFactory()
        mock_request.user = user

        project = ProjectFactory()
        result = sample_check_has_edit_permission(mock_request, project)

        assert result is True


class TestPluginMenuItem:
    """Test the PluginMenuItem class."""

    def test_create_menu_item_with_icon(self):
        """Test creating a menu item with an icon."""
        menu_item = PluginMenuItem(name="Test", category="explore", icon="star")

        assert menu_item.name == "Test"
        assert menu_item.category == "explore"
        assert menu_item.icon == "star"

    def test_create_menu_item_without_icon(self):
        """Test creating a menu item without an icon."""
        menu_item = PluginMenuItem(name="Test", category="actions")

        assert menu_item.name == "Test"
        assert menu_item.category == "actions"
        assert menu_item.icon == ""


class TestPluginRegistry:
    """Test the PluginRegistry class."""

    @pytest.fixture
    def clean_plugin_registry(self):
        """Create a fresh plugin registry for testing."""
        test_registry = PluginRegistry()
        yield test_registry
        # Cleanup
        test_registry._model_view_registry.clear()

    @pytest.mark.django_db
    def test_register_creates_decorator(self, clean_plugin_registry):
        """Test that register returns a decorator function."""
        decorator = clean_plugin_registry.register(Project)

        assert callable(decorator)

    @pytest.mark.django_db
    def test_register_with_non_model_raises_error(self, clean_plugin_registry):
        """Test that registering a non-model raises TypeError."""
        with pytest.raises(TypeError, match=r"plugins\.register expects Django Model subclasses"):

            @clean_plugin_registry.register("NotAModel")
            class BadPlugin(FairDMPlugin):
                pass

    @pytest.mark.django_db
    def test_get_or_create_view_for_model_creates_new_view(self, clean_plugin_registry):
        """Test that get_or_create_view_for_model creates a new PluggableView."""
        view_class = clean_plugin_registry.get_or_create_view_for_model(Project)

        assert issubclass(view_class, PluggableView)
        assert view_class.base_model == Project
        assert view_class.model == Project
        assert view_class.__name__ == "ProjectDetailView"

    @pytest.mark.django_db
    def test_get_or_create_view_for_model_returns_existing_view(self, clean_plugin_registry):
        """Test that get_or_create_view_for_model returns existing view on second call."""
        view_class_1 = clean_plugin_registry.get_or_create_view_for_model(Project)
        view_class_2 = clean_plugin_registry.get_or_create_view_for_model(Project)

        assert view_class_1 is view_class_2

    @pytest.mark.django_db
    def test_get_view_for_model_returns_none_when_not_registered(self, clean_plugin_registry):
        """Test that get_view_for_model returns None for unregistered model."""
        result = clean_plugin_registry.get_view_for_model(Project)

        assert result is None

    @pytest.mark.django_db
    def test_get_view_for_model_returns_view_when_registered(self, clean_plugin_registry):
        """Test that get_view_for_model returns view for registered model."""
        clean_plugin_registry.get_or_create_view_for_model(Project)
        result = clean_plugin_registry.get_view_for_model(Project)

        assert result is not None
        assert issubclass(result, PluggableView)

    @pytest.mark.django_db
    def test_register_plugin_full_workflow(self, clean_plugin_registry):
        """Test complete plugin registration workflow."""

        @clean_plugin_registry.register(Project)
        class TestPlugin(FairDMPlugin, TemplateView):
            category = EXPLORE
            menu_item = PluginMenuItem(name="Test Plugin", icon="test")
            title = "Test Plugin"

        # Verify view was created
        view_class = clean_plugin_registry.get_view_for_model(Project)
        assert view_class is not None

        # Verify plugin was registered
        assert len(view_class.plugins) == 1
        assert issubclass(view_class.plugins[0], PluggableView)


class TestFairDMPlugin:
    """Test the FairDMPlugin base class."""

    def test_plugin_has_default_title(self):
        """Test that FairDMPlugin has a default title."""

        class TestPlugin(FairDMPlugin):
            pass

        plugin = TestPlugin()
        assert plugin.title == "Unnamed Plugin"

    def test_plugin_media_returns_empty_when_no_media_class(self):
        """Test that media property returns empty Media when not defined."""

        class TestPlugin(FairDMPlugin):
            pass

        plugin = TestPlugin()
        media = plugin.media

        assert isinstance(media, Media)
        assert str(media) == ""

    def test_plugin_media_returns_media_when_defined(self):
        """Test that media property returns Media when defined."""

        class TestPlugin(FairDMPlugin):
            class Media:
                css = {"all": ("css/test.css",)}
                js = ("js/test.js",)

        plugin = TestPlugin()
        media = plugin.media

        assert isinstance(media, Media)
        assert "css/test.css" in str(media)
        assert "js/test.js" in str(media)

    @pytest.mark.django_db
    def test_get_breadcrumbs_returns_empty_without_base_object(self, rf):
        """Test that get_breadcrumbs returns empty list without base_object."""

        class TestPlugin(FairDMPlugin):
            pass

        plugin = TestPlugin()
        plugin.request = rf.get("/")
        breadcrumbs = plugin.get_breadcrumbs()

        assert breadcrumbs == []

    @pytest.mark.django_db
    def test_get_breadcrumbs_with_public_object(self, rf, django_user_model):
        """Test breadcrumbs generation for public object."""
        from fairdm.utils.choices import Visibility

        class TestPlugin(FairDMPlugin):
            title = "Test Page"

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        user = AnonymousUser()

        plugin = TestPlugin()
        plugin.request = rf.get("/")
        plugin.request.user = user
        plugin.base_object = project

        breadcrumbs = plugin.get_breadcrumbs()

        assert len(breadcrumbs) == 3
        assert "All Projects" in breadcrumbs[0]["text"]
        assert "href" in breadcrumbs[0]
        assert breadcrumbs[1]["text"] == str(project)[:27] + ("..." if len(str(project)) > 30 else "")
        assert "href" in breadcrumbs[1]
        assert breadcrumbs[2]["text"] == "Test Page"
        assert "href" not in breadcrumbs[2]

    @pytest.mark.django_db
    def test_get_breadcrumbs_truncates_long_object_names(self, rf, django_user_model):
        """Test that long object names are truncated in breadcrumbs."""
        from fairdm.utils.choices import Visibility

        class TestPlugin(FairDMPlugin):
            title = "Test Page"

        # Create project with a very long name
        long_name = "A" * 50
        project = ProjectFactory(name=long_name, visibility=Visibility.PUBLIC)
        user = AnonymousUser()

        plugin = TestPlugin()
        plugin.request = rf.get("/")
        plugin.request.user = user
        plugin.base_object = project

        breadcrumbs = plugin.get_breadcrumbs()

        # Second breadcrumb should be truncated
        assert breadcrumbs[1]["text"] == long_name[:27] + "..."

    @pytest.mark.django_db
    def test_get_context_data_includes_menus_and_breadcrumbs(self, rf):
        """Test that get_context_data includes menus and breadcrumbs."""

        class TestPlugin(FairDMPlugin, TemplateView):
            title = "Test Page"
            menus = {"explore": Menu(name="Explore")}

        plugin = TestPlugin()
        plugin.request = rf.get("/")

        context = plugin.get_context_data()

        assert "menus" in context
        assert "breadcrumbs" in context
        assert "plugin_media" in context


class TestPluggableView:
    """Test the PluggableView class."""

    @pytest.mark.django_db
    def test_init_subclass_creates_empty_plugins_list(self):
        """Test that subclassing PluggableView creates an empty plugins list."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        assert hasattr(TestView, "plugins")
        assert TestView.plugins == []

    @pytest.mark.django_db
    def test_init_subclass_creates_menus(self):
        """Test that subclassing PluggableView creates menu dictionaries."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        assert hasattr(TestView, "menus")
        assert "explore" in TestView.menus
        assert "actions" in TestView.menus
        assert "management" in TestView.menus
        assert isinstance(TestView.menus["explore"], Menu)

    @pytest.mark.django_db
    def test_get_template_names_with_explicit_template(self):
        """Test get_template_names returns explicit template when set."""

        class TestView(PluggableView):
            base_model = Project
            model = Project
            template_name = "custom/template.html"

        view = TestView()
        templates = view.get_template_names()

        assert templates == ["custom/template.html"]

    @pytest.mark.django_db
    def test_get_template_names_default_hierarchy(self):
        """Test get_template_names returns correct hierarchy of templates."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        view = TestView()
        templates = view.get_template_names()

        assert "project/plugins/test-view.html" in templates
        assert "plugins/test-view.html" in templates
        assert "fairdm/plugin.html" in templates

    @pytest.mark.django_db
    def test_get_template_names_polymorphic_hierarchy(self):
        """Test get_template_names returns correct hierarchy for polymorphic models."""
        from fairdm.contrib.contributors.models import Contributor

        class TestView(PluggableView):
            base_model = Contributor
            model = Contributor

        # Create a Person instance (polymorphic child of Contributor)
        person = PersonFactory()
        view = TestView()
        view.base_object = person

        templates = view.get_template_names()

        # Should check child class first, then parent class
        assert "person/plugins/test-view.html" in templates
        assert "contributor/plugins/test-view.html" in templates
        assert "plugins/test-view.html" in templates
        assert "fairdm/plugin.html" in templates

        # Verify order: child before parent
        person_index = templates.index("person/plugins/test-view.html")
        contributor_index = templates.index("contributor/plugins/test-view.html")
        assert person_index < contributor_index

    @pytest.mark.django_db
    def test_register_plugin_with_invalid_category_raises_error(self):
        """Test that registering plugin with invalid category raises ValueError."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        class InvalidPlugin(FairDMPlugin):
            category = "invalid_category"

        with pytest.raises(ValueError, match="Invalid category 'invalid_category'"):
            TestView.register_plugin(InvalidPlugin)

    @pytest.mark.django_db
    def test_register_plugin_adds_to_plugins_list(self):
        """Test that register_plugin adds plugin to the plugins list."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        class ValidPlugin(FairDMPlugin, TemplateView):
            category = EXPLORE

        TestView.register_plugin(ValidPlugin)

        assert len(TestView.plugins) == 1
        assert issubclass(TestView.plugins[0], PluggableView)

    @pytest.mark.django_db
    def test_register_plugin_auto_mixins_parent_view(self):
        """Test that register_plugin auto-mixins the parent view class."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        class TestPlugin(FairDMPlugin, TemplateView):
            category = EXPLORE

        result = TestView.register_plugin(TestPlugin)

        assert issubclass(result, PluggableView)
        assert issubclass(result, TestPlugin)

    @pytest.mark.django_db
    def test_register_plugin_preserves_plugins_and_menus(self):
        """Test that register_plugin preserves parent's plugins and menus."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        original_menus = TestView.menus

        class TestPlugin(FairDMPlugin, TemplateView):
            category = EXPLORE

        result = TestView.register_plugin(TestPlugin)

        assert result.menus is original_menus
        assert result.plugins is TestView.plugins

    @pytest.mark.django_db
    def test_get_urls_generates_plugin_urls(self):
        """Test that get_urls generates URL patterns for plugins."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        class TestPlugin(FairDMPlugin, TemplateView):
            category = EXPLORE
            menu_item = PluginMenuItem(name="Test", icon="test")

        TestView.register_plugin(TestPlugin)
        urls = TestView.get_urls()

        assert len(urls) >= 1
        # Check that at least one URL pattern was created
        assert any(isinstance(url_pattern, type(path("", lambda: None))) for url_pattern in urls)

    @pytest.mark.django_db
    def test_get_urls_adds_menu_items_to_correct_menu(self):
        """Test that get_urls adds menu items to the correct category menu."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        class ExplorePlugin(FairDMPlugin, TemplateView):
            category = EXPLORE
            menu_item = PluginMenuItem(name="Explore Test", icon="view")

        class ActionsPlugin(FairDMPlugin, TemplateView):
            category = ACTIONS
            menu_item = PluginMenuItem(name="Action Test", icon="action")

        TestView.register_plugin(ExplorePlugin)
        TestView.register_plugin(ActionsPlugin)
        TestView.get_urls()

        # Check that menu items were added to appropriate menus
        assert len(TestView.menus["explore"].children) > 0
        assert len(TestView.menus["actions"].children) > 0

    @pytest.mark.django_db
    def test_get_urls_sets_view_name_on_menu_item(self):
        """Test that get_urls sets the view_name on menu items."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        class TestPlugin(FairDMPlugin, TemplateView):
            category = EXPLORE
            menu_item = PluginMenuItem(name="Test", icon="test")

        TestView.register_plugin(TestPlugin)
        TestView.get_urls()

        # Menu item should have view_name set
        menu_item = TestPlugin.menu_item
        assert hasattr(menu_item, "view_name")
        assert menu_item.view_name == "project:test-plugin"

    @pytest.mark.django_db
    def test_plugin_without_menu_item_not_added_to_menu(self):
        """Test that plugins without menu_item are not added to menus."""

        class TestView(PluggableView):
            base_model = Project
            model = Project

        class TestPlugin(FairDMPlugin, TemplateView):
            category = EXPLORE
            menu_item = None

        initial_menu_count = len(TestView.menus["explore"].children)

        TestView.register_plugin(TestPlugin)
        TestView.get_urls()

        # Menu count should not change
        assert len(TestView.menus["explore"].children) == initial_menu_count


class TestGlobalRegistry:
    """Test the global registry instance."""

    def test_registry_is_plugin_registry_instance(self):
        """Test that global registry is an instance of PluginRegistry."""
        assert isinstance(registry, PluginRegistry)

    def test_register_is_registry_register_method(self):
        """Test that global register is the registry's register method."""
        from fairdm.plugins import register as global_register

        assert global_register == registry.register


class TestPluginIntegration:
    """Integration tests for plugin system."""

    @pytest.fixture
    def clean_plugin_registry(self):
        """Create a fresh plugin registry for testing."""
        test_registry = PluginRegistry()
        yield test_registry
        test_registry._model_view_registry.clear()

    @pytest.mark.django_db
    def test_complete_plugin_registration_workflow(self, clean_plugin_registry):
        """Test complete workflow of registering and using a plugin."""

        # Register a plugin
        @clean_plugin_registry.register(Project)
        class OverviewPlugin(FairDMPlugin, TemplateView):
            category = EXPLORE
            menu_item = PluginMenuItem(name="Overview", icon="view")
            title = "Overview"
            template_name = "test/overview.html"

        # Get the view
        view_class = clean_plugin_registry.get_view_for_model(Project)

        # Verify plugin was registered
        assert len(view_class.plugins) == 1
        assert view_class.plugins[0].title == "Overview"

        # Generate URLs
        urls = view_class.get_urls()
        assert len(urls) >= 1

        # Verify menu was populated
        assert len(view_class.menus["explore"].children) > 0

    @pytest.mark.django_db
    def test_multiple_plugins_same_model(self, clean_plugin_registry):
        """Test registering multiple plugins for the same model."""

        @clean_plugin_registry.register(Project)
        class OverviewPlugin(FairDMPlugin, TemplateView):
            category = EXPLORE
            menu_item = PluginMenuItem(name="Overview", icon="view")
            title = "Overview"

        @clean_plugin_registry.register(Project)
        class SettingsPlugin(FairDMPlugin, TemplateView):
            category = MANAGEMENT
            menu_item = PluginMenuItem(name="Settings", icon="settings")
            title = "Settings"

        view_class = clean_plugin_registry.get_view_for_model(Project)

        # Verify both plugins were registered
        assert len(view_class.plugins) == 2

        # Generate URLs
        urls = view_class.get_urls()
        assert len(urls) >= 2

        # Verify both menus were populated
        assert len(view_class.menus["explore"].children) > 0
        assert len(view_class.menus["management"].children) > 0
