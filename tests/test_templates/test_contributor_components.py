"""Tests for the ``c-contributor.*`` display components.

Each component is rendered through a small template that uses it the way a portal would, and the
tests read what it delivers: which contributors appear, where they link, what a missing value
falls back to, and the markup and slots a caller can rely on. Wording is never asserted.
"""

import pytest

from fairdm.factories import (
    AffiliationFactory,
    ContributionFactory,
    ContributorIdentifierFactory,
    OrganizationFactory,
    PersonFactory,
)


@pytest.fixture
def render_with(child_template, render_template):
    """Render a template source with a context and return its HTML."""

    def render(source, **context):
        return render_template(child_template(source), context)

    return render


@pytest.fixture
def credit(contribution_roles):
    """A contribution crediting a person under one role."""
    contribution = ContributionFactory()
    contribution.roles.add(contribution_roles.first())
    return contribution


@pytest.fixture
def contribution_roles(db):
    from research_vocabs.models import Concept

    return Concept.objects.filter(vocabulary__name="fairdm-roles")


@pytest.mark.django_db
class TestNames:
    def test_a_list_of_people_renders_every_name(self, render_with):
        people = PersonFactory.create_batch(2)

        html = render_with('<c-contributor.names :contributors="people" />', people=people)

        assert all(person.name in html for person in people)

    def test_past_max_the_rest_are_counted_and_link_to_the_full_list(self, render_with, soup):
        people = PersonFactory.create_batch(5)

        html = render_with(
            '<c-contributor.names :contributors="people" max="2" more_url="/all/" />',
            people=people,
        )

        page = soup(html)
        assert [a["href"] for a in page.select("a.link")][-1] == "/all/"
        assert people[2].name not in html

    def test_one_hidden_name_is_written_out_rather_than_counted(self, render_with):
        people = PersonFactory.create_batch(3)

        html = render_with('<c-contributor.names :contributors="people" max="2" />', people=people)

        assert all(person.name in html for person in people)

    def test_nobody_credited_draws_nothing(self, render_with, soup):
        html = render_with('<c-contributor.names :contributors="people" />', people=[])

        assert soup(html).get_text(strip=True) == ""


@pytest.mark.django_db
class TestAvatar:
    def test_the_avatar_is_the_daisyui_avatar_component(self, render_with, soup):
        person = PersonFactory()

        html = render_with('<c-contributor.avatar :contributor="person" />', person=person)

        assert soup(html).select_one(".avatar") is not None

    def test_a_person_without_a_photo_shows_their_initials(self, render_with, soup):
        person = PersonFactory(first_name="Ada", last_name="Lovelace", name="Ada Lovelace")

        html = render_with('<c-contributor.avatar :contributor="person" />', person=person)

        assert soup(html).get_text(strip=True) == "AL"

    def test_link_wraps_the_avatar_in_a_link_to_the_contributor(self, render_with, soup):
        person = PersonFactory()

        html = render_with('<c-contributor.avatar :contributor="person" link />', person=person)

        assert soup(html).find("a")["href"] == person.get_absolute_url()


@pytest.mark.django_db
class TestName:
    def test_a_person_links_to_their_page(self, render_with, soup):
        person = PersonFactory()

        html = render_with('<c-contributor.name :contributor="person" />', person=person)

        assert soup(html).find("a", string=person.name)["href"] == person.get_absolute_url()

    def test_a_persons_orcid_icon_links_to_their_orcid_record(self, render_with, soup):
        person = PersonFactory()
        orcid = ContributorIdentifierFactory(related=person, type="ORCID")

        html = render_with('<c-contributor.name :contributor="person" />', person=person)

        assert soup(html).find("a", href=orcid.get_absolute_url()) is not None

    def test_an_organizations_ror_icon_links_to_its_ror_record(self, render_with, soup):
        organization = OrganizationFactory()
        ror = ContributorIdentifierFactory(related=organization, type="ROR", value="04z8jg394")

        html = render_with('<c-contributor.name :contributor="org" />', org=organization)

        assert soup(html).find("a", href=ror.get_absolute_url()) is not None

    def test_identifier_false_leaves_the_icon_out(self, render_with, soup):
        person = PersonFactory()
        ContributorIdentifierFactory(related=person, type="ORCID")

        html = render_with(
            '<c-contributor.name :contributor="person" :identifier="False" />', person=person
        )

        assert [a["href"] for a in soup(html).find_all("a")] == [person.get_absolute_url()]

    def test_a_contribution_names_its_contributor(self, render_with, soup, credit):
        html = render_with('<c-contributor.name :contributor="credit" />', credit=credit)

        assert soup(html).find("a")["href"] == credit.contributor.get_absolute_url()


