from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from shortuuid.django_fields import ShortUUIDField

from fairdm.db import models
from fairdm.utils.choices import Visibility

from ..abstract import AbstractDate, AbstractDescription, AbstractIdentifier, BaseModel
from ..choices import ProjectStatus
from ..utils import CORE_PERMISSIONS
from ..vocabularies import FairDMDates, FairDMDescriptions, FairDMIdentifiers, FairDMRoles

if TYPE_CHECKING:
    from fairdm.core.project.models import Project


class ProjectQuerySet(models.QuerySet):
    """Custom QuerySet for Project model with optimized query methods."""

    def get_visible(self) -> QuerySet["Project"]:
        """Return only projects with public visibility."""
        return self.filter(visibility=Visibility.PUBLIC)

    def with_contributors(self) -> QuerySet["Project"]:
        """Prefetch related contributors for optimized access."""
        return self.prefetch_related("contributors")

    def with_metadata(self) -> QuerySet["Project"]:
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

    def with_list_data(self) -> QuerySet["Project"]:
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

    objects = ProjectQuerySet.as_manager()

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
        help_text=_("Related funding information."),
        null=True,
        blank=True,
    )
    status = models.IntegerField(_("status"), choices=STATUS_CHOICES, default=STATUS_CHOICES.CONCEPT)
    contributors = GenericRelation("contributors.Contribution")

    # RELATIONS
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
            from django.core.exceptions import ValidationError

            existing = ProjectDescription.objects.filter(
                related=self.related, type=self.type
            ).exclude(pk=self.pk).exists()
            if existing:
                raise ValidationError({
                    "type": _("A description of this type already exists for this project.")
                })


class ProjectDate(AbstractDate):
    VOCABULARY = FairDMDates.from_collection("Project")
    related = models.ForeignKey("Project", on_delete=models.CASCADE)

    class Meta(AbstractDate.Meta):
        verbose_name = _("project date")
        verbose_name_plural = _("project dates")

    def clean(self):
        """Validate that end_date is not before start date."""
        super().clean()
        if self.date and self.end_date and self.end_date < self.date:
            from django.core.exceptions import ValidationError

            raise ValidationError({
                "end_date": _("End date cannot be before start date.")
            })


class ProjectIdentifier(AbstractIdentifier):
    VOCABULARY = FairDMIdentifiers()
    related = models.ForeignKey("Project", on_delete=models.CASCADE)

    class Meta(AbstractIdentifier.Meta):
        verbose_name = _("project identifier")
        verbose_name_plural = _("project identifiers")

@receiver(pre_delete, sender=Project)
def prevent_project_deletion_with_datasets(sender, instance, **kwargs):
    """Prevent deletion of projects that have associated datasets.

    This signal ensures data integrity by blocking project deletion when
    child datasets exist. Administrator can force deletion through admin
    interface if needed.

    Args:
        sender: The Project model class
        instance: The Project instance being deleted
        **kwargs: Additional signal arguments

    Raises:
        ValidationError: If the project has associated datasets
    """
    if instance.datasets.exists():
        raise ValidationError(
            _("Cannot delete project '{name}' because it has {count} associated dataset(s). "
              "Delete the datasets first or contact an administrator.").format(
                name=instance.name,
                count=instance.datasets.count()
            )
        )
