"""Tests for the PartialDateField model field."""

from fairdm.db.fields import PartialDateField
from fairdm.forms.fields import PartialDateField as PartialDateFormField


class TestPartialDateField:
    """Test the PartialDateField model field."""

    def test_formfield_returns_correct_form_field_class(self):
        """Test that formfield() returns an instance of PartialDateFormField."""
        model_field = PartialDateField(blank=True)
        form_field = model_field.formfield()

        assert isinstance(form_field, PartialDateFormField)

    def test_formfield_respects_blank(self):
        """Test that formfield() correctly sets required based on blank."""
        # blank=True should create non-required form field
        model_field_blank = PartialDateField(blank=True)
        form_field_blank = model_field_blank.formfield()
        assert form_field_blank.required is False

        # blank=False should create required form field
        model_field_required = PartialDateField(blank=False)
        form_field_required = model_field_required.formfield()
        assert form_field_required.required is True

    def test_formfield_preserves_verbose_name(self):
        """Test that formfield() uses verbose_name as the label."""
        model_field = PartialDateField(verbose_name="collection date", blank=True)
        form_field = model_field.formfield()

        assert form_field.label == "Collection date"

    def test_formfield_preserves_help_text(self):
        """Test that formfield() preserves help_text."""
        help_text = "Enter the date the sample was collected"
        model_field = PartialDateField(help_text=help_text, blank=True)
        form_field = model_field.formfield()

        assert form_field.help_text == help_text

    def test_formfield_accepts_kwargs_override(self):
        """Test that formfield() allows kwargs to override defaults."""
        model_field = PartialDateField(blank=True)
        form_field = model_field.formfield(required=True, label="Custom Label", help_text="Custom help text")

        assert form_field.required is True
        assert form_field.label == "Custom Label"
        assert form_field.help_text == "Custom help text"
