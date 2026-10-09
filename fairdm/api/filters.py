"""FairDM API filter backends."""

from __future__ import annotations

import contextlib
import copy
from typing import TYPE_CHECKING, Any, cast

import django_filters
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model
from django.db.models.constants import LOOKUP_SEP
from django_filters.filters import QuerySetRequestMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import BaseFilterBackend

from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.models import Dataset, Sample
from fairdm.core.utils import get_objects_for_user

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


def _get_public_filter(model) -> dict:
    """Return a queryset filter dict that selects publicly-visible records.

    Project and Dataset carry an integer ``visibility`` field. Sample and Measurement have
    none: they are public when their dataset is public and published, as the portal has it.

    Args:
        model: The model class to build the filter for.

    Returns:
        A dict to pass to ``queryset.filter(**...)``, or an empty dict when the
        model has no known visibility field and filtering should be skipped.
    """
    from django.db.models import IntegerField

    with contextlib.suppress(Exception):
        field = model._meta.get_field("visibility")
        if isinstance(field, IntegerField):
            from fairdm.utils.choices import Visibility

            return {"visibility": Visibility.PUBLIC}

    with contextlib.suppress(Exception):
        model._meta.get_field("dataset")
        from fairdm.utils.choices import Visibility

        return {"dataset__visibility": Visibility.PUBLIC, "dataset__published": True}

    return {}


class FairDMVisibilityFilter(BaseFilterBackend):
    """Queryset-level visibility filter for FairDM API list endpoints.

    Restricts list querysets to objects the requesting user can see:

    - Projects and datasets with ``visibility=PUBLIC`` are always included. Samples and
      measurements are included when their dataset is public and published: a public dataset
      that is not published shows its own record and keeps its data back.
    - Records the user holds at least the view level on, directly or from the dataset or
      project above, are also included. Rows that django-guardian stores for a project, dataset,
      sample or measurement grant nothing.
    - For any other model, records where the user holds a stored guardian 'view' permission.

    Both sets are combined in one query to avoid N+1 queries.

    For models with no known visibility mechanism (such as Contributor), the
    filter returns the full queryset, making all records publicly accessible.
    Override ``filter_queryset()`` in a viewset subclass for stricter filtering.

    This replaces ``ObjectPermissionsFilter`` from ``djangorestframework-guardian``,
    which requires explicit guardian entries for *all* objects and so hides
    publicly-visible records that have no guardian permission rows.
    """

    def filter_queryset(self, request: Request, queryset, view: APIView):
        """Limit the queryset to public records plus those the user may view."""
        public_filter = _get_public_filter(queryset.model)

        if not public_filter:
            return queryset

        if request.user and request.user.is_authenticated:
            public_qs = queryset.filter(**public_filter)
            model = queryset.model
            core = getattr(model, "type_of", None) or model
            if RecordAccess.is_core_model(core):
                manager = getattr(core, "all_objects", core.objects)
                held = manager.accessible_to(request.user, ContributionLevel.VIEW)
                permitted_qs = queryset.filter(pk__in=held.values("pk"))
            else:
                view_perm = f"{model._meta.app_label}.view_{model._meta.model_name}"
                permitted_qs = get_objects_for_user(request.user, view_perm, queryset)
            return (public_qs | permitted_qs).distinct()

        return queryset.filter(**public_filter)


