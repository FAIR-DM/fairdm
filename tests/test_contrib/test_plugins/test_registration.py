"""Tests for plugin registration, URL generation and record pages."""

import pytest
from django.urls import reverse
from django.views.generic import TemplateView
from flex_menu import Menu

from demo.factories import RockSampleFactory
from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins import reverse as plugin_reverse
from fairdm.contrib.plugins.cards import Card
from fairdm.contrib.plugins.checks import PluginRegistrationError
from fairdm.contrib.plugins.places import OverviewPlaces
from fairdm.contrib.plugins.registration import PluginRegistry
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    PointFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


class TestBasicRegistration:
    def test_register_plugin_for_single_model(self):

        @plugins.register(Sample)
        class TestPlugin(Plugin, TemplateView):
            menu = {"label": "Test", "icon": "test", "order": 10}
            template_name = "test.html"

        registered_plugins = plugins.registry.get_plugins_for_model(Sample)
        plugin_names = [cls.__name__ for cls, _kwargs in registered_plugins]
        assert "TestPlugin" in plugin_names

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
    def test_get_plugins_returns_list(self):
        plugins_list = plugins.registry.get_plugins_for_model(Sample)
        assert isinstance(plugins_list, list)

    def test_get_plugins_for_unregistered_model(self):
        from django.contrib.auth.models import User

        plugins_list = plugins.registry.get_plugins_for_model(User)
        assert plugins_list == []


class TestPluginAttributes:
    def test_plugin_has_get_urls_classmethod(self):

        @plugins.register(Sample)
        class AttributeTestPlugin(Plugin, TemplateView):
            menu = {"label": "Attr", "icon": "attr", "order": 40}
            template_name = "attr.html"

        assert hasattr(AttributeTestPlugin, "get_urls")
        assert callable(AttributeTestPlugin.get_urls)

    def test_plugin_has_get_name_classmethod(self):

        @plugins.register(Sample)
        class NameTestPlugin(Plugin, TemplateView):
            menu = {"label": "Name", "icon": "name", "order": 50}
            template_name = "name.html"

        assert hasattr(NameTestPlugin, "get_name")
        assert callable(NameTestPlugin.get_name)
        assert NameTestPlugin.get_name() == "name-test-plugin"

    def test_plugin_has_get_url_path_classmethod(self):

        @plugins.register(Sample)
        class PathTestPlugin(Plugin, TemplateView):
            menu = {"label": "Path", "icon": "path", "order": 60}
            template_name = "path.html"

        assert hasattr(PathTestPlugin, "get_url_path")
        assert callable(PathTestPlugin.get_url_path)
        assert PathTestPlugin.get_url_path() == "path-test-plugin"


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
        addresses = {
            "add-person": ({}, "/projects/abc/contributors/add-person/"),
            "add-organization": ({}, "/projects/abc/contributors/add-organization/"),
            "edit": ({"pk": 7}, "/projects/abc/contributors/7/edit/"),
            "remove": ({"pk": 7}, "/projects/abc/contributors/7/remove/"),
            "move": ({"pk": 7}, "/projects/abc/contributors/7/move/"),
        }

        for name, (kwargs, expected) in addresses.items():
            url = reverse(
                f"project:contribution-list-contribution-{name}",
                kwargs={"uuid": "abc", **kwargs},
            )
            assert url == expected, name


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
            reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
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

    def test_the_declared_surface_is_all_an_author_needs(self):
        import fairdm.contrib.plugins as api

        for name in ("Plugin", "register", "registry", "is_instance_of", "has_perm"):
            assert hasattr(api, name), name


@pytest.mark.django_db
class TestARecordWithoutAUuid:
    def test_a_location_plugin_resolves_and_reverses(self):
        from django.urls import reverse as django_reverse

        from fairdm.contrib.location.models import Point
        from fairdm.contrib.plugins import reverse as plugin_reverse

        django_reverse("point:point-overview", kwargs={"lon": "1", "lat": "2"})

        point = PointFactory()
        url = plugin_reverse(point, "point-overview")
        assert str(point.x) in url
        assert str(point.y) in url

        assert plugins.registry.lookup_for(Point) == {"lon": "x", "lat": "y"}


