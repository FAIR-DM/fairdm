"""
FairDM Demo Portal - Form Examples

This module demonstrates best practices for creating forms in FairDM portals,
including:

1. **Request-Based Queryset Filtering**: User permission integration
2. **Internationalized Help Text**: Using gettext_lazy for translation
3. **Autocomplete Widgets**: Select2 integration on all relationship fields
4. **License Defaults**: FAIR-compliant default licensing
5. **DOI Entry Fields**: Creating DatasetIdentifier instances
6. **Form-Specific Help Text**: User-friendly guidance (not model help_text)
7. **Validation**: Custom clean methods and field validators

These examples follow the patterns established in fairdm.core.dataset.forms
and can be adapted for custom Sample and Measurement models.

## Quick Reference

**Request Parameter Pattern**:
```python
class MyForm(ModelForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        if request and request.user.is_authenticated:
            self.fields["project"].queryset = request.user.projects.all()
```

**Internationalization**:
```python
from django.utils.translation import gettext_lazy as _

name = forms.CharField(
    label=_("Name"), help_text=_("Enter a descriptive name for better discoverability.")
)
```

**Autocomplete Widget**:
```python
from django_select2.forms import ModelSelect2Widget

project = forms.ModelChoiceField(
    queryset=Project.objects.all(),
    widget=ModelSelect2Widget(
        search_fields=["name__icontains"],
        attrs={"data-placeholder": _("Select a project...")},
    ),
)
```

**DOI Entry Field**:
```python
doi = forms.CharField(
    label=_("DOI"),
    help_text=_("Enter the DOI if already assigned"),
    required=False,
    widget=forms.TextInput(attrs={"pattern": r"10\\.\\d{4,}/.*"}),
)


def save(self, commit=True):
    instance = super().save(commit=commit)
    if commit and (doi := self.cleaned_data.get("doi")):
        DatasetIdentifier.objects.update_or_create(
            related=instance, type="DOI", defaults={"value": doi}
        )
    return instance
```

## Related Documentation

- **Form Guide**: `docs/portal-development/forms/creating-forms.md`
- **Dataset Form Reference**: `fairdm/core/dataset/forms.py`
- **Widget Customization**: `docs/portal-development/forms/widgets.md`

## Integration with FairDM Registry

Forms work seamlessly with the FairDM registry system. You can specify
custom form classes in your model configuration:

```python
from fairdm.registry import register, ModelConfiguration


@register
class MySampleConfig(ModelConfiguration):
    model = MySample
    form_class = MySampleForm  # Custom form class
    fields = ["name", "location", "date"]
```

See `docs/portal-development/registry_integration.md` for details.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django_select2.forms import ModelSelect2MultipleWidget, ModelSelect2Widget
from licensing.models import License

from fairdm.core.models import Project
from fairdm.core.sample.forms import SampleFormMixin
from fairdm.forms import ModelForm

# Import demo models for sample forms
from fairdm_demo.models import RockSample, WaterSample

# ============================================================================
# Example 1: Form with Request-Based Queryset Filtering
# ============================================================================


# Commented out example - uncomment and adapt
# class RockSampleForm(ModelForm):
class RockSampleFormExample(ModelForm):
    """Example form demonstrating request-based queryset filtering.

    This form shows how to:
    1. Accept optional request parameter in __init__()
    2. Filter project queryset based on user permissions
    3. Handle anonymous users gracefully
    4. Use gettext_lazy for all user-facing strings

    Pattern Usage:
    Copy this pattern to your own Sample/Measurement forms when you need
    to filter choices based on the authenticated user's permissions.

    Usage in views:
        ```python
        # In a view
        form = RockSampleForm(request=request, data=request.POST)

        # For editing
        form = RockSampleForm(request=request, instance=sample)
        ```
    """

    name = forms.CharField(
        label=_("Sample Name"),
        help_text=_(
            "Provide a unique, descriptive name for this rock sample. "
            "Include location or formation name if applicable (e.g., 'Granite-Site A-001')."
        ),
        required=True,
        max_length=200,
    )

    dataset = forms.ModelChoiceField(
        queryset=None,  # Set in __init__ based on user
        label=_("Dataset"),
        help_text=_(
            "Select the dataset this sample belongs to. You can only add samples "
            "to datasets where you have contributor permissions."
        ),
        required=True,
        widget=ModelSelect2Widget(
            search_fields=["name__icontains"],
            attrs={"data-placeholder": _("Select a dataset...")},
        ),
    )

    project = forms.ModelChoiceField(
        queryset=None,  # Set in __init__ based on user
        label=_("Project"),
        help_text=_("Optionally associate this sample with a research project for better organization and tracking."),
        required=False,
        widget=ModelSelect2Widget(
            search_fields=["name__icontains"],
            attrs={"data-placeholder": _("Select a project...")},
        ),
    )

    # Example: Rock-specific fields with internationalized help text
    rock_type = forms.CharField(
        label=_("Rock Type"),
        help_text=_(
            "Classify the rock type (e.g., igneous, sedimentary, metamorphic). "
            "Be as specific as possible for better analysis."
        ),
        required=False,
        max_length=100,
    )

    collection_date = forms.DateField(
        label=_("Collection Date"),
        help_text=_("Date when this sample was collected in the field."),
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        # model = RockSample
        model = None  # Replace with your model
        fields = ["name", "dataset", "project", "rock_type", "collection_date"]

    def __init__(self, request=None, *args, **kwargs):
        """Initialize form with optional request parameter for permission filtering.

        Args:
            request: Optional HttpRequest object for user context
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments (including 'instance' for editing)
        """
        super().__init__(*args, **kwargs)
        self.request = request

        # Filter dataset queryset based on user permissions
        dataset_field = self.fields.get("dataset")
        if dataset_field:
            if self.request and hasattr(self.request, "user") and self.request.user.is_authenticated:
                # Show only datasets where user is a contributor
                from fairdm.core.dataset.models import Dataset

                # This is a simplified example - adjust based on your permission logic
                dataset_field.queryset = Dataset.objects.filter(contributors__person=self.request.user)
            else:
                # Anonymous or no request - show no datasets (prevents data leakage)
                from fairdm.core.dataset.models import Dataset

                dataset_field.queryset = Dataset.objects.none()

        # Filter project queryset based on user permissions
        project_field = self.fields.get("project")
        if project_field:
            if self.request and hasattr(self.request, "user") and self.request.user.is_authenticated:
                # Show only user's accessible projects
                project_field.queryset = self.request.user.projects.all()
            else:
                # Anonymous - no projects
                project_field.queryset = Project.objects.none()


# ============================================================================
# Example 2: Form with License Default and DOI Entry
# ============================================================================


# Commented out example - uncomment and adapt
# class DatasetEnhancedForm(ModelForm):
class DatasetEnhancedFormExample(ModelForm):
    """Example form demonstrating license defaults and DOI entry.

    This form shows how to:
    1. Set license field default to CC BY 4.0
    2. Add DOI entry field that creates DatasetIdentifier
    3. Use autocomplete on all relationship fields
    4. Provide comprehensive help text

    Pattern Usage:
    Use this pattern when your model needs:
    - License field with FAIR-compliant default
    - DOI support through DatasetIdentifier
    - Rich metadata entry
    """

    name = forms.CharField(
        label=_("Dataset Name"),
        help_text=_(
            "Give your dataset a descriptive name that reflects its purpose and content. "
            "This will help others discover and understand your data."
        ),
        required=True,
        max_length=300,
    )

    license = forms.ModelChoiceField(
        queryset=License.objects.all(),
        label=_("License"),
        help_text=_(
            "Choose a license that defines how others can use this dataset. "
            "CC BY 4.0 (default) allows sharing and adaptation with attribution. "
            "This encourages FAIR data principles and open science."
        ),
        widget=ModelSelect2Widget(
            search_fields=["name__icontains"],
            attrs={"data-placeholder": _("Select a license...")},
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
        # model = Dataset
        model = None  # Replace with your model
        fields = ["name", "license", "keywords"]

    def __init__(self, *args, **kwargs):
        """Initialize form with license default."""
        super().__init__(*args, **kwargs)

        # Set license default to CC BY 4.0 (FAIR-compliant)
        license_field = self.fields.get("license")
        if license_field:
            cc_by_license = License.objects.filter(name="CC BY 4.0").first()
            if cc_by_license:
                license_field.initial = cc_by_license

        # Set keywords queryset
        # NOTE: Dataset model does not currently have a keywords field
        # keywords_field = self.fields.get("keywords")
        # if keywords_field:
        #     from fairdm.contrib.dicts.models import Term
        #     keywords_field.queryset = Term.objects.filter(vocabulary__name="Keywords")

        # Pre-populate DOI if editing existing instance
        if self.instance and self.instance.pk:
            from fairdm.core.dataset.models import DatasetIdentifier

            doi_identifier = DatasetIdentifier.objects.filter(related=self.instance, type="DOI").first()
            if doi_identifier:
                self.fields["doi"].initial = doi_identifier.value

    def save(self, commit=True):
        """Save instance and handle DOI identifier creation/update.

        This method extends the default save() to handle the DOI field which
        creates or updates a DatasetIdentifier instance with type='DOI'.

        Args:
            commit: Whether to save to database immediately

        Returns:
            The saved instance
        """
        instance = super().save(commit=commit)

        # Handle DOI field - create/update DatasetIdentifier
        doi_value = self.cleaned_data.get("doi", "").strip()

        if commit:
            from fairdm.core.dataset.models import DatasetIdentifier

            if doi_value:
                # Create or update DOI identifier
                DatasetIdentifier.objects.update_or_create(
                    related=instance,
                    type="DOI",
                    defaults={"value": doi_value},
                )
            else:
                # Remove DOI identifier if field is empty
                DatasetIdentifier.objects.filter(related=instance, type="DOI").delete()

        return instance


# ============================================================================
# Best Practices Summary
# ============================================================================

"""
## Form Best Practices for FairDM Portals

