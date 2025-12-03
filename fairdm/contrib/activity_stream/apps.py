from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ActivityStreamConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fairdm.contrib.activity_stream"
    verbose_name = _("Activity Stream")
    label = "fairdm_activity_stream"

    def ready(self):
        """Register models with actstream when app is ready."""
        # Import here to avoid circular imports
        from actstream import registry

        from fairdm.core.models import Dataset, Measurement, Project, Sample

        registry.register(Project)
        registry.register(Dataset)
        registry.register(Sample)
        registry.register(Measurement)
