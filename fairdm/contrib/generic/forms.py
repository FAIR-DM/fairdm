"""Forms and formsets for the vocabulary-typed models (descriptions, dates, keywords)."""

import copy

from crispy_forms.helper import FormHelper
from django import forms
from django.conf import settings
from django.forms import BaseFormSet, BaseInlineFormSet
from django.utils.module_loading import import_string
from django_select2.forms import Select2TagWidget
from extra_views import InlineFormSetFactory
from markdownx.fields import MarkdownxFormField

from fairdm.contrib.autocomplete.fields import ConceptMultiSelect
from fairdm.contrib.contributors.access import RecordAccess
from fairdm.core.abstract import DESCRIPTION_MAX_LENGTH
from fairdm.core.sample.models import SampleDescription
from fairdm.forms import PartialDateField


class TagWidget(Select2TagWidget):
    """Tag input that submits its tags as one comma-separated string."""

    def value_from_datadict(self, data, files, name):
        """Join the submitted tags with commas, or return None when there are none."""
        value = super().value_from_datadict(data, files, name)
        return ",".join(value) if value else None


class FormsetMixin:
    """Formset behaviour for models typed by a vocabulary, with one form per concept.

    Concepts without a row get an extra form, forms are listed in vocabulary order,
    and a form left blank is deleted on save.

    Args:
        *args: Passed to the formset base class.
        **kwargs: Passed to the formset base class. ``queryset`` is required and holds
            the existing rows.
    """

    def __init__(self, *args, **kwargs):
        self.vocabulary = self.model.VOCABULARY
        kwargs["initial"] = self.get_initial(kwargs.pop("queryset"))
        super().__init__(*args, **kwargs)
        self.can_delete = False
        self.can_delete_extra = False
        self.helper = FormHelper()
        self.helper.form_method = "post"

    def get_initial(self, qs):
        """Build initial data for each vocabulary value that has no row yet.

        Args:
            qs: The existing rows.

        Returns:
            One ``{"type": value}`` dict per missing vocabulary value.
        """
        existing_choices = qs.values_list("type", flat=True)
        missing_choices = [
            c for c in self.vocabulary.values if c not in existing_choices
        ]
        initial = [{"type": choice} for choice in missing_choices]
        self.extra = len(missing_choices)
        return initial

    def __iter__(self):
        """Yield the forms in vocabulary order rather than saved-first order."""
        form_map = {
            form.initial.get("type", form.instance.type): form for form in self.forms
        }
        for type_value in self.vocabulary.values:
            if type_value in form_map:
                yield form_map[type_value]

    def _construct_form(self, i, **kwargs):
        """Pass the vocabulary to each form for labelling."""
        kwargs["vocab"] = self.vocabulary
        return super()._construct_form(i, **kwargs)

    def save(self, commit=True):
        """Delete rows whose form was left blank, then save."""
        self._deleted_form_indexes = []
        self.can_delete = True
        for i, form in enumerate(self.forms):
            if (
                not form.cleaned_data.get("value")
                and i not in self._deleted_form_indexes
            ):
                self._deleted_form_indexes.append(i)

        return super().save(commit=commit)


class CoreFormset(FormsetMixin, BaseFormSet):
    """Plain formset for vocabulary-typed rows."""


class CoreInlineFormset(FormsetMixin, BaseInlineFormSet):
    """Inline formset for the generic models (Description, Date) attached to a core object.

    Rendered as one form per vocabulary choice, in vocabulary order.

    Args:
        *args: Passed to ``BaseInlineFormSet``.
        instance: The Project, Dataset, Sample or Measurement the rows belong to.
        **kwargs: Passed to ``BaseInlineFormSet``.
    """

    def __init__(self, *args, instance=None, **kwargs):
        kwargs["queryset"] = self.model._default_manager.filter(
            **{self.fk.name: instance}
        )
        super().__init__(*args, instance=instance, **kwargs)


class TypeVocabularyFormMixin(forms.ModelForm):
    """Hide the ``type`` field and label ``value`` from the type's vocabulary concept.

    Args:
        *args: Passed to ``ModelForm``.
        **kwargs: Passed to ``ModelForm`` after removing ``vocab``, the vocabulary
            whose concepts are mapped to type values.
    """

    def __init__(self, *args, **kwargs):
        vocabulary = kwargs.pop("vocab", [])
        super().__init__(*args, **kwargs)
        self.fields["type"].widget = forms.HiddenInput()

        if type_value := self.initial.get("type") or self.instance.type:
            concept = vocabulary.get_concept(type_value)
            self.fields["value"].label = concept.label()
            self.fields["value"].help_text = concept.definition()


class DateForm(TypeVocabularyFormMixin):
    """Form for a typed date whose ``value`` may be partial, such as a year or year-month.

    Attributes:
        value: The optional partial date. Label and help text come from the type's concept.
    """

    value = PartialDateField(required=False)

    class Meta:
        fields = ["value", "type"]


