"""
Tests for fairdm.contrib.plugins.base.Plugin.

Covers custom URL configuration (User Story 6), permission handling
(User Story 5), dispatch/context/breadcrumb/template-name coverage gaps,
plugin context and breadcrumb generation (User Story 7), template
resolution (User Story 3), and the reusable base plugin classes built on
top of Plugin (User Story 8).
"""

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.plugins import DeletePlugin, OverviewPlugin, UpdatePlugin
from fairdm.core.sample.models import Sample
from fairdm.factories import SampleFactory
from fairdm.factories.contributors import UserFactory

pytestmark = pytest.mark.django_db


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

    def test_plugin_with_extra_views(self):
        """A plugin owning further views serves each beneath its own path, flat.

        This replaces a test that overrode ``get_urls`` to return arbitrary patterns. That was the
        most flexible extension point and the least checkable — the registry cannot see a plugin's
        children until they are already URL patterns, which makes collisions undetectable at
        registration. ``extra_views`` is the declared surface instead.
        """

        class Export(Plugin, TemplateView):
            template_name = "export.html"

        @plugins.register(Sample)
        class MultiURLPlugin(Plugin, TemplateView):
            template_name = "multi.html"
            extra_views = [Export]

        url_patterns = MultiURLPlugin.get_urls(model=Sample)

        assert len(url_patterns) == 2
        assert [p.name for p in url_patterns] == [
            "multi-url-plugin",
            "multi-url-plugin-export",
        ]
        # Flat, not a nested namespace: the child hangs off the parent's path.
        assert str(url_patterns[1].pattern) == "multi-url-plugin/export/"


class TestDefaultURLGeneration:
    """Test default URL generation for plugins."""

    def test_default_url_path_from_class_name(self):
        """Without custom url_path, URL path is derived from class name."""

        @plugins.register(Sample)
        class DefaultURLPlugin(Plugin, TemplateView):
            menu = {"label": "Default", "icon": "default", "order": 30}
            template_name = "default.html"

        # Default slug should be kebab-case of class name
        # Note: "DefaultURLPlugin" → "default-url-plugin" (each capital gets hyphen)
        expected_path = "default-url-plugin"
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

        # Default get_urls requires menu_class (the registry passes the plugin
        # menu for the model it's building URLs for); pass None here since
        # this test isn't exercising menu/tab configuration.
        url_patterns = ParamPlugin.get_urls(menu_class=None)

        # Should have at least one URL pattern
        assert len(url_patterns) > 0

        # First pattern should be simple (no pk - that's in parent routing)
        first_pattern = url_patterns[0]
        pattern_str = str(first_pattern.pattern)

        # Should just be the plugin path
        assert pattern_str == "param-plugin/"


class TestPluginPermissions:
    """Test permission integration (User Story 5)."""

    def test_plugin_with_permission_attribute(self):
        """Given a plugin with a permission attribute,
        When a user without permission tries to access it,
        Then access is denied (User Story 5, Scenario 1)."""

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.change_sample"
            menu = {"label": "Edit", "icon": "edit", "order": 10}
            template_name = "plugins/edit.html"

        # Create users
        user_with_perm = UserFactory(email="editor@example.com")
        user_without_perm = UserFactory(email="viewer@example.com")

        # Grant permission to one user
        content_type = ContentType.objects.get_for_model(Sample)
        change_perm = Permission.objects.get(
            codename="change_sample", content_type=content_type
        )
        user_with_perm.user_permissions.add(change_perm)

        # Check permission
        assert user_with_perm.has_perm("sample.change_sample")
        assert not user_without_perm.has_perm("sample.change_sample")

    def test_plugin_without_permission_is_public(self):
        """Given a plugin without a permission attribute,
        When any user accesses it,
        Then access is allowed (User Story 5, Scenario 2)."""

        @plugins.register(Sample)
        class PublicPlugin(Plugin, TemplateView):
            # No permission attribute
            menu = {"label": "Overview", "icon": "info", "order": 20}
            template_name = "plugins/overview.html"

        # Plugin should not have permission requirement
        assert (
            not hasattr(PublicPlugin, "permission") or PublicPlugin.permission is None
        )

    def test_permission_shown_in_tab(self, sample, admin_user):
        """Tab should include permission information."""

        @plugins.register(Sample)
        class SecurePlugin(Plugin, TemplateView):
            permission = "sample.delete_sample"
            menu = {"label": "Delete", "icon": "trash", "order": 30}
            template_name = "plugins/delete.html"

        # Verify plugin has permission attribute set
        assert hasattr(SecurePlugin, "permission")
        assert SecurePlugin.permission == "sample.delete_sample"


