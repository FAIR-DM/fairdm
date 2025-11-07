from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import QuerySet
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from licensing.fields import LicenseField
from shortuuid.django_fields import ShortUUIDField

from fairdm.contrib.location.utils import bbox_for_dataset
from fairdm.db import models
from fairdm.utils.choices import Visibility

from ..abstract import AbstractDate, AbstractDescription, AbstractIdentifier, BaseModel
from ..utils import CORE_PERMISSIONS
from ..vocabularies import FairDMDates, FairDMDescriptions, FairDMIdentifiers, FairDMRoles

if TYPE_CHECKING:
    from fairdm.core.dataset.models import Dataset


class DatasetQuerySet(models.QuerySet):
    """Custom QuerySet for Dataset model with optimized query methods."""

    def get_visible(self) -> QuerySet["Dataset"]:
        """Return only datasets with public visibility."""
        return self.filter(visibility=Visibility.PUBLIC)

    def with_related(self) -> QuerySet["Dataset"]:
        """Prefetch related project, contributors, and literature for optimized access."""
        return self.prefetch_related(
            "project",
            "contributors",
        )

    def with_contributors(self) -> QuerySet["Dataset"]:
        """Prefetch only contributors for optimized access."""
        return self.prefetch_related("contributors")


class Dataset(BaseModel):
    """A dataset is a collection of samples, measurements and associated metadata. The Dataset model
    is the second level model in the FairDM schema heirarchy and all geographic sites,
    samples and sample measurements MUST relate back to a dataset."""

    CONTRIBUTOR_ROLES = FairDMRoles.from_collection("Dataset")
    DATE_TYPES = FairDMDates.from_collection("Dataset")
    DESCRIPTION_TYPES = FairDMDescriptions.from_collection("Dataset")
    # IDENTIFIER_TYPES = choices.DataCiteIdentifiers
    VISIBILITY_CHOICES = Visibility
    DEFAULT_ROLES = ["ProjectMember"]
    # DEFAULT_ROLES = FairDMRoles.from_collection("Dataset").get_concept("ProjectMember")

    objects = DatasetQuerySet.as_manager()

    uuid = ShortUUIDField(
        editable=False,
        unique=True,
        prefix="d",
        verbose_name="UUID",
    )

    visibility = models.IntegerField(
        _("visibility"),
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_CHOICES.PRIVATE,
        help_text=_("Visibility within the application."),
    )

    # published = models.BooleanField(
    #     _("published"),
    #     help_text=_("Determines whether data from this dataset can be accessed by the public."),
    #     default=False,
    # )

    # GENERIC RELATIONS
    contributors = GenericRelation("contributors.Contribution", related_query_name="dataset")

    # RELATIONS
    project = models.ForeignKey(
        "project.Project",
        verbose_name=_("project"),
        help_text=_("The project associated with the dataset."),
        related_name="datasets",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    reference = models.OneToOneField(
        "literature.LiteratureItem",
        verbose_name=_("Data reference"),
        help_text=_("The data publication associated with this dataset."),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    related_literature = models.ManyToManyField(
        "literature.LiteratureItem",
        help_text=_("Any literature that is related to this dataset."),
        related_name="related_datasets",
        related_query_name="related_dataset",
        blank=True,
    )
    license = LicenseField(null=True, blank=True)

    _metadata = {
        "title": "name",
        "description": "get_meta_description",
        "type": "research.dataset",
    }

    class Meta:
        verbose_name = _("dataset")
        verbose_name_plural = _("datasets")
        default_related_name = "datasets"
        ordering = ["modified"]
        permissions = [
            *CORE_PERMISSIONS,
            ("import_data", "Can import data into dataset"),
        ]

    @cached_property
    def has_data(self):
        """Check if the dataset has any samples or measurements."""
        return self.samples.exists() or self.measurements.exists()

    @cached_property
    def bbox(self):
        return bbox_for_dataset(self)


class DatasetDescription(AbstractDescription):
    VOCABULARY = FairDMDescriptions.from_collection("Dataset")
    related = models.ForeignKey("Dataset", on_delete=models.CASCADE)


class DatasetDate(AbstractDate):
    VOCABULARY = FairDMDates.from_collection("Dataset")
    related = models.ForeignKey("Dataset", on_delete=models.CASCADE)


class DatasetIdentifier(AbstractIdentifier):
    VOCABULARY = FairDMIdentifiers()
    related = models.ForeignKey("Dataset", on_delete=models.CASCADE)