@pytest.mark.django_db
class TestNavigationUnchanged:
    def test_the_navigation_lists_the_pages_and_not_an_action_beside_them(self):
        @plugins.register(Sample, label="Listed Page")
        class ListedPage(Plugin, TemplateView):
            template_name = "base.html"

        @plugins.register(Sample, label="Follow Action", place="action")
        class FollowAction(Plugin, TemplateView):
            template_name = "base.html"

        plugins.registry.get_urls_for_model(Sample)

        menu = plugins.registry.get_plugin_menu_for_model(Sample)
        labels = [item.extra_context["label"] for item in menu.children]
        assert "Listed Page" in labels
        assert "Follow Action" not in labels

    def test_the_action_is_served_under_its_own_name(self):
        @plugins.register(Sample, place="action")
        class WatchAction(Plugin, TemplateView):
            url_path = "watch"
            template_name = "base.html"

        patterns = plugins.registry.get_urls_for_model(Sample)

        (pattern,) = [p for p in patterns if p.name == "watch-action"]
        assert str(pattern.pattern) == "watch/"
        assert pattern.callback.view_initkwargs["registered_model"] is Sample

    def test_a_registration_with_no_place_is_listed_as_before(self):
        @plugins.register(Sample, label="Plain Page")
        class PlainPage(Plugin, TemplateView):
            template_name = "base.html"

        plugins.registry.get_urls_for_model(Sample)

        menu = plugins.registry.get_plugin_menu_for_model(Sample)
        assert "Plain Page" in [item.extra_context["label"] for item in menu.children]


class SomeOverview(OverviewPlaces, Plugin, TemplateView):
    template_name = "base.html"


class OwnAddressOverview(OverviewPlaces, Plugin, TemplateView):
    url_path = None
    template_name = "base.html"


class SampleStyleOverview(OverviewPlaces, Plugin, TemplateView):
    url_path = "overview"
    template_name = "base.html"


class UnbuiltOverview(Plugin, TemplateView):
    url_path = None
    template_name = "base.html"


class Detail(Plugin, TemplateView):
    template_name = "base.html"


class ActivityPage(Plugin, TemplateView):
    template_name = "base.html"
    extra_views = [Detail]


class WatchAction(Plugin, TemplateView):
    template_name = "base.html"
    extra_views = [Detail]


class ActivityCard(Card):
    template_name = "plugin_cards/card.html"
    extra_views = [Detail]


PLACES = {
    "navigation": (ActivityPage, {"label": "Activity"}),
    "action": (WatchAction, {"place": "action"}),
    "card": (ActivityCard, {"place": "card"}),
}


def offering_registry():
    """A registry whose Sample overview draws the places, as the shipped one does.

    It builds its navigation in menus of its own, so the shipped navigation, which is shared by
    every test, is not rewritten from the few plugins registered here.
    """
    registry = PluginRegistry()
    menus = {}

    def own_menu(model):
        if model not in menus:
            menus[model] = Menu(f"{model.__name__}Menu")
            # A Menu joins the shared root when it is made.
            menus[model].parent = None
        return menus[model]

    registry.get_plugin_menu_for_model = own_menu
    registry.register(Sample)(SomeOverview)
    return registry


def served_names(registry, model):
    """The URL names a record type's patterns carry."""
    return [p.name for p in registry.get_urls_for_model(model)]


def entry_labels(registry, model):
    """The labels of a record type's navigation entries, after its patterns are built."""
    registry.get_urls_for_model(model)
    menu = registry.get_plugin_menu_for_model(model)
    return [item.extra_context["label"] for item in menu.children]


@pytest.fixture
def offering():
    return offering_registry()


