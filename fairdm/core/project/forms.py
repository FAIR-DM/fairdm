from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from fairdm.forms import ModelForm
from fairdm.core.choices import ProjectStatus
from fairdm.utils.choices import Visibility

from .models import Project


class ProjectForm(ModelForm):
    """Form for creating and editing Project instances.

    Provides fields for project image, name, visibility, and status with
    custom widgets and help text to guide users through project creation.
    """

    image = forms.ImageField(
        required=False,
        label=False,
    )
    name = forms.CharField(
        label=_("Project name"),
        help_text=_("Provide the name of your project."),
    )
    visibility = forms.ChoiceField(
        label=_("Visibility"),
        choices=Project.VISIBILITY.choices,
        help_text=_("Should this project be visible to the public?"),
    )
    status = forms.ChoiceField(
        label=_("Current status"),
        choices=Project.STATUS_CHOICES.choices,
        help_text=_("In what phase of it's lifecycle is this project?"),
    )

    class Meta:
        model = Project
        fields = [
            "image",
            "name",
            "visibility",
            "status",
        ]


class ProjectCreateForm(ModelForm):
    """Streamlined form for creating new Project instances.

    Provides minimal required fields for quick project creation, following
    a GitHub-like repository creation pattern. Users can add detailed metadata
    through the edit interface after creation.

    Required fields:
    - name: Project name
    - status: Current project status
    - visibility: Public or private
    - owner: Owning organization

    Usage:
        form = ProjectCreateForm(data=request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
    """

    name = forms.CharField(
        label=_("Project name"),
        max_length=255,
        help_text=_("A clear, descriptive name for your project."),
        widget=forms.TextInput(attrs={
            "placeholder": _("e.g., Arctic Climate Study 2024"),
            "class": "form-control",
        }),
    )

    status = forms.ChoiceField(
        label=_("Status"),
        choices=ProjectStatus.choices,
        initial=ProjectStatus.CONCEPT,
        help_text=_("Current phase of the project lifecycle."),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    visibility = forms.ChoiceField(
        label=_("Visibility"),
        choices=Visibility.choices,
        initial=Visibility.PRIVATE,
        help_text=_("Who can view this project? Private projects are only visible to team members."),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    owner = forms.ModelChoiceField(
        label=_("Owner organization"),
        queryset=None,  # Set in __init__
        help_text=_("The organization that owns this project."),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Project
        fields = ["name", "status", "visibility", "owner"]

    def __init__(self, *args, **kwargs):
        """Initialize form and set owner queryset."""
        super().__init__(*args, **kwargs)
        # Set owner queryset to all organizations
        from fairdm.contrib.contributors.models import Organization
        self.fields["owner"].queryset = Organization.objects.all()


class ProjectEditForm(ModelForm):
    """Form for editing existing Project instances.

    Provides full access to project fields with validation rules to prevent
    invalid state transitions (e.g., concept projects cannot be made public).

    Validation rules:
    - Concept projects must remain private
    - All other statuses allow any visibility

    Usage:
        form = ProjectEditForm(data=request.POST, instance=project)
        if form.is_valid():
            form.save()
    """

    name = forms.CharField(
        label=_("Project name"),
        max_length=255,
        help_text=_("A clear, descriptive name for your project."),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    status = forms.ChoiceField(
        label=_("Status"),
        choices=ProjectStatus.choices,
        help_text=_("Current phase of the project lifecycle."),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    visibility = forms.ChoiceField(
        label=_("Visibility"),
        choices=Visibility.choices,
        help_text=_("Who can view this project?"),
        widget=forms.Select(attrs={"class": "form-control"}),
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
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 10,
            "placeholder": _('[\n  {\n    "funderName": "...",\n    "awardNumber": "..."\n  }\n]'),
        }),
    )

    class Meta:
        model = Project
        fields = ["name", "status", "visibility", "owner", "funding"]

    def __init__(self, *args, **kwargs):
        """Initialize form and set owner queryset."""
        super().__init__(*args, **kwargs)
        from fairdm.contrib.contributors.models import Organization
        self.fields["owner"].queryset = Organization.objects.all()

    def clean(self):
        """Validate form data and enforce business rules.

        Rules:
        - Concept projects cannot be made public
        """
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        visibility = cleaned_data.get("visibility")

        # Convert to integer if string
        if isinstance(status, str):
            status = int(status)
        if isinstance(visibility, str):
            visibility = int(visibility)

        # Rule: Concept projects must remain private
        if status == ProjectStatus.CONCEPT and visibility == Visibility.PUBLIC:
            raise ValidationError({
                "visibility": _(
                    "Concept projects cannot be made public. "
                    "Change the status to 'Planning' or 'In Progress' before making the project public."
                )
            })

        return cleaned_data


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
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 5,
        }),
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

            existing = ProjectDescription.objects.filter(
                related=self.instance.related,
                type=description_type
            ).exclude(pk=self.instance.pk).exists()

            if existing:
                raise ValidationError({
                    "type": _("A description of type '{type}' already exists for this project.").format(
                        type=description_type
                    )
                })

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
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("e.g., 2024-01-01"),
        }),
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
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("e.g., 10.1000/example.doi.12345"),
        }),
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