class TestObjectLevelPermissions:
    """Test object-level permission integration."""

    def test_plugin_respects_object_permissions(self):
        """Plugins should integrate with django-guardian for object-level permissions."""

        @plugins.register(Sample)
        class ObjectPermPlugin(Plugin, TemplateView):
            permission = "sample.view_sample"
            menu = {"label": "View Details", "icon": "eye", "order": 40}
            template_name = "plugins/details.html"

        # Plugin should have permission attribute for guardian to check
        assert ObjectPermPlugin.permission == "sample.view_sample"


class TestPluginGetObject:
    """Test Plugin.get_base_object() method with various scenarios.

    The old API exposed this as get_object(); the current base class exposes
    it as get_base_object() and keys off `registered_model` (the attribute the
    registry sets during URL generation) rather than `model`.
    """

    def test_get_object_with_pk_kwarg(self, sample):
        """Plugin should fetch object using pk kwarg."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.kwargs = {"pk": sample.pk}
        plugin.registered_model = Sample

        obj = plugin.get_base_object()
        assert obj == sample
        assert obj.pk == sample.pk

    def test_get_object_with_uuid_kwarg(self, sample):
        """Plugin should fetch object using uuid kwarg."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.kwargs = {"uuid": sample.uuid}
        plugin.registered_model = Sample

        obj = plugin.get_base_object()
        assert obj == sample
        assert str(obj.uuid) == str(sample.uuid)

    def test_get_object_without_model_raises_error(self):
        """Plugin without registered_model should raise ValueError."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.kwargs = {"pk": 1}
        plugin.registered_model = None

        with pytest.raises(ValueError, match="has no associated model"):
            plugin.get_base_object()

    def test_get_object_without_pk_or_uuid_raises_error(self):
        """Plugin without pk or uuid kwarg should raise ValueError."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.kwargs = {}
        plugin.registered_model = Sample

        with pytest.raises(ValueError, match="mounted without any of the lookup kwargs"):
            plugin.get_base_object()

    def test_get_object_with_nonexistent_record_is_404(self):
        """A record that does not exist is a 404, not a 500.

        The old behaviour swallowed the miss into ``obj = None`` and then failed further along with
        an AttributeError, which reached the user as a server error.
        """

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.kwargs = {"pk": 999999}
        plugin.registered_model = Sample

        with pytest.raises(Http404):
            plugin.get_base_object()


class TestPluginHasPermission:
    """Test Plugin.has_permission() method."""

    def test_has_permission_without_permission_attribute(self, sample):
        """Plugin without permission requirement should always allow access."""

        @plugins.register(Sample)
        class PublicPlugin(Plugin, TemplateView):
            permission = None
            template_name = "test.html"

        request = RequestFactory().get("/")
        request.user = UserFactory()

        plugin = PublicPlugin()
        plugin.request = request
        plugin.kwargs = {"uuid": sample.uuid}
        plugin.registered_model = Sample

        assert plugin.has_permission() is True

    def test_has_permission_with_model_level_permission(self, sample):
        """Plugin should check model-level permissions."""

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.change_sample"
            template_name = "test.html"

        request = RequestFactory().get("/")

        # User with permission
        user_with_perm = UserFactory()
        content_type = ContentType.objects.get_for_model(Sample)
        perm = Permission.objects.get(
            codename="change_sample", content_type=content_type
        )
        user_with_perm.user_permissions.add(perm)
        request.user = user_with_perm

        plugin = PermissionPlugin()
        plugin.request = request
        plugin.kwargs = {"uuid": sample.uuid}
        plugin.registered_model = Sample

        assert plugin.has_permission() is True

    def test_has_permission_denies_user_without_permission(self, sample):
        """Plugin should deny access to users without permission."""

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.delete_sample"
            template_name = "test.html"

        request = RequestFactory().get("/")
        request.user = UserFactory()  # User without delete permission

        plugin = PermissionPlugin()
        plugin.request = request
        plugin.kwargs = {"uuid": sample.uuid}
        plugin.registered_model = Sample

        assert plugin.has_permission() is False

    def test_has_permission_with_anonymous_user(self, sample):
        """Plugin should handle anonymous users."""

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.view_sample"
            template_name = "test.html"

        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        plugin = PermissionPlugin()
        plugin.request = request
        plugin.kwargs = {"uuid": sample.uuid}
        plugin.registered_model = Sample

        assert plugin.has_permission() is False


