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

    def test_each_listed_record_carries_the_counts_its_card_draws(
        self, get_page, credited_world
    ):
        world = credited_world

        projects, _ = get_page(_tab_url(world.person, "projects"))
        datasets, _ = get_page(_tab_url(world.person, "datasets"))

        (project,) = projects.context["object_list"]
        (dataset,) = datasets.context["object_list"]
        assert project.dataset_count == 1
        assert dataset.sample_count == 1
        assert dataset.measurement_count == 1

    @pytest.mark.parametrize("tab", ["projects", "datasets"])
    def test_a_member_of_a_private_project_sees_what_a_visitor_sees(
        self, get_page, credited_world, tab
    ):
        world = credited_world
        member = PersonFactory(is_active=True)
        assign_perm("view_project", member, world.private_project)
        visitor, _ = get_page(_tab_url(world.person, tab))

        response, _ = get_page(_tab_url(world.person, tab), viewer=member)

        assert set(response.context["object_list"]) == set(
            visitor.context["object_list"]
        )

    @pytest.mark.parametrize("tab", ["projects", "datasets"])
    def test_a_contributor_credited_on_nothing_gets_an_empty_tab_not_an_error(
        self, get_page, db, tab
    ):
        person = PersonFactory()

        response, _ = get_page(_tab_url(person, tab))

        assert response.status_code == 200
        assert list(response.context["object_list"]) == []
