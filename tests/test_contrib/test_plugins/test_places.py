"""Tests for the place a registration names and for what a record type serves."""

import pytest
from django.views.generic import TemplateView

from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.cards import Card
from fairdm.contrib.plugins.checks import PluginRegistrationError
from fairdm.contrib.plugins.places import OverviewPlaces, Place
from fairdm.contrib.plugins.registration import PluginRegistry
from fairdm.core.dataset.models import Dataset
from fairdm.core.sample.models import Sample
from fairdm.contrib.location.models import Point


class AlphaPage(Plugin, TemplateView):
    template_name = "base.html"


class BetaPage(Plugin, TemplateView):
    template_name = "base.html"


class FollowAction(Plugin, TemplateView):
    template_name = "base.html"


class ReportAction(Plugin, TemplateView):
    template_name = "base.html"


class SharedSegment(Plugin, TemplateView):
    url_path = "elsewhere"
    template_name = "base.html"


class SomeOverview(OverviewPlaces, Plugin, TemplateView):
    template_name = "base.html"


class ActivityCard(Card):
    template_name = "plugin_cards/card.html"


def offering_registry():
    """A registry whose Sample overview draws page actions, as the shipped one does."""
    registry = PluginRegistry()
    registry.register(Sample)(SomeOverview)
    return registry


def mount_of(registry, plugin_class):
    """The mount Sample serves for one plugin class."""
    return next(m for m in registry.resolve(Sample) if m.plugin_class is plugin_class)


@pytest.fixture
def fresh():
    """An empty registry the test fills."""
    return PluginRegistry()


@pytest.fixture
def offering():
    return offering_registry()


class TestPlaceOption:
    def test_a_registration_with_no_place_gets_a_navigation_mount(self, fresh):
        fresh.register(Sample)(AlphaPage)

        (mount,) = fresh.resolve(Sample)

        assert mount.place is Place.NAVIGATION

    @pytest.mark.parametrize("place", ["action", Place.ACTION])
    def test_the_action_place_is_accepted_as_a_string_or_a_member(
        self, offering, place
    ):
        offering.register(Sample, place=place)(FollowAction)

        assert mount_of(offering, FollowAction).place is Place.ACTION

    def test_an_action_has_the_defaults_a_navigation_entry_has(self, offering):
        other = offering_registry()
        offering.register(Sample)(FollowAction)
        other.register(Sample, place="action")(FollowAction)

        page = mount_of(offering, FollowAction)
        action = mount_of(other, FollowAction)

        assert (action.label, action.icon, action.order) == (
            page.label,
            page.icon,
            page.order,
        )

    def test_an_unknown_place_is_refused_when_registered(self, fresh):
        with pytest.raises(PluginRegistrationError, match="FollowAction"):
            fresh.register(Sample, place="sidebar")(FollowAction)

        assert fresh.get_plugins_for_model(Sample) == []

    @pytest.mark.parametrize("place", [None, "action"])
    def test_a_column_on_something_that_is_not_a_card_is_refused(self, fresh, place):
        options = {"column": "wide"}
        if place:
            options["place"] = place

        with pytest.raises(PluginRegistrationError, match="FollowAction"):
            fresh.register(Sample, **options)(FollowAction)

        assert fresh.get_plugins_for_model(Sample) == []


class TestResolve:
    def test_each_registration_is_one_mount_carrying_its_declaration(self, offering):
        offering.register(Sample, label="Alpha", icon="star", order=30)(AlphaPage)
        offering.register(Sample, place="action", label="Follow", icon="bell", order=5)(
            FollowAction
        )

        by_name = {mount.name: mount for mount in offering.resolve(Sample)}

        assert set(by_name) == {"some-overview", "alpha-page", "follow-action"}
        alpha = by_name["alpha-page"]
        assert alpha.plugin_class is AlphaPage
        assert alpha.url_path == "alpha-page"
        assert (alpha.label, alpha.icon, alpha.order) == ("Alpha", "star", 30)
        follow = by_name["follow-action"]
        assert follow.plugin_class is FollowAction
        assert follow.url_path == "follow-action"
        assert (follow.label, follow.icon, follow.order) == ("Follow", "bell", 5)

    def test_a_plugin_without_a_base_path_has_no_segment(self, fresh):
        class Own(Plugin, TemplateView):
            url_path = None
            template_name = "base.html"

        fresh.register(Sample)(Own)

        (mount,) = fresh.resolve(Sample)

        assert mount.url_path is None

    def test_declining_the_entry_gives_a_mount_that_is_served_and_not_listed(
        self, fresh
    ):
        fresh.register(Sample, menu=False)(AlphaPage)
        fresh.register(Sample)(BetaPage)

        by_name = {mount.name: mount for mount in fresh.resolve(Sample)}

        assert by_name["alpha-page"].listed is False
        assert by_name["beta-page"].listed is True

    def test_resolving_twice_gives_the_same_list(self, offering):
        offering.register(Sample)(AlphaPage)
        offering.register(Sample, place="action")(FollowAction)

        assert offering.resolve(Sample) == offering.resolve(Sample)

    def test_resolving_leaves_the_declarations_as_made(self, offering):
        offering.register(Sample, place="action", order=3)(FollowAction)

        offering.resolve(Sample)

        assert offering.get_plugins_for_model(Sample) == [
            (SomeOverview, {}),
            (FollowAction, {"place": "action", "order": 3}),
        ]

    def test_a_record_type_with_no_registrations_serves_nothing(self, fresh):
        assert fresh.resolve(Sample) == []

    def test_each_record_type_resolves_its_own_registrations(self, fresh):
        fresh.register(Sample)(AlphaPage)
        fresh.register(Dataset)(BetaPage)

        assert [m.name for m in fresh.resolve(Sample)] == ["alpha-page"]
        assert [m.name for m in fresh.resolve(Dataset)] == ["beta-page"]

    def test_a_segment_of_none_is_never_compared(self, fresh):
        class OwnOne(Plugin, TemplateView):
            url_path = None
            template_name = "base.html"

        class OwnTwo(Plugin, TemplateView):
            url_path = None
            template_name = "base.html"

        fresh.register(Sample)(OwnOne)
        fresh.register(Sample)(OwnTwo)

        assert len(fresh.resolve(Sample)) == 2

    def test_two_plugins_claiming_one_segment_are_refused_when_resolved(self, fresh):
        fresh._registry[Sample] = [
            (AlphaPage, {}),
            (SharedSegment, {}),
            (type("Twin", (SharedSegment,), {}), {}),
        ]

        with pytest.raises(PluginRegistrationError, match="Sample"):
            fresh.resolve(Sample)


