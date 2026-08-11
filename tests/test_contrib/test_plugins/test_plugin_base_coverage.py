"""
Enhanced test coverage forPlugin base class.

Covers gaps in permission handling, dispatch, context data, and error cases.
"""

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.views.generic import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.sample.models import Sample
from fairdm.factories import SampleFactory
from fairdm.factories.contributors import UserFactory

pytestmark = pytest.mark.django_db


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

        with pytest.raises(ValueError, match="must include 'pk' or 'uuid' kwarg"):
            plugin.get_base_object()

    def test_get_object_with_nonexistent_pk_raises_error(self):
        """Plugin with non-existent pk should raise DoesNotExist."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.kwargs = {"pk": 999999}
        plugin.registered_model = Sample

        with pytest.raises(Sample.DoesNotExist):
            plugin.get_base_object()


class TestPluginHasPermission:
    """Test Plugin.has_permission() method."""

    def test_has_permission_without_permission_attribute(self, sample):
        """Plugin without permission requirement should always allow access."""

        @plugins.register(Sample)
        class PublicPlugin(Plugin, TemplateView):
            permission = None
            template_name = "test.html"

        plugin = PublicPlugin()
        factory = RequestFactory()
        request = factory.get("/")
        request.user = UserFactory()

        assert plugin.has_permission(request, sample) is True

    def test_has_permission_with_model_level_permission(self, sample):
        """Plugin should check model-level permissions."""

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.change_sample"
            template_name = "test.html"

        plugin = PermissionPlugin()
        factory = RequestFactory()
        request = factory.get("/")

        # User with permission
        user_with_perm = UserFactory()
        content_type = ContentType.objects.get_for_model(Sample)
        perm = Permission.objects.get(
            codename="change_sample", content_type=content_type
        )
        user_with_perm.user_permissions.add(perm)
        request.user = user_with_perm

        assert plugin.has_permission(request, sample) is True

    def test_has_permission_denies_user_without_permission(self, sample):
        """Plugin should deny access to users without permission."""

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.delete_sample"
            template_name = "test.html"

        plugin = PermissionPlugin()
        factory = RequestFactory()
        request = factory.get("/")
        request.user = UserFactory()  # User without delete permission

        assert plugin.has_permission(request, sample) is False

    def test_has_permission_with_anonymous_user(self, sample):
        """Plugin should handle anonymous users."""

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.view_sample"
            template_name = "test.html"

        plugin = PermissionPlugin()
        factory = RequestFactory()
        request = factory.get("/")
        request.user = AnonymousUser()

        assert plugin.has_permission(request, sample) is False


class TestPluginDispatch:
    """Test Plugin.dispatch() method."""

    def test_dispatch_stores_object(self, sample):
        """Dispatch should store object as self.object."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            # dispatch() -> get_base_object() reads self.registered_model, which
            # is normally set by the registry during URL generation. Since we
            # call as_view() directly here (bypassing the registry), it must be
            # set explicitly.
            registered_model = Sample

            def get(self, request, *args, **kwargs):
                # Check that self.object was set
                assert hasattr(self, "object")
                assert self.object == sample
                return super().get(request, *args, **kwargs)

        plugin = TestPlugin.as_view()
        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.uuid}/test/")
        request.user = UserFactory()

        # This will call dispatch, which should set self.object
        response = plugin(request, uuid=sample.uuid)
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

    def test_dispatch_handles_missing_object(self):
        """Dispatch should handle non-existent object gracefully."""

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            registered_model = Sample

        plugin = TestPlugin.as_view()
        factory = RequestFactory()
        request = factory.get("/sample/nonexistent-uuid/test/")
        request.user = UserFactory()

        # Should not crash, just set obj=None and continue
        response = plugin(request, uuid="nonexistent-uuid")
        # Should get 200 since no permission check with None object
        assert response.status_code == 200


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
        plugin.kwargs = {"pk": 999999}  # Non-existent

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
        plugin.kwargs = {"pk": 999999}  # Non-existent
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
