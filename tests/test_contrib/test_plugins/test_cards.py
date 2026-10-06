"""Tests for overview cards: what a registration may say, what a record type serves, how one is drawn."""

import pytest
from bs4 import BeautifulSoup
from django.views.generic import TemplateView
from fairdm.contrib.plugins.cards import Card

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.checks import PluginRegistrationError
from fairdm.contrib.plugins.places import Column, OverviewPlaces, Place
from fairdm.contrib.plugins.registration import PluginRegistry
from fairdm.core.sample.models import Sample

CARD_TEMPLATE = "plugin_cards/card.html"


def make_card(name, **attributes):
    """Build a card class named ``name`` that draws the shared test template."""
    return type(name, (LabelledCard,), {"label": name, **attributes})


class LabelledCard(Card):
    """A card that draws the shared test template under its own label."""

    template_name = CARD_TEMPLATE
    label = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["label"] = self.label
        return context


class ActivityCard(LabelledCard):
    label = "activity"


class SummaryCard(LabelledCard):
    label = "summary"


class NotesCard(LabelledCard):
    label = "notes"


class AlphaPage(Plugin, TemplateView):
    template_name = "base.html"


class FollowAction(Plugin, TemplateView):
    template_name = "base.html"


class SomeOverview(OverviewPlaces, Plugin, TemplateView):
    template_name = "base.html"


def offering_registry():
    """A registry whose Sample overview draws the places, as the shipped one does."""
    registry = PluginRegistry()
    registry.register(Sample)(SomeOverview)
    return registry


def mount_of(registry, plugin_class):
    """The mount Sample serves for one plugin class."""
    return next(m for m in registry.resolve(Sample) if m.plugin_class is plugin_class)


@pytest.fixture
def offering():
    return offering_registry()


class TestCardRegistration:
    def test_a_class_that_cannot_be_drawn_is_refused_as_a_card(self, offering):
        with pytest.raises(PluginRegistrationError, match="AlphaPage"):
            offering.register(Sample, place="card")(AlphaPage)

        assert offering.get_plugins_for_model(Sample) == [(SomeOverview, {})]

    def test_a_card_with_no_template_and_no_drawing_of_its_own_is_refused(
        self, offering
    ):
        class Blank(Card):
            pass

        with pytest.raises(PluginRegistrationError, match="Blank"):
            offering.register(Sample, place="card")(Blank)

    def test_a_card_that_draws_itself_needs_no_template(self, offering):
        class Inline(Card):
            def render_card(self, request, record):
                return "<p>drawn</p>"

        offering.register(Sample, place="card")(Inline)

        assert mount_of(offering, Inline).place is Place.CARD

    def test_a_card_cannot_be_registered_as_a_page_or_an_action(self, offering):
        for place in (None, "action"):
            options = {"place": place} if place else {}
            with pytest.raises(PluginRegistrationError, match="ActivityCard"):
                offering.register(Sample, **options)(ActivityCard)

    def test_a_card_with_no_segment_of_its_own_is_refused_when_registered(
        self, offering
    ):
        segmentless = make_card("SegmentlessCard", url_path=None)

        with pytest.raises(PluginRegistrationError, match="SegmentlessCard") as excinfo:
            offering.register(Sample, place="card")(segmentless)

        assert "segment" in str(excinfo.value)
        assert segmentless not in [
            cls for cls, _ in offering.get_plugins_for_model(Sample)
        ]

    def test_a_card_with_no_column_resolves_to_the_side_column(self, offering):
        offering.register(Sample, place="card")(ActivityCard)

        assert mount_of(offering, ActivityCard).column is Column.SIDE

    @pytest.mark.parametrize("column", ["wide", Column.WIDE])
    def test_the_wide_column_is_accepted_as_a_string_or_a_member(
        self, offering, column
    ):
        offering.register(Sample, place="card", column=column)(ActivityCard)

        assert mount_of(offering, ActivityCard).column is Column.WIDE

    def test_a_page_has_no_column(self, offering):
        offering.register(Sample)(AlphaPage)
        offering.register(Sample, place="action")(FollowAction)

        assert mount_of(offering, AlphaPage).column is None
        assert mount_of(offering, FollowAction).column is None

    def test_an_unknown_column_is_refused_when_registered(self, offering):
        with pytest.raises(PluginRegistrationError, match="ActivityCard"):
            offering.register(Sample, place="card", column="middle")(ActivityCard)

        assert offering.get_plugins_for_model(Sample) == [(SomeOverview, {})]

    def test_a_column_on_something_that_is_not_a_card_is_still_refused(self, offering):
        with pytest.raises(PluginRegistrationError, match="FollowAction"):
            offering.register(Sample, place="action", column="wide")(FollowAction)

    def test_a_card_cannot_decline_its_entry(self, offering):
        with pytest.raises(PluginRegistrationError, match="ActivityCard"):
            offering.register(Sample, place="card", menu=False)(ActivityCard)

        assert offering.get_plugins_for_model(Sample) == [(SomeOverview, {})]

    def test_a_card_whose_name_clashes_with_another_plugin_is_refused(self, offering):
        offering.register(Sample)(AlphaPage)
        clashing = make_card("AlphaPage")

        with pytest.raises(PluginRegistrationError, match="AlphaPage"):
            offering.register(Sample, place="card")(clashing)