### 1. Request Parameter Pattern
- Always accept optional `request` parameter in __init__()
- Use it to filter querysets based on user permissions
- Handle anonymous users gracefully (show no data)
- Document the pattern in docstrings

### 2. Internationalization (i18n)
- Use gettext_lazy() for ALL user-facing strings
- Import as: from django.utils.translation import gettext_lazy as _
- Wrap labels, help_text, placeholders, error messages
- Test with different locale settings

### 3. Help Text Guidelines
- Create form-specific help_text (don't copy from model)
- Explain WHY a field is needed, not just WHAT it is
- Mention format requirements (dates, patterns, etc.)
- Reference examples when helpful
- Keep it concise but informative (1-2 sentences)

### 4. Autocomplete Widgets
- Use ModelSelect2Widget on ALL ForeignKey fields
- Use ModelSelect2MultipleWidget on ALL ManyToMany fields
- Configure search_fields for efficient lookups
- Add data-placeholder for better UX
- Test with large datasets (100+ records)

### 5. License Defaults
- Default to CC BY 4.0 for FAIR compliance
- Allow users to change before publication
- Explain license implications in help_text
- Use ModelSelect2Widget for searchability

### 6. DOI Entry Pattern
- Add DOI as CharField (not model field)
- Create/update DatasetIdentifier in save()
- Use regex pattern for validation
- Handle empty values (don't create identifier)
- Pre-populate when editing existing instance

### 7. Validation
- Use clean() for cross-field validation
- Use clean_<fieldname>() for single-field validation
- Raise ValidationError with clear messages
- Test edge cases (empty strings, None, special characters)

### 8. Field Ordering
- Group related fields logically
- Put required fields first
- Put optional/advanced fields last
- Match expected workflow (top-to-bottom)

### 9. Widget Customization
- Use AddAnotherWidgetWrapper for convenience
- Add placeholders for better UX
- Use appropriate input types (date, email, url)
- Add HTML5 validation attributes (pattern, min, max)

### 10. Testing
After creating forms, test:
1. Required field validation
2. Queryset filtering with different users
3. Anonymous user handling
4. DOI creation/update/deletion
5. License default behavior
6. Autocomplete functionality
7. Form rendering (no errors)
8. i18n string extraction (makemessages)

See: `tests/unit/core/dataset/test_form.py` for comprehensive form tests.
"""


# ============================================================================
# Concrete Sample Forms Using SampleFormMixin (Phase 5 - US3)
# ============================================================================


class RockSampleForm(SampleFormMixin, ModelForm):
    """Form for creating and editing Rock Sample instances.

    Inherits widget configuration, request handling, and crispy forms setup
    from SampleFormMixin. Adds rock-specific field configurations.

    Features:
        - Pre-configured Select2 widget for dataset
        - Permission-based dataset filtering
        - Default status value ('available')
        - Add another functionality for dataset
        - Internationalized help text
        - DateInput widget for collection_date

    Usage:
        # In a view with request context
        form = RockSampleForm(request=request, data=request.POST)

        # For editing existing sample
        form = RockSampleForm(request=request, instance=rock_sample)
    """

    class Meta:
        model = RockSample
        fields = [
            "name",
            "dataset",
            "local_id",
            "status",
            "location",
            "rock_type",
            "mineral_content",
            "weight_grams",
            "hardness_mohs",
            "collection_date",
            "image",
            "tags",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter sample name..."),
                }
            ),
            "local_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Optional local identifier..."),
                }
            ),
            "rock_type": forms.Select(attrs={"class": "form-select"}),
            "mineral_content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("List primary minerals..."),
                }
            ),
            "weight_grams": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "hardness_mohs": forms.NumberInput(attrs={"class": "form-control", "min": "1", "max": "10", "step": "0.1"}),
            "collection_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        help_text = {
            "name": _("A unique, descriptive name for this rock sample."),
            "dataset": _("The dataset this sample belongs to."),
            "local_id": _("Optional local identifier used in your laboratory."),
            "status": _("Current status of the sample."),
            "location": _("Geographic location where the sample was collected."),
            "rock_type": _("Classification of the rock (igneous, sedimentary, metamorphic)."),
            "mineral_content": _("Primary minerals present in the sample."),
            "weight_grams": _("Sample weight in grams."),
            "hardness_mohs": _("Hardness on the Mohs scale (1-10)."),
            "collection_date": _("Date when the sample was collected."),
            "image": _("Optional photo of the sample."),
            "tags": _("Keywords or tags for categorization."),
        }


class WaterSampleForm(SampleFormMixin, ModelForm):
    """Form for creating and editing Water Sample instances.

    Inherits widget configuration, request handling, and crispy forms setup
    from SampleFormMixin. Adds water quality specific field configurations.

    Features:
        - Pre-configured Select2 widget for dataset
        - Permission-based dataset filtering
        - Default status value ('available')
        - Add another functionality for dataset
        - Internationalized help text
        - Appropriate input widgets for numeric fields

    Usage:
        # In a view with request context
        form = WaterSampleForm(request=request, data=request.POST)

        # For editing existing sample
        form = WaterSampleForm(request=request, instance=water_sample)
    """

    class Meta:
        model = WaterSample
        fields = [
            "name",
            "dataset",
            "local_id",
            "status",
            "location",
            "water_source",
            "temperature_celsius",
            "ph_level",
            "turbidity_ntu",
            "dissolved_oxygen_mg_l",
            "conductivity_us_cm",
            "image",
            "tags",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter sample name..."),
                }
            ),
            "local_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Optional local identifier..."),
                }
            ),
            "water_source": forms.Select(attrs={"class": "form-select"}),
            "temperature_celsius": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "-50",
                    "max": "100",
                    "step": "0.1",
                }
            ),
            "ph_level": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "14", "step": "0.01"}),
            "turbidity_ntu": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "dissolved_oxygen_mg_l": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "conductivity_us_cm": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.1"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        help_text = {
            "name": _("A unique, descriptive name for this water sample."),
            "dataset": _("The dataset this sample belongs to."),
            "local_id": _("Optional local identifier used in your laboratory."),
            "status": _("Current status of the sample."),
            "location": _("Geographic location where the sample was collected."),
            "water_source": _("Type of water source (river, lake, groundwater, etc.)."),
            "temperature_celsius": _("Water temperature in degrees Celsius."),
            "ph_level": _("pH level on a 0-14 scale."),
            "turbidity_ntu": _("Turbidity measured in Nephelometric Turbidity Units (NTU)."),
            "dissolved_oxygen_mg_l": _("Dissolved oxygen concentration in mg/L."),
            "conductivity_us_cm": _("Electrical conductivity in microsiemens per centimeter (µS/cm)."),
            "image": _("Optional photo of the water sample or sampling location."),
            "tags": _("Keywords or tags for categorization."),
        }
