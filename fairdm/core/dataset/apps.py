from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FairDMDatasetConfig(AppConfig):
    name = "fairdm.core.dataset"
    label = "dataset"
    verbose_name = _("Dataset")
    verbose_name_plural = _("Dataset")

    def ready(self) -> None:
        # Register models for actstream
        from actstream import registry

        registry.register(self.get_model("Dataset"))
        return super().ready()
