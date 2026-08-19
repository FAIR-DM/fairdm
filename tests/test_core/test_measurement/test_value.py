"""Tests for the value a measurement reports (User Story 7).

FR-036: a measurement reports a value - the type's nominated value where it has one,
the record's name otherwise.
FR-037: where a type records an uncertainty alongside its value, the reported value
carries it.
FR-038: a measurement renders its value for a person, with the uncertainty and units
carried alongside it.
FR-039: at least one framework-shipped type nominates a value and records an
uncertainty (`ICP_MS_Measurement`, T093) so this behaviour is exercised, not only
described.
"""

import pint
import pytest

from fairdm_demo.factories import ExampleMeasurementFactory, ICP_MS_MeasurementFactory


@pytest.mark.django_db
class TestGetValue:
    """`Measurement.get_value()` (FR-036)."""

    def test_type_nominating_a_value_reports_that_value(self, sample):
        measurement = ICP_MS_MeasurementFactory(sample=sample, value="5.000")
        measurement.refresh_from_db()

        assert measurement.get_value() == measurement.value

    def test_type_nominating_none_reports_the_record_name(self, sample):
        measurement = ExampleMeasurementFactory(sample=sample, name="Base Reading")

        assert measurement.get_value() == "Base Reading"


@pytest.mark.django_db
class TestGetValueWithUncertainty:
    """`Measurement.get_value()` carries a type's uncertainty (FR-037)."""

    def test_uncertainty_is_carried_with_the_value(self, sample):
        measurement = ICP_MS_MeasurementFactory(
            sample=sample, value="5.000", uncertainty="0.300"
        )
        measurement.refresh_from_db()

        result = measurement.get_value()

        # A pint `Measurement`'s attributes are `.value` and `.error` - not `.err`,
        # which no installed pint object carries (plan.md, R1).
        assert isinstance(result, pint.Measurement)
        assert result.value.magnitude == pytest.approx(
            float(measurement.value.magnitude)
        )
        assert result.error.magnitude == pytest.approx(
            float(measurement.uncertainty.magnitude)
        )
        assert result.value.units == measurement.value.units
