"""The page actions dropdown on a record's overview, opened through the test client."""

import logging

import pytest
from bs4 import BeautifulSoup
from django.views.generic import TemplateView

from demo.factories import RockSampleFactory, XRFMeasurementFactory
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

DROPDOWN = "[data-page-actions]"


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


def make_action(name, **attributes):
    """Build a plugin class with the given attributes, named ``name``."""
    return type(
        name, (Plugin, TemplateView), {"template_name": "base.html", **attributes}
    )


def only_for(predicate):
    """Wrap a ``check(request, obj)`` predicate so a class can carry it."""
    return staticmethod(predicate)


def page_of(response):
    return BeautifulSoup(response.content, "html.parser")


def offered(response):
    """The addresses the dropdown offers, in the order it lists them."""
    return [a["href"] for a in page_of(response).select(f"{DROPDOWN} a[href]")]


@pytest.fixture
def public_dataset(db):
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


@pytest.mark.django_db
class TestEachRecordTypeOffersItsActions:
    @pytest.mark.parametrize("kind", KINDS)
    def test_the_overview_offers_the_action_and_it_leads_to_the_record(
        self, client, plugin_sandbox, kind
    ):
        model, record = make_record(kind)
        with plugin_sandbox.declare():
            plugins.register(model, place="action", label="Follow", icon="bell")(
                make_action("FollowAction")
            )

        response = client.get(record.get_absolute_url())

        assert response.status_code == 200
        assert offered(response) == [plugin_reverse(record, "follow-action")]
        assert client.get(plugin_reverse(record, "follow-action")).status_code == 200


@pytest.mark.django_db
class TestWhoIsOffered:
    def test_a_visitor_who_is_not_signed_in_is_offered_an_unrestricted_action(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="action")(make_action("OpenAction"))

        response = client.get(public_dataset.get_absolute_url())

        assert offered(response) == [plugin_reverse(public_dataset, "open-action")]

    def test_an_action_whose_predicate_excludes_the_visitor_is_neither_offered_nor_opened(
        self, client, plugin_sandbox, public_dataset
    ):
        signed_in_only = make_action(
            "MembersAction",
            check=only_for(lambda request, obj: request.user.is_authenticated),
        )
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="action")(signed_in_only)
        address = plugin_reverse(public_dataset, "members-action")

        stranger = client.get(public_dataset.get_absolute_url())
        stranger_open = client.get(address)
        client.force_login(UserFactory())
        member = client.get(public_dataset.get_absolute_url())
        member_open = client.get(address)

        assert offered(stranger) == []
        assert stranger_open.status_code != 200
        assert offered(member) == [address]
        assert member_open.status_code == 200

    def test_an_action_whose_permission_the_visitor_lacks_is_neither_offered_nor_opened(
        self, client, plugin_sandbox, public_dataset
    ):
        editing = make_action("EditorsAction", permission="dataset.change_dataset")
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="action")(editing)
        address = plugin_reverse(public_dataset, "editors-action")
        editor = UserFactory()
        ContributionFactory(
            content_object=public_dataset,
            contributor=editor,
            level=ContributionLevel.EDIT,
        )

        client.force_login(UserFactory())
        outsider = client.get(public_dataset.get_absolute_url())
        outsider_open = client.get(address)
        client.force_login(editor)
        team = client.get(public_dataset.get_absolute_url())
        team_open = client.get(address)

        assert offered(outsider) == []
        assert outsider_open.status_code == 403
        assert offered(team) == [address]
        assert team_open.status_code == 200

    def test_an_action_registered_against_contributors_and_narrowed_to_people(
        self, client, plugin_sandbox
    ):
        people_only = make_action(
            "PeopleAction", check=only_for(is_instance_of(Person))
        )
        with plugin_sandbox.declare():
            plugins.register(Contributor, place="action")(people_only)
        _, person = make_record("person")
        _, organization = make_record("organization")
        client.force_login(UserFactory())

        person_page = client.get(person.get_absolute_url())
        organization_page = client.get(organization.get_absolute_url())
        organization_open = client.get(plugin_reverse(organization, "people-action"))

        assert offered(person_page) == [plugin_reverse(person, "people-action")]
        assert offered(organization_page) == []
        assert organization_open.status_code == 403


