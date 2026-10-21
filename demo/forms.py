r"""Forms for the demo models, with examples of common form patterns.

This module demonstrates best practices for creating forms in FairDM portals,
including:

1. **Request-Based Queryset Filtering**: User permission integration
2. **Internationalized Help Text**: Using gettext_lazy for translation
3. **Autocomplete Fields**: FairDM's record fields on relations to records
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

**Autocomplete Field**:
```python
from fairdm.contrib.autocomplete.fields import ProjectChoiceField

project = ProjectChoiceField(scope="edit", label=_("Project"))
```

**DOI Entry Field**:
```python
doi = forms.CharField(
    label=_("DOI"),
    help_text=_("Enter the DOI if already assigned"),
    required=False,
    widget=forms.TextInput(attrs={"pattern": r"10\.\d{4,}/.*"}),
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

## Best Practices

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
- Use the record fields from fairdm.contrib.autocomplete.fields for relations to
  projects, datasets, samples and measurements
- Pick the scope by what the field does: "edit" places a record inside another,
  "view" links to one
- Narrow with type=, depends_on= or prefer= instead of writing a view
- Test with large datasets (100+ records)

### 5. License Defaults
- Default to CC BY 4.0 for FAIR compliance
- Allow users to change before publication
- Explain license implications in help_text

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
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from licensing.models import License
from mvp_forms.widgets import TomSelectMultiple

from demo.models import RockSample, WaterSample
from fairdm.contrib.autocomplete.fields import (
    DatasetChoiceField,
    ProjectChoiceField,
    SampleChoiceField,
)
from fairdm.core.sample.forms import SampleFormMixin
from fairdm.forms import ModelForm


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
        form = RockSampleForm(request=request, data=request.POST)

        # For editing
        form = RockSampleForm(request=request, instance=sample)
        ```

    Args:
        request: Optional HttpRequest object for user context.
        *args: Positional arguments passed to the parent form.
        **kwargs: Keyword arguments passed to the parent form, including
            `instance` for editing.

    Attributes:
        name: The sample name.
        dataset: Dataset choice, limited to datasets the user contributes to.
        project: Optional project choice, limited to the user's projects.
        rock_type: Free-text rock classification.
        collection_date: Date the sample was collected.
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

    dataset = DatasetChoiceField(
        scope="edit",
        label=_("Dataset"),
        help_text=_(
            "Select the dataset this sample belongs to. You can only add samples "
            "to datasets you may edit."
        ),
        required=True,
    )

    project = ProjectChoiceField(
        scope="edit",
        label=_("Project"),
        help_text=_(
            "Optionally associate this sample with a research project for better organization and tracking."
        ),
        required=False,
    )

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
        model = None
        fields = ["name", "dataset", "project", "rock_type", "collection_date"]

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request


class DatasetEnhancedFormExample(ModelForm):
    """Example form demonstrating license defaults and DOI entry.

    This form shows how to:
    1. Set license field default to CC BY 4.0
    2. Add DOI entry field that creates DatasetIdentifier
    3. Use the record fields on relations to records
    4. Provide comprehensive help text

    Pattern Usage:
    Use this pattern when your model needs:
    - License field with FAIR-compliant default
    - DOI support through DatasetIdentifier
    - Rich metadata entry

    Args:
        *args: Positional arguments passed to the parent form.
        **kwargs: Keyword arguments passed to the parent form.

    Attributes:
        name: The dataset name.
        license: License choice, defaulting to CC BY 4.0 when it exists.
        keywords: Optional keyword selection.
        doi: Optional DOI, stored as a DatasetIdentifier on save.
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
    )

    keywords = forms.ModelMultipleChoiceField(
        queryset=None,
        label=_("Keywords"),
        help_text=_(
            "Add keywords to help others find this dataset. Keywords improve "
            "searchability and enable better dataset discovery."
        ),
        required=False,
        widget=TomSelectMultiple(placeholder=_("Select keywords...")),
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
        model = None
        fields = ["name", "license", "keywords"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        license_field = self.fields.get("license")
        if license_field:
            cc_by_license = License.objects.filter(name="CC BY 4.0").first()
            if cc_by_license:
                license_field.initial = cc_by_license

        if self.instance and self.instance.pk:
            from fairdm.core.dataset.models import DatasetIdentifier

            doi_identifier = DatasetIdentifier.objects.filter(
                related=self.instance, type="DOI"
            ).first()
            if doi_identifier:
                self.fields["doi"].initial = doi_identifier.value

    def save(self, commit=True):
        """Save the instance and create, update or remove its DOI identifier."""
        instance = super().save(commit=commit)

        doi_value = self.cleaned_data.get("doi", "").strip()

        if commit:
            from fairdm.core.dataset.models import DatasetIdentifier

            if doi_value:
                DatasetIdentifier.objects.update_or_create(
                    related=instance,
                    type="DOI",
                    defaults={"value": doi_value},
                )
            else:
                DatasetIdentifier.objects.filter(related=instance, type="DOI").delete()

        return instance


class RockSampleForm(SampleFormMixin, ModelForm):
    """Form for creating and editing Rock Sample instances.

    Inherits widget configuration, request handling, and crispy forms setup
    from SampleFormMixin. Adds rock-specific field configurations.

    Features:
        - Dataset field offering the datasets the user may edit
        - Default status value ('available')
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
            "weight_grams": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.01"}
            ),
            "hardness_mohs": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "max": "10", "step": "0.1"}
            ),
            "collection_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        help_text = {
            "name": _("A unique, descriptive name for this rock sample."),
            "dataset": _("The dataset this sample belongs to."),
            "local_id": _("Optional local identifier used in your laboratory."),
            "status": _("Current status of the sample."),
            "location": _("Geographic location where the sample was collected."),
            "rock_type": _(
                "Classification of the rock (igneous, sedimentary, metamorphic)."
            ),
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
        - Dataset field offering the datasets the user may edit
        - Default status value ('available')
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
            "ph_level": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "max": "14", "step": "0.01"}
            ),
            "turbidity_ntu": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.01"}
            ),
            "dissolved_oxygen_mg_l": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.01"}
            ),
            "conductivity_us_cm": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.1"}
            ),
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
            "turbidity_ntu": _(
                "Turbidity measured in Nephelometric Turbidity Units (NTU)."
            ),
            "dissolved_oxygen_mg_l": _("Dissolved oxygen concentration in mg/L."),
            "conductivity_us_cm": _(
                "Electrical conductivity in microsiemens per centimeter (µS/cm)."
            ),
            "image": _("Optional photo of the water sample or sampling location."),
            "tags": _("Keywords or tags for categorization."),
        }


class SampleReferenceFormExample(forms.Form):
    """Example form that picks one rock sample, with the sample field narrowed to a type.

    This form shows how to:
    1. Choose a sample among the ones the user may view, with no view or address of your own
    2. Keep the field to one registered sample type with ``type=``

    Pattern Usage:
        Build it inside a request, so the field knows who is choosing:

        ```python
        form = SampleReferenceFormExample(request.POST)
        ```

    Attributes:
        rock_sample: A rock sample the user may view. A sample of any other type is refused.
    """

    rock_sample = SampleChoiceField(
        type=RockSample,
        label=_("Rock sample"),
        help_text=_("Search by name, local ID or IGSN. Only rock samples are offered."),
    )
