"""The Samples and Measurements tabs of a dataset."""

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from demo.factories import (
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
    SoilSampleFactory,
    XRFMeasurementFactory,
)
from demo.models import RockSample, SoilSample, XRFMeasurement
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import ContributionFactory, DatasetFactory, UserFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility

pytestmark = pytest.mark.django_db


def address(dataset, kind, type_model=None):
    """Return the address of a dataset's tab, or of one type beneath it."""
    kwargs = {"uuid": dataset.uuid}
    if type_model is None:
        return reverse(f"dataset:{kind}", kwargs=kwargs)
    slug = registry.get_for_model(type_model).get_slug()
    return reverse(f"dataset:{kind}-type", kwargs={**kwargs, "type": slug})


def listed(response):
    """Return the records one page of the response's table lists."""
    return [row.record for row in response.context["table"].page.object_list]


def tab_links(response, dataset):
    """Return the addresses of the two tabs that the response's tab strip offers.

    The strip is the list that holds the dataset's Overview and Contributors tabs, which every
    viewer of a public dataset is offered.
    """
    page = BeautifulSoup(response.content, "html.parser")
    anchors = {dataset.get_absolute_url(), address(dataset, "contribution-list")}
    strips = [
        [a["href"] for a in ul.find_all("a", href=True)]
        for ul in page.find_all("ul")
    ]
    strip = min((hrefs for hrefs in strips if anchors <= set(hrefs)), key=len)
    wanted = {address(dataset, "samples"), address(dataset, "measurements")}
    return wanted & set(strip)


def team_member(dataset, level=ContributionLevel.VIEW):
    """Return a user listed on the dataset at the given level."""
    user = UserFactory()
    ContributionFactory(content_object=dataset, contributor=user, level=level)
    return user


@pytest.fixture
def dataset():
    """A published dataset with three rocks and two soils, three XRF and two ICP-MS runs."""
    dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
    rocks = RockSampleFactory.create_batch(3, dataset=dataset)
    SoilSampleFactory.create_batch(2, dataset=dataset)
    XRFMeasurementFactory.create_batch(3, dataset=dataset, sample=rocks[0])
    ICP_MS_MeasurementFactory.create_batch(2, dataset=dataset, sample=rocks[1])
    dataset.rocks = rocks
    return dataset


