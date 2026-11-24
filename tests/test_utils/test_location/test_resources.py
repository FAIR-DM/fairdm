"""Tests for the location columns in ``fairdm.utils.location.resources``."""

import pytest
from django.core.exceptions import ValidationError
from import_export.resources import ModelResource

from demo.models import RockSample
from fairdm.utils.location.resources import LocatedResourceMixin


class RockSampleResource(LocatedResourceMixin, ModelResource):
    """A resource of rock samples with a number field and the location."""

    class Meta:
        model = RockSample
        fields = ("weight_grams", "location")


def refusal(row):
    """Return the errors, by field, a row is refused with."""
    with pytest.raises(ValidationError) as caught:
        RockSampleResource().import_instance(RockSample(), row)
    return caught.value.message_dict


class TestImportInstance:
    def test_invalid_field_without_location_column_is_refused(self):
        errors = refusal({"weight_grams": "heavy"})

        assert "weight_grams" in errors
        assert "location" not in errors

    def test_invalid_field_with_invalid_location_reports_both(self):
        errors = refusal(
            {"weight_grams": "heavy", "latitude": "95", "longitude": "8.4"}
        )

        assert "weight_grams" in errors
        assert "location" in errors

    def test_valid_row_without_location_column_is_not_refused(self):
        instance = RockSample()

        RockSampleResource().import_instance(instance, {"weight_grams": "12.5"})

        assert instance.weight_grams == 12.5
