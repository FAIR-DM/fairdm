"""Tests for the organisation forms."""

import pytest
from django.contrib.gis.geos import Point

from fairdm.contrib.contributors.forms.organization import (
    OrganizationCreateForm,
    OrganizationProfileForm,
)
from fairdm.contrib.location.forms import LocationField
from fairdm.factories import OrganizationFactory


@pytest.mark.django_db
class TestOrganizationCreateForm:
    def test_ror_action_creates_the_organization_from_ror(
        self, registry_network, recorded
    ):
        registry_network.answer(
            "https://api.ror.org/v2/organizations/04z8jg394", recorded("ror-record")
        )
        form = OrganizationCreateForm(
            data={
                "action": "from_ror",
                "from_ror": "https://ror.org/04z8jg394",
                "name": "GFZ",
            }
        )
        assert form.is_valid(), form.errors

        organization = form.save()

        assert organization.pk is not None
        assert organization.name == "GFZ Helmholtz Centre for Geosciences"
        assert organization.city == "Potsdam"

    def test_the_location_is_a_point_only_input(self):
        field = OrganizationCreateForm().fields["location"]

        assert isinstance(field, LocationField)
        assert field.full is False

    def test_a_manually_added_organization_is_saved_with_the_point_typed(self):
        form = OrganizationCreateForm(
            data={
                "action": "from_form",
                "name": "Potsdam Research Institute",
                "country": "DE",
                "location_first": "52.39886",
                "location_second": "13.06566",
            }
        )
        assert form.is_valid(), form.errors

        organization = form.save()

        organization.refresh_from_db()
        assert organization.location.srid == 4326
        assert organization.location.y == pytest.approx(52.39886, abs=1e-4)
        assert organization.location.x == pytest.approx(13.06566, abs=1e-4)

    def test_a_manually_added_organization_without_coordinates_has_no_point(self):
        form = OrganizationCreateForm(
            data={
                "action": "from_form",
                "name": "Potsdam Research Institute",
                "country": "DE",
            }
        )
        assert form.is_valid(), form.errors

        organization = form.save()

        assert organization.location is None


@pytest.mark.django_db
class TestOrganizationProfileForm:
    def test_the_location_is_a_point_only_input(self):
        field = OrganizationProfileForm().fields["location"]

        assert isinstance(field, LocationField)
        assert field.full is False

    def test_the_point_typed_is_saved(self):
        organization = OrganizationFactory(location=None)
        form = OrganizationProfileForm(
            data={
                "name": organization.name,
                "country": "DE",
                "location_first": "48.9353",
                "location_second": "8.4021",
            },
            instance=organization,
        )
        assert form.is_valid(), form.errors

        form.save()

        organization.refresh_from_db()
        assert organization.location.equals(Point(8.4021, 48.9353, srid=4326))
