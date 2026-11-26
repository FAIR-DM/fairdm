"""Tests for changing, removing and reordering what a record credits, through the test
client.
"""

import pytest
from bs4 import BeautifulSoup
from django.test import Client

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contribution
from fairdm.contrib.contributors.plugins.tab_base import MEMBER, role_by_slug
from fairdm.contrib.plugins import reverse
from fairdm.factories import ContributionFactory, OrganizationFactory, PersonFactory


def page_of(record, name, **kwargs):
    return reverse(record, f"contribution-list-{name}", **kwargs)


def browser_as(user):
    browser = Client()
    if user is not None:
        browser.force_login(user)
    return browser


def soup_of(response):
    return BeautifulSoup(response.content.decode(), "html.parser")


def credited(record, *, level=ContributionLevel.VIEW, **fields):
    """A person credited on the record who can sign in."""
    person = PersonFactory(is_active=True, is_claimed=True, password="x")
    return ContributionFactory(
        content_object=record, contributor=person, level=level, **fields
    )


@pytest.mark.django_db
class TestEditCredit:
    def test_the_sheet_offers_every_level_to_a_person_held_at_none_above(
        self, record, manager, colleague
    ):
        response = browser_as(manager).get(page_of(record, "edit", pk=colleague.pk))

        assert response.status_code == 200
        levels = soup_of(response).select("input[name=level]")
        assert [radio["value"] for radio in levels] == [
            str(level.value) for level in ContributionLevel
        ]
        assert not any(radio.has_attr("disabled") for radio in levels)

    def test_a_level_below_what_is_held_from_above_is_offered_disabled(
        self, public_chain
    ):
        manager = credited(public_chain.dataset, level=ContributionLevel.MANAGE)
        holder = PersonFactory(is_active=True, is_claimed=True)
        ContributionFactory(
            content_object=public_chain.project,
            contributor=holder,
            level=ContributionLevel.EDIT,
        )
        here = ContributionFactory(
            content_object=public_chain.dataset,
            contributor=holder,
            level=ContributionLevel.EDIT,
        )

        response = browser_as(manager.contributor).get(
            page_of(public_chain.dataset, "edit", pk=here.pk)
        )

        offered = {
            int(radio["value"]): radio.has_attr("disabled")
            for radio in soup_of(response).select("input[name=level]")
        }
        assert offered == {
            ContributionLevel.VIEW: True,
            ContributionLevel.EDIT: False,
            ContributionLevel.MANAGE: False,
        }

    def test_saving_changes_the_roles_affiliation_and_level(
        self, record, manager, colleague
    ):
        institute = OrganizationFactory()
        offered = list(
            browser_as(manager)
            .get(page_of(record, "edit", pk=colleague.pk))
            .context["roles"]
        )
        chosen = next(r for r in offered if r != role_by_slug(MEMBER))

        response = browser_as(manager).post(
            page_of(record, "edit", pk=colleague.pk),
            {
                "roles": [chosen.pk],
                "affiliation": institute.pk,
                "level": ContributionLevel.EDIT.value,
            },
        )

        colleague.refresh_from_db()
        assert response.status_code == 200
        assert colleague.affiliation_id == institute.pk
        assert colleague.level == ContributionLevel.EDIT
        assert chosen in colleague.roles.all()

    def test_a_level_below_what_is_held_from_above_is_refused(self, public_chain):
        manager = credited(public_chain.dataset, level=ContributionLevel.MANAGE)
        holder = PersonFactory(is_active=True, is_claimed=True)
        ContributionFactory(
            content_object=public_chain.project,
            contributor=holder,
            level=ContributionLevel.EDIT,
        )
        here = ContributionFactory(
            content_object=public_chain.dataset,
            contributor=holder,
            level=ContributionLevel.EDIT,
        )

        browser_as(manager.contributor).post(
            page_of(public_chain.dataset, "edit", pk=here.pk),
            {"level": ContributionLevel.VIEW.value},
        )

        here.refresh_from_db()
        assert here.level == ContributionLevel.EDIT

    @pytest.mark.parametrize("kind", ["project", "dataset"])
    def test_someone_who_holds_project_member_keeps_it_on_edit(
        self, public_chain, kind
    ):
        record = getattr(public_chain, kind)
        manager = credited(record, level=ContributionLevel.MANAGE).contributor
        colleague = credited(record)
        member = role_by_slug(MEMBER)
        colleague.roles.add(member)

        browser_as(manager).post(page_of(record, "edit", pk=colleague.pk), {})

        assert member in colleague.roles.all()

    @pytest.mark.parametrize("viewer", ["reader", "visitor"])
    def test_nobody_but_a_manager_may_edit(self, request, record, colleague, viewer):
        user = request.getfixturevalue(viewer) if viewer != "visitor" else None
        url = page_of(record, "edit", pk=colleague.pk)

        assert browser_as(user).get(url).status_code in {302, 403}
        assert browser_as(user).post(url, {"level": 3}).status_code in {302, 403}
        colleague.refresh_from_db()
        assert colleague.level == ContributionLevel.VIEW


