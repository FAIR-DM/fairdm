"""Tests for a record's Contributors tab and the pages it leads to, through the test client.

Each page is opened and submitted on a project, a dataset, a registered sample type and a
registered measurement type, as a manager, as a signed-in reader and as a visitor. Elements are
found by link target and context value. Nothing here asserts a sentence or a layout.
"""

from types import SimpleNamespace
from urllib.parse import urlparse

import pytest
import requests
from bs4 import BeautifulSoup
from django.contrib.auth.models import Group
from django.contrib.messages import ERROR, get_messages
from django.core.exceptions import NON_FIELD_ERRORS
from django.test import Client
from research_vocabs.models import Concept

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import AccountState, ContributionLevel
from fairdm.contrib.contributors.models import (
    Contribution,
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.contrib.plugins import reverse
from fairdm.factories import (
    ContributionFactory,
    ContributorIdentifierFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.portal_roles import PortalRoles
from fairdm.utils.choices import Visibility

ORCID_SEARCH = "https://pub.orcid.org/v3.0/expanded-search/"
ROR_SEARCH = "https://api.ror.org/v2/organizations"
JOSIAH = "0000-0002-1825-0097"
GFZ = "04z8jg394"
UNREACHABLE = [
    pytest.param(requests.Timeout("slow"), 200, id="timeout"),
    pytest.param(requests.ConnectionError("down"), 200, id="connection-error"),
    pytest.param(None, 500, id="server-error"),
]


def tab(record):
    return reverse(record, "contribution-list")


def page_of(record, name, **kwargs):
    return reverse(record, f"contribution-list-contribution-{name}", **kwargs)


def browser_as(user):
    browser = Client()
    if user is not None:
        browser.force_login(user)
    return browser


def links(response):
    soup = BeautifulSoup(response.content.decode(), "html.parser")
    return {urlparse(a["href"]).path for a in soup.select("a[href]")}


def stored(record):
    """Everything stored about who is listed on a record, to compare before and after."""
    return sorted(
        (c.pk, c.level, sorted(r.name for r in c.roles.all()))
        for c in record.contributors.all()
    )


def offered(response, fieldset):
    """The values of the organization radio buttons in a fieldset, and the one checked."""
    soup = BeautifulSoup(response.content.decode(), "html.parser")
    radios = soup.find(id=fieldset).select("input[name=affiliation]")
    values = [radio["value"] for radio in radios]
    return values, [radio["value"] for radio in radios if radio.has_attr("checked")]


def row_of(response, contributor):
    """The tab's entry for a contributor, whichever list it is in."""
    rows = (
        response.context["people"]["rows"] + response.context["organizations"]["rows"]
    )
    return next(row for row in rows if row["contributor"].pk == contributor.pk)


def add_from_portal(record, manager, person, **chosen):
    return browser_as(manager).post(
        page_of(record, "add-person"),
        {"via": "portal", "contributor": person.pk, **chosen},
    )


def made():
    """How many profiles and identifiers the portal holds, to compare before and after."""
    return (
        Person.objects.count(),
        Organization.objects.count(),
        ContributorIdentifier.objects.count(),
    )


def orcid_record_address(orcid_id):
    return f"https://pub.orcid.org/v3.0/{orcid_id}/record"


def ror_record_address(ror_id):
    return f"https://api.ror.org/v2/organizations/{ror_id}"


def soup_of(response):
    return BeautifulSoup(response.content.decode(), "html.parser")


def role_pks(*names):
    found = Concept.objects.filter(vocabulary__name="fairdm-roles", name__in=names)
    return [str(pk) for pk in found.values_list("pk", flat=True)]


@pytest.mark.django_db
class TestContributorsTab:
    def test_it_lists_people_and_organizations_separately(
        self, record, colleague, partner
    ):
        response = browser_as(None).get(tab(record))

        assert response.status_code == 200
        people = [e["contributor"].pk for e in response.context["people"]["rows"]]
        organizations = [
            e["contributor"].pk for e in response.context["organizations"]["rows"]
        ]
        assert people == [colleague.contributor_id]
        assert organizations == [partner.contributor_id]

    def test_a_manager_is_offered_the_two_add_pages(self, record, manager):
        response = browser_as(manager).get(tab(record))

        assert response.context["can_manage"] is True
        assert {page_of(record, "add-person"), page_of(record, "add-organization")} <= (
            links(response)
        )

    def test_a_manager_is_offered_edit_and_remove_for_each_contributor(
        self, record, manager, colleague
    ):
        response = browser_as(manager).get(tab(record))

        assert {
            page_of(record, "edit", pk=colleague.pk),
            page_of(record, "remove", pk=colleague.pk),
        } <= links(response)

    @pytest.mark.parametrize("viewer", ["reader", "visitor", "stranger"])
    def test_nobody_else_is_offered_a_control(
        self, request, record, colleague, partner, viewer
    ):
        user = None if viewer == "visitor" else request.getfixturevalue(
            "newcomer" if viewer == "stranger" else viewer
        )

        response = browser_as(user).get(tab(record))

        controls = {
            page_of(record, "add-person"),
            page_of(record, "add-organization"),
            page_of(record, "edit", pk=colleague.pk),
            page_of(record, "remove", pk=colleague.pk),
            page_of(record, "edit", pk=partner.pk),
            page_of(record, "remove", pk=partner.pk),
        }
        assert response.status_code == 200
        assert response.context["can_manage"] is False
        assert links(response).isdisjoint(controls)

    def test_a_record_with_nobody_credited_still_offers_a_manager_both_add_pages(
        self, record, curator
    ):
        response = browser_as(curator).get(tab(record))

        assert response.context["people"]["total"] == 0
        assert response.context["organizations"]["total"] == 0
        assert {page_of(record, "add-person"), page_of(record, "add-organization")} <= (
            links(response)
        )

    def test_a_search_narrows_both_lists(self, record):
        ContributionFactory(
            content_object=record, contributor=PersonFactory(name="Zelda Alphonse")
        )
        ContributionFactory(
            content_object=record, contributor=PersonFactory(name="Boris Gamma")
        )
        ContributionFactory(
            content_object=record, contributor=OrganizationFactory(name="Alphonse Lab")
        )
        ContributionFactory(
            content_object=record, contributor=OrganizationFactory(name="Gamma Works")
        )

        response = browser_as(None).get(tab(record), {"q": "alphonse"})

        people = [e["contributor"].name for e in response.context["people"]["rows"]]
        organizations = [
            e["contributor"].name for e in response.context["organizations"]["rows"]
        ]
        assert (people, organizations) == (["Zelda Alphonse"], ["Alphonse Lab"])


@pytest.mark.django_db
class TestOverviewLinksToTheTab:
    def test_the_people_card_leads_to_the_tab(self, record):
        response = browser_as(None).get(record.get_absolute_url())

        assert response.context["people_url"] == tab(record)


@pytest.mark.django_db
class TestChangingPagesRefuseAnyoneButAManager:
    """Scenario 10: a refused request changes nothing."""

    def requests_for(self, record, colleague, newcomer):
        return [
            ("get", page_of(record, "add-person"), {}),
            ("post", page_of(record, "add-person"), {"contributor": newcomer.pk}),
            ("get", page_of(record, "add-organization"), {}),
            (
                "post",
                page_of(record, "add-organization"),
                {"contributor": OrganizationFactory().pk},
            ),
            ("get", page_of(record, "edit", pk=colleague.pk), {}),
            (
                "post",
                page_of(record, "edit", pk=colleague.pk),
                {"roles": role_pks("Creator"), "level": ContributionLevel.MANAGE},
            ),
            ("get", page_of(record, "remove", pk=colleague.pk), {}),
            ("post", page_of(record, "remove", pk=colleague.pk), {}),
            ("get", page_of(record, "move", pk=colleague.pk), {}),
            ("post", page_of(record, "move", pk=colleague.pk), {"direction": "up"}),
        ]

    def test_a_signed_in_person_who_cannot_manage_gets_403(
        self, record, reader, colleague, newcomer
    ):
        before = stored(record)

        for method, url, data in self.requests_for(record, colleague, newcomer):
            response = getattr(browser_as(reader), method)(url, data)
            assert response.status_code == 403, (method, url)

        assert stored(record) == before

    def test_a_visitor_is_sent_to_sign_in(self, record, colleague, newcomer):
        before = stored(record)

        for method, url, data in self.requests_for(record, colleague, newcomer):
            response = getattr(browser_as(None), method)(url, data)
            assert response.status_code == 302, (method, url)
            assert "login" in response["Location"], (method, url)

        assert stored(record) == before


VIEW, EDIT, MANAGE = (
    ContributionLevel.VIEW,
    ContributionLevel.EDIT,
    ContributionLevel.MANAGE,
)


@pytest.fixture
def private_chain(db):
    """A private project, a private dataset in it, and a sample and measurement in that."""
    project = ProjectFactory(visibility=Visibility.PRIVATE)
    dataset = DatasetFactory(
        project=project, visibility=Visibility.PRIVATE, published=False
    )
    sample = RockSampleFactory(dataset=dataset)
    measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)
    return SimpleNamespace(
        project=project, dataset=dataset, sample=sample, measurement=measurement
    )


@pytest.fixture(params=["project", "dataset", "sample", "measurement"])
def private_record(request, private_chain):
    """Each kind of private record in turn."""
    return getattr(private_chain, request.param)


def person_at(record, level, **fields):
    """A person who can sign in, listed on the record at the level."""
    person = PersonFactory(is_active=True, is_claimed=True, password="x", **fields)
    ContributionFactory(content_object=record, contributor=person, level=level)
    return person


def changing_page(record):
    """The address of a page that changes the record, or None when it has none."""
    kind = RecordAccess(record).kind
    if kind in ("project", "dataset"):
        return reverse(record, "overview-update")
    if kind == "sample":
        return reverse(record, "edit")
    return None


def refusal(record):
    """The status a signed-in person who may open the record gets from one of its editing pages.

    A private project's or dataset's pages answer a refusal as a record that does not exist,
    which is the rule those pages already had.
    """
    private = getattr(record, "visibility", None) == Visibility.PRIVATE
    return 404 if private else 403


def deletion_page(record):
    """The address of the page that deletes the record, or None when it has none."""
    if RecordAccess(record).kind in ("project", "dataset"):
        return reverse(record, "overview-delete")
    return None


def tab_pages(record, contribution):
    """Every page of the record's Contributors tab that is opened, for one contribution."""
    return [
        tab(record),
        page_of(record, "add-person"),
        page_of(record, "add-organization"),
        page_of(record, "edit", pk=contribution.pk),
        page_of(record, "remove", pk=contribution.pk),
    ]


def submissions(record, contribution):
    """Every address the tab accepts a submission at, for one contribution on it."""
    return [
        *tab_pages(record, contribution)[1:],
        page_of(record, "move", pk=contribution.pk),
    ]


@pytest.mark.django_db
class TestLevels:
    """User story 4: the level a person holds decides who opens, edits and manages."""

    def test_a_person_added_from_the_tab_opens_a_private_record_and_cannot_change_it(
        self, private_record, newcomer
    ):
        manager = person_at(private_record, MANAGE)
        assert (
            browser_as(newcomer).get(private_record.get_absolute_url()).status_code
            == 404
        )

        add_from_portal(private_record, manager, newcomer)

        assert (
            browser_as(newcomer).get(private_record.get_absolute_url()).status_code
            == 200
        )
        if changing_page(private_record):
            assert browser_as(newcomer).get(
                changing_page(private_record)
            ).status_code == refusal(private_record)
        assert not newcomer.has_perm(
            f"{RecordAccess(private_record).kind}.change_{RecordAccess(private_record).kind}",
            private_record,
        )

    def test_the_edit_page_sets_the_level_with_the_roles(
        self, private_record, newcomer
    ):
        manager = person_at(private_record, MANAGE)
        add_from_portal(private_record, manager, newcomer)
        contribution = private_record.contributors.get(contributor=newcomer)
        names = list(private_record.CONTRIBUTOR_ROLES.values)[:1]

        response = browser_as(manager).post(
            page_of(private_record, "edit", pk=contribution.pk),
            {"roles": role_pks(*names), "level": EDIT},
        )

        contribution.refresh_from_db()
        assert response["Location"] == tab(private_record)
        assert contribution.level == EDIT
        assert {r.name for r in contribution.roles.all()} == set(names)

    def test_changing_roles_does_not_change_the_level(self, private_record):
        manager = person_at(private_record, MANAGE)
        editor = person_at(private_record, EDIT)
        contribution = private_record.contributors.get(contributor=editor)

        browser_as(manager).post(
            page_of(private_record, "edit", pk=contribution.pk),
            {
                "roles": role_pks(private_record.CONTRIBUTOR_ROLES.values[0]),
                "level": EDIT,
            },
        )

        contribution.refresh_from_db()
        assert contribution.level == EDIT

    def test_an_editor_may_change_the_record_and_is_refused_the_rest(
        self, private_record
    ):
        editor = person_at(private_record, EDIT)
        colleague = ContributionFactory(content_object=private_record, level=VIEW)

        if changing_page(private_record):
            assert (
                browser_as(editor).get(changing_page(private_record)).status_code == 200
            )
        if deletion_page(private_record):
            assert browser_as(editor).get(
                deletion_page(private_record)
            ).status_code == refusal(private_record)
        for url in tab_pages(private_record, colleague)[1:]:
            assert browser_as(editor).get(url).status_code == 403, url
        assert browser_as(editor).get(tab(private_record)).status_code == 200

    def test_a_manager_may_change_manage_and_delete(self, private_record):
        manager = person_at(private_record, MANAGE)
        colleague = ContributionFactory(content_object=private_record, level=VIEW)

        if changing_page(private_record):
            assert (
                browser_as(manager).get(changing_page(private_record)).status_code
                == 200
            )
        if deletion_page(private_record):
            assert (
                browser_as(manager).get(deletion_page(private_record)).status_code
                == 200
            )
        for url in tab_pages(private_record, colleague):
            assert browser_as(manager).get(url).status_code == 200, url

    def test_a_person_who_is_lowered_is_refused_what_only_the_higher_level_allowed(
        self, private_record
    ):
        manager = person_at(private_record, MANAGE)
        editor = person_at(private_record, EDIT)
        contribution = private_record.contributors.get(contributor=editor)
        if changing_page(private_record):
            assert (
                browser_as(editor).get(changing_page(private_record)).status_code == 200
            )

        browser_as(manager).post(
            page_of(private_record, "edit", pk=contribution.pk), {"level": VIEW}
        )

        assert (
            browser_as(editor).get(private_record.get_absolute_url()).status_code == 200
        )
        if changing_page(private_record):
            assert browser_as(editor).get(
                changing_page(private_record)
            ).status_code == refusal(private_record)

    def test_a_person_who_is_removed_is_refused_a_private_record(self, private_record):
        manager = person_at(private_record, MANAGE)
        reader = person_at(private_record, VIEW)
        contribution = private_record.contributors.get(contributor=reader)

        browser_as(manager).post(page_of(private_record, "remove", pk=contribution.pk))

        assert (
            browser_as(reader).get(private_record.get_absolute_url()).status_code == 404
        )

    def test_a_person_removed_from_a_dataset_keeps_what_they_hold_from_the_project(
        self, private_chain
    ):
        manager = person_at(private_chain.dataset, MANAGE)
        reader = person_at(private_chain.project, VIEW)
        contribution = ContributionFactory(
            content_object=private_chain.dataset,
            contributor=reader,
            level=VIEW,
        )

        browser_as(manager).post(
            page_of(private_chain.dataset, "remove", pk=contribution.pk)
        )

        assert not private_chain.dataset.contributors.filter(
            contributor=reader
        ).exists()
        assert (
            browser_as(reader).get(private_chain.dataset.get_absolute_url()).status_code
            == 200
        )

    def test_no_level_is_offered_for_an_organization_and_none_is_stored(
        self, private_record
    ):
        manager = person_at(private_record, MANAGE)
        partner = ContributionFactory(
            content_object=private_record, contributor=OrganizationFactory(), level=None
        )

        page = browser_as(manager).get(page_of(private_record, "edit", pk=partner.pk))
        browser_as(manager).post(
            page_of(private_record, "edit", pk=partner.pk), {"level": MANAGE}
        )

        partner.refresh_from_db()
        assert page.context["entry"]["is_person"] is False
        assert partner.level is None

    def test_a_level_below_what_is_held_from_above_is_refused_on_the_field(
        self, private_chain
    ):
        manager = person_at(private_chain.dataset, MANAGE)
        holder = person_at(private_chain.project, EDIT)
        contribution = ContributionFactory(
            content_object=private_chain.dataset, contributor=holder, level=EDIT
        )
        before = stored(private_chain.dataset)

        response = browser_as(manager).post(
            page_of(private_chain.dataset, "edit", pk=contribution.pk),
            {"level": VIEW},
        )

        assert response.status_code == 422
        assert "level" in response.context["errors"]
        assert stored(private_chain.dataset) == before

    def test_the_tab_shows_a_manager_who_holds_access_from_above_and_where_from(
        self, private_chain
    ):
        manager = person_at(private_chain.dataset, MANAGE)
        holder = person_at(private_chain.project, EDIT)

        response = browser_as(manager).get(tab(private_chain.dataset))

        found = {
            (h["person"].pk, h["label"], h["source"])
            for h in response.context["access_from_above"]
        }
        assert found == {(holder.pk, EDIT.label, private_chain.project)}

    def test_the_tab_shows_a_reader_nobodys_level(self, private_chain):
        reader = person_at(private_chain.dataset, VIEW)
        person_at(private_chain.dataset, MANAGE)
        person_at(private_chain.project, EDIT)

        response = browser_as(reader).get(tab(private_chain.dataset))

        assert response.status_code == 200
        assert response.context["can_manage"] is False
        assert response.context["access_from_above"] == []
        for row in response.context["people"]["rows"]:
            assert row["effective"] is None and row["own"] is None
        content = response.content.decode()
        assert not any(str(level.label) in content for level in ContributionLevel)

    def test_a_manager_sees_levels_on_the_same_tab(self, private_chain):
        manager = person_at(private_chain.dataset, MANAGE)

        response = browser_as(manager).get(tab(private_chain.dataset))

        assert any(
            str(level.label) in response.content.decode() for level in ContributionLevel
        )

    def test_a_person_without_an_account_keeps_the_level_and_the_tab_marks_it(
        self, private_record
    ):
        manager = person_at(private_record, MANAGE)
        ghost = PersonFactory(is_active=False, password="x")
        added = Crediting(private_record).add(ghost)

        browser_as(manager).post(
            page_of(private_record, "edit", pk=added.pk), {"level": EDIT}
        )
        response = browser_as(manager).get(tab(private_record))

        added.refresh_from_db()
        assert added.level == EDIT
        assert row_of(response, ghost)["has_account"] is False
        assert RecordAccess(private_record).level_of(ghost) is None


@pytest.mark.django_db
class TestPrivateRecordTab:
    """A private record's tab answers as its overview does."""

    def test_a_stranger_and_a_visitor_get_404_on_every_page(
        self, private_record, newcomer
    ):
        colleague = ContributionFactory(content_object=private_record, level=VIEW)

        for viewer in (newcomer, None):
            for url in tab_pages(private_record, colleague):
                assert browser_as(viewer).get(url).status_code == 404, (viewer, url)
            for url in submissions(private_record, colleague):
                assert browser_as(viewer).post(url, {}).status_code == 404, (
                    viewer,
                    url,
                )

    def test_the_overview_gives_the_same_answer(self, private_record, newcomer):
        assert (
            browser_as(newcomer).get(private_record.get_absolute_url()).status_code
            == 404
        )

    def test_a_reader_opens_the_tab_and_is_refused_its_changing_pages(
        self, private_record
    ):
        reader = person_at(private_record, VIEW)
        colleague = ContributionFactory(content_object=private_record, level=VIEW)

        assert browser_as(reader).get(tab(private_record)).status_code == 200
        for url in tab_pages(private_record, colleague)[1:]:
            assert browser_as(reader).get(url).status_code == 403, url
        for url in submissions(private_record, colleague):
            assert browser_as(reader).post(url, {}).status_code == 403, url

    def test_a_visitor_is_sent_to_sign_in_on_a_public_records_changing_pages(
        self, public_chain
    ):
        colleague = ContributionFactory(content_object=public_chain.dataset, level=VIEW)

        for url in tab_pages(public_chain.dataset, colleague)[1:]:
            response = browser_as(None).get(url)
            assert response.status_code == 302 and "login" in response["Location"]

    def test_a_public_records_tab_opens_to_everyone(self, record, newcomer):
        assert browser_as(None).get(tab(record)).status_code == 200
        assert browser_as(newcomer).get(tab(record)).status_code == 200

    def test_a_person_listed_on_a_dataset_in_a_private_project_opens_the_datasets_tab(
        self, private_chain
    ):
        member = person_at(private_chain.dataset, VIEW)

        assert browser_as(member).get(tab(private_chain.dataset)).status_code == 200
        assert browser_as(member).get(tab(private_chain.project)).status_code == 404

    def test_a_person_listed_only_on_a_sample_opens_the_sample_and_not_the_dataset(
        self, private_chain
    ):
        member = person_at(private_chain.sample, VIEW)

        assert browser_as(member).get(tab(private_chain.sample)).status_code == 200
        assert browser_as(member).get(tab(private_chain.dataset)).status_code == 404

    def test_a_curator_opens_every_tab(self, private_record, curator):
        assert browser_as(curator).get(tab(private_record)).status_code == 200


@pytest.mark.django_db
class TestAddFromPortal:
    def test_a_person_is_added_and_the_manager_is_sent_to_the_edit_page(
        self, record, manager, newcomer
    ):
        response = browser_as(manager).post(
            page_of(record, "add-person"), {"via": "portal", "contributor": newcomer.pk}
        )

        added = record.contributors.get(contributor=newcomer)
        assert response.status_code == 302
        assert response["Location"] == page_of(record, "edit", pk=added.pk)
        assert RecordAccess(record).own_level(newcomer) == ContributionLevel.VIEW

    def test_an_organization_is_added_and_the_manager_is_sent_to_the_edit_page(
        self, record, manager
    ):
        organization = OrganizationFactory()

        response = browser_as(manager).post(
            page_of(record, "add-organization"),
            {"via": "portal", "contributor": organization.pk},
        )

        added = record.contributors.get(contributor=organization)
        assert response["Location"] == page_of(record, "edit", pk=added.pk)
        assert added.level is None

    def test_someone_already_listed_is_marked_in_the_search_results(
        self, record, manager, colleague
    ):
        response = browser_as(manager).get(
            page_of(record, "add-person"), {"q": colleague.contributor.name}
        )

        results = {r["contributor"].pk: r["listed"] for r in response.context["adding"]["results"]}
        assert results[colleague.contributor_id] is True

    def test_someone_already_listed_cannot_be_added_again(
        self, record, manager, colleague
    ):
        before = stored(record)

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {"via": "portal", "contributor": colleague.contributor_id},
        )

        assert stored(record) == before
        assert ERROR in {m.level for m in get_messages(response.wsgi_request)}

    def test_a_superuser_is_refused_without_an_error_page(self, record, manager):
        superuser = PersonFactory(is_active=True, is_superuser=True, password="x")
        before = stored(record)

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {"via": "portal", "contributor": superuser.pk},
        )

        assert response.status_code < 500
        assert stored(record) == before
        assert ERROR in {m.level for m in get_messages(response.wsgi_request)}


