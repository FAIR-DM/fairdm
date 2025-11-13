from rest_framework.fields import Field as Field
from rest_framework.serializers import HyperlinkedIdentityField, ModelSerializer

from ..models import Project


class ProjectSerializer(ModelSerializer):
    """DRF serializer for Project model.

    Provides REST API representation of Project instances with expandable
    fields for related datasets. Excludes internal fields like visibility
    and options from API responses.
    """

    web = HyperlinkedIdentityField(view_name="project-detail")
    # dates = DateSerializer(many=True)

    class Meta:
        model = Project
        exclude = ["visibility", "options"]
        expandable_fields = {
            "datasets": (
                "fairdm.contrib.api.serializers.DatasetSerializer",
                {"many": True},
            )
        }
