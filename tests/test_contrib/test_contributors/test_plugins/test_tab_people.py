"""Tests for adding a person to a record's Contributors tab, through the test client."""

import pytest
import requests
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.test import Client

from fairdm.contrib.contributors.models import ContributorIdentifier, Person
from fairdm.contrib.contributors.plugins.tab_base import MEMBER, role_by_slug
from fairdm.contrib.contributors.services.registries import SEARCHES_PER_MINUTE
from fairdm.contrib.plugins import reverse
from fairdm.factories import ContributionFactory, PersonFactory

ORCID_SEARCH = "https://pub.orcid.org/v3.0/expanded-search/"
JOSIAH = "0000-0002-1825-0097"
JOSIAH_RECORD = f"https://pub.orcid.org/v3.0/{JOSIAH}/record"


def page_of(record, name, **kwargs):
    return reverse(record, f"contribution-list-{name}", **kwargs)


def browser_as(user):
    browser = Client()
    if user is not None:
        browser.force_login(user)
    return browser


def soup_of(response):
    return BeautifulSoup(response.content.decode(), "html.parser")


def picked(response):
    """The addresses the pick buttons of a sheet's results lead to."""
    return [tag["hx-get"] for tag in soup_of(response).select("button.contrib-pick")]


def toast_is_error(response):
    return bool(soup_of(response).select_one(".contrib-toast .alert-error"))


@pytest.mark.django_db
class TestAddPerson:
    def test_the_sheet_lists_people_not_yet_credited(self, record, manager, colleague):
        outsider = PersonFactory(is_active=True, is_claimed=True)

        response = browser_as(manager).get(page_of(record, "add-person"))

        assert response.status_code == 200
        addresses = " ".join(picked(response))
        assert str(outsider.uuid) in addresses
        assert str(colleague.contributor.person.uuid) not in addresses
        assert response["HX-Trigger-After-Settle"]

    def test_a_search_narrows_the_list_by_name(self, record, manager):
        wanted = PersonFactory(name="Zelda Alphonse")
        other = PersonFactory(name="Boris Gamma")

        response = browser_as(manager).get(
            page_of(record, "add-person"), {"q": "alphonse"}
        )

        addresses = " ".join(picked(response))
        assert str(wanted.uuid) in addresses
        assert str(other.uuid) not in addresses

    def test_a_name_nobody_has_is_offered_as_a_new_row(self, record, manager):
        response = browser_as(manager).get(
            page_of(record, "add-person"), {"q": "Nobody Atall"}
        )

        assert soup_of(response).select_one("[data-contrib-new-row]")

    @pytest.mark.parametrize("kind", ["project", "dataset"])
    def test_someone_from_the_portal_is_added_at_the_view_level_with_project_member(
        self, public_chain, kind
    ):
        record = getattr(public_chain, kind)
        manager = PersonFactory(is_active=True, is_claimed=True, password="x")
        ContributionFactory(content_object=record, contributor=manager, level=3)
        person = PersonFactory(is_active=True, is_claimed=True)

        browser_as(manager).post(
            page_of(record, "add-person-step"), {"person": person.uuid}
        )

        credit = record.contributors.get(contributor=person)
        assert credit.level == 1
        assert role_by_slug(MEMBER) in credit.roles.all()

    def test_someone_added_by_name_alone_is_made_unclaimed(self, record, manager):
        before = Person.objects.count()

        browser_as(manager).post(
            page_of(record, "add-person-step"),
            {"first_name": "Ada", "last_name": "Lovelace"},
        )

        made = Person.objects.get(last_name="Lovelace")
        assert Person.objects.count() == before + 1
        assert record.contributors.filter(contributor=made).exists()

    def test_a_last_name_is_required_for_someone_new(self, record, manager):
        response = browser_as(manager).post(
            page_of(record, "add-person-step"), {"first_name": "Ada"}
        )

        assert response.status_code == 400

    @pytest.mark.parametrize("viewer", ["reader", "visitor"])
    def test_nobody_but_a_manager_may_add(self, request, record, viewer):
        user = request.getfixturevalue(viewer) if viewer != "visitor" else None
        person = PersonFactory(is_active=True, is_claimed=True)

        browser_as(user).post(
            page_of(record, "add-person-step"), {"person": person.uuid}
        )

        assert not record.contributors.filter(contributor=person).exists()


@pytest.mark.django_db
class TestAddPersonFromOrcid:
    @pytest.fixture(autouse=True)
    def orcid(self, registry_network, recorded):
        registry_network.answer(ORCID_SEARCH, recorded("orcid-search"))
        registry_network.answer(JOSIAH_RECORD, recorded("orcid-record"))
        self.network = registry_network

    def test_an_iD_nobody_holds_is_offered_as_a_new_row(self, record, manager):
        response = browser_as(manager).get(page_of(record, "add-person"), {"q": JOSIAH})

        assert soup_of(response).select_one("[data-contrib-new-row]")

    def test_adding_them_keeps_their_ORCID_iD(self, record, manager):
        browser_as(manager).post(page_of(record, "add-person-step"), {"orcid": JOSIAH})

        stored = ContributorIdentifier.objects.get(value=JOSIAH)
        assert record.contributors.filter(contributor=stored.related).exists()

    @pytest.mark.parametrize(
        "error", [requests.Timeout("slow"), requests.ConnectionError("down")]
    )
    def test_an_unreachable_ORCID_adds_nobody_and_says_so(self, record, manager, error):
        self.network.fail(JOSIAH_RECORD, error)
        before = Person.objects.count()

        response = browser_as(manager).post(
            page_of(record, "add-person-step"), {"orcid": JOSIAH}
        )

        assert toast_is_error(response)
        assert Person.objects.count() == before


@pytest.mark.django_db
class TestAddPersonSearchLimit:
    @pytest.fixture(autouse=True)
    def keeping_cache(self, settings, registry_network, recorded):
        settings.CACHES = {
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
        }
        registry_network.answer(ORCID_SEARCH, recorded("orcid-search"))
        self.network = registry_network
        yield
        cache.clear()

    def test_searching_too_often_stops_asking_ORCID(self, record, manager):
        browser = browser_as(manager)
        query = {"first_name": "Josiah", "last_name": "Carberry", "via": "search"}

        for number in range(SEARCHES_PER_MINUTE + 2):
            browser.get(
                page_of(record, "add-person-step"),
                {**query, "last_name": f"Carberry{number}"},
            )

        assert len(self.network.calls) <= SEARCHES_PER_MINUTE

    def test_the_same_search_is_answered_from_the_cache_the_second_time(
        self, record, manager
    ):
        browser = browser_as(manager)
        query = {"first_name": "Josiah", "last_name": "Carberry", "via": "search"}

        browser.get(page_of(record, "add-person-step"), query)
        calls = len(self.network.calls)
        browser.get(page_of(record, "add-person-step"), query)

        assert len(self.network.calls) == calls