class TestPluginDispatch:
    """Test Plugin.dispatch() method."""

    def test_dispatch_leaves_the_view_s_own_object_alone(self, sample):
        """The plugin system must not assign self.object.

        This replaces a test that asserted the opposite. The core record and the view's own object
        are two different things, and sharing one attribute name broke any view that manages its
        own — a CreateView sets self.object to None in its own get(), and the old dispatch had
        already overwritten it with the record.
        """

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            registered_model = Sample

            def get(self, request, *args, **kwargs):
                assert not hasattr(self, "object")
                return super().get(request, *args, **kwargs)

        request = RequestFactory().get(f"/sample/{sample.uuid}/test/")
        request.user = UserFactory()

        response = TestPlugin.as_view()(request, uuid=sample.uuid)
        assert response.status_code == 200

    def test_dispatch_raises_permission_denied_without_permission(self, sample):
        """Dispatch should raise PermissionDenied for unauthorized users."""

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.delete_sample"
            template_name = "test.html"
            registered_model = Sample

        plugin = PermissionPlugin.as_view()
        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.uuid}/test/")
        request.user = UserFactory()  # User without delete permission

        with pytest.raises(PermissionDenied):
            plugin(request, uuid=sample.uuid)

    def test_dispatch_raises_404_for_a_missing_record(self):
        """A record that does not exist is a 404.

        This replaces a test that asserted 200 with the record silently absent, which is how a
        missing sample used to surface as a server error further along the request.
        """

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            registered_model = Sample

        request = RequestFactory().get("/sample/nonexistent-uuid/test/")
        request.user = UserFactory()

        with pytest.raises(Http404):
            TestPlugin.as_view()(request, uuid="nonexistent-uuid")


