"""Pages served by a plugin that replaces another, opened through the test client."""

import pytest
from bs4 import BeautifulSoup
from django.urls import NoReverseMatch
from django.views.generic import TemplateView

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins import reverse as plugin_reverse
from fairdm.contrib.plugins.cards import Card
from fairdm.contrib.plugins.places import OverviewPlaces
from fairdm.contrib.contributors.models import Contributor
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

DROPDOWN = "[data-page-actions]"
CARD = "[data-test-card]"


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


def make_page(name, **attributes):
    """Build a plugin page class named ``name``."""
    return type(
        name, (Plugin, TemplateView), {"template_name": "base.html", **attributes}
    )


class LabelledCard(Card):
    """A card that draws the shared test template under its own name."""

    template_name = "plugin_cards/card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["label"] = self.get_name()
        context["body"] = ""
        return context


def make_card(name, **attributes):
    """Build a card class named ``name``."""
    return type(name, (LabelledCard,), attributes)


def only_for(predicate):
    """Wrap a ``check(request, obj)`` predicate so a class can carry it."""
    return staticmethod(predicate)


def shipped_overview(model):
    """The class a record type serves at its overview."""
    return next(
        mount.plugin_class
        for mount in plugins.registry.resolve(model)
        if issubclass(mount.plugin_class, OverviewPlaces)
    )


def page_of(response):
    return BeautifulSoup(response.content, "html.parser")


def served_by(response):
    """The class of the view that answered."""
    return type(response.context["view"])


def entries(response, record):
    """The addresses of the navigation entries that lead into the record, in page order."""
    base = record.get_absolute_url()
    return [
        a["href"]
        for a in page_of(response).select("li a.group")
        if a["href"].startswith(base)
    ]


def offered(response):
    """The addresses the dropdown offers, in the order it lists them."""
    return [a["href"] for a in page_of(response).select(f"{DROPDOWN} a[href]")]


def drawn(response):
    """The names of the cards in the response, in page order."""
    return [card["data-test-card"] for card in page_of(response).select(CARD)]


@pytest.fixture
def public_dataset(db):
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


