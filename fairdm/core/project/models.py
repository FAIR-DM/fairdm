from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError

# from django.db.models import QuerySet
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from partial_date import PartialDate
from shortuuid.django_fields import ShortUUIDField

from fairdm.db import models
from fairdm.db.models import QuerySet
from fairdm.utils.choices import Visibility

from ..abstract import AbstractDate, AbstractDescription, AbstractIdentifier, BaseModel
from ..choices import ProjectStatus
from ..utils import CORE_PERMISSIONS
from ..vocabularies import (
    FairDMDates,
    FairDMDescriptions,
    FairDMIdentifiers,
    FairDMRoles,
)
from .validators import validate_funding


class ProjectQuerySet(QuerySet):
    """Custom QuerySet for Project model with optimized query methods."""

    def get_visible(self) -> "ProjectQuerySet":
        """Return only projects with public visibility."""
        return self.filter(visibility=Visibility.PUBLIC)

    def with_contributors(self) -> "ProjectQuerySet":
        """Prefetch related contributors for optimized access."""
        return self.prefetch_related("contributors")

    def with_metadata(self) -> "ProjectQuerySet":
        """Prefetch all related metadata for detail views.

        Includes descriptions, dates, identifiers, and contributors to minimize
        database queries when displaying full project details.
        """
        return self.select_related("owner").prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
            "contributors",
            "keywords",
        )

    def with_list_data(self) -> "ProjectQuerySet":
        """Optimized queryset for list views.

        Only prefetches owner and keywords, avoiding expensive related data
        not needed in list displays.
        """
        return self.select_related("owner").prefetch_related("keywords")


class Project(BaseModel):
    """A project is a collection of datasets and associated metadata. The Project model
    is the top level model in the FairDM schema hierarchy and all datasets, samples,
    and measurements should relate back to a project."""

    DEFAULT_ROLES = ["ProjectMember"]
    CONTRIBUTOR_ROLES = FairDMRoles.from_collection("Project")
    DATE_TYPES = FairDMDates.from_collection("Project")
    DESCRIPTION_TYPES = FairDMDescriptions.from_collection("Project")
    # IDENTIFIER_TYPES = choices.DataCiteIdentifiers
    STATUS_CHOICES = ProjectStatus
    VISIBILITY = Visibility

    objects = ProjectQuerySet.as_manager()  # type: ignore[assignment,misc]

    uuid = ShortUUIDField(
        editable=False,
        unique=True,
        prefix="p",
        verbose_name="UUID",
    )

    visibility = models.IntegerField(
        _("visibility"),
        choices=VISIBILITY,
        default=VISIBILITY.PRIVATE,
        help_text=_("Visibility within the application."),
    )
    funding = models.JSONField(
        verbose_name=_("funding"),
        help_text=_(
            "Funding awards, in DataCite's funding reference shape: a list "
            "of objects, each naming a funder and optionally an award."
        ),
        null=True,
        blank=True,
        validators=[validate_funding],
    )
    status = models.IntegerField(
        _("status"),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.CONCEPT,
        help_text=_("The current lifecycle stage of the project."),
    )
    contributors = GenericRelation("contributors.Contribution")

    # RELATIONS
    # `created_by` is a ForeignKey rather than a plain nullable char field, so it
    # carries a database index by default - no additional indexing decision is
    # needed here. Not editable: the creator is written server-side only (see
    # the portal create view and ProjectViewSet.perform_create), never through a
    # form, the admin or a serializer field.
    created_by = models.ForeignKey(
        "contributors.Person",
        on_delete=models.SET_NULL,
        related_name="created_projects",
        verbose_name=_("created by"),
        help_text=_(
            "The user who created this project. Left unset if that user's "
            "account has since been removed."
        ),
        null=True,
        blank=True,
        editable=False,
    )
    owner = models.ForeignKey(
        "contributors.Organization",
        help_text=_("The organization that owns the project."),
        on_delete=models.PROTECT,
        related_name="owned_projects",
        verbose_name=_("owner"),
        null=True,
        blank=True,
    )

    _metadata = {
        "title": "name",
        "description": "get_meta_description",
        "image": "get_meta_image",
        "type": "research.project",
    }

    class Meta:
        verbose_name = _("project")
        verbose_name_plural = _("projects")
        default_related_name = "projects"
        ordering = ["-modified"]
        permissions = [
            *CORE_PERMISSIONS,
            ("change_project_metadata", _("Can edit project metadata")),
            ("change_project_settings", _("Can change project settings")),
        ]


