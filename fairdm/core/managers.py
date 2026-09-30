"""Polymorphic manager and the record-visibility queryset mixin shared by the core record types."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
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


class RecordVisibilityMixin:
    """QuerySet methods for records that follow their own dataset: samples and measurements.

    Both rules are applied per record, against the record's own dataset. Being on one dataset's
    team never opens another dataset's records. The queryset it is mixed into must have a
    ``dataset`` foreign key.
    """

    def published(self):
        """Return the records whose own dataset is published.

        It is a bare filter with no ``select_related``, as it also builds filter choice lists.
        Deliberately ``dataset__published``: a record's presence is decided by the dataset that
        owns it, not by the dataset that owns a record it hangs from.

        Returns:
            The records in published datasets.
        """
        return self.filter(dataset__published=True)

    def visible_to(self, user):
        """Return the records the user may see.

        Those whose own dataset is public and published, and those in a dataset the user holds
        ``dataset.view_dataset`` or ``dataset.change_dataset`` on.

        Args:
            user: The user, or ``None`` for a visitor.

        Returns:
            The records the user may see.
        """
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.utils import get_objects_for_user
        from fairdm.utils.choices import Visibility

        released = Q(dataset__visibility=Visibility.PUBLIC, dataset__published=True)
        if user is None or not user.is_authenticated:
            return self.filter(released)
        if user.has_perm("dataset.view_dataset") or user.has_perm(
            "dataset.change_dataset"
        ):
            return self
        team_datasets = get_objects_for_user(
            user,
            ["dataset.view_dataset", "dataset.change_dataset"],
            Dataset.all_objects.all(),
            any_perm=True,
            accept_global_perms=False,
        )
        return self.filter(released | Q(dataset__in=team_datasets))