class TestPageActions:
    def test_only_action_mounts_are_returned(self, offering):
        offering.register(Sample)(AlphaPage)
        offering.register(Sample, place="action")(FollowAction)

        assert [m.plugin_class for m in offering.get_page_actions(Sample)] == [
            FollowAction
        ]

    def test_an_action_that_declined_its_entry_is_not_offered(self, offering):
        offering.register(Sample, place="action", menu=False)(FollowAction)
        offering.register(Sample, place="action")(ReportAction)

        assert [m.plugin_class for m in offering.get_page_actions(Sample)] == [
            ReportAction
        ]

    def test_actions_are_in_order_and_then_name(self, offering):
        offering.register(Sample, place="action", order=20)(FollowAction)
        offering.register(Sample, place="action", order=10)(ReportAction)
        offering.register(Sample, place="action", order=10)(AlphaPage)

        names = [m.name for m in offering.get_page_actions(Sample)]

        assert names == ["alpha-page", "report-action", "follow-action"]

    def test_the_list_is_the_same_whichever_order_they_were_registered_in(self):
        forward, backward = offering_registry(), offering_registry()
        classes = [FollowAction, ReportAction, AlphaPage, BetaPage]
        for cls in classes:
            forward.register(Sample, place="action")(cls)
        for cls in reversed(classes):
            backward.register(Sample, place="action")(cls)

        assert forward.get_page_actions(Sample) == backward.get_page_actions(Sample)


class TestRecordTypeOffersPlaces:
    def test_an_action_against_a_record_type_with_no_overview_places_is_refused(
        self, fresh
    ):
        fresh.register(Point)(AlphaPage)
        fresh.register(Point, place="action")(FollowAction)

        with pytest.raises(PluginRegistrationError) as excinfo:
            fresh.validate_all()

        assert "FollowAction" in str(excinfo.value)
        assert "Point" in str(excinfo.value)

    def test_the_same_action_against_a_record_type_that_draws_them_is_accepted(
        self, fresh
    ):
        fresh.register(Sample)(SomeOverview)
        fresh.register(Sample, place="action")(FollowAction)

        fresh.validate_all()

    def test_a_card_against_a_record_type_with_no_overview_places_is_refused(
        self, fresh
    ):
        fresh.register(Point)(AlphaPage)
        fresh.register(Point, place="card")(ActivityCard)

        with pytest.raises(PluginRegistrationError) as excinfo:
            fresh.validate_all()

        assert "ActivityCard" in str(excinfo.value)
        assert "Point" in str(excinfo.value)

    def test_the_same_card_against_a_record_type_that_draws_them_is_accepted(
        self, fresh
    ):
        fresh.register(Sample)(SomeOverview)
        fresh.register(Sample, place="card")(ActivityCard)

        fresh.validate_all()

    def test_pages_alone_need_no_overview_places(self, fresh):
        fresh.register(Point)(AlphaPage)

        fresh.validate_all()


class TestServedUnderAMount:
    def test_the_patterns_use_the_name_and_segment_of_the_mount(self):
        patterns = AlphaPage.get_urls(model=Sample, name="alias", url_path="there")

        assert [p.name for p in patterns] == ["alias"]
        assert [str(p.pattern) for p in patterns] == ["there/"]

    def test_a_mount_without_a_segment_is_served_at_the_record_s_own_address(self):
        patterns = AlphaPage.get_urls(model=Sample, url_path=None)

        assert [str(p.pattern) for p in patterns] == [""]