@pytest.mark.django_db
class TestRemoveCredit:
    def test_removing_credits_nobody_and_offers_undo(self, record, manager, colleague):
        response = browser_as(manager).post(page_of(record, "remove", pk=colleague.pk))

        assert not Contribution.objects.filter(pk=colleague.pk).exists()
        assert soup_of(response).select_one("input[name=undo]")

    def test_undo_puts_them_back_as_they_were(self, record, manager, colleague):
        colleague.roles.set(
            browser_as(manager)
            .get(page_of(record, "edit", pk=colleague.pk))
            .context["roles"][:2]
        )
        before = (colleague.level, sorted(r.pk for r in colleague.roles.all()))
        removed = browser_as(manager).post(page_of(record, "remove", pk=colleague.pk))
        token = soup_of(removed).select_one("input[name=undo]")["value"]

        browser_as(manager).post(page_of(record, "undo"), {"undo": token})

        back = record.contributors.get(contributor=colleague.contributor)
        assert (back.level, sorted(r.pk for r in back.roles.all())) == before

    def test_an_altered_undo_is_refused(self, record, manager, colleague):
        removed = browser_as(manager).post(page_of(record, "remove", pk=colleague.pk))
        token = soup_of(removed).select_one("input[name=undo]")["value"]

        response = browser_as(manager).post(
            page_of(record, "undo"), {"undo": token[:-3] + "xyz"}
        )

        assert response.status_code == 400
        assert not record.contributors.filter(
            contributor=colleague.contributor
        ).exists()

    def test_the_last_manager_cannot_be_removed(self, record, manager):
        own = record.contributors.get(contributor=manager)

        browser_as(manager).post(page_of(record, "remove", pk=own.pk))

        assert Contribution.objects.filter(pk=own.pk).exists()

    def test_a_reader_cannot_remove(self, record, reader, colleague):
        browser_as(reader).post(page_of(record, "remove", pk=colleague.pk))

        assert Contribution.objects.filter(pk=colleague.pk).exists()


@pytest.mark.django_db
class TestReorder:
    def test_it_saves_the_order_given(self, record, manager, colleague):
        other = credited(record)
        wanted = [
            other.pk,
            colleague.pk,
            record.contributors.get(contributor=manager).pk,
        ]

        response = browser_as(manager).post(
            page_of(record, "reorder"), {"order": wanted}
        )

        assert response.status_code == 200
        ordered = list(record.contributors.people().values_list("pk", flat=True))
        assert ordered == wanted

    def test_an_order_naming_someone_not_credited_is_refused(
        self, record, manager, colleague
    ):
        response = browser_as(manager).post(
            page_of(record, "reorder"), {"order": [colleague.pk, 0]}
        )

        assert response.status_code == 400
