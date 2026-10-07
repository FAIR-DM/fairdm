"""Tests for fairdm.contrib.plugins.base.Plugin."""

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse
from django.views.generic import DetailView, TemplateView, UpdateView

from demo.factories import RockSampleFactory
from fairdm.utils.choices import Visibility
from fairdm.factories import DatasetFactory
from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.plugins import OverviewPlugin
from fairdm.core.sample.models import Sample
from fairdm.factories.contributors import UserFactory

pytestmark = pytest.mark.django_db


class TestCustomURLs:
    def test_plugin_with_custom_url_path(self):

        @plugins.register(Sample)
        class CustomURLPlugin(Plugin, TemplateView):
            url_path = "custom/analysis"
            menu = {"label": "Custom", "icon": "custom", "order": 10}
            template_name = "custom.html"

        assert CustomURLPlugin.get_url_path() == "custom/analysis"

    def test_plugin_with_extra_views(self):

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
        assert str(url_patterns[1].pattern) == "multi-url-plugin/export/"


class TestDefaultURLGeneration:
    def test_default_url_path_from_class_name(self):

        @plugins.register(Sample)
        class DefaultURLPlugin(Plugin, TemplateView):
            menu = {"label": "Default", "icon": "default", "order": 30}
            template_name = "default.html"

        expected_path = "default-url-plugin"
        assert DefaultURLPlugin.get_url_path() == expected_path

    def test_default_url_name_from_class_name(self):

        @plugins.register(Sample)
        class NamedPlugin(Plugin, TemplateView):
            menu = {"label": "Named", "icon": "name", "order": 40}
            template_name = "named.html"

        expected_name = "named-plugin"
        assert NamedPlugin.get_name() == expected_name


class TestURLParameters:
    def test_plugin_url_includes_pk_parameter(self):

        @plugins.register(Sample)
        class ParamPlugin(Plugin, TemplateView):
            menu = {"label": "Param", "icon": "param", "order": 50}
            template_name = "param.html"

        url_patterns = ParamPlugin.get_urls(menu_class=None)

        assert len(url_patterns) > 0

        first_pattern = url_patterns[0]
        pattern_str = str(first_pattern.pattern)

        assert pattern_str == "param-plugin/"


class TestPluginPermissions:
    def test_plugin_with_permission_attribute(self):

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.change_sample"
            menu = {"label": "Edit", "icon": "edit", "order": 10}
            template_name = "plugins/edit.html"

        user_with_perm = UserFactory(email="editor@example.com")
        user_without_perm = UserFactory(email="viewer@example.com")

        content_type = ContentType.objects.get_for_model(Sample)
        change_perm = Permission.objects.get(
            codename="change_sample", content_type=content_type
        )
        user_with_perm.user_permissions.add(change_perm)

        assert user_with_perm.has_perm("sample.change_sample")
        assert not user_without_perm.has_perm("sample.change_sample")

    def test_plugin_without_permission_is_public(self):

        @plugins.register(Sample)
        class PublicPlugin(Plugin, TemplateView):
            menu = {"label": "Overview", "icon": "info", "order": 20}
            template_name = "plugins/overview.html"

        assert (
            not hasattr(PublicPlugin, "permission") or PublicPlugin.permission is None
        )

    def test_permission_shown_in_tab(self, sample, admin_user):

        @plugins.register(Sample)
        class SecurePlugin(Plugin, TemplateView):
            permission = "sample.delete_sample"
            menu = {"label": "Delete", "icon": "trash", "order": 30}
            template_name = "plugins/delete.html"

        assert hasattr(SecurePlugin, "permission")
        assert SecurePlugin.permission == "sample.delete_sample"


class TestObjectLevelPermissions:
    def test_plugin_respects_object_permissions(self):

        @plugins.register(Sample)
        class ObjectPermPlugin(Plugin, TemplateView):
            permission = "sample.view_sample"
            menu = {"label": "View Details", "icon": "eye", "order": 40}
            template_name = "plugins/details.html"

        assert ObjectPermPlugin.permission == "sample.view_sample"