class TestDatasetRecords:
    def test_each_tab_lists_the_most_numerous_type_of_only_this_dataset(
        self, client, dataset
    ):
        other = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        foreign = RockSampleFactory.create_batch(5, dataset=other)
        XRFMeasurementFactory.create_batch(5, dataset=other, sample=foreign[0])

        samples = client.get(address(dataset, "samples"))
        measurements = client.get(address(dataset, "measurements"))

        assert samples.status_code == measurements.status_code == 200
        assert {r.pk for r in listed(samples)} == {r.pk for r in dataset.rocks}
        assert {type(r) for r in listed(measurements)} == {XRFMeasurement}
        assert len(listed(measurements)) == 3

    def test_exactly_the_types_the_dataset_holds_are_offered_with_their_counts(
        self, client, dataset
    ):
        samples = client.get(address(dataset, "samples"))
        measurements = client.get(address(dataset, "measurements"))

        assert [e["count"] for e in samples.context["type_entries"]] == [3, 2]
        assert [e["count"] for e in measurements.context["type_entries"]] == [3, 2]
        assert [e["url"] for e in samples.context["type_entries"]] == [
            address(dataset, "samples", RockSample),
            address(dataset, "samples", SoilSample),
        ]

    def test_a_tie_in_counts_is_ordered_by_name(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        SoilSampleFactory(dataset=dataset)
        RockSampleFactory(dataset=dataset)

        response = client.get(address(dataset, "samples"))

        names = [e["name"] for e in response.context["type_entries"]]
        assert len(names) == 2
        assert names == sorted(names)

    def test_a_types_own_address_shows_that_type(self, client, dataset):
        response = client.get(address(dataset, "samples", SoilSample))

        assert response.status_code == 200
        assert {type(r) for r in listed(response)} == {SoilSample}
        assert len(listed(response)) == 2
        current = [e for e in response.context["type_entries"] if e["is_current"]]
        assert [e["count"] for e in current] == [2]

    def test_a_type_the_dataset_holds_none_of_is_not_found(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory(dataset=dataset)

        response = client.get(address(dataset, "samples", SoilSample))

        assert response.status_code == 404

    def test_an_unregistered_slug_is_not_found(self, client, dataset):
        url = reverse(
            "dataset:samples-type", kwargs={"uuid": dataset.uuid, "type": "no-such"}
        )

        assert client.get(url).status_code == 404

    def test_a_type_address_on_an_empty_tab_is_not_found(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)

        assert client.get(address(dataset, "samples", RockSample)).status_code == 404

    def test_a_measurement_on_another_datasets_sample_is_listed_with_its_own_dataset(
        self, client, dataset
    ):
        other = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        borrowed = RockSampleFactory(dataset=other)
        measurement = XRFMeasurementFactory(dataset=dataset, sample=borrowed)

        measurements = client.get(address(dataset, "measurements"))
        samples = client.get(address(other, "samples"))
        elsewhere = client.get(address(dataset, "samples"))

        assert measurement.pk in {r.pk for r in listed(measurements)}
        assert borrowed.pk in {r.pk for r in listed(samples)}
        assert borrowed.pk not in {r.pk for r in listed(elsewhere)}

    def test_a_private_dataset_is_not_found_to_a_visitor_and_open_to_its_team(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PRIVATE, published=True)
        rock = RockSampleFactory(dataset=dataset)
        XRFMeasurementFactory(dataset=dataset, sample=rock)

        assert client.get(address(dataset, "samples")).status_code == 404
        assert client.get(address(dataset, "measurements")).status_code == 404

        client.force_login(team_member(dataset))
        assert client.get(address(dataset, "samples")).status_code == 200
        assert client.get(address(dataset, "measurements")).status_code == 200

    def test_each_rows_name_links_to_the_record(self, client, dataset):
        response = client.get(address(dataset, "samples"))

        for record in dataset.rocks:
            assert f'href="{record.get_absolute_url()}"' in response.content.decode()

    def test_a_sample_page_has_neither_tab(self, client, dataset):
        sample = dataset.rocks[0]

        response = client.get(sample.get_absolute_url())

        page = BeautifulSoup(response.content, "html.parser")
        tabs = [
            a["href"]
            for a in page.find_all("a", href=True)
            if a["href"].startswith(sample.get_absolute_url())
        ]
        assert tabs  # the sample's own tab strip is there
        assert not [
            h for h in tabs if h.rstrip("/").endswith(("samples", "measurements"))
        ]


class TestRecordState:
    @pytest.fixture
    def waiting(self):
        """A public dataset not yet published, holding a rock and its measurement."""
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        rock = RockSampleFactory(dataset=dataset)
        XRFMeasurementFactory(dataset=dataset, sample=rock)
        return dataset

    def test_a_visitor_is_offered_neither_tab_and_both_addresses_are_not_found(
        self, client, waiting
    ):
        overview = client.get(waiting.get_absolute_url())

        assert overview.status_code == 200
        assert tab_links(overview, waiting) == set()
        assert client.get(address(waiting, "samples")).status_code == 404
        assert client.get(address(waiting, "measurements")).status_code == 404
        assert client.get(address(waiting, "samples", RockSample)).status_code == 404

    def test_the_team_gets_both_tabs_and_the_rows(self, client, waiting):
        client.force_login(team_member(waiting))

        overview = client.get(waiting.get_absolute_url())
        samples = client.get(address(waiting, "samples"))
        measurements = client.get(address(waiting, "measurements"))

        assert tab_links(overview, waiting) == {
            address(waiting, "samples"),
            address(waiting, "measurements"),
        }
        assert samples.context["record_state"] == "listed"
        assert len(listed(samples)) == 1
        assert len(listed(measurements)) == 1

    @pytest.mark.parametrize("kind", ["samples", "measurements"])
    def test_a_dataset_holding_nothing_is_empty_for_everyone(self, client, kind):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)

        overview = client.get(dataset.get_absolute_url())
        response = client.get(address(dataset, kind))

        assert len(tab_links(overview, dataset)) == 2
        assert response.status_code == 200
        assert response.context["record_state"] == "empty"
        assert response.context["type_entries"] == []

    def test_an_unpublished_dataset_holding_nothing_is_empty_for_its_team(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        client.force_login(team_member(dataset))

        response = client.get(address(dataset, "samples"))

        assert response.status_code == 200
        assert response.context["record_state"] == "empty"
        assert len(tab_links(client.get(dataset.get_absolute_url()), dataset)) == 2

    def test_with_no_measurement_type_registered_the_tab_is_empty(
        self, client, monkeypatch
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        monkeypatch.setattr(type(registry), "measurements", property(lambda self: []))

        response = client.get(address(dataset, "measurements"))

        assert response.status_code == 200
        assert response.context["record_state"] == "empty"