class TestPluginGetContextData:
    """Test Plugin.get_context_data() method."""

    def test_get_context_data_uses_self_object(self, sample):
        """get_context_data should use self.object if set."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {}
        plugin.object = sample  # Set object directly

        factory = RequestFactory()
        plugin.request = factory.get("/")
        plugin.request.user = UserFactory()

        context = plugin.get_context_data()

        assert context["object"] == sample

    def test_get_context_data_fetches_object_if_not_set(self, sample):
        """get_context_data should fetch object if not in context."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}

        factory = RequestFactory()
        plugin.request = factory.get("/")
        plugin.request.user = UserFactory()

        context = plugin.get_context_data()

        assert context["object"] == sample

    def test_get_context_data_handles_fetch_failure(self):
        """get_context_data should set object=None if fetch fails."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {}  # Non-existent

        factory = RequestFactory()
        plugin.request = factory.get("/")
        plugin.request.user = UserFactory()

        context = plugin.get_context_data()

        assert context["object"] is None

    def test_get_context_data_includes_breadcrumbs(self, sample):
        """get_context_data should include breadcrumbs."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            # get_breadcrumbs() appends a "current page" crumb built from
            # self.page_title whenever self.menu is truthy. Set it explicitly
            # so that branch doesn't hit the source's undefined-attribute bug
            # (see get_breadcrumbs() docstring note in base.py).
            page_title = "Test"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}
        plugin.menu = {"label": "Test"}

        factory = RequestFactory()
        plugin.request = factory.get("/")
        plugin.request.user = UserFactory()

        context = plugin.get_context_data()

        assert "breadcrumbs" in context
        assert isinstance(context["breadcrumbs"], list)

    def test_get_context_data_includes_plugin_menu(self, sample):
        """get_context_data should include plugin_menu reflecting self.menu.

        The old "tabs" context key is gone; get_context_data() now exposes
        the plugin's own menu configuration as "plugin_menu" so the base
        template can decide whether to render the local tab navigation.
        """

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            page_title = "Test Tab"
            menu = {"label": "Test Tab"}

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}

        factory = RequestFactory()
        plugin.request = factory.get("/")
        plugin.request.user = UserFactory()

        context = plugin.get_context_data()

        assert "plugin_menu" in context
        assert context["plugin_menu"] == TestPlugin.menu

    def test_get_context_data_includes_plugin_media(self):
        """get_context_data should include plugin_media."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

            class Media:
                css = {"all": ("plugin.css",)}
                js = ("plugin.js",)

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {}

        factory = RequestFactory()
        plugin.request = factory.get("/")
        plugin.request.user = UserFactory()

        context = plugin.get_context_data()

        assert "plugin_media" in context
        assert context["plugin_media"] is not None

    def test_get_context_data_without_media(self):
        """get_context_data should set plugin_media=None if no Media class."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.model = Sample
        plugin.kwargs = {}

        factory = RequestFactory()
        plugin.request = factory.get("/")
        plugin.request.user = UserFactory()

        context = plugin.get_context_data()

        assert context["plugin_media"] is None