@pytest.mark.parametrize("place", PLACES)
class TestRemove:
    def test_a_removed_plugin_has_no_mount_pattern_entry_action_or_card(
        self, offering, place
    ):
        plugin_class, options = PLACES[place]
        offering.register(Sample, **options)(plugin_class)

        offering.remove(Sample, plugin_class)

        name = plugin_class.get_name()
        assert name not in [m.name for m in offering.resolve(Sample)]
        assert not [n for n in served_names(offering, Sample) if n.startswith(name)]
        assert "Activity" not in entry_labels(offering, Sample)
        assert plugin_class not in [
            m.plugin_class for m in offering.get_page_actions(Sample)
        ]
        assert plugin_class not in [m.plugin_class for m in offering.get_cards(Sample)]

    def test_a_removal_may_name_the_plugin_by_its_name(self, offering, place):
        plugin_class, options = PLACES[place]
        offering.register(Sample, **options)(plugin_class)

        offering.remove(Sample, plugin_class.get_name())

        assert plugin_class.get_name() not in [m.name for m in offering.resolve(Sample)]

    def test_removed_from_one_record_type_it_is_still_mounted_on_another(
        self, offering, place
    ):
        plugin_class, options = PLACES[place]
        offering.register(Dataset)(SomeOverview)
        offering.register(Sample, **options)(plugin_class)
        offering.register(Dataset, **options)(plugin_class)

        offering.remove(Sample, plugin_class)

        assert plugin_class.get_name() not in [m.name for m in offering.resolve(Sample)]
        assert plugin_class.get_name() in [m.name for m in offering.resolve(Dataset)]
        assert [
            n
            for n in served_names(offering, Dataset)
            if n.startswith(plugin_class.get_name())
        ]

    def test_the_result_is_the_same_whether_remove_or_register_came_first(
        self, place
    ):
        plugin_class, options = PLACES[place]
        before, after = offering_registry(), offering_registry()

        before.remove(Sample, plugin_class)
        before.register(Sample, **options)(plugin_class)
        after.register(Sample, **options)(plugin_class)
        after.remove(Sample, plugin_class)

        assert before.resolve(Sample) == after.resolve(Sample)
        assert served_names(before, Sample) == served_names(after, Sample)
        assert entry_labels(before, Sample) == entry_labels(after, Sample)

    def test_the_registration_is_still_declared(self, offering, place):
        plugin_class, options = PLACES[place]
        offering.register(Sample, **options)(plugin_class)

        offering.remove(Sample, plugin_class)

        assert (plugin_class, options) in offering.get_plugins_for_model(Sample)

    def test_removing_does_not_stop_the_portal_starting(self, offering, place):
        plugin_class, options = PLACES[place]
        offering.register(Sample, **options)(plugin_class)
        offering.remove(Sample, plugin_class)

        offering.validate_all()


class TestRemoveRefusals:
    def test_remove_itself_checks_nothing(self, offering):
        offering.remove(Sample, "nothing-called-this")
        offering.remove(Project, ActivityPage)

    def test_a_removal_of_something_not_registered_is_refused_naming_both(
        self, offering
    ):
        offering.register(Dataset)(SomeOverview)
        offering.register(Dataset)(ActivityPage)
        offering.remove(Sample, ActivityPage)

        with pytest.raises(PluginRegistrationError) as excinfo:
            offering.validate_all()

        assert "activity-page" in str(excinfo.value)
        assert "Sample" in str(excinfo.value)

    def test_a_removal_on_a_record_type_with_no_registration_is_refused(self):
        registry = PluginRegistry()
        registry.remove(Sample, "activity-page")

        with pytest.raises(PluginRegistrationError, match="Sample"):
            registry.validate_all()

    def test_a_removal_declared_before_the_plugin_is_refused_when_it_never_arrives(
        self, offering
    ):
        offering.remove(Sample, "late-arrival")

        with pytest.raises(PluginRegistrationError, match="late-arrival"):
            offering.resolve(Sample)

    @pytest.mark.parametrize(
        ("record_type", "overview"),
        [(Project, OwnAddressOverview), (Sample, SampleStyleOverview)],
        ids=["project", "sample"],
    )
    def test_the_overview_cannot_be_removed_and_the_refusal_says_it_can_be_replaced(
        self, record_type, overview
    ):
        registry = PluginRegistry()
        registry.register(record_type)(overview)
        registry.remove(record_type, overview)

        with pytest.raises(PluginRegistrationError) as excinfo:
            registry.validate_all()

        message = str(excinfo.value)
        assert record_type.__name__ in message
        assert overview.get_name() in message
        assert "replace" in message

    def test_a_page_served_at_the_record_s_own_address_counts_as_its_overview(self):
        registry = PluginRegistry()
        registry.register(Project)(UnbuiltOverview)
        registry.remove(Project, UnbuiltOverview)

        with pytest.raises(PluginRegistrationError, match="replace"):
            registry.validate_all()
