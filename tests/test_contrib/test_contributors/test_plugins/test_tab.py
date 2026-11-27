"""Tests for a record's Contributors tab as a page, through the test client.

The tab is opened on a project, a dataset, a registered sample type and a registered
measurement type, as a manager, as a signed-in reader and as a visitor. Elements are
found by id, link target and context value. Nothing here asserts a sentence or a layout.
"""

import pytest
from bs4 import BeautifulSoup
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.plugins import reverse
from fairdm.factories import ContributionFactory, OrganizationFactory, PersonFactory


def tab(record):
    return reverse(record, "contribution-list")


def browser_as(user):
    browser = Client()
    if user is not None:
        browser.force_login(user)
    return browser


def person_on(record, level):
    """A person who can sign in, credited on the record at the level."""
    person = PersonFactory(is_active=True, is_claimed=True, password="x")
    ContributionFactory(content_object=record, contributor=person, level=level)
    return person


def soup_of(response):
    return BeautifulSoup(response.content.decode(), "html.parser")


@pytest.mark.django_db
class TestContributorsTab:
    def test_it_lists_people_and_organizations_separately(
        self, record, colleague, partner
    ):
        response = browser_as(None).get(tab(record))

        assert response.status_code == 200
        page = soup_of(response)
        assert page.select_one(f"#contrib-person-{colleague.pk}")
        assert page.select_one(f"#contrib-org-{partner.contributor_id}")

    def test_a_manager_is_offered_to_add_and_change(self, record, manager, colleague):
        page = soup_of(browser_as(manager).get(tab(record)))

        wanted = {
            reverse(record, "contribution-list-add-person"),
            reverse(record, "contribution-list-add-organization"),
            reverse(record, "contribution-list-edit", pk=colleague.pk),
            reverse(record, "contribution-list-remove", pk=colleague.pk),
        }
        offered = {tag["hx-get"] for tag in page.select("[hx-get]")} | {
            tag["hx-post"] for tag in page.select("[hx-post]")
        }
        assert wanted <= offered

    @pytest.mark.parametrize("viewer", ["reader", "visitor", "stranger"])
    def test_nobody_else_is_offered_a_control(
        self, request, record, colleague, partner, viewer
    ):
        user = (
            None
            if viewer == "visitor"
            else request.getfixturevalue("newcomer" if viewer == "stranger" else viewer)
        )

        response = browser_as(user).get(tab(record))

        assert response.status_code == 200
        page = soup_of(response)
        assert page.select_one("#contrib-region")
        assert not page.select("#contrib-region [hx-get], #contrib-region [hx-post]")

    def test_a_record_with_nobody_credited_still_offers_a_manager_both_adds(
        self, record, curator
    ):
        page = soup_of(browser_as(curator).get(tab(record)))

        assert {tag["hx-get"] for tag in page.select(".contrib-add")} == {
            reverse(record, "contribution-list-add-person"),
            reverse(record, "contribution-list-add-organization"),
        }

    def test_a_manager_sees_who_holds_access_from_a_record_above(self, public_chain):
        manager = person_on(public_chain.dataset, ContributionLevel.MANAGE)
        holder = person_on(public_chain.project, ContributionLevel.EDIT)

        page = soup_of(browser_as(manager).get(tab(public_chain.dataset)))

        assert page.select_one(f"#contrib-above-{holder.pk}")

    def test_a_reader_does_not_see_who_holds_access_from_above(self, public_chain):
        reader = person_on(public_chain.dataset, ContributionLevel.VIEW)
        person_on(public_chain.project, ContributionLevel.EDIT)

        page = soup_of(browser_as(reader).get(tab(public_chain.dataset)))

        assert not page.select("[data-contrib-above]")


@pytest.mark.django_db
class TestContributorsTabQueries:
    @staticmethod
    def queries_with(record, manager, people):
        """Count the queries the tab takes once the record lists this many people."""
        for _number in range(people - record.contributors.people().count()):
            ContributionFactory(
                content_object=record,
                contributor=PersonFactory(is_active=True, is_claimed=True),
                level=ContributionLevel.VIEW,
                affiliation=OrganizationFactory(),
            )
        browser = browser_as(manager)
        # The first request fills caches that later ones read, such as content types.
        browser.get(tab(record))
        with CaptureQueriesContext(connection) as captured:
            response = browser.get(tab(record))
        assert response.status_code == 200
        return len(captured)

    def test_the_count_does_not_grow_with_the_number_of_people(self, record, manager):
        few = self.queries_with(record, manager, 5)
        many = self.queries_with(record, manager, 25)

        assert many == few
