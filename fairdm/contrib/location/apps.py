from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LocationConfig(AppConfig):
    name = "fairdm.contrib.location"
    label = "fairdm_location"
    verbose_name = _("Location")

    def ready(self):
        from actstream import registry

        registry.register(self.get_model("Point"))

        return super().ready()
