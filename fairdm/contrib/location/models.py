"""The abstract model that gives a record a location of its own."""

from django.contrib.gis.db.models import PointField
from django.contrib.postgres.indexes import GistIndex
from django.db.models import Q
from django.db.models.functions import Cast
from django.utils.translation import gettext_lazy as _

from fairdm.db import models


class LocatedRecord(models.Model):
    """A record that says where it is: a WGS 84 point, an elevation and an uncertainty.

    The three values belong to the one record that holds them. No row is shared between records.
    The database refuses an elevation or an uncertainty without a point, and a negative
    uncertainty.

    Attributes:
        location: The point, in WGS 84.
        location_elevation: Metres above mean sea level, negative below it.
        location_uncertainty: Metres from the point within which the true place lies.
    """

    location = PointField(
        srid=4326,
        verbose_name=_("location"),
        help_text=_("Where the record is, as a point in WGS 84."),
        null=True,
        blank=True,
    )
    location_elevation = models.FloatField(
        verbose_name=_("elevation"),
        help_text=_(
            "Metres above mean sea level, and a negative number below it. Needs a location."
        ),
        null=True,
        blank=True,
    )
    location_uncertainty = models.FloatField(
        verbose_name=_("uncertainty"),
        help_text=_(
            "The distance in metres from the location within which the true place lies. "
            "Needs a location."
        ),
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


def location_constraints():
    """Return the check constraints that keep a record's three location fields consistent.

    An uncertainty is null or zero or more, and an elevation or an uncertainty needs a point.
    A concrete model lists these in its own ``Meta.constraints``. They are not declared on
    ``LocatedRecord.Meta``, because a type that subclasses ``Sample`` without a ``Meta`` of its
    own would inherit them onto a table that has none of the columns.

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
