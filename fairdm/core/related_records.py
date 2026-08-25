"""Shared, portal-page-facing row-set declarations for the related-record
models that carry a ``type``/``value`` pair - ``AbstractDate`` and
``AbstractIdentifier`` (``fairdm/core/abstract.py``).

Every core record type (Project, Dataset, Sample, Measurement) carries the
same related records, and each is edited on its owning record's page as a
row set (plan P3, P6).

This module is not itself a page, view or URL - later stories register those
and list the pieces declared here.
"""

from mvp.views.inline import InlineFormSet

from .dataset.models import DatasetDate, DatasetIdentifier
from .project.models import ProjectDate, ProjectIdentifier


class RelatedRecordInline(InlineFormSet):
    """One row per existing ``type``/``value`` pair, and no blank rows beyond
    them (``extra = 0`` - the interface layer omits anything left unset, so
    Django's own default of three blank rows would apply otherwise).

    A subclass names only its ``model``; ``type`` and ``value`` are the two
    fields every related-record model carries (plan P6).

    ``fields`` is a tuple, not a list: ``BaseInlineFormSet.__init__`` appends
    the parent foreign key's name to ``form._meta.fields`` in place, and a
    list here would be that same list - mutating this shared class attribute
    on every formset built from it, project rows leaking into dataset rows
    and back. A tuple forces Django's own copy-on-write branch instead
    (``django/forms/models.py:1116``).
    """

    fields = ("type", "value")
    extra = 0

    def get_factory_kwargs(self):
        """Bound the row set to one row per type its vocabulary offers - the
        same rule the Django admin already applies per model
        (``fairdm/core/dataset/admin.py``'s ``DescriptionInline``/``DateInline``/
        ``IdentifierInline``), generalised here so every subclass gets it for
        free.

        Read from ``self.model.VOCABULARY`` (``GenericModel.VOCABULARY``),
        which is already scoped to the owning record's own collection
        (``DatasetIdentifier.VOCABULARY = FairDMIdentifiers.from_collection
        ("Dataset")``) - not a parent-model constant this module would have to
        import Dataset/Project to reach.
        """
        kwargs = super().get_factory_kwargs()
        kwargs["max_num"] = len(self.model.VOCABULARY.choices)
        kwargs["validate_max"] = True
        return kwargs


class ProjectDateInline(RelatedRecordInline):
    model = ProjectDate


class ProjectIdentifierInline(RelatedRecordInline):
    model = ProjectIdentifier


class DatasetDateInline(RelatedRecordInline):
    model = DatasetDate


class DatasetIdentifierInline(RelatedRecordInline):
    model = DatasetIdentifier