class TestCardMounts:
    def test_only_card_mounts_are_returned(self, offering):
        offering.register(Sample)(AlphaPage)
        offering.register(Sample, place="action")(FollowAction)
        offering.register(Sample, place="card")(ActivityCard)

        assert [m.plugin_class for m in offering.get_cards(Sample)] == [ActivityCard]

    def test_cards_are_in_order_and_then_name(self, offering):
        offering.register(Sample, place="card", order=20)(NotesCard)
        offering.register(Sample, place="card", order=10)(SummaryCard)
        offering.register(Sample, place="card", order=10)(ActivityCard)

        names = [m.name for m in offering.get_cards(Sample)]

        assert names == ["activity-card", "summary-card", "notes-card"]

    def test_the_list_is_the_same_whichever_order_they_were_registered_in(self):
        forward, backward = offering_registry(), offering_registry()
        classes = [NotesCard, SummaryCard, ActivityCard]
        for cls in classes:
            forward.register(Sample, place="card")(cls)
        for cls in reversed(classes):
            backward.register(Sample, place="card")(cls)

        assert forward.get_cards(Sample) == backward.get_cards(Sample)

    def test_a_card_is_not_among_the_page_actions(self, offering):
        offering.register(Sample, place="card")(ActivityCard)
        offering.register(Sample, place="action")(FollowAction)

        assert [m.plugin_class for m in offering.get_page_actions(Sample)] == [
            FollowAction
        ]

    def test_a_card_contributes_no_pattern_at_its_own_name(self):
        plugins.registry.register(Sample, place="card")(ActivityCard)

        names = [p.name for p in plugins.registry.get_urls_for_model(Sample)]

        assert "activity-card" not in names

    def test_a_card_contributes_one_pattern_for_each_further_view_beneath_its_name(
        self,
    ):
        class Detail(Plugin, TemplateView):
            template_name = "base.html"

        class Export(Plugin, TemplateView):
            template_name = "base.html"

        card = make_card("WithViews", extra_views=[Detail, Export])
        plugins.registry.register(Sample, place="card")(card)

        patterns = {
            p.name: str(p.pattern)
            for p in plugins.registry.get_urls_for_model(Sample)
            if p.name.startswith("with-views")
        }

        assert patterns == {
            "with-views-detail": "with-views/detail/",
            "with-views-export": "with-views/export/",
        }

    def test_a_card_has_no_navigation_entry(self):
        plugins.registry.register(Sample, place="card", label="Cardlabel")(ActivityCard)

        plugins.registry.get_urls_for_model(Sample)
        menu = plugins.registry.get_plugin_menu_for_model(Sample)

        assert "Cardlabel" not in [c.extra_context.get("label") for c in menu.children]


class TestRenderCard:
    def test_the_template_is_drawn_with_the_record_and_the_request(
        self, rf, plain_user, project
    ):
        request = rf.get("/")
        request.user = plain_user

        html = ActivityCard().render_card(request, project)

        card = BeautifulSoup(html, "html.parser").select_one("[data-test-card]")
        assert card["data-test-card"] == "activity"
        assert card["data-record"] == str(project.pk)
        assert card["data-base-object"] == str(project.pk)
        assert card["data-viewer"] == str(plain_user.pk)

    def test_what_the_card_adds_to_its_context_is_drawn(self, rf, plain_user, project):
        class Saying(Card):
            template_name = CARD_TEMPLATE
            label = "saying"

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["body"] = "in the card"
                return context

        request = rf.get("/")
        request.user = plain_user

        html = Saying().render_card(request, project)

        assert BeautifulSoup(html, "html.parser").select_one(
            "[data-test-card]"
        ).text == ("in the card")

    def test_a_card_declares_assets_as_a_plugin_does(self):
        class Styled(Card):
            template_name = CARD_TEMPLATE

            class Media:
                css = {"all": ["styled.css"]}
                js = ["styled.js"]

        media = Styled().get_media()

        assert "styled.css" in str(media)
        assert "styled.js" in str(media)

    def test_a_card_with_no_assets_declares_none(self):
        assert str(ActivityCard().get_media()) == ""
