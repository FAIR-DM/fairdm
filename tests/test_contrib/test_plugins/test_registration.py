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
from fairdm.contrib.plugins.places import Column, OverviewPlaces, Place
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


class Export(Plugin, TemplateView):
    template_name = "base.html"


class OtherPage(Plugin, TemplateView):
    template_name = "base.html"


class ShippedMap(Plugin, TemplateView):
    url_path = "map"
    template_name = "base.html"
    extra_views = [Detail]


class BetterMap(ShippedMap):
    """Built on the one it replaces, so it keeps its segment and its further views."""


class RicherMap(Plugin, TemplateView):
    template_name = "base.html"
    extra_views = [Export]


class RivalMap(Plugin, TemplateView):
    template_name = "base.html"


class RichestMap(Plugin, TemplateView):
    template_name = "base.html"


class RicherActivityPage(Plugin, TemplateView):
    template_name = "base.html"


class RicherWatchAction(Plugin, TemplateView):
    template_name = "base.html"


class RicherActivityCard(Card):
    template_name = "plugin_cards/card.html"


class RicherOverview(SomeOverview):
    """Built on the shipped overview, so it keeps what draws the places."""


class RivalOverview(SomeOverview):
    pass


class PlainOverview(Plugin, TemplateView):
    template_name = "base.html"


REPLACEMENTS = {
    "navigation": (RicherActivityPage, {}),
    "action": (RicherWatchAction, {}),
    # A card is a card whether or not it says so, and is refused when it does not.
    "card": (RicherActivityCard, {"place": "card"}),
}


def replaced_registry(place, target_options=None, replacement_options=None):
    """A registry in which one plugin of a place has a replacement.

    Returns:
        The registry, the plugin that is replaced and the one that replaces it.
    """
    registry = offering_registry()
    target, options = PLACES[place]
    replacement, own = REPLACEMENTS[place]
    registry.register(Sample, **{**options, **(target_options or {})})(target)
    registry.register(
        Sample, **{**own, "replaces": target, **(replacement_options or {})}
    )(replacement)
    return registry, target, replacement


def mount_named(registry, name):
    """The mount a record type serves under one name."""
    return next(m for m in registry.resolve(Sample) if m.name == name)


KEPT = {"label": "Mine", "icon": "map", "order": 7}


@pytest.mark.parametrize("place", PLACES)
class TestReplace:
    def test_the_mount_carries_the_replacement_s_class_under_the_target_s_name_and_segment(
        self, place
    ):
        registry, target, replacement = replaced_registry(place)

        mount = mount_named(registry, target.get_name())

        assert mount.plugin_class is replacement
        assert mount.url_path == target.get_url_path()
        assert replacement.get_name() not in [m.name for m in registry.resolve(Sample)]
        assert target not in [m.plugin_class for m in registry.resolve(Sample)]

    def test_the_target_may_be_named_by_its_name(self, place):
        registry, target, replacement = replaced_registry(
            place, replacement_options={"replaces": PLACES[place][0].get_name()}
        )

        assert mount_named(registry, target.get_name()).plugin_class is replacement

    def test_it_appears_in_the_place_of_the_target_whether_or_not_it_says_so(
        self, place
    ):
        registry, target, _ = replaced_registry(place)

        assert mount_named(registry, target.get_name()).place == Place(place)

    def test_stating_nothing_it_keeps_the_target_s_label_icon_order_and_column(
        self, place
    ):
        column = {"column": "wide"} if place == "card" else {}
        registry, target, _ = replaced_registry(place, {**KEPT, **column})

        mount = mount_named(registry, target.get_name())

        assert (mount.label, mount.icon, mount.order) == ("Mine", "map", 7)
        assert mount.column == (Column.WIDE if place == "card" else None)

    @pytest.mark.parametrize(
        ("field", "value"), [("label", "Theirs"), ("icon", "star"), ("order", 3)]
    )
    def test_stating_one_it_uses_that_and_keeps_the_rest(self, place, field, value):
        registry, target, _ = replaced_registry(place, KEPT, {field: value})

        mount = mount_named(registry, target.get_name())

        assert {"label": mount.label, "icon": mount.icon, "order": mount.order} == {
            **KEPT,
            field: value,
        }

    def test_the_replacement_is_the_only_one_of_its_name_among_the_mounts(self, place):
        registry, target, replacement = replaced_registry(place)

        classes = [m.plugin_class for m in registry.resolve(Sample)]

        assert classes.count(replacement) == 1
        assert target not in classes

    def test_replaced_on_one_record_type_the_original_is_mounted_on_another(
        self, place
    ):
        registry, target, replacement = replaced_registry(place)
        registry.register(Dataset)(SomeOverview)
        registry.register(Dataset, **PLACES[place][1])(target)

        (mount,) = [m for m in registry.resolve(Dataset) if m.name == target.get_name()]

        assert mount.plugin_class is target
        assert mount_named(registry, target.get_name()).plugin_class is replacement

    def test_the_registrations_are_still_declared_as_made(self, place):
        registry, target, replacement = replaced_registry(place)

        assert [p for p, _ in registry.get_plugins_for_model(Sample)] == [
            SomeOverview,
            target,
            replacement,
        ]

    def test_the_result_is_the_same_whichever_is_registered_first(self, place):
        target, options = PLACES[place]
        replacement, own = REPLACEMENTS[place]
        target_first, replacement_first = offering_registry(), offering_registry()

        target_first.register(Sample, **options)(target)
        target_first.register(Sample, **own, replaces=target)(replacement)
        replacement_first.register(Sample, **own, replaces=target)(replacement)
        replacement_first.register(Sample, **options)(target)

        assert sorted(target_first.resolve(Sample), key=lambda m: m.name) == sorted(
            replacement_first.resolve(Sample), key=lambda m: m.name
        )

    def test_removing_the_replacement_leaves_the_original_served(self, place):
        registry, target, replacement = replaced_registry(place)

        registry.remove(Sample, replacement)

        assert mount_named(registry, target.get_name()).plugin_class is target


