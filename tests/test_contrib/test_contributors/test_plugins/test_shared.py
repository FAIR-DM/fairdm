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
from fairdm.contrib.contributors.models import Contribution, Organization
from fairdm.contrib.plugins import reverse
from fairdm.factories import (
    AffiliationFactory,
    ContributionFactory,
    OrganizationFactory,
    PersonFactory,
)


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
