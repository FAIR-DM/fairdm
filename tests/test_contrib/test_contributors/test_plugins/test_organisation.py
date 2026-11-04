"""Tests for an organization's Members tab, requested through the test client."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from fairdm.contrib.contributors.models import Affiliation
from fairdm.factories import AffiliationFactory, OrganizationFactory, PersonFactory


def _members_url(contributor):
    return reverse(
        "contributor:organization-members", kwargs={"uuid": contributor.uuid}
    )


def _join(organization, name, kind=Affiliation.MembershipType.MEMBER, **kwargs):
    person = PersonFactory(name=name, is_active=True, is_claimed=True, password="x")
    AffiliationFactory(organization=organization, person=person, type=kind, **kwargs)
    return person


def _tabs(page, contributor):
    """The addresses in the contributor's tab strip, in order."""
    base = f"/contributor/{contributor.uuid}/"
    tabs = []
    for link in page.select("a[href]"):
        href = link["href"]
        if href.startswith(base) and href not in tabs:
            tabs.append(href)
    return tabs


@pytest.mark.django_db
class TestOrganizationMembers:
    # User Story 4, scenario 1
    def test_the_current_verified_members_are_listed_owner_first_then_administrators(
        self, get_page
    ):
        organization = OrganizationFactory()
        member_b = _join(organization, "Beta")
        member_a = _join(organization, "Alpha")
        admin = _join(organization, "Yara", Affiliation.MembershipType.ADMIN)
        owner = _join(organization, "Zed", Affiliation.MembershipType.OWNER)
        _join(organization, "Pending", Affiliation.MembershipType.PENDING)
        _join(organization, "Former", start_date="2010", end_date="2014")

        response, _ = get_page(_members_url(organization))

        assert list(response.context["object_list"]) == [
            owner,
            admin,
            member_a,
            member_b,
        ]

    # User Story 4, scenario 2
    def test_pending_and_former_members_are_listed_for_no_viewer(self, get_page):
        organization = OrganizationFactory()
        owner = _join(organization, "Owner", Affiliation.MembershipType.OWNER)
        pending = _join(organization, "Pending", Affiliation.MembershipType.PENDING)
        former = _join(organization, "Former", start_date="2010", end_date="2014")

        for viewer in (None, owner, pending, former):
            response, _ = get_page(_members_url(organization), viewer=viewer)

            listed = set(response.context["object_list"])
            assert pending not in listed
            assert former not in listed

    # User Story 4, scenario 3
    def test_the_tab_opens_for_a_visitor_and_signed_in(self, get_page):
        organization = OrganizationFactory()
        member = _join(organization, "Member")
        outsider = PersonFactory(is_active=True, is_claimed=True, password="x")

        for viewer in (None, member, outsider):
            response, _ = get_page(_members_url(organization), viewer=viewer)

            assert response.status_code == 200

    # User Story 4, scenario 4
    def test_the_tab_comes_right_after_the_overview(self, get_page):
        organization = OrganizationFactory()

        _, page = get_page(organization.get_absolute_url())

        tabs = _tabs(page, organization)
        assert tabs[:2] == [organization.get_absolute_url(), _members_url(organization)]

    # User Story 4, scenario 5
    def test_a_person_has_no_members_tab(self, get_page):
        person = PersonFactory(is_active=True, is_claimed=True, password="x")

        _, page = get_page(person.get_absolute_url(), viewer=person)

        assert _members_url(person) not in _tabs(page, person)

    # User Story 4, scenario 6
    def test_a_persons_members_address_is_not_found_for_every_viewer(self, get_page):
        person = PersonFactory(is_active=True, is_claimed=True, password="x")
        other = PersonFactory(is_active=True, is_claimed=True, password="x")

        for viewer in (None, person, other):
            response, _ = get_page(_members_url(person), viewer=viewer)

            assert response.status_code == 404

    # User Story 4, scenario 7
    def test_an_organization_without_members_gets_the_tab_saying_it_has_none(
        self, get_page
    ):
        organization = OrganizationFactory()
        _join(organization, "Pending", Affiliation.MembershipType.PENDING)

        _, page = get_page(organization.get_absolute_url())
        tab, _ = get_page(_members_url(organization))

        assert _members_url(organization) in _tabs(page, organization)
        assert tab.status_code == 200
        assert list(tab.context["object_list"]) == []
        assert tab.context["empty_state"]["heading"]

    # User Story 4, scenario 8
    def test_the_overviews_count_of_members_not_shown_links_to_the_tab(self, get_page):
        organization = OrganizationFactory()
        for n in range(13):
            _join(organization, f"Member {n:02d}")

        _, page = get_page(organization.get_absolute_url())
        tab, _ = get_page(_members_url(organization))

        places = page.select_one("[data-card=members]").select("ul > li")
        assert places[-1].select_one("a[href]")["href"] == _members_url(organization)
        figure = page.select_one(f".stat a[href='{_members_url(organization)}']")
        value = figure.find_parent(class_="stat").select_one(".stat-value")
        assert int(value.get_text(strip=True)) == tab.context["paginator"].count

    # SC-005
    def test_the_number_of_queries_does_not_grow_with_the_members(self, client):
        def queries_for(count):
            organization = OrganizationFactory()
            for n in range(count):
                _join(organization, f"Member {n:02d}")
            with CaptureQueriesContext(connection) as captured:
                client.get(_members_url(organization))
            return len(captured)

        # The first request also fills the caches every page shares.
        queries_for(1)
        assert queries_for(2) == queries_for(8)
