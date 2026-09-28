"""DRF serializer for projects."""

from rest_framework.fields import Field as Field
from rest_framework.serializers import HyperlinkedIdentityField, ModelSerializer

from ..models import Project


class ProjectSerializer(ModelSerializer):
    """Serialize a project for the REST API, with expandable related datasets.

    The ``visibility`` and ``options`` fields are excluded from the output.
    """

    web = HyperlinkedIdentityField(view_name="project:overview", lookup_field="uuid")

    class Meta:
        model = Project
        exclude = ["visibility", "options"]
        expandable_fields = {
            "datasets": (
                "fairdm.contrib.api.serializers.DatasetSerializer",
                {"many": True},
            )
        }
