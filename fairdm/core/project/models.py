"""Models for projects and their related descriptions, dates and identifiers."""

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
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
    """QuerySet for projects, with helpers that load related records in a bounded number of queries."""

    def get_visible(self) -> "ProjectQuerySet":
        """Return only the projects with public visibility.

        Returns:
            The public projects.
        """
        return self.filter(visibility=Visibility.PUBLIC)

    def with_contributors(self) -> "ProjectQuerySet":
        """Prefetch the contributions and the contributors behind them.

        Callers go on to name the person or organisation behind each credit, and
        ``Contributor`` is polymorphic, so resolving them lazily costs two queries per credit.

        Returns:
            The queryset with the prefetch applied.
        """
        return self.prefetch_related("contributors__contributor")

    def with_metadata(self) -> "ProjectQuerySet":
        """Load the owner, descriptions, dates, identifiers, contributions and keywords.

        Returns:
            The queryset with the related records loaded.
        """
        return self.select_related("owner").prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
            "contributors",
            "keywords",
        )

    def with_list_data(self) -> "ProjectQuerySet":
        """Load everything a project card draws, and annotate ``dataset_count``.

        The count covers public datasets only. An annotation aggregates over a join and never
        consults a manager, so the exclusion of private datasets is written into the aggregate.

        Returns:
            The queryset with the related records and count loaded.
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
    """A collection of datasets and associated metadata.

    The top-level model in the FairDM schema hierarchy: datasets, samples and measurements
    should relate back to a project.
    """

    DEFAULT_ROLES = ["ProjectMember"]
    CONTRIBUTOR_ROLES = FairDMRoles.from_collection("Project")
    DATE_TYPES = FairDMDates.from_collection("Project")
    DESCRIPTION_TYPES = FairDMDescriptions.from_collection("Project")
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

    # Not editable: the creator is written server-side only, never through a form, the admin
    # or a serializer field.
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
    #: `SEARCHING_FOR_COLLABORATORS` is a call to action, so only it gets an attention colour.
    STATUS_BADGE_VARIANTS = {
        STATUS_CHOICES.CONCEPT: "neutral",
        STATUS_CHOICES.PLANNING: "info",
        STATUS_CHOICES.IN_PROGRESS: "success",
        STATUS_CHOICES.COMPLETE: "neutral",
        STATUS_CHOICES.SEARCHING_FOR_COLLABORATORS: "accent",
    }

    @property
    def status_badge_variant(self):
        """Return the theme colour name for this project's status badge.

        Falls back to ``neutral`` so a status without an entry above still renders a legible badge.
        """
        return self.STATUS_BADGE_VARIANTS.get(self.status, "neutral")

    def get_absolute_url(self):
        """Return the URL of the project's registered overview page."""
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
    """Typed prose about a project, at most one description per type."""

    VOCABULARY = FairDMDescriptions.from_collection("Project")
    related = models.ForeignKey("Project", on_delete=models.CASCADE)

    class Meta(AbstractDescription.Meta):
        unique_together = [("related", "type")]
        verbose_name = _("project description")
        verbose_name_plural = _("project descriptions")

    def clean(self):
        """Refuse a second description of a type the project already carries."""
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
    """Typed date on a project, at most one per type, with the end no earlier than the start."""

    VOCABULARY = FairDMDates.from_collection("Project")
    related = models.ForeignKey("Project", on_delete=models.CASCADE)

    START_TYPE = "Start"
    END_TYPE = "End"

    class Meta(AbstractDate.Meta):
        verbose_name = _("project date")
        verbose_name_plural = _("project dates")

    def clean(self):
        """Refuse an end date that precedes the start date."""
        super().clean()

        # Start and end are separate rows, so the rule compares against the sibling row.
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
    """Typed external identifier naming a project outside the portal."""

    VOCABULARY = FairDMIdentifiers.from_collection("Project")
    related = models.ForeignKey("Project", on_delete=models.CASCADE)

    class Meta(AbstractIdentifier.Meta):
        verbose_name = _("project identifier")
        verbose_name_plural = _("project identifiers")


class PublicDatasetsProtect(Exception):
    """Raised before a project is deleted while it still has public datasets.

    Args:
        datasets: The queryset of public datasets blocking deletion.
    """

    def __init__(self, datasets):
        self.datasets = datasets
        super().__init__(
            f"Cannot delete project: {datasets.count()} public dataset(s) must be made private or deleted first."
        )


@receiver(pre_delete, sender=Project)
def prevent_project_deletion_with_datasets(sender, instance, **kwargs):
    """Block deleting a project that has public datasets.

    A project with only private datasets can be deleted, and they go with it by cascade.

    Args:
        sender: The Project model class.
        instance: The project being deleted.
        **kwargs: Additional signal arguments.

    Raises:
        PublicDatasetsProtect: The project has public datasets.
    """
    public_datasets = instance.datasets.filter(visibility=Visibility.PUBLIC)
    if public_datasets.exists():
        raise PublicDatasetsProtect(public_datasets)
