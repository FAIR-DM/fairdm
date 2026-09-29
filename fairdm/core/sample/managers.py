"""QuerySet for samples, with helpers that load related records and traverse sample hierarchies."""

from polymorphic.managers import PolymorphicQuerySet


class SampleQuerySet(PolymorphicQuerySet):
    """QuerySet for samples, whose methods chain with the standard queryset operations."""

    def published(self):
        """Return the samples whose own dataset is published.

        It is a bare filter with no ``select_related``, as it also builds filter choice lists.

        Returns:
            The samples in published datasets.
        """
        return self.filter(dataset__published=True)

    def visible_to(self, user):
        """Samples the user may see: those whose own dataset is public and published, and those
        in a dataset the user holds ``dataset.view_dataset`` or ``dataset.change_dataset`` on.

        Applied per record, against each record's own dataset. Being on one dataset's team never
        opens another dataset's records.
        """
        from django.db.models import Q

        from fairdm.core.dataset.models import Dataset
        from fairdm.core.utils import get_objects_for_user
        from fairdm.utils.choices import Visibility

        released = Q(dataset__visibility=Visibility.PUBLIC, dataset__published=True)
        if user is None or not user.is_authenticated:
            return self.filter(released)
        if user.has_perm("dataset.view_dataset") or user.has_perm("dataset.change_dataset"):
            return self
        team_datasets = get_objects_for_user(
            user,
            ["dataset.view_dataset", "dataset.change_dataset"],
            Dataset.all_objects.all(),
            any_perm=True,
            accept_global_perms=False,
        )
        return self.filter(released | Q(dataset__in=team_datasets))

    def with_related(self):
        """Load each sample's dataset, project and location, and prefetch its contributors and roles.

        Returns:
            The queryset with the related records loaded.

        Example:
            ```python
            samples = Sample.objects.with_related().filter(dataset=my_dataset)
            ```
        """
        return self.select_related(
            "dataset",
            "dataset__project",
            "location",
        ).prefetch_related(
            "contributors",
            "contributors__contributor",
            "contributors__roles",
        )

    def with_keywords(self):
        """Prefetch the controlled keywords (the ``keywords`` many-to-many).

        Split from :meth:`with_metadata` because the keywords are vocabulary concepts a sample is
        tagged with, not a per-sample record of its own.

        Returns:
            The queryset with the keywords prefetched.
        """
        return self.prefetch_related("keywords")

    def with_metadata(self):
        """Prefetch the descriptions, dates and identifiers.

        Returns:
            The queryset with the prefetches applied.
        """
        return self.prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
        )

    def by_relationship(self, related_to=None, relationship_type=None):
        """Filter samples by their relationship to another sample.

        With ``related_to``, returns the sources of relations targeting that sample, which are its
        children. Without it, returns every sample involved in a matching relation.

        Args:
            related_to: The sample whose children are wanted.
            relationship_type: Only consider relations of this type, such as ``"child_of"``.

        Returns:
            The samples matching the relationship criteria.
        """
        from .models import SampleRelation

        queryset = SampleRelation.objects.all()

        if relationship_type:
            queryset = queryset.filter(type=relationship_type)

        if related_to:
            queryset = queryset.filter(target=related_to)
            sample_ids = queryset.values_list("source_id", flat=True)
        else:
            relationship_ids = queryset.values_list("source_id", "target_id")
            sample_ids = set()
            for source_id, target_id in relationship_ids:
                sample_ids.add(source_id)
                sample_ids.add(target_id)

        return self.filter(id__in=sample_ids)

    def get_descendants(self, sample, max_depth=None):
        """Return the descendants of a sample in the hierarchy.

        The single traversal implementation for descendants, which ``Sample.get_descendants()``
        delegates to. A ``SampleRelation`` has ``source`` as the child and ``target`` as the
        parent, so the walk goes from each level's ``target`` to its ``source``. It is an iterative
        breadth-first search, which suits moderate depths.

        Args:
            sample: The sample to find descendants of.
            max_depth: The maximum depth to traverse. ``None`` is unlimited.

        Returns:
            A queryset of the descendant samples.
        """
        from .models import SampleRelation

        if max_depth is not None and max_depth <= 0:
            return self.none()

        descendant_ids = set()
        visited = {sample.id}
        current_level = {sample.id}
        depth = 0

        while current_level:
            if max_depth is not None and depth >= max_depth:
                break

            next_level = set(
                SampleRelation.objects.filter(
                    target_id__in=current_level, type="child_of"
                ).values_list("source_id", flat=True)
            )

            next_level = next_level - visited

            if not next_level:
                break

            descendant_ids.update(next_level)
            visited.update(next_level)
            current_level = next_level
            depth += 1

        if not descendant_ids:
            return self.none()

        return self.filter(id__in=descendant_ids)

    def get_ancestors(self, sample, max_depth=None):
        """Return the ancestors of a sample in the hierarchy.

        The single traversal implementation for ancestors, which ``Sample.get_ancestors()``
        delegates to. It walks the reverse direction of ``get_descendants()``, from each level's
        ``source`` to its ``target``, as an iterative breadth-first search.

        Args:
            sample: The sample to find ancestors of.
            max_depth: The maximum depth to traverse. ``None`` is unlimited.

        Returns:
            A queryset of the ancestor samples.
        """
        from .models import SampleRelation

        if max_depth is not None and max_depth <= 0:
            return self.none()

        ancestor_ids = set()
        visited = {sample.id}
        current_level = {sample.id}
        depth = 0

        while current_level:
            if max_depth is not None and depth >= max_depth:
                break

            next_level = set(
                SampleRelation.objects.filter(
                    source_id__in=current_level, type="child_of"
                ).values_list("target_id", flat=True)
            )

            next_level = next_level - visited

            if not next_level:
                break

            ancestor_ids.update(next_level)
            visited.update(next_level)
            current_level = next_level
            depth += 1

        if not ancestor_ids:
            return self.none()

        return self.filter(id__in=ancestor_ids)
