"""Polymorphic manager and the record-visibility queryset mixin shared by the core record types."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import CharField, Count, Exists, OuterRef, Q
from django.db.models.functions import Cast
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


class RecordLevelMixin:
    """The ``with_level`` queryset method, shared by projects, datasets, samples and measurements.

    A record is held on its own contributions and on those of the records above it: a dataset on
    its project, a sample or measurement on its dataset and that dataset's project. A measurement
    follows its own dataset, not its sample's.
    """

    def with_level(self, user, level):
        """Return the records the user holds at least a level on.

        Args:
            user: The user, or ``None`` or an anonymous user for a visitor.
            level: The least level wanted, a ``ContributionLevel``.

        Returns:
            The records the user holds the level on, on the record itself or from a record above.
            None for a visitor or an inactive user.
        """
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import Project

        if user is None or not (user.is_authenticated and user.is_active):
            return self.none()
        held = Contribution.objects.filter(contributor_id=user.pk, level__gte=level)

        def holds(content_type, key):
            return Exists(
                held.filter(
                    content_type=content_type,
                    object_id=Cast(OuterRef(key), CharField()),
                )
            )

        project_type = ContentType.objects.get_for_model(Project)
        dataset_type = ContentType.objects.get_for_model(Dataset)
        if hasattr(self.model, "polymorphic_ctype"):
            own = holds(OuterRef("polymorphic_ctype_id"), "pk")
        elif self.model._meta.model_name == "dataset":
            own = holds(dataset_type, "pk")
        else:
            own = holds(project_type, "pk")
        if self.model._meta.model_name == "project":
            return self.filter(own)
        if self.model._meta.model_name == "dataset":
            return self.filter(own | holds(project_type, "project_id"))
        return self.filter(
            own
            | holds(dataset_type, "dataset_id")
            | holds(project_type, "dataset__project_id")
        )

    def accessible_to(self, user, level):
        """Return the records the user holds a level on, and every record for a portal-wide right.

        Choice lists and filters offer the same records the permission backends would let the
        user act on: those the user holds the level on, and all of them for someone the portal
        gives ``view`` (for the view level) or ``change`` (for edit and manage) on the whole
        model, as a superuser or a Data Curator has.

        Args:
            user: The user, or ``None`` or an anonymous user for a visitor.
            level: The least level wanted, a ``ContributionLevel``.

        Returns:
            The records the user may act on at that level.
        """
        from fairdm.contrib.contributors.choices import ContributionLevel

        if user is None or not (user.is_authenticated and user.is_active):
            return self.none()
        meta = self.model._meta
        action = "view" if level == ContributionLevel.VIEW else "change"
        if user.has_perm(f"{meta.app_label}.{action}_{meta.model_name}"):
            return self.all()
        return self.with_level(user, level)


class RecordVisibilityMixin(RecordLevelMixin):
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

        Those whose own dataset is public and published, and those the user holds a level on, on
        the record itself or from its dataset or that dataset's project. Someone listed only on
        one record sees that record and not its siblings. A user who holds ``view_dataset`` or
        ``change_dataset`` for the whole portal sees every record.

        Args:
            user: The user, or ``None`` for a visitor.

        Returns:
            The records the user may see.
        """
        from fairdm.contrib.contributors.choices import ContributionLevel
        from fairdm.utils.choices import Visibility

        released = Q(dataset__visibility=Visibility.PUBLIC, dataset__published=True)
        if user is None or not user.is_authenticated:
            return self.filter(released)
        if user.has_perm("dataset.view_dataset") or user.has_perm(
            "dataset.change_dataset"
        ):
            return self
        held = self.with_level(user, ContributionLevel.VIEW).values("pk")
        return self.filter(released | Q(pk__in=held))
