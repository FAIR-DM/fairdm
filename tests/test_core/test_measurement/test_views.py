"""The former measurement addresses under ``/measurement/``."""

import pytest
from pytest_django.asserts import assertRedirects

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from fairdm.factories import DatasetFactory
from fairdm.utils.choices import Visibility


def make_measurement(*, public=True):
    visibility = Visibility.PUBLIC if public else Visibility.PRIVATE
    dataset = DatasetFactory(visibility=visibility, published=public)
    sample = RockSampleFactory(dataset=dataset)
    return XRFMeasurementFactory(dataset=dataset, sample=sample)


@pytest.mark.django_db
class TestFormerAddressRedirect:
    def test_the_former_address_redirects_to_the_measurements_own_address(
        self, client
    ):
        xrf = make_measurement()

        response = client.get(f"/measurement/{xrf.uuid}/?from=citation")

        assertRedirects(
            response, f"/measurements/{xrf.uuid}/?from=citation", status_code=301
        )

    def test_a_page_below_the_former_address_redirects_to_the_same_page(self, client):
        xrf = make_measurement()

        response = client.get(f"/measurement/{xrf.uuid}/contributors/")

        assertRedirects(
            response,
            f"/measurements/{xrf.uuid}/contributors/",
            status_code=301,
            fetch_redirect_response=False,
        )

    def test_the_former_address_says_no_more_than_the_page_about_a_private_one(
        self, client
    ):
        private = make_measurement(public=False)

        response = client.get(f"/measurement/{private.uuid}/", follow=True)

        assert response.status_code == 404
