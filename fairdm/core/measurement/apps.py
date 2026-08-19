from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

#: Mirrors the message `Measurement.clean()` raises (models.py:114). Declared here
#: rather than imported from there because this module is what connects the
#: `pre_save` guard below - `fairdm/core/measurement/models.py` is owned by a
#: concurrently running story for this feature and out of this story's scope.
BASE_MEASUREMENT_ERROR = _(
    "Cannot create base Measurement instances directly. Please use a specific "
    "measurement type subclass."
)


def block_base_measurement_creation(sender, instance, **kwargs):
    """Refuse to save a bare ``Measurement`` row, by any route.

    T028: `Measurement.objects.create()` and a bare `Measurement().save()` reach the
    database without ever calling `clean()`/`full_clean()`, so the record's own
    validation (models.py:111) never runs for them. Connected below with
    `sender=Measurement` rather than without a sender: a subclass instance sends its
    own class on save, never `Measurement`, so this never fires for a registered
    measurement type. `pre_save` is also the one mechanism that covers fixture
    loading - `django.core.serializers` sends `pre_save` on every deserialized
    object before it saves.
    """
    from django.core.exceptions import ValidationError

    raise ValidationError(BASE_MEASUREMENT_ERROR)


class FairDMMeasurementConfig(AppConfig):
    name = "fairdm.core.measurement"
    label = "measurement"
    verbose_name = _("Measurement")
    verbose_name_plural = _("Measurements")

    def ready(self):
        from django.db.models.signals import pre_save

        from .models import Measurement

        pre_save.connect(block_base_measurement_creation, sender=Measurement)