class TestReplaceKeepsOnlyWhatIsStated:
    @pytest.mark.parametrize("place", ["navigation", "action"])
    def test_a_replacement_stating_no_label_does_not_get_one_from_its_own_class_name(
        self, place
    ):
        registry, target, replacement = replaced_registry(place, KEPT)

        mount = mount_named(registry, target.get_name())

        assert mount.label == "Mine"
        assert mount.label != replacement.get_name().replace("-", " ").title()

    @pytest.mark.parametrize("place", ["navigation", "action"])
    def test_a_target_that_declined_its_entry_leaves_the_replacement_unlisted(
        self, place
    ):
        registry, target, _ = replaced_registry(place, {"menu": False})

        assert mount_named(registry, target.get_name()).listed is False
        assert registry.get_page_actions(Sample) == []
        assert "Activity" not in entry_labels(registry, Sample)

    @pytest.mark.parametrize("place", ["navigation", "action"])
    def test_a_replacement_may_state_an_entry_the_target_declined(self, place):
        registry, target, _ = replaced_registry(
            place, {"menu": False}, {"menu": True}
        )

        assert mount_named(registry, target.get_name()).listed is True

    @pytest.mark.parametrize("place", ["navigation", "action"])
    def test_a_replacement_may_decline_the_entry_the_target_listed(self, place):
        registry, target, _ = replaced_registry(place, {}, {"menu": False})

        assert mount_named(registry, target.get_name()).listed is False


class TestReplaceTheNavigation:
    def test_the_navigation_has_one_entry_in_the_target_s_position(self):
        registry = offering_registry()
        registry.register(Sample, label="Activity", order=5)(ActivityPage)
        registry.register(Sample, label="Other", order=9)(OtherPage)
        registry.register(Sample, replaces=ActivityPage)(RicherActivityPage)

        labels = entry_labels(registry, Sample)

        assert labels.count("Activity") == 1
        assert [label for label in labels if label in ("Activity", "Other")] == [
            "Activity",
            "Other",
        ]

    def test_the_entry_leads_to_the_target_s_name(self):
        registry = offering_registry()
        registry.register(Sample, label="Activity")(ActivityPage)
        registry.register(Sample, replaces=ActivityPage)(RicherActivityPage)

        registry.get_urls_for_model(Sample)
        menu = registry.get_plugin_menu_for_model(Sample)

        (entry,) = [i for i in menu.children if i.extra_context["label"] == "Activity"]
        assert entry.view_name == f"sample:{ActivityPage.get_name()}"


