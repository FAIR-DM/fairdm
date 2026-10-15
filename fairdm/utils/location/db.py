"""The constraints and index a model with a ``location`` lists in its own ``Meta``."""

from django.contrib.gis.db.models import PointField
from django.contrib.postgres.indexes import GistIndex
from django.db.models import Q
from django.db.models.functions import Cast

from fairdm.db import models


def location_constraints():
    """Return the check constraints that keep a record's three location fields consistent.

    An uncertainty is null or zero or more, and an elevation or an uncertainty needs a point.
    A concrete model lists these in its own ``Meta.constraints``, because a type that subclasses
    ``Sample`` without a ``Meta`` of its own would otherwise inherit them onto a table that has
    none of the columns.

    Returns:
        A list of two check constraints, named from the app label and class name of the model
        that lists them.
    """
    return [
        models.CheckConstraint(
            condition=Q(location_uncertainty__isnull=True)
            | Q(location_uncertainty__gte=0),
            name="%(app_label)s_%(class)s_uncertainty_not_negative",
        ),
        models.CheckConstraint(
            condition=Q(location__isnull=False)
            | (
                Q(location_elevation__isnull=True)
                & Q(location_uncertainty__isnull=True)
            ),
            name="%(app_label)s_%(class)s_extras_need_location",
        ),
    ]


def geography_index(name):
    """Return the index that distance lookups on a ``location`` read.

    The expression has to match the one the lookups cast to, or PostgreSQL will not use it. A
    model that declares its own ``Meta.indexes`` lists this index there, because a ``Meta`` that
    sets ``indexes`` replaces an inherited list.

    Args:
        name: The index name, 30 characters or fewer.

    Returns:
        A GiST index on the location as a geography.
    """
    return GistIndex(Cast("location", PointField(geography=True)), name=name)