@pytest.mark.django_db
class TestItem:
    def test_a_person_is_shown_with_their_primary_organization(self, render_with, soup):
        person = PersonFactory()
        affiliation = AffiliationFactory(person=person, is_primary=True)

        html = render_with('<c-contributor.item :contributor="person" />', person=person)

        assert soup(html).find("a", href=affiliation.organization.get_absolute_url())

    def test_the_affiliation_on_a_credit_is_shown_instead(self, render_with, soup, credit):
        AffiliationFactory(person=credit.contributor, is_primary=True)
        credited_with = OrganizationFactory()
        credit.affiliation = credited_with
        credit.save()

        html = render_with('<c-contributor.item :contributor="credit" />', credit=credit)

        hrefs = [a["href"] for a in soup(html).find_all("a")]
        assert credited_with.get_absolute_url() in hrefs

    def test_an_organization_renders_with_no_affiliation_link(self, render_with, soup):
        organization = OrganizationFactory()

        html = render_with('<c-contributor.item :contributor="org" />', org=organization)

        assert [a["href"] for a in soup(html).find_all("a")] == [organization.get_absolute_url()]

    def test_the_roles_on_a_credit_are_listed(self, render_with, soup, credit):
        role = credit.roles.get()

        html = render_with('<c-contributor.item :contributor="credit" />', credit=credit)

        assert str(role.label) in [b.get_text(strip=True) for b in soup(html).select(".badge")]

    def test_secondary_none_leaves_the_second_line_out(self, render_with, soup):
        person = PersonFactory()
        affiliation = AffiliationFactory(person=person, is_primary=True)

        html = render_with(
            '<c-contributor.item :contributor="person" secondary="none" />', person=person
        )

        assert not soup(html).find("a", href=affiliation.organization.get_absolute_url())


@pytest.mark.django_db
class TestRow:
    def test_the_row_is_a_daisyui_list_row(self, render_with, soup):
        person = PersonFactory()

        html = render_with('<c-contributor.row :contributor="person" />', person=person)

        assert soup(html).select_one("li.list-row") is not None

    def test_the_actions_slot_is_drawn_in_the_row(self, render_with, soup):
        person = PersonFactory()

        html = render_with(
            '<c-contributor.row :contributor="person">'
            '<c-slot name="actions"><button id="edit-action">Edit</button></c-slot>'
            "</c-contributor.row>",
            person=person,
        )

        assert soup(html).select_one("li.list-row #edit-action") is not None


@pytest.mark.django_db
class TestStack:
    def test_past_max_a_placeholder_links_to_the_full_list(self, render_with, soup):
        people = PersonFactory.create_batch(4)

        html = render_with(
            '<c-contributor.stack :contributors="people" max="2" more_url="/all/" />',
            people=people,
        )

        assert soup(html).find("a", href="/all/") is not None


@pytest.mark.django_db
class TestByline:
    def test_each_shown_contributor_is_a_list_item(self, render_with, soup):
        people = PersonFactory.create_batch(3)

        html = render_with('<c-contributor.byline :contributors="people" />', people=people)

        assert len(soup(html).select("ul > li")) == 3


@pytest.mark.django_db
class TestCard:
    def test_a_persons_card_lists_their_portal_roles(self, render_with, soup):
        from django.contrib.auth.models import Group

        from fairdm.portal_roles import PortalRoles

        person = PersonFactory()
        person.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))

        html = render_with('<c-contributor.card :contributor="person" />', person=person)

        badges = [b.get_text(strip=True) for b in soup(html).select(".badge")]
        assert str(PortalRoles.DATA_CURATOR.label) in badges

    def test_an_organization_gets_the_organization_card(self, render_with, soup):
        organization = OrganizationFactory()

        html = render_with('<c-contributor.card :contributor="org" />', org=organization)

        assert soup(html).find("a", string=organization.name) is not None


@pytest.mark.django_db
@pytest.mark.parametrize("component", ["c-contributor.item", "c-contributor.card.person"])
class TestCreditedFromNone:
    def test_a_credit_with_no_organization_shows_none(
        self, render_with, soup, credit, component
    ):
        primary = AffiliationFactory(person=credit.contributor, is_primary=True)

        html = render_with(f'<{component} :contributor="credit" />', credit=credit)

        hrefs = [a["href"] for a in soup(html).find_all("a")]
        assert primary.organization.get_absolute_url() not in hrefs

    def test_a_credit_shows_the_organization_it_names(
        self, render_with, soup, credit, component
    ):
        AffiliationFactory(person=credit.contributor, is_primary=True)
        credited_with = OrganizationFactory()
        credit.affiliation = credited_with
        credit.save()

        html = render_with(f'<{component} :contributor="credit" />', credit=credit)

        hrefs = [a["href"] for a in soup(html).find_all("a")]
        assert credited_with.get_absolute_url() in hrefs

    def test_a_person_is_shown_with_their_primary_organization(
        self, render_with, soup, component
    ):
        person = PersonFactory()
        primary = AffiliationFactory(person=person, is_primary=True)

        html = render_with(f'<{component} :contributor="person" />', person=person)

        hrefs = [a["href"] for a in soup(html).find_all("a")]
        assert primary.organization.get_absolute_url() in hrefs

    def test_a_person_given_as_a_plain_contributor_row_keeps_their_primary_organization(
        self, render_with, soup, component
    ):
        from fairdm.contrib.contributors.models import Contributor

        person = PersonFactory()
        primary = AffiliationFactory(person=person, is_primary=True)
        plain = Contributor.objects.non_polymorphic().get(pk=person.pk)

        html = render_with(f'<{component} :contributor="plain" />', plain=plain)

        hrefs = [a["href"] for a in soup(html).find_all("a")]
        assert primary.organization.get_absolute_url() in hrefs
