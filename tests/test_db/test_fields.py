"""Tests for the quantity and partial-date model fields."""

import pytest
from bs4 import BeautifulSoup
from django import forms
from quantityfield.units import ureg

from fairdm.db.fields import PartialDateField
from fairdm.forms.fields import PartialDateField as PartialDateFormField
from tests.registry_models.models import ConcreteMeasurement

DepthForm = forms.modelform_factory(ConcreteMeasurement, fields=["depth"])


class TestQuantityField:
    def test_an_unchanged_edit_form_saves_the_stored_quantity(self, measurement):
        measurement.depth = ureg.Quantity(35.14, "m")
        measurement.save()
        rendered = BeautifulSoup(str(DepthForm(instance=measurement)), "html.parser")
        number = rendered.select_one("input[name=depth_0]")
        unit = rendered.select_one("select[name=depth_1] option[selected]")

        form = DepthForm(
            {"depth_0": number["value"], "depth_1": unit["value"]},
            instance=measurement,
        )

        assert form.is_valid(), form.errors
        form.save()
        measurement.refresh_from_db()
        assert measurement.depth == ureg.Quantity(35.14, "m")

    def test_a_value_in_another_allowed_unit_is_stored_in_base_units(self, measurement):
        form = DepthForm({"depth_0": "1.5", "depth_1": "km"}, instance=measurement)

        assert form.is_valid(), form.errors
        form.save()
        measurement.refresh_from_db()
        assert measurement.depth.magnitude == pytest.approx(1500)
        assert measurement.depth.units == ureg.meter


class TestPartialDateField:
    def test_formfield_returns_correct_form_field_class(self):
        model_field = PartialDateField(blank=True)
        form_field = model_field.formfield()

        assert isinstance(form_field, PartialDateFormField)

    def test_formfield_respects_blank(self):
        model_field_blank = PartialDateField(blank=True)
        form_field_blank = model_field_blank.formfield()
        assert form_field_blank.required is False

        model_field_required = PartialDateField(blank=False)
        form_field_required = model_field_required.formfield()
        assert form_field_required.required is True

    def test_formfield_preserves_verbose_name(self):
        model_field = PartialDateField(verbose_name="collection date", blank=True)
        form_field = model_field.formfield()

        assert form_field.label == "Collection date"

    def test_formfield_preserves_help_text(self):
        help_text = "Enter the date the sample was collected"
        model_field = PartialDateField(help_text=help_text, blank=True)
        form_field = model_field.formfield()

        assert form_field.help_text == help_text

    def test_formfield_accepts_kwargs_override(self):
        model_field = PartialDateField(blank=True)
        form_field = model_field.formfield(
            required=True, label="Custom Label", help_text="Custom help text"
        )

        assert form_field.required is True
        assert form_field.label == "Custom Label"
        assert form_field.help_text == "Custom help text"