class KeywordForm(forms.ModelForm):
    """Manage an object's keywords with one autocomplete field per configured vocabulary.

    The vocabularies come from ``FAIRDM_DATASET["keyword_vocabularies"]`` for datasets and
    ``FAIRDM_{MODEL}["keywords"]`` for the other core models, read for the record's core model, so
    a registered sample type reads the sample setting. A record type with nothing configured gets
    the free-text tags alone. Tags come last.

    Args:
        *args: Passed to ``ModelForm``.
        **kwargs: Passed to ``ModelForm``. The model is taken from ``instance`` when given.
    """

    class Meta:
        fields = ["keywords"]

    @staticmethod
    def configured_vocabularies(record):
        """List the keyword vocabularies the portal configures for a record's core model.

        Args:
            record: A project, dataset, sample or measurement, of any registered type.

        Returns:
            The dotted paths of the vocabularies, empty when the setting or its key is absent.
        """
        name = RecordAccess(record).model._meta.model_name.upper()
        key = "keyword_vocabularies" if name == "DATASET" else "keywords"
        return (getattr(settings, f"FAIRDM_{name}", None) or {}).get(key) or []

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        if instance:
            # A copy, so building the form for one model never rebinds the class for the next.
            self._meta = copy.copy(self._meta)
            self._meta.model = type(instance)

        super().__init__(*args, **kwargs)

        vocabularies = self.configured_vocabularies(self.instance)

        existing_keywords = []
        if self.instance and self.instance.pk:
            existing_keywords = list(self.instance.keywords.all())

        for vocab_str in vocabularies:
            vocab_class = import_string(vocab_str)
            field_name = vocab_class.__name__

            self.fields[field_name] = ConceptMultiSelect(
                vocabulary=vocab_str, required=False
            )

            if existing_keywords:
                vocab_name = vocab_class._meta.name
                matching_keywords = [
                    kw for kw in existing_keywords if kw.vocabulary.name == vocab_name
                ]
                if matching_keywords:
                    self.initial[field_name] = matching_keywords

        self.fields["tags"] = forms.CharField(
            label="Free keywords",
            help_text="Additional keywords that are not available in the listed controlled vocabularies.",
            widget=TagWidget,
            required=False,
        )
        if self.instance.pk:
            tags = list(self.instance.tags.names())
            self.initial["tags"] = tags
            # A tag input draws only the options it is given, so the recorded tags are offered as
            # its choices to show as chosen.
            self.fields["tags"].widget.choices = [(tag, tag) for tag in tags]

        self.helper = FormHelper()
        self.helper.form_id = "keyword-form"

    def save(self, commit=True):
        """Save the vocabulary keywords and the free-text tags."""
        instance = super().save(commit=False)

        if commit:
            instance.save()

            concepts = []
            for field_name, field in self.fields.items():
                if (
                    isinstance(field, ConceptMultiSelect)
                    and field_name in self.cleaned_data
                ):
                    concepts.extend(self.cleaned_data[field_name])

            instance.keywords.set(concepts)

            if hasattr(instance, "tags") and "tags" in self.cleaned_data:
                tags_value = self.cleaned_data["tags"]
                if tags_value:
                    instance.tags.set(
                        tags_value.split(",")
                        if isinstance(tags_value, str)
                        else tags_value
                    )
                else:
                    instance.tags.clear()

        return instance


class BaseInlineFactory(InlineFormSetFactory):
    """Inline factory for ``UpdateWithInlinesView`` that disables deleting rows."""

    factory_kwargs = {
        "can_delete": False,
        "can_delete_extra": False,
    }


class DescriptionForm(TypeVocabularyFormMixin):
    """Form for a typed description written in Markdown.

    Attributes:
        value: The optional Markdown text. Label and help text come from the type's concept.
    """

    value = MarkdownxFormField(
        required=False,
        label=False,
        max_length=DESCRIPTION_MAX_LENGTH,
    )

    class Meta:
        model = SampleDescription
        fields = ["value", "type"]


class DescriptionInline(InlineFormSetFactory):
    """Inline for editing an object's descriptions.

    Args:
        parent_model: The model the descriptions belong to.
        request: The current request.
        instance: The parent object.
        view_kwargs: Accepted for compatibility and not used.
        view: Accepted for compatibility and not used.

    Attributes:
        form_class: The description form.
        formset_class: The formset that lists one form per description type.
    """

    form_class = DescriptionForm
    formset_class = CoreInlineFormset

    def __init__(self, parent_model, request, instance, view_kwargs=None, view=None):
        self.model = parent_model._meta.get_field("descriptions").related_model
        super().__init__(parent_model, request, instance, view_kwargs=None, view=None)

    def construct_formset(self):
        """Give the formset helper the collection's form id."""
        formset = super().construct_formset()
        formset.helper.form_id = "description-form-collection"
        return formset


class Description2Inline(BaseInlineFormSet):
    """Inline for editing an object's descriptions.

    Args:
        parent_model: The model the descriptions belong to.
        request: The current request.
        instance: The parent object.
        view_kwargs: Accepted for compatibility and not used.
        view: Accepted for compatibility and not used.

    Attributes:
        form_class: The description form.
        formset_class: The formset that lists one form per description type.
    """

    form_class = DescriptionForm
    formset_class = CoreInlineFormset

    def __init__(self, parent_model, request, instance, view_kwargs=None, view=None):
        self.model = parent_model._meta.get_field("descriptions").related_model
        super().__init__(parent_model, request, instance, view_kwargs=None, view=None)

    def construct_formset(self):
        """Give the formset helper the collection's form id."""
        formset = super().construct_formset()
        formset.helper.form_id = "description-form-collection"
        return formset
