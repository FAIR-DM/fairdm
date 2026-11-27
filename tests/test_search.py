"""Tests for the portal's site search kinds, their address and the header."""

from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
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
from fairdm.search import register_kinds
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


def lines(group):
    """Return everything the group's results say under their titles, as one string."""
    return " ".join(f"{r.where} {r.passage}" for r in group.results)


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
    def test_registering_again_leaves_the_seven_kinds_as_they_are(self):
        register_kinds()

        names = [kind.name for kind in registry.default_registry.active()]
        assert names == KIND_NAMES


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

    def test_a_record_is_found_by_its_portal_id(self):
        records = make_everything()
        client = Client()

        failed = []
        for kind in ("projects", "datasets", "samples", "measurements"):
            record = records[kind]
            found = urls(panel(client, str(record.uuid)).get(kind, SimpleNamespace(results=[])))
            if found != [record.get_absolute_url()]:
                failed.append(f"{kind}: {found}")

        assert not failed, "These kinds did not find their record by portal id:\n" + "\n".join(failed)

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

    def test_what_the_list_page_returns_the_kind_returns_too(self):
        make_everything()
        client = Client()
        found = panel(client, WORD)

        failed = []
        for kind, list_name in [
            ("projects", "project-list"),
            ("datasets", "dataset-list"),
            ("people", "people-list"),
            ("organizations", "organization-list"),
            ("literature", "literature:item-list"),
        ]:
            listed = client.get(reverse(list_name), {"q": WORD})
            listed_urls = {
                obj.get_absolute_url() for obj in listed.context["object_list"]
            }
            if not listed_urls or not listed_urls <= set(urls(found[kind])):
                failed.append(f"{kind}: list shows {sorted(listed_urls)}")

        assert not failed, "\n".join(failed)

    def test_a_query_that_is_only_a_doi_prefix_lists_no_literature(self):
        LiteratureItemFactory()

        groups = panel(Client(), "doi:")

        assert "literature" not in groups


@pytest.mark.django_db
class TestOrdering:
    def test_results_are_ordered_by_name(self):
        for name in ("c", "a", "b"):
            OrganizationFactory(name=f"{WORD} {name}")

        found = panel(Client(), WORD)["organizations"]

        assert [r.title for r in found.results] == [f"{WORD} {n}" for n in "abc"]

    def test_every_kind_ends_its_order_with_the_record_id(self):
        """Read the order itself, as the database returns ties in no fixed order."""
        request = SimpleNamespace(user=AnonymousUser())

        not_ending_on_pk = [
            kind.name
            for kind in registry.default_registry.active()
            if kind.find(WORD, request).query.order_by[-1] != "pk"
        ]

        assert not_ending_on_pk == []


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

    def test_a_person_with_a_portal_wide_right_finds_every_private_record(
        self, private
    ):
        client = self.client_for(PersonFactory(is_superuser=True))

        groups = panel(client, WORD)

        assert urls(groups["projects"]) == [private.get_absolute_url()]

    def test_a_measurement_does_not_name_a_sample_the_person_cannot_open(self):
        hidden = DatasetFactory(project=None, visibility=Visibility.PRIVATE)
        sample = ConcreteSampleFactory(name="secretsamplename", dataset=hidden)
        shown = DatasetFactory(
            project=None, visibility=Visibility.PUBLIC, published=True
        )
        ConcreteMeasurementFactory(name=WORD, sample=sample, dataset=shown)

        group = panel(Client(), WORD)["measurements"]

        assert "secretsamplename" not in lines(group)

    def test_a_measurement_names_the_sample_to_a_person_who_may_open_it(self):
        hidden = DatasetFactory(project=None, visibility=Visibility.PRIVATE)
        sample = ConcreteSampleFactory(name="secretsamplename", dataset=hidden)
        shown = DatasetFactory(
            project=None, visibility=Visibility.PUBLIC, published=True
        )
        ConcreteMeasurementFactory(name=WORD, sample=sample, dataset=shown)
        holder = PersonFactory()
        ContributionFactory(
            content_object=hidden, contributor=holder, level=ContributionLevel.VIEW
        )

        group = panel(self.client_for(holder), WORD)["measurements"]

        assert "secretsamplename" in lines(group)

    def test_a_dataset_does_not_name_a_project_the_person_cannot_open(self):
        project = ProjectFactory(
            name="secretprojectname", visibility=Visibility.PRIVATE
        )
        dataset = DatasetFactory(
            name=WORD, project=project, visibility=Visibility.PRIVATE
        )
        holder = PersonFactory()
        ContributionFactory(
            content_object=dataset, contributor=holder, level=ContributionLevel.VIEW
        )

        group = panel(self.client_for(holder), WORD)["datasets"]

        assert urls(group) == [dataset.get_absolute_url()]
        assert "secretprojectname" not in lines(group)

    def test_a_dataset_names_the_project_to_a_person_who_may_open_it(self):
        project = ProjectFactory(
            name="secretprojectname", visibility=Visibility.PRIVATE
        )
        DatasetFactory(name=WORD, project=project, visibility=Visibility.PRIVATE)
        holder = PersonFactory()
        ContributionFactory(
            content_object=project, contributor=holder, level=ContributionLevel.VIEW
        )

        group = panel(self.client_for(holder), WORD)["datasets"]

        assert "secretprojectname" in lines(group)

    def test_a_dataset_names_its_public_project_to_a_visitor(self):
        project = ProjectFactory(name="openprojectname", visibility=Visibility.PUBLIC)
        DatasetFactory(
            name=WORD, project=project, visibility=Visibility.PUBLIC, published=True
        )

        group = panel(Client(), WORD)["datasets"]

        assert "openprojectname" in lines(group)

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
        # The wide-screen field and the narrow-screen button both open the dialog.
        page = BeautifulSoup(html, "html.parser")
        assert len(page.select('button[commandfor="mvp-search"]')) == 2
        assert page.select_one("button[data-mvp-search-open]") is not None

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
