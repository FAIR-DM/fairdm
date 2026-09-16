"""Integration tests for the portal team page (FR-030 to FR-035).

A public page listing the active people holding each portal role, grouped by
role in `PortalRoles.ROLES` declaration order. Covers T031.
"""

import pytest
from django.contrib.auth.models import Group
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.html import escape
from pytest_django.asserts import assertContains, assertNotContains

from fairdm.factories import ContributionFactory, PersonFactory
from fairdm.portal_roles import PortalRoles


def _group(role):
    return Group.objects.get(name=role.name)


def _non_instrumentation_queries(captured):
    """Queries the page's own rendering made, minus django-orbit's write-behind
    logging of the render signals every template emits (`ORBIT_CONFIG`,
    `fairdm/conf/settings/addons.py`) - one `INSERT` per signal, scaling with
    the number of cards on the page rather than with the view's own query
    count, so it would otherwise swamp this comparison."""
    return [q for q in captured if "orbit_orbitentry" not in q["sql"]]


@pytest.mark.django_db
class TestTeamView:
    """`TeamView`, reached at the `team` URL name."""

    def test_visitor_who_is_not_signed_in_gets_200(self, client):
        response = client.get(reverse("team"))

        assert response.status_code == 200

    def test_roles_appear_in_declaration_order(self, client):
        _group(PortalRoles.DEVELOPER).user_set.add(PersonFactory())
        _group(PortalRoles.PORTAL_ADMINISTRATOR).user_set.add(PersonFactory())
        _group(PortalRoles.DATA_CURATOR).user_set.add(PersonFactory())

        response = client.get(reverse("team"))

        assert [entry["role"] for entry in response.context["roles"]] == [
            PortalRoles.PORTAL_ADMINISTRATOR,
            PortalRoles.DATA_CURATOR,
            PortalRoles.DEVELOPER,
        ]

    def test_person_holding_two_roles_appears_under_both(self, client):
        person = PersonFactory()
        _group(PortalRoles.PORTAL_ADMINISTRATOR).user_set.add(person)
        _group(PortalRoles.COMMUNITY_MANAGER).user_set.add(person)

        response = client.get(reverse("team"))

        holders_by_role = {
            entry["role"]: entry["holders"] for entry in response.context["roles"]
        }
        assert person in holders_by_role[PortalRoles.PORTAL_ADMINISTRATOR]
        assert person in holders_by_role[PortalRoles.COMMUNITY_MANAGER]

    def test_role_nobody_holds_is_absent(self, client):
        _group(PortalRoles.DATA_CURATOR).user_set.add(PersonFactory())

        response = client.get(reverse("team"))

        roles_shown = [entry["role"] for entry in response.context["roles"]]
        assert roles_shown == [PortalRoles.DATA_CURATOR]

    def test_deactivated_holder_is_absent(self, client):
        active = PersonFactory()
        deactivated = PersonFactory(is_active=False)
        group = _group(PortalRoles.COMMUNITY_MANAGER)
        group.user_set.add(active, deactivated)

        response = client.get(reverse("team"))

        holders = response.context["roles"][0]["holders"]
        assert active in holders
        assert deactivated not in holders

    def test_no_email_address_appears_in_response(self, client):
        holder = PersonFactory(email="team-holder@example.com")
        _group(PortalRoles.PORTAL_ADMINISTRATOR).user_set.add(holder)

        response = client.get(reverse("team"))

        assertNotContains(response, "team-holder@example.com")
        assertNotContains(response, "mailto:")

    def test_contribution_role_holder_without_a_portal_role_is_absent(self, client):
        contributor = PersonFactory()
        ContributionFactory(contributor=contributor)

        response = client.get(reverse("team"))

        assert response.context["roles"] == []
        assert contributor.name not in response.content.decode()

    def test_page_holds_its_query_count_as_the_number_of_holders_grows(self, client):
        _group(PortalRoles.PORTAL_ADMINISTRATOR).user_set.add(PersonFactory())

        # A first request creates any request-scoped singleton (e.g. the
        # identity branding row) that would otherwise inflate only the
        # "before" capture below with one-off queries unrelated to holders.
        client.get(reverse("team"))

        with CaptureQueriesContext(connection) as before:
            client.get(reverse("team"))

        for role in (
            PortalRoles.DATA_CURATOR,
            PortalRoles.COMMUNITY_MANAGER,
            PortalRoles.DEVELOPER,
        ):
            group = _group(role)
            group.user_set.add(PersonFactory(), PersonFactory(), PersonFactory())

        with CaptureQueriesContext(connection) as after:
            client.get(reverse("team"))

        assert len(_non_instrumentation_queries(after.captured_queries)) == len(
            _non_instrumentation_queries(before.captured_queries)
        )

    def test_page_title_is_portal_team(self, client):
        response = client.get(reverse("team"))

        assert response.context["page"]["title"] == "Portal Team"

    def test_lead_paragraph_introduces_the_people_listed(self, client):
        response = client.get(reverse("team"))

        subtitle = response.context["page"]["subtitle"]
        assert subtitle
        assertContains(response, escape(subtitle), html=False)

    def test_info_dialog_carries_its_text_and_links_to_the_docs(self, client):
        response = client.get(reverse("team"))

        page = response.context["page"]
        assert page["info"]
        # The dialog renders `{{ text }}`, so the copy reaches the page escaped -
        # an apostrophe in it arrives as `&#x27;`.
        assertContains(response, escape(page["info"]))
        assert page["info_actions"] == [
            {
                "text": "About portal roles",
                "href": "https://fairdm.org/portal-administration/roles/",
                "icon": "external-link",
                "target": "_blank",
            }
        ]
        assertContains(response, 'href="https://fairdm.org/portal-administration/roles/"')

    def test_holders_grid_is_responsive_across_breakpoints(self, client):
        _group(PortalRoles.PORTAL_ADMINISTRATOR).user_set.add(PersonFactory())

        response = client.get(reverse("team"))

        content = response.content.decode()
        assert "grid-cols-1" in content
        assert "md:grid-cols-2" in content
        assert "lg:grid-cols-4" in content