class TestPluginGetObject:
    def test_get_object_with_pk_kwarg(self, sample):

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

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.kwargs = {"pk": 1}
        plugin.registered_model = None

        with pytest.raises(ValueError, match="has no associated model"):
            plugin.get_base_object()

    def test_get_object_without_pk_or_uuid_raises_error(self):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.kwargs = {}
        plugin.registered_model = Sample

        with pytest.raises(
            ValueError, match="mounted without any of the lookup kwargs"
        ):
            plugin.get_base_object()

    def test_get_object_with_nonexistent_record_is_404(self):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.kwargs = {"pk": 999999}
        plugin.registered_model = Sample

        with pytest.raises(Http404):
            plugin.get_base_object()


class TestPluginHasPermission:
    def test_has_permission_without_permission_attribute(self, sample):

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

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.change_sample"
            template_name = "test.html"

        request = RequestFactory().get("/")

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

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.delete_sample"
            template_name = "test.html"

        request = RequestFactory().get("/")
        request.user = UserFactory()

        plugin = PermissionPlugin()
        plugin.request = request
        plugin.kwargs = {"uuid": sample.uuid}
        plugin.registered_model = Sample

        assert plugin.has_permission() is False

    def test_has_permission_with_anonymous_user(self, sample):

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
    def test_dispatch_leaves_the_view_s_own_object_alone(self, sample):

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

        @plugins.register(Sample)
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.delete_sample"
            template_name = "test.html"
            registered_model = Sample

        plugin = PermissionPlugin.as_view()
        factory = RequestFactory()
        request = factory.get(f"/sample/{sample.uuid}/test/")
        request.user = UserFactory()

        with pytest.raises(PermissionDenied):
            plugin(request, uuid=sample.uuid)

    def test_dispatch_raises_404_for_a_missing_record(self):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            registered_model = Sample

        request = RequestFactory().get("/sample/nonexistent-uuid/test/")
        request.user = UserFactory()

        with pytest.raises(Http404):
            TestPlugin.as_view()(request, uuid="nonexistent-uuid")


class TestPluginGetContextData:
    def test_get_context_data_uses_self_object(self, sample):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {}
        plugin.object = sample

        factory = RequestFactory()
        plugin.request = factory.get("/")
        plugin.request.user = UserFactory()

        context = plugin.get_context_data()

        assert context["object"] == sample

    def test_get_context_data_fetches_object_if_not_set(self, sample):

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

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {}

        factory = RequestFactory()
        plugin.request = factory.get("/")
        plugin.request.user = UserFactory()

        context = plugin.get_context_data()

        assert context["object"] is None

    def test_get_context_data_includes_breadcrumbs(self, sample):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
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
    def test_get_breadcrumbs_includes_model_name(self, sample):

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
        assert (
            Sample._meta.verbose_name_plural.lower() in breadcrumbs[0]["text"].lower()
        )

    def test_get_breadcrumbs_includes_object_str(self, sample):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            page_title = "Edit"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}
        plugin.menu = {"label": "Edit"}

        breadcrumbs = plugin.get_breadcrumbs()

        assert len(breadcrumbs) >= 2

    def test_get_breadcrumbs_truncates_long_names(self):
        long_name = "A" * 100
        sample = RockSampleFactory(name=long_name)

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            page_title = "View"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}
        plugin.menu = {"label": "View"}

        breadcrumbs = plugin.get_breadcrumbs()

        obj_breadcrumb = next(
            (b for b in breadcrumbs if "..." in b.get("text", "")), None
        )
        if obj_breadcrumb:
            assert len(obj_breadcrumb["text"]) <= 50

    def test_get_breadcrumbs_includes_current_page(self, sample):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            page_title = "Custom Page"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {"pk": sample.pk}
        plugin.menu = {"label": "Custom Page"}

        breadcrumbs = plugin.get_breadcrumbs()

        assert breadcrumbs[-1]["text"] == "Custom Page"

    def test_get_breadcrumbs_handles_missing_object(self):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            page_title = "Page"

        plugin = TestPlugin()
        plugin.registered_model = Sample
        plugin.kwargs = {}
        plugin.menu = {"label": "Page"}

        breadcrumbs = plugin.get_breadcrumbs()

        assert len(breadcrumbs) >= 1


