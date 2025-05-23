from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FairDMMeasurementConfig(AppConfig):
    name = "fairdm.core.measurement"
    label = "measurement"
    verbose_name = _("Measurement")
    verbose_name_plural = _("Measurements")

    def ready(self) -> None:
        return super().ready()