class ProjectDescription(AbstractDescription):
    VOCABULARY = FairDMDescriptions.from_collection("Project")
    related = models.ForeignKey("Project", on_delete=models.CASCADE)

    class Meta(AbstractDescription.Meta):
        unique_together = [("related", "type")]
        verbose_name = _("project description")
        verbose_name_plural = _("project descriptions")

    def clean(self):
        """Validate that only one description per type exists for this project."""
        super().clean()
        if self.related_id and self.type:
            existing = (
                ProjectDescription.objects.filter(related=self.related, type=self.type)
                .exclude(pk=self.pk)
                .exists()
            )
            if existing:
                raise ValidationError(
                    {
                        "type": _(
                            "A description of type '%(type)s' already exists "
                            "for this project."
                        )
                        % {"type": self.type}
                    }
                )


class ProjectDate(AbstractDate):
    VOCABULARY = FairDMDates.from_collection("Project")
    related = models.ForeignKey("Project", on_delete=models.CASCADE)

    START_TYPE = "Start"
    END_TYPE = "End"

    class Meta(AbstractDate.Meta):
        verbose_name = _("project date")
        verbose_name_plural = _("project dates")

    def clean(self):
        """Validate that the project's end date does not precede its start.

        A project's start and end are stored as two separate `ProjectDate`
        rows, one per type, so the comparison is made against the sibling
        record rather than within a single instance. `PartialDate` mixes
        precision into its ordering (`self.date >= other.date and
        self.precision >= other.precision`), so comparing two values of
        different precision directly is unsafe - the check instead compares
        at the coarser of the two precisions.
        """
        super().clean()

        if not self.related_id or not self.value:
            return

        if self.type == self.START_TYPE:
            start_value, end_value = self.value, self._sibling_value(self.END_TYPE)
        elif self.type == self.END_TYPE:
            start_value, end_value = self._sibling_value(self.START_TYPE), self.value
        else:
            return

        if start_value is None or end_value is None:
            return

        if self._precedes(end_value, start_value):
            raise ValidationError(
                {
                    "value": _(
                        "The project's end date (%(end)s) cannot be before "
                        "its start date (%(start)s)."
                    )
                    % {"start": start_value, "end": end_value}
                }
            )

    def _sibling_value(self, type_):
        """Return the value of this project's other date of `type_`, if any."""
        queryset = ProjectDate.objects.filter(related_id=self.related_id, type=type_)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        sibling = queryset.first()
        return sibling.value if sibling else None

    @staticmethod
    def _precedes(a: PartialDate, b: PartialDate) -> bool:
        """Whether PartialDate `a` is earlier than PartialDate `b`.

        Compares at the coarser of the two precisions: years only if either
        is year-precision, year and month if either is month-precision, and
        the full date only when both carry day precision.
        """
        precision = min(a.precision, b.precision)
        if precision == PartialDate.YEAR:
            return bool(a.date.year < b.date.year)
        if precision == PartialDate.MONTH:
            return bool((a.date.year, a.date.month) < (b.date.year, b.date.month))
        return bool(a.date < b.date)


class ProjectIdentifier(AbstractIdentifier):
    VOCABULARY = FairDMIdentifiers.from_collection("Project")
    related = models.ForeignKey("Project", on_delete=models.CASCADE)

    class Meta(AbstractIdentifier.Meta):
        verbose_name = _("project identifier")
        verbose_name_plural = _("project identifiers")


class PublicDatasetsProtect(Exception):
    """Raised by pre_delete signal when a Project has publicly visible datasets.

    Attributes:
        datasets: QuerySet of public Dataset instances blocking deletion.
    """

    def __init__(self, datasets):
        self.datasets = datasets
        super().__init__(
            f"Cannot delete project: {datasets.count()} public dataset(s) must be made private or deleted first."
        )


@receiver(pre_delete, sender=Project)
def prevent_project_deletion_with_datasets(sender, instance, **kwargs):
    """Prevent deletion of projects that have associated PUBLIC datasets.

    This signal ensures data integrity by blocking project deletion when
    publicly visible child datasets exist. Projects with only private datasets
    can be deleted freely (private datasets are removed via CASCADE).

    Args:
        sender: The Project model class
        instance: The Project instance being deleted
        **kwargs: Additional signal arguments

    Raises:
        PublicDatasetsProtect: If the project has any PUBLIC datasets
    """
    public_datasets = instance.datasets.filter(visibility=Visibility.PUBLIC)
    if public_datasets.exists():
        raise PublicDatasetsProtect(public_datasets)
