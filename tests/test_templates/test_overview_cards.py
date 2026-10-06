"""Overview cards drawn into a record's overview, opened through the test client."""

import logging

import pytest
from bs4 import BeautifulSoup
from django.views.generic import TemplateView
from fairdm.contrib.plugins.cards import Card

from demo.factories import RockSampleFactory, WaterSampleFactory, XRFMeasurementFactory
from demo.models import RockSample
from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contributor, Person
from fairdm.contrib.plugins import Plugin, is_instance_of
from fairdm.contrib.plugins import reverse as plugin_reverse
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility

KINDS = ["project", "dataset", "sample", "measurement", "person", "organization"]

CARD = "[data-test-card]"
CONTRIBUTED = "[data-contributed-card]"


def make_record(kind):
    """Create a record of one kind that every visitor may open, with the model plugins register against."""
    dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
    if kind == "project":
        return Project, ProjectFactory(visibility=Visibility.PUBLIC)
    if kind == "dataset":
        return Dataset, dataset
    if kind == "sample":
        return Sample, RockSampleFactory(dataset=dataset)
    if kind == "measurement":
        sample = RockSampleFactory(dataset=dataset)
        return Measurement, XRFMeasurementFactory(dataset=dataset, sample=sample)
    if kind == "person":
        return Contributor, PersonFactory(
            is_active=True, is_claimed=True, password="testpass123"
        )
    return Contributor, OrganizationFactory()


class LabelledCard(Card):
    """A card that draws the shared test template under its own name."""

    template_name = "plugin_cards/card.html"
    body = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["label"] = self.get_name()
        context["body"] = self.body
        return context


def make_card(name, **attributes):
    """Build a card class named ``name``."""
    return type(name, (LabelledCard,), attributes)


def make_view(name, **attributes):
    """Build a plugin page class named ``name``, for a card to own."""
    return type(
        name, (Plugin, TemplateView), {"template_name": "base.html", **attributes}
    )


def only_for(predicate):
    """Wrap a ``check(request, obj)`` predicate so a class can carry it."""
    return staticmethod(predicate)


def page_of(response):
    return BeautifulSoup(response.content, "html.parser")


def drawn(response):
    """The names of the cards in the response, in page order."""
    return [card["data-test-card"] for card in page_of(response).select(CARD)]


def drawn_in(response, column):
    """The names of the cards in one column, in page order."""
    selector = f"[data-contributed-card='{column}'] {CARD}"
    return [card["data-test-card"] for card in page_of(response).select(selector)]


@pytest.fixture
def public_dataset(db):
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


@pytest.fixture
def private_project(db):
    return ProjectFactory(visibility=Visibility.PRIVATE)


