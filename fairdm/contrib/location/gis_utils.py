"""Ordering filter for distance queries that requires the optional ``gis`` extra."""

from django.core.exceptions import ImproperlyConfigured

try:
    from rest_framework_gis import filters
except ModuleNotFoundError as exc:
    raise ImproperlyConfigured(
        "fairdm.contrib.location.gis_utils requires djangorestframework-gis, "
        "which is not installed. Install the 'gis' extra: pip install fairdm[gis]"
    ) from exc


class DistanceToPointOrderingFilter(filters.DistanceToPointOrderingFilter):
    """Distance-to-point ordering filter that documents its ordering parameter in the API schema."""

    def get_schema_operation_parameters(self, view):
        """Add the ``asc``/``desc`` ordering parameter to the schema."""
        params = super().get_schema_operation_parameters(view)
        params.append(
            {
                "name": self.order_param,
                "required": False,
                "in": "query",
                "description": "",
                "schema": {
                    "type": "enum",
                    "items": {"type": "string", "enum": ["asc", "desc"]},
                    "example": "desc",
                },
                "style": "form",
                "explode": False,
            }
        )
        return params
