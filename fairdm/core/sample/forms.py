"""Forms for the Sample app."""

from crispy_forms.helper import FormHelper
from django import forms

from .models import Sample


class SampleForm(forms.ModelForm):
    """Form for creating and editing Sample instances.

    Automatically excludes system-managed fields (created, modified, keywords,
    tree fields) from the form. Uses crispy_forms for enhanced rendering.

    The form can accept a request object to customize behavior based on the
    current user or request context.
    """

    class Meta:
        model = Sample
        exclude = ["created", "modified", "keywords", "depth", "options", "path", "numchild", "keywords"]

    def __init__(self, *args, **kwargs):
        """Initialize form with optional request context."""
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        # if self.request:
        # self.fields["dataset"].queryset = self.request.user.datasets.all()
        # self.fields["dataset"].initial = self.request.GET.get("dataset")

        self.helper = FormHelper()
        self.helper.form_tag = False
        # self.helper.layout = fieldsets_to_crispy_layout(fieldsets)

    # def save(self, commit=True):
    #     instance = super().save(commit=False)
    #     if commit:
    #         instance.save()
    #     return instance
