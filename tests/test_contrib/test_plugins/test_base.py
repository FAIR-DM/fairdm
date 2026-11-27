"""Tests for fairdm.contrib.plugins.base.Plugin."""

import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse
from django.views.generic import DetailView, TemplateView, UpdateView

from demo.factories import RockSampleFactory
from fairdm.contrib.plugins import Plugin
from fairdm.core.plugins import OverviewPlugin
from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory
from fairdm.factories.contributors import UserFactory
from fairdm.utils.choices import Visibility

pytestmark = pytest.mark.django_db


def mounted(plugin_class, user=None, **kwargs):
    """Return an instance of ``plugin_class`` set up as a request leaves it."""
    plugin = plugin_class()
    plugin.registered_model = Sample
    plugin.kwargs = kwargs
    plugin.request = RequestFactory().get("/")
    plugin.request.user = user if user is not None else UserFactory()
    return plugin


class TestPluginGetObject:
    def test_get_object_with_pk_kwarg(self, sample):
        plugin = mounted(type("P", (Plugin, TemplateView), {}), pk=sample.pk)

        assert plugin.get_base_object() == sample

    def test_get_object_with_uuid_kwarg(self, sample):
        plugin = mounted(type("P", (Plugin, TemplateView), {}), uuid=sample.uuid)

        assert plugin.get_base_object() == sample

    def test_get_object_without_model_raises_error(self):
        plugin = mounted(type("P", (Plugin, TemplateView), {}), pk=1)
        plugin.registered_model = None

        with pytest.raises(ValueError, match="has no associated model"):
            plugin.get_base_object()

    def test_get_object_without_pk_or_uuid_raises_error(self):
        plugin = mounted(type("P", (Plugin, TemplateView), {}))

        with pytest.raises(
            ValueError, match="mounted without any of the lookup kwargs"
        ):
            plugin.get_base_object()

    def test_get_object_with_nonexistent_record_is_404(self):
        plugin = mounted(type("P", (Plugin, TemplateView), {}), pk=999999)

        with pytest.raises(Http404):
            plugin.get_base_object()


class TestPluginHasPermission:
    """Permission rules are tested in test_access; these check the wiring."""

    def test_has_permission_without_permission_attribute(self, sample):
        class PublicPlugin(Plugin, TemplateView):
            permission = None

        assert mounted(PublicPlugin, uuid=sample.uuid).has_permission() is True

    def test_has_permission_with_a_shipped_role(self, sample):
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.change_sample"

        user = UserFactory()
        user.groups.add(Group.objects.get(name="Data Curator"))

        assert (
            mounted(PermissionPlugin, user, uuid=sample.uuid).has_permission() is True
        )


class TestPluginDispatch:
    def test_dispatch_leaves_the_view_s_own_object_alone(self, sample):
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
        class PermissionPlugin(Plugin, TemplateView):
            permission = "sample.delete_sample"
            template_name = "test.html"
            registered_model = Sample

        request = RequestFactory().get(f"/sample/{sample.uuid}/test/")
        request.user = UserFactory()

        with pytest.raises(PermissionDenied):
            PermissionPlugin.as_view()(request, uuid=sample.uuid)

    def test_dispatch_raises_404_for_a_missing_record(self):
        class TestPlugin(Plugin, TemplateView):
            template_name = "test.html"
            registered_model = Sample

        request = RequestFactory().get("/sample/nonexistent-uuid/test/")
        request.user = UserFactory()

        with pytest.raises(Http404):
            TestPlugin.as_view()(request, uuid="nonexistent-uuid")


class TestPluginGetContextData:
    def test_get_context_data_uses_self_object(self, sample):
        plugin = mounted(type("P", (Plugin, TemplateView), {}))
        plugin.object = sample

        assert plugin.get_context_data()["object"] == sample

    def test_get_context_data_fetches_object_if_not_set(self, sample):
        plugin = mounted(type("P", (Plugin, TemplateView), {}), pk=sample.pk)

        assert plugin.get_context_data()["object"] == sample

    def test_get_context_data_handles_fetch_failure(self):
        plugin = mounted(type("P", (Plugin, TemplateView), {}))

        assert plugin.get_context_data()["object"] is None

    def test_get_context_data_includes_plugin_menu(self, sample):
        class TestPlugin(Plugin, TemplateView):
            menu = {"label": "Test Tab"}

        plugin = mounted(TestPlugin, pk=sample.pk)

        assert plugin.get_context_data()["plugin_menu"] == {"label": "Test Tab"}

    def test_get_context_data_without_media(self):
        plugin = mounted(type("P", (Plugin, TemplateView), {}))

        assert plugin.get_context_data()["plugin_media"] is None

    def test_a_plugin_can_add_to_the_context(self, sample):
        class CustomContextPlugin(Plugin, TemplateView):
            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["custom_field"] = "custom_value"
                return context

        context = mounted(CustomContextPlugin, pk=sample.pk).get_context_data()

        assert context["custom_field"] == "custom_value"
        assert context["object"] == sample


