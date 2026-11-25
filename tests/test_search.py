"""Tests for the portal's site search kinds, their address and the header."""

import pytest
from django.test import Client
from django.urls import reverse
from mvp.search import registry

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    LiteratureItemFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    SampleIdentifierFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from tests.factories import ConcreteMeasurementFactory, ConcreteSampleFactory

WORD = "zephyrite"
KIND_NAMES = [
    "projects",
    "datasets",
    "samples",
    "measurements",
    "people",
    "organizations",
    "literature",
]


def panel(client, query, **params):
    """Search through the dialog's address and return its groups by kind name."""
    response = client.get(reverse("mvp-search-panel"), {"q": query, **params})
    assert response.status_code == 200
    return {group.kind.name: group for group in response.context["groups"]}


def urls(group):
    """Return the addresses a group's results link to."""
    return [result.url for result in group.results]


def make_everything(word=WORD):
    """Create one public record of every type whose name holds the word."""
    project = ProjectFactory(name=f"{word} project", visibility=Visibility.PUBLIC)
    dataset = DatasetFactory(
        name=f"{word} dataset",
        project=project,
        visibility=Visibility.PUBLIC,
        published=True,
    )
    sample = ConcreteSampleFactory(name=f"{word} sample", dataset=dataset)
    measurement = ConcreteMeasurementFactory(
        name=f"{word} measurement", sample=sample, dataset=dataset
    )
    person = PersonFactory(name=f"{word} Person")
    organization = OrganizationFactory(name=f"{word} institute")
    item = LiteratureItemFactory(title=f"{word} paper")
    return {
        "projects": project,
        "datasets": dataset,
        "samples": sample,
        "measurements": measurement,
        "people": person,
        "organizations": organization,
        "literature": item,
    }


@pytest.mark.django_db
class TestRegisteredKinds:
    def test_the_active_kinds_are_the_seven_record_types_in_order(self):
        active = registry.default_registry.active()

        assert [kind.name for kind in active] == KIND_NAMES


@pytest.mark.django_db
class TestFindsEveryRecordType:
    def test_every_record_type_appears_as_a_group_linking_to_its_record(self):
        records = make_everything()

        groups = panel(Client(), WORD)

        assert list(groups) == KIND_NAMES
        for name, record in records.items():
            assert groups[name].total == 1
            assert urls(groups[name]) == [record.get_absolute_url()]