@pytest.mark.django_db
class TestTheReplacementAnswersAtTheTargetsAddress:
    @pytest.fixture
    def shipped(self):
        return make_page("ShippedMap", url_path="map", extra_views=[make_page("Detail")])

    def test_the_target_s_address_serves_the_replacement(
        self, client, plugin_sandbox, public_dataset, shipped
    ):
        richer = make_page("RicherMap")
        with plugin_sandbox.declare():
            plugins.register(Dataset)(shipped)
            plugins.register(Dataset, replaces=shipped)(richer)

        response = client.get(plugin_reverse(public_dataset, "shipped-map"))

        assert response.status_code == 200
        assert served_by(response) is richer
        assert plugin_reverse(public_dataset, "shipped-map").endswith("/map/")

    def test_the_target_s_name_reverses_to_it_and_the_replacement_s_own_does_not(
        self, plugin_sandbox, public_dataset, shipped
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset)(shipped)
            plugins.register(Dataset, replaces=shipped)(make_page("RicherMap"))

        assert plugin_reverse(public_dataset, "shipped-map")
        with pytest.raises(NoReverseMatch):
            plugin_reverse(public_dataset, "richer-map")

    def test_a_view_the_replaced_plugin_owned_is_not_served_unless_the_replacement_declares_it(
        self, client, plugin_sandbox, public_dataset, shipped
    ):
        export = make_page("Export")
        with plugin_sandbox.declare():
            plugins.register(Dataset)(shipped)
            plugins.register(Dataset, replaces=shipped)(
                make_page("RicherMap", extra_views=[export])
            )
        address = plugin_reverse(public_dataset, "shipped-map")

        assert client.get(f"{address}detail/").status_code == 404
        response = client.get(f"{address}export/")
        assert response.status_code == 200
        assert served_by(response) is export

    def test_a_replacement_built_on_the_target_serves_the_views_it_declares(
        self, client, plugin_sandbox, public_dataset, shipped
    ):
        better = type("BetterMap", (shipped,), {})
        with plugin_sandbox.declare():
            plugins.register(Dataset)(shipped)
            plugins.register(Dataset, replaces=shipped)(better)
        address = plugin_reverse(public_dataset, "shipped-map")

        assert client.get(f"{address}detail/").status_code == 200

    def test_the_original_is_still_served_on_a_record_type_it_was_not_replaced_on(
        self, client, plugin_sandbox, shipped
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        richer = make_page("RicherMap")
        with plugin_sandbox.declare():
            plugins.register(Project, Dataset)(shipped)
            plugins.register(Dataset, replaces=shipped)(richer)

        on_project = client.get(plugin_reverse(project, "shipped-map"))
        on_dataset = client.get(plugin_reverse(dataset, "shipped-map"))

        assert served_by(on_project) is shipped
        assert served_by(on_dataset) is richer

    @pytest.mark.parametrize("target_first", [True, False])
    def test_a_replacement_built_on_the_target_is_served_whichever_arrived_first(
        self, client, plugin_sandbox, public_dataset, shipped, target_first
    ):
        better = type("BetterMap", (shipped,), {})
        with plugin_sandbox.declare():
            if target_first:
                plugins.register(Dataset)(shipped)
            plugins.register(Dataset, replaces=shipped)(better)
            if not target_first:
                plugins.register(Dataset)(shipped)

        response = client.get(plugin_reverse(public_dataset, "shipped-map"))

        assert served_by(response) is better


@pytest.mark.django_db
class TestTheNavigationHasOneEntry:
    def test_the_replacement_is_the_one_entry_in_the_position_of_the_target(
        self, client, plugin_sandbox, public_dataset
    ):
        shipped = make_page("ShippedMap")
        other = make_page("OtherPage")
        with plugin_sandbox.declare():
            plugins.register(Dataset, label="Map", order=100)(shipped)
            plugins.register(Dataset, label="Other", order=200)(other)
            plugins.register(Dataset, replaces=shipped)(make_page("RicherMap"))
        map_address = plugin_reverse(public_dataset, "shipped-map")
        other_address = plugin_reverse(public_dataset, "other-page")

        found = entries(client.get(public_dataset.get_absolute_url()), public_dataset)

        assert found.count(map_address) == 1
        assert found.index(map_address) < found.index(other_address)
        assert [a for a in found if a.endswith("/richer-map/")] == []

    def test_a_replacement_that_states_a_position_takes_it(
        self, client, plugin_sandbox, public_dataset
    ):
        shipped = make_page("ShippedMap")
        other = make_page("OtherPage")
        with plugin_sandbox.declare():
            plugins.register(Dataset, label="Map", order=100)(shipped)
            plugins.register(Dataset, label="Other", order=200)(other)
            plugins.register(Dataset, replaces=shipped, order=300)(
                make_page("RicherMap")
            )
        map_address = plugin_reverse(public_dataset, "shipped-map")
        other_address = plugin_reverse(public_dataset, "other-page")

        found = entries(client.get(public_dataset.get_absolute_url()), public_dataset)

        assert found.count(map_address) == 1
        assert found.index(map_address) > found.index(other_address)


@pytest.mark.django_db
class TestTheAccessDecisionIsTheReplacementsOwn:
    def test_a_visitor_the_target_admitted_and_the_replacement_excludes_is_refused(
        self, client, plugin_sandbox, public_dataset
    ):
        shipped = make_page("ShippedMap")
        signed_in_only = make_page(
            "RicherMap",
            check=only_for(lambda request, obj: request.user.is_authenticated),
        )
        with plugin_sandbox.declare():
            plugins.register(Dataset, label="Map")(shipped)
            plugins.register(Dataset, replaces=shipped)(signed_in_only)
        address = plugin_reverse(public_dataset, "shipped-map")

        stranger = client.get(address)
        stranger_page = client.get(public_dataset.get_absolute_url())
        client.force_login(UserFactory())
        member = client.get(address)

        assert stranger.status_code != 200
        assert address not in entries(stranger_page, public_dataset)
        assert member.status_code == 200

    def test_a_visitor_the_target_excluded_and_the_replacement_admits_is_served(
        self, client, plugin_sandbox, public_dataset
    ):
        shipped = make_page("ShippedMap", check=False)
        open_to_all = make_page("RicherMap")
        with plugin_sandbox.declare():
            plugins.register(Dataset, label="Map")(shipped)
            plugins.register(Dataset, replaces=shipped)(open_to_all)
        address = plugin_reverse(public_dataset, "shipped-map")

        response = client.get(address)
        page = client.get(public_dataset.get_absolute_url())

        assert response.status_code == 200
        assert address in entries(page, public_dataset)

    def test_the_target_s_permission_is_not_asked_of_the_replacement(
        self, client, plugin_sandbox, public_dataset
    ):
        shipped = make_page("ShippedMap", permission="dataset.change_dataset")
        with plugin_sandbox.declare():
            plugins.register(Dataset)(shipped)
            plugins.register(Dataset, replaces=shipped)(make_page("RicherMap"))

        response = client.get(plugin_reverse(public_dataset, "shipped-map"))

        assert response.status_code == 200

    def test_the_replacement_s_permission_is_asked_though_the_target_had_none(
        self, client, plugin_sandbox, public_dataset
    ):
        shipped = make_page("ShippedMap")
        editing = make_page("RicherMap", permission="dataset.change_dataset")
        with plugin_sandbox.declare():
            plugins.register(Dataset)(shipped)
            plugins.register(Dataset, replaces=shipped)(editing)
        address = plugin_reverse(public_dataset, "shipped-map")
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


@pytest.mark.django_db
class TestAReplacedActionOrCard:
    def test_a_replaced_page_action_is_offered_once_as_the_replacement(
        self, client, plugin_sandbox, public_dataset
    ):
        shipped = make_page("FollowAction")
        richer = make_page("RicherFollow")
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="action", label="Follow")(shipped)
            plugins.register(Dataset, replaces=shipped)(richer)
        address = plugin_reverse(public_dataset, "follow-action")

        page = client.get(public_dataset.get_absolute_url())
        opened = client.get(address)

        assert offered(page) == [address]
        assert served_by(opened) is richer

    def test_a_replaced_page_action_the_replacement_hides_is_not_offered(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            shipped = make_page("FollowAction")
            plugins.register(Dataset, place="action")(shipped)
            plugins.register(Dataset, replaces=shipped)(
                make_page("RicherFollow", check=False)
            )

        page = client.get(public_dataset.get_absolute_url())

        assert offered(page) == []
        assert page_of(page).select_one(DROPDOWN) is None

    def test_a_replaced_card_is_drawn_once_as_the_replacement(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            shipped = make_card("ShippedCard")
            plugins.register(Dataset, place="card")(shipped)
            plugins.register(Dataset, place="card", replaces=shipped)(
                make_card("RicherCard")
            )

        page = client.get(public_dataset.get_absolute_url())

        assert drawn(page) == ["richer-card"]

    def test_a_replaced_card_keeps_the_column_of_the_card_it_replaced(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            shipped = make_card("ShippedCard")
            plugins.register(Dataset, place="card", column="wide")(shipped)
            plugins.register(Dataset, place="card", replaces=shipped)(
                make_card("RicherCard")
            )

        page = client.get(public_dataset.get_absolute_url())

        wide = page_of(page).select_one("[data-contributed-card='wide']")
        assert [c["data-test-card"] for c in wide.select(CARD)] == ["richer-card"]

    def test_a_replaced_card_the_replacement_hides_is_not_drawn(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            shipped = make_card("ShippedCard")
            plugins.register(Dataset, place="card")(shipped)
            plugins.register(Dataset, place="card", replaces=shipped)(
                make_card("RicherCard", check=False)
            )

        page = client.get(public_dataset.get_absolute_url())

        assert drawn(page) == []


@pytest.mark.django_db
class TestReplacingTheOverview:
    @pytest.mark.parametrize("kind", KINDS)
    def test_a_replacement_built_on_the_shipped_overview_still_shows_an_action_and_a_card(
        self, client, plugin_sandbox, kind
    ):
        model, record = make_record(kind)
        shipped = shipped_overview(model)
        richer = type("RicherOverview", (shipped,), {"name": "richer-overview"})
        with plugin_sandbox.declare():
            plugins.register(model, replaces=shipped)(richer)
            plugins.register(model, place="action")(make_page("FollowAction"))
            plugins.register(model, place="card")(make_card("RecentCard"))

        response = client.get(record.get_absolute_url())

        assert response.status_code == 200
        assert served_by(response) is richer
        assert offered(response) == [plugin_reverse(record, "follow-action")]
        assert drawn(response) == ["recent-card"]

    def test_the_shipped_overview_is_served_again_when_its_replacement_is_removed(
        self, client, plugin_sandbox, public_dataset
    ):
        shipped = shipped_overview(Dataset)
        richer = type("RicherOverview", (shipped,), {"name": "richer-overview"})
        with plugin_sandbox.declare():
            plugins.register(Dataset, replaces=shipped)(richer)
            plugins.remove(Dataset, richer)

        response = client.get(public_dataset.get_absolute_url())

        assert response.status_code == 200
        assert served_by(response) is shipped