@pytest.mark.django_db
class TestEditRoles:
    def test_only_the_record_types_roles_are_offered(self, record, manager, colleague):
        response = browser_as(manager).get(page_of(record, "edit", pk=colleague.pk))

        offered = [r["concept"].name for r in response.context["roles"]]
        assert offered == list(record.CONTRIBUTOR_ROLES.values)

    def test_the_roles_chosen_are_saved_and_the_level_is_left_alone(
        self, record, manager, colleague
    ):
        names = list(record.CONTRIBUTOR_ROLES.values)[:2]

        response = browser_as(manager).post(
            page_of(record, "edit", pk=colleague.pk),
            {"roles": role_pks(*names), "level": ContributionLevel.VIEW},
        )

        colleague.refresh_from_db()
        assert response["Location"] == tab(record)
        assert {r.name for r in colleague.roles.all()} == set(names)
        assert colleague.level == ContributionLevel.VIEW

    def test_a_role_from_another_record_types_group_is_refused(
        self, record, manager, colleague
    ):
        elsewhere = Concept.objects.filter(vocabulary__name="fairdm-roles").exclude(
            name__in=record.CONTRIBUTOR_ROLES.values
        )[0]
        before = stored(record)

        response = browser_as(manager).post(
            page_of(record, "edit", pk=colleague.pk),
            {"roles": [elsewhere.pk], "level": ContributionLevel.VIEW},
        )

        assert response.status_code == 422
        assert "roles" in response.context["errors"]
        assert stored(record) == before

    def test_no_role_is_allowed(self, record, manager, colleague):
        colleague.roles.add(*Concept.objects.filter(name=record.CONTRIBUTOR_ROLES.values[0]))

        response = browser_as(manager).post(
            page_of(record, "edit", pk=colleague.pk),
            {"level": ContributionLevel.VIEW},
        )

        assert response["Location"] == tab(record)
        assert not colleague.roles.exists()


