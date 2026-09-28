"""Form fields for autocomplete functionality."""

from typing import Any, ClassVar

from dal import autocomplete, forward
from django import forms
from django.urls import reverse
from django.utils.module_loading import import_string
from research_vocabs.models import Concept


class ConceptMixin:
    """Configure a model choice field to autocomplete the concepts of one vocabulary.

    Args:
        vocabulary: A vocabulary builder class or the dotted path to one.
        minimum_input_length: Characters typed before the autocomplete queries.
        **kwargs: Passed to the model choice field. ``queryset``, ``widget`` and
            ``label`` are filled in from the vocabulary when not given.

    Attributes:
        widget: The autocomplete widget class used when the caller passes none.
    """

    widget: ClassVar[type[Any]]

    def __init__(self, vocabulary, minimum_input_length=2, **kwargs):
        if isinstance(vocabulary, str):
            vocabulary = import_string(vocabulary)

        vocab_name = vocabulary._meta.name

        if "queryset" not in kwargs:
            kwargs["queryset"] = Concept.objects.filter(vocabulary__name=vocab_name)

        if "widget" not in kwargs:
            kwargs["widget"] = self.widget(
                url=reverse("autocomplete:concept"),
                forward=(forward.Const(vocab_name, "vocabulary"),),
                attrs={
                    "data-placeholder": f"Select {vocabulary.__name__}...",
                    "data-minimum-input-length": minimum_input_length,
                },
            )

        if "label" not in kwargs:
            kwargs["label"] = vocabulary.__name__

        super().__init__(**kwargs)


class ConceptSelect(ConceptMixin, forms.ModelChoiceField):
    """Select a single Concept with autocomplete.

    The field configures autocomplete for one vocabulary, given as a
    VocabularyBuilder class or a string path.

    Args:
        vocabulary: Either a VocabularyBuilder class or a string path to one
                   (e.g., "my_app.vocabularies.ScienceKeywords")
        minimum_input_length: Minimum characters before autocomplete triggers (default: 2)
        **kwargs: Standard ModelChoiceField arguments

    Attributes:
        widget: The autocomplete widget class used when the caller passes none.

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
    """Select multiple Concepts with autocomplete.

    The field configures autocomplete for one vocabulary, given as a
    VocabularyBuilder class or a string path.

    Args:
        vocabulary: Either a VocabularyBuilder class or a string path to one
                   (e.g., "my_app.vocabularies.ScienceKeywords")
        minimum_input_length: Minimum characters before autocomplete triggers (default: 2)
        **kwargs: Standard ModelMultipleChoiceField arguments

    Attributes:
        widget: The autocomplete widget class used when the caller passes none.

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
