"""Polymorphic manager shared by the core record types."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from polymorphic import managers


class PolymorphicManager(managers.PolymorphicManager):
    """Polymorphic manager that can count records per child type."""

    def get_type_counts(self):
        """Count the records of each polymorphic child type.

        Returns:
            A dictionary mapping each child model class to the number of
            records of that type.
        """
        type_counts = (
            self.get_queryset()
            .values("polymorphic_ctype")
            .annotate(count=Count("id"))
            .order_by()
        )

        content_type_ids = [entry["polymorphic_ctype"] for entry in type_counts]
        content_types = ContentType.objects.filter(id__in=content_type_ids).in_bulk()
        content_type_map = {
            ct_id: content_types[ct_id].model_class() for ct_id in content_type_ids
        }

        return {
            content_type_map[entry["polymorphic_ctype"]]: entry["count"]
            for entry in type_counts
        }
