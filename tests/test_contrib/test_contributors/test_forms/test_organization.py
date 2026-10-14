"""Tests for the organisation forms."""

import pytest

from fairdm.contrib.contributors.forms.organization import OrganizationCreateForm


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
