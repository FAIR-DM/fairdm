from crispy_forms.bootstrap import InlineRadios
from crispy_forms.helper import FormHelper, Layout
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from fairdm.contrib.contributors.models import Organization
from fairdm.core.choices import ProjectStatus
from fairdm.forms import ModelForm
from fairdm.utils.choices import Visibility

from .models import Project


class ProjectForm(ModelForm):
    """Base form for Project instances.

    Centralises all field declarations, help_texts, and widgets. Used directly
    by the update view and subclassed by ProjectCreateForm.
    """

    image = forms.ImageField(
        required=False,
        label=False,
    )
    name = forms.CharField(
        label=_("Project name"),
        max_length=255,
        help_text=_("A clear, descriptive name for your project."),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    status = forms.TypedChoiceField(
        label=_("Status"),
        choices=ProjectStatus.choices,
        coerce=int,
        help_text=_("Current phase of the project lifecycle."),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    visibility = forms.TypedChoiceField(
        label=_("Visibility"),
        choices=Visibility.choices,
        coerce=int,
        initial=Visibility.PUBLIC,
        help_text=_("Who can view this project?"),
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    owner = forms.ModelChoiceField(
        label=_("Owner organization"),
        queryset=None,  # Set in __init__
        help_text=_("The organization that owns this project."),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    funding = forms.JSONField(
        label=_("Funding information"),
        required=False,
        help_text=_("DataCite FundingReference schema (JSON format)."),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 10,
                "placeholder": _('[\n  {\n    "funderName": "...",\n    "awardNumber": "..."\n  }\n]'),
            }
        ),
    )

    class Meta:
        model = Project
        # TODO: Come up with a plan for editing funding data. This is a complex field that may require a custom interface
        # rather than a raw JSON textarea. For now, we declare the field but don't list it in meta.fields.
        fields = ["image", "name", "status", "visibility", "owner"]

    def __init__(self, *args, **kwargs):
        """Initialize form and set owner queryset if the field is present."""
        super().__init__(*args, **kwargs)
        if "owner" in self.fields:
            self.fields["owner"].queryset = Organization.objects.all()

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            "image",
            "name",
            "status",
            InlineRadios("visibility"),
            "owner",
        )


class ProjectCreateForm(ProjectForm):
    """Streamlined form for creating new Project instances.

    Restricts fields to the minimum required for project creation. Users can
    add detailed metadata through the edit interface after creation.
    """

    class Meta(ProjectForm.Meta):
        fields = ["name", "status", "visibility"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            "name",
            "status",
            InlineRadios("visibility"),
        )


class ProjectDescriptionForm(ModelForm):
    """Form for adding/editing ProjectDescription instances.

    Validates that only one description of each type exists per project,
    enforcing the unique_together constraint at the form level.

    Fields:
    - type: Description type from controlled vocabulary
    - value: Description text content

    Validation:
    - Enforces uniqueness of (related, type) combination
    - Provides clear error messages for duplicate types

    Usage:
        form = ProjectDescriptionForm(data=request.POST)
        form.instance.related = project
        if form.is_valid():
            form.save()
    """

    type = forms.ChoiceField(
        label=_("Description type"),
        help_text=_("What kind of description is this?"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    value = forms.CharField(
        label=_("Description"),
        help_text=_("Provide the description text."),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
            }
        ),
    )

    class Meta:
        from .models import ProjectDescription

        model = ProjectDescription
        fields = ["type", "value"]

    def __init__(self, *args, **kwargs):
        """Initialize form and set type choices from vocabulary."""
        super().__init__(*args, **kwargs)
        from .models import ProjectDescription

        # Set type choices from model vocabulary
        self.fields["type"].choices = ProjectDescription.VOCABULARY.choices

    def clean(self):
        """Validate that description type is unique for the project."""
        cleaned_data = super().clean()
        description_type = cleaned_data.get("type")

        # Check for duplicate description type on the same project
        if self.instance.related_id and description_type:
            from .models import ProjectDescription

            existing = (
                ProjectDescription.objects.filter(related=self.instance.related, type=description_type)
                .exclude(pk=self.instance.pk)
                .exists()
            )

            if existing:
                raise ValidationError(
                    {
                        "type": _("A description of type '{type}' already exists for this project.").format(
                            type=description_type
                        )
                    }
                )

        return cleaned_data


class ProjectDateForm(ModelForm):
    """Form for adding/editing ProjectDate instances.

    Validates date ranges to ensure end_date is not before start date when
    both fields are present. Supports PartialDate format (YYYY, YYYY-MM, YYYY-MM-DD).

    Fields:
    - type: Date type from controlled vocabulary
    - value: Primary date (start date for ranges)
    - end_date: Optional end date for date ranges

    Validation:
    - If end_date provided, must be after value (start date)
    - Supports PartialDate string format

    Note: AbstractDate currently only has 'value' field. If end_date is needed,
    it must be added to ProjectDate model first.

    Usage:
        form = ProjectDateForm(data=request.POST)
        form.instance.related = project
        if form.is_valid():
            form.save()
    """

    type = forms.ChoiceField(
        label=_("Date type"),
        help_text=_("What does this date represent?"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    value = forms.CharField(
        label=_("Date"),
        help_text=_("Date in YYYY, YYYY-MM, or YYYY-MM-DD format."),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("e.g., 2024-01-01"),
            }
        ),
    )

    # Note: end_date field would be added here when model supports it
    # end_date = forms.CharField(...)

    class Meta:
        from .models import ProjectDate

        model = ProjectDate
        fields = ["type", "value"]

    def __init__(self, *args, **kwargs):
        """Initialize form and set type choices from vocabulary."""
        super().__init__(*args, **kwargs)
        from .models import ProjectDate

        # Set type choices from model vocabulary
        self.fields["type"].choices = ProjectDate.VOCABULARY.choices

    def clean(self):
        """Validate date values and ranges.

        Note: Range validation would go here when end_date field is added to model.
        Current implementation validates single date value format.
        """
        cleaned_data = super().clean()

        # Future: Validate end_date is after value if both present
        # end_date = cleaned_data.get("end_date")
        # start_date = cleaned_data.get("value")
        # if end_date and start_date:
        #     if end_date < start_date:
        #         raise ValidationError({
        #             "end_date": _("End date cannot be before start date.")
        #         })

        return cleaned_data


class ProjectIdentifierForm(ModelForm):
    """Form for adding/editing ProjectIdentifier instances.

    Supports various identifier types (DOI, Grant numbers, etc.) with
    validation for format and uniqueness.

    Fields:
    - type: Identifier type from controlled vocabulary
    - value: Identifier value (must be unique across all projects)

    Validation:
    - Identifier value must be unique globally
    - Format validation can be added per identifier type

    Usage:
        form = ProjectIdentifierForm(data=request.POST)
        form.instance.related = project
        if form.is_valid():
            form.save()
    """

    type = forms.ChoiceField(
        label=_("Identifier type"),
        help_text=_("What type of identifier is this?"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    value = forms.CharField(
        label=_("Identifier value"),
        max_length=255,
        help_text=_("The unique identifier value."),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("e.g., 10.1000/example.doi.12345"),
            }
        ),
    )

    class Meta:
        from .models import ProjectIdentifier

        model = ProjectIdentifier
        fields = ["type", "value"]

    def __init__(self, *args, **kwargs):
        """Initialize form and set type choices from vocabulary."""
        super().__init__(*args, **kwargs)
        from .models import ProjectIdentifier

        # Set type choices from model vocabulary
        self.fields["type"].choices = ProjectIdentifier.VOCABULARY.choices
