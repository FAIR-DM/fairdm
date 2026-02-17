"""
Activity Stream Plugins

Provides plugin classes for displaying activity streams in FairDM.
"""

from actstream.models import Action
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample


class ActivityPlugin(Plugin, TemplateView):
    """
    Plugin for displaying recent activity on an object.

    Shows activities where the object is either the target or action_object,
    displaying up to 20 most recent activities.
    """

    title = _("Recent Activity")
    menu = {"label": _("Activity"), "icon": "activity", "order": 300}
    template_name = "activity_stream/activity_stream.html"

    def get_context_data(self, **kwargs):
        """Add activity stream data to the context."""

        context = super().get_context_data(**kwargs)

        # Get content type for the base object
        content_type = ContentType.objects.get_for_model(self.object)

        # Get all actions where base_object is the target or action_object
        activities = Action.objects.filter(
            target_object_id=self.object.pk,
            target_content_type=content_type,
        ) | Action.objects.filter(
            action_object_object_id=self.object.pk,
            action_object_content_type=content_type,
        )

        # Order by most recent first and prefetch related objects
        activities = (
            activities.select_related(
                "actor_content_type",
                "target_content_type",
                "action_object_content_type",
            )
            .prefetch_related("actor", "target", "action_object")
            .order_by("-timestamp")[:20]
        )

        context["activities"] = activities
        return context


# ============================================================================
# Plugin Registrations
# ============================================================================


@plugins.register(Project)
class ProjectActivity(ActivityPlugin):
    """Plugin for displaying recent activity on a project."""

    pass


@plugins.register(Dataset)
class DatasetActivity(ActivityPlugin):
    """Plugin for displaying recent activity on a dataset."""

    pass


@plugins.register(Sample)
class SampleActivity(ActivityPlugin):
    """Plugin for displaying recent activity on a sample."""

    pass


@plugins.register(Measurement)
class MeasurementActivity(ActivityPlugin):
    """Plugin for displaying recent activity on a measurement."""

    pass
