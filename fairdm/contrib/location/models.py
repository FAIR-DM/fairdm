"""Model for a location given by its coordinates."""

from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.translation import gettext as _

from fairdm.core.models import Measurement
from fairdm.db import models

X_OPTS = settings.FAIRDM_X_COORD
Y_OPTS = settings.FAIRDM_Y_COORD


X_MAX_DIGITS = X_OPTS.get("max_digits") or X_OPTS["decimal_places"] + 3

Y_MAX_DIGITS = Y_OPTS.get("max_digits") or Y_OPTS["decimal_places"] + 2


class Point(models.Model):
    """A location given by its x and y coordinates and their coordinate reference system.

    Attributes:
        x: The x-coordinate (longitude).
        y: The y-coordinate (latitude).
        crs: The coordinate reference system, set from the ``FAIRDM_CRS`` setting.
    """

    x = models.DecimalField(
        verbose_name=_("x"),
        help_text=_("The x-coordinate of the location."),
        max_digits=X_MAX_DIGITS,
        decimal_places=X_OPTS["decimal_places"],
    )
    y = models.DecimalField(
        verbose_name=_("y"),
        help_text=_("The y-coordinate of the location."),
        max_digits=Y_MAX_DIGITS,
        decimal_places=Y_OPTS["decimal_places"],
    )
    crs = models.CharField(
        verbose_name=_("CRS"),
        help_text=_("The coordinate reference system."),
        max_length=255,
        default=settings.FAIRDM_CRS,
        editable=False,
    )

    class Meta:
        verbose_name = _("location")
        verbose_name_plural = _("locations")
        unique_together = ("x", "y")

    def __str__(self):
        """Return the latitude and longitude."""
        return f"{self.latitude}, {self.longitude}"

    def point2d(self):
        """Return the location as a GeoJSON ``Point`` dict.

        Returns:
            A dict with the ``Point`` type and the ``[x, y]`` coordinates.
        """
        return {"type": "Point", "coordinates": [self.x, self.y]}

    @property
    @admin.display(description=_("latitude"))
    def latitude(self):
        """Return the latitude, which is the y-coordinate."""
        return self.y

    @latitude.setter
    def latitude(self, val):
        self.y = val

    @property
    @admin.display(description=_("longitude"))
    def longitude(self):
        """Return the longitude, which is the x-coordinate."""
        return self.x

    @longitude.setter
    def longitude(self, val):
        self.x = val

    def measurements(self):
        """Return the measurements of samples at this location.

        Returns:
            A queryset of measurements.
        """
        return Measurement.objects.filter(sample__location=self)

    def get_absolute_url(self):
        """Return the URL of the location's detail page."""
        return reverse(
            "point-detail", kwargs={"lon": self.longitude, "lat": self.latitude}
        )