class TestReplaceFurtherViews:
    def test_the_replaced_class_contributes_no_patterns_and_the_replacement_is_served_at_its_address(
        self,
    ):
        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(RicherMap)

        patterns = {p.name: p for p in registry.get_urls_for_model(Sample)}

        assert str(patterns["shipped-map"].pattern) == "map/"
        assert patterns["shipped-map"].callback.view_class is RicherMap
        assert "shipped-map-detail" not in patterns
        assert "richer-map" not in patterns

    def test_the_replacement_s_own_further_views_are_named_beneath_the_target_s(
        self,
    ):
        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(RicherMap)

        patterns = {p.name: p for p in registry.get_urls_for_model(Sample)}

        assert str(patterns["shipped-map-export"].pattern) == "map/export/"
        assert patterns["shipped-map-export"].callback.view_class is Export
        assert (
            patterns["shipped-map-export"].callback.view_initkwargs["plugin_class"]
            is RicherMap
        )

    def test_a_replacement_built_on_the_target_serves_the_views_it_declares_at_the_same_segments(
        self,
    ):
        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(BetterMap)

        patterns = {p.name: p for p in registry.get_urls_for_model(Sample)}

        assert str(patterns["shipped-map-detail"].pattern) == "map/detail/"
        assert (
            patterns["shipped-map-detail"].callback.view_initkwargs["plugin_class"]
            is BetterMap
        )

    @pytest.mark.parametrize("target_first", [True, False])
    def test_a_replacement_with_the_target_s_own_segment_is_accepted_in_either_order(
        self, target_first
    ):
        registry = offering_registry()
        arrivals = [
            lambda: registry.register(Sample)(ShippedMap),
            lambda: registry.register(Sample, replaces=ShippedMap)(BetterMap),
        ]
        for arrive in arrivals if target_first else reversed(arrivals):
            arrive()

        registry.validate_all()
        patterns = {p.name: p for p in registry.get_urls_for_model(Sample)}
        assert patterns["shipped-map"].callback.view_class is BetterMap
        assert "better-map" not in patterns

    def test_the_two_orders_serve_the_same_addresses(self):
        target_first, replacement_first = offering_registry(), offering_registry()
        target_first.register(Sample)(ShippedMap)
        target_first.register(Sample, replaces=ShippedMap)(BetterMap)
        replacement_first.register(Sample, replaces=ShippedMap)(BetterMap)
        replacement_first.register(Sample)(ShippedMap)

        def served(registry):
            return sorted(
                (p.name, str(p.pattern)) for p in registry.get_urls_for_model(Sample)
            )

        assert served(target_first) == served(replacement_first)

    def test_a_plugin_that_arrives_after_a_replacement_may_not_take_its_target_s_segment(
        self,
    ):
        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(BetterMap)

        class Squatter(Plugin, TemplateView):
            url_path = "map"
            template_name = "base.html"

        with pytest.raises(PluginRegistrationError, match="map"):
            registry.register(Sample)(Squatter)

    def test_a_replacement_s_own_name_must_still_be_unique(self):
        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(BetterMap)

        with pytest.raises(PluginRegistrationError, match="better-map"):
            registry.register(Sample)(BetterMap)


class TestReplaceAReplacement:
    def test_a_replacement_of_a_replacement_is_served_at_the_first_plugin_s_address(
        self,
    ):
        registry = offering_registry()
        registry.register(Sample, label="First", icon="a", order=1)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap, label="Second", icon="b")(
            RicherMap
        )
        registry.register(Sample, replaces="richer-map", icon="c")(RichestMap)

        mount = mount_named(registry, "shipped-map")

        assert mount.plugin_class is RichestMap
        assert mount.url_path == "map"
        assert len([m for m in registry.resolve(Sample) if m.name == "shipped-map"]) == 1
        assert len(registry.resolve(Sample)) == 2

    def test_each_link_keeps_what_the_one_before_it_had_unless_it_states_its_own(self):
        registry = offering_registry()
        registry.register(Sample, label="First", icon="a", order=1)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap, label="Second", icon="b")(
            RicherMap
        )
        registry.register(Sample, replaces="richer-map", icon="c")(RichestMap)

        mount = mount_named(registry, "shipped-map")

        assert (mount.label, mount.icon, mount.order) == ("Second", "c", 1)

    def test_the_result_is_the_same_in_any_order_of_arrival(self):
        arrivals = [
            lambda r: r.register(Sample)(ShippedMap),
            lambda r: r.register(Sample, replaces=ShippedMap)(RicherMap),
            lambda r: r.register(Sample, replaces="richer-map")(RichestMap),
        ]
        results = []
        for order in ([0, 1, 2], [2, 1, 0], [1, 2, 0]):
            registry = offering_registry()
            for index in order:
                arrivals[index](registry)
            results.append(registry.resolve(Sample))

        assert results[0] == results[1] == results[2]

    def test_only_the_last_link_is_served(self):
        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(RicherMap)
        registry.register(Sample, replaces="richer-map")(RichestMap)

        patterns = {p.name: p for p in registry.get_urls_for_model(Sample)}

        assert patterns["shipped-map"].callback.view_class is RichestMap
        assert "shipped-map-export" not in patterns

    def test_the_middle_link_can_be_removed_only_with_what_replaced_it(self):
        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(RicherMap)
        registry.register(Sample, replaces="richer-map")(RichestMap)

        registry.remove(Sample, RichestMap)

        assert mount_named(registry, "shipped-map").plugin_class is RicherMap