class DatasetFilterSet(django_filters.FilterSet):
    """Narrows a list to the records of one dataset, named by its short identifier.

    A database number names no dataset and is refused, as is an identifier of a dataset the
    caller may not see.
    """

    dataset = django_filters.ModelChoiceFilter(
        field_name="dataset",
        to_field_name="uuid",
        queryset=Dataset.all_objects.all(),
    )

    def __init__(self, *args, **kwargs):
        """Offer only the datasets the requesting user may see, and no content-type filter."""
        super().__init__(*args, **kwargs)
        self.filters["dataset"].queryset = self.visible(Dataset.all_objects.all())
        # A relation filter without an identifier takes a database number, which the API
        # does not accept. A type's own filter set may need it while it is built, so it
        # goes only now.
        for name, filter_ in list(self.filters.items()):
            if self.drops(filter_):
                del self.filters[name]

    @staticmethod
    def drops(filter_) -> bool:
        """Say whether the API removes a filter when it builds the filter set for a request.

        Args:
            filter_: A filter of the filter set.

        Returns:
            True for a relation filter that does not match on the short identifier.
        """
        return (
            isinstance(filter_, QuerySetRequestMixin)
            and filter_.extra.get("to_field_name") != "uuid"
        )

    def visible(self, queryset):
        """Limit a queryset of filter choices to what the requesting user may see.

        Args:
            queryset: The records the filter would otherwise offer.

        Returns:
            The records the list filter would let the requesting user see.
        """
        if hasattr(queryset, "non_polymorphic"):
            queryset = queryset.non_polymorphic()
        return FairDMVisibilityFilter().filter_queryset(self.request, queryset, None)

    @classmethod
    def match_relations_on_uuid(cls) -> None:
        """Make every relation filter of this class that can match on ``uuid`` do so.

        The filters are replaced by copies, so a filter set the portal's own pages share is
        left as it was. Call it on a class built for the API. A relation whose model has no
        ``uuid`` keeps its filter here and loses it when the filter set is built.
        """
        for name, filter_ in list(cls.base_filters.items()):
            if not isinstance(filter_, QuerySetRequestMixin):
                continue
            related = cls.related_model(filter_)
            if related is None or not any(
                field.name == "uuid" for field in related._meta.concrete_fields
            ):
                continue
            matching = copy.deepcopy(filter_)
            matching.extra["to_field_name"] = "uuid"
            if isinstance(matching, django_filters.ModelMultipleChoiceFilter):
                # It reads the chosen records' `uuid` but filters on `field_name` as given.
                matching.field_name += f"{LOOKUP_SEP}uuid"
            cls.base_filters[name] = matching

    @classmethod
    def related_model(cls, filter_) -> type[Model] | None:
        """Return the model a relation filter chooses among.

        Args:
            filter_: A relation filter of this class.

        Returns:
            The model at the end of the filter's field path, or ``None`` when the path does
            not end on a relation.
        """
        model: Any = cls._meta.model
        for segment in filter_.field_name.split(LOOKUP_SEP):
            try:
                field = model._meta.get_field(segment)
            except FieldDoesNotExist:
                return None
            model = field.related_model
            if model is None:
                return None
        return cast("type[Model]", model)


class SampleFilterSet(DatasetFilterSet):
    """Narrows a list to the records made on one sample, named by its short identifier."""

    sample = django_filters.ModelChoiceFilter(
        field_name="sample",
        to_field_name="uuid",
        queryset=Sample.objects.none(),
    )

    def __init__(self, *args, **kwargs):
        """Offer only the samples the requesting user may see."""
        super().__init__(*args, **kwargs)
        self.filters["sample"].queryset = self.visible(Sample.objects.all())


class FairDMFilterBackend(DjangoFilterBackend):
    """Django-filter backend that gives every list its dataset, and measurements their sample.

    The filters a registered type declares match related records by database number, and are
    shared with the portal's own pages. Here every relation filter matches by short identifier,
    a number is refused, and a filter on a relation with no identifier is left out.
    """

    parent_filtersets: dict[tuple, type] = {}

    def get_filterset_class(self, view, queryset=None):
        """Build the type's filter set with the parent filters added.

        Args:
            view: The view being filtered.
            queryset: The queryset being filtered.

        Returns:
            The filter set to use, or ``None`` when there is none.
        """
        filterset_class = super().get_filterset_class(view, queryset)
        parent_filterset = getattr(view, "parent_filterset", None)
        if parent_filterset is None:
            return filterset_class
        key = (filterset_class, parent_filterset)
        if key not in self.parent_filtersets:
            bases = (
                (parent_filterset, filterset_class)
                if filterset_class
                else (parent_filterset,)
            )
            attrs = {}
            if filterset_class is None:
                attrs["Meta"] = type(
                    "Meta", (), {"model": queryset.model, "fields": []}
                )
            name = f"{queryset.model.__name__}FilterSet"
            generated = type(name, bases, attrs)
            generated.match_relations_on_uuid()
            self.parent_filtersets[key] = generated
        return self.parent_filtersets[key]
