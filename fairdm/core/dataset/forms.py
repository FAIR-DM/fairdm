"""Django forms for Dataset models.

This module provides forms for creating and editing Dataset instances with:
- Request-based queryset filtering (user permissions)
- Internationalized help text using gettext_lazy
- Autocomplete widgets on all ForeignKey/ManyToMany fields
- License field defaulting to CC BY 4.0
- DOI entry field that creates DatasetIdentifier
- Form-specific help text (not copied from model)

The forms follow Django best practices and integrate with FairDM's permission system.
"""

from django import forms
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_addanother.widgets import AddAnotherWidgetWrapper
from django_select2.forms import ModelSelect2MultipleWidget, ModelSelect2Widget
from licensing.models import License

from fairdm.core.models import Project
from fairdm.forms import ModelForm

from .models import Dataset, DatasetIdentifier

DEFAULT_LICENSE = getattr(settings, "FAIRDM_DEFAULT_LICENSE", "CC BY 4.0")


class DatasetForm(ModelForm):
    """Form for creating and editing Dataset instances.

    This form provides a user-friendly interface for dataset creation and editing
    with the following features:

    **Request Parameter:**
    The form accepts an optional `request` parameter in __init__() to enable
    user-specific queryset filtering. When provided, only projects accessible
    to the authenticated user are shown in the project field.

    Usage:
        ```python
        # In a view
        form = DatasetForm(request=request, data=request.POST)

        # For editing
        form = DatasetForm(request=request, instance=dataset)
        ```

    **User Permissions:**
    Project queryset is automatically filtered based on user permissions when
    request parameter is provided. Anonymous users see no projects, authenticated
    users see only their accessible projects.

    **License Default:**
    License field defaults to CC BY 4.0 (or FAIRDM_DEFAULT_LICENSE setting).
    This encourages open licensing consistent with FAIR principles.

    **DOI Support:**
    The DOI entry field creates/updates a DatasetIdentifier with type='DOI'
    when the form is saved. Empty DOI values do not create identifiers.

    **Internationalization:**
    All user-facing strings use gettext_lazy for translation support.

    **Widgets:**
    - Select2 autocomplete on all ForeignKey/ManyToMany fields
    - "Add another" functionality on project field
    - Image upload with preview (optional)

    See Also:
        - docs/portal-development/forms/dataset-forms.md
        - tests/unit/core/dataset/test_form.py
    """

    name = forms.CharField(
        label=_("Name"),
        help_text=_(
            "Give your dataset a descriptive name that reflects its purpose and content. "
            "This will help others discover and understand your data."
        ),
        required=True,
        max_length=300,
    )

    image = forms.ImageField(
        required=False,
        label=_("Dataset Image"),
        help_text=_(
            "Upload an image that represents this dataset (e.g., map, photo, diagram). "
            "Recommended aspect ratio is 16:9 for best display in cards and previews."
        ),
    )

    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        label=_("Project"),
        help_text=_(
            "Select the research project this dataset belongs to. Datasets can be "
            "organized under projects for better management. Use the plus icon to "
            "quickly create a new project if needed."
        ),
        required=False,
        widget=AddAnotherWidgetWrapper(
            ModelSelect2Widget(
                search_fields=["name__icontains"],
                attrs={"data-placeholder": _("Select a project...")},
            ),
            reverse_lazy("project-create"),
        ),
    )

    license = forms.ModelChoiceField(
        queryset=License.objects.all(),
        label=_("License"),
        help_text=_(
            "Choose a license that defines how others can use this dataset. "
            "CC BY 4.0 (default) allows sharing and adaptation with attribution. "
            "You can change this until the dataset is published."
        ),
        widget=ModelSelect2Widget(
            search_fields=["name__icontains"],
            attrs={"data-placeholder": _("Select a license...")},
        ),
    )

    reference = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        label=_("Data Publication"),
        help_text=_(
            "Link to the primary data publication (paper, report, or other literature) "
            "that describes this dataset. Use the plus icon to add a new publication."
        ),
        required=False,
        widget=AddAnotherWidgetWrapper(
            ModelSelect2Widget(
                search_fields=["title__icontains", "authors__icontains"],
                attrs={"data-placeholder": _("Select a publication...")},
            ),
            reverse_lazy("literature-create"),
        ),
    )

    keywords = forms.ModelMultipleChoiceField(
        queryset=None,  # Set in __init__
        label=_("Keywords"),
        help_text=_(
            "Add keywords to help others find this dataset. Keywords improve "
            "searchability and enable better dataset discovery."
        ),
        required=False,
        widget=ModelSelect2MultipleWidget(
            search_fields=["name__icontains"],
            attrs={
                "data-placeholder": _("Select keywords..."),
                "data-tags": "true",  # Allow creating new keywords
            },
        ),
    )

    doi = forms.CharField(
        label=_("DOI (Digital Object Identifier)"),
        help_text=_(
            "If this dataset already has a DOI assigned (e.g., from a data repository "
            "like Zenodo or Dryad), enter it here. Format: 10.1000/xyz123. "
            "Leave empty if no DOI has been assigned yet."
        ),
        required=False,
        max_length=255,
        widget=forms.TextInput(
            attrs={
                "placeholder": _("10.1000/example"),
                "pattern": r"10\.\d{4,}/.*",
                "title": _("DOI must start with 10. followed by a number"),
            }
        ),
    )

    class Meta:
        model = Dataset
        fields = ["name", "image", "project", "license", "reference", "keywords"]

    def __init__(self, request=None, *args, **kwargs):
        """Initialize form with optional request parameter for permission filtering.

        Args:
            request: Optional HttpRequest object for user context
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments (including 'instance' for editing)
        """
        super().__init__(*args, **kwargs)
        self.request = request

        # Set license default to CC BY 4.0
        license_field = self.fields.get("license")
        if license_field:
            license_field.initial = License.objects.filter(name=DEFAULT_LICENSE).first()

        # Filter project queryset based on user permissions
        project_field = self.fields.get("project")
        if project_field:
            if self.request and hasattr(self.request, "user") and self.request.user.is_authenticated:
                # Show only user's accessible projects
                project_field.queryset = self.request.user.projects.all()
            else:
                # Anonymous or no request - show no projects (prevents data leakage)
                project_field.queryset = Project.objects.none()

        # Set reference queryset (literature items)
        # reference_field = self.fields.get("reference")
        # if reference_field:
        #     from fairdm.contrib.literature.models import LiteratureItem

        #     reference_field.queryset = LiteratureItem.objects.all()

        # Set keywords queryset
        # NOTE: Dataset model does not currently have a keywords field
        # keywords_field = self.fields.get("keywords")
        # if keywords_field:
        #     from fairdm.contrib.dicts.models import Term
        #     keywords_field.queryset = Term.objects.filter(vocabulary__name="Keywords")

        # Pre-populate DOI field if editing existing dataset with DOI
        if self.instance and self.instance.pk:
            doi_identifier = DatasetIdentifier.objects.filter(related=self.instance, type="DOI").first()
            if doi_identifier:
                self.fields["doi"].initial = doi_identifier.value

    def save(self, commit=True):
        """Save dataset and handle DOI identifier creation/update.

        This method extends the default save() to handle the DOI field which
        creates or updates a DatasetIdentifier instance with type='DOI'.

        Args:
            commit: Whether to save to database immediately

        Returns:
            The saved Dataset instance
        """
        dataset = super().save(commit=commit)

        # Handle DOI field - create/update DatasetIdentifier
        doi_value = self.cleaned_data.get("doi", "").strip()

        if commit:
            if doi_value:
                # Create or update DOI identifier
                DatasetIdentifier.objects.update_or_create(
                    related=dataset,
                    type="DOI",
                    defaults={"value": doi_value},
                )
            else:
                # Remove DOI identifier if field is empty
                DatasetIdentifier.objects.filter(related=dataset, type="DOI").delete()

        return dataset