@pytest.mark.django_db
class TestEachRecordTypeDrawsItsCards:
    @pytest.mark.parametrize("kind", KINDS)
    def test_the_overview_draws_the_card_with_the_record_it_belongs_to(
        self, client, plugin_sandbox, kind
    ):
        model, record = make_record(kind)
        with plugin_sandbox.declare():
            plugins.register(model, place="card")(make_card("RecentCard"))

        response = client.get(record.get_absolute_url())

        assert response.status_code == 200
        (card,) = page_of(response).select(CARD)
        assert card["data-test-card"] == "recent-card"
        assert card["data-record"] == str(record.pk)
        assert card["data-base-object"] == str(record.pk)

    def test_the_card_is_drawn_with_the_request_of_the_visitor(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(make_card("RecentCard"))
        visitor = UserFactory()
        client.force_login(visitor)

        response = client.get(public_dataset.get_absolute_url())

        (card,) = page_of(response).select(CARD)
        assert card["data-viewer"] == str(visitor.pk)

    def test_a_card_is_not_in_the_navigation_or_the_page_actions(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(make_card("RecentCard"))

        response = client.get(public_dataset.get_absolute_url())

        page = page_of(response)
        assert page.select_one("[data-page-actions]") is None
        assert page.select_one("a[href*='recent-card']") is None


@pytest.mark.django_db
class TestWhoSeesACard:
    def test_a_card_whose_predicate_excludes_the_visitor_leaves_nothing_in_the_page(
        self, client, plugin_sandbox, public_dataset
    ):
        signed_in_only = make_card(
            "MembersCard",
            body="MEMBERS-ONLY-TEXT",
            check=only_for(lambda request, obj: request.user.is_authenticated),
        )
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(signed_in_only)

        stranger = client.get(public_dataset.get_absolute_url())
        client.force_login(UserFactory())
        member = client.get(public_dataset.get_absolute_url())

        assert stranger.status_code == 200
        assert drawn(stranger) == []
        assert b"MEMBERS-ONLY-TEXT" not in stranger.content
        assert drawn(member) == ["members-card"]
        assert b"MEMBERS-ONLY-TEXT" in member.content

    def test_a_card_whose_permission_the_visitor_lacks_leaves_nothing_in_the_page(
        self, client, plugin_sandbox, public_dataset
    ):
        editing = make_card(
            "EditorsCard", body="EDITORS-ONLY-TEXT", permission="dataset.change_dataset"
        )
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(editing)
        editor = UserFactory()
        ContributionFactory(
            content_object=public_dataset,
            contributor=editor,
            level=ContributionLevel.EDIT,
        )

        client.force_login(UserFactory())
        outsider = client.get(public_dataset.get_absolute_url())
        client.force_login(editor)
        team = client.get(public_dataset.get_absolute_url())

        assert drawn(outsider) == []
        assert b"EDITORS-ONLY-TEXT" not in outsider.content
        assert drawn(team) == ["editors-card"]

    def test_a_card_narrowed_to_one_sample_type_is_not_drawn_on_another(
        self, client, plugin_sandbox, public_dataset
    ):
        rock_only = make_card("RockCard", check=only_for(is_instance_of(RockSample)))
        with plugin_sandbox.declare():
            plugins.register(Sample, place="card")(rock_only)
        rock = RockSampleFactory(dataset=public_dataset)
        water = WaterSampleFactory(dataset=public_dataset)

        on_rock = client.get(rock.get_absolute_url())
        on_water = client.get(water.get_absolute_url())

        assert on_water.status_code == 200
        assert drawn(on_rock) == ["rock-card"]
        assert drawn(on_water) == []

    def test_a_card_registered_against_contributors_and_narrowed_to_one_kind(
        self, client, plugin_sandbox
    ):
        people_only = make_card("PeopleCard", check=only_for(is_instance_of(Person)))
        with plugin_sandbox.declare():
            plugins.register(Contributor, place="card")(people_only)
        _, person = make_record("person")
        _, organization = make_record("organization")

        on_person = client.get(person.get_absolute_url())
        on_organization = client.get(organization.get_absolute_url())

        assert drawn(on_person) == ["people-card"]
        assert drawn(on_organization) == []


@pytest.mark.django_db
class TestFurtherViewsOfACard:
    def test_a_view_of_a_card_the_predicate_hides_is_refused_and_served_to_who_it_admits(
        self, client, plugin_sandbox, public_dataset
    ):
        card = make_card(
            "MembersCard",
            extra_views=[make_view("Detail")],
            check=only_for(lambda request, obj: request.user.is_authenticated),
        )
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(card)
        address = plugin_reverse(public_dataset, "members-card-detail")

        stranger = client.get(address)
        client.force_login(UserFactory())
        member = client.get(address)

        assert stranger.status_code != 200
        assert member.status_code == 200

    def test_a_view_of_a_card_only_its_permission_hides_is_refused_and_served_to_who_it_admits(
        self, client, plugin_sandbox, public_dataset
    ):
        card = make_card(
            "EditorsCard",
            extra_views=[make_view("Detail")],
            permission="dataset.change_dataset",
        )
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(card)
        address = plugin_reverse(public_dataset, "editors-card-detail")
        editor = UserFactory()
        ContributionFactory(
            content_object=public_dataset,
            contributor=editor,
            level=ContributionLevel.EDIT,
        )

        client.force_login(UserFactory())
        outsider = client.get(address)
        client.force_login(editor)
        team = client.get(address)

        assert outsider.status_code == 403
        assert team.status_code == 200

    def test_a_view_of_a_card_is_refused_when_the_view_s_own_rule_refuses(
        self, client, plugin_sandbox, public_dataset
    ):
        card = make_card(
            "OpenCard",
            extra_views=[make_view("Detail", check=False)],
        )
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(card)

        response = client.get(plugin_reverse(public_dataset, "open-card-detail"))

        assert response.status_code != 200

    def test_a_view_of_a_card_with_no_predicate_on_a_private_project_is_refused_to_a_stranger(
        self, client, plugin_sandbox, private_project
    ):
        card = make_card("OpenCard", extra_views=[make_view("Detail")])
        with plugin_sandbox.declare():
            plugins.register(Project, place="card")(card)
        address = plugin_reverse(private_project, "open-card-detail")
        reader = UserFactory()
        ContributionFactory(
            content_object=private_project,
            contributor=reader,
            level=ContributionLevel.VIEW,
        )

        client.force_login(UserFactory())
        stranger = client.get(address)
        client.force_login(reader)
        member = client.get(address)

        assert stranger.status_code != 200
        assert member.status_code == 200

    def test_a_view_of_a_page_is_decided_as_it_always_was(
        self, client, plugin_sandbox, public_dataset
    ):
        page = make_view(
            "OpenPage",
            extra_views=[make_view("Detail")],
            check=only_for(lambda request, obj: request.user.is_authenticated),
        )
        with plugin_sandbox.declare():
            plugins.register(Dataset)(page)

        response = client.get(plugin_reverse(public_dataset, "open-page-detail"))

        assert response.status_code == 200


@pytest.mark.django_db
class TestWhereACardIsDrawn:
    def test_a_side_card_follows_the_cards_the_page_has_in_the_side_column(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(make_card("RecentCard"))

        response = client.get(public_dataset.get_absolute_url())

        wrapper = page_of(response).select_one("[data-contributed-card='side']")
        column = wrapper.parent
        assert column.select_one("[data-card='citation']") is not None
        assert column.select_one("[data-card='publications']") is not None
        assert wrapper.find_next_siblings(True) == []
        assert wrapper.find_previous_siblings(True) != []

    def test_a_card_with_no_column_is_drawn_in_the_side_column(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(make_card("RecentCard"))

        response = client.get(public_dataset.get_absolute_url())

        assert drawn_in(response, "side") == ["recent-card"]
        assert drawn_in(response, "wide") == []

    def test_a_wide_card_follows_the_wide_column_s_own_content(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card", column="wide")(
                make_card("RecentCard")
            )

        response = client.get(public_dataset.get_absolute_url())

        wrapper = page_of(response).select_one("[data-contributed-card='wide']")
        column = wrapper.parent
        assert column.select_one("[data-card='citation']") is None
        assert wrapper.find_next_siblings(True) == []
        assert wrapper.find_previous_siblings(True) != []
        assert drawn_in(response, "side") == []

    def test_cards_in_one_column_are_in_position_order_and_then_by_name(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            for name, order in [("LateCard", 20), ("BCard", 10), ("ACard", 10)]:
                plugins.register(Dataset, place="card", order=order)(make_card(name))
            plugins.register(Dataset, place="card", column="wide", order=1)(
                make_card("WideCard")
            )

        response = client.get(public_dataset.get_absolute_url())

        assert drawn_in(response, "side") == ["a-card", "b-card", "late-card"]
        assert drawn_in(response, "wide") == ["wide-card"]


@pytest.mark.django_db
class TestACardThatFails:
    def test_a_card_that_raises_is_left_out_the_page_is_served_and_the_failure_is_logged(
        self, client, plugin_sandbox, public_dataset, caplog
    ):
        class Broken(LabelledCard):
            def get_context_data(self, **kwargs):
                msg = "the card failed"
                raise RuntimeError(msg)

        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card", order=1)(Broken)
            plugins.register(Dataset, place="card", order=2)(make_card("FineCard"))

        with caplog.at_level(logging.ERROR):
            response = client.get(public_dataset.get_absolute_url())

        assert response.status_code == 200
        assert drawn(response) == ["fine-card"]
        failures = [r for r in caplog.records if r.exc_info]
        assert any(
            "Broken" in r.getMessage() and str(public_dataset.pk) in r.getMessage()
            for r in failures
        )

    def test_a_card_whose_predicate_raises_is_hidden_the_page_is_served_and_the_failure_is_logged(
        self, client, plugin_sandbox, public_dataset, caplog
    ):
        def explode(request, obj):
            msg = "the predicate failed"
            raise RuntimeError(msg)

        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(
                make_card("BrokenCard", check=only_for(explode))
            )
            plugins.register(Dataset, place="card")(make_card("FineCard"))

        with caplog.at_level(logging.ERROR):
            response = client.get(public_dataset.get_absolute_url())

        assert response.status_code == 200
        assert drawn(response) == ["fine-card"]
        assert any(
            r.exc_info and "BrokenCard" in r.getMessage() for r in caplog.records
        )

    def test_a_card_that_fails_adds_none_of_its_assets(
        self, client, plugin_sandbox, public_dataset
    ):
        class Broken(LabelledCard):
            class Media:
                js = ["https://assets.example.test/broken.js"]

            def get_context_data(self, **kwargs):
                msg = "the card failed"
                raise RuntimeError(msg)

        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(Broken)

        response = client.get(public_dataset.get_absolute_url())

        assert b"assets.example.test/broken.js" not in response.content


@pytest.mark.django_db
class TestACardWithNothingToShow:
    def test_a_card_that_draws_nothing_is_still_drawn(
        self, client, plugin_sandbox, public_dataset
    ):
        quiet = make_card("QuietCard", template_name="plugin_cards/empty.html")
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(quiet)

        response = client.get(public_dataset.get_absolute_url())

        assert response.status_code == 200
        assert len(page_of(response).select(CONTRIBUTED)) == 1


@pytest.mark.django_db
class TestACardsAssets:
    ASSETS = {
        "css": "https://assets.example.test/card.css",
        "js": "https://assets.example.test/card.js",
    }

    def make_styled(self):
        assets = self.ASSETS
        return make_card(
            "StyledCard",
            check=only_for(lambda request, obj: request.user.is_authenticated),
            Media=type(
                "Media", (), {"css": {"all": [assets["css"]]}, "js": [assets["js"]]}
            ),
        )

    def test_the_stylesheet_and_script_are_in_the_response_when_the_card_is_drawn(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(self.make_styled())
        client.force_login(UserFactory())

        response = client.get(public_dataset.get_absolute_url())

        assert drawn(response) == ["styled-card"]
        assert self.ASSETS["css"].encode() in response.content
        assert self.ASSETS["js"].encode() in response.content

    def test_they_are_absent_for_a_visitor_the_card_is_hidden_from(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="card")(self.make_styled())

        response = client.get(public_dataset.get_absolute_url())

        assert drawn(response) == []
        assert self.ASSETS["css"].encode() not in response.content
        assert self.ASSETS["js"].encode() not in response.content


@pytest.mark.django_db
class TestWithNoCards:
    @pytest.mark.parametrize("kind", KINDS)
    def test_the_overview_has_no_contributed_card_markup(self, client, kind):
        _, record = make_record(kind)

        response = client.get(record.get_absolute_url())

        assert response.status_code == 200
        assert page_of(response).select(CONTRIBUTED) == []
