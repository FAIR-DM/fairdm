"""Tests for a record's Contributors tab and the pages it leads to, through the test client.

Each page is opened and submitted on a project, a dataset, a registered sample type and a
registered measurement type, as a manager, as a signed-in reader and as a visitor. Elements are
found by link target and context value. Nothing here asserts a sentence or a layout.
"""

from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup
from django.contrib.messages import ERROR, get_messages
from django.test import Client
from research_vocabs.models import Concept

from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contribution
from fairdm.contrib.plugins import reverse
from fairdm.factories import ContributionFactory, OrganizationFactory, PersonFactory


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