@pytest.mark.django_db
class TestWhenThereIsNothingToOffer:
    def test_a_record_type_with_no_action_has_no_dropdown(self, client, public_dataset):
        response = client.get(public_dataset.get_absolute_url())

        assert response.status_code == 200
        assert page_of(response).select_one(DROPDOWN) is None

    def test_a_visitor_every_action_is_hidden_from_has_no_dropdown(
        self, client, plugin_sandbox, public_dataset
    ):
        nobody = make_action("NobodyAction", check=False)
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="action")(nobody)

        response = client.get(public_dataset.get_absolute_url())

        assert response.status_code == 200
        assert page_of(response).select_one(DROPDOWN) is None

    def test_an_action_that_declined_its_entry_is_served_and_not_offered(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="action", menu=False)(
                make_action("QuietAction")
            )

        response = client.get(public_dataset.get_absolute_url())

        assert page_of(response).select_one(DROPDOWN) is None
        assert (
            client.get(plugin_reverse(public_dataset, "quiet-action")).status_code
            == 200
        )


@pytest.mark.django_db
class TestAPredicateThatRaises:
    def test_the_action_is_hidden_the_page_is_served_and_the_failure_is_logged(
        self, client, plugin_sandbox, public_dataset, caplog
    ):
        def explode(request, obj):
            msg = "the predicate failed"
            raise RuntimeError(msg)

        with plugin_sandbox.declare():
            plugins.register(Dataset, place="action")(
                make_action("BrokenAction", check=only_for(explode))
            )
            plugins.register(Dataset, place="action")(make_action("FineAction"))

        with caplog.at_level(logging.ERROR):
            response = client.get(public_dataset.get_absolute_url())

        assert response.status_code == 200
        assert offered(response) == [plugin_reverse(public_dataset, "fine-action")]
        assert any(
            record.exc_info and "BrokenAction" in record.getMessage()
            for record in caplog.records
        )


@pytest.mark.django_db
class TestAnActionWhoseAddressNeedsMoreThanTheRecord:
    def test_the_action_is_left_out_the_page_is_served_and_the_plugin_is_named_in_the_log(
        self, client, plugin_sandbox, public_dataset, caplog
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="action")(
                make_action("FlagAction", url_path="<int:pk>/flag")
            )
            plugins.register(Dataset, place="action")(make_action("FineAction"))

        with caplog.at_level(logging.WARNING):
            response = client.get(public_dataset.get_absolute_url())

        assert response.status_code == 200
        assert offered(response) == [plugin_reverse(public_dataset, "fine-action")]
        assert any(
            record.levelno == logging.WARNING and "FlagAction" in record.getMessage()
            for record in caplog.records
        )


@pytest.mark.django_db
class TestOrder:
    def test_actions_are_listed_by_position_and_then_name(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            for name, order in [("LateAction", 20), ("BAction", 10), ("AAction", 10)]:
                plugins.register(Dataset, place="action", order=order)(
                    make_action(name)
                )

        response = client.get(public_dataset.get_absolute_url())

        assert offered(response) == [
            plugin_reverse(public_dataset, name)
            for name in ("a-action", "b-action", "late-action")
        ]


@pytest.mark.django_db
class TestApartFromTheManageMenu:
    def test_a_page_action_is_not_inside_the_manage_menu_and_the_menu_is_still_there(
        self, client, plugin_sandbox, public_dataset
    ):
        with plugin_sandbox.declare():
            plugins.register(Dataset, place="action")(make_action("FollowAction"))
        manager = UserFactory()
        ContributionFactory(
            content_object=public_dataset,
            contributor=manager,
            level=ContributionLevel.MANAGE,
        )
        client.force_login(manager)

        response = client.get(public_dataset.get_absolute_url())

        page = page_of(response)
        action = plugin_reverse(public_dataset, "follow-action")
        edit = response.context["urls"]["update"]
        action_menu = page.select_one(f"a[href='{action}']").find_parent(
            attrs={"data-mvp-dropdown": True}
        )
        manage_menu = page.select_one(f"a[href='{edit}']").find_parent(
            attrs={"data-mvp-dropdown": True}
        )
        assert action_menu is not manage_menu
        assert action_menu.find_parent(attrs={"data-page-actions": True}) is not None
        assert manage_menu.select_one(f"a[href='{action}']") is None
        assert action_menu.select_one(f"a[href='{edit}']") is None