@pytest.mark.django_db
class TestRemoveContributor:
    def test_the_page_asks_before_anything_is_removed(self, record, manager, colleague):
        response = browser_as(manager).get(page_of(record, "remove", pk=colleague.pk))

        assert response.status_code == 200
        assert Contribution.objects.filter(pk=colleague.pk).exists()

    def test_confirming_removes_the_contributor(self, record, manager, colleague):
        response = browser_as(manager).post(
            page_of(record, "remove", pk=colleague.pk)
        )

        assert response["Location"] == tab(record)
        assert not Contribution.objects.filter(pk=colleague.pk).exists()
        assert RecordAccess(record).own_level(colleague.contributor) is None
        after = browser_as(None).get(tab(record))
        listed = [e["contributor"].pk for e in after.context["people"]["rows"]]
        assert colleague.contributor_id not in listed


@pytest.fixture
def data_curator(db):
    """A person who can manage any record through the Data Curator role, credited on none."""
    person = PersonFactory(is_active=True, is_claimed=True, password="x")
    person.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))
    return person


@pytest.fixture(params=["manager", "curator", "data_curator"])
def asker(request):
    """Each person who may open the editing pages of a record in turn."""
    return request.getfixturevalue(request.param)


@pytest.mark.django_db
class TestLastManagerPages:
    def test_lowering_the_only_manager_is_refused_on_the_level_field(
        self, record, manager, asker
    ):
        contribution = record.contributors.get(contributor=manager)
        before = stored(record)

        response = browser_as(asker).post(
            page_of(record, "edit", pk=contribution.pk),
            {
                "roles": role_pks(record.CONTRIBUTOR_ROLES.values[0]),
                "level": ContributionLevel.EDIT,
            },
        )

        assert response.status_code == 422
        assert "level" in response.context["errors"]
        assert stored(record) == before

    def test_keeping_the_only_manager_at_the_manage_level_saves_their_roles(
        self, record, manager, asker
    ):
        contribution = record.contributors.get(contributor=manager)
        names = [record.CONTRIBUTOR_ROLES.values[0]]

        response = browser_as(asker).post(
            page_of(record, "edit", pk=contribution.pk),
            {"roles": role_pks(*names), "level": ContributionLevel.MANAGE},
        )

        assert response["Location"] == tab(record)
        assert {r.name for r in contribution.roles.all()} == set(names)

    def test_lowering_one_of_two_managers_is_saved(self, record, manager, asker):
        other = PersonFactory(is_active=True, is_claimed=True, password="x")
        ContributionFactory(
            content_object=record, contributor=other, level=ContributionLevel.MANAGE
        )
        contribution = record.contributors.get(contributor=manager)

        response = browser_as(asker).post(
            page_of(record, "edit", pk=contribution.pk),
            {"level": ContributionLevel.EDIT},
        )

        contribution.refresh_from_db()
        assert response["Location"] == tab(record)
        assert contribution.level == ContributionLevel.EDIT

    def test_the_remove_page_refuses_the_only_manager_and_offers_no_way_to_go_ahead(
        self, record, manager, asker
    ):
        contribution = record.contributors.get(contributor=manager)

        response = browser_as(asker).get(page_of(record, "remove", pk=contribution.pk))

        assert response.status_code == 200
        assert response.context["refused"] is True
        assert not soup_of(response).select("main form[method=post]")

    def test_submitting_the_remove_page_for_the_only_manager_changes_nothing(
        self, record, manager, asker
    ):
        contribution = record.contributors.get(contributor=manager)
        before = stored(record)

        response = browser_as(asker).post(
            page_of(record, "remove", pk=contribution.pk)
        )

        assert response.status_code == 422
        assert response.context["refused"] is True
        assert stored(record) == before

    def test_the_remove_page_goes_ahead_when_another_person_can_manage(
        self, record, manager, asker
    ):
        other = PersonFactory(is_active=True, is_claimed=True, password="x")
        ContributionFactory(
            content_object=record, contributor=other, level=ContributionLevel.MANAGE
        )
        contribution = record.contributors.get(contributor=manager)
        client = browser_as(asker)

        page = client.get(page_of(record, "remove", pk=contribution.pk))
        response = client.post(page_of(record, "remove", pk=contribution.pk))

        assert page.context["refused"] is False
        assert soup_of(page).select("main form[method=post]")
        assert response["Location"] == tab(record)
        assert not Contribution.objects.filter(pk=contribution.pk).exists()