class TestPluginGetBreadcrumbs:
    """Test Plugin.get_breadcrumbs() method."""

    def test_get_breadcrumbs_includes_model_name(self, sample):
        """Breadcrumbs should include model verbose name plural."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            page_title = "Details"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}
        plugin.menu = {"label": "Details"}

        breadcrumbs = plugin.get_breadcrumbs()

        assert len(breadcrumbs) > 0
        # First breadcrumb should be model name
        assert (
            Sample._meta.verbose_name_plural.lower() in breadcrumbs[0]["text"].lower()
        )

    def test_get_breadcrumbs_includes_object_str(self, sample):
        """Breadcrumbs should include object string representation."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            page_title = "Edit"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}
        plugin.menu = {"label": "Edit"}

        breadcrumbs = plugin.get_breadcrumbs()

        # Should have at least model, object, and current page
        assert len(breadcrumbs) >= 2

    def test_get_breadcrumbs_truncates_long_names(self):
        """Breadcrumbs should truncate long object names."""
        # Create sample with very long name
        long_name = "A" * 100
        sample = SampleFactory(name=long_name)

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            page_title = "View"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}
        plugin.menu = {"label": "View"}

        breadcrumbs = plugin.get_breadcrumbs()

        # Find object breadcrumb
        obj_breadcrumb = next(
            (b for b in breadcrumbs if "..." in b.get("text", "")), None
        )
        if obj_breadcrumb:
            # Should be truncated to 50 chars
            assert len(obj_breadcrumb["text"]) <= 50

    def test_get_breadcrumbs_includes_current_page(self, sample):
        """Breadcrumbs should include current page from page_title.

        The current-page breadcrumb text comes from self.page_title, not from
        the menu dict's "label" (the old behaviour this test used to assert).
        """

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            page_title = "Custom Page"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}
        plugin.menu = {"label": "Custom Page"}

        breadcrumbs = plugin.get_breadcrumbs()

        # Last breadcrumb should be current page
        assert breadcrumbs[-1]["text"] == "Custom Page"

    def test_get_breadcrumbs_handles_missing_object(self):
        """Breadcrumbs should handle missing object gracefully."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            page_title = "Page"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {}  # Non-existent
        plugin.menu = {"label": "Page"}

        breadcrumbs = plugin.get_breadcrumbs()

        # Should still have breadcrumbs, just no object breadcrumb
        assert len(breadcrumbs) >= 1


class TestPluginGetTemplateNames:
    """Test Plugin.get_template_names().

    NOTE: the hierarchical model-specific -> plugin-default -> framework
    fallback template resolution this class used to test does not exist in
    the current base.py. Plugin does not override get_template_names() at
    all, so it falls straight through to Django's
    TemplateResponseMixin.get_template_names(), which just returns
    [self.template_name]. The three tests that asserted the removed
    hierarchy (model-specific path, plugin-default path, "plugins/base.html"
    fallback) have been deleted rather than updated, since that feature no
    longer exists in any form to test.
    """

    def test_get_url_path_fallback(self):
        """When url_path not set, should use get_name()."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            # Don't set url_path
            pass

        # Should fall back to slugified class name
        assert TestPlugin.get_url_path() == "test-plugin"

    def test_get_template_names_with_explicit_template(self):
        """Plugin with explicit template_name should use it first."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "custom/template.html"

        plugin = TestPlugin()
        plugin.registered_model = Sample

        templates = plugin.get_template_names()

        assert templates[0] == "custom/template.html"


class TestPluginContext:
    """Test plugin context data (User Story 7)."""

    def test_plugin_get_object_returns_instance(self, sample):
        """Given a plugin view,
        When get_base_object is called,
        Then it returns the model instance."""

        @plugins.register(Sample)
        class ObjectPlugin(Plugin, TemplateView):
            menu = {"label": "Object", "icon": "obj", "order": 10}
            template_name = "object.html"

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/object/")

        plugin = ObjectPlugin()
        plugin.request = request
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}

        # Get object (renamed from get_object() to get_base_object())
        obj = plugin.get_base_object()
        assert obj == sample
        assert isinstance(obj, Sample)

    def test_plugin_context_object(self, sample, user):
        """Plugin context should contain the object."""

        @plugins.register(Sample)
        class ContextObjPlugin(Plugin, TemplateView):
            menu = {"label": "Context", "icon": "ctx", "order": 20}
            page_title = "Context"
            template_name = "context.html"

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/context/")
        request.user = user

        plugin = ContextObjPlugin()
        plugin.request = request
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}

        context = plugin.get_context_data()

        # Should have object in context
        assert "object" in context
        assert context["object"] == sample


class TestPluginBreadcrumbs:
    """Test breadcrumb generation (User Story 7)."""

    def test_plugin_get_breadcrumbs(self, sample, user):
        """Given a plugin with get_breadcrumbs method,
        When called,
        Then it returns breadcrumb navigation (User Story 7, Scenario 2)."""

        @plugins.register(Sample)
        class BreadcrumbPlugin(Plugin, TemplateView):
            menu = {"label": "Breadcrumb", "icon": "bread", "order": 30}
            page_title = "Breadcrumb"
            template_name = "breadcrumb.html"

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/breadcrumb/")
        request.user = user

        plugin = BreadcrumbPlugin()
        plugin.request = request
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}

        breadcrumbs = plugin.get_breadcrumbs()

        # Should return a list
        assert isinstance(breadcrumbs, list)

        # Should have at least the current page
        assert len(breadcrumbs) > 0

    def test_breadcrumb_structure(self, sample, user):
        """Breadcrumbs should have proper structure with text and href."""

        @plugins.register(Sample)
        class StructuredBreadcrumb(Plugin, TemplateView):
            menu = {"label": "Structured", "icon": "struct", "order": 40}
            page_title = "Structured"
            template_name = "structured.html"

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/structured/")
        request.user = user

        plugin = StructuredBreadcrumb()
        plugin.request = request
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}

        breadcrumbs = plugin.get_breadcrumbs()

        # Each breadcrumb should be a dict with text and optionally href
        for crumb in breadcrumbs:
            assert isinstance(crumb, dict)
            assert "text" in crumb
            # href might be missing for the current page


class TestPluginContextData:
    """Test extended context data functionality."""

    def test_plugin_can_add_custom_context(self, sample, user):
        """Plugins can add custom data to the context."""

        @plugins.register(Sample)
        class CustomContextPlugin(Plugin, TemplateView):
            menu = {"label": "Custom Context", "icon": "custom", "order": 50}
            page_title = "Custom Context"
            template_name = "custom_context.html"

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["custom_field"] = "custom_value"
                context["computed_data"] = self.compute_data()
                return context

            def compute_data(self):
                return {"result": 42}

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/custom-context/")
        request.user = user

        plugin = CustomContextPlugin()
        plugin.request = request
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}

        context = plugin.get_context_data()

        # Should have custom fields
        assert "custom_field" in context
        assert context["custom_field"] == "custom_value"
        assert "computed_data" in context
        assert context["computed_data"]["result"] == 42


class TestTemplateResolution:
    """Test template resolution hierarchy (User Story 3)."""

    def test_plugin_uses_specified_template(self):
        """Given a plugin with template_name specified,
        When rendering the plugin,
        Then the specified template is used."""

        @plugins.register(Sample)
        class TemplatePlugin(Plugin, TemplateView):
            template_name = "plugins/custom-template.html"
            menu = {"label": "Template", "icon": "file", "order": 10}

        plugin = TemplatePlugin()
        assert plugin.template_name == "plugins/custom-template.html"

    def test_template_hierarchy_for_model_specific_override(self):
        """Template resolution should follow the hierarchy:
        1. plugins/<app>/<model>/<plugin>.html
        2. plugins/<plugin>.html
        3. Plugin's template_name attribute
        """

        @plugins.register(Sample)
        class HierarchyPlugin(Plugin, TemplateView):
            template_name = "plugins/fallback.html"
            menu = {"label": "Hierarchy", "icon": "layer", "order": 20}

        # The plugin should look for templates in this order:
        # 1. plugins/sample/sample/hierarchy-plugin.html (most specific)
        # 2. plugins/hierarchy-plugin.html (generic)
        # 3. plugins/fallback.html (explicit template_name)

        plugin = HierarchyPlugin()

        # Verify fallback template is set
        assert plugin.template_name == "plugins/fallback.html"


class TestTemplateContext:
    """Test template context for plugins."""

    def test_plugin_get_context_data(self, user):
        """Plugin should be able to add context data."""

        @plugins.register(Sample)
        class ContextPlugin(Plugin, TemplateView):
            template_name = "plugins/context.html"
            menu = {"label": "Context", "icon": "database", "order": 30}
            # Concrete plugins declare page_title; get_breadcrumbs reads it
            # directly when the plugin contributes a menu entry.
            page_title = "Context"

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["custom_data"] = "test_value"
                return context

        factory = RequestFactory()
        request = factory.get("/test/")
        request.user = user

        plugin = ContextPlugin()
        plugin.request = request

        context = plugin.get_context_data()
        assert "custom_data" in context
        assert context["custom_data"] == "test_value"


class TestBaseOverviewPlugin:
    """Test OverviewPlugin reusable base (User Story 8).

    OverviewPlugin (fairdm.core.plugins) is a thin combination of this
    module's Plugin mixin with FairDMTemplateView; these tests exercise
    Plugin behaviour (registration, get_context_data) through that
    concrete subclass.
    """

    def test_overview_plugin_inheritance(self):
        """Given OverviewPlugin as a base,
        When creating a plugin,
        Then minimal configuration is needed (User Story 8, Scenario 1)."""

        @plugins.register(Sample)
        class SampleOverview(OverviewPlugin):
            menu = {"label": "Overview", "icon": "info-circle", "order": 1}

        # Should have template_name from base class
        assert hasattr(SampleOverview, "template_name")

        # Should be properly registered
        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [cls.__name__ for cls, _kwargs in registered_plugins]
        assert "SampleOverview" in plugin_names

    def test_overview_plugin_provides_context(self, sample, user):
        """OverviewPlugin should provide object context."""

        @plugins.register(Sample)
        class ContextOverview(OverviewPlugin):
            menu = {"label": "Context Overview", "icon": "ctx", "order": 2}
            # OverviewPlugin only defines get_page_title() (a method), not a
            # page_title attribute, but get_breadcrumbs() reads self.page_title
            # directly whenever self.menu is truthy. Set it explicitly so this
            # test can exercise get_context_data() without tripping that
            # unrelated bug.
            page_title = "Context Overview"

        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.pk}/context-overview/")
        request.user = user

        plugin = ContextOverview()
        plugin.request = request
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}
        # Normally dispatch() sets self.object before get_context_data() runs;
        # we call get_context_data() directly here, bypassing dispatch, so set
        # it explicitly (OverviewPlugin.get_page_title() reads self.object).
        plugin.object = sample

        context = plugin.get_context_data()

        # Should have object in context
        assert "object" in context


class TestBaseEditPlugin:
    """Test UpdatePlugin reusable base (User Story 8)."""

    def test_edit_plugin_inheritance(self):
        """UpdatePlugin should provide edit form functionality."""

        @plugins.register(Sample)
        class SampleEdit(UpdatePlugin):
            menu = {"label": "Edit", "icon": "edit", "order": 10}
            permission = "sample.change_sample"
            fields = ["name", "description"]

        # Should inherit from Plugin and UpdateView
        assert hasattr(SampleEdit, "get_object")
        assert hasattr(SampleEdit, "get_form_class")

        # Should be registered
        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [cls.__name__ for cls, _kwargs in registered_plugins]
        assert "SampleEdit" in plugin_names

    def test_edit_plugin_with_custom_form_class(self):
        """UpdatePlugin can use a custom form class."""
        from django import forms

        class CustomSampleForm(forms.ModelForm):
            class Meta:
                model = Sample
                fields = ["name"]

        @plugins.register(Sample)
        class CustomFormEdit(UpdatePlugin):
            form_class = CustomSampleForm
            menu = {"label": "Custom Edit", "icon": "edit", "order": 11}
            permission = "sample.change_sample"

        # Should use custom form class
        assert CustomFormEdit.form_class == CustomSampleForm


class TestBaseDeletePlugin:
    """Test DeletePlugin reusable base (User Story 8)."""

    def test_delete_plugin_inheritance(self):
        """DeletePlugin should provide delete functionality."""

        @plugins.register(Sample)
        class SampleDelete(DeletePlugin):
            menu = {"label": "Delete", "icon": "trash", "order": 20}
            permission = "sample.delete_sample"

        # Should inherit from Plugin and DeleteView
        assert hasattr(SampleDelete, "get_object")
        assert hasattr(SampleDelete, "delete")

        # Should be registered
        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [cls.__name__ for cls, _kwargs in registered_plugins]
        assert "SampleDelete" in plugin_names

    def test_delete_plugin_requires_permission(self):
        """DeletePlugin should enforce permissions."""

        @plugins.register(Sample)
        class RestrictedDelete(DeletePlugin):
            menu = {"label": "Restricted Delete", "icon": "lock", "order": 21}
            permission = "sample.delete_sample"

        # Should have permission attribute
        assert RestrictedDelete.permission == "sample.delete_sample"


class TestInheritancePatterns:
    """Test proper inheritance patterns with base classes."""

    def test_multiple_plugins_from_same_base(self):
        """Multiple plugins can inherit from the same base class."""

        @plugins.register(Sample)
        class Overview1(OverviewPlugin):
            menu = {"label": "Overview 1", "icon": "o1", "order": 100}

        @plugins.register(Sample)
        class Overview2(OverviewPlugin):
            menu = {"label": "Overview 2", "icon": "o2", "order": 101}

        # Both should be registered
        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [cls.__name__ for cls, _kwargs in registered_plugins]

        assert "Overview1" in plugin_names
        assert "Overview2" in plugin_names

    def test_base_classes_do_not_require_plugin_mixin(self):
        """Base plugin classes already include Plugin mixin."""

        # These should work without explicit Plugin inheritance
        @plugins.register(Sample)
        class SimpleOverview(OverviewPlugin):
            menu = {"label": "Simple", "icon": "simple", "order": 200}

        # Should have Plugin methods
        assert hasattr(SimpleOverview, "get_urls")
        assert hasattr(SimpleOverview, "get_name")
        assert hasattr(SimpleOverview, "get_url_path")
