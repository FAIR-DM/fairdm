from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.functional import classproperty

# from rest_framework.authtoken.models import Token
from django.utils.translation import gettext_lazy as _
from research_vocabs.fields import ConceptField
from shortuuid.django_fields import ShortUUIDField

from ..abstract import AbstractDate, AbstractDescription, AbstractIdentifier, BasePolymorphicModel
from ..choices import SampleStatus
from ..managers import PolymorphicManager
from ..vocabularies import FairDMDates, FairDMDescriptions, FairDMIdentifiers, FairDMRoles


# WARNING: PolymorphicModel must always be listed first in the inheritance list to ensure
# proper polymorphic behavior across relations and queries.
# SEE: https://github.com/jazzband/django-polymorphic/issues/437#issuecomment-677638021
class Sample(BasePolymorphicModel):
    """A sample is a physical or digital object that is part of a dataset."""

    CONTRIBUTOR_ROLES = FairDMRoles.from_collection("Sample")
    DATE_TYPES = FairDMDates.from_collection("Sample")
    DESCRIPTION_TYPES = FairDMDescriptions.from_collection("Sample")
    # IDENTIFIER_TYPES = choices.DataCiteIdentifiers

    objects = PolymorphicManager()

    dataset = models.ForeignKey(
        "dataset.Dataset",
        verbose_name=_("dataset"),
        help_text=_("The original dataset this sample first appeared in."),
        related_name="samples",
        on_delete=models.CASCADE,
    )

    uuid = ShortUUIDField(
        editable=False,
        unique=True,
        prefix="s",
        verbose_name="UUID",
    )
    local_id = models.CharField(
        _("Local ID"),
        max_length=255,
        help_text=_(
            "An alphanumeric identifier used by the creator/s to identify the sample within a specific dataset"
        ),
        null=True,
        blank=True,
    )
    status = ConceptField(
        verbose_name=_("status"),
        vocabulary=SampleStatus,
        default="unknown",
    )

    location = models.ForeignKey(
        "fairdm_location.Point",
        verbose_name=_("location"),
        help_text=_("The location of the sample."),
        # related_name="samples",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # GENERIC RELATIONS
    contributors = GenericRelation("contributors.Contribution")
    # RELATIONS

    class Meta:
        verbose_name = _("sample")
        verbose_name_plural = _("samples")
        ordering = ["added"]
        default_related_name = "samples"

    # class FairDM:
    #     description = "A sample is a physical or digital object that is part of a dataset."
    #     filterset_class = "fairdm.core.filters.SampleFilter"
    #     form_class = "fairdm.core.forms.SampleForm"
    #     table_class = "fairdm.core.tables.SampleTable"
    #     resource_class = "fairdm.contrib.import_export.resources.SampleResource"

    @classproperty
    def type_of(self):
        return Sample

    def get_template_name(self):
        app_name = self._meta.app_label
        model_name = self._meta.model_name
        return [f"{app_name}/{model_name}_card.html", "fairdm/sample_card.html"]


class SampleDescription(AbstractDescription):
    VOCABULARY = FairDMDescriptions.from_collection("Sample")
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)


class SampleDate(AbstractDate):
    VOCABULARY = FairDMDates.from_collection("Sample")
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)


class SampleIdentifier(AbstractIdentifier):
    VOCABULARY = FairDMIdentifiers()
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)


class SampleRelation(models.Model):
    """A custom M2M through-model that stores relationships between samples."""

    # TODO: create a custom manager that gets the related samples based on the type of relation

    RELATION_TYPES = [
        ("child_of", _("child of")),
    ]
    type = models.CharField(max_length=255, verbose_name=_("type"), choices=RELATION_TYPES)
    source = models.ForeignKey(
        "Sample",
        verbose_name=_("source"),
        related_name="related_samples",
        on_delete=models.CASCADE,
    )
    target = models.ForeignKey(
        "Sample",
        verbose_name=_("target"),
        related_name="related_to",
        on_delete=models.CASCADE,
    )