@pytest.mark.django_db
class TestAffiliationChoice:
    def test_the_persons_affiliations_are_offered_with_the_primary_selected(
        self, record, manager, newcomer, affiliate, institutes
    ):
        affiliate(newcomer)

        response = browser_as(manager).get(
            page_of(record, "add-person"), {"person": newcomer.pk}
        )

        values, selected = offered(response, "portal-affiliation")
        assert values == [
            f"org:{institutes.today.pk}",
            f"org:{institutes.earlier.pk}",
            "other",
            "none",
        ]
        assert selected == [f"org:{institutes.today.pk}"]

    def test_a_person_with_no_affiliation_starts_on_none(
        self, record, manager, newcomer
    ):
        response = browser_as(manager).get(
            page_of(record, "add-person"), {"person": newcomer.pk}
        )

        values, selected = offered(response, "portal-affiliation")
        assert values == ["other", "none"]
        assert selected == ["none"]

    def test_an_earlier_affiliation_can_be_chosen(
        self, record, manager, newcomer, affiliate, institutes
    ):
        affiliate(newcomer)

        add_from_portal(
            record, manager, newcomer, affiliation=f"org:{institutes.earlier.pk}"
        )

        added = record.contributors.get(contributor=newcomer)
        assert added.affiliation == institutes.earlier

    def test_another_organization_in_the_portal_can_be_chosen_by_name(
        self, record, manager, newcomer, affiliate, institutes
    ):
        affiliate(newcomer)
        before = Organization.objects.count()

        add_from_portal(
            record,
            manager,
            newcomer,
            affiliation="other",
            affiliation_name=institutes.elsewhere.name,
        )

        added = record.contributors.get(contributor=newcomer)
        assert added.affiliation == institutes.elsewhere
        assert Organization.objects.count() == before

    def test_an_organization_not_in_the_portal_is_made_from_its_name(
        self, record, manager, newcomer
    ):
        add_from_portal(
            record,
            manager,
            newcomer,
            affiliation="other",
            affiliation_name="A Brand New Institute",
        )

        made = Organization.objects.get(name="A Brand New Institute")
        added = record.contributors.get(contributor=newcomer)
        assert added.affiliation == made
        assert record.contributors.filter(contributor=made).exists()

    def test_an_empty_name_for_another_organization_is_refused_on_the_field(
        self, record, manager, newcomer
    ):
        before, organizations = stored(record), Organization.objects.count()

        response = add_from_portal(
            record, manager, newcomer, affiliation="other", affiliation_name="  "
        )

        assert response.status_code == 422
        assert "affiliation" in response.context["adding"]["errors"]
        assert stored(record) == before
        assert Organization.objects.count() == organizations

    def test_none_can_be_chosen(self, record, manager, newcomer, affiliate):
        affiliate(newcomer)

        add_from_portal(record, manager, newcomer, affiliation="none")

        added = record.contributors.get(contributor=newcomer)
        assert added.affiliation is None
        assert RecordAccess(record).own_level(newcomer) == ContributionLevel.VIEW

    def test_an_affiliation_the_person_does_not_hold_is_refused(
        self, record, manager, newcomer, affiliate, institutes
    ):
        affiliate(newcomer)
        before = stored(record)

        response = add_from_portal(
            record, manager, newcomer, affiliation=f"org:{institutes.elsewhere.pk}"
        )

        assert response.status_code == 422
        assert stored(record) == before

    def test_the_person_is_shown_with_the_organization_chosen(
        self, record, manager, newcomer, affiliate, institutes
    ):
        affiliate(newcomer)
        add_from_portal(
            record, manager, newcomer, affiliation=f"org:{institutes.earlier.pk}"
        )

        response = browser_as(manager).get(tab(record))

        assert row_of(response, newcomer)["affiliation"] == institutes.earlier
        assert institutes.earlier.get_absolute_url() in links(response)

    def test_the_organization_is_among_the_organizations_once(
        self, record, manager, newcomer, affiliate, institutes
    ):
        affiliate(newcomer)
        add_from_portal(
            record, manager, newcomer, affiliation=f"org:{institutes.today.pk}"
        )
        other = PersonFactory(is_active=True, is_claimed=True, password="x")
        add_from_portal(
            record,
            manager,
            other,
            affiliation="other",
            affiliation_name=institutes.today.name,
        )

        response = browser_as(manager).get(tab(record))

        listed = [
            e["contributor"].pk for e in response.context["organizations"]["rows"]
        ]
        assert listed.count(institutes.today.pk) == 1

    def test_a_person_added_with_none_is_shown_with_none_whatever_the_profile_says(
        self, record, manager, newcomer, affiliate, institutes
    ):
        affiliate(newcomer)
        add_from_portal(record, manager, newcomer, affiliation="none")

        response = browser_as(manager).get(tab(record))

        assert row_of(response, newcomer)["affiliation"] is None
        assert institutes.today.get_absolute_url() not in links(response)

    def test_a_later_change_of_primary_affiliation_changes_nothing_on_the_record(
        self, record, manager, newcomer, affiliate, institutes
    ):
        affiliate(newcomer)
        add_from_portal(
            record, manager, newcomer, affiliation=f"org:{institutes.earlier.pk}"
        )

        moved_again = institutes.today.affiliations.get(person=newcomer)
        moved_again.is_primary = False
        moved_again.save()
        newcomer.affiliations.filter(organization=institutes.earlier).update(
            is_primary=True, end_date=None
        )
        response = browser_as(manager).get(tab(record))

        assert row_of(response, newcomer)["affiliation"] == institutes.earlier

    def test_deleting_the_organization_from_the_portal_leaves_the_person_with_none(
        self, record, manager, newcomer, affiliate, institutes
    ):
        affiliate(newcomer)
        add_from_portal(
            record, manager, newcomer, affiliation=f"org:{institutes.earlier.pk}"
        )

        institutes.earlier.delete()
        response = browser_as(manager).get(tab(record))

        assert response.status_code == 200
        assert row_of(response, newcomer)["affiliation"] is None

    def test_the_edit_page_offers_the_same_choice_with_the_current_one_selected(
        self, record, manager, colleague, affiliate, institutes
    ):
        affiliate(colleague.contributor)
        colleague.affiliation = institutes.earlier
        colleague.save()

        response = browser_as(manager).get(page_of(record, "edit", pk=colleague.pk))

        values, selected = offered(response, "affiliation")
        assert values == [
            f"org:{institutes.today.pk}",
            f"org:{institutes.earlier.pk}",
            "other",
            "none",
        ]
        assert selected == [f"org:{institutes.earlier.pk}"]

    def test_the_edit_page_selects_none_for_a_person_credited_from_none(
        self, record, manager, colleague, affiliate
    ):
        affiliate(colleague.contributor)

        response = browser_as(manager).get(page_of(record, "edit", pk=colleague.pk))

        assert offered(response, "affiliation")[1] == ["none"]

    def test_the_edit_page_selects_another_organization_the_person_was_credited_from(
        self, record, manager, colleague, institutes
    ):
        colleague.affiliation = institutes.elsewhere
        colleague.save()

        response = browser_as(manager).get(page_of(record, "edit", pk=colleague.pk))

        assert offered(response, "affiliation")[1] == ["other"]
        assert (
            response.context["affiliation"]["other_name"] == institutes.elsewhere.name
        )

    def test_saving_a_different_organization_changes_that_and_nothing_else(
        self, record, manager, colleague, affiliate, institutes
    ):
        affiliate(colleague.contributor)
        colleague.affiliation = institutes.earlier
        colleague.save()
        names = list(record.CONTRIBUTOR_ROLES.values)[:1]
        colleague.roles.add(*Concept.objects.filter(name__in=names))

        response = browser_as(manager).post(
            page_of(record, "edit", pk=colleague.pk),
            {
                "roles": role_pks(*names),
                "level": ContributionLevel.VIEW,
                "affiliation": f"org:{institutes.today.pk}",
            },
        )

        colleague.refresh_from_db()
        assert response["Location"] == tab(record)
        assert colleague.affiliation == institutes.today
        assert colleague.level == ContributionLevel.VIEW
        assert {r.name for r in colleague.roles.all()} == set(names)
        assert record.contributors.filter(contributor=institutes.today).count() == 1

    def test_the_edit_page_can_set_the_organization_to_none(
        self, record, manager, colleague, institutes
    ):
        colleague.affiliation = institutes.today
        colleague.save()

        browser_as(manager).post(
            page_of(record, "edit", pk=colleague.pk),
            {"level": ContributionLevel.VIEW, "affiliation": "none"},
        )

        colleague.refresh_from_db()
        assert colleague.affiliation is None

    def test_an_empty_name_on_the_edit_page_is_refused_and_nothing_is_saved(
        self, record, manager, colleague, institutes
    ):
        colleague.affiliation = institutes.today
        colleague.save()
        names = list(record.CONTRIBUTOR_ROLES.values)[:1]
        before = stored(record)

        response = browser_as(manager).post(
            page_of(record, "edit", pk=colleague.pk),
            {
                "roles": role_pks(*names),
                "level": ContributionLevel.EDIT,
                "affiliation": "other",
                "affiliation_name": "",
            },
        )

        colleague.refresh_from_db()
        assert response.status_code == 422
        assert "affiliation" in response.context["errors"]
        assert stored(record) == before
        assert colleague.affiliation == institutes.today

    def test_an_organization_typed_on_the_edit_page_is_made_when_it_is_new(
        self, record, manager, colleague
    ):
        browser_as(manager).post(
            page_of(record, "edit", pk=colleague.pk),
            {
                "level": ContributionLevel.VIEW,
                "affiliation": "other",
                "affiliation_name": "Newly Typed Institute",
            },
        )

        colleague.refresh_from_db()
        assert colleague.affiliation.name == "Newly Typed Institute"

    def test_an_organization_made_for_a_refused_save_is_not_kept(
        self, record, manager, colleague
    ):
        response = browser_as(manager).post(
            page_of(record, "edit", pk=colleague.pk),
            {
                "level": "",
                "affiliation": "other",
                "affiliation_name": "Never Saved Institute",
            },
        )

        assert response.status_code == 422
        assert not Organization.objects.filter(name="Never Saved Institute").exists()


