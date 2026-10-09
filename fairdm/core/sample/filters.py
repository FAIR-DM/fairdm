"""Filter sets for samples, including the reusable ``SampleFilterMixin``."""

import django_filters
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from fairdm.core.measurement.filters import PartialDateFilter
from fairdm.core.sample.models import Sample
from fairdm.core.vocabularies import FairDMSampleStatus


class SampleFilterMixin(django_filters.FilterSet):
    """Reusable base carrying the filters every sample type inherits.

    A ``FilterSet`` subclass rather than a plain mixin, because django-filter only collects
    declared filters from bases that carry ``declared_filters``. ``Meta`` deliberately has no
    ``model``, or the metaclass would generate a full, unused Sample filter set whenever this
    class or a subclass is defined. ``Meta.fields`` is a list a subclass's own ``Meta`` can extend.

    The dataset choices come from ``Dataset.all_objects``. The default manager is privacy-first
    and would reject every private dataset, which is every dataset until someone publishes it.

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from fairdm.core.models import Dataset

        if "dataset" in self.filters:
            self.filters["dataset"].queryset = Dataset.all_objects.all()

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
        search: Search across name, local_id and uuid.
        description: Search in the description text.
        date_after: Filter to dates on or after a date.
        date_before: Filter to dates on or before a date.
    """

    # `status` is a `ConceptField` storing the concept's name as a string, so a
    # `ModelChoiceFilter` never matches.
    status = django_filters.ChoiceFilter(
        field_name="status",
        label=_("Status"),
        choices=FairDMSampleStatus().choices,
        empty_label=_("Any status"),
    )

    dataset = django_filters.ModelChoiceFilter(
        field_name="dataset",
        label=_("Dataset"),
        queryset=None,
        empty_label=_("Any dataset"),
    )

    polymorphic_ctype = django_filters.ModelChoiceFilter(
        field_name="polymorphic_ctype",
        label=_("Sample Type"),
        queryset=None,
        empty_label=_("Any type"),
    )

    search = django_filters.CharFilter(
        method="filter_search",
        label=_("Search"),
    )

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

    def filter_search(self, queryset, name, value):
        """Filter by a search term matching the name, local_id or uuid.

        Args:
            queryset: The queryset to filter.
            name: The filter name (unused).
            value: The search term.

        Returns:
            The queryset matching the term, unchanged when there is none.
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value)
            | Q(local_id__icontains=value)
            | Q(uuid__icontains=value)
        )

    class Meta(SampleFilterMixin.Meta):
        model = Sample
        fields = [*SampleFilterMixin.Meta.fields, "date_after", "date_before"]