@pytest.mark.django_db
class TestMatchingFollowsTheList:
    def test_a_sample_is_found_by_its_local_id(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        sample = ConcreteSampleFactory(dataset=dataset, local_id="LID-9137")

        groups = panel(Client(), "LID-9137")

        assert urls(groups["samples"]) == [sample.get_absolute_url()]

    @pytest.mark.parametrize(
        "kind", ["projects", "datasets", "samples", "measurements"]
    )
    def test_a_record_is_found_by_its_portal_id(self, kind):
        records = make_everything()
        record = records[kind]

        groups = panel(Client(), str(record.uuid))

        assert urls(groups[kind]) == [record.get_absolute_url()]

    def test_a_project_is_found_by_an_external_identifier(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        identifier = ProjectIdentifierFactory(related=project, value="ext-4471-id")

        groups = panel(Client(), identifier.value)

        assert urls(groups["projects"]) == [project.get_absolute_url()]

    def test_a_sample_identifier_does_not_find_the_sample(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        sample = ConcreteSampleFactory(dataset=dataset)
        identifier = SampleIdentifierFactory(related=sample, value="smp-ext-5521")

        groups = panel(Client(), identifier.value)

        assert "samples" not in groups

    def test_a_dataset_is_found_by_its_description(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, descriptions=1)
        passage = dataset.descriptions.first().value.split()[0]

        groups = panel(Client(), passage)

        assert dataset.get_absolute_url() in urls(groups["datasets"])

    @pytest.mark.parametrize(
        ("kind", "list_name"),
        [
            ("projects", "project-list"),
            ("datasets", "dataset-list"),
            ("people", "people-list"),
            ("organizations", "organization-list"),
            ("literature", "literature:item-list"),
        ],
    )
    def test_what_the_list_page_returns_the_kind_returns_too(self, kind, list_name):
        make_everything()
        client = Client()

        listed = client.get(reverse(list_name), {"q": WORD})
        found = panel(client, WORD)[kind]

        listed_urls = {obj.get_absolute_url() for obj in listed.context["object_list"]}
        assert listed_urls
        assert listed_urls <= set(urls(found))

    def test_a_query_that_is_only_a_doi_prefix_lists_no_literature(self):
        LiteratureItemFactory()

        groups = panel(Client(), "doi:")

        assert "literature" not in groups


@pytest.mark.django_db
class TestVisibility:
    @pytest.fixture
    def private(self):
        project = ProjectFactory(name=f"{WORD} private", visibility=Visibility.PRIVATE)
        dataset = DatasetFactory(
            name=f"{WORD} private dataset",
            project=project,
            visibility=Visibility.PRIVATE,
        )
        sample = ConcreteSampleFactory(name=f"{WORD} private sample", dataset=dataset)
        measurement = ConcreteMeasurementFactory(
            name=f"{WORD} private measurement", sample=sample, dataset=dataset
        )
        return project

    def client_for(self, person):
        client = Client()
        client.force_login(person)
        return client

    def test_a_visitor_finds_none_of_a_private_project_and_its_records(self, private):
        assert panel(Client(), WORD) == {}

    def test_a_person_with_no_level_finds_none_of_them(self, private):
        client = self.client_for(PersonFactory())

        assert panel(client, WORD) == {}

    def test_a_person_with_a_level_finds_and_counts_every_one(self, private):
        project = private
        person = PersonFactory()
        ContributionFactory(
            content_object=project, contributor=person, level=ContributionLevel.VIEW
        )

        groups = panel(self.client_for(person), WORD)

        assert {name: group.total for name, group in groups.items()} == {
            "projects": 1,
            "datasets": 1,
            "samples": 1,
            "measurements": 1,
        }

    def test_a_public_dataset_in_a_private_project_is_hidden_without_a_level(self):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        DatasetFactory(name=WORD, project=project, visibility=Visibility.PUBLIC)

        groups = panel(self.client_for(PersonFactory()), WORD)

        assert "datasets" not in groups

    def test_a_private_dataset_outside_any_project_follows_the_level_on_it(self):
        dataset = DatasetFactory(name=WORD, project=None, visibility=Visibility.PRIVATE)
        sample = ConcreteSampleFactory(name=WORD, dataset=dataset)
        holder = PersonFactory()
        ContributionFactory(
            content_object=dataset, contributor=holder, level=ContributionLevel.VIEW
        )

        assert panel(Client(), WORD) == {}
        assert panel(self.client_for(PersonFactory()), WORD) == {}
        groups = panel(self.client_for(holder), WORD)
        assert urls(groups["datasets"]) == [dataset.get_absolute_url()]
        assert urls(groups["samples"]) == [sample.get_absolute_url()]

    def test_a_superuser_is_not_found_among_the_people(self):
        PersonFactory(name=f"{WORD} Admin", is_superuser=True)

        groups = panel(Client(), WORD)

        assert "people" not in groups


@pytest.mark.django_db
class TestRegisteredTypes:
    def test_a_registered_sample_type_is_found_as_a_sample_and_links_to_its_page(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        sample = ConcreteSampleFactory(name=WORD, dataset=dataset)

        groups = panel(Client(), WORD)

        assert urls(groups["samples"]) == [sample.get_absolute_url()]


@pytest.mark.django_db
class TestResultsPage:
    def test_the_records_past_the_first_page_are_on_the_second(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        for _ in range(25):
            ConcreteSampleFactory(name=WORD, dataset=dataset)
        client = Client()
        params = {"q": WORD, "kind": "samples"}

        first = client.get(reverse("mvp-search"), params)
        second = client.get(reverse("mvp-search"), {**params, "page": 2})

        first_urls = {result.url for result in first.context["results"]}
        second_urls = {result.url for result in second.context["results"]}
        assert len(first_urls) + len(second_urls) == 25
        assert not first_urls & second_urls

    def test_a_query_that_matches_nothing_lists_no_group(self):
        make_everything()

        response = Client().get(reverse("mvp-search"), {"q": "nothingmatchesthis"})

        assert response.status_code == 200
        assert response.context["groups"] == []


@pytest.mark.django_db
class TestHeader:
    @pytest.mark.parametrize("signed_in", [False, True])
    def test_a_list_page_carries_the_dialog_and_the_form(self, signed_in):
        client = Client()
        if signed_in:
            client.force_login(UserFactory())

        html = client.get(reverse("dataset-list")).content.decode()

        assert 'id="mvp-search"' in html
        assert "data-mvp-search-form" in html

    def test_the_landing_page_carries_neither(self):
        html = Client().get(reverse("home")).content.decode()

        assert 'id="mvp-search"' not in html
        assert "data-mvp-search-form" not in html


@pytest.mark.django_db
class TestChecks:
    def test_the_system_checks_report_no_search_error(self):
        from django.core.checks import run_checks

        found = {message.id for message in run_checks()}

        assert not found & {f"mvp.E00{n}" for n in range(4, 10)}