@pytest.fixture
def credited_from(record, colleague, institutes):
    """An organization on the record that the colleague is credited from."""
    colleague.affiliation = institutes.today
    colleague.save()
    return ContributionFactory(
        content_object=record, contributor=institutes.today, level=None
    )


@pytest.mark.django_db
class TestOrganizationRemoval:
    def test_no_removal_is_offered_for_an_organization_people_are_credited_from(
        self, record, manager, colleague, credited_from, institutes
    ):
        response = browser_as(manager).get(tab(record))

        entry = row_of(response, institutes.today)
        assert entry["removable"] is False
        assert [person.pk for person in entry["attached"]] == [colleague.contributor_id]

    def test_a_direct_request_is_refused_and_names_the_people(
        self, record, manager, colleague, credited_from
    ):
        before = stored(record)

        response = browser_as(manager).post(
            page_of(record, "remove", pk=credited_from.pk)
        )

        assert response.status_code == 422
        assert stored(record) == before
        named = response.context["entry"]["attached"]
        assert [person.pk for person in named] == [colleague.contributor_id]

    def test_the_remove_page_names_them_before_anything_is_asked(
        self, record, manager, colleague, credited_from
    ):
        response = browser_as(manager).get(
            page_of(record, "remove", pk=credited_from.pk)
        )

        assert response.status_code == 200
        named = response.context["entry"]["attached"]
        assert [person.pk for person in named] == [colleague.contributor_id]

    def test_an_organization_nobody_is_credited_from_is_removed_on_confirming(
        self, record, manager, partner
    ):
        response = browser_as(manager).post(page_of(record, "remove", pk=partner.pk))

        assert response["Location"] == tab(record)
        assert not Contribution.objects.filter(pk=partner.pk).exists()

    def test_an_organization_is_removable_once_its_last_person_leaves(
        self, record, manager, colleague, credited_from, institutes
    ):
        browser_as(manager).post(page_of(record, "remove", pk=colleague.pk))

        response = browser_as(manager).get(tab(record))
        assert row_of(response, institutes.today)["removable"] is True
        browser_as(manager).post(page_of(record, "remove", pk=credited_from.pk))

        assert not Contribution.objects.filter(pk=credited_from.pk).exists()

    def test_an_organization_is_removable_once_its_last_person_is_credited_elsewhere(
        self, record, manager, colleague, credited_from, institutes
    ):
        browser_as(manager).post(
            page_of(record, "edit", pk=colleague.pk),
            {"level": ContributionLevel.VIEW, "affiliation": "none"},
        )

        response = browser_as(manager).get(tab(record))

        assert row_of(response, institutes.today)["removable"] is True
        assert Contribution.objects.filter(pk=credited_from.pk).exists()


def orcid_way(registry_network, recorded):
    """ORCID behind the page for adding a person, with its responses replaced."""
    registry_network.answer(ORCID_SEARCH, recorded("orcid-search"))
    registry_network.answer(orcid_record_address(JOSIAH), recorded("orcid-record"))

    def answer_search(more=False, empty=False):
        body = recorded("orcid-search")
        body["num-found"] = 3 + (60 if more else 0)
        if empty:
            body = {"expanded-result": None, "num-found": 0}
        registry_network.answer(ORCID_SEARCH, body)

    return SimpleNamespace(
        page="add-person",
        model=Person,
        type="ORCID",
        term="Carberry",
        identifier=JOSIAH,
        stored=JOSIAH,
        name="Josiah Carberry",
        search_address=ORCID_SEARCH,
        record_address=orcid_record_address(JOSIAH),
        answer_search=answer_search,
        network=registry_network,
        factory=PersonFactory,
    )


def ror_way(registry_network, recorded):
    """ROR behind the page for adding an organization, with its responses replaced."""
    registry_network.answer(ROR_SEARCH, recorded("ror-search"))
    registry_network.answer(ror_record_address(GFZ), recorded("ror-record"))

    def answer_search(more=False, empty=False):
        body = recorded("ror-search")
        if empty:
            body = {"number_of_results": 0, "items": []}
        elif more:
            body["number_of_results"] = 214
        registry_network.answer(ROR_SEARCH, body)

    return SimpleNamespace(
        page="add-organization",
        model=Organization,
        type="ROR",
        term="Potsdam",
        identifier=f"https://ror.org/{GFZ}",
        stored=GFZ,
        name="GFZ Helmholtz Centre for Geosciences",
        search_address=ROR_SEARCH,
        record_address=ror_record_address(GFZ),
        answer_search=answer_search,
        network=registry_network,
        factory=OrganizationFactory,
    )


@pytest.fixture
def way_person(registry_network, recorded):
    """ORCID alone, for what only the page for adding a person has."""
    return orcid_way(registry_network, recorded)


@pytest.fixture
def way(request, registry_network, recorded):
    """The registry behind one of the two add pages: ORCID for a person, ROR for an organization."""
    build = {"person": orcid_way, "organization": ror_way}[request.param]
    return build(registry_network, recorded)


both_ways = pytest.mark.parametrize("way", ["person", "organization"], indirect=True)


