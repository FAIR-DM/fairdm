"""Models for datasets and their related descriptions, dates, identifiers and literature links."""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from licensing.fields import LicenseField
from shortuuid.django_fields import ShortUUIDField

from fairdm.db import models
from fairdm.db.models import QuerySet
from fairdm.utils.choices import Visibility

from ..abstract import AbstractDate, AbstractDescription, AbstractIdentifier, BaseModel
from ..dates import precedes
from ..utils import CORE_PERMISSIONS
from ..vocabularies import (
    FairDMDates,
    FairDMDescriptions,
    FairDMIdentifiers,
    FairDMRoles,
)


def get_default_license_pk():
    """Return the pk of the portal's configured default licence.

    Reads ``settings.FAIRDM_DEFAULT_LICENSE`` at call time, not at import time, so
    ``override_settings`` and per-portal configuration are both honoured. Falls back to
    "CC BY 4.0" where a portal states none.

    Returns:
        The licence pk, or ``None`` when the portal has not seeded its licences yet.
    """
    from licensing.models import License

    name = getattr(settings, "FAIRDM_DEFAULT_LICENSE", "CC BY 4.0")
    return License.objects.filter(name=name).values_list("pk", flat=True).first()


# DataCite Metadata Schema 4.4 relation types, https://schema.datacite.org/meta/kernel-4.4/
DATACITE_RELATIONSHIP_TYPES = [
    ("IsCitedBy", _("Is Cited By")),
    ("Cites", _("Cites")),
    ("IsSupplementTo", _("Is Supplement To")),
    ("IsSupplementedBy", _("Is Supplemented By")),
    ("IsContinuedBy", _("Is Continued By")),
    ("Continues", _("Continues")),
    ("IsDescribedBy", _("Is Described By")),
    ("Describes", _("Describes")),
    ("HasMetadata", _("Has Metadata")),
    ("IsMetadataFor", _("Is Metadata For")),
    ("HasVersion", _("Has Version")),
    ("IsVersionOf", _("Is Version Of")),
    ("IsNewVersionOf", _("Is New Version Of")),
    ("IsPreviousVersionOf", _("Is Previous Version Of")),
    ("IsPartOf", _("Is Part Of")),
    ("HasPart", _("Has Part")),
    ("IsPublishedIn", _("Is Published In")),
    ("IsReferencedBy", _("Is Referenced By")),
    ("References", _("References")),
    ("IsDocumentedBy", _("Is Documented By")),
    ("Documents", _("Documents")),
    ("IsCompiledBy", _("Is Compiled By")),
    ("Compiles", _("Compiles")),
    ("IsVariantFormOf", _("Is Variant Form Of")),
    ("IsOriginalFormOf", _("Is Original Form Of")),
    ("IsIdenticalTo", _("Is Identical To")),
    ("IsReviewedBy", _("Is Reviewed By")),
    ("Reviews", _("Reviews")),
    ("IsDerivedFrom", _("Is Derived From")),
    ("IsSourceOf", _("Is Source Of")),
    ("IsRequiredBy", _("Is Required By")),
    ("Requires", _("Requires")),
    ("Obsoletes", _("Obsoletes")),
    ("IsObsoletedBy", _("Is Obsoleted By")),
]


class DatasetLiteratureRelation(models.Model):
    """Link between a dataset and a literature item, typed with a DataCite relation type."""

    dataset = models.ForeignKey(
        "Dataset",
        on_delete=models.CASCADE,
        related_name="literature_relations",
        verbose_name=_("dataset"),
    )
    literature_item = models.ForeignKey(
        "literature.LiteratureItem",
        on_delete=models.CASCADE,
        related_name="dataset_relations",
        verbose_name=_("literature item"),
    )
    relationship_type = models.CharField(
        _("relationship type"),
        max_length=50,
        choices=DATACITE_RELATIONSHIP_TYPES,
        help_text=_(
            "DataCite relationship type (e.g., IsCitedBy, Cites, IsDocumentedBy)"
        ),
    )

    class Meta:
        verbose_name = _("dataset literature relation")
        verbose_name_plural = _("dataset literature relations")
        unique_together = [["dataset", "literature_item", "relationship_type"]]
        indexes = [
            models.Index(fields=["relationship_type"]),
        ]

    def __str__(self):
        """Show the dataset, the relation and the literature item."""
        return f"{self.dataset} {self.get_relationship_type_display()} {self.literature_item}"


