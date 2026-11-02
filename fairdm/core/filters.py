"""Base filter set shared by the core list pages."""

import django_filters
from controlled_vocabularies.models import Record
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as df
from django_filters.fields import ModelChoiceField

from .forms import ConceptSelectField


class BaseListFilter(df.FilterSet):
    """Base filter set for the core list pages, adding a "has image" filter."""

    image = django_filters.BooleanFilter(
        field_name="image",
        lookup_expr="isnull",
        exclude=True,
        label=_("Has image"),
    )


class RecordTypeChoiceField(ModelChoiceField):
    """A choice of content type, each shown by its model's verbose name."""

    def label_from_instance(self, obj):
        """Return the model's verbose name, which a content type calls its ``name``."""
        return obj.name


class RecordTypeFilter(django_filters.ModelChoiceFilter):
    """Filter a polymorphic record by its concrete type, offered by verbose name."""

    field_class = RecordTypeChoiceField


class ConceptTypeFilter(django_filters.ModelChoiceFilter):
    """Filter by a typed row, offering the concepts its ``type`` field offers.

    The concepts are shown by name in the reading language, in their collection's
    order, and the address of a filtered list carries the concept's address.

    Args:
        *args: Passed to ``ModelChoiceFilter``.
        row_model: The row model, such as ``DatasetDate``, whose ``type`` field is
            offered.
        **kwargs: Passed to ``ModelChoiceFilter``.
    """

    field_class = ConceptSelectField

    def __init__(self, *args, row_model, **kwargs):
        def offered_concepts(request):
            uris = [concept.uri for concept in row_model.get_type_concepts()]
            return Record.objects.filter(uri__in=uris)

        kwargs.setdefault("empty_label", _("Any type"))
        super().__init__(
            *args,
            queryset=offered_concepts,
            to_field_name="uri",
            model_field=row_model._meta.get_field("type"),
            **kwargs,
        )
