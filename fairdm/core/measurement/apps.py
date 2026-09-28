"""App configuration for the measurement app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

#: Mirrors the message `Measurement.clean()` raises.
BASE_MEASUREMENT_ERROR = _(
    "Cannot create base Measurement instances directly. Please use a specific "
    "measurement type subclass."
)


def block_base_measurement_creation(sender, instance, **kwargs):
    """Refuse to save a bare ``Measurement`` row, by any route.

    ``Measurement.objects.create()`` and a bare ``Measurement().save()`` reach the database
    without calling ``clean()``. This is connected with ``sender=Measurement`` because a subclass
    instance sends its own class on save, so it never fires for a registered measurement type.
    ``pre_save`` also covers fixture loading.

    Args:
        sender: The model class being saved.
        instance: The instance being saved.
        **kwargs: Additional signal arguments.

    Raises:
        ValidationError: Always, since a bare ``Measurement`` cannot be saved.
    """
    from django.core.exceptions import ValidationError

    raise ValidationError(BASE_MEASUREMENT_ERROR)


class FairDMMeasurementConfig(AppConfig):
    """Configuration for the ``fairdm.core.measurement`` app."""

    name = "fairdm.core.measurement"
    label = "measurement"
    verbose_name = _("Measurement")
    verbose_name_plural = _("Measurements")

    def ready(self):
        """Connect the guard that blocks saving a bare ``Measurement``."""
        from django.db.models.signals import pre_save

        from .models import Measurement

        pre_save.connect(block_base_measurement_creation, sender=Measurement)
