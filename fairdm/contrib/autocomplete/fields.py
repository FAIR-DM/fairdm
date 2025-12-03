"""Form fields for autocomplete functionality."""

from typing import Any, ClassVar

from dal import autocomplete, forward
from django import forms
from django.urls import reverse
from django.utils.module_loading import import_string
from research_vocabs.models import Concept


class ConceptMixin:
    widget: ClassVar[type[Any]]

    def __init__(self, vocabulary, minimum_input_length=2, **kwargs):
        # Import vocabulary if it's a string
        if isinstance(vocabulary, str):
            vocabulary = import_string(vocabulary)

        # Get vocabulary name from Meta or class name
        vocab_name = vocabulary._meta.name

        # Set up queryset filtered by vocabulary
        if "queryset" not in kwargs:
            kwargs["queryset"] = Concept.objects.filter(vocabulary__name=vocab_name)

        # Set up autocomplete widget
        if "widget" not in kwargs:
            kwargs["widget"] = self.widget(
                url=reverse("autocomplete:concept"),
                forward=(forward.Const(vocab_name, "vocabulary"),),
                attrs={
                    "data-placeholder": f"Select {vocabulary.__name__}...",
                    "data-minimum-input-length": minimum_input_length,
                },
            )

        # Set label if not provided
        if "label" not in kwargs:
            kwargs["label"] = vocabulary.__name__

        super().__init__(**kwargs)


class ConceptSelect(ConceptMixin, forms.ModelChoiceField):
    """
    A ModelChoiceField for selecting a single Concept with autocomplete.

    This field automatically configures autocomplete for a specific vocabulary,
    handling both VocabularyBuilder classes and string paths.

    Args:
        vocabulary: Either a VocabularyBuilder class or a string path to one
                   (e.g., "my_app.vocabularies.ScienceKeywords")
        minimum_input_length: Minimum characters before autocomplete triggers (default: 2)
        **kwargs: Standard ModelChoiceField arguments

    Example:
        from fairdm.contrib.autocomplete.fields import ConceptSelect
        from my_app.vocabularies import ScienceKeywords

        # Using a class
        field = ConceptSelect(vocabulary=ScienceKeywords)

        # Using a string with custom minimum input
        field = ConceptSelect(
            vocabulary="my_app.vocabularies.ScienceKeywords",
            minimum_input_length=3
        )
    """

    widget = autocomplete.ModelSelect2


class ConceptMultiSelect(ConceptMixin, forms.ModelMultipleChoiceField):
    """
    A ModelMultipleChoiceField for selecting multiple Concepts with autocomplete.

    This field automatically configures autocomplete for a specific vocabulary,
    handling both VocabularyBuilder classes and string paths.

    Args:
        vocabulary: Either a VocabularyBuilder class or a string path to one
                   (e.g., "my_app.vocabularies.ScienceKeywords")
        minimum_input_length: Minimum characters before autocomplete triggers (default: 2)
        **kwargs: Standard ModelMultipleChoiceField arguments

    Example:
        from fairdm.contrib.autocomplete.fields import ConceptMultiSelect
        from my_app.vocabularies import ScienceKeywords

        # Using a class
        field = ConceptMultiSelect(vocabulary=ScienceKeywords)

        # Using a string with custom minimum input
        field = ConceptMultiSelect(
            vocabulary="my_app.vocabularies.ScienceKeywords",
            minimum_input_length=3
        )
    """

    widget = autocomplete.ModelSelect2Multiple
