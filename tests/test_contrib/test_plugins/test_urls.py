"""Registration, addresses and the record behind them."""

import pytest
from django.urls import reverse
from django.views.generic import DetailView, TemplateView, UpdateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins import reverse as plugin_reverse
from fairdm.contrib.plugins.utils import slugify
from fairdm.core.dataset.models import Dataset
from fairdm.core.sample.models import Sample
from fairdm_demo.factories import RockSampleFactory


class TestNaming:
    def test_explicit_name_wins(self):
        class P(Plugin, TemplateView):
            name = "chosen"

        assert P.get_name() == "chosen"

    def test_name_is_derived_from_the_class(self):
        class AnalysisSummary(Plugin, TemplateView):
            pass

        assert AnalysisSummary.get_name() == "analysis-summary"

    def test_acronyms_are_not_split_into_letters(self):
        """The hand-rolled version turned URLTestPlugin into u-r-l-test-plugin."""
        assert slugify("URLTestPlugin") == "url-test-plugin"

    def test_spaces_and_underscores_become_hyphens(self):
        assert slugify("My Plugin_Name") == "my-plugin-name"

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
class TestAddresses:
    def test_a_registered_plugin_reverses_through_the_record_namespace(self):
        sample = RockSampleFactory()
        url = reverse("sample:overview", kwargs={"uuid": sample.uuid})
        assert url == f"/samples/{sample.uuid}/overview/"

    def test_an_explicit_segment_is_the_one_served(self):
        @plugins.register(Sample, label="Custom")
        class CustomSegment(Plugin, TemplateView):
            url_path = "my-segment"
            template_name = "base.html"

        names = [p.name for p in CustomSegment.get_urls(model=Sample)]
        paths = [str(p.pattern) for p in CustomSegment.get_urls(model=Sample)]
        assert names == ["custom-segment"]
        assert paths == ["my-segment/"]

    def test_reverse_uses_the_record_s_declared_lookup(self):
        sample = RockSampleFactory()
        assert plugin_reverse(sample, "overview").endswith(f"{sample.uuid}/overview/")


@pytest.mark.django_db
class TestOneClassTwoRecords:
    def test_each_mount_resolves_its_own_record_type(self):
        """The class must not be mutated.

        Assigning the model onto the class meant the last URL configuration imported won for every
        mount, so one of the two served the wrong record type.
        """

        @plugins.register(Sample, Dataset, label="Shared")
        class Shared(Plugin, TemplateView):
            template_name = "base.html"

        sample_views = Shared.get_urls(model=Sample)
        dataset_views = Shared.get_urls(model=Dataset)

        assert sample_views[0].callback.view_initkwargs["registered_model"] is Sample
        assert dataset_views[0].callback.view_initkwargs["registered_model"] is Dataset
        # And the class itself is untouched.
        assert Shared.registered_model is None


@pytest.mark.django_db
class TestReachingTheRecord:
    def test_the_record_is_in_the_context(self, client):
        sample = RockSampleFactory()
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        assert response.context["base_object"] == sample

    def test_a_missing_record_is_404(self, client):
        import uuid as uuid_module

        response = client.get(
            reverse("sample:overview", kwargs={"uuid": uuid_module.uuid4()})
        )
        assert response.status_code == 404

    def test_a_view_keeps_its_own_object(self, rf, plain_user):
        """A plugin over a view that manages its own object must keep it."""
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
        # Its own object resolution and form machinery are untouched by registration.
        assert response.status_code == 200


@pytest.mark.django_db
class TestExtraViews:
    def test_children_share_the_parent_prefix(self):
        class Editor(Plugin, TemplateView):
            url_path = "edit"

        @plugins.register(Sample, label="Parent")
        class Parent(Plugin, TemplateView):
            url_path = "parent"
            extra_views = [Editor]

        patterns = Parent.get_urls(model=Sample)
        assert [str(p.pattern) for p in patterns] == ["parent/", "parent/edit/"]
        assert [p.name for p in patterns] == ["parent", "parent-editor"]

    def test_children_are_bound_to_the_record_and_their_owner(self):
        class Editor(Plugin, TemplateView):
            url_path = "edit"

        @plugins.register(Sample, label="Owner")
        class Owner(Plugin, TemplateView):
            extra_views = [Editor]

        child = Owner.get_urls(model=Sample)[1].callback
        assert child.view_initkwargs["registered_model"] is Sample
        assert child.view_initkwargs["plugin_class"] is Owner

    def test_the_shipped_contribution_views_address_their_target(self):
        """These had no identifier in their address at all before."""
        url = reverse(
            "project:contribution-list-contribution-update",
            kwargs={"uuid": "abc", "pk": 7},
        )
        assert url == "/project/abc/contributors/7/edit/"


@pytest.mark.django_db
class TestTheNavigationTrail:
    def test_the_record_entry_links_to_the_record(self, client):
        sample = RockSampleFactory()
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        trail = response.context["breadcrumbs"]
        record_entry = next(e for e in trail if e["text"] == str(sample))
        assert record_entry["href"] == sample.get_absolute_url()

    def test_no_entry_carries_a_placeholder_link(self, client):
        """Both hrefs used to be hardcoded, one to the site root and one to a dead anchor."""
        sample = RockSampleFactory()
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        for entry in response.context["breadcrumbs"]:
            assert entry.get("href") not in {"#", "/"}

    def test_a_plugin_without_a_page_title_does_not_raise(self, rf, plain_user):
        """Issue #112: get_breadcrumbs read an attribute the base class never defined."""
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
        sample = RockSampleFactory()
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        # The base template renders plugin_media in the head and before the closing body.
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
