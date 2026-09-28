"""Row-set declarations for the related records that carry a ``type``/``value`` pair.

Covers the models built on ``AbstractDate`` and ``AbstractIdentifier``
(``fairdm/core/abstract.py``), each edited on its owning record's page as a row set.
"""

from mvp.views.inline import InlineFormSet

from .dataset.models import DatasetDate, DatasetIdentifier
from .project.models import ProjectDate, ProjectIdentifier


class RelatedRecordInline(InlineFormSet):
    """Row set with one row per existing ``type``/``value`` pair and no blank extras.

    A subclass names only its ``model``.
    """

    # A tuple, not a list: BaseInlineFormSet appends the parent key to a list in place,
    # leaking rows between the subclasses that share it.
    fields = ("type", "value")
    extra = 0

    def get_factory_kwargs(self):
        """Cap the row set at one row per type the model's vocabulary offers."""
        kwargs = super().get_factory_kwargs()
        kwargs["max_num"] = len(self.model.VOCABULARY.choices)
        kwargs["validate_max"] = True
        return kwargs


class ProjectDateInline(RelatedRecordInline):
    """Row set for a project's dates."""

    model = ProjectDate


class ProjectIdentifierInline(RelatedRecordInline):
    """Row set for a project's identifiers."""

    model = ProjectIdentifier


class DatasetDateInline(RelatedRecordInline):
    """Row set for a dataset's dates."""

    model = DatasetDate


class DatasetIdentifierInline(RelatedRecordInline):
    """Row set for a dataset's identifiers."""

    model = DatasetIdentifier