class TestReplaceTheOverview:
    def test_a_replacement_built_on_the_shipped_overview_still_draws_the_places(self):
        registry = PluginRegistry()
        registry.register(Sample)(SomeOverview)
        registry.register(Sample, replaces=SomeOverview)(RicherOverview)
        registry.register(Sample, place="action")(WatchAction)
        registry.register(Sample, place="card")(ActivityCard)

        registry.validate_all()

        assert mount_named(registry, SomeOverview.get_name()).plugin_class is (
            RicherOverview
        )
        assert [m.plugin_class for m in registry.get_page_actions(Sample)] == [
            WatchAction
        ]
        assert [m.plugin_class for m in registry.get_cards(Sample)] == [ActivityCard]

    def test_a_replacement_overview_can_be_removed_and_the_shipped_one_is_served_again(
        self,
    ):
        registry = PluginRegistry()
        registry.register(Sample)(SomeOverview)
        registry.register(Sample, replaces=SomeOverview)(RicherOverview)

        registry.remove(Sample, RicherOverview)

        registry.validate_all()
        assert registry.resolve(Sample)[0].plugin_class is SomeOverview

    def test_the_overview_still_cannot_be_removed_when_nothing_replaces_it(self):
        registry = PluginRegistry()
        registry.register(Sample)(SomeOverview)
        registry.register(Sample)(RivalOverview)
        registry.remove(Sample, SomeOverview)

        with pytest.raises(PluginRegistrationError, match="replace"):
            registry.validate_all()


