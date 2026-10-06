"""What a person may do on one project, dataset, sample or measurement, read from contribution levels."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.functional import cached_property

from .choices import ContributionLevel
from .models import Contribution, Person

_CORE_MODELS = ("project", "dataset", "sample", "measurement")

#: The level a person needs for each permission a core record type declares.
REQUIRED_LEVEL = {
    **{f"view_{model}": ContributionLevel.VIEW for model in _CORE_MODELS},
    **{
        f"{action}_{model}": ContributionLevel.EDIT
        for model in _CORE_MODELS
        for action in ("add", "change")
    },
    "import_data": ContributionLevel.EDIT,
    "modify_metadata": ContributionLevel.EDIT,
    "change_project_metadata": ContributionLevel.EDIT,
    "change_dataset_metadata": ContributionLevel.EDIT,
    **{f"delete_{model}": ContributionLevel.MANAGE for model in _CORE_MODELS},
    "add_contributor": ContributionLevel.MANAGE,
    "modify_contributor": ContributionLevel.MANAGE,
    "change_project_settings": ContributionLevel.MANAGE,
    "change_dataset_settings": ContributionLevel.MANAGE,
    "can_publish": ContributionLevel.MANAGE,
}


class RecordAccess:
    """Answer what people may do on one record from the levels on its contributions.

    A level is held on the record or on a record above it: a sample or measurement takes its
    dataset's levels and the dataset's project's, a dataset takes its project's. Contributions of
    an organization hold no level.

    Args:
        record: A project, dataset, sample or measurement, of any registered type.
    """

    def __init__(self, record):
        self.record = record

    @property
    def model(self):
        """The core model the record belongs to, whatever registered type it is."""
        return getattr(self.record, "type_of", None) or type(self.record)

    @cached_property
    def above(self):
        """The records this one takes levels from, nearest first.

        A measurement follows its own dataset, not its sample's.
        """
        found = []
        parent = getattr(self.record, "dataset", None) or getattr(
            self.record, "project", None
        )
        while parent is not None:
            found.append(parent)
            parent = getattr(parent, "project", None)
        return found

    @staticmethod
    def key(record):
        """Return the pair that names a record on a contribution.

        Args:
            record: A project, dataset, sample or measurement.

        Returns:
            The content type id and the object id, as stored on a contribution.
        """
        if hasattr(record, "get_real_instance"):
            record = record.get_real_instance()
        return ContentType.objects.get_for_model(record).pk, str(record.pk)

    def on_chain(self, *, include_record):
        """Narrow contributions to those on the record and the records above, or only above.

        Args:
            include_record: Whether the record itself is part of the chain.

        Returns:
            The contributions with a level, and the record each key stands for.
        """
        records = [self.record, *self.above] if include_record else self.above
        keys = {self.key(record): record for record in records}
        wanted = Q(pk__in=[])
        for content_type_id, object_id in keys:
            wanted |= Q(content_type_id=content_type_id, object_id=object_id)
        return Contribution.objects.filter(wanted, level__isnull=False), keys

    def levels_held(self, person_id):
        """Return each level a person holds on the record or above it, with where it is held.

        Args:
            person_id: The id of the person.

        Returns:
            ``(record, level)`` pairs, in one query.
        """
        held, keys = self.on_chain(include_record=True)
        rows = held.filter(contributor_id=person_id).values_list(
            "content_type_id", "object_id", "level"
        )
        return [
            (keys[(content_type_id, object_id)], ContributionLevel(level))
            for content_type_id, object_id, level in rows
        ]

    def level_of(self, user):
        """Return the highest level a user holds on the record or any record above it.

        Args:
            user: The user, or an anonymous user for a visitor.

        Returns:
            The level, or None for a visitor, an inactive user or someone who holds none.
        """
        if not (user.is_authenticated and user.is_active):
            return None
        return max((level for _, level in self.levels_held(user.pk)), default=None)

    def own_level(self, person):
        """Return the level a person holds from being listed on the record itself.

        Args:
            person: The person.

        Returns:
            The level, or None.
        """
        for record, level in self.levels_held(person.pk):
            if record is self.record:
                return level
        return None

    def level_from_above(self, person):
        """Return the highest level a person holds from a record above, and that record.

        Args:
            person: The person.

        Returns:
            ``(level, record)``, or ``(None, None)``.
        """
        best, source = None, None
        for record, level in self.levels_held(person.pk):
            if record is not self.record and (best is None or level > best):
                best, source = level, record
        return best, source

    def people_above(self):
        """Return everyone who holds a level from a record above, at the highest they hold.

        Returns:
            ``(person, level, source record)`` for each person, by name.
        """
        held, keys = self.on_chain(include_record=False)
        best = {}
        for contributor_id, content_type_id, object_id, level in held.values_list(
            "contributor_id", "content_type_id", "object_id", "level"
        ):
            if contributor_id not in best or level > best[contributor_id][0]:
                best[contributor_id] = (level, keys[(content_type_id, object_id)])
        people = Person.objects.in_bulk(best)
        found = [
            (people[pk], ContributionLevel(level), source)
            for pk, (level, source) in best.items()
        ]
        return sorted(found, key=lambda entry: str(entry[0]))

    def managers(self):
        """Return the ids of the people who count as able to manage the record.

        A person counts when they can sign in and hold the manage level on the record or on a
        record above it. Holders of portal roles do not count.

        Returns:
            A set of person ids.
        """
        held, _keys = self.on_chain(include_record=True)
        ids = held.filter(level=ContributionLevel.MANAGE).values_list(
            "contributor_id", flat=True
        )
        return {
            person.pk
            for person in Person.objects.filter(pk__in=list(ids))
            if person.can_sign_in()
        }

    def can_manage(self, user):
        """Say whether a user may change the record's contributors.

        Args:
            user: The user, or an anonymous user for a visitor.

        Returns:
            True for the manage level on the record or above it, and for anyone holding
            ``change_<model>`` for the whole portal, which a superuser and a Data Curator do.
        """
        if not (user.is_authenticated and user.is_active):
            return False
        if self.level_of(user) == ContributionLevel.MANAGE:
            return True
        meta = self.model._meta
        return user.has_perm(f"{meta.app_label}.change_{meta.model_name}")