@pytest.mark.django_db
class TestAddPages:
    @pytest.mark.parametrize("page", ["add-person", "add-organization"])
    def test_each_page_carries_all_three_ways_in_one_response(
        self, record, manager, registry_network, page
    ):
        response = browser_as(manager).get(page_of(record, page))

        soup = soup_of(response)
        assert response.status_code == 200
        for tab_id in ("tab-portal", "tab-registry", "tab-new"):
            assert soup.find(id=tab_id) is not None
        assert len(soup.select("input[role=tab]")) == 3
        assert registry_network.calls == []

    @pytest.mark.parametrize("page", ["add-person", "add-organization"])
    @pytest.mark.parametrize(
        ("via", "open_tab"), [("portal", 0), ("registry", 1), ("new", 2)]
    )
    def test_a_response_reopens_on_the_way_named_in_the_address(
        self, record, manager, page, via, open_tab
    ):
        response = browser_as(manager).get(page_of(record, page), {"via": via})

        radios = soup_of(response).select("input[role=tab]")
        assert [i for i, radio in enumerate(radios) if radio.has_attr("checked")] == [
            open_tab
        ]
        adding = response.context["adding"]
        assert [adding["on_portal"], adding["on_registry"], adding["on_new"]] == [
            i == open_tab for i in range(3)
        ]

    @pytest.mark.parametrize("page", ["add-person", "add-organization"])
    def test_a_way_nobody_named_opens_on_the_portal(self, record, manager, page):
        for via in ({}, {"via": "elsewhere"}):
            response = browser_as(manager).get(page_of(record, page), via)

            assert response.context["adding"]["on_portal"] is True

    @both_ways
    def test_each_way_keeps_its_own_search_term(self, record, manager, way):
        response = browser_as(manager).get(
            page_of(record, way.page), {"via": "registry", "q": "Alice", "rq": way.term}
        )

        soup = soup_of(response)
        assert soup.find(id="portal-search")["value"] == "Alice"
        assert soup.find(id="registry-search")["value"] == way.term

    @both_ways
    def test_a_portal_search_does_not_ask_the_registry(self, record, manager, way):
        browser_as(manager).get(
            page_of(record, way.page), {"via": "portal", "q": "Alice", "rq": way.term}
        )

        assert way.network.calls == []

    @pytest.mark.parametrize("page", ["add-person", "add-organization"])
    def test_the_portal_search_says_when_there_are_more_results_than_it_shows(
        self, record, manager, page
    ):
        factory = PersonFactory if page == "add-person" else OrganizationFactory
        for number in range(30):
            factory(name=f"Searchable {number:02d}")
        address = page_of(record, page)

        everything = browser_as(manager).get(
            address, {"via": "portal", "q": "Searchable"}
        )
        narrowed = browser_as(manager).get(
            address, {"via": "portal", "q": "Searchable 07"}
        )

        assert everything.context["adding"]["results_more"] is True
        assert 0 < len(everything.context["adding"]["results"]) < 30
        assert soup_of(everything).select_one("#tab-portal [data-results=more]")
        assert narrowed.context["adding"]["results_more"] is False
        assert soup_of(narrowed).select_one("#tab-portal [data-results=more]") is None

    def test_nobody_but_a_manager_makes_anything_or_asks_a_registry(
        self, record, manager, reader, newcomer, registry_network, recorded
    ):
        registry_network.answer(ORCID_SEARCH, recorded("orcid-search"))
        registry_network.answer(orcid_record_address(JOSIAH), recorded("orcid-record"))
        registry_network.answer(ROR_SEARCH, recorded("ror-search"))
        registry_network.answer(ror_record_address(GFZ), recorded("ror-record"))
        person, organization = (
            page_of(record, "add-person"),
            page_of(record, "add-organization"),
        )
        requests_made = [
            ("get", person, {"via": "registry", "rq": "Carberry"}),
            ("get", person, {"via": "registry", "chosen": JOSIAH}),
            ("get", organization, {"via": "registry", "rq": "Potsdam"}),
            ("post", person, {"via": "registry", "registry_id": JOSIAH}),
            ("post", organization, {"via": "registry", "registry_id": GFZ}),
            ("post", person, {"via": "new", "given": "Una", "family": "Made"}),
            ("post", organization, {"via": "new", "name": "Made Institute"}),
        ]
        before, listed = made(), stored(record)

        for viewer, refused in ((reader, 403), (newcomer, 403), (None, 302)):
            for method, address, data in requests_made:
                response = getattr(browser_as(viewer), method)(address, data)
                assert response.status_code == refused, (viewer, method, address, data)

        assert made() == before
        assert stored(record) == listed
        assert registry_network.calls == []