class TestPluginGetBreadcrumbs:
    def test_the_trail_ends_at_the_current_page(self, sample):
        class TestPlugin(Plugin, TemplateView):
            page_title = "Custom Page"
            menu = {"label": "Custom Page"}

        breadcrumbs = mounted(TestPlugin, pk=sample.pk).get_breadcrumbs()

        assert breadcrumbs[-1]["text"] == "Custom Page"

    def test_a_long_record_name_is_kept_whole(self):
        sample = RockSampleFactory(name="A" * 100)

        class TestPlugin(Plugin, TemplateView):
            page_title = "View"
            menu = {"label": "View"}

        breadcrumbs = mounted(TestPlugin, pk=sample.pk).get_breadcrumbs()

        assert str(sample) in [b["text"] for b in breadcrumbs]

    def test_every_entry_has_text(self, sample):
        class TestPlugin(Plugin, TemplateView):
            page_title = "Structured"
            menu = {"label": "Structured"}

        breadcrumbs = mounted(TestPlugin, pk=sample.pk).get_breadcrumbs()

        assert breadcrumbs
        assert all(isinstance(crumb, dict) and crumb["text"] for crumb in breadcrumbs)

    def test_a_missing_record_still_leaves_the_current_page(self):
        class TestPlugin(Plugin, TemplateView):
            page_title = "Page"
            menu = {"label": "Page"}

        breadcrumbs = mounted(TestPlugin).get_breadcrumbs()

        assert breadcrumbs[-1]["text"] == "Page"


class TestPluginGetTemplateNames:
    def test_get_template_names_with_explicit_template(self):
        class TestPlugin(Plugin, TemplateView):
            template_name = "custom/template.html"

        plugin = TestPlugin()
        plugin.registered_model = Sample

        assert plugin.get_template_names()[0] == "custom/template.html"


class TestOverviewPlugin:
    def test_overview_plugin_provides_the_record(self, sample, user):
        class ContextOverview(OverviewPlugin):
            page_title = "Context Overview"

        plugin = mounted(ContextOverview, user, pk=sample.pk)
        # Normally dispatch() sets self.object before get_context_data() runs;
        # we call get_context_data() directly here, bypassing dispatch, so set
        # it explicitly (OverviewPlugin.get_page_title() reads self.object).
        plugin.object = sample

        assert plugin.get_context_data()["object"] == sample


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
    def trail_of(self, rf, user, sample, **attrs):
        view_class = type(
            "Titled",
            (Plugin, TemplateView),
            {"template_name": "fairdm/plugin.html", **attrs},
        )
        view = view_class()
        view.request = rf.get("/")
        view.request.user = user
        view.kwargs = {"uuid": sample.uuid}
        view.registered_model = Sample
        return view.get_finished_breadcrumbs()

    def test_the_record_entry_links_to_the_record_below_it(self, rf, plain_user):
        sample = RockSampleFactory()
        trail = self.trail_of(rf, plain_user, sample, page_title="Analysis")
        record_entry = next(e for e in trail if e["text"] == str(sample))
        assert record_entry["href"] == sample.get_absolute_url()

    def test_the_trail_starts_at_the_list_of_the_records_own_type(self, rf, plain_user):
        sample = RockSampleFactory()
        first = self.trail_of(rf, plain_user, sample)[0]
        assert first["text"] == "Rock Samples"
        assert first["href"] == reverse("rocksample-list")

    def test_the_first_entry_carries_the_record_types_icon(self, rf, plain_user):
        sample = RockSampleFactory()
        assert self.trail_of(rf, plain_user, sample)[0]["icon"] == "sample"

    def test_the_page_trail_ends_at_the_record_without_a_link(self, client):
        sample = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        trail = response.context["breadcrumbs"]
        assert trail[-1]["text"] == str(sample)
        assert "href" not in trail[-1]
        assert response.context["page"]["breadcrumbs"] == trail
        assert all(entry.get("href") not in {"#", "/"} for entry in trail)

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
