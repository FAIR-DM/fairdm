"""Forms for the Measurement app."""

from crispy_forms.helper import FormHelper
from django import forms

from .models import Measurement


class MeasurementForm(forms.ModelForm):
    """Base form for creating and editing Measurement instances.

    This form provides a foundation for measurement data entry. Subclasses
    should override to add domain-specific fields like 'value' and 'uncertainty'.

    Automatically excludes system-managed fields (created, modified, keywords,
    tree fields) from the form. Uses crispy_forms for enhanced rendering.

    The form can accept a request object to customize behavior based on the
    current user or request context.
    """

    class Meta:
        model = Measurement
        exclude = ["created", "modified", "keywords", "depth", "options", "path", "numchild", "tags"]

    def __init__(self, *args, **kwargs):
        """Initialize form with optional request context."""
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