class TestReplaceRefusals:
    def test_two_replacements_for_one_plugin_are_refused_naming_both(self):
        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(RicherMap)
        registry.register(Sample, replaces=ShippedMap)(RivalMap)

        with pytest.raises(PluginRegistrationError) as excinfo:
            registry.validate_all()

        message = str(excinfo.value)
        assert "RicherMap" in message
        assert "RivalMap" in message
        assert "shipped-map" in message
        assert "Sample" in message

    def test_one_of_the_two_removed_the_other_stands_for_a_page(self):
        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(RicherMap)
        registry.register(Sample, replaces=ShippedMap)(RivalMap)
        registry.remove(Sample, RivalMap)

        registry.validate_all()

        assert mount_named(registry, "shipped-map").plugin_class is RicherMap

    def test_one_of_the_two_removed_the_other_stands_for_a_record_type_s_overview(
        self,
    ):
        registry = PluginRegistry()
        registry.register(Sample)(SomeOverview)
        registry.register(Sample, replaces=SomeOverview)(RicherOverview)
        registry.register(Sample, replaces=SomeOverview)(RivalOverview)
        registry.remove(Sample, RicherOverview)

        registry.validate_all()

        assert mount_named(registry, SomeOverview.get_name()).plugin_class is (
            RivalOverview
        )

    def test_the_conflict_is_settled_whichever_of_removal_and_registration_came_first(
        self,
    ):
        registry = offering_registry()
        registry.remove(Sample, RivalMap)
        registry.register(Sample, replaces=ShippedMap)(RivalMap)
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(RicherMap)

        registry.validate_all()

        assert mount_named(registry, "shipped-map").plugin_class is RicherMap

    def test_a_target_not_registered_against_the_record_type_is_refused_naming_both(
        self,
    ):
        registry = offering_registry()
        registry.register(Dataset)(SomeOverview)
        registry.register(Dataset)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(RicherMap)

        with pytest.raises(PluginRegistrationError) as excinfo:
            registry.validate_all()

        message = str(excinfo.value)
        assert "RicherMap" in message
        assert "Sample" in message
        assert "shipped-map" in message

    def test_a_target_that_never_arrives_is_refused(self):
        registry = offering_registry()
        registry.register(Sample, replaces="never-registered")(RicherMap)

        with pytest.raises(PluginRegistrationError, match="never-registered"):
            registry.resolve(Sample)

    def test_a_target_that_is_removed_is_refused_naming_the_replacement_and_the_removal(
        self,
    ):
        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(RicherMap)
        registry.remove(Sample, ShippedMap)

        with pytest.raises(PluginRegistrationError) as excinfo:
            registry.validate_all()

        message = str(excinfo.value)
        assert "RicherMap" in message
        assert "Sample" in message
        assert "removal" in message
        assert "shipped-map" in message

    @pytest.mark.parametrize(
        ("target", "options", "replacement", "own"),
        [
            (ActivityPage, {}, RicherActivityCard, {"place": "card"}),
            (ActivityCard, {"place": "card"}, RicherActivityPage, {}),
            (WatchAction, {"place": "action"}, RicherActivityPage, {"place": "navigation"}),
            (ActivityPage, {}, RicherWatchAction, {"place": "action"}),
        ],
        ids=["card-for-page", "page-for-card", "page-for-action", "action-for-page"],
    )
    def test_a_replacement_in_a_different_place_is_refused_naming_both(
        self, target, options, replacement, own
    ):
        registry = offering_registry()
        registry.register(Sample, **options)(target)
        registry.register(Sample, replaces=target, **own)(replacement)

        with pytest.raises(PluginRegistrationError) as excinfo:
            registry.validate_all()

        message = str(excinfo.value)
        assert replacement.__name__ in message
        assert target.get_name() in message
        assert "Sample" in message

    def test_a_card_that_says_nothing_of_its_place_does_not_take_a_page_s(self):
        registry = offering_registry()
        registry.register(Sample)(ActivityPage)

        with pytest.raises(PluginRegistrationError, match="card"):
            registry.register(Sample, replaces=ActivityPage)(RicherActivityCard)

    def test_replacements_that_replace_each_other_are_refused_naming_both(self):
        registry = offering_registry()
        registry.register(Sample, replaces="rival-map")(RicherMap)
        registry.register(Sample, replaces="richer-map")(RivalMap)

        with pytest.raises(PluginRegistrationError) as excinfo:
            registry.validate_all()

        message = str(excinfo.value)
        assert "RicherMap" in message
        assert "RivalMap" in message
        assert "Sample" in message

    def test_a_plugin_that_replaces_itself_is_refused(self):
        registry = offering_registry()
        registry.register(Sample, replaces="richer-map")(RicherMap)

        with pytest.raises(PluginRegistrationError, match="RicherMap"):
            registry.validate_all()

    def test_a_replacement_whose_further_views_clash_with_another_plugin_is_refused(
        self,
    ):
        class ShippedMapExport(Plugin, TemplateView):
            template_name = "base.html"

        registry = offering_registry()
        registry.register(Sample)(ShippedMap)
        registry.register(Sample, replaces=ShippedMap)(RicherMap)
        registry.register(Sample)(ShippedMapExport)

        with pytest.raises(PluginRegistrationError) as excinfo:
            registry.validate_all()

        message = str(excinfo.value)
        assert "shipped-map-export" in message
        assert "Sample" in message

    def test_a_replacement_overview_not_built_on_the_shipped_one_cannot_draw_an_action(
        self,
    ):
        registry = PluginRegistry()
        registry.register(Sample)(SomeOverview)
        registry.register(Sample, replaces=SomeOverview)(PlainOverview)
        registry.register(Sample, place="action")(WatchAction)

        with pytest.raises(PluginRegistrationError) as excinfo:
            registry.validate_all()

        message = str(excinfo.value)
        assert "WatchAction" in message
        assert "Sample" in message

    def test_a_replacement_that_inherits_its_target_s_name_is_refused_as_a_duplicate(
        self,
    ):
        class NamedMap(Plugin, TemplateView):
            name = "named-map"
            template_name = "base.html"

        class InheritingMap(NamedMap):
            pass

        registry = offering_registry()
        registry.register(Sample)(NamedMap)

        with pytest.raises(PluginRegistrationError, match="named-map"):
            registry.register(Sample, replaces=NamedMap)(InheritingMap)


class TestReplaceACard:
    def test_a_replacement_card_stating_a_column_uses_it(self):
        registry, target, _ = replaced_registry(
            "card", {"column": "wide"}, {"column": "side"}
        )

        assert mount_named(registry, target.get_name()).column == Column.SIDE

    def test_the_replacement_is_the_one_card_offered(self):
        registry, _, replacement = replaced_registry("card")

        assert [m.plugin_class for m in registry.get_cards(Sample)] == [replacement]


class TestReplaceAnAction:
    def test_the_replacement_is_the_one_action_offered(self):
        registry, _, replacement = replaced_registry("action")

        assert [m.plugin_class for m in registry.get_page_actions(Sample)] == [
            replacement
        ]
