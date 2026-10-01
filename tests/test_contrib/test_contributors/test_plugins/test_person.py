"""Tests for the tabs beside a contributor's overview: their Projects and Datasets lists."""

import pytest
from django.urls import reverse

from fairdm.core.utils import assign_perm
from fairdm.factories import PersonFactory


def _tab_url(contributor, tab):
    return reverse(f"contributor:contributor-{tab}", kwargs={"uuid": contributor.uuid})


@pytest.mark.django_db
class TestContributorTabs:
    # Scenario 14
    def test_the_projects_tab_lists_the_public_projects_only(
        self, get_page, credited_world
    ):
        world = credited_world

        response, _ = get_page(_tab_url(world.person, "projects"))

        assert set(response.context["object_list"]) == {world.public_project}

    def test_the_datasets_tab_lists_the_public_datasets_outside_private_projects_only(
        self, get_page, credited_world
    ):
        world = credited_world

        response, _ = get_page(_tab_url(world.person, "datasets"))

        assert set(response.context["object_list"]) == {world.public_dataset}

    @pytest.mark.parametrize("tab", ["projects", "datasets"])
    def test_the_person_and_a_member_of_a_private_project_see_what_a_visitor_sees(
        self, get_page, credited_world, tab
    ):
        world = credited_world
        member = PersonFactory(is_active=True)
        assign_perm("view_project", member, world.private_project)
        visitor, _ = get_page(_tab_url(world.person, tab))

        for viewer in (world.person, member):
            response, _ = get_page(_tab_url(world.person, tab), viewer=viewer)

            assert set(response.context["object_list"]) == set(
                visitor.context["object_list"]
            )

    # #248
    @pytest.mark.parametrize("tab", ["projects", "datasets"])
    def test_each_tab_answers_for_a_visitor_and_for_a_signed_in_person(
        self, get_page, credited_world, tab
    ):
        world = credited_world

        visitor, _ = get_page(_tab_url(world.person, tab))
        signed_in, _ = get_page(_tab_url(world.person, tab), viewer=world.person)

        assert visitor.status_code == 200
        assert signed_in.status_code == 200

    @pytest.mark.parametrize("tab", ["projects", "datasets"])
    def test_a_contributor_credited_on_nothing_gets_an_empty_tab_not_an_error(
        self, get_page, db, tab
    ):
        person = PersonFactory()

        response, _ = get_page(_tab_url(person, tab))

        assert response.status_code == 200
        assert list(response.context["object_list"]) == []
