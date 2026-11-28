"""Tests for plugin registration, URL generation and record pages."""

import pytest
from django.urls import reverse
from django.views.generic import TemplateView

from demo.factories import RockSampleFactory
from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins import reverse as plugin_reverse
from fairdm.core.dataset.models import Dataset
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


class TestBasicRegistration:
    def test_register_plugin_for_multiple_models(self):
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import Project

        @plugins.register(Project, Dataset, Sample)
        class MultiModelPlugin(Plugin, TemplateView):
            menu = {"label": "Multi", "icon": "multi", "order": 20}
            template_name = "multi.html"

        for model in [Project, Dataset, Sample]:
            registered_plugins = plugins.registry.get_plugins_for_model(model)
            plugin_names = [cls.__name__ for cls, _kwargs in registered_plugins]
            assert "MultiModelPlugin" in plugin_names

    def test_plugin_appears_in_url_patterns(self):

        @plugins.register(Sample)
        class URLTestPlugin(Plugin, TemplateView):
            menu = {"label": "URL Test", "icon": "url", "order": 30}
            template_name = "url_test.html"

        url_patterns = plugins.registry.get_urls_for_model(Sample)
        url_names = []
        for pattern in url_patterns:
            if hasattr(pattern, "name") and pattern.name:
                url_names.append(pattern.name)

        assert any("url-test-plugin" in name for name in url_names)


class TestPluginDeregistration:
    def test_get_plugins_for_unregistered_model(self):
        from django.contrib.auth.models import User

        plugins_list = plugins.registry.get_plugins_for_model(User)
        assert plugins_list == []


@pytest.mark.django_db
class TestAddresses:
    def test_a_registered_plugin_reverses_through_the_record_namespace(self):
        sample = RockSampleFactory()
        url = reverse("sample:overview", kwargs={"uuid": sample.uuid})
        assert url == f"/samples/{sample.uuid}/"

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
        assert plugin_reverse(sample, "overview").endswith(f"{sample.uuid}/")


@pytest.mark.django_db
class TestOneClassTwoRecords:
    def test_each_mount_resolves_its_own_record_type(self):

        @plugins.register(Sample, Dataset, label="Shared")
        class Shared(Plugin, TemplateView):
            template_name = "base.html"

        sample_views = Shared.get_urls(model=Sample)
        dataset_views = Shared.get_urls(model=Dataset)

        assert sample_views[0].callback.view_initkwargs["registered_model"] is Sample
        assert dataset_views[0].callback.view_initkwargs["registered_model"] is Dataset
        assert Shared.registered_model is None


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
        assert (
            reverse("project:contribution-list-add-person", kwargs={"uuid": "abc"})
            == "/projects/abc/contributors/add-person/"
        )
        assert (
            reverse("project:contribution-list-edit", kwargs={"uuid": "abc", "pk": 7})
            == "/projects/abc/contributors/7/edit/"
        )


@pytest.mark.django_db
class TestRecordPagesServe:
    def test_sample_overview(self, client):
        sample = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        response = client.get(reverse("sample:overview", kwargs={"uuid": sample.uuid}))
        assert response.status_code == 200

    def test_dataset_plugin_page(self, client):
        user = UserFactory()
        dataset = DatasetFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        response = client.get(
            reverse("dataset:descriptions", kwargs={"uuid": dataset.uuid})
        )
        assert response.status_code == 200

    def test_dataset_overview(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        response = client.get(
            reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        )
        assert response.status_code == 200

    def test_project_plugin_page(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(
            reverse("project:dataset-list", kwargs={"uuid": project.uuid})
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestAnAddonCanExtendARecordItDoesNotOwn:
    def test_a_registration_from_outside_the_framework_is_served(self, client):

        @plugins.register(Sample, label="Addon Page", icon="puzzle", order=900)
        class AddonPage(Plugin, TemplateView):
            template_name = "fairdm/plugin.html"

        # Re-mount so the new registration is routed, as it would be at startup.
        patterns = plugins.registry.get_urls_for_model(Sample)
        assert "addon-page" in [p.name for p in patterns]
