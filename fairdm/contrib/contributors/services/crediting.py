"""The one place the contributors of a project, dataset, sample or measurement are changed."""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from research_vocabs.models import Concept

from ..choices import ContributionLevel
from ..models import Contribution, Person


class Crediting:
    """Add, change and remove the contributors of one record.

    Each refusal is a ``ValidationError`` with a code, so a page can attach it to a field and a
    test can assert on it.

    Args:
        record: A project, dataset, sample or measurement, of any registered type.
    """

    def __init__(self, record):
        self.record = record

    def offered_roles(self):
        """Return the contribution roles the record's type offers.

        Returns:
            The concepts of the roles vocabulary that its group names for this type, in the
            vocabulary's order.
        """
        names = list(self.record.CONTRIBUTOR_ROLES.values)
        concepts = Concept.objects.filter(
            vocabulary__name="fairdm-roles", name__in=names
        )
        return sorted(concepts, key=lambda concept: names.index(concept.name))

    def add(self, contributor):
        """List a contributor on the record, last of its kind. A person starts at the view level.

        Args:
            contributor: The person or organization to list.

        Returns:
            The new contribution.

        Raises:
            ValidationError: With code ``duplicate`` when the contributor is already listed,
                or ``superuser`` when they are a superuser, who cannot be credited.
        """
        contributor = contributor.get_real_instance()
        if self.record.contributors.filter(contributor=contributor).exists():
            raise ValidationError(
                _("%(name)s is already a contributor on this record.")
                % {"name": contributor},
                code="duplicate",
            )
        is_person = isinstance(contributor, Person)
        if is_person and contributor.is_superuser:
            raise ValidationError(
                _("%(name)s is a superuser, and a superuser cannot be a contributor.")
                % {"name": contributor},
                code="superuser",
            )
        return Contribution.objects.create(
            contributor=contributor,
            content_type=ContentType.objects.get_for_model(self.record),
            object_id=self.record.pk,
            level=ContributionLevel.VIEW if is_person else None,
        )

    def update(self, contribution, *, roles):
        """Replace the roles a contributor holds on the record. Their level is left as it is.

        Args:
            contribution: The contribution to change.
            roles: Concepts of the roles vocabulary, none or more.

        Raises:
            ValidationError: With code ``role_not_offered`` when a role is not in the group the
                record's type offers.
        """
        offered = {concept.pk for concept in self.offered_roles()}
        if any(role.pk not in offered for role in roles):
            raise ValidationError(
                _("Choose from the roles offered for this kind of record."),
                code="role_not_offered",
            )
        contribution.roles.set(roles)

    def remove(self, contribution):
        """Remove a contributor from the record, and with them the level they held on it.

        Args:
            contribution: The contribution to remove.
        """
        contribution.delete()
