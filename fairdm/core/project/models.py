from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db.models import Count, Q

# from django.db.models import QuerySet
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from shortuuid.django_fields import ShortUUIDField

from fairdm.db import models
from fairdm.db.models import QuerySet
from fairdm.utils.choices import Visibility

from ..abstract import AbstractDate, AbstractDescription, AbstractIdentifier, BaseModel
from ..choices import ProjectStatus
from ..dates import precedes
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
        """Prefetch related contributors for optimized access.

        Reaches through to the contributor itself, not just the contribution
        row: every caller that prefetches contributions goes on to name the
        person or organisation behind each one, and `Contributor` is
        polymorphic, so resolving them lazily costs two queries per credit.
        """
        return self.prefetch_related("contributors__contributor")

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

        Loads everything a project card draws — the owning organization, the
        keyword badges, and the descriptions the plain-text abstract is taken
        from — and annotates ``dataset_count``, the number of datasets the card
        reports.

        That count names **public datasets only**. ``Dataset.objects`` excludes
        private records, but an annotation aggregates over a join to the dataset
        table and never consults a manager, so the exclusion has to be written
        into the aggregate itself. Without it the listing would publish a number
        that only a private dataset explains.
        """
        return (
            self.select_related("owner")
            .prefetch_related("keywords", "descriptions")
            .annotate(
                dataset_count=Count(
                    "datasets",
                    filter=~Q(datasets__visibility=Visibility.PRIVATE),
                    distinct=True,
                )
            )
        )


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

    #: The theme colour each lifecycle stage carries on a project card. Only
    #: `SEARCHING_FOR_COLLABORATORS` is a call to action, so it is the only one
    #: given an attention colour; the rest report state and stay quiet.
    STATUS_BADGE_VARIANTS = {
        STATUS_CHOICES.CONCEPT: "neutral",
        STATUS_CHOICES.PLANNING: "info",
        STATUS_CHOICES.IN_PROGRESS: "success",
        STATUS_CHOICES.COMPLETE: "neutral",
        STATUS_CHOICES.SEARCHING_FOR_COLLABORATORS: "accent",
    }

    @property
    def status_badge_variant(self):
        """The theme colour name for this project's status badge.

        Falls back to `neutral` so a status added to the vocabulary without an
        entry above still renders a legible badge rather than an unstyled one.
        """
        return self.STATUS_BADGE_VARIANTS.get(self.status, "neutral")

    def get_absolute_url(self):
        """The project's own page: its registered overview (013 plan P1).

        Overrides ``BaseModel.get_absolute_url``, which reverses ``f"{model_name}-detail"`` — a
        name this record no longer has, now that its own page is a registration rather than a
        standalone route. ``Dataset``, the other direct ``BaseModel`` subclass, keeps that
        behaviour unchanged; its own singular/plural address split is issue #283, not this one.
        """
        return reverse("project:overview", kwargs={"uuid": self.uuid})

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
        record rather than within a single instance. The comparison itself
        is precision-aware and shared, in `fairdm.core.dates`.
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

        if precedes(end_value, start_value):
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