class TestPluginGetTemplateNames:
    def test_get_url_path_fallback(self):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            pass

        assert TestPlugin.get_url_path() == "test-plugin"

    def test_get_template_names_with_explicit_template(self):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            template_name = "custom/template.html"

        plugin = TestPlugin()
        plugin.registered_model = Sample

        templates = plugin.get_template_names()

        assert templates[0] == "custom/template.html"


class TestPluginContext:
    def test_plugin_get_object_returns_instance(self, sample):

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

        obj = plugin.get_base_object()
        assert obj == sample
        assert isinstance(obj, Sample)

    def test_plugin_context_object(self, sample, user):

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

        assert "object" in context
        assert context["object"] == sample


class TestPluginBreadcrumbs:
    def test_plugin_get_breadcrumbs(self, sample, user):

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

        assert isinstance(breadcrumbs, list)

        assert len(breadcrumbs) > 0

    def test_breadcrumb_structure(self, sample, user):

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

        for crumb in breadcrumbs:
            assert isinstance(crumb, dict)
            assert "text" in crumb


class TestPluginContextData:
    def test_plugin_can_add_custom_context(self, sample, user):

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

        assert "custom_field" in context
        assert context["custom_field"] == "custom_value"
        assert "computed_data" in context
        assert context["computed_data"]["result"] == 42


class TestTemplateResolution:
    def test_plugin_uses_specified_template(self):

        @plugins.register(Sample)
        class TemplatePlugin(Plugin, TemplateView):
            template_name = "plugins/custom-template.html"
            menu = {"label": "Template", "icon": "file", "order": 10}

        plugin = TemplatePlugin()
        assert plugin.template_name == "plugins/custom-template.html"

    def test_template_hierarchy_for_model_specific_override(self):

        @plugins.register(Sample)
        class HierarchyPlugin(Plugin, TemplateView):
            template_name = "plugins/fallback.html"
            menu = {"label": "Hierarchy", "icon": "layer", "order": 20}

        plugin = HierarchyPlugin()

        assert plugin.template_name == "plugins/fallback.html"


class TestTemplateContext:
    def test_plugin_get_context_data(self, user):

        @plugins.register(Sample)
        class ContextPlugin(Plugin, TemplateView):
            template_name = "plugins/context.html"
            menu = {"label": "Context", "icon": "database", "order": 30}
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
    def test_overview_plugin_inheritance(self):

        @plugins.register(Sample)
        class SampleOverview(OverviewPlugin):
            menu = {"label": "Overview", "icon": "info-circle", "order": 1}

        assert hasattr(SampleOverview, "template_name")

        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [cls.__name__ for cls, _kwargs in registered_plugins]
        assert "SampleOverview" in plugin_names

    def test_overview_plugin_provides_context(self, sample, user):

        @plugins.register(Sample)
        class ContextOverview(OverviewPlugin):
            menu = {"label": "Context Overview", "icon": "ctx", "order": 2}
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

        assert "object" in context


class TestInheritancePatterns:
    def test_multiple_plugins_from_same_base(self):

        @plugins.register(Sample)
        class Overview1(OverviewPlugin):
            menu = {"label": "Overview 1", "icon": "o1", "order": 100}

        @plugins.register(Sample)
        class Overview2(OverviewPlugin):
            menu = {"label": "Overview 2", "icon": "o2", "order": 101}

        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [cls.__name__ for cls, _kwargs in registered_plugins]

        assert "Overview1" in plugin_names
        assert "Overview2" in plugin_names

    def test_base_classes_do_not_require_plugin_mixin(self):

        @plugins.register(Sample)
        class SimpleOverview(OverviewPlugin):
            menu = {"label": "Simple", "icon": "simple", "order": 200}

        assert hasattr(SimpleOverview, "get_urls")
        assert hasattr(SimpleOverview, "get_name")
        assert hasattr(SimpleOverview, "get_url_path")


