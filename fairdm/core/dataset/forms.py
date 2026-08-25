"""Django forms for Dataset models.

This module provides forms for creating and editing Dataset instances with:
- Request-based queryset filtering (user permissions)
- Internationalized help text using gettext_lazy
- Autocomplete widgets on all ForeignKey/ManyToMany fields
- License field defaulting to CC BY 4.0
- Visibility field presented as a radio choice, pre-selecting Public
- Form-specific help text (not copied from model)

The forms follow Django best practices and integrate with FairDM's permission system.
"""

from django import forms
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_addanother.widgets import AddAnotherWidgetWrapper
from django_select2.forms import ModelSelect2Widget
from easy_thumbnails.widgets import ImageClearableFileInput
from licensing.models import License

from fairdm.core.image_utils import IMAGE_HELP_TEXT, validate_image_file_size
from fairdm.core.models import Project
from fairdm.forms import ModelForm
from fairdm.utils.choices import Visibility

from .models import Dataset

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

    **Identifiers:**
    External identifiers, including a DOI, are edited as rows on the update page's
    identifiers row set (014 plan P3), not through a field on this form.

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

    image = forms.ImageField(
        required=False,
        label=_("Cover Image"),
        help_text=IMAGE_HELP_TEXT,
        validators=[validate_image_file_size],
        widget=ImageClearableFileInput(
            thumbnail_options={"size": (150, 100), "crop": True}
        ),
    )

    name = forms.CharField(
        label=_("Name"),
        help_text=_(
            "Give your dataset a descriptive name that reflects its purpose and content. "
            "This will help others discover and understand your data."
        ),
        required=True,
        max_length=300,
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
    )

    # Note: reference field queryset is set in __init__ to avoid AppRegistryNotReady
    reference: forms.ModelChoiceField = forms.ModelChoiceField(
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

    visibility = forms.TypedChoiceField(
        label=_("Visibility"),
        choices=Visibility.choices,
        coerce=int,
        initial=Visibility.PUBLIC,
        help_text=_(
            "Whether this dataset's metadata may be read by anyone using the portal. "
            "The data held beneath the dataset is governed separately."
        ),
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Dataset
        fields = ["image", "name", "project", "license", "reference", "visibility"]
        # The shared render tag emits its own `<form>` whenever a crispy helper is
        # present, which nests a second one inside the one the update page already
        # opened. Every other core form sets this; the dataset form is the last to
        # (014 plan P4). Set through `helper_attrs` rather than replacing the helper
        # in `__init__` (`ProjectForm`'s approach), which keeps the derived layout,
        # the form id and the interaction attributes this metaclass builds.
        helper_attrs = {"form_tag": False}

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
        if project_field and self.request:
            # Only filter if request is provided
            if (
                hasattr(self.request, "user")
                and self.request.user is not None
                and self.request.user.is_authenticated
            ):
                # Show only user's accessible projects
                project_field.queryset = self.request.user.projects.all()
            else:
                # Anonymous user - show no projects (prevents data leakage)
                project_field.queryset = Project.objects.none()
        # If no request provided, leave queryset as-is (all projects)

        # Set reference queryset (literature items)
        # Note: literature app is optional, handle gracefully if not installed
        reference_field = self.fields.get("reference")
        if reference_field:
            try:
                from literature.models import LiteratureItem

                reference_field.queryset = LiteratureItem.objects.all()
            except (ImportError, LookupError):
                # Literature app not installed - try via apps registry
                from django.apps import apps

                try:
                    LiteratureItem = apps.get_model("literature", "LiteratureItem")
                    reference_field.queryset = LiteratureItem.objects.all()
                except LookupError:
                    # Model doesn't exist - remove field and update Meta.fields
                    del self.fields["reference"]
                    # Update Meta.fields to exclude reference
                    if hasattr(self.Meta, "fields") and "reference" in self.Meta.fields:
                        self.Meta.fields = [
                            f for f in self.Meta.fields if f != "reference"
                        ]


class DatasetCreateForm(DatasetForm):
    """Restricted form for initial dataset creation.

    Narrows the update page's declared ``DatasetForm`` (014 plan FR-022) to the four fields the
    creation page asks for: name, visibility, licence and project. All other fields (image,
    reference, descriptions) are available after creation via the full ``DatasetForm`` on the
    update page.

    Usage:
        ```python
        # In a create view
        form = DatasetCreateForm(request=request, data=request.POST)
        ```
    """

    class Meta(DatasetForm.Meta):
        fields = ["name", "project", "license", "visibility"]