class DatasetQuerySet(QuerySet):
    """QuerySet for datasets, with helpers that load related records in a bounded number of queries.

    None of the methods widens an already-narrowed query. ``Dataset.objects`` excludes private
    datasets before a caller holds a queryset, so ``Dataset.all_objects`` is the route to every
    dataset.
    """

    def get_visible(self) -> "DatasetQuerySet":
        """Return the public datasets that are not inside a private project.

        A private project hides everything beneath it, so a public dataset in one is left out.
        A dataset with no project counts on its own visibility.

        Returns:
            The datasets a profile or a public listing may name.
        """
        return self.filter(visibility=Visibility.PUBLIC).filter(
            Q(project__isnull=True) | Q(project__visibility=Visibility.PUBLIC)
        )

    def published(self) -> "DatasetQuerySet":
        """Return the datasets whose ``published`` flag is set.

        Call it on ``all_objects``, not ``objects``: the default manager excludes private
        datasets, and a published private dataset is an ordinary state a related-record
        filter must still offer.

        Returns:
            The published datasets.
        """
        return self.filter(published=True)

    def with_related(self) -> "DatasetQuerySet":
        """Prefetch the project and contributors.

        Returns:
            The queryset with the prefetches applied.
        """
        return self.prefetch_related(
            "project",
            "contributors",
        )

    def with_contributors(self) -> "DatasetQuerySet":
        """Prefetch only the contributors, which is lighter than ``with_related()``.

        Returns:
            The queryset with the prefetch applied.
        """
        return self.prefetch_related("contributors")

    def with_list_data(self) -> "DatasetQuerySet":
        """Load everything a dataset card draws, and annotate its sample and measurement counts.

        The counts are not filtered: a sample or measurement is as visible as its dataset, and
        this queryset is already narrowed to the datasets the visitor may see.

        Returns:
            The queryset with the related records and counts loaded.
        """
        # `distinct=True` is load-bearing: two counts in one query become two joins that
        # multiply each other's rows.
        # The contributor prefetch reaches the person, because a card names every contributor.
        return (
            self.select_related("project", "license")
            .prefetch_related("keywords", "descriptions", "contributors__contributor")
            .annotate(
                sample_count=Count("samples", distinct=True),
                measurement_count=Count("measurements", distinct=True),
            )
        )

    def with_metadata(self) -> "DatasetQuerySet":
        """Prefetch descriptions, dates, identifiers, contributions and keywords.

        Returns:
            The queryset with the prefetches applied.
        """
        return self.prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
            "contributors",
            "keywords",
        )


class DatasetManager(models.Manager.from_queryset(DatasetQuerySet)):  # type: ignore[misc]
    """The default manager for ``Dataset``, which excludes private datasets.

    Built from ``DatasetQuerySet`` so the queryset helpers work on the default manager too.
    Forward relations and the deletion collector use the unfiltered base manager, so following a
    relation to a private dataset, or cascading a deletion to one, is unaffected.
    """

    def get_queryset(self) -> DatasetQuerySet:
        """Exclude private datasets."""
        queryset: DatasetQuerySet = super().get_queryset()
        return queryset.exclude(visibility=Visibility.PRIVATE)


