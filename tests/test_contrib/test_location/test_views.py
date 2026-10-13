"""Tests for the location page in ``fairdm.contrib.location.views``."""

import pytest
from bs4 import BeautifulSoup
from django.db import connection
from django.test.utils import CaptureQueriesContext

from demo.factories import RockSampleFactory, WaterSampleFactory
from fairdm.factories import DatasetFactory, PointFactory, UserFactory
from fairdm.utils.choices import Visibility


@pytest.fixture
def point():
    return PointFactory()


@pytest.fixture
def released():
    """A dataset anyone may read: public and published."""
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


def links_on(response):
    """The addresses linked from a rendered page."""
    page = BeautifulSoup(response.content, "html.parser")
    return {link["href"] for link in page.find_all("a", href=True)}


@pytest.mark.django_db
class TestPointDetailView:
    def test_the_page_links_every_released_sample_at_the_location(
        self, client, point, released
    ):
        rock = RockSampleFactory(location=point, dataset=released)
        water = WaterSampleFactory(location=point, dataset=released)

        response = client.get(point.get_absolute_url())

        assert response.status_code == 200
        assert {rock.get_absolute_url(), water.get_absolute_url()} <= links_on(response)

    def test_a_sample_at_another_location_is_not_listed(self, client, point, released):
        elsewhere = RockSampleFactory(location=PointFactory(), dataset=released)

        response = client.get(point.get_absolute_url())

        assert elsewhere.get_absolute_url() not in links_on(response)

    def test_a_sample_in_a_private_dataset_is_hidden_from_a_visitor(
        self, client, point
    ):
        private = RockSampleFactory(
            location=point, dataset=DatasetFactory(), name="PRIVATE-SAMPLE-MARKER"
        )

        response = client.get(point.get_absolute_url())

        assert response.status_code == 200
        assert private.get_absolute_url() not in links_on(response)
        assert private.name not in response.content.decode()

    def test_a_sample_in_a_private_dataset_is_shown_to_someone_who_may_read_it(
        self, client, point
    ):
        private = RockSampleFactory(location=point, dataset=DatasetFactory())
        client.force_login(UserFactory(is_superuser=True))

        response = client.get(point.get_absolute_url())

        assert private.get_absolute_url() in links_on(response)

    def test_a_location_with_no_samples_renders(self, client, point):
        response = client.get(point.get_absolute_url())

        assert response.status_code == 200

    def test_an_address_with_no_location_is_not_found(self, client):
        response = client.get("/location/1.5/2.5/")

        assert response.status_code == 404

    def test_an_address_that_is_not_a_coordinate_pair_is_not_found(self, client):
        response = client.get("/location/here/there/")

        assert response.status_code == 404

    def test_the_query_count_does_not_grow_with_the_samples(
        self, client, point, released
    ):
        RockSampleFactory(location=point, dataset=released)
        # The first request also fills caches that later ones read.
        client.get(point.get_absolute_url())
        with CaptureQueriesContext(connection) as one:
            client.get(point.get_absolute_url())

        RockSampleFactory.create_batch(3, location=point, dataset=released)
        with CaptureQueriesContext(connection) as several:
            client.get(point.get_absolute_url())

        assert len(several) == len(one)