@pytest.mark.django_db
class TestAddFromRegistry:
    @both_ways
    def test_a_search_lists_the_matches_with_a_way_to_choose_each(
        self, record, manager, way
    ):
        response = browser_as(manager).get(
            page_of(record, way.page), {"via": "registry", "rq": way.term}
        )

        adding = response.context["adding"]
        assert response.status_code == 200
        assert adding["on_registry"] is True
        assert adding["registry_unavailable"] is False
        assert way.identifier in [r["id"] for r in adding["registry_results"]]
        choices = soup_of(response).select("#tab-registry a[href*='chosen=']")
        assert len(choices) == len(adding["registry_results"])
        assert [call.url for call in way.network.calls] == [way.search_address]

    @both_ways
    def test_a_search_with_no_match_says_so_and_nothing_else_changes(
        self, record, manager, way
    ):
        way.answer_search(empty=True)

        response = browser_as(manager).get(
            page_of(record, way.page), {"via": "registry", "rq": "Nobody"}
        )

        adding = response.context["adding"]
        assert response.status_code == 200
        assert adding["registry_results"] == []
        assert adding["registry_unavailable"] is False
        assert adding["registry_more"] is False
        assert soup_of(response).select("#tab-registry a[href*='chosen=']") == []

    @both_ways
    def test_the_page_says_when_a_registry_has_more_matches_than_it_shows(
        self, record, manager, way
    ):
        address = page_of(record, way.page)
        query = {"via": "registry", "rq": way.term}

        way.answer_search(more=True)
        more = browser_as(manager).get(address, query)
        way.answer_search(more=False)
        all_shown = browser_as(manager).get(address, query)

        assert more.context["adding"]["registry_more"] is True
        assert soup_of(more).select_one("#tab-registry [data-results=more]")
        assert all_shown.context["adding"]["registry_more"] is False
        assert (
            soup_of(all_shown).select_one("#tab-registry [data-results=more]") is None
        )

    @both_ways
    def test_a_chosen_record_is_fetched_by_identifier_and_nothing_is_made(
        self, record, manager, way
    ):
        before = made()

        response = browser_as(manager).get(
            page_of(record, way.page),
            {"via": "registry", "rq": way.term, "chosen": way.identifier},
        )

        chosen = response.context["adding"]["chosen"]
        assert chosen["record"]["id"] == way.identifier
        assert chosen["record"]["name"] == way.name
        form = soup_of(response).select_one("#tab-registry input[name=registry_id]")
        assert form["value"] == way.identifier
        assert [call.url for call in way.network.calls] == [way.record_address]
        assert made() == before

    @both_ways
    def test_adding_makes_the_profile_and_sends_the_manager_to_the_edit_page(
        self, record, manager, way
    ):
        response = browser_as(manager).post(
            page_of(record, way.page),
            {"via": "registry", "registry_id": way.identifier},
        )

        contributor = way.model.objects.get(identifiers__value=way.stored)
        added = record.contributors.get(contributor=contributor)
        assert response.status_code == 302
        assert response["Location"] == page_of(record, "edit", pk=added.pk)
        assert contributor.name == way.name
        assert contributor.identifiers.get().type == way.type

    def test_a_person_added_from_orcid_has_no_account(
        self, record, manager, way_person
    ):
        browser_as(manager).post(
            page_of(record, "add-person"), {"via": "registry", "registry_id": JOSIAH}
        )

        person = Person.objects.get(identifiers__value=JOSIAH)
        assert person.email is None
        assert not person.has_usable_password()
        assert person.account_state == AccountState.GHOST
        assert not person.can_sign_in()
        assert RecordAccess(record).own_level(person) == ContributionLevel.VIEW

    @both_ways
    def test_the_profile_is_made_from_a_fresh_fetch_not_from_posted_fields(
        self, record, manager, way
    ):
        browser_as(manager).post(
            page_of(record, way.page),
            {
                "via": "registry",
                "registry_id": way.identifier,
                "name": "Mallory Forged",
                "given": "Mallory",
                "family": "Forged",
                "detail": "Forged University",
                "record": {"name": "Mallory Forged"},
            },
        )

        assert way.network.calls[-1].url == way.record_address
        assert way.model.objects.get(identifiers__value=way.stored).name == way.name
        assert not way.model.objects.filter(name__icontains="Mallory").exists()

    @both_ways
    def test_an_identifier_that_is_not_well_formed_makes_no_request_and_nothing(
        self, record, manager, way
    ):
        before, listed = made(), stored(record)

        for forged in ("../0000-0001-5109-3700", "https://evil.example/x", "x" * 400):
            response = browser_as(manager).post(
                page_of(record, way.page), {"via": "registry", "registry_id": forged}
            )
            assert response.status_code < 500

        assert way.network.calls == []
        assert made() == before
        assert stored(record) == listed

    @both_ways
    def test_an_identifier_the_registry_does_not_know_makes_nothing(
        self, record, manager, way, recorded
    ):
        way.network.answer(way.record_address, recorded("ror-missing"), status=404)
        before, listed = made(), stored(record)

        response = browser_as(manager).post(
            page_of(record, way.page),
            {"via": "registry", "registry_id": way.identifier},
        )

        assert response.status_code < 500
        assert made() == before
        assert stored(record) == listed

    def test_a_record_with_no_public_name_makes_nothing(
        self, record, manager, way_person, recorded
    ):
        body = recorded("orcid-record")
        body["person"]["name"] = None
        way_person.network.answer(way_person.record_address, body)
        before, listed = made(), stored(record)

        response = browser_as(manager).post(
            page_of(record, "add-person"), {"via": "registry", "registry_id": JOSIAH}
        )

        assert response.status_code < 500
        assert made() == before
        assert stored(record) == listed

    @both_ways
    def test_a_profile_the_portal_holds_under_the_identifier_is_used(
        self, record, manager, way
    ):
        held = way.factory()
        ContributorIdentifierFactory(related=held, type=way.type, value=way.stored)
        before = made()

        browser_as(manager).post(
            page_of(record, way.page),
            {"via": "registry", "registry_id": way.identifier},
        )

        assert made() == before
        assert record.contributors.filter(contributor=held).exists()

    @both_ways
    def test_someone_already_on_the_record_is_not_added_again(
        self, record, manager, way
    ):
        held = way.factory()
        ContributorIdentifierFactory(related=held, type=way.type, value=way.stored)
        ContributionFactory(content_object=record, contributor=held, level=None)
        before, listed = made(), stored(record)

        response = browser_as(manager).post(
            page_of(record, way.page),
            {"via": "registry", "registry_id": way.identifier},
        )

        assert response.status_code < 500
        assert ERROR in {m.level for m in get_messages(response.wsgi_request)}
        assert made() == before
        assert stored(record) == listed

    def test_a_person_from_orcid_is_asked_for_their_organization(
        self, record, manager, way_person
    ):
        response = browser_as(manager).get(
            page_of(record, "add-person"),
            {"via": "registry", "rq": "Carberry", "chosen": JOSIAH},
        )

        values, selected = offered(response, "registry-affiliation")
        assert values == ["other", "none"]
        assert selected == ["other"]
        suggested = soup_of(response).select_one(
            "#registry-affiliation input[name=affiliation_name]"
        )
        assert suggested["value"] in {"Brown University", "Wesleyan University"}

    def test_the_organization_chosen_for_a_person_from_orcid_is_kept_with_the_credit(
        self, record, manager, way_person
    ):
        browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "registry",
                "registry_id": JOSIAH,
                "affiliation": "other",
                "affiliation_name": "Brown University",
            },
        )

        person = Person.objects.get(identifiers__value=JOSIAH)
        brown = Organization.objects.get(name="Brown University")
        assert record.contributors.get(contributor=person).affiliation == brown
        assert record.contributors.filter(contributor=brown).exists()

    def test_none_can_be_chosen_for_a_person_from_orcid(
        self, record, manager, way_person
    ):
        browser_as(manager).post(
            page_of(record, "add-person"),
            {"via": "registry", "registry_id": JOSIAH, "affiliation": "none"},
        )

        person = Person.objects.get(identifiers__value=JOSIAH)
        assert record.contributors.get(contributor=person).affiliation is None

    def test_a_person_the_portal_holds_is_offered_their_own_affiliations(
        self, record, manager, way_person, affiliate, institutes
    ):
        held = affiliate(PersonFactory())
        ContributorIdentifierFactory(related=held, type="ORCID", value=JOSIAH)

        response = browser_as(manager).get(
            page_of(record, "add-person"),
            {"via": "registry", "rq": "Carberry", "chosen": JOSIAH},
        )
        browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "registry",
                "registry_id": JOSIAH,
                "affiliation": f"org:{institutes.earlier.pk}",
            },
        )

        values, _selected = offered(response, "registry-affiliation")
        assert f"org:{institutes.today.pk}" in values
        assert (
            record.contributors.get(contributor=held).affiliation == institutes.earlier
        )

    def test_a_refused_organization_makes_no_profile_and_keeps_the_chosen_record(
        self, record, manager, way_person
    ):
        before, listed = made(), stored(record)

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "registry",
                "registry_id": JOSIAH,
                "affiliation": "other",
                "affiliation_name": " ",
            },
        )

        adding = response.context["adding"]
        assert response.status_code == 422
        assert "affiliation" in adding["errors"]
        assert adding["on_registry"] is True
        assert adding["chosen"]["record"]["id"] == JOSIAH
        assert made() == before
        assert stored(record) == listed

    def test_an_organization_made_for_a_refused_credit_is_not_kept(
        self, record, manager, way_person
    ):
        held = PersonFactory()
        ContributorIdentifierFactory(related=held, type="ORCID", value=JOSIAH)
        ContributionFactory(content_object=record, contributor=held, level=None)
        before = made()

        browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "registry",
                "registry_id": JOSIAH,
                "affiliation": "other",
                "affiliation_name": "Orphan Institute",
            },
        )

        assert made() == before
        assert not Organization.objects.filter(name="Orphan Institute").exists()

    def test_a_superuser_found_by_orcid_is_refused_without_an_error_page(
        self, record, manager, way_person
    ):
        superuser = PersonFactory(is_active=True, is_superuser=True, password="x")
        ContributorIdentifierFactory(related=superuser, type="ORCID", value=JOSIAH)
        before = stored(record)

        response = browser_as(manager).post(
            page_of(record, "add-person"), {"via": "registry", "registry_id": JOSIAH}
        )

        assert response.status_code < 500
        assert stored(record) == before
        assert ERROR in {m.level for m in get_messages(response.wsgi_request)}

    @both_ways
    @pytest.mark.parametrize(("error", "status"), UNREACHABLE)
    def test_a_registry_that_cannot_be_reached_says_so_and_answers_200(
        self, record, manager, way, error, status
    ):
        if error is not None:
            way.network.fail(way.search_address, error)
        else:
            way.network.answer(way.search_address, {"errors": ["down"]}, status=status)

        response = browser_as(manager).get(
            page_of(record, way.page), {"via": "registry", "rq": way.term}
        )

        adding = response.context["adding"]
        assert response.status_code == 200
        assert adding["registry_unavailable"] is True
        assert adding["registry_results"] == []
        assert adding["on_registry"] is True
        assert soup_of(response).select_one("#tab-registry [data-registry=unavailable]")

    @both_ways
    def test_a_registry_that_can_be_reached_does_not_say_it_cannot(
        self, record, manager, way
    ):
        response = browser_as(manager).get(
            page_of(record, way.page), {"via": "registry", "rq": way.term}
        )

        assert soup_of(response).select_one("[data-registry=unavailable]") is None

    @both_ways
    def test_choosing_while_a_registry_cannot_be_reached_answers_200_and_makes_nothing(
        self, record, manager, way
    ):
        way.network.fail(way.record_address, requests.ConnectionError("down"))
        before, listed = made(), stored(record)
        address = page_of(record, way.page)

        chosen = browser_as(manager).get(
            address, {"via": "registry", "rq": way.term, "chosen": way.identifier}
        )
        added = browser_as(manager).post(
            address, {"via": "registry", "registry_id": way.identifier}
        )

        for response in (chosen, added):
            assert response.status_code == 200
            assert response.context["adding"]["registry_unavailable"] is True
            assert response.context["adding"]["chosen"] is None
        assert made() == before
        assert stored(record) == listed

    @both_ways
    def test_the_other_two_ways_still_work_while_a_registry_cannot_be_reached(
        self, record, manager, way
    ):
        way.network.fail(way.search_address, requests.Timeout("slow"))
        way.network.fail(way.record_address, requests.Timeout("slow"))
        address = page_of(record, way.page)
        known = way.factory(name="Findable Name")
        data = {"via": "new", "name": "Typed Name", "given": "Typed", "family": "Name"}

        searched = browser_as(manager).get(address, {"via": "portal", "q": "Findable"})
        from_portal = browser_as(manager).post(
            address, {"via": "portal", "contributor": known.pk}
        )
        by_hand = browser_as(manager).post(address, data)

        assert [r["contributor"].pk for r in searched.context["adding"]["results"]] == [
            known.pk
        ]
        assert from_portal.status_code == 302
        assert by_hand.status_code == 302
        assert record.contributors.filter(contributor=known).exists()
        assert record.contributors.filter(contributor__name="Typed Name").exists()
        assert way.network.calls == []