class Dataset(BaseModel):
    """The unit a portal cites and distributes, optionally within a project.

    Samples and measurements hang beneath a dataset, and ``has_data`` reports whether any do.
    A dataset is private until its visibility is set otherwise: ``objects`` excludes private
    datasets and ``all_objects`` returns every dataset. Deleting its project deletes it too.
    A dataset created with no licence gets the portal's default (``get_default_license_pk``).

    Related records are ``DatasetDescription``, ``DatasetDate``, ``DatasetIdentifier`` and
    ``DatasetLiteratureRelation``, plus ``contributors``, whose roles come from
    ``CONTRIBUTOR_ROLES``.
    """

    CONTRIBUTOR_ROLES = FairDMRoles.from_collection("Dataset")
    DATE_TYPES = FairDMDates.from_collection("Dataset")
    DESCRIPTION_TYPES = FairDMDescriptions.from_collection("Dataset")
    # The "Dataset" collection, as `DatasetIdentifier.VOCABULARY` uses, not the unscoped vocabulary.
    IDENTIFIER_TYPES = FairDMIdentifiers.from_collection("Dataset").choices
    VISIBILITY_CHOICES = Visibility
    DEFAULT_ROLES = ["ProjectMember"]

    # `objects` is declared first, so Django takes it as `_default_manager`.
    objects = DatasetManager()  # type: ignore[misc]
    all_objects = DatasetQuerySet.as_manager()

    uuid = ShortUUIDField(
        editable=False,
        unique=True,
        prefix="d",
        verbose_name=_("UUID"),
        help_text=_(
            "A short, unique identifier generated automatically when the "
            "dataset is created. Cannot be edited afterwards."
        ),
    )

    visibility = models.IntegerField(
        _("visibility"),
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_CHOICES.PRIVATE,
        db_index=True,
        help_text=_("Visibility within the application."),
    )

    published = models.BooleanField(
        _("published"),
        default=False,
        db_index=True,
        help_text=_(
            "Whether the data beneath this dataset may be shown publicly. "
            "Independent of visibility, which governs metadata only. Set in "
            "the Django admin."
        ),
    )

    contributors = GenericRelation(
        "contributors.Contribution", related_query_name="dataset"
    )

    # Not editable: the creator is written server-side only, never through a form, the admin
    # or a serializer field.
    created_by = models.ForeignKey(
        "contributors.Person",
        on_delete=models.SET_NULL,
        related_name="created_datasets",
        verbose_name=_("created by"),
        help_text=_(
            "The user who created this dataset. Left unset if that user's "
            "account has since been removed."
        ),
        null=True,
        blank=True,
        editable=False,
    )
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
    related_literature: models.ManyToManyField = models.ManyToManyField(
        "literature.LiteratureItem",
        help_text=_("Any literature that is related to this dataset."),
        through="DatasetLiteratureRelation",
        related_name="related_datasets",
        related_query_name="related_dataset",
        blank=True,
    )
    license = LicenseField(
        null=True,
        blank=True,
        default=get_default_license_pk,
        verbose_name=_("license"),
        help_text=_(
            "The license under which the dataset's data is published. "
            "Defaults to the portal's configured license when none is chosen."
        ),
    )

    _metadata = {
        "title": "name",
        "description": "get_meta_description",
        "type": "research.dataset",
    }

    class Meta:
        verbose_name = _("dataset")
        verbose_name_plural = _("datasets")
        default_related_name = "datasets"
        ordering = ["-modified"]
        permissions = [
            *CORE_PERMISSIONS,
            ("import_data", "Can import data into dataset"),
            ("can_publish", "Can publish dataset"),
            ("change_dataset_metadata", "Can edit dataset metadata"),
            ("change_dataset_settings", "Can change dataset settings"),
        ]

    @property
    def data_is_public(self) -> bool:
        """Whether anyone may see this dataset's samples and measurements.

        Publishing is meant to make a dataset public, so a published dataset should never be
        private. The two fields are still set separately, so both are checked.
        """
        return self.visibility == Visibility.PUBLIC and self.published

    def get_absolute_url(self):
        """Return the URL of the dataset's registered overview page."""
        return reverse("dataset:overview", kwargs={"uuid": self.uuid})

    @cached_property
    def has_data(self):
        """Return whether the dataset holds any samples or measurements, in a single query.

        Returns:
            True when at least one sample or measurement hangs beneath the dataset.
        """
        sample_pks = self.samples.values("pk")
        measurement_pks = self.measurements.values("pk")
        return sample_pks.union(measurement_pks).exists()

    @cached_property
    def bbox(self):
        """Return the bounding box of the dataset's locations.

        Returns:
            The bounding box computed by ``bbox_for_dataset``.
        """
        from fairdm.contrib.location.utils import bbox_for_dataset

        return bbox_for_dataset(self)


class DatasetDescription(AbstractDescription):
    """Typed prose about a dataset, at most one description per type.

    Enforced by ``clean()`` and by a database constraint.
    """

    VOCABULARY = FairDMDescriptions.from_collection("Dataset")
    related = models.ForeignKey("Dataset", on_delete=models.CASCADE)

    class Meta(AbstractDescription.Meta):
        indexes = [
            models.Index(fields=["type"], name="dataset_desc_type_idx"),
        ]

    def clean(self):
        """Refuse a second description of a type the dataset already carries."""
        super().clean()
        if self.related_id and self.type:
            existing = (
                DatasetDescription.objects.filter(related=self.related, type=self.type)
                .exclude(pk=self.pk)
                .exists()
            )
            if existing:
                raise ValidationError(
                    {
                        "type": _(
                            "A description of type '%(type)s' already exists "
                            "for this dataset."
                        )
                        % {"type": self.type}
                    }
                )


class DatasetDate(AbstractDate):
    """Typed dates marking points in a dataset's life, at most one date per type.

    Enforced by ``clean()`` and by a database constraint. The collection end cannot precede
    the collection start.
    """

    VOCABULARY = FairDMDates.from_collection("Dataset")
    related = models.ForeignKey("Dataset", on_delete=models.CASCADE)

    START_TYPE = "CollectionStart"
    END_TYPE = "CollectionEnd"

    class Meta(AbstractDate.Meta):
        indexes = [
            models.Index(fields=["type"], name="dataset_date_type_idx"),
        ]

    def clean(self):
        """Refuse a collection end date that precedes the collection start date."""
        # Start and end are separate rows, so the rule compares against the sibling row.
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
                        "The dataset's collection end date (%(end)s) cannot "
                        "be before its collection start date (%(start)s)."
                    )
                    % {"start": start_value, "end": end_value}
                }
            )

    def _sibling_value(self, type_):
        """Return the value of this dataset's other date of `type_`, if any."""
        queryset = DatasetDate.objects.filter(related_id=self.related_id, type=type_)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        sibling = queryset.first()
        return sibling.value if sibling else None


class DatasetIdentifier(AbstractIdentifier):
    """Typed external identifier naming a dataset outside the portal, at most one per type.

    Enforced by a database constraint. The same value cannot name two records: the
    cross-record check lives in ``AbstractIdentifier.clean()``.
    """

    VOCABULARY = FairDMIdentifiers.from_collection("Dataset")
    related = models.ForeignKey("Dataset", on_delete=models.CASCADE)
