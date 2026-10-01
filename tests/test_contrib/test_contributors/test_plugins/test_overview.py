"""Tests for the contributor overview pages, requested through the test client.

A page is read as a visitor and signed in. Cards are found by their ``data-card`` attribute,
figures by the tab they link to, and notices by the alert role outside any card. Nothing here
asserts a sentence, a width or an order of sections.
"""

import json
import re
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from django.urls import NoReverseMatch, reverse

from fairdm import plugins
from fairdm.contrib.contributors.choices import OrganizationType
from fairdm.contrib.contributors.models import (
    Affiliation,
    Contributor,
    ContributorIdentifier,
)
from fairdm.core.project.models import Project
from fairdm.core.utils import assign_perm
from fairdm.factories import (
    AffiliationFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    PointFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility

CARDS = ["about", "projects", "datasets", "roles", "identifiers", "links", "affiliations"]


def _tab_url(person, tab):
    return reverse(f"contributor:contributor-{tab}", kwargs={"uuid": person.uuid})


def _card(page, name):
    return page.select_one(f"[data-card={name}]")


def _hrefs(card):
    return [a["href"] for a in card.select("a[href]")]


def _entries(page, card_name):
    """The links to records a card lists, leaving out its link to the full list."""
    return [a["href"] for a in _card(page, card_name).select("ul a[href]")]


def _figure(page, url):
    """The number in the figure whose title links to ``url``."""
    link = page.select_one(f".stat a[href='{url}']")
    assert link is not None, f"no figure links to {url}"
    value = link.find_parent(class_="stat").select_one(".stat-value").get_text(strip=True)
    return int(value.replace(",", ""))


def _notices(page):
    """The alerts the page shows outside its cards."""
    return [
        alert
        for alert in page.select("[role=alert]")
        if alert.find_parent(attrs={"data-card": True}) is None
    ]


def _header(page):
    return page.select_one("h1").parent


def _public_project(**kwargs):
    return ProjectFactory(visibility=Visibility.PUBLIC, **kwargs)


@pytest.fixture
def claimed_person(db):
    return PersonFactory(is_active=True, is_claimed=True, password="testpass123")


@pytest.mark.django_db
class TestPersonOverview:
    def test_the_page_answers_for_a_visitor(self, get_page, credited_world):
        response, _ = get_page(credited_world.person.get_absolute_url())

        assert response.status_code == 200

    def test_a_contributor_that_does_not_exist_answers_not_found(self, get_page, db):
        response, _ = get_page("/contributor/cDoesNotExist/")

        assert response.status_code == 404

    # Scenario 1
    def test_the_cards_list_the_public_projects_and_datasets_only(
        self, get_page, credited_world
    ):
        world = credited_world

        _, page = get_page(world.person.get_absolute_url())

        assert _entries(page, "projects") == [world.public_project.get_absolute_url()]
        assert _entries(page, "datasets") == [world.public_dataset.get_absolute_url()]

    def test_the_figures_count_the_public_projects_and_datasets_only(
        self, get_page, credited_world
    ):
        world = credited_world

        _, page = get_page(world.person.get_absolute_url())

        assert _figure(page, _tab_url(world.person, "projects")) == 1
        assert _figure(page, _tab_url(world.person, "datasets")) == 1

    def test_no_private_record_is_named_anywhere_on_the_page(
        self, get_page, credited_world
    ):
        world = credited_world

        response, _ = get_page(world.person.get_absolute_url())

        content = response.content.decode()
        for record in (
            world.private_project,
            world.private_dataset,
            world.dataset_in_private_project,
        ):
            assert record.get_absolute_url() not in content
            assert record.name not in content

    # Scenario 2
    def test_a_member_of_a_private_project_does_not_see_it_listed(
        self, get_page, credited_world
    ):
        world = credited_world
        member = PersonFactory(is_active=True)
        assign_perm("view_project", member, world.private_project)

        _, page = get_page(world.person.get_absolute_url(), viewer=member)

        assert world.private_project.get_absolute_url() not in _entries(page, "projects")
        assert _figure(page, _tab_url(world.person, "projects")) == 1

    def test_the_person_sees_the_same_public_work_as_a_visitor(
        self, get_page, credited_world
    ):
        world = credited_world

        _, page = get_page(world.person.get_absolute_url(), viewer=world.person)

        assert _entries(page, "projects") == [world.public_project.get_absolute_url()]
        assert _entries(page, "datasets") == [world.public_dataset.get_absolute_url()]

    # Scenario 3
    def test_someone_who_shares_only_a_private_record_is_not_a_collaborator(
        self, get_page, credited_world
    ):
        world = credited_world

        _, page = get_page(world.person.get_absolute_url())

        collaborators = _hrefs(_card(page, "people"))
        assert world.open_mate.get_absolute_url() in collaborators
        assert world.private_mate.get_absolute_url() not in collaborators
        assert world.private_dataset_mate.get_absolute_url() not in collaborators

    # Scenario 4
    def test_a_card_lists_five_records_with_those_in_progress_first(
        self, get_page, claimed_person
    ):
        statuses = [Project.STATUS_CHOICES.IN_PROGRESS] * 3 + [
            Project.STATUS_CHOICES.COMPLETE
        ] * 4
        projects = [_public_project(status=status) for status in statuses]
        for day, project in enumerate(projects, start=1):
            claimed_person.add_to(project)
            Project.objects.filter(pk=project.pk).update(
                modified=datetime(2026, 1, day, tzinfo=UTC)
            )
        in_progress = [p for p in projects if p.is_active]
        others = [p for p in projects if not p.is_active]
        expected = sorted(in_progress, key=lambda p: -p.pk) + sorted(
            others, key=lambda p: -p.pk
        )

        _, page = get_page(claimed_person.get_absolute_url())

        assert _entries(page, "projects") == [
            p.get_absolute_url() for p in expected[:5]
        ]

    def test_the_card_offers_the_full_list_of_what_it_cannot_show(
        self, get_page, claimed_person
    ):
        for _ in range(7):
            claimed_person.add_to(_public_project())

        _, page = get_page(claimed_person.get_absolute_url())

        all_url = _tab_url(claimed_person, "projects")
        assert all_url in _hrefs(_card(page, "projects"))
        assert _figure(page, all_url) == 7

    # Scenario 5
    def test_an_authenticated_orcid_id_and_a_typed_in_one_are_linked_and_told_apart(
        self, get_page, claimed_person, orcid_signed_in
    ):
        signed_in = PersonFactory(is_active=True, is_claimed=True, password="x")
        authenticated = ContributorIdentifier.objects.create(
            related=signed_in, type="ORCID", value="0000-0001-1111-2222"
        )
        orcid_signed_in(signed_in)
        typed = ContributorIdentifier.objects.create(
            related=claimed_person, type="ORCID", value="0000-0001-2345-6789"
        )

        _, first = get_page(signed_in.get_absolute_url())
        _, second = get_page(claimed_person.get_absolute_url())

        first_link = _header(first).select_one(f"a[href='{authenticated.resolver_url}']")
        second_link = _header(second).select_one(f"a[href='{typed.resolver_url}']")
        assert first_link is not None
        assert second_link is not None
        assert first_link["aria-label"] != second_link["aria-label"]
        assert str(first_link.select_one("i, svg")) != str(second_link.select_one("i, svg"))

    def test_a_person_with_no_orcid_id_has_no_orcid_link(self, get_page, claimed_person):
        _, page = get_page(claimed_person.get_absolute_url())

        assert _header(page).select_one("a[href*='orcid.org']") is None

    # Scenario 6
    def test_an_unclaimed_profile_gets_a_notice_with_the_claim_action_disabled(
        self, get_page, unclaimed_person
    ):
        _, page = get_page(unclaimed_person.get_absolute_url())

        (notice,) = _notices(page)
        button = notice.select_one("button")
        assert button.has_attr("disabled")
        assert button["type"] == "button"

    def test_an_unclaimed_profile_says_in_its_figure_that_there_is_no_account(
        self, get_page, unclaimed_person
    ):
        _, page = get_page(unclaimed_person.get_absolute_url())

        figure = page.select(".stat")[-1]
        assert unclaimed_person.member_since is None
        assert figure.select_one(".stat-value").get_text(strip=True) == "–"
        assert figure.select_one(".stat-desc") is not None

    def test_a_claimed_profile_has_no_notice_and_shows_the_year_of_its_account(
        self, get_page, claimed_person
    ):
        _, page = get_page(claimed_person.get_absolute_url())

        assert _notices(page) == []
        figure = page.select(".stat")[-1]
        assert figure.select_one(".stat-value").get_text(strip=True) == str(
            claimed_person.date_joined.year
        )

    # Scenario 7
    def test_an_inactive_account_gets_a_notice_and_keeps_its_credited_work(
        self, get_page, db
    ):
        person = PersonFactory(is_active=False, is_claimed=True, password="x")
        project = _public_project()
        person.add_to(project)

        response, page = get_page(person.get_absolute_url())

        assert response.status_code == 200
        (notice,) = _notices(page)
        assert notice.select_one("button") is None
        assert _entries(page, "projects") == [project.get_absolute_url()]

    # Scenario 8
    def test_the_header_names_the_primary_organization_and_its_location(
        self, get_page, claimed_person
    ):
        organization = OrganizationFactory(city="Potsdam", country="DE")
        AffiliationFactory(
            person=claimed_person, organization=organization, is_primary=True
        )

        _, page = get_page(claimed_person.get_absolute_url())

        header = _header(page)
        assert header.select_one(f"a[href='{organization.get_absolute_url()}']")
        assert organization.get_location_display()
        assert organization.get_location_display() in header.get_text()

    def test_the_affiliations_card_lists_current_then_past_with_dates_as_recorded(
        self, get_page, claimed_person
    ):
        primary = AffiliationFactory(
            person=claimed_person,
            organization=OrganizationFactory(name="Zeta Institute"),
            is_primary=True,
            start_date="2021-04",
        )
        other = AffiliationFactory(
            person=claimed_person, organization=OrganizationFactory(name="Alpha Lab")
        )
        older = AffiliationFactory(
            person=claimed_person, start_date="2008", end_date="2012-06-30"
        )
        newer = AffiliationFactory(
            person=claimed_person, start_date="2013", end_date="2017"
        )
        for affiliation in (primary, older, newer):
            affiliation.refresh_from_db()

        _, page = get_page(claimed_person.get_absolute_url())

        card = _card(page, "affiliations")
        assert _entries(page, "affiliations") == [
            a.organization.get_absolute_url() for a in (primary, other, newer, older)
        ]
        rows = [row.get_text() for row in card.select("li")]
        assert primary.start_display in rows[0]
        assert older.start_display in rows[3] and older.end_display in rows[3]
        assert older.end_display != older.start_display

    # Scenario 9
    def test_a_pending_primary_affiliation_names_its_organization_nowhere(
        self, get_page, claimed_person
    ):
        organization = OrganizationFactory(name="PENDING-ORG-MARKER", city="Pendingville")
        AffiliationFactory(
            person=claimed_person,
            organization=organization,
            is_primary=True,
            type=AffiliationFactory._meta.model.MembershipType.PENDING,
        )

        response, page = get_page(claimed_person.get_absolute_url())

        content = response.content.decode()
        assert "PENDING-ORG-MARKER" not in content
        assert "Pendingville" not in content
        assert organization.get_absolute_url() not in content

    def test_without_a_primary_affiliation_the_header_names_no_organization(
        self, get_page, claimed_person
    ):
        _, page = get_page(claimed_person.get_absolute_url())

        assert _header(page).select_one("a[href^='/contributor/']") is None

    # Scenario 10
    def test_each_role_is_listed_with_its_count_most_frequent_first(
        self, get_page, credited_world
    ):
        world = credited_world
        world.person.add_to(world.public_dataset, roles=["Creator"])

        _, page = get_page(world.person.get_absolute_url())

        card = _card(page, "roles")
        names = [dt.get_text(strip=True) for dt in card.select("dt")]
        counts = [int(re.search(r"\d+", dd.get_text()).group()) for dd in card.select("dd")]
        assert names[0] == "Creator"
        assert counts[0] == 2
        assert counts == sorted(counts, reverse=True)

    def test_a_role_held_only_on_a_private_record_is_not_listed(
        self, get_page, credited_world
    ):
        world = credited_world

        _, page = get_page(world.person.get_absolute_url())

        names = {dt.get_text(strip=True) for dt in _card(page, "roles").select("dt")}
        assert names == {"Creator", "Data Collector", "Researcher", "Support"}

    # Scenario 11
    def test_the_collaborators_card_shows_eighteen_and_counts_the_rest(
        self, get_page, claimed_person
    ):
        project = _public_project()
        claimed_person.add_to(project)
        mates = [PersonFactory() for _ in range(20)]
        for mate in mates:
            mate.add_to(project)

        _, page = get_page(claimed_person.get_absolute_url())

        card = _card(page, "people")
        faces = card.select("li")
        assert len(faces) == 18
        assert "2" in card.get_text()
        assert {a["href"] for a in card.select("li a")} <= {
            mate.get_absolute_url() for mate in mates
        }

    def test_each_collaborator_links_to_their_page_and_is_named_on_hover_and_to_screen_readers(
        self, get_page, claimed_person
    ):
        project = _public_project()
        mate = PersonFactory(name="Collaborator Name")
        claimed_person.add_to(project)
        mate.add_to(project)

        _, page = get_page(claimed_person.get_absolute_url())

        face = _card(page, "people").select_one("li")
        assert face["data-tip"] == "Collaborator Name"
        link = face.select_one("a")
        assert link["href"] == mate.get_absolute_url()
        assert link["aria-label"] == "Collaborator Name"

    # Scenario 12
    def test_a_person_with_nothing_still_shows_every_card_and_says_what_is_missing(
        self, get_page, claimed_person
    ):
        _, page = get_page(claimed_person.get_absolute_url())
        claimed_person.refresh_from_db()

        shown = [card["data-card"] for card in page.select("[data-card]")]
        for name in ("projects", "datasets", "roles", "links", "affiliations", "people"):
            assert name in shown
            assert _card(page, name).select_one("[role=alert], p") is not None
        assert "identifiers" in shown

    def test_a_person_with_no_biography_is_told_so_where_the_biography_goes(
        self, get_page, db
    ):
        person = PersonFactory(is_active=True, is_claimed=True, password="x", profile="")

        _, page = get_page(person.get_absolute_url())

        assert _card(page, "about").select_one("[role=alert]") is not None

    # Scenario 13
    def test_the_page_head_carries_the_schema_org_description(
        self, get_page, claimed_person
    ):
        _, page = get_page(claimed_person.get_absolute_url())

        script = page.select_one("head script[type='application/ld+json']")
        data = json.loads(script.string)
        assert data["@type"] == "Person"
        assert data["name"] == claimed_person.name

    def test_neither_the_page_nor_its_description_contains_the_email_address(
        self, get_page, claimed_person
    ):
        claimed_person.email = "secret.address@example.org"
        claimed_person.save()

        response, _ = get_page(claimed_person.get_absolute_url())
        signed_in, _ = get_page(claimed_person.get_absolute_url(), viewer=claimed_person)

        assert "secret.address@example.org" not in response.content.decode()
        assert "secret.address@example.org" not in signed_in.content.decode()

    # Scenario 15
    def test_the_first_tab_is_the_overview_and_there_is_no_statistics_or_network_tab(
        self, get_page, claimed_person
    ):
        _, page = get_page(claimed_person.get_absolute_url())

        base = f"/contributor/{claimed_person.uuid}/"
        tabs = [a["href"] for a in page.select("a[href]") if a["href"].startswith(base)]
        assert tabs[0] == claimed_person.get_absolute_url()
        assert not [href for href in tabs if href.rstrip("/").endswith(("statistics", "network"))]
        for name in ("statistics", "network"):
            with pytest.raises(NoReverseMatch):
                reverse(f"contributor:{name}", kwargs={"uuid": claimed_person.uuid})

    def test_the_overview_tab_carries_the_name_every_record_gives_its_first_tab(self, db):
        def first_tab(model):
            plugins.registry.get_urls_for_model(model)
            return plugins.registry.get_plugin_menu_for_model(model).children[0]

        assert str(first_tab(Contributor).name) == str(first_tab(Project).name)
        assert first_tab(Contributor).view_name == "contributor:overview"

    # SC-003
    @pytest.mark.parametrize("who", ["visitor", "person", "member"])
    def test_each_figure_equals_the_number_of_entries_in_its_tab(
        self, get_page, credited_world, who
    ):
        world = credited_world
        member = PersonFactory(is_active=True)
        assign_perm("view_project", member, world.private_project)
        viewer = {"visitor": None, "person": world.person, "member": member}[who]
        person = world.person

        _, page = get_page(person.get_absolute_url(), viewer=viewer)
        projects, _ = get_page(_tab_url(person, "projects"), viewer=viewer)
        datasets, _ = get_page(_tab_url(person, "datasets"), viewer=viewer)

        assert _figure(page, _tab_url(person, "projects")) == len(
            projects.context["object_list"]
        )
        assert _figure(page, _tab_url(person, "datasets")) == len(
            datasets.context["object_list"]
        )

    # Scenario 1
    def test_on_their_own_profile_the_header_action_links_to_the_editing_page(
        self, get_page, claimed_person
    ):
        update_url = reverse(
            "contributor:overview-update", kwargs={"uuid": claimed_person.uuid}
        )

        _, page = get_page(claimed_person.get_absolute_url(), viewer=claimed_person)

        links = [
            a
            for a in page.select(f"a[href='{update_url}']")
            if a.find_parent(attrs={"data-card": True}) is None
        ]
        assert len(links) == 1

    # Scenario 7
    def test_each_checklist_item_the_page_can_fix_links_to_its_field(
        self, get_page, db
    ):
        person = PersonFactory(
            is_active=True,
            is_claimed=True,
            password="x",
            profile="",
            links=[],
        )
        update_url = reverse(
            "contributor:overview-update", kwargs={"uuid": person.uuid}
        )

        response, page = get_page(person.get_absolute_url(), viewer=person)

        urls = [item.get("url") for item in response.context["readiness"]["items"]]
        assert urls == [
            f"{update_url}#id_image",
            reverse("socialaccount_connections"),
            f"{update_url}#id_profile",
            None,
            f"{update_url}#id_links",
        ]
        assert set(_hrefs(_card(page, "readiness"))) == {
            f"{update_url}#id_image",
            reverse("socialaccount_connections"),
            f"{update_url}#id_profile",
            f"{update_url}#id_links",
        }

    def test_the_about_prompt_links_to_the_biography_field(self, get_page, db):
        person = PersonFactory(
            is_active=True, is_claimed=True, password="x", profile=""
        )
        update_url = reverse(
            "contributor:overview-update", kwargs={"uuid": person.uuid}
        )

        _, page = get_page(person.get_absolute_url(), viewer=person)

        assert _hrefs(_card(page, "about")) == [f"{update_url}#id_profile"]

    # Scenario 8
    @pytest.mark.parametrize("who", ["visitor", "signed_in", "staff", "superuser"])
    def test_someone_elses_profile_offers_no_link_to_the_editing_page(
        self, get_page, claimed_person, who
    ):
        viewer = {
            "visitor": None,
            "signed_in": PersonFactory(is_active=True, password="x"),
            "staff": PersonFactory(is_active=True, is_staff=True, password="x"),
            "superuser": PersonFactory(
                is_active=True, is_staff=True, is_superuser=True, password="x"
            ),
        }[who]
        update_url = reverse(
            "contributor:overview-update", kwargs={"uuid": claimed_person.uuid}
        )

        response, page = get_page(claimed_person.get_absolute_url(), viewer=viewer)

        assert page.select(f"a[href^='{update_url}']") == []
        assert response.context["can_edit"] is False


def _members(page):
    """The places of the members card, as the person each links to or None for a count."""
    places = []
    for place in _card(page, "members").select("ul > li"):
        link = place.select_one("a[href]")
        places.append(link["href"] if link else None)
    return places


def _owned_marks(page, card_name):
    """The links in a records card whose row carries the owner badge."""
    return [
        row.select_one("a[href]")["href"]
        for row in _card(page, card_name).select("ul > li")
        if row.select_one(".badge-outline")
    ]


def _join_actions(page):
    """The disabled buttons in the page header, outside every card."""
    return [
        button
        for button in page.select("button[disabled]")
        if button.find_parent(attrs={"data-card": True}) is None
    ]


def _management_menu(page):
    return [
        item
        for item in page.select("li.menu-disabled")
        if item.find_parent(attrs={"data-card": True}) is None
    ]


def _join(organization, name, type=Affiliation.MembershipType.MEMBER, **kwargs):
    person = PersonFactory(name=name, is_active=True, is_claimed=True, password="x")
    AffiliationFactory(organization=organization, person=person, type=type, **kwargs)
    return person


@pytest.fixture
def owner_world(db):
    """An organization that owns projects and is credited on others, public and private.

    The organization owns a public project holding a public dataset it is not credited on, a
    public dataset it is credited on and a private dataset, and owns a private project holding a
    public dataset. It is credited on a public project, which it does not own, and on a private
    one. One more public project is both owned and credited. A member has credits of their own.
    """
    organization = OrganizationFactory(name="Owning Institute")
    owned = _public_project(owner=organization)
    owned_and_credited = _public_project(owner=organization)
    owned_private = ProjectFactory(owner=organization, visibility=Visibility.PRIVATE)
    credited = _public_project()
    credited_private = ProjectFactory(visibility=Visibility.PRIVATE)
    inside_not_credited = DatasetFactory(
        project=owned, visibility=Visibility.PUBLIC, published=True
    )
    inside_credited = DatasetFactory(
        project=owned, visibility=Visibility.PUBLIC, published=True
    )
    inside_private = DatasetFactory(
        project=owned, visibility=Visibility.PRIVATE, published=False
    )
    inside_private_project = DatasetFactory(
        project=owned_private, visibility=Visibility.PUBLIC, published=True
    )
    credited_dataset = DatasetFactory(
        project=credited, visibility=Visibility.PUBLIC, published=True
    )
    credited_private_dataset = DatasetFactory(
        project=credited, visibility=Visibility.PRIVATE, published=False
    )
    for record in (
        owned_and_credited,
        credited,
        credited_private,
        inside_credited,
        credited_dataset,
        credited_private_dataset,
    ):
        organization.add_to(record)
    member = _join(organization, "Member Person")
    members_project = _public_project()
    members_dataset = DatasetFactory(
        project=members_project, visibility=Visibility.PUBLIC, published=True
    )
    member.add_to(members_project)
    member.add_to(members_dataset)
    return SimpleNamespace(
        organization=organization,
        owned=owned,
        owned_and_credited=owned_and_credited,
        owned_private=owned_private,
        credited=credited,
        credited_private=credited_private,
        inside_not_credited=inside_not_credited,
        inside_credited=inside_credited,
        inside_private=inside_private,
        inside_private_project=inside_private_project,
        credited_dataset=credited_dataset,
        credited_private_dataset=credited_private_dataset,
        member=member,
        members_project=members_project,
        members_dataset=members_dataset,
    )


@pytest.mark.django_db
class TestOrganizationOverview:
    def test_the_page_answers_for_a_visitor_and_signed_in(self, get_page, owner_world):
        url = owner_world.organization.get_absolute_url()

        visitor, _ = get_page(url)
        signed_in, _ = get_page(url, viewer=owner_world.member)

        assert visitor.status_code == 200
        assert signed_in.status_code == 200

    # Scenario 1
    def test_the_owned_and_the_credited_projects_are_both_listed_once_with_the_owned_marked(
        self, get_page, owner_world
    ):
        world = owner_world

        _, page = get_page(world.organization.get_absolute_url())

        listed = _entries(page, "projects")
        assert sorted(listed) == sorted(
            p.get_absolute_url()
            for p in (world.owned, world.owned_and_credited, world.credited)
        )
        assert sorted(_owned_marks(page, "projects")) == sorted(
            p.get_absolute_url() for p in (world.owned, world.owned_and_credited)
        )

    # Scenario 2
    def test_the_public_datasets_of_an_owned_project_count_whether_or_not_it_is_credited_on_them(
        self, get_page, owner_world
    ):
        world = owner_world

        _, page = get_page(world.organization.get_absolute_url())

        listed = _entries(page, "datasets")
        assert world.inside_not_credited.get_absolute_url() in listed
        assert world.inside_credited.get_absolute_url() in listed
        assert len(listed) == len(set(listed))

    def test_the_figures_equal_the_projects_and_datasets_listed(
        self, get_page, owner_world
    ):
        world = owner_world
        organization = world.organization

        _, page = get_page(organization.get_absolute_url())

        assert _figure(page, _tab_url(organization, "projects")) == 3
        assert _figure(page, _tab_url(organization, "datasets")) == 3
        assert len(_entries(page, "datasets")) == 3

    # Scenario 3
    @pytest.mark.parametrize("who", ["visitor", "member", "manager"])
    def test_no_private_record_is_counted_or_named_anywhere_on_the_page(
        self, get_page, owner_world, who
    ):
        world = owner_world
        manager = _join(
            world.organization, "Manager Person", Affiliation.MembershipType.OWNER
        )
        viewer = {"visitor": None, "member": world.member, "manager": manager}[who]
        for private in (world.owned_private, world.credited_private):
            assign_perm("view_project", world.member, private)
        assign_perm("view_dataset", world.member, world.inside_private)

        response, page = get_page(world.organization.get_absolute_url(), viewer=viewer)

        content = response.content.decode()
        for record in (
            world.owned_private,
            world.credited_private,
            world.inside_private,
            world.inside_private_project,
            world.credited_private_dataset,
        ):
            assert record.get_absolute_url() not in content
            assert record.name not in content
        assert _figure(page, _tab_url(world.organization, "projects")) == 3
        assert _figure(page, _tab_url(world.organization, "datasets")) == 3

    # Scenario 4
    def test_the_records_of_its_members_are_not_counted_as_its_own(
        self, get_page, owner_world
    ):
        world = owner_world

        response, page = get_page(world.organization.get_absolute_url())

        content = response.content.decode()
        assert world.members_project.get_absolute_url() not in content
        assert world.members_dataset.get_absolute_url() not in content
        assert _figure(page, _tab_url(world.organization, "projects")) == 3

    # Scenario 5
    def test_only_current_verified_members_are_listed_and_counted_in_their_order(
        self, get_page, db
    ):
        organization = OrganizationFactory()
        member_b = _join(organization, "Beta")
        member_a = _join(organization, "Alpha")
        admin = _join(organization, "Yara", Affiliation.MembershipType.ADMIN)
        owner = _join(organization, "Zed", Affiliation.MembershipType.OWNER)
        pending = _join(organization, "Pending", Affiliation.MembershipType.PENDING)
        former = _join(organization, "Former", start_date="2010", end_date="2014")

        _, page = get_page(organization.get_absolute_url())

        assert _members(page) == [
            p.get_absolute_url() for p in (owner, admin, member_a, member_b)
        ]
        content = str(page)
        for gone in (pending, former):
            assert gone.get_absolute_url() not in content
        assert (
            page.select(".stat")[-1].select_one(".stat-value").get_text(strip=True)
            == "4"
        )

    # Scenario 6
    def test_the_last_place_counts_the_members_not_shown(self, get_page, db):
        organization = OrganizationFactory()
        people = [_join(organization, f"Member {n:02d}") for n in range(13)]

        _, page = get_page(organization.get_absolute_url())

        places = _members(page)
        assert len(places) == 10
        assert places[:9] == [p.get_absolute_url() for p in people[:9]]
        assert places[9] is None
        assert "+4" in _card(page, "members").select("ul > li")[9].get_text()
        assert (
            page.select(".stat")[-1].select_one(".stat-value").get_text(strip=True)
            == "13"
        )

    def test_ten_members_fill_the_card_without_a_count(self, get_page, db):
        organization = OrganizationFactory()
        people = [_join(organization, f"Member {n:02d}") for n in range(10)]

        _, page = get_page(organization.get_absolute_url())

        assert _members(page) == [p.get_absolute_url() for p in people]

    # Scenarios 7 and 8
    def test_the_hierarchy_lists_the_parent_the_siblings_with_this_one_and_its_children(
        self, get_page, db
    ):
        parent = OrganizationFactory(name="Parent")
        organization = OrganizationFactory(name="Middle", parent=parent)
        before = OrganizationFactory(name="Before", parent=parent)
        after = OrganizationFactory(name="Zulu", parent=parent)
        child_a = OrganizationFactory(name="Child A", parent=organization)
        child_b = OrganizationFactory(name="Child B", parent=organization)

        _, page = get_page(organization.get_absolute_url())

        card = _card(page, "hierarchy")
        assert _hrefs(card) == [
            o.get_absolute_url() for o in (parent, before, child_a, child_b, after)
        ]
        marked = card.select("[aria-current=page]")
        assert len(marked) == 1
        assert marked[0].select_one("a") is None

    def test_without_a_parent_the_hierarchy_starts_at_this_organization(
        self, get_page, db
    ):
        organization = OrganizationFactory()
        child = OrganizationFactory(parent=organization)

        _, page = get_page(organization.get_absolute_url())

        card = _card(page, "hierarchy")
        assert _hrefs(card) == [child.get_absolute_url()]
        assert card.select_one("ul > li > [aria-current=page]") is not None

    def test_with_neither_a_parent_nor_children_the_hierarchy_says_none_is_recorded(
        self, get_page, db
    ):
        organization = OrganizationFactory()

        _, page = get_page(organization.get_absolute_url())

        card = _card(page, "hierarchy")
        assert card.select_one("[role=alert]") is not None
        assert card.select_one("ul") is None

    # Scenario 9
    def test_an_organization_with_a_location_shows_a_map(self, get_page, db):
        organization = OrganizationFactory(location=PointFactory())

        _, page = get_page(organization.get_absolute_url())

        assert _card(page, "location") is not None

    def test_an_organization_without_a_location_shows_no_map_and_no_empty_card(
        self, get_page, db
    ):
        organization = OrganizationFactory(city="Potsdam", country="DE")

        _, page = get_page(organization.get_absolute_url())

        assert _card(page, "location") is None

    # Scenario 10
    def test_a_signed_in_person_who_is_not_a_member_sees_asking_to_join_as_not_available(
        self, get_page, owner_world
    ):
        stranger = PersonFactory(is_active=True)

        _, page = get_page(owner_world.organization.get_absolute_url(), viewer=stranger)

        (button,) = _join_actions(page)
        assert button["type"] == "button"
        assert _management_menu(page) == []

    def test_a_person_with_only_a_pending_request_may_still_ask_to_join(
        self, get_page, db
    ):
        organization = OrganizationFactory()
        pending = _join(organization, "Pending", Affiliation.MembershipType.PENDING)

        _, page = get_page(organization.get_absolute_url(), viewer=pending)

        assert len(_join_actions(page)) == 1

    def test_a_visitor_is_not_offered_asking_to_join(self, get_page, owner_world):
        _, page = get_page(owner_world.organization.get_absolute_url())

        assert _join_actions(page) == []
        assert _management_menu(page) == []

    def test_a_current_member_is_not_offered_asking_to_join(
        self, get_page, owner_world
    ):
        _, page = get_page(
            owner_world.organization.get_absolute_url(), viewer=owner_world.member
        )

        assert _join_actions(page) == []
        assert _management_menu(page) == []

    @pytest.mark.parametrize(
        "type", [Affiliation.MembershipType.ADMIN, Affiliation.MembershipType.OWNER]
    )
    def test_those_who_keep_the_record_get_the_management_menu_and_the_checklist(
        self, get_page, db, type
    ):
        organization = OrganizationFactory()
        manager = _join(organization, "Manager", type)

        _, page = get_page(organization.get_absolute_url(), viewer=manager)

        assert _management_menu(page)
        assert _join_actions(page) == []
        assert _card(page, "readiness") is not None

    def test_a_portal_role_alone_does_not_show_the_checklist_or_the_menu(
        self, get_page, db
    ):
        organization = OrganizationFactory()
        staff = PersonFactory(is_active=True, is_staff=True, is_superuser=True)

        _, page = get_page(organization.get_absolute_url(), viewer=staff)

        assert _card(page, "readiness") is None
        assert _management_menu(page) == []

    @pytest.mark.parametrize("who", ["visitor", "member"])
    def test_the_checklist_is_shown_to_no_one_who_does_not_keep_the_record(
        self, get_page, owner_world, who
    ):
        viewer = {"visitor": None, "member": owner_world.member}[who]

        _, page = get_page(owner_world.organization.get_absolute_url(), viewer=viewer)

        assert _card(page, "readiness") is None

    # Scenario 11
    def test_an_organization_with_nothing_recorded_still_shows_every_card_but_the_map(
        self, get_page, db
    ):
        organization = OrganizationFactory(
            name="Bare Organization", profile="", city="", country="", location=None
        )

        _, page = get_page(organization.get_absolute_url())

        shown = [card["data-card"] for card in page.select("[data-card]")]
        for name in (
            "about",
            "members",
            "projects",
            "datasets",
            "links",
            "hierarchy",
        ):
            assert name in shown
            assert _card(page, name).select_one("[role=alert], p") is not None
        assert "identifiers" in shown
        assert "location" not in shown

    # Scenario 12
    def test_the_page_head_carries_the_schema_org_description(
        self, get_page, owner_world
    ):
        organization = owner_world.organization

        _, page = get_page(organization.get_absolute_url())

        script = page.select_one("head script[type='application/ld+json']")
        data = json.loads(script.string)
        assert data["@type"] == "Organization"
        assert data["name"] == organization.name

    # SC-003
    @pytest.mark.parametrize("who", ["visitor", "member"])
    def test_each_figure_equals_the_number_of_entries_in_its_tab_for_an_organization_that_owns_a_project_it_is_not_credited_on(
        self, get_page, owner_world, who
    ):
        world = owner_world
        organization = world.organization
        viewer = {"visitor": None, "member": world.member}[who]

        _, page = get_page(organization.get_absolute_url(), viewer=viewer)
        projects, _ = get_page(_tab_url(organization, "projects"), viewer=viewer)
        datasets, _ = get_page(_tab_url(organization, "datasets"), viewer=viewer)

        assert world.owned.pk in {p.pk for p in projects.context["object_list"]}
        assert world.inside_not_credited.pk in {
            d.pk for d in datasets.context["object_list"]
        }
        assert _figure(page, _tab_url(organization, "projects")) == len(
            projects.context["object_list"]
        )
        assert _figure(page, _tab_url(organization, "datasets")) == len(
            datasets.context["object_list"]
        )


    # Scenario 1
    @pytest.mark.parametrize("who", ["owner", "admin"])
    def test_the_menus_edit_entry_links_to_the_editing_page_and_the_other_two_stay_disabled(
        self, get_page, keeper_world, who
    ):
        organization = keeper_world.organization

        response, page = get_page(
            organization.get_absolute_url(), viewer=getattr(keeper_world, who)
        )

        disabled = _management_menu(page)
        menu = disabled[0].find_parent("ul")
        assert len(disabled) == 2
        assert len(menu.find_all("li", recursive=False)) == 3
        assert [a["href"] for a in menu.select("a[href]")] == [
            organization.get_update_url()
        ]
        assert menu.select("button:not([disabled])") == []
        assert response.context["can_edit"] is True
        assert response.context["update_url"] == organization.get_update_url()

    # Scenario 7
    def test_the_checklist_items_the_page_can_fix_link_to_their_fields_and_the_ror_item_is_unchanged(
        self, get_page, keeper_world
    ):
        organization = keeper_world.organization
        update_url = organization.get_update_url()

        response, page = get_page(
            organization.get_absolute_url(), viewer=keeper_world.owner
        )

        urls = [item.get("url") for item in response.context["readiness"]["items"]]
        assert urls == [
            None,
            f"{update_url}#id_image",
            f"{update_url}#id_type",
            f"{update_url}#id_city",
            f"{update_url}#id_profile",
            f"{update_url}#id_website",
        ]
        assert set(_hrefs(_card(page, "readiness"))) == set(urls) - {None}

    def test_the_description_prompt_links_to_the_description_field(
        self, get_page, keeper_world
    ):
        organization = keeper_world.organization

        _, page = get_page(organization.get_absolute_url(), viewer=keeper_world.owner)

        assert _hrefs(_card(page, "about")) == [
            f"{organization.get_update_url()}#id_profile"
        ]

    # Scenario 8
    @pytest.mark.parametrize(
        "who",
        [
            "member",
            "pending",
            "stranger",
            "visitor",
            "staff",
            "superuser",
            "former_admin",
            "former_owner",
        ],
    )
    def test_nobody_else_is_offered_a_link_to_the_editing_page(
        self, get_page, keeper_world, who
    ):
        organization = keeper_world.organization
        viewer = None if who == "visitor" else getattr(keeper_world, who)

        response, page = get_page(organization.get_absolute_url(), viewer=viewer)

        assert page.select(f"a[href^='{organization.get_update_url()}']") == []
        assert response.context["can_edit"] is False


def _checklist(page):
    """The checklist card's progress as (items in place, total items), or None without it."""
    card = _card(page, "readiness")
    if card is None:
        return None
    bar = card.select_one("progress")
    return int(bar["value"]), int(bar["max"])


def _icon(button):
    """The markup of the icon a button carries."""
    return str(button.select_one("i, svg"))


@pytest.fixture
def incomplete_person(db):
    """A claimed person with a biography and nothing else on the checklist."""
    return PersonFactory(
        is_active=True, is_claimed=True, password="x", profile="A biography.", links=[]
    )


@pytest.mark.django_db
class TestPersonChecklist:
    # Scenario 1
    def test_the_person_sees_each_item_and_how_many_are_in_place(
        self, get_page, incomplete_person
    ):
        response, page = get_page(
            incomplete_person.get_absolute_url(), viewer=incomplete_person
        )

        complete = incomplete_person.get_profile_completeness()
        assert _checklist(page) == (sum(complete.values()), len(complete))
        assert len(_card(page, "readiness").select("ul > li")) == len(complete)
        assert _card(page, "readiness").select_one(".badge") is not None
        items = response.context["readiness"]["items"]
        assert [item["done"] for item in items] == [
            complete[key]
            for key in ("image", "orcid", "profile", "primary_affiliation", "links")
        ]

    def test_the_photo_and_the_links_are_optional_and_the_rest_are_not(
        self, get_page, incomplete_person
    ):
        response, _ = get_page(
            incomplete_person.get_absolute_url(), viewer=incomplete_person
        )

        items = response.context["readiness"]["items"]
        assert [item.get("required", True) for item in items] == [
            False,
            True,
            True,
            True,
            False,
        ]

    def test_a_profile_with_everything_in_place_is_ready(
        self, get_page, incomplete_person, orcid_signed_in
    ):
        person = PersonFactory(
            is_active=True,
            is_claimed=True,
            password="x",
            with_image=True,
            profile="A biography.",
            links=["https://example.org/me"],
        )
        orcid_signed_in(person)
        AffiliationFactory(person=person, is_primary=True)

        response, page = get_page(person.get_absolute_url(), viewer=person)

        assert _checklist(page) == (5, 5)
        assert response.context["readiness"]["ready"] is True
        assert _card(page, "readiness").select("a[href]") == []

    # Scenario 2
    @pytest.mark.parametrize("who", ["visitor", "signed_in", "staff", "superuser"])
    def test_nobody_else_sees_the_checklist(self, get_page, incomplete_person, who):
        viewer = {
            "visitor": None,
            "signed_in": PersonFactory(is_active=True, password="x"),
            "staff": PersonFactory(is_active=True, is_staff=True, password="x"),
            "superuser": PersonFactory(
                is_active=True, is_staff=True, is_superuser=True, password="x"
            ),
        }[who]

        response, page = get_page(incomplete_person.get_absolute_url(), viewer=viewer)

        assert response.status_code == 200
        assert _card(page, "readiness") is None
        assert "readiness" not in response.context

    # Scenario 3
    def test_the_orcid_item_links_to_the_page_where_an_account_is_connected(
        self, get_page, incomplete_person
    ):
        _, page = get_page(
            incomplete_person.get_absolute_url(), viewer=incomplete_person
        )

        assert reverse("socialaccount_connections") in _hrefs(_card(page, "readiness"))

    def test_connecting_orcid_puts_the_item_in_place_and_drops_its_link(
        self, get_page, incomplete_person, orcid_signed_in
    ):
        _, before = get_page(
            incomplete_person.get_absolute_url(), viewer=incomplete_person
        )
        orcid_signed_in(incomplete_person)

        _, after = get_page(
            incomplete_person.get_absolute_url(), viewer=incomplete_person
        )

        assert _checklist(after) == (_checklist(before)[0] + 1, _checklist(before)[1])
        assert reverse("socialaccount_connections") in _hrefs(_card(before, "readiness"))
        assert reverse("socialaccount_connections") not in _hrefs(
            _card(after, "readiness")
        )

    # Scenario 4
    def test_an_orcid_id_typed_in_does_not_put_the_item_in_place(
        self, get_page, incomplete_person
    ):
        ContributorIdentifier.objects.create(
            related=incomplete_person, type="ORCID", value="0000-0001-2345-6789"
        )

        _, page = get_page(
            incomplete_person.get_absolute_url(), viewer=incomplete_person
        )

        complete = incomplete_person.get_profile_completeness()
        assert complete["orcid"] is False
        assert _checklist(page) == (sum(complete.values()), len(complete))
        assert reverse("socialaccount_connections") in _hrefs(_card(page, "readiness"))

    def test_a_pending_primary_affiliation_does_not_put_its_item_in_place(
        self, get_page, incomplete_person
    ):
        AffiliationFactory(
            person=incomplete_person,
            is_primary=True,
            type=Affiliation.MembershipType.PENDING,
        )

        _, page = get_page(
            incomplete_person.get_absolute_url(), viewer=incomplete_person
        )

        assert _header(page).select_one("a[href*='/organization/']") is None
        assert _checklist(page) == (1, 5)

    # Scenario 5
    def test_the_person_is_offered_editing_in_place_of_the_contact_action(
        self, get_page, db
    ):
        person = PersonFactory(
            is_active=True, is_claimed=True, password="x", profile=""
        )

        _, own = get_page(person.get_absolute_url(), viewer=person)
        _, other = get_page(person.get_absolute_url())

        (contact,) = _join_actions(other)
        assert contact["type"] == "button"
        assert _join_actions(own) == []
        assert _card(own, "about").select_one("button[disabled]") is None

    @pytest.mark.parametrize("who", ["visitor", "signed_in", "superuser"])
    def test_anyone_else_is_offered_the_contact_action_and_not_editing(
        self, get_page, db, who
    ):
        person = PersonFactory(
            is_active=True, is_claimed=True, password="x", profile=""
        )
        _, visitor = get_page(person.get_absolute_url())
        viewer = {
            "visitor": None,
            "signed_in": PersonFactory(is_active=True, password="x"),
            "superuser": PersonFactory(
                is_active=True, is_staff=True, is_superuser=True, password="x"
            ),
        }[who]

        _, page = get_page(person.get_absolute_url(), viewer=viewer)

        (contact,) = _join_actions(page)
        (visitors_contact,) = _join_actions(visitor)
        assert _icon(contact) == _icon(visitors_contact)
        assert _card(page, "about").select_one("button[disabled]") is None


@pytest.fixture
def keeper_world(db):
    """An organization with each kind of person around it, and nothing recorded on it."""
    organization = OrganizationFactory(
        profile="", type="", city="", country="", links=[], location=None
    )
    return SimpleNamespace(
        organization=organization,
        owner=_join(organization, "Owner", Affiliation.MembershipType.OWNER),
        admin=_join(organization, "Admin", Affiliation.MembershipType.ADMIN),
        member=_join(organization, "Member", Affiliation.MembershipType.MEMBER),
        pending=_join(organization, "Pending", Affiliation.MembershipType.PENDING),
        former_admin=_join(
            organization,
            "Former admin",
            Affiliation.MembershipType.ADMIN,
            start_date="2010",
            end_date="2014",
        ),
        former_owner=_join(
            organization,
            "Former owner",
            Affiliation.MembershipType.OWNER,
            start_date="2010",
            end_date="2014",
        ),
        stranger=PersonFactory(is_active=True, password="x"),
        staff=PersonFactory(is_active=True, is_staff=True, password="x"),
        superuser=PersonFactory(
            is_active=True, is_staff=True, is_superuser=True, password="x"
        ),
    )


@pytest.mark.django_db
class TestOrganizationChecklist:
    # Scenario 6
    @pytest.mark.parametrize("who", ["owner", "admin"])
    def test_the_owner_and_the_administrators_see_the_checklist_and_the_menu(
        self, get_page, keeper_world, who
    ):
        response, page = get_page(
            keeper_world.organization.get_absolute_url(),
            viewer=getattr(keeper_world, who),
        )

        complete = keeper_world.organization.get_record_completeness()
        assert _checklist(page) == (sum(complete.values()), len(complete))
        assert len(_card(page, "readiness").select("ul > li")) == len(complete)
        assert _card(page, "readiness").select_one(".badge") is not None
        assert [item["done"] for item in response.context["readiness"]["items"]] == [
            complete[key]
            for key in ("ror", "image", "type", "location", "profile", "links")
        ]
        assert _management_menu(page)

    def test_the_logo_and_the_website_are_optional_and_the_rest_are_not(
        self, get_page, keeper_world
    ):
        response, _ = get_page(
            keeper_world.organization.get_absolute_url(), viewer=keeper_world.owner
        )

        items = response.context["readiness"]["items"]
        assert [item.get("required", True) for item in items] == [
            True,
            False,
            True,
            True,
            True,
            False,
        ]

    def test_every_management_action_but_editing_is_disabled(
        self, get_page, keeper_world
    ):
        organization = keeper_world.organization
        _, page = get_page(organization.get_absolute_url(), viewer=keeper_world.admin)

        disabled = _management_menu(page)
        menu = disabled[0].find_parent("ul")
        entries = menu.find_all("li", recursive=False)
        assert len(disabled) == len(entries) - 1
        assert [a["href"] for a in menu.select("a[href]")] == [
            organization.get_update_url()
        ]
        assert menu.select("button:not([disabled])") == []

    # FR-032
    @pytest.mark.parametrize(("who", "offered"), [("owner", True), ("member", False)])
    def test_only_the_people_who_keep_the_record_are_offered_writing_its_description(
        self, get_page, keeper_world, who, offered
    ):
        _, page = get_page(
            keeper_world.organization.get_absolute_url(),
            viewer=getattr(keeper_world, who),
        )

        action = _card(page, "about").select_one("a[href], button")
        assert (action is not None) is offered
        if offered:
            assert action["href"] == (
                f"{keeper_world.organization.get_update_url()}#id_profile"
            )

    def test_a_record_with_everything_in_place_is_ready(self, get_page, db):
        organization = OrganizationFactory(
            with_image=True,
            profile="A description.",
            type=OrganizationType.EDUCATION,
            city="Potsdam",
            country="DE",
            links=["https://example.org"],
        )
        ContributorIdentifier.objects.create(
            related=organization, type="ROR", value="https://ror.org/02nr0ka47"
        )
        owner = _join(organization, "Owner", Affiliation.MembershipType.OWNER)

        response, page = get_page(organization.get_absolute_url(), viewer=owner)

        assert _checklist(page) == (6, 6)
        assert response.context["readiness"]["ready"] is True

    # Scenario 7
    @pytest.mark.parametrize(
        "who", ["member", "pending", "stranger", "visitor", "staff", "superuser"]
    )
    def test_nobody_else_sees_the_checklist_or_the_menu(
        self, get_page, keeper_world, who
    ):
        viewer = None if who == "visitor" else getattr(keeper_world, who)

        response, page = get_page(
            keeper_world.organization.get_absolute_url(), viewer=viewer
        )

        assert response.status_code == 200
        assert _checklist(page) is None
        assert "readiness" not in response.context
        assert _management_menu(page) == []

    # Scenario 8
    @pytest.mark.parametrize("who", ["former_admin", "former_owner"])
    def test_a_former_administrator_sees_neither_the_checklist_nor_the_menu(
        self, get_page, keeper_world, who
    ):
        response, page = get_page(
            keeper_world.organization.get_absolute_url(),
            viewer=getattr(keeper_world, who),
        )

        assert response.status_code == 200
        assert _checklist(page) is None
        assert "readiness" not in response.context
        assert _management_menu(page) == []

    def test_the_checklist_and_the_menu_are_shown_together_or_not_at_all(
        self, get_page, keeper_world
    ):
        for name in vars(keeper_world):
            if name == "organization":
                continue
            _, page = get_page(
                keeper_world.organization.get_absolute_url(),
                viewer=getattr(keeper_world, name),
            )

            assert (_checklist(page) is not None) == bool(_management_menu(page)), name