@pytest.mark.django_db
class TestAddByHand:
    def test_a_person_needs_both_names(self, record, manager):
        before, listed = made(), stored(record)
        address = page_of(record, "add-person")

        for given, family, missing in (
            ("", "Jones", {"given"}),
            ("Ada", "", {"family"}),
            ("", "", {"given", "family"}),
            ("  ", "Jones", {"given"}),
        ):
            response = browser_as(manager).post(
                address,
                {
                    "via": "new",
                    "given": given,
                    "family": family,
                    "email": "x@example.com",
                },
            )

            adding = response.context["adding"]
            assert response.status_code == 422
            assert adding["on_new"] is True
            for field in missing:
                assert adding["form"].has_error(field, code="required")
                assert field in adding["errors"]
            assert adding["values"]["email"] == "x@example.com"

        assert made() == before
        assert stored(record) == listed

    def test_a_person_is_made_with_no_account_and_the_manager_is_sent_to_the_edit_page(
        self, record, manager
    ):
        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {"via": "new", "given": "Ada", "family": "Lovelace"},
        )

        person = Person.objects.get(first_name="Ada", last_name="Lovelace")
        added = record.contributors.get(contributor=person)
        assert response.status_code == 302
        assert response["Location"] == page_of(record, "edit", pk=added.pk)
        assert person.name == "Ada Lovelace"
        assert person.email is None
        assert not person.has_usable_password()
        assert person.account_state == AccountState.GHOST
        assert not person.can_sign_in()
        assert added.level == ContributionLevel.VIEW

    def test_an_email_address_is_stored_and_does_not_make_an_account(
        self, record, manager, mailoutbox
    ):
        browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "new",
                "given": "Ada",
                "family": "Lovelace",
                "email": " ada@example.org ",
            },
        )

        person = Person.objects.get(first_name="Ada", last_name="Lovelace")
        assert person.email == "ada@example.org"
        assert not person.has_usable_password()
        assert person.account_state == AccountState.INVITED
        assert not person.can_sign_in()
        assert not person.socialaccount_set.exists()
        assert mailoutbox == []

    def test_the_email_address_is_not_shown_on_the_tab_or_the_edit_page(
        self, record, manager
    ):
        browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "new",
                "given": "Ada",
                "family": "Lovelace",
                "email": "ada@example.org",
            },
        )
        added = record.contributors.get(contributor__name="Ada Lovelace")

        for address in (tab(record), page_of(record, "edit", pk=added.pk)):
            response = browser_as(manager).get(address)
            assert "ada@example.org" not in response.content.decode()

    def test_an_email_address_must_be_one(self, record, manager):
        before = made()

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "new",
                "given": "Ada",
                "family": "Lovelace",
                "email": "not-an-address",
            },
        )

        assert response.status_code == 422
        assert response.context["adding"]["form"].has_error("email", code="invalid")
        assert made() == before

    @pytest.mark.parametrize("typed", ["held@example.com", "HELD@Example.COM"])
    def test_an_address_the_portal_holds_is_refused_without_naming_its_owner(
        self, record, manager, typed
    ):
        holder = PersonFactory(
            first_name="Zacharias", last_name="Holder", email="held@example.com"
        )
        before, listed = made(), stored(record)

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {"via": "new", "given": "Alice", "family": "Typed", "email": typed},
        )

        adding = response.context["adding"]
        content = response.content.decode()
        assert response.status_code == 422
        assert adding["form"].has_error("email", code="email_in_use")
        assert "email" in adding["errors"]
        assert adding["same_name"] == []
        assert adding["picked"] is None
        assert "Zacharias" not in content
        assert str(holder.uuid) not in content
        assert holder.get_absolute_url() not in content
        assert made() == before
        assert stored(record) == listed

    def test_an_address_the_portal_holds_is_refused_even_for_the_same_name(
        self, record, manager
    ):
        holder = PersonFactory(
            first_name="Zacharias", last_name="Holder", email="held@example.com"
        )
        before = made()

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "new",
                "given": "Zacharias",
                "family": "Holder",
                "email": "held@example.com",
                "confirmed": "1",
            },
        )

        adding = response.context["adding"]
        assert response.status_code == 422
        assert adding["form"].has_error("email", code="email_in_use")
        assert adding["same_name"] == []
        assert holder.get_absolute_url() not in response.content.decode()
        assert made() == before

    def test_the_same_name_offers_the_profiles_already_in_the_portal_and_makes_nothing(
        self, record, manager
    ):
        twin = PersonFactory(first_name="Mia", last_name="Meyer")
        other = PersonFactory(first_name="Mia", last_name="Meyer")
        before, listed = made(), stored(record)

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {"via": "new", "given": "mia", "family": "MEYER"},
        )

        adding = response.context["adding"]
        assert response.status_code == 422
        assert adding["on_new"] is True
        assert {p.pk for p in adding["same_name"]} == {twin.pk, other.pk}
        assert adding["form"].has_error(NON_FIELD_ERRORS, code="same_name")
        assert made() == before
        assert stored(record) == listed

    def test_a_new_profile_can_still_be_made_once_the_same_name_is_confirmed(
        self, record, manager
    ):
        twin = PersonFactory(first_name="Mia", last_name="Meyer")

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {"via": "new", "given": "Mia", "family": "Meyer", "confirmed": "1"},
        )

        made_now = Person.objects.filter(name="Mia Meyer").exclude(pk=twin.pk).get()
        assert response.status_code == 302
        assert record.contributors.filter(contributor=made_now).exists()
        assert not record.contributors.filter(contributor=twin).exists()

    def test_a_superuser_with_the_same_name_is_not_offered(self, record, manager):
        PersonFactory(
            first_name="Root", last_name="User", is_superuser=True, is_staff=True
        )

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {"via": "new", "given": "Root", "family": "User"},
        )

        assert response.status_code == 302

    def test_a_person_is_asked_for_their_organization(self, record, manager):
        response = browser_as(manager).get(
            page_of(record, "add-person"), {"via": "new"}
        )

        values, selected = offered(response, "new-affiliation")
        assert values == ["other", "none"]
        assert selected == ["none"]

    def test_the_organization_chosen_is_kept_with_the_credit_and_listed(
        self, record, manager
    ):
        browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "new",
                "given": "Ada",
                "family": "Lovelace",
                "affiliation": "other",
                "affiliation_name": "Analytical Engines Ltd",
            },
        )

        person = Person.objects.get(name="Ada Lovelace")
        company = Organization.objects.get(name="Analytical Engines Ltd")
        assert record.contributors.get(contributor=person).affiliation == company
        assert record.contributors.filter(contributor=company).exists()

    def test_a_refused_organization_makes_no_person_and_keeps_what_was_typed(
        self, record, manager
    ):
        before, listed = made(), stored(record)

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "new",
                "given": "Ada",
                "family": "Lovelace",
                "email": "ada@example.org",
                "affiliation": "other",
                "affiliation_name": " ",
            },
        )

        adding = response.context["adding"]
        assert response.status_code == 422
        assert "affiliation" in adding["errors"]
        assert adding["on_new"] is True
        assert adding["values"]["given"] == "Ada"
        assert adding["values"]["email"] == "ada@example.org"
        assert made() == before
        assert stored(record) == listed

    def test_nothing_is_kept_when_the_credit_is_refused(self, record, manager):
        before = made()

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {
                "via": "new",
                "given": "Ada",
                "family": "Lovelace",
                "affiliation": "org:999999",
            },
        )

        assert response.status_code == 422
        assert made() == before

    def test_an_organization_needs_a_name(self, record, manager):
        before, listed = made(), stored(record)

        for name in ("", "   "):
            response = browser_as(manager).post(
                page_of(record, "add-organization"),
                {"via": "new", "name": name, "city": "Potsdam"},
            )

            adding = response.context["adding"]
            assert response.status_code == 422
            assert adding["form"].has_error("name", code="required")
            assert adding["values"]["city"] == "Potsdam"

        assert made() == before
        assert stored(record) == listed

    def test_an_organization_is_made_with_the_optional_fields_stored(
        self, record, manager
    ):
        response = browser_as(manager).post(
            page_of(record, "add-organization"),
            {
                "via": "new",
                "name": "Institute of Examples",
                "city": "Potsdam",
                "country": "DE",
                "website": "https://examples.example.org/",
            },
        )

        organization = Organization.objects.get(name="Institute of Examples")
        added = record.contributors.get(contributor=organization)
        assert response.status_code == 302
        assert response["Location"] == page_of(record, "edit", pk=added.pk)
        assert organization.city == "Potsdam"
        assert organization.country == "DE"
        assert organization.links == ["https://examples.example.org/"]
        assert added.level is None

    def test_an_organization_needs_only_a_name(self, record, manager):
        browser_as(manager).post(
            page_of(record, "add-organization"),
            {"via": "new", "name": "Institute of Examples"},
        )

        organization = Organization.objects.get(name="Institute of Examples")
        assert not organization.city
        assert not organization.country
        assert not organization.links

    @pytest.mark.parametrize("typed", ["DE", "de", "Germany", "germany", " Germany "])
    def test_a_country_is_taken_by_name_or_by_code(self, record, manager, typed):
        browser_as(manager).post(
            page_of(record, "add-organization"),
            {"via": "new", "name": "Institute of Examples", "country": typed},
        )

        assert Organization.objects.get(name="Institute of Examples").country == "DE"

    def test_a_country_that_does_not_resolve_is_refused_on_the_field(
        self, record, manager
    ):
        before = made()

        response = browser_as(manager).post(
            page_of(record, "add-organization"),
            {"via": "new", "name": "Institute of Examples", "country": "Atlantis"},
        )

        adding = response.context["adding"]
        assert response.status_code == 422
        assert adding["form"].has_error("country", code="invalid_country")
        assert adding["values"]["country"] == "Atlantis"
        assert made() == before

    def test_a_website_must_be_an_address(self, record, manager):
        before = made()

        response = browser_as(manager).post(
            page_of(record, "add-organization"),
            {"via": "new", "name": "Institute of Examples", "website": "not a website"},
        )

        assert response.status_code == 422
        assert response.context["adding"]["form"].has_error("website", code="invalid")
        assert made() == before

    @pytest.mark.parametrize("typed", ["Helmholtz Zentrum", " helmholtz zentrum "])
    @pytest.mark.parametrize("confirmed", [{}, {"confirmed": "1"}])
    def test_the_same_name_offers_the_existing_organization_and_makes_no_second(
        self, record, manager, typed, confirmed
    ):
        existing = OrganizationFactory(name="Helmholtz Zentrum")
        before, listed = made(), stored(record)

        response = browser_as(manager).post(
            page_of(record, "add-organization"),
            {"via": "new", "name": typed, **confirmed},
        )

        adding = response.context["adding"]
        assert response.status_code == 422
        assert adding["on_new"] is True
        assert [o.pk for o in adding["same_name"]] == [existing.pk]
        assert adding["form"].has_error(NON_FIELD_ERRORS, code="same_name")
        assert made() == before
        assert stored(record) == listed

    def test_the_existing_organization_offered_can_be_added_in_its_place(
        self, record, manager
    ):
        existing = OrganizationFactory(name="Helmholtz Zentrum")
        offer = browser_as(manager).post(
            page_of(record, "add-organization"),
            {"via": "new", "name": "Helmholtz Zentrum"},
        )

        form = soup_of(offer).select_one("#tab-new form input[name=contributor]")
        browser_as(manager).post(
            page_of(record, "add-organization"),
            {"via": "portal", "contributor": form["value"]},
        )

        assert form["value"] == str(existing.pk)
        assert record.contributors.filter(contributor=existing).exists()
        assert Organization.objects.filter(name="Helmholtz Zentrum").count() == 1

    def test_a_person_with_the_name_of_an_organization_is_made(self, record, manager):
        OrganizationFactory(name="Ada Lovelace")

        response = browser_as(manager).post(
            page_of(record, "add-person"),
            {"via": "new", "given": "Ada", "family": "Lovelace"},
        )

        assert response.status_code == 302
