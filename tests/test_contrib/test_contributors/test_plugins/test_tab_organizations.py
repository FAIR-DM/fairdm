"""Tests for adding an organization to a record's Contributors tab, through the test
client.
"""

import pytest
import requests
from bs4 import BeautifulSoup
from django.test import Client

from fairdm.contrib.contributors.models import Organization
from fairdm.contrib.plugins import reverse
from fairdm.factories import OrganizationFactory

ROR_SEARCH = "https://api.ror.org/v2/organizations"
GFZ = "04z8jg394"
GFZ_RECORD = f"https://api.ror.org/v2/organizations/{GFZ}"


def page_of(record, name, **kwargs):
    return reverse(record, f"contribution-list-{name}", **kwargs)


def browser_as(user):
    browser = Client()
    if user is not None:
        browser.force_login(user)
    return browser


def soup_of(response):
    return BeautifulSoup(response.content.decode(), "html.parser")


@pytest.mark.django_db
class TestAddOrganization:
    def test_the_sheet_lists_organizations_not_yet_on_the_record(
        self, record, manager, partner
    ):
        other = OrganizationFactory()

        response = browser_as(manager).get(page_of(record, "add-organization"))

        addresses = " ".join(
            tag["hx-get"] for tag in soup_of(response).select("button.contrib-pick")
        )
        assert str(other.uuid) in addresses
        assert str(partner.contributor.uuid) not in addresses

    def test_an_organization_from_the_portal_is_listed_with_its_roles(
        self, record, manager
    ):
        organization = OrganizationFactory()
        roles = (
            browser_as(manager)
            .get(
                page_of(record, "add-organization"), {"organization": organization.uuid}
            )
            .context["roles"]
        )

        browser_as(manager).post(
            page_of(record, "add-organization"),
            {"organization": organization.uuid, "roles": [roles[0].pk]},
        )

        credit = record.contributors.get(contributor=organization)
        assert roles[0] in credit.roles.all()

    def test_the_roles_step_submits_which_organization_it_adds(self, record, manager):
        organization = OrganizationFactory()
        browser = browser_as(manager)

        for query, field in [
            ({"organization": organization.uuid}, "organization"),
            ({"new_name": "Brand New Institute", "skip": 1}, "new_name"),
        ]:
            form = soup_of(browser.get(page_of(record, "add-organization"), query))
            tag = form.select_one(f"#contrib-form input[name={field}]")
            assert tag is not None, field

    def test_a_new_organization_is_added_with_what_its_form_submits(
        self, record, manager
    ):
        browser = browser_as(manager)
        step = soup_of(
            browser.get(
                page_of(record, "add-organization"),
                {"new_name": "Brand New Institute", "skip": 1},
            )
        )
        sent = {
            tag["name"]: tag.get("value", "")
            for tag in step.select("#contrib-form input[type=hidden]")
        }

        response = browser.post(page_of(record, "add-organization"), sent)

        assert response.status_code == 200
        assert Organization.objects.filter(name="Brand New Institute").exists()

    def test_a_name_alone_makes_an_organization(self, record, manager):
        browser_as(manager).post(
            page_of(record, "add-organization"), {"new_name": "Brand New Institute"}
        )

        made = Organization.objects.get(name="Brand New Institute")
        assert record.contributors.filter(contributor=made).exists()

    def test_a_name_is_required(self, record, manager):
        response = browser_as(manager).post(page_of(record, "add-organization"), {})

        assert response.status_code == 400

    @pytest.mark.parametrize("viewer", ["reader", "visitor"])
    def test_nobody_but_a_manager_may_add(self, request, record, viewer):
        user = request.getfixturevalue(viewer) if viewer != "visitor" else None

        browser_as(user).post(
            page_of(record, "add-organization"), {"new_name": "Sneaky Lab"}
        )

        assert not Organization.objects.filter(name="Sneaky Lab").exists()


@pytest.mark.django_db
class TestAddOrganizationFromRor:
    @pytest.fixture(autouse=True)
    def ror(self, registry_network, recorded):
        registry_network.answer(ROR_SEARCH, recorded("ror-search"))
        registry_network.answer(GFZ_RECORD, recorded("ror-record"))
        self.network = registry_network

    def test_adding_one_keeps_its_ROR_ID(self, record, manager):
        browser_as(manager).post(page_of(record, "add-organization"), {"ror": GFZ})

        made = Organization.objects.get(identifiers__value=GFZ)
        assert record.contributors.filter(contributor=made).exists()

    def test_one_the_portal_already_holds_is_not_made_twice(self, record, manager):
        browser_as(manager).post(page_of(record, "add-organization"), {"ror": GFZ})
        before = Organization.objects.count()

        browser_as(manager).post(page_of(record, "add-organization"), {"ror": GFZ})

        assert Organization.objects.count() == before

    @pytest.mark.parametrize(
        "error", [requests.Timeout("slow"), requests.ConnectionError("down")]
    )
    def test_an_unreachable_ROR_adds_nothing_and_says_so(self, record, manager, error):
        self.network.fail(GFZ_RECORD, error)
        before = Organization.objects.count()

        response = browser_as(manager).post(
            page_of(record, "add-organization"), {"ror": GFZ}
        )

        assert soup_of(response).select_one(".contrib-toast .alert-error")
        assert Organization.objects.count() == before