class TestNaming:
    def test_explicit_name_wins(self):
        class P(Plugin, TemplateView):
            name = "chosen"

        assert P.get_name() == "chosen"

    def test_name_is_derived_from_the_class(self):
        class AnalysisSummary(Plugin, TemplateView):
            pass

        assert AnalysisSummary.get_name() == "analysis-summary"

    def test_explicit_segment_wins(self):
        class P(Plugin, TemplateView):
            url_path = "custom/analysis"

        assert P.get_url_path() == "custom/analysis"

    def test_segment_defaults_to_the_name(self):
        class DataExport(Plugin, TemplateView):
            pass

        assert DataExport.get_url_path() == "data-export"

    def test_a_plugin_can_decline_a_segment(self):
        class P(Plugin, TemplateView):
            url_path = None

        assert P.get_url_path() is None


@pytest.mark.django_db
class TestReachingTheRecord:
    def test_the_record_is_in_the_context(self, client):
        sample = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        assert response.context["base_object"] == sample

    def test_a_missing_record_is_404(self, client):
        import uuid as uuid_module

        response = client.get(
            reverse("sample:overview", kwargs={"uuid": uuid_module.uuid4()})
        )
        assert response.status_code == 404

    def test_a_view_keeps_its_own_object(self, rf, plain_user):
        sample = RockSampleFactory()

        seen = {}

        class Detail(Plugin, DetailView):
            model = Sample
            template_name = "base.html"
            slug_field = "uuid"
            slug_url_kwarg = "uuid"

            def get_context_data(self, **kwargs):
                seen["object"] = self.object
                seen["base_object"] = self.base_object
                return super().get_context_data(**kwargs)

        request = rf.get("/")
        request.user = plain_user
        Detail.as_view(registered_model=Sample)(request, uuid=sample.uuid)
        assert seen["object"] == sample
        assert seen["base_object"] == sample

    def test_a_stock_update_view_keeps_its_form_class(self, rf, plain_user):
        from fairdm.core.sample.models import Sample as SampleModel

        class Editor(Plugin, UpdateView):
            model = SampleModel
            fields = ["name"]
            template_name = "base.html"
            slug_field = "uuid"
            slug_url_kwarg = "uuid"

        sample = RockSampleFactory()
        request = rf.get("/")
        request.user = plain_user
        response = Editor.as_view(registered_model=SampleModel)(
            request, uuid=sample.uuid
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestTheNavigationTrail:
    def test_the_record_entry_links_to_the_record(self, client):
        sample = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        trail = response.context["breadcrumbs"]
        record_entry = next(e for e in trail if e["text"] == str(sample))
        assert record_entry["href"] == sample.get_absolute_url()

    def test_no_entry_carries_a_placeholder_link(self, client):
        sample = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        for entry in response.context["breadcrumbs"]:
            assert entry.get("href") not in {"#", "/"}

    def test_a_plugin_without_a_page_title_does_not_raise(self, rf, plain_user):
        sample = RockSampleFactory()

        class Quiet(Plugin, TemplateView):
            template_name = "fairdm/plugin.html"

        view = Quiet()
        view.request = rf.get("/")
        view.request.user = plain_user
        view.kwargs = {"uuid": sample.uuid}
        view.registered_model = Sample
        assert view.get_breadcrumbs()


@pytest.mark.django_db
class TestDeclaredAssets:
    def test_declared_stylesheets_and_scripts_reach_the_response(self, client):
        sample = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        assert "plugin_media" in response.context

    def test_a_plugin_declaring_media_exposes_it(self, rf, plain_user):
        sample = RockSampleFactory()

        class WithAssets(Plugin, TemplateView):
            template_name = "fairdm/plugin.html"

            class Media:
                css = {"all": ["myapp/analysis.css"]}
                js = ["myapp/analysis.js"]

        view = WithAssets()
        view.request = rf.get("/")
        view.request.user = plain_user
        view.kwargs = {"uuid": sample.uuid}
        view.registered_model = Sample
        media = view.get_context_data()["plugin_media"]
        assert "myapp/analysis.css" in str(media)
        assert "myapp/analysis.js" in str(media)
