"""Filter sets for samples, including the reusable ``SampleFilterMixin``."""

import django_filters
from controlled_vocabularies.models import Record
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from mvp.filters import SearchFilter

from fairdm.contrib.autocomplete.fields import DatasetMultipleChoiceField
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter
from fairdm.core.measurement.filters import PartialDateFilter
from fairdm.core.sample.models import Sample
from fairdm.core.vocabularies import SAMPLE_STATUS


class SampleFilterMixin(django_filters.FilterSet):
    """Reusable base carrying the filters every sample type inherits.

    A ``FilterSet`` subclass rather than a plain mixin, because django-filter only collects
    declared filters from bases that carry ``declared_filters``. ``Meta`` deliberately has no
    ``model``, or the metaclass would generate a full, unused Sample filter set whenever this
    class or a subclass is defined. ``Meta.fields`` is a list a subclass's own ``Meta`` can extend.

    The dataset filter is a ``RecordMultipleFilter`` at public scope, so a visitor and a
    signed-in researcher are offered the same public datasets. Ticking several narrows the list
    to the samples of any of them.

    Args:
        *args: Positional arguments passed to ``FilterSet``.
        **kwargs: Keyword arguments passed to ``FilterSet``.

    Attributes:
        image: Filter to samples that do, or do not, carry an image.

    Example:
        ```python
        class MySampleFilter(SampleFilterMixin, django_filters.FilterSet):
            class Meta(SampleFilterMixin.Meta):
                model = MySample
                fields = SampleFilterMixin.Meta.fields + ["custom_field"]
        ```
    """

    image = django_filters.BooleanFilter(
        method="filter_has_image",
        label=_("Has image"),
    )

    def filter_has_image(self, queryset, name, value):
        """Narrow to samples that do, or do not, carry an image.

        Args:
            queryset: The queryset to filter.
            name: The filter name (unused).
            value: True for samples with an image, False for those without, ``None`` for all.

        Returns:
            The filtered queryset.
        """
        # An unset `FileField` is stored as "" even where NULL is allowed, so `isnull` alone
        # never matches it. Both count as "no image".
        if value is None:
            return queryset
        no_image = Q(image="") | Q(image__isnull=True)
        return queryset.exclude(no_image) if value else queryset.filter(no_image)

    class Meta:
        fields = ["status", "dataset", "polymorphic_ctype"]


class SampleFilter(SampleFilterMixin, django_filters.FilterSet):
    """Filter set for ``Sample``, with the filters inherited from ``SampleFilterMixin``.

    Args:
        *args: Positional arguments passed to ``FilterSet``.
        **kwargs: Keyword arguments passed to ``FilterSet``.

    Attributes:
        status: Filter by custody status.
        dataset: Filter by parent dataset.
        polymorphic_ctype: Filter by sample type.
        q: Search across name, local_id and uuid.
        description: Search in the description text.
        date_after: Filter to dates on or after a date.
        date_before: Filter to dates on or before a date.
    """

    # Chosen by the concept's slug, so the address of a filtered list stays readable.
    status = django_filters.ModelChoiceFilter(
        field_name="status",
        label=_("Status"),
        queryset=Record.objects.filter(
            scheme__uri=SAMPLE_STATUS, type=Record.Type.CONCEPT
        ).order_by("pref_label"),
        to_field_name="slug",
        empty_label=_("Any status"),
    )

    dataset = RecordMultipleFilter(DatasetMultipleChoiceField, field_name="dataset")

    polymorphic_ctype = django_filters.ModelChoiceFilter(
        field_name="polymorphic_ctype",
        label=_("Sample Type"),
        queryset=None,
        empty_label=_("Any type"),
    )

    q = SearchFilter(fields=["name", "local_id", "uuid"], label=_("Search"))

    description = django_filters.CharFilter(
        field_name="descriptions__value",
        lookup_expr="icontains",
        label=_("Description contains"),
    )

    date_after = PartialDateFilter(
        field_name="dates__value",
        lookup_expr="gte",
        label=_("Date after"),
    )

    date_before = PartialDateFilter(
        field_name="dates__value",
        lookup_expr="lte",
        label=_("Date before"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.contenttypes.models import ContentType

        self.filters["polymorphic_ctype"].queryset = ContentType.objects.filter(
            app_label__in=["fairdm_core", "demo"]
        )

    class Meta(SampleFilterMixin.Meta):
        model = Sample
        fields = [*SampleFilterMixin.Meta.fields, "date_after", "date_before"]
