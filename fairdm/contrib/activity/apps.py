"""App configuration for activity."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ActivityConfig(AppConfig):
    """Configuration for the activity app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "fairdm.contrib.activity"
    label = "activity"
    verbose_name = _("Activity")

    def ready(self):
        """Register the recorded models and connect the receivers."""
        from actstream import registry

        from fairdm.contrib.contributors.models import Contributor, Organization, Person
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import Project

        from . import plugins, receivers  # noqa: F401

        for model in (Project, Dataset, Contributor, Person, Organization):
            registry.register(model)
        receivers.connect()
